"""v6.5.0 全量增减改造专项单元测试。"""

from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import geopandas as gpd
import pandas as pd
import streamlit as st
from shapely.geometry import LineString, box

ROOT = Path(__file__).resolve().parent.parent


def test_spatial_syntax_registry_and_runner(tmp_path: Path) -> None:
    """验证 SpatialSyntaxEngine 懒加载注册及 run_site_spatial_syntax 在临时矢量上的完整输出。"""
    from src.engines import engine_registry
    from src.stages.stage04_diagnosis.page import run_site_spatial_syntax

    assert hasattr(engine_registry, "SpatialSyntaxEngine")
    assert hasattr(engine_registry, "get_spatial_syntax_engine")
    assert callable(engine_registry.get_spatial_syntax_engine)

    roads_path = tmp_path / "roads.geojson"
    buildings_path = tmp_path / "buildings.geojson"
    boundary_path = tmp_path / "boundary.geojson"

    boundary_gdf = gpd.GeoDataFrame(
        [{"name": "测试研究范围", "geometry": box(120.000, 30.000, 120.010, 30.010)}],
        crs="EPSG:4326",
    )
    roads_gdf = gpd.GeoDataFrame(
        [
            {"id": 1, "geometry": LineString([(120.001, 30.005), (120.009, 30.005)])},
            {"id": 2, "geometry": LineString([(120.005, 30.001), (120.005, 30.009)])},
            {"id": 3, "geometry": LineString([(120.002, 30.002), (120.008, 30.008)])},
            {"id": 4, "geometry": LineString([(120.002, 30.008), (120.008, 30.002)])},
        ],
        crs="EPSG:4326",
    )
    buildings_gdf = gpd.GeoDataFrame(
        [
            {"building_id": 1, "Floor": 4, "geometry": box(120.002, 30.002, 120.003, 30.003)},
            {"building_id": 2, "Floor": 8, "geometry": box(120.006, 30.006, 120.007, 30.007)},
        ],
        crs="EPSG:4326",
    )

    boundary_gdf.to_file(boundary_path, driver="GeoJSON")
    roads_gdf.to_file(roads_path, driver="GeoJSON")
    buildings_gdf.to_file(buildings_path, driver="GeoJSON")

    res = run_site_spatial_syntax(
        roads_path=roads_path,
        buildings_path=buildings_path,
        boundary_path=boundary_path,
        max_road_segments=50,
    )

    for key in (
        "road_segment_count",
        "mean_integration",
        "max_integration",
        "mean_depth",
        "mean_choice",
        "integration_distribution",
        "BCR",
        "FAR",
        "avg_height_m",
        "aspect_ratio_HW",
        "SVF",
        "site_area_m2",
        "wind_comfort_index",
        "solar_shadow_index",
        "microclimate_grade",
        "recommendation",
    ):
        assert key in res, f"Missing key: {key}"

    assert res["road_segment_count"] == 4
    assert res["mean_integration"] > 0
    assert res["BCR"] > 0
    assert res["FAR"] > 0
    assert 0 < res["SVF"] <= 1.0
    assert res["microclimate_grade"] in ("A", "B", "C")
    assert res["recommendation"]


def test_datav_bigscreen_payload_and_responsive_rendering(monkeypatch) -> None:
    """验证 sc-datav 载荷采集、6 处占位符全量注入及移动端/桌面端高度响应切换。"""
    from src.ui import digital_twin

    payload = digital_twin.collect_datav_payload()
    for key in (
        "boundary_ha",
        "building_count",
        "poi_count",
        "gvi_count",
        "max_height",
        "avg_height",
        "high_rise_ratio",
        "poi_list",
        "landuse_chart",
        "height_chart",
    ):
        assert key in payload

    monkeypatch.setattr(digital_twin, "get_site_name", lambda: "苏州平江路示范区")
    monkeypatch.setattr(digital_twin, "get_map_viewport", lambda: {"center": [120.63, 31.31], "zoom": 15.0, "pitch": 60.0, "bearing": 0.0})

    # 桌面端检查
    monkeypatch.setattr(digital_twin, "is_mobile_client", lambda: False)
    with patch.object(digital_twin.components, "html") as mock_html:
        digital_twin.render_datav_bigscreen()
        mock_html.assert_called_once()
        rendered_html = mock_html.call_args.args[0]
        assert mock_html.call_args.kwargs["height"] == 880
        assert mock_html.call_args.kwargs["scrolling"] is False
        assert "苏州平江路示范区" in rendered_html
        for leftover in (
            "/*__SITE_NAME__*/",
            "/*__DV_STATS__*/",
            "/*__DV_BOUNDARY__*/",
            "/*__DV_PLOTS__*/",
            "/*__DV_BUILDING_URL__*/",
            "/*__DV_MAP_CONFIG__*/",
        ):
            assert leftover not in rendered_html

    # 移动端检查
    monkeypatch.setattr(digital_twin, "is_mobile_client", lambda: True)
    with patch.object(digital_twin.components, "html") as mock_html_mobile:
        digital_twin.render_datav_bigscreen()
        mock_html_mobile.assert_called_once()
        assert mock_html_mobile.call_args.kwargs["height"] == 1650
        assert mock_html_mobile.call_args.kwargs["scrolling"] is True


def test_wb1_assets_quality_check_global_coords_and_tools(tmp_path: Path, monkeypatch) -> None:
    """验证工作台 01 资产质量体检支持全球任意合法 WGS-84 坐标且不误报长春偏移。"""
    wb1_path = ROOT / "pages" / "01_全息空间诊断与数据沙盘.py"
    wb1_text = wb1_path.read_text(encoding="utf-8")
    for expected in (
        "规划文档语义萃取引擎",
        "16 类空间与业务数据在线质量体检",
        "街景采样点 4 方向实景巡检",
    ):
        assert expected in wb1_text

    spec = importlib.util.spec_from_file_location("wb1_mod_check", wb1_path)
    assert spec and spec.loader
    wb1_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wb1_mod)

    # 构造北京、伦敦、悉尼的合法全球 POI 与越界 POI 对比
    valid_poi_csv = tmp_path / "global_poi.csv"
    pd.DataFrame(
        [
            {"Name": "故宫博物院", "Lat": 39.9163, "Lng": 116.3972},
            {"Name": "伦敦国王十字", "Lat": 51.5308, "Lng": -0.1238},
            {"Name": "悉尼歌剧院", "Lat": -33.8568, "Lng": 151.2153},
        ]
    ).to_csv(valid_poi_csv, index=False)

    bad_poi_csv = tmp_path / "bad_poi.csv"
    pd.DataFrame(
        [
            {"Name": "异常点位", "Lat": 999.0, "Lng": 120.5},
        ]
    ).to_csv(bad_poi_csv, index=False)

    valid_geo = tmp_path / "boundary.geojson"
    valid_geo.write_text(
        json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": None}]}),
        encoding="utf-8",
    )

    import src.data as data_pkg

    mock_cats = [
        {"id": "poi", "title": "POI兴趣点", "icon": "📍", "target_path": valid_poi_csv},
        {"id": "boundary", "title": "研究范围边界", "icon": "📐", "target_path": valid_geo},
    ]
    monkeypatch.setattr(data_pkg, "DATA_CATEGORIES", mock_cats)

    res_ok = wb1_mod.run_assets_quality_check()
    assert len(res_ok) == 2
    assert res_ok[0]["状态"] == "已上传"
    assert res_ok[0]["问题数"] == 0
    assert res_ok[0]["质量评级"] == "A"

    mock_cats[0]["target_path"] = bad_poi_csv
    res_bad = wb1_mod.run_assets_quality_check()
    assert res_bad[0]["问题数"] >= 1
    assert "WGS-84" in res_bad[0]["详情"]


def test_stage15_and_stage16_clean_import_and_adaptation() -> None:
    """验证 Stage 15/16 已晋升至 src/stages/ 且导入无顶层副作用。"""
    st.session_state.pop("_embedded_mode", None)
    st.set_page_config.reset_mock()

    mod15 = importlib.import_module("src.stages.stage15_aigc.page")
    mod16 = importlib.import_module("src.stages.stage16_skills.page")

    assert mod15.ROOT == ROOT
    assert callable(mod15.render_page)
    assert mod16.ROOT == ROOT
    assert callable(mod16.render_page)
    st.set_page_config.assert_not_called()

    scenarios = mod16.get_skill_conflict_scenarios("平江路更新区", "苏州市")
    assert len(scenarios) == 3
    all_txt = " ".join(scenarios.keys()) + " " + " ".join(scenarios.values())
    assert "平江路更新区" in all_txt
    assert "苏州市" in all_txt
    for forbidden in ("伪满", "伊通河", "长春"):
        assert forbidden not in all_txt


def test_v65_cleanup_and_deduplication_verified() -> None:
    """验证遗留目录、过渡草稿加载器与重复权重/演示视频均已清理或归档。"""
    assert not (ROOT / "src" / "legacy_pages").exists()
    assert not (ROOT / "src" / "engines" / "local_draft_loader.py").exists()
    assert (ROOT / "tools" / "archive" / "local_draft_loader.py").exists()

    realesr_root = ROOT / "tools" / "realesrgan-ncnn-vulkan"
    assert (realesr_root / "realesrgan-ncnn-vulkan.exe").exists()
    assert (realesr_root / "models" / "realesrgan-x4plus.bin").exists()
    assert not (realesr_root / "realesrgan-x4plus.bin").exists()
    assert not (realesr_root / "onepiece_demo.mp4").exists()

    vid_out = ROOT / "tools" / "video_generator" / "output"
    assert not (vid_out / "final.mp4").exists()
    assert not (vid_out / "preview.mp4").exists()
