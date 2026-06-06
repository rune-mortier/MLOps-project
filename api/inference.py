import os
import pickle
import numpy as np

os.environ.setdefault("KERAS_BACKEND", "torch")

MODEL_DIR = os.environ.get("MODEL_DIR", "/models")

CATEGORY_AVG_PRICE = {"FOODS": 5.5, "HOBBIES": 10.5, "HOUSEHOLD": 10.5}

CATEGORY_MAP = {"FOODS": 0, "HOBBIES": 1, "HOUSEHOLD": 2}
STORE_MAP    = {"CA_1": 0, "CA_2": 1, "TX_1": 2}
STATE_MAP    = {"CA": 0, "TX": 1}
DEPT_MAP     = {"FOODS_1": 0, "HOBBIES_1": 1, "HOUSEHOLD_1": 2}

# Items per category from mock data generator (i%3 determines category)
# FOODS: i=0,3,6,...,48  → FOODS_1_001, FOODS_1_004, ..., FOODS_1_049
# HOBBIES: i=1,4,7,...,49 → HOBBIES_1_002, HOBBIES_1_005, ..., HOBBIES_1_050
# HOUSEHOLD: i=2,5,8,...,47 → HOUSEHOLD_1_003, HOUSEHOLD_1_006, ..., HOUSEHOLD_1_048
ITEMS_BY_CATEGORY = {
    "FOODS":     sorted([f"FOODS_1_{i+1:03d}"     for i in range(50) if i % 3 == 0]),
    "HOBBIES":   sorted([f"HOBBIES_1_{i+1:03d}"   for i in range(50) if i % 3 == 1]),
    "HOUSEHOLD": sorted([f"HOUSEHOLD_1_{i+1:03d}" for i in range(50) if i % 3 == 2]),
}

# Global sorted item list — matches LabelEncoder.fit_transform order from train.py
_all_items = sorted(item for items in ITEMS_BY_CATEGORY.values() for item in items)
ITEM_MAP = {item: idx for idx, item in enumerate(_all_items)}

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


def build_feature_vector(category: str, store: str, month: int, item_id: str) -> np.ndarray:
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
        ITEM_MAP.get(item_id, 0),
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


def predict(category: str, store: str, month: int, pct_change: float, item_id: str) -> dict:
    model, scaler = load_model()
    features        = build_feature_vector(category, store, month, item_id)
    features_scaled = scaler.transform(features)

    baseline_qty = float(np.maximum(0, model.predict(features_scaled, verbose=0).flatten()[0]))
    scenario_qty = baseline_qty * (1 + pct_change / 100.0)
    price        = CATEGORY_AVG_PRICE.get(category, 10.0)

    return {
        "baseline_revenue": round(baseline_qty * price, 2),
        "scenario_revenue": round(scenario_qty * price, 2),
        "delta":            round((scenario_qty - baseline_qty) * price, 2),
        "baseline_qty":     round(baseline_qty, 2),
        "scenario_qty":     round(scenario_qty, 2),
    }