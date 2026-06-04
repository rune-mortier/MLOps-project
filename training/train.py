"""
M5 Forecasting — Azure ML Training Script
MLP + LSTM op Walmart dagelijkse verkoopdata

Gebruik:
    python train.py --data_dir <pad_naar_csvs> [--sample_frac 0.05] [--epochs 50]
"""

import os
import argparse
import random
import pickle

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.preprocessing import StandardScaler, LabelEncoder

# ── Azure ML logging ────────────────────────────────────────────────────────
try:
    import mlflow
    import mlflow.keras
    MLFLOW = True
except ImportError:
    MLFLOW = False

# ── Keras / PyTorch backend ─────────────────────────────────────────────────
os.environ["KERAS_BACKEND"] = "torch"
import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout, BatchNormalization, Input, LSTM
from keras.callbacks import EarlyStopping
from keras.optimizers import Adam
import torch


# ════════════════════════════════════════════════════════════════════════════
# Config & argumenten
# ════════════════════════════════════════════════════════════════════════════

def parse_args():
    parser = argparse.ArgumentParser(description="M5 MLP + LSTM training")
    parser.add_argument("--data_dir",    type=str, default="csv",
                        help="Map met de 5 M5 CSV-bestanden")
    parser.add_argument("--output_dir",  type=str, default="outputs",
                        help="Map waar het model en de scaler opgeslagen worden")
    parser.add_argument("--sample_frac", type=float, default=0.05,
                        help="Fractie van items om op te trainen (0.0–1.0)")
    parser.add_argument("--epochs",      type=int,   default=50)
    parser.add_argument("--batch_mlp",   type=int,   default=4096)
    parser.add_argument("--batch_lstm",  type=int,   default=512)
    parser.add_argument("--seq_len",     type=int,   default=14,
                        help="Vensterlengte voor LSTM")
    parser.add_argument("--seed",        type=int,   default=50)
    return parser.parse_args()


# ════════════════════════════════════════════════════════════════════════════
# Reproducibiliteit
# ════════════════════════════════════════════════════════════════════════════

def set_seeds(seed):
    random.seed(seed)
    np.random.seed(seed)
    keras.utils.set_random_seed(seed)
    try:
        torch.manual_seed(seed)
        torch.use_deterministic_algorithms(True)
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════════════════
# 1. Data inladen
# ════════════════════════════════════════════════════════════════════════════

def load_data(data_dir):
    print("\n── Data inladen ──────────────────────────────────────────────")
    cal       = pd.read_csv(os.path.join(data_dir, "calendar.csv"),            parse_dates=["date"])
    train_val = pd.read_csv(os.path.join(data_dir, "sales_train_validation.csv"))
    prices    = pd.read_csv(os.path.join(data_dir, "sell_prices.csv"))

    print(f"Calendar : {cal.shape}  |  {cal.date.min().date()} → {cal.date.max().date()}")
    print(f"Train    : {train_val.shape}")
    print(f"Prices   : {prices.shape}")
    return cal, train_val, prices


# ════════════════════════════════════════════════════════════════════════════
# 2. Feature engineering
# ════════════════════════════════════════════════════════════════════════════

LAG_DAYS     = [7, 14, 28, 35]
ROLL_WINDOWS = [7, 28]

def build_features(cal, train_val, prices, sample_frac, seed):
    print("\n── Feature engineering ───────────────────────────────────────")
    id_cols = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]
    d_cols  = [c for c in train_val.columns if c.startswith("d_")]

    # Lang formaat
    df = train_val.melt(id_vars=id_cols, value_vars=d_cols,
                        var_name="d", value_name="sales")

    # Kalender koppelen
    df = df.merge(
        cal[["d", "date", "wday", "month", "year",
             "event_name_1", "snap_CA", "snap_TX", "snap_WI"]],
        on="d", how="left"
    )
    df["date"]  = pd.to_datetime(df["date"])
    df["d_num"] = df["d"].str.replace("d_", "").astype(int)
    df = df.sort_values(["id", "date"]).reset_index(drop=True)

    # Subsampling
    rng         = np.random.default_rng(seed)
    unique_ids  = df["id"].unique()
    n_sample    = max(1, int(len(unique_ids) * sample_frac))
    sampled_ids = rng.choice(unique_ids, size=n_sample, replace=False)
    df = df[df["id"].isin(sampled_ids)].copy().reset_index(drop=True)
    print(f"Subsampling: {n_sample} items → {df.shape[0]:,} rijen")

    # Prijzen
    df = df.merge(cal[["d", "wm_yr_wk"]], on="d", how="left")
    df = df.merge(prices, on=["store_id", "item_id", "wm_yr_wk"], how="left")
    df["sell_price"] = (
        df.sort_values("date")
          .groupby(["store_id", "item_id"])["sell_price"]
          .transform(lambda x: x.ffill())
    )
    df["sell_price"] = df["sell_price"].fillna(df["sell_price"].median())
    df = df.drop(columns=["wm_yr_wk"])

    # Lag-features
    for lag in LAG_DAYS:
        df[f"lag_{lag}"] = df.groupby("id")["sales"].shift(lag)

    # Rollende gemiddelden
    for w in ROLL_WINDOWS:
        df[f"roll_mean_{w}"] = (
            df.groupby("id")["sales"]
              .transform(lambda x: x.shift(28).rolling(w, min_periods=1).mean())
        )

    # Extra features
    df["is_weekend"] = df["wday"].isin([1, 2]).astype(int)
    df["has_event"]  = df["event_name_1"].notna().astype(int)
    df["snap"]       = np.where(df["state_id"] == "CA", df["snap_CA"],
                        np.where(df["state_id"] == "TX", df["snap_TX"], df["snap_WI"]))

    # Label encoding
    for col in ["cat_id", "dept_id", "store_id", "state_id", "item_id"]:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))

    print(f"Features klaar: {df.shape}")
    return df


# ════════════════════════════════════════════════════════════════════════════
# 3. Train/test split + standaardisatie
# ════════════════════════════════════════════════════════════════════════════

FEATURES = (
    ["cat_id", "dept_id", "store_id", "state_id", "item_id",
     "wday", "month", "year", "is_weekend", "has_event", "snap", "sell_price"]
    + [f"lag_{l}"       for l in LAG_DAYS]
    + [f"roll_mean_{w}" for w in ROLL_WINDOWS]
)

def split_and_scale(df):
    print("\n── Train/test split ──────────────────────────────────────────")
    df_clean    = df.dropna(subset=FEATURES + ["sales"]).copy()
    cutoff_date = df_clean["date"].max() - pd.Timedelta(days=28 * 6)
    train_mask  = df_clean["date"] < cutoff_date

    X_train = df_clean.loc[train_mask,  FEATURES]
    X_test  = df_clean.loc[~train_mask, FEATURES]
    y_train = df_clean.loc[train_mask,  "sales"]
    y_test  = df_clean.loc[~train_mask, "sales"]

    print(f"Cutoff  : {cutoff_date.date()}")
    print(f"Train   : {X_train.shape}")
    print(f"Test    : {X_test.shape}")

    scaler = StandardScaler()
    X_train_s = X_train.copy()
    X_test_s  = X_test.copy()
    X_train_s[FEATURES] = scaler.fit_transform(X_train[FEATURES])
    X_test_s[FEATURES]  = scaler.transform(X_test[FEATURES])

    return X_train_s, X_test_s, y_train, y_test, scaler, df_clean, X_test.index


# ════════════════════════════════════════════════════════════════════════════
# 4 & 5. MLP bouwen en trainen
# ════════════════════════════════════════════════════════════════════════════

def build_mlp(n_features):
    model = keras.Sequential([
        keras.layers.Input(shape=(n_features,)),
        keras.layers.Dense(256, activation="relu",
                           kernel_regularizer=keras.regularizers.L2(1e-4)),
        keras.layers.BatchNormalization(),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(128, activation="relu",
                           kernel_regularizer=keras.regularizers.L2(1e-4)),
        keras.layers.BatchNormalization(),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(64, activation="relu",
                           kernel_regularizer=keras.regularizers.L2(1e-4)),
        keras.layers.BatchNormalization(),
        keras.layers.Dropout(0.1),
        keras.layers.Dense(1)
    ])
    model.compile(optimizer=Adam(learning_rate=1e-3), loss="mse", metrics=["mae"])
    return model


def train_mlp(X_train_s, y_train, X_test_s, y_test, epochs, batch_size):
    print("\n── MLP training ──────────────────────────────────────────────")
    n_features = X_train_s.shape[1]
    model      = build_mlp(n_features)
    model.summary()

    early_stop = EarlyStopping(monitor="val_loss", patience=5,
                               restore_best_weights=True, verbose=1)

    history = model.fit(
        X_train_s.values, y_train.values,
        validation_split=0.1,
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[early_stop],
        verbose=1
    )

    y_pred = np.maximum(0, model.predict(X_test_s.values, batch_size=batch_size).flatten())
    rmse   = np.sqrt(mean_squared_error(y_test.values, y_pred))
    mae    = mean_absolute_error(y_test.values, y_pred)

    print(f"\nMLP  →  RMSE: {rmse:.4f}  |  MAE: {mae:.4f}")
    return model, history, rmse, mae


# ════════════════════════════════════════════════════════════════════════════
# 7 & 8. LSTM bouwen en trainen
# ════════════════════════════════════════════════════════════════════════════

def build_sequences(X_arr, y_arr, seq_len):
    Xs, ys = [], []
    for i in range(seq_len, len(X_arr)):
        Xs.append(X_arr[i - seq_len:i])
        ys.append(y_arr[i])
    return np.array(Xs, dtype=np.float32), np.array(ys, dtype=np.float32)


def prepare_lstm_data(df_clean, scaler, seq_len):
    print("\n── LSTM data voorbereiding ────────────────────────────────────")
    X_seq_list, y_seq_list = [], []
    for _, grp in df_clean.sort_values("d_num").groupby("id"):
        Xg = scaler.transform(grp[FEATURES])
        yg = grp["sales"].values
        if len(Xg) > seq_len:
            Xs_g, ys_g = build_sequences(Xg, yg, seq_len)
            X_seq_list.append(Xs_g)
            y_seq_list.append(ys_g)

    X_seq = np.concatenate(X_seq_list, axis=0)
    y_seq = np.concatenate(y_seq_list, axis=0)

    train_end = int(len(X_seq) * 0.60)
    val_end   = int(len(X_seq) * 0.80)

    splits = {
        "X_train": X_seq[:train_end],        "y_train": y_seq[:train_end],
        "X_val":   X_seq[train_end:val_end], "y_val":   y_seq[train_end:val_end],
        "X_test":  X_seq[val_end:],          "y_test":  y_seq[val_end:],
    }
    print(f"Train: {splits['X_train'].shape}  Val: {splits['X_val'].shape}  Test: {splits['X_test'].shape}")
    return splits


def build_lstm(seq_len, n_features):
    model = Sequential([
        Input(shape=(seq_len, n_features)),
        LSTM(64, return_sequences=True),
        Dropout(0.2),
        LSTM(32),
        Dropout(0.1),
        Dense(1)
    ])
    model.compile(optimizer=Adam(learning_rate=1e-3), loss="mse", metrics=["mae"])
    return model


def train_lstm(splits, n_features, seq_len, epochs, batch_size):
    print("\n── LSTM training ─────────────────────────────────────────────")
    model      = build_lstm(seq_len, n_features)
    model.summary()

    early_stop = EarlyStopping(monitor="val_loss", patience=5,
                               restore_best_weights=True, verbose=1)

    history = model.fit(
        splits["X_train"], splits["y_train"],
        validation_data=(splits["X_val"], splits["y_val"]),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[early_stop],
        verbose=1
    )

    y_pred = np.maximum(0, model.predict(splits["X_test"], batch_size=batch_size).flatten())
    rmse   = np.sqrt(mean_squared_error(splits["y_test"], y_pred))
    mae    = mean_absolute_error(splits["y_test"], y_pred)

    print(f"\nLSTM →  RMSE: {rmse:.4f}  |  MAE: {mae:.4f}")
    return model, history, rmse, mae


# ════════════════════════════════════════════════════════════════════════════
# Opslaan
# ════════════════════════════════════════════════════════════════════════════

def save_artifacts(output_dir, mlp_model, lstm_model, scaler):
    os.makedirs(output_dir, exist_ok=True)

    mlp_path  = os.path.join(output_dir, "mlp_model.keras")
    lstm_path = os.path.join(output_dir, "lstm_model.keras")
    scaler_path = os.path.join(output_dir, "scaler.pkl")

    mlp_model.save(mlp_path)
    lstm_model.save(lstm_path)
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    print(f"\nArtifacts opgeslagen in '{output_dir}':")
    print(f"  {mlp_path}")
    print(f"  {lstm_path}")
    print(f"  {scaler_path}")
    return mlp_path, lstm_path, scaler_path


# ════════════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════════════

def main():
    args = parse_args()
    set_seeds(args.seed)

    if MLFLOW:
        mlflow.start_run()
        mlflow.log_params({
            "sample_frac": args.sample_frac,
            "epochs":      args.epochs,
            "batch_mlp":   args.batch_mlp,
            "batch_lstm":  args.batch_lstm,
            "seq_len":     args.seq_len,
            "seed":        args.seed,
        })

    # 1. Data
    cal, train_val, prices = load_data(args.data_dir)

    # 2. Features
    df = build_features(cal, train_val, prices, args.sample_frac, args.seed)

    # 3. Split + scale
    X_train_s, X_test_s, y_train, y_test, scaler, df_clean, _ = split_and_scale(df)
    n_features = X_train_s.shape[1]

    # 4–6. MLP
    mlp_model, _, mlp_rmse, mlp_mae = train_mlp(
        X_train_s, y_train, X_test_s, y_test,
        epochs=args.epochs, batch_size=args.batch_mlp
    )

    # 7–9. LSTM
    lstm_splits = prepare_lstm_data(df_clean, scaler, args.seq_len)
    lstm_model, _, lstm_rmse, lstm_mae = train_lstm(
        lstm_splits, n_features, args.seq_len,
        epochs=args.epochs, batch_size=args.batch_lstm
    )

    # Eindresultaten
    print("\n" + "=" * 40)
    print(f"{'Model':<10}  {'RMSE':>8}  {'MAE':>8}")
    print("-" * 40)
    print(f"{'MLP':<10}  {mlp_rmse:>8.4f}  {mlp_mae:>8.4f}")
    print(f"{'LSTM':<10}  {lstm_rmse:>8.4f}  {lstm_mae:>8.4f}")
    print("=" * 40)

    # MLflow metrics loggen
    if MLFLOW:
        mlflow.log_metrics({
            "mlp_rmse":  mlp_rmse,  "mlp_mae":  mlp_mae,
            "lstm_rmse": lstm_rmse, "lstm_mae": lstm_mae,
        })

    # Opslaan
    mlp_path, lstm_path, scaler_path = save_artifacts(
        args.output_dir, mlp_model, lstm_model, scaler
    )

    # MLflow model registreren
    if MLFLOW:
        mlflow.keras.log_model(mlp_model,  "mlp_model",  registered_model_name="m5-mlp")
        mlflow.keras.log_model(lstm_model, "lstm_model", registered_model_name="m5-lstm")
        mlflow.log_artifact(scaler_path)
        mlflow.end_run()
        print("\nModellen geregistreerd in MLflow/Azure ML Model Registry.")


if __name__ == "__main__":
    main()
