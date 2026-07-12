import warnings
import sys
sys.modules.setdefault("streamlit", type(sys)("streamlit_mock"))

import geopandas as gpd
from shapely.geometry import Polygon

from src.engines.spatial_engine import get_skyline_features, _filter_buildings_within_boundary


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


def test_filter_buildings_within_boundary_projects_before_centroid():
    buildings = gpd.GeoDataFrame(
        {"id": [1, 2]},
        geometry=[
            Polygon([(125.351, 43.911), (125.352, 43.911), (125.352, 43.912), (125.351, 43.912)]),
            Polygon([(125.38, 43.94), (125.381, 43.94), (125.381, 43.941), (125.38, 43.941)]),
        ],
        crs="EPSG:4326",
    )
    boundary = gpd.GeoDataFrame(
        geometry=[
            Polygon([(125.35, 43.91), (125.353, 43.91), (125.353, 43.913), (125.35, 43.913)])
        ],
        crs="EPSG:4326",
    )

    with warnings.catch_warnings(record=True) as caught:
        filtered = _filter_buildings_within_boundary(buildings, boundary)

    assert filtered["id"].tolist() == [1]
    assert not any("geographic CRS" in str(item.message) for item in caught)
