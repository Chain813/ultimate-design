import sys
sys.modules.setdefault("streamlit", type(sys)("streamlit_mock"))

from src.engines.spatial_engine import get_skyline_features


def test_get_skyline_features_returns_dict_with_expected_keys():
    features = get_skyline_features()
    assert isinstance(features, dict)
    for key in ("max_height", "avg_height", "high_rise_ratio", "building_count"):
        assert key in features


def test_get_skyline_features_values_are_numeric():
    features = get_skyline_features()
    assert isinstance(features["max_height"], (int, float))
    assert isinstance(features["avg_height"], (int, float))
    assert isinstance(features["high_rise_ratio"], (int, float))
    assert isinstance(features["building_count"], (int, float))


def test_get_skyline_features_empty_when_files_missing(monkeypatch):
    """Should return zeros when data files are absent."""
    monkeypatch.setattr(
        "src.engines.spatial_engine.resolve_path",
        lambda x: type(sys)("Path")(x),
    )
    features = get_skyline_features()
    assert features["building_count"] == 0
    assert features["max_height"] == 0
