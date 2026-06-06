import os
import sys

import numpy as np
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../api"))

from inference import build_feature_vector, predict


def test_feature_vector_has_18_features():
    vec = build_feature_vector("FOODS", "CA_1", 3)
    assert vec.shape == (1, 18)


def test_feature_vector_encodes_month():
    vec = build_feature_vector("FOODS", "CA_1", 7)
    assert vec[0, 6] == 7  # month is at index 6 in the feature list


def test_feature_vector_encodes_category():
    vec_foods   = build_feature_vector("FOODS",   "CA_1", 1)
    vec_hobbies = build_feature_vector("HOBBIES", "CA_1", 1)
    assert vec_foods[0, 0] != vec_hobbies[0, 0]


def _make_mock(qty):
    model  = MagicMock()
    scaler = MagicMock()
    model.predict.return_value = np.array([[qty]])
    scaler.transform.side_effect = lambda x: x
    return model, scaler


def test_zero_pct_change_gives_equal_revenues():
    with patch("inference.load_model", return_value=_make_mock(4.0)):
        result = predict("FOODS", "CA_1", 3, 0.0)
    assert result["baseline_revenue"] == result["scenario_revenue"]
    assert result["delta"] == 0.0


def test_positive_pct_increases_revenue():
    with patch("inference.load_model", return_value=_make_mock(4.0)):
        result = predict("FOODS", "CA_1", 3, 50.0)
    assert result["scenario_revenue"] > result["baseline_revenue"]
    assert result["delta"] > 0


def test_negative_pct_decreases_revenue():
    with patch("inference.load_model", return_value=_make_mock(4.0)):
        result = predict("FOODS", "CA_1", 3, -25.0)
    assert result["scenario_revenue"] < result["baseline_revenue"]
    assert result["delta"] < 0


def test_zero_model_output_gives_zero_revenues():
    with patch("inference.load_model", return_value=_make_mock(0.0)):
        result = predict("FOODS", "CA_1", 3, 100.0)
    assert result["baseline_revenue"] == 0.0
    assert result["scenario_revenue"] == 0.0