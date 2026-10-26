"""Unit and integration tests for the Custom Site & Digital Twin Split-Brain Elimination Pipeline.

Verifies:
1. OSMDataFetcher standardized GeoJSON outputs (Boundary_Scope, Building_Footprints, road_clipped, landuse_clipped, Key_Plots_District).
2. site_diagnostic_engine geodesic area calculation and Polygon/MultiPolygon safety when Shape_Area is missing.
3. spatial_syntax_engine vectorized Floyd-Warshall speed, dynamic metric building area, and dynamic microclimate site_area_m2.
4. spatial_engine lowercase/uppercase landuse legend, multi-column skyline height, and custom site HUD statistics.
5. site_ingestion_panel activation, backup, one-click restoration, title parameter, and RAG document ingestion.
6. digital_twin cache-busting static URLs and custom_site viewport center synchronization.
"""

import json
import os
import time
from pathlib import Path

import geopandas as gpd
import pytest
import streamlit as st
from shapely.geometry import LineString, MultiPolygon, Polygon, box

from src.engines.osm_fetcher import OSMDataFetcher
from src.engines.site_diagnostic_engine import get_plot_diagnostics
from src.engines.spatial_engine import (
    _calc_boundary_ha,
    get_hud_statistics,
    get_landuse_legend,
    get_skyline_features,
)
from src.engines.spatial_syntax_engine import SpatialSyntaxEngine
from src.ui.digital_twin import _versioned_static_url, get_map_viewport
from src.ui.site_ingestion_panel import (
    activate_custom_site_files,
    ingest_custom_rag_document,
    parse_geojson_data,
    render_site_ingestion_panel,
    restore_default_changchun_site,
    save_mode_a_files,
)


def test_osm_fetcher_standardized_files(tmp_path):
    """Verify OSMDataFetcher generates all 6 standardized files with required schema fields."""
    fetcher = OSMDataFetcher(timeout=2)
    gdfs = fetcher._generate_fallback_gdfs(
        min_lat=30.650,
        min_lon=104.060,
        max_lat=30.660,
        max_lon=104.070,
        utm_crs="EPSG:32648",
        output_dir=str(tmp_path),
    )

    expected_files = [
        "Boundary_Scope.geojson",
        "Building_Footprints.geojson",
        "road_network_clipped.geojson",
        "road_clipped.geojson",
        "landuse_clipped.geojson",
        "Key_Plots_District.json",
    ]
    for fname in expected_files:
        fpath = tmp_path / fname
        assert fpath.exists(), f"Missing expected output file: {fname}"

    # Verify Boundary_Scope.geojson
    boundary_geo = json.loads((tmp_path / "Boundary_Scope.geojson").read_text(encoding="utf-8"))
    b_props = boundary_geo["features"][0]["properties"]
    assert b_props["Shape_Area"] > 0
    assert b_props["area_ha"] > 0

    # Verify Building_Footprints.geojson
    bldg_gdf = gdfs["buildings"]
    assert "building_id" in bldg_gdf.columns
    assert "Floor" in bldg_gdf.columns
    assert "height" in bldg_gdf.columns
    assert "area_m2" in bldg_gdf.columns
    assert "Shape_Area" in bldg_gdf.columns
    assert (bldg_gdf["Shape_Area"] > 0).all()

    # Verify landuse_clipped.geojson has both lowercase and uppercase standard fields
    lu_gdf = gdfs["landuse"]
    for col in ("type", "color", "Type", "Color", "GB_Code", "Shape_Area"):
        assert col in lu_gdf.columns
    assert (lu_gdf["Shape_Area"] > 0).all()
    assert any(t in ["居住用地", "商业服务业设施用地", "绿地与广场用地", "公共管理与公共服务用地", "工业用地"] for t in lu_gdf["Type"])

    # Verify Key_Plots_District.json
    plots_geo = json.loads((tmp_path / "Key_Plots_District.json").read_text(encoding="utf-8"))
    assert 3 <= len(plots_geo["features"]) <= 5
    for feat in plots_geo["features"]:
        p = feat["properties"]
        assert p.get("Name") and p.get("name")
        assert p.get("Type")
        assert p.get("Shape_Area", 0) > 0
        assert p.get("area_ha", 0) > 0
        assert "FAR" in p and "poi" in p and "gvi" in p and "svf" in p


def test_site_diagnostic_engine_polygon_and_multipolygon_without_shape_area(tmp_path, monkeypatch):
    """Verify get_plot_diagnostics computes geodesic area for Polygon and MultiPolygon lacking Shape_Area."""
    poly = Polygon([
        (114.300, 30.500),
        (114.305, 30.500),
        (114.305, 30.505),
        (114.300, 30.505),
        (114.300, 30.500),
    ])
    mpoly = MultiPolygon([
        Polygon([
            (114.310, 30.500),
            (114.314, 30.500),
            (114.314, 30.504),
            (114.310, 30.504),
            (114.310, 30.500),
        ]),
        Polygon([
            (114.315, 30.500),
            (114.318, 30.500),
            (114.318, 30.503),
            (114.315, 30.503),
            (114.315, 30.500),
        ]),
    ])

    custom_plots_file = tmp_path / "Key_Plots_District.json"
    fc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"Name": "无Shape_Area单多边形地块", "poi": 22, "gvi": 18.5, "svf": 0.58},
                "geometry": json.loads(gpd.GeoSeries([poly]).to_json())["features"][0]["geometry"],
            },
            {
                "type": "Feature",
                "properties": {"Name": "无Shape_Area复合多边形地块", "poi": 15, "gvi": 24.0, "svf": 0.62},
                "geometry": json.loads(gpd.GeoSeries([mpoly]).to_json())["features"][0]["geometry"],
            },
        ],
    }
    custom_plots_file.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setitem(
        __import__("src.engines.site_diagnostic_engine", fromlist=["SHP_FILES"]).SHP_FILES,
        "plots",
        custom_plots_file,
    )
    if hasattr(get_plot_diagnostics, "clear"):
        get_plot_diagnostics.clear()

    diags = get_plot_diagnostics()
    assert len(diags) == 2
    assert diags[0]["name"] == "无Shape_Area单多边形地块"
    assert diags[0]["area_ha"] > 10.0  # ~500m x 550m > 20 ha
    assert diags[0]["mpi_score"] > 0.0
    assert diags[1]["name"] == "无Shape_Area复合多边形地块"
    assert diags[1]["area_ha"] > 10.0
    assert diags[1]["mpi_score"] > 0.0


def test_spatial_syntax_engine_vectorized_speed_and_dynamic_area():
    """Verify SpatialSyntaxEngine vectorized Floyd-Warshall speed and dynamic metric area calculation."""
    engine = SpatialSyntaxEngine()

    # Build a 60-segment grid road network
    lines = []
    for i in range(30):
        lines.append({"id": i, "geometry": LineString([(120.0 + i * 0.001, 30.0), (120.0 + i * 0.001, 30.03)])})
    for j in range(30):
        lines.append({"id": 30 + j, "geometry": LineString([(120.0, 30.0 + j * 0.001), (120.03, 30.0 + j * 0.001)])})
    roads_gdf = gpd.GeoDataFrame(lines, crs="EPSG:4326")

    t0 = time.perf_counter()
    res = engine.analyze_network_syntax(roads_gdf)
    elapsed = time.perf_counter() - t0

    assert elapsed < 1.5, f"Vectorized syntax analysis took too long: {elapsed:.2f}s"
    assert "Integration" in res.columns
    assert "Choice" in res.columns
    assert "integration_norm" in res.columns
    assert (res["Integration"] > 0).all()

    # Test compute_momepy_morphometrics without 'area_m2' column on geographic WGS84 buildings
    b1 = box(120.001, 30.001, 120.0015, 30.0015)  # ~48m x 55m ~= 2650 m2 (NOT hardcoded 400.0)
    b2 = box(120.003, 30.003, 120.0035, 30.0035)
    buildings_gdf = gpd.GeoDataFrame(
        [{"geometry": b1, "Floor": 6}, {"geometry": b2, "Floor": 10}],
        crs="EPSG:4326",
    )
    morpho = engine.compute_momepy_morphometrics(buildings_gdf)
    assert morpho["BCR"] > 0
    assert morpho["FAR"] > 0
    assert morpho["site_area_m2"] != 1702000.0

    # Test evaluate_microclimate dynamic site_area_m2
    mc = engine.evaluate_microclimate(buildings_gdf)
    assert mc["site_area_m2"] != 1702000.0
    assert mc["site_area_m2"] > 1000.0


def test_site_ingestion_activate_and_restore(tmp_path):
    """Verify activate_custom_site_files backs up original files, syncs custom site, and restores cleanly."""
    mock_gis = tmp_path / "gis"
    mock_static = tmp_path / "static"
    mock_backup = tmp_path / "backup_changchun_default"
    mock_custom = tmp_path / "custom_site"
    mock_py = tmp_path / "project.yaml"
    mock_cfg = tmp_path / "custom_site.json"

    mock_gis.mkdir()
    mock_static.mkdir()

    # Seed mock Changchun files
    orig_boundary = '{"type": "FeatureCollection", "name": "changchun_orig", "features": []}'
    (mock_gis / "Boundary_Scope.geojson").write_text(orig_boundary, encoding="utf-8")
    (mock_gis / "Key_Plots_District.json").write_text(orig_boundary, encoding="utf-8")
    (mock_gis / "Building_Footprints.geojson").write_text(orig_boundary, encoding="utf-8")
    (mock_gis / "road_clipped.geojson").write_text(orig_boundary, encoding="utf-8")
    (mock_gis / "landuse_clipped.geojson").write_text(orig_boundary, encoding="utf-8")
    (mock_static / "buildings.geojson").write_text(orig_boundary, encoding="utf-8")
    (mock_static / "landuse.geojson").write_text(orig_boundary, encoding="utf-8")
    (mock_static / "road_clipped.geojson").write_text(orig_boundary, encoding="utf-8")
    (mock_static / "boundary.geojson").write_text(orig_boundary, encoding="utf-8")
    mock_py.write_text("project:\n  name: 长春默认项目\nsite:\n  city: 长春市\n  name: 伪满皇宫\n", encoding="utf-8")

    # Mode A upload simulation
    sample_geo = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "苏州平江历史街区地块"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[120.62, 31.31], [120.63, 31.31], [120.63, 31.32], [120.62, 31.32], [120.62, 31.31]]],
                },
            }
        ],
    }
    parsed = parse_geojson_data(sample_geo)
    parsed["city"] = "苏州市"
    parsed["name"] = "平江历史文化街区"

    save_mode_a_files(parsed, custom_dir=mock_custom, auto_fetch_osm=False)
    mock_cfg.write_text(json.dumps(parsed, ensure_ascii=False), encoding="utf-8")

    # Activate custom site
    synced = activate_custom_site_files(
        custom_dir=mock_custom,
        site_context=parsed,
        gis_dir=mock_gis,
        static_dir=mock_static,
        backup_dir=mock_backup,
        project_yaml_path=mock_py,
    )
    assert "gis/Boundary_Scope.geojson" in synced
    assert "static/buildings.geojson" in synced
    assert (mock_backup / "Boundary_Scope.geojson").exists()
    assert "苏州平江历史街区地块" in (mock_gis / "Key_Plots_District.json").read_text(encoding="utf-8")
    assert "苏州市" in mock_py.read_text(encoding="utf-8")

    # Restore default Changchun site
    restore_default_changchun_site(
        backup_dir=mock_backup,
        gis_dir=mock_gis,
        static_dir=mock_static,
        project_yaml_path=mock_py,
        custom_config_path=mock_cfg,
    )
    assert not mock_cfg.exists()
    assert "changchun_orig" in (mock_gis / "Boundary_Scope.geojson").read_text(encoding="utf-8")
    assert "长春市" in mock_py.read_text(encoding="utf-8")


def test_render_site_ingestion_panel_accepts_title_and_rag_doc(tmp_path, monkeypatch):
    """Verify render_site_ingestion_panel accepts title=... and ingest_custom_rag_document updates stage_bus."""
    custom_rag_file = tmp_path / "custom_rag_knowledge.json"
    monkeypatch.setattr(
        "src.engines.rag_engine.resolve_path",
        lambda p: custom_rag_file if "custom_rag" in str(p) else p,
    )
    render_site_ingestion_panel(title="🏛️ 自定义测试标题")

    txt = ingest_custom_rag_document("test_taskbook.md", "## 规划设计任务书\n总用地面积 45 公顷，容积率上限 2.2。".encode("utf-8"))
    assert "45 公顷" in txt
    assert st.session_state.get("stage_bus", {}).get("01.project_info") == txt


def test_digital_twin_cache_bust_and_viewport(monkeypatch):
    """Verify digital_twin _versioned_static_url appends ?v= and get_map_viewport uses custom_site center."""
    url = _versioned_static_url("buildings.geojson")
    assert "/app/static/buildings.geojson?v=" in url

    st.session_state["custom_site_context"] = {
        "city": "杭州市",
        "name": "西湖文化广场片区",
        "center": [120.165, 30.275],
    }
    vp = get_map_viewport()
    assert vp["center"] == [120.165, 30.275]
    st.session_state["custom_site_context"] = {}


def test_spatial_engine_hardening(tmp_path, monkeypatch):
    """Verify spatial_engine supports lowercase landuse legend, multi-column heights, and custom site boundary_ha."""
    st.session_state["custom_site_context"] = {
        "city": "成都市",
        "name": "东郊记忆更新区",
        "center": [104.12, 30.67],
        "bbox": [104.11, 30.66, 104.13, 30.68],
        "area_ha": 42.8,
        "plots": [{"name": "核心区", "poi": 28}],
    }
    ha = _calc_boundary_ha(str(tmp_path / "non_existent_boundary.geojson"))
    assert ha == 42.8

    if hasattr(get_hud_statistics, "clear"):
        get_hud_statistics.clear()
    hud = get_hud_statistics()
    assert hud["boundary_ha"] == 42.8
    assert hud["poi_count"] == 28

    # Lowercase landuse columns with RGB list color
    lu_gdf = gpd.GeoDataFrame(
        [
            {"type": "residential", "color": [255, 255, 0], "gb_code": "R", "geometry": box(104.11, 30.66, 104.12, 30.67)},
            {"type": "park", "color": "#32CD32", "gb_code": "G", "geometry": box(104.12, 30.66, 104.13, 30.67)},
        ],
        crs="EPSG:4326",
    )
    monkeypatch.setattr("src.engines.spatial_engine.get_landuse_data", lambda: lu_gdf)
    legend = get_landuse_legend()
    assert len(legend) == 2
    assert legend[0]["GB_Code"] in ("G", "R")
    assert legend[0]["Color"].startswith("#")

    st.session_state["custom_site_context"] = {}
    if hasattr(get_hud_statistics, "clear"):
        get_hud_statistics.clear()
