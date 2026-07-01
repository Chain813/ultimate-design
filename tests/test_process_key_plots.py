import json
from importlib import import_module

import geopandas as gpd
import pytest
from shapely.geometry import box

from scripts.process_key_plots import main, process_key_plots
from src.data.data_categories import DATA_CATEGORIES
from src.engines.key_plot_engine import load_key_plots_from_geojson


def _write_gdf(path, geometries, records=None, crs="EPSG:4326"):
    records = records or [{} for _ in geometries]
    gdf = gpd.GeoDataFrame(records, geometry=geometries, crs=crs)
    gdf.to_file(path, driver="GeoJSON")
    return gdf


def _read_geojson(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _key_plots_category():
    return next(category for category in DATA_CATEGORIES if category["id"] == "key_plots")


def _category_tutorial_text(category):
    tutorial = category["tutorial"]
    methods = tutorial["methods"]
    pieces = [category["description"], category["format_desc"], tutorial["summary"], tutorial["sample_fields"]]
    for method in methods:
        pieces.extend([method["name"], method.get("code_example", ""), method.get("tip", "")])
        pieces.extend(method["steps"])
    return "\n".join(pieces)


def test_process_key_plots_clips_indexes_and_writes_geojson(tmp_path):
    input_path = tmp_path / "raw_plots.geojson"
    boundary_path = tmp_path / "boundary.geojson"
    output_path = tmp_path / "nested" / "Key_Plots_District.json"

    _write_gdf(
        input_path,
        [box(0.0, 0.0, 0.01, 0.01), box(0.02, 0.0, 0.03, 0.01)],
        [{"name": "门户更新单元", "role": "门户展示"}, {"role": "社区生活"}],
    )
    _write_gdf(boundary_path, [box(-0.01, -0.01, 0.04, 0.02)])

    count = process_key_plots(input_path, boundary_path, output_path)

    assert count == 2
    data = _read_geojson(output_path)
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 2
    assert [feature["properties"]["plot_index"] for feature in data["features"]] == [1, 2]
    assert [feature["properties"]["name"] for feature in data["features"]] == ["门户更新单元", "地块2"]
    assert data["features"][0]["properties"]["role"] == "门户展示"
    assert all(feature["properties"]["area_ha"] > 0 for feature in data["features"])

    loaded = load_key_plots_from_geojson(output_path)
    assert [plot.index for plot in loaded] == [1, 2]
    assert [plot.name for plot in loaded] == ["门户更新单元", "地块2"]
    assert all(plot.area_ha > 0 for plot in loaded)


def test_process_key_plots_preserves_source_fields_and_adds_compatibility_fields(tmp_path):
    input_path = tmp_path / "raw_plots.geojson"
    boundary_path = tmp_path / "boundary.geojson"
    output_path = tmp_path / "out.geojson"

    _write_gdf(
        input_path,
        [box(0.0, 0.0, 0.01, 0.01)],
        [{"name": "compat plot", "role": "legacy", "source_code": "SRC-001"}],
    )
    _write_gdf(boundary_path, [box(-0.01, -0.01, 0.02, 0.02)])

    count = process_key_plots(input_path, boundary_path, output_path)

    assert count == 1
    properties = _read_geojson(output_path)["features"][0]["properties"]
    assert properties["source_code"] == "SRC-001"
    assert properties["plot_index"] == 1
    assert properties["id"] == 1
    assert properties["OBJECTID"] == 1
    assert properties["Shape_Area"] > 0
    assert properties["Shape_Area"] == pytest.approx(properties["area_ha"] * 10000)


def test_process_key_plots_clips_partial_polygon_to_boundary(tmp_path):
    input_path = tmp_path / "raw_plots.geojson"
    boundary_path = tmp_path / "boundary.geojson"
    output_path = tmp_path / "out.geojson"

    source_gdf = _write_gdf(input_path, [box(0.0, 0.0, 2.0, 2.0)], [{"name": "partial"}])
    _write_gdf(boundary_path, [box(0.5, 0.5, 1.5, 1.5)])

    count = process_key_plots(input_path, boundary_path, output_path)

    assert count == 1
    output_gdf = gpd.read_file(output_path)
    assert tuple(round(value, 6) for value in output_gdf.total_bounds) == (0.5, 0.5, 1.5, 1.5)
    assert output_gdf.geometry.iloc[0].area < source_gdf.geometry.iloc[0].area


def test_process_key_plots_writes_empty_geojson_when_boundary_is_disjoint(tmp_path):
    input_path = tmp_path / "raw_plots.geojson"
    boundary_path = tmp_path / "boundary.geojson"
    output_path = tmp_path / "out.geojson"

    _write_gdf(input_path, [box(0.0, 0.0, 1.0, 1.0)], [{"name": "outside"}])
    _write_gdf(boundary_path, [box(10.0, 10.0, 11.0, 11.0)])

    count = process_key_plots(input_path, boundary_path, output_path)

    assert count == 0
    assert output_path.exists()
    assert _read_geojson(output_path)["features"] == []


def test_process_key_plots_writes_empty_geojson_when_boundary_has_no_features(tmp_path):
    input_path = tmp_path / "raw_plots.geojson"
    boundary_path = tmp_path / "empty_boundary.geojson"
    output_path = tmp_path / "out.geojson"

    _write_gdf(input_path, [box(0.0, 0.0, 1.0, 1.0)], [{"name": "unclipped"}])
    boundary_path.write_text('{"type": "FeatureCollection", "features": []}', encoding="utf-8")

    count = process_key_plots(input_path, boundary_path, output_path)

    assert count == 0
    assert output_path.exists()
    assert _read_geojson(output_path)["features"] == []


def test_process_key_plots_reprojects_boundary_to_plot_crs(tmp_path):
    input_path = tmp_path / "raw_plots.geojson"
    boundary_path = tmp_path / "boundary.geojson"
    output_path = tmp_path / "out.geojson"

    plot_wgs84 = gpd.GeoDataFrame(
        [{"name": "projected clip"}],
        geometry=[box(0.0, 0.0, 0.02, 0.02)],
        crs="EPSG:4326",
    )
    plot_projected = plot_wgs84.to_crs("EPSG:3857")
    plot_projected.to_file(input_path, driver="GeoJSON")
    _write_gdf(boundary_path, [box(0.005, 0.005, 0.015, 0.015)], crs="EPSG:4326")

    count = process_key_plots(input_path, boundary_path, output_path)

    assert count == 1
    output_gdf = gpd.read_file(output_path)
    assert output_gdf.crs.to_epsg() == 4326
    minx, miny, maxx, maxy = output_gdf.total_bounds
    assert 0.0049 <= minx <= 0.0051
    assert 0.0049 <= miny <= 0.0051
    assert 0.0149 <= maxx <= 0.0151
    assert 0.0149 <= maxy <= 0.0151


def test_process_key_plots_uses_geodesic_area_fallback_without_web_mercator(tmp_path, monkeypatch):
    module = import_module("scripts.process_key_plots")
    input_path = tmp_path / "raw_plots.geojson"
    boundary_path = tmp_path / "boundary.geojson"
    output_path = tmp_path / "out.geojson"

    _write_gdf(input_path, [box(0.0, 0.0, 0.01, 0.01)], [{"name": "geodesic fallback"}])
    _write_gdf(boundary_path, [box(-0.01, -0.01, 0.02, 0.02)])
    monkeypatch.setattr(module, "_estimated_utm_crs", lambda _: None)

    original_to_crs = gpd.GeoDataFrame.to_crs

    def reject_web_mercator(self, crs=None, epsg=None, *args, **kwargs):
        target = f"EPSG:{epsg}" if epsg is not None else str(crs)
        if target.upper() == "EPSG:3857":
            raise AssertionError("EPSG:3857 must not be used for area fallback")
        return original_to_crs(self, crs=crs, epsg=epsg, *args, **kwargs)

    monkeypatch.setattr(gpd.GeoDataFrame, "to_crs", reject_web_mercator)

    count = process_key_plots(input_path, boundary_path, output_path)

    assert count == 1
    assert _read_geojson(output_path)["features"][0]["properties"]["area_ha"] > 0


def test_write_geojson_preserves_existing_output_when_non_empty_write_fails(tmp_path, monkeypatch):
    module = import_module("scripts.process_key_plots")
    output_path = tmp_path / "out.geojson"
    old_content = '{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"old": true}}]}'
    output_path.write_text(old_content, encoding="utf-8")
    gdf = gpd.GeoDataFrame([{"name": "new"}], geometry=[box(0.0, 0.0, 0.01, 0.01)], crs="EPSG:4326")

    def fail_to_file(self, *args, **kwargs):
        raise RuntimeError("simulated write failure")

    monkeypatch.setattr(gpd.GeoDataFrame, "to_file", fail_to_file)

    with pytest.raises(RuntimeError, match="simulated write failure"):
        module._write_geojson(gdf, output_path)

    assert output_path.read_text(encoding="utf-8") == old_content


def test_process_key_plots_main_prints_processed_message(tmp_path, capsys):
    input_path = tmp_path / "raw_plots.geojson"
    boundary_path = tmp_path / "boundary.geojson"
    output_path = tmp_path / "out.geojson"

    _write_gdf(input_path, [box(0.0, 0.0, 0.01, 0.01)], [{"name": "cli plot"}])
    _write_gdf(boundary_path, [box(-0.01, -0.01, 0.02, 0.02)])

    exit_code = main(["--input", str(input_path), "--boundary", str(boundary_path), "--output", str(output_path)])

    assert exit_code == 0
    assert output_path.exists()
    assert "Processed 1 key plot feature" in capsys.readouterr().out


def test_key_plots_category_describes_dynamic_processing_script():
    category = _key_plots_category()
    category_text = _category_tutorial_text(category)

    assert "5 个 Polygon" not in category_text
    assert "5 个重点" not in category_text
    assert "scripts/process_key_plots.py" in category_text
    assert "GeoJSON FeatureCollection (N 个 Polygon / MultiPolygon 要素)" in category["format_desc"]
    assert "plot_index" in category["tutorial"]["sample_fields"]
    assert "name" in category["tutorial"]["sample_fields"]
    assert "role" in category["tutorial"]["sample_fields"]


def test_process_key_plots_module_exports_required_function():
    module = import_module("scripts.process_key_plots")

    assert module.process_key_plots is process_key_plots
