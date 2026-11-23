"""Unit and benchmark tests for src.core.spatial_engine_v2 (DuckDB Spatial + rustworkx + MVT)."""

from __future__ import annotations

import json
import struct

import numpy as np
import pytest

from src.config.paths import DATA_FILES
from src.core.runtime_adapter import get_active_project_id, runtime_state
from src.core.spatial_engine_v2 import DEFAULT_PROJECT_ID, SpatialEngineV2, get_spatial_engine_v2


@pytest.fixture(scope="module")
def engine() -> SpatialEngineV2:
    eng = get_spatial_engine_v2()
    eng.switch_project(DEFAULT_PROJECT_ID)
    return eng


def test_ensure_project_initialized(engine: SpatialEngineV2):
    info = engine.ensure_project_initialized(DEFAULT_PROJECT_ID)
    assert info["project_id"] == DEFAULT_PROJECT_ID
    tables = info["tables"]
    assert tables["boundary"] >= 1
    assert tables["plots"] == 5
    assert tables["buildings"] > 100000
    assert tables["landuse"] > 500
    assert tables["roads"] > 1000
    assert tables["rails"] > 50
    assert tables["water"] > 10
    assert tables["poi"] > 300
    assert tables["traffic"] > 50
    assert tables["gvi"] > 200
    assert tables["nlp"] > 100


def test_build_fused_plots_table_and_geojson(engine: SpatialEngineV2):
    fused = engine.build_fused_plots_table(DEFAULT_PROJECT_ID)
    assert len(fused) == 5

    required_fields = {
        "plot_id",
        "name",
        "area_m2",
        "bldg_count",
        "footprint_sum_m2",
        "gfa_sum_m2",
        "bcr",
        "far",
        "avg_floor",
        "hist_bldg_count",
        "dominant_landuse",
        "poi_count",
        "poi_density",
        "gvi_mean",
        "svf_mean",
        "nlp_sentiment_mean",
        "syntax_int_mean",
        "traffic_load_mean",
    }

    for plot in fused:
        assert required_fields.issubset(plot.keys())
        assert plot["area_m2"] > 5000.0
        assert plot["bldg_count"] > 0, f"Plot {plot['name']} should have >0 buildings"
        assert plot["poi_count"] > 0, f"Plot {plot['name']} should have >0 POIs"
        assert plot["gvi_mean"] > 0.0, f"Plot {plot['name']} should have >0 GVI mean"
        assert plot["svf_mean"] > 0.0
        assert 0.0 < plot["bcr"] <= 1.0
        assert plot["far"] > 0.0
        assert isinstance(plot["dominant_landuse"], str) and len(plot["dominant_landuse"]) > 0

    geojson = engine.get_fused_plots_geojson(DEFAULT_PROJECT_ID)
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 5
    first_props = geojson["features"][0]["properties"]
    assert "mpi_score" in first_props
    assert "bldg_count" in first_props
    assert geojson["features"][0]["geometry"]["type"] in ("Polygon", "MultiPolygon")


def test_compute_ahp_mpi_ranking_and_overrides(engine: SpatialEngineV2):
    res = engine.compute_ahp_mpi(project_id=DEFAULT_PROJECT_ID)
    ranking = res["ranking"]
    assert len(ranking) == 5
    scores = [item["mpi_score"] for item in ranking]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= s <= 100.0 for s in scores)
    assert res["top_plot"]["name"] == ranking[0]["name"]

    expected_dims = {
        "土地开发潜力",
        "建筑更新迫切度",
        "商业业态活力",
        "绿视与微气候",
        "交通可达性",
        "公众舆情期望",
    }
    for plot_name, radar in res["radar_by_plot"].items():
        assert set(radar.keys()) == expected_dims
        assert all(0.0 <= val <= 100.0 for val in radar.values())

    # Test custom weights and metric overrides
    target_name = ranking[-1]["name"]
    res_ov = engine.compute_ahp_mpi(
        weights={"poi_vitality": 0.70, "green_quality": 0.10, "far_gap": 0.10, "bldg_density": 0.05, "traffic_access": 0.05},
        overrides={target_name: {"poi_count": 200, "poi_density": 80.0}},
        project_id=DEFAULT_PROJECT_ID,
    )
    ov_entry = next(item for item in res_ov["ranking"] if item["name"] == target_name)
    orig_entry = next(item for item in ranking if item["name"] == target_name)
    assert ov_entry["mpi_score"] > orig_entry["mpi_score"]


def test_analyze_full_network_syntax_no_truncation_no_outliers(engine: SpatialEngineV2):
    syntax_res = engine.analyze_full_network_syntax(project_id=DEFAULT_PROJECT_ID, snap_tolerance_m=2.5)
    summary = syntax_res["summary"]
    geojson = syntax_res["geojson"]

    assert summary["total_segments"] > 1000
    assert len(geojson["features"]) == summary["total_segments"]
    assert 0.0 < summary["mean_int_rn"] < 50.0
    assert 0.0 < summary["max_int_rn"] < 100.0
    assert 0.0 <= summary["mean_choice"] <= 1.0
    assert len(summary["top_roads"]) == 10

    # Strictly verify zero >= 1000.0 outliers (no 100000.0 artifacts) across all segments and radii
    r400_vals = []
    r800_vals = []
    rn_vals = []
    choice_vals = []
    for feat in geojson["features"]:
        props = feat["properties"]
        for col in ("int_r400", "int_r800", "int_rn"):
            v = float(props[col])
            assert 0.0 <= v < 1000.0, f"Outlier {v} detected in {col}"
        c = float(props["choice_norm"])
        assert 0.0 <= c <= 1.0
        r400_vals.append(float(props["int_r400"]))
        r800_vals.append(float(props["int_r800"]))
        rn_vals.append(float(props["int_rn"]))
        choice_vals.append(c)

    assert max(r400_vals) > 0.0
    assert max(r800_vals) > 0.0
    assert max(rn_vals) > 0.0
    assert max(choice_vals) > 0.0

    cached_summary = engine.get_spatial_syntax_summary(DEFAULT_PROJECT_ID)
    assert cached_summary["total_segments"] == summary["total_segments"]


def test_get_mvt_tile_changchun_z14(engine: SpatialEngineV2):
    # Tile (z=14, x=13896, y=5964) covers the Changchun Puppet Palace study area (~125.34E, 43.905N)
    z, x, y = 14, 13896, 5964
    for layer in ("buildings", "roads", "landuse", "plots", "boundary", "road_syntax_v2"):
        pbf_bytes = engine.get_mvt_tile(layer, z, x, y, project_id=DEFAULT_PROJECT_ID)
        assert isinstance(pbf_bytes, bytes)
        assert len(pbf_bytes) > 32, f"Expected non-empty MVT .pbf bytes for layer {layer} at ({z},{x},{y})"

    # Second call hits LRU cache
    cached_pbf = engine.get_mvt_tile("buildings", z, x, y, project_id=DEFAULT_PROJECT_ID)
    assert len(cached_pbf) > 32

    # Empty ocean tile returns b""
    empty_pbf = engine.get_mvt_tile("buildings", 14, 0, 0, project_id=DEFAULT_PROJECT_ID)
    assert empty_pbf == b""


def test_get_binary_layer_gvi_and_poi(engine: SpatialEngineV2):
    buf = engine.get_binary_layer("gvi", project_id=DEFAULT_PROJECT_ID)
    assert len(buf) > 64

    (header_len,) = struct.unpack("<I", buf[:4])
    header_json = buf[4 : 4 + header_len].decode("utf-8").strip()
    meta = json.loads(header_json)
    assert meta["layer"] == "gvi"
    assert meta["count"] > 200
    assert meta["stride"] == 5
    assert meta["fields"] == ["lon", "lat", "gvi", "svf", "bvi"]

    payload_bytes = buf[4 + header_len :]
    assert len(payload_bytes) == meta["count"] * meta["stride"] * 4
    arr = np.frombuffer(payload_bytes, dtype=np.float32).reshape(meta["count"], meta["stride"])
    assert np.all((arr[:, 0] > 120.0) & (arr[:, 0] < 130.0))
    assert np.all((arr[:, 1] > 40.0) & (arr[:, 1] < 48.0))
    assert float(np.mean(arr[:, 2])) > 0.0


def test_multi_project_lifecycle_and_rag_protection(engine: SpatialEngineV2):
    rag_path = DATA_FILES["rag"]
    assert rag_path.exists(), "data/rag_knowledge.json must exist"
    rag_stat_before = (rag_path.stat().st_mtime_ns, rag_path.stat().st_size)
    assert rag_stat_before[1] > 10000

    test_pid = "pytest_custom_clone"
    try:
        created = engine.create_project(
            project_id=test_pid,
            name="测试独立更新工程",
            city="长春测试区",
            clone_default=True,
        )
        assert created["project_id"] == test_pid

        projects = engine.list_projects()
        assert any(p["project_id"] == test_pid for p in projects)

        # Save stage_bus item in default project
        engine.switch_project(DEFAULT_PROJECT_ID)
        engine.save_stage_bus_item("04", "unit_test_marker", {"site": "default"})

        # Switch to custom project and verify isolation
        switched = engine.switch_project(test_pid)
        assert switched["project_id"] == test_pid
        assert get_active_project_id() == test_pid
        assert "04_unit_test_marker" not in (runtime_state.get("stage_bus") or {})

        engine.save_stage_bus_item("04", "unit_test_marker", {"site": "custom_clone"})
        bus_custom = engine.load_stage_bus_all(test_pid)
        assert bus_custom["04"]["unit_test_marker"] == {"site": "custom_clone"}

        # Switch back to default project and confirm its stage_bus is intact
        engine.switch_project(DEFAULT_PROJECT_ID)
        assert get_active_project_id() == DEFAULT_PROJECT_ID
        bus_default = engine.load_stage_bus_all(DEFAULT_PROJECT_ID)
        assert bus_default["04"]["unit_test_marker"] == {"site": "default"}

        # Default project deletion must be blocked
        with pytest.raises(ValueError):
            engine.delete_project(DEFAULT_PROJECT_ID)
    finally:
        engine.switch_project(DEFAULT_PROJECT_ID)
        engine.delete_project(test_pid)

    rag_stat_after = (rag_path.stat().st_mtime_ns, rag_path.stat().st_size)
    assert rag_stat_after == rag_stat_before, "data/rag_knowledge.json must never be modified or reset!"
