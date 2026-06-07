import os
import sys
import numpy as np
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../api"))

from inference import build_feature_vector, predict, ITEMS_BY_CATEGORY, ITEM_MAP


def test_feature_vector_has_18_features():
    vec = build_feature_vector("FOODS", "CA_1", 3, "FOODS_1_001")
    assert vec.shape == (1, 18)


def test_feature_vector_encodes_month():
    vec = build_feature_vector("FOODS", "CA_1", 7, "FOODS_1_001")
    assert vec[0, 6] == 7


def test_feature_vector_encodes_item():
    vec1 = build_feature_vector("FOODS", "CA_1", 1, "FOODS_1_001")
    vec2 = build_feature_vector("FOODS", "CA_1", 1, "FOODS_1_004")
    assert vec1[0, 4] != vec2[0, 4]


def test_items_by_category_counts():
    assert len(ITEMS_BY_CATEGORY["FOODS"])     == 17
    assert len(ITEMS_BY_CATEGORY["HOBBIES"])   == 17
    assert len(ITEMS_BY_CATEGORY["HOUSEHOLD"]) == 16


def test_item_map_covers_all_items():
    assert len(ITEM_MAP) == 50


def _make_mock(qty):
    model  = MagicMock()
    scaler = MagicMock()
    model.predict.return_value = np.array([[qty]])
    scaler.transform.side_effect = lambda x: x
    return model, scaler


def test_zero_pct_change_gives_equal_revenues():
    with patch("inference.load_model", return_value=_make_mock(4.0)):
        result = predict("FOODS", "CA_1", 3, 0.0, "FOODS_1_001")
    assert result["baseline_revenue"] == result["scenario_revenue"]
    assert result["delta"] == 0.0


def test_positive_pct_increases_revenue():
    with patch("inference.load_model", return_value=_make_mock(4.0)):
        result = predict("FOODS", "CA_1", 3, 50.0, "FOODS_1_001")
    assert result["scenario_revenue"] > result["baseline_revenue"]
    assert result["baseline_qty"] < result["scenario_qty"]


def test_negative_pct_decreases_revenue():
    with patch("inference.load_model", return_value=_make_mock(4.0)):
        result = predict("FOODS", "CA_1", 3, -25.0, "FOODS_1_001")
    assert result["scenario_revenue"] < result["baseline_revenue"]
    assert result["delta"] < 0


def test_zero_model_output_gives_zero_revenues():
    with patch("inference.load_model", return_value=_make_mock(0.0)):
        result = predict("FOODS", "CA_1", 3, 100.0, "FOODS_1_001")
    assert result["baseline_revenue"] == 0.0
    assert result["scenario_revenue"] == 0.0