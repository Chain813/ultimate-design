import json
from importlib import import_module
from pathlib import Path
from typing import get_type_hints

import pytest


def _engine():
    try:
        return import_module("src.engines.key_plot_engine")
    except ModuleNotFoundError as exc:
        pytest.fail(f"key plot engine module is missing: {exc}")


def _write_three_plot_geojson(path):
    features = [
        {
            "type": "Feature",
            "id": "plot-a",
            "properties": {"name": "门户更新单元", "role": "门户展示"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [125.3400, 43.9000],
                        [125.3410, 43.9000],
                        [125.3410, 43.9010],
                        [125.3400, 43.9010],
                        [125.3400, 43.9000],
                    ]
                ],
            },
        },
        {
            "type": "Feature",
            "properties": {"OBJECTID": 102, "Name": "滨水活力单元", "type": "产业服务"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [125.3420, 43.9000],
                        [125.3432, 43.9000],
                        [125.3432, 43.9012],
                        [125.3420, 43.9012],
                        [125.3420, 43.9000],
                    ]
                ],
            },
        },
        {
            "type": "Feature",
            "properties": {"plot_name": "街区织补单元", "category": "社区生活"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [125.3440, 43.9000],
                        [125.3454, 43.9000],
                        [125.3454, 43.9014],
                        [125.3440, 43.9014],
                        [125.3440, 43.9000],
                    ]
                ],
            },
        },
    ]
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False),
        encoding="utf-8",
    )


def _valid_polygon_feature(name="valid plot"):
    return {
        "type": "Feature",
        "properties": {"name": name},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [125.3400, 43.9000],
                    [125.3410, 43.9000],
                    [125.3410, 43.9010],
                    [125.3400, 43.9010],
                    [125.3400, 43.9000],
                ]
            ],
        },
    }


def _write_feature_collection(path, features):
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False),
        encoding="utf-8",
    )


def test_suffixes_are_canonical_and_ordered():
    engine = _engine()

    assert engine.KEY_PLOT_DRAWING_SUFFIXES == [
        "现状问题图",
        "更新定位图",
        "平面深化图",
        "AIGC推演效果图",
        "人视效果图",
        "建筑更新图",
        "街道断面图",
        "改造前后对比图",
        "运营场景图",
    ]


def test_load_key_plots_from_geojson_returns_ordered_plot_metadata(tmp_path):
    engine = _engine()
    geojson_path = tmp_path / "plots.geojson"
    _write_three_plot_geojson(geojson_path)

    plots = engine.load_key_plots_from_geojson(geojson_path)

    assert [plot.index for plot in plots] == [1, 2, 3]
    assert [plot.name for plot in plots] == ["门户更新单元", "滨水活力单元", "街区织补单元"]
    assert [plot.role for plot in plots] == ["门户展示", "产业服务", "社区生活"]
    assert all(plot.area_ha > 0 for plot in plots)
    assert all(plot.centroid is not None for plot in plots)


def test_load_key_plot_geometries_from_geojson_returns_paired_metadata_and_wgs84_geometry(tmp_path):
    engine = _engine()
    from shapely.geometry import Point

    geojson_path = tmp_path / "paired-plots.geojson"
    features = [
        {
            "type": "Feature",
            "properties": {"id": "west", "name": "West Plot"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0.0, 0.0], [0.01, 0.0], [0.01, 0.01], [0.0, 0.01], [0.0, 0.0]]],
            },
        },
        {
            "type": "Feature",
            "properties": {"id": "east", "name": "East Plot"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0.02, 0.0], [0.03, 0.0], [0.03, 0.01], [0.02, 0.01], [0.02, 0.0]]],
            },
        },
    ]
    _write_feature_collection(geojson_path, features)

    paired = engine.load_key_plot_geometries_from_geojson(geojson_path)

    assert [item.plot.plot_id for item in paired] == ["west", "east"]
    assert [item.plot.name for item in paired] == ["West Plot", "East Plot"]
    assert paired[0].geometry.covers(Point(0.005, 0.005))
    assert not paired[0].geometry.covers(Point(0.025, 0.005))
    assert paired[1].geometry.covers(Point(0.025, 0.005))


def test_normalize_key_plot_name_replaces_numbered_plot_prefixes():
    engine = _engine()

    assert engine.normalize_key_plot_name("地块7街道断面图") == "重点地块街道断面图"
    assert engine.normalize_key_plot_name("地块12AIGC推演效果图") == "重点地块AIGC推演效果图"


def test_build_key_plot_drawing_names_expands_each_plot_to_nine_names(tmp_path):
    engine = _engine()
    geojson_path = tmp_path / "plots.geojson"
    _write_three_plot_geojson(geojson_path)
    plots = engine.load_key_plots_from_geojson(geojson_path)

    names = engine.build_key_plot_drawing_names(plots)

    assert len(names) == 27
    assert "地块1现状问题图" in names
    assert "地块3运营场景图" in names
    assert "地块4现状问题图" not in names


def test_format_key_plot_context_includes_count_names_roles_and_area():
    engine = _engine()
    plots = [
        engine.KeyPlot(index=1, plot_id="plot-a", name="门户更新单元", role="门户展示", area_ha=2.5),
        engine.KeyPlot(index=2, plot_id="plot-b", name="滨水活力单元", role="产业服务", area_ha=3.25),
    ]

    context = engine.format_key_plot_context(plots)

    assert "共 2 个重点更新单元" in context
    assert "地块1：门户更新单元" in context
    assert "门户展示" in context
    assert "2.50 ha" in context
    assert "地块2：滨水活力单元" in context


def test_format_key_plot_context_explains_missing_plot_boundaries():
    engine = _engine()

    context = engine.format_key_plot_context([])

    assert "重点更新单元尚未配置" in context
    assert "上传" in context
    assert "地块边界" in context


def test_load_key_plots_from_geojson_missing_file_returns_empty_list(tmp_path):
    engine = _engine()

    assert engine.load_key_plots_from_geojson(tmp_path / "missing.geojson") == []


def test_load_key_plots_from_geojson_uses_index_property_for_plot_id(tmp_path):
    engine = _engine()
    geojson_path = tmp_path / "plot-with-index.geojson"
    feature = {
        "type": "Feature",
        "properties": {"index": "plot-index-value", "name": "索引地块"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [125.3400, 43.9000],
                    [125.3410, 43.9000],
                    [125.3410, 43.9010],
                    [125.3400, 43.9010],
                    [125.3400, 43.9000],
                ]
            ],
        },
    }
    geojson_path.write_text(
        json.dumps({"type": "FeatureCollection", "features": [feature]}, ensure_ascii=False),
        encoding="utf-8",
    )

    loaded = engine.load_key_plots_from_geojson(geojson_path)

    assert loaded[0].plot_id == "plot-index-value"


def test_load_key_plots_from_geojson_corrupt_file_raises_typed_error(tmp_path):
    engine = _engine()
    corrupt_path = tmp_path / "corrupt.geojson"
    corrupt_path.write_text("{not valid geojson", encoding="utf-8")

    assert hasattr(engine, "KeyPlotLoadError")
    with pytest.raises(engine.KeyPlotLoadError):
        engine.load_key_plots_from_geojson(corrupt_path)


def test_load_key_plots_from_geojson_object_without_feature_collection_raises_typed_error(tmp_path):
    engine = _engine()
    malformed_path = tmp_path / "object.geojson"
    malformed_path.write_text("{}", encoding="utf-8")

    with pytest.raises(engine.KeyPlotLoadError):
        engine.load_key_plots_from_geojson(malformed_path)


def test_load_key_plots_from_geojson_feature_collection_without_features_raises_typed_error(tmp_path):
    engine = _engine()
    malformed_path = tmp_path / "missing-features.geojson"
    malformed_path.write_text(json.dumps({"type": "FeatureCollection"}), encoding="utf-8")

    with pytest.raises(engine.KeyPlotLoadError):
        engine.load_key_plots_from_geojson(malformed_path)


def test_load_key_plots_from_geojson_feature_collection_with_non_list_features_raises_typed_error(tmp_path):
    engine = _engine()
    malformed_path = tmp_path / "non-list-features.geojson"
    malformed_path.write_text(
        json.dumps({"type": "FeatureCollection", "features": {}}),
        encoding="utf-8",
    )

    with pytest.raises(engine.KeyPlotLoadError):
        engine.load_key_plots_from_geojson(malformed_path)


def test_load_key_plots_from_geojson_empty_feature_collection_returns_empty_list(tmp_path):
    engine = _engine()
    empty_path = tmp_path / "empty.geojson"
    empty_path.write_text(
        json.dumps({"type": "FeatureCollection", "features": []}),
        encoding="utf-8",
    )

    assert engine.load_key_plots_from_geojson(empty_path) == []


def test_load_key_plots_from_geojson_feature_missing_geometry_raises_typed_error(tmp_path):
    engine = _engine()
    missing_geometry_path = tmp_path / "missing-geometry.geojson"
    feature = {"type": "Feature", "properties": {"name": "missing geometry"}}
    _write_feature_collection(missing_geometry_path, [feature])

    with pytest.raises(engine.KeyPlotLoadError):
        engine.load_key_plots_from_geojson(missing_geometry_path)


def test_load_key_plots_from_geojson_feature_null_geometry_raises_typed_error(tmp_path):
    engine = _engine()
    null_geometry_path = tmp_path / "null-geometry.geojson"
    feature = {"type": "Feature", "properties": {"name": "null geometry"}, "geometry": None}
    _write_feature_collection(null_geometry_path, [feature])

    with pytest.raises(engine.KeyPlotLoadError):
        engine.load_key_plots_from_geojson(null_geometry_path)


def test_load_key_plots_from_geojson_feature_empty_polygon_raises_typed_error(tmp_path):
    engine = _engine()
    empty_polygon_path = tmp_path / "empty-polygon.geojson"
    feature = {
        "type": "Feature",
        "properties": {"name": "empty polygon"},
        "geometry": {"type": "Polygon", "coordinates": []},
    }
    _write_feature_collection(empty_polygon_path, [feature])

    with pytest.raises(engine.KeyPlotLoadError):
        engine.load_key_plots_from_geojson(empty_polygon_path)


def test_load_key_plots_from_geojson_mixed_valid_and_invalid_geometry_raises_typed_error(tmp_path):
    engine = _engine()
    mixed_path = tmp_path / "mixed-invalid.geojson"
    features = [
        _valid_polygon_feature("valid plot"),
        {"type": "Feature", "properties": {"name": "missing geometry"}},
        {"type": "Feature", "properties": {"name": "null geometry"}, "geometry": None},
        {
            "type": "Feature",
            "properties": {"name": "empty polygon"},
            "geometry": {"type": "Polygon", "coordinates": []},
        },
    ]
    _write_feature_collection(mixed_path, features)

    with pytest.raises(engine.KeyPlotLoadError):
        engine.load_key_plots_from_geojson(mixed_path)


def test_load_key_plots_from_geojson_uses_geodesic_area_fallback_when_utm_unavailable(tmp_path, monkeypatch):
    engine = _engine()
    geojson_path = tmp_path / "plots.geojson"
    _write_three_plot_geojson(geojson_path)

    import geopandas as gpd

    original_to_crs = gpd.GeoDataFrame.to_crs

    def no_estimated_utm(self, *args, **kwargs):
        return None

    def reject_web_mercator(self, crs=None, epsg=None, *args, **kwargs):
        target = f"EPSG:{epsg}" if epsg is not None else str(crs)
        if target.upper() == "EPSG:3857":
            raise AssertionError("EPSG:3857 must not be used for area fallback")
        return original_to_crs(self, crs=crs, epsg=epsg, *args, **kwargs)

    monkeypatch.setattr(gpd.GeoDataFrame, "estimate_utm_crs", no_estimated_utm)
    monkeypatch.setattr(gpd.GeoDataFrame, "to_crs", reject_web_mercator)

    loaded = engine.load_key_plots_from_geojson(geojson_path)

    assert loaded
    assert all(plot.area_ha > 0 for plot in loaded)


def test_load_key_plots_from_geojson_geodesic_area_fallback_matches_known_small_polygon(tmp_path, monkeypatch):
    engine = _engine()
    geojson_path = tmp_path / "equator.geojson"
    feature = {
        "type": "Feature",
        "properties": {"name": "equator plot"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [0.0, 0.0],
                    [0.01, 0.0],
                    [0.01, 0.01],
                    [0.0, 0.01],
                    [0.0, 0.0],
                ]
            ],
        },
    }
    _write_feature_collection(geojson_path, [feature])

    import geopandas as gpd

    monkeypatch.setattr(gpd.GeoDataFrame, "estimate_utm_crs", lambda self, *args, **kwargs: None)

    loaded = engine.load_key_plots_from_geojson(geojson_path)

    assert 120 <= loaded[0].area_ha <= 126


def test_load_key_plots_from_geojson_accepts_str_or_path_annotation():
    engine = _engine()

    hints = get_type_hints(engine.load_key_plots_from_geojson)

    assert hints["path"] == str | Path


def test_plot_names_returns_loaded_names(tmp_path):
    engine = _engine()
    geojson_path = tmp_path / "plots.geojson"
    _write_three_plot_geojson(geojson_path)
    plots = engine.load_key_plots_from_geojson(geojson_path)

    assert engine.plot_names(plots) == ["门户更新单元", "滨水活力单元", "街区织补单元"]
