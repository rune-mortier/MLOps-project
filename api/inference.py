import os
import pickle
import numpy as np

os.environ.setdefault("KERAS_BACKEND", "torch")

MODEL_DIR = os.environ.get("MODEL_DIR", "/models")

CATEGORY_AVG_PRICE = {"FOODS": 5.5, "HOBBIES": 10.5, "HOUSEHOLD": 10.5}

# Label encodings must match the order produced by train.py's LabelEncoder
CATEGORY_MAP = {"FOODS": 0, "HOBBIES": 1, "HOUSEHOLD": 2}
STORE_MAP    = {"CA_1": 0, "CA_2": 1, "TX_1": 2}
STATE_MAP    = {"CA": 0, "TX": 1}
DEPT_MAP     = {"FOODS_1": 0, "HOBBIES_1": 1, "HOUSEHOLD_1": 2}

_model  = None
_scaler = None


def load_model():
    global _model, _scaler
    if _model is None:
        import keras
        _model = keras.models.load_model(os.path.join(MODEL_DIR, "mlp_model.keras"))
    if _scaler is None:
        with open(os.path.join(MODEL_DIR, "scaler.pkl"), "rb") as f:
            _scaler = pickle.load(f)
    return _model, _scaler


def build_feature_vector(category: str, store: str, month: int) -> np.ndarray:
    """Build the 18-feature vector expected by the trained MLP.

    Feature order matches FEATURES list in training/train.py:
    cat_id, dept_id, store_id, state_id, item_id,
    wday, month, year, is_weekend, has_event, snap, sell_price,
    lag_7, lag_14, lag_28, lag_35, roll_mean_7, roll_mean_28
    """
    state = store.split("_")[0]
    dept  = category + "_1"
    features = [
        CATEGORY_MAP.get(category, 0),
        DEPT_MAP.get(dept, 0),
        STORE_MAP.get(store, 0),
        STATE_MAP.get(state, 0),
        0,                                       # item_id — representative first item
        3,                                       # wday — midweek
        month,
        2024,                                    # year
        0,                                       # is_weekend
        0,                                       # has_event
        0,                                       # snap
        CATEGORY_AVG_PRICE.get(category, 10.0),  # sell_price
        3.0, 3.0, 3.0, 3.0,                     # lag_7, lag_14, lag_28, lag_35
        3.0, 3.0,                                # roll_mean_7, roll_mean_28
    ]
    return np.array(features, dtype=np.float32).reshape(1, -1)


def predict(category: str, store: str, month: int, pct_change: float) -> dict:
    model, scaler = load_model()
    features        = build_feature_vector(category, store, month)
    features_scaled = scaler.transform(features)

    baseline_qty = float(np.maximum(0, model.predict(features_scaled, verbose=0).flatten()[0]))
    scenario_qty = baseline_qty * (1 + pct_change / 100.0)
    price        = CATEGORY_AVG_PRICE.get(category, 10.0)

    return {
        "baseline_revenue": round(baseline_qty * price, 2),
        "scenario_revenue": round(scenario_qty * price, 2),
        "delta":            round((scenario_qty - baseline_qty) * price, 2),
    }