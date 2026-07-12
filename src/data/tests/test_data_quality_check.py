import pandas as pd

from tools.data_quality_check import (
    _count_poi_for_geometry,
    check_csv_or_excel,
    check_geojson,
    main,
)


def test_count_poi_for_geometry_uses_polygon_not_bbox():
    geometry = {
        "type": "Polygon",
        "coordinates": [[(0, 0), (1, 0), (0, 1), (0, 0)]],
    }
    bbox = {"min_lng": 0, "max_lng": 1, "min_lat": 0, "max_lat": 1}
    df_poi = pd.DataFrame(
        [
            {"Lng": 0.1, "Lat": 0.1},
            {"Lng": 0.9, "Lat": 0.9},
        ]
    )

    count, method, note = _count_poi_for_geometry(df_poi, geometry, bbox)

    assert count == 1
    assert method == "polygon"


def test_count_poi_for_geometry_empty_df():
    geometry = {
        "type": "Polygon",
        "coordinates": [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]],
    }
    bbox = {"min_lng": 0, "max_lng": 1, "min_lat": 0, "max_lat": 1}
    df_poi = pd.DataFrame()

    count, method, note = _count_poi_for_geometry(df_poi, geometry, bbox)
    assert count == 0
    assert note == "POI数据为空"


def test_check_csv_or_excel_missing_file(tmp_path):
    cfg = {"path": tmp_path / "nonexistent.csv", "required_cols": ["A"]}
    report = check_csv_or_excel("test", cfg)
    assert report["status"] == "MISSING"


def test_check_csv_or_excel_healthy(tmp_path):
    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame({"Name": ["a", "b"], "Lat": [43.9, 43.91], "Lng": [125.3, 125.31]})
    df.to_csv(csv_path, index=False)

    cfg = {"path": csv_path, "required_cols": ["Name", "Lat", "Lng"]}
    report = check_csv_or_excel("test", cfg)
    assert report["grade"] == "A"
    assert report["stats"]["rows"] == 2


def test_check_csv_or_excel_missing_column(tmp_path):
    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame({"Name": ["a"], "Lat": [43.9]})
    df.to_csv(csv_path, index=False)

    cfg = {"path": csv_path, "required_cols": ["Name", "Lat", "Lng"]}
    report = check_csv_or_excel("test", cfg)
    assert report["status"] == "WARNING"
    assert any("Lng" in issue for issue in report["issues"])


def test_main_returns_zero():
    """In a healthy project, main() should return 0."""
    result = main()
    assert result == 0
