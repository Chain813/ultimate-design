"""Tests for workbench routing (?sub= vs ?tab=), restored Stages 06/15/16, and Stages 04-12 custom site adaptation."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box
import streamlit as st

from src.stages.common.workspace import (
    StageWorkspaceSpec,
    SubpageSpec,
    build_stage_workspace_html,
    resolve_active_subpage,
)
from src.workflow.city_design_workflow import resolve_subpage_option, resolve_subpage_value

ROOT = Path(__file__).resolve().parent.parent


def _sample_workspace() -> StageWorkspaceSpec:
    return StageWorkspaceSpec(
        stage_code="10",
        title="重点地段深化",
        description="测试工作区",
        evidence_stages=("08", "09", "10"),
        subpages=[
            SubpageSpec(
                label="📍 重点地块诊断雷达",
                title="重点地块诊断雷达",
                description="多维雷达",
            ),
            SubpageSpec(
                label="📊 控制性详细指标推演",
                title="控制性详细指标推演",
                description="指标反推",
            ),
            SubpageSpec(
                label="🔄 Before/After 推演",
                title="Before/After 推演",
                description="街景对比",
            ),
        ],
    )


def test_resolve_active_subpage_separates_sub_and_tab() -> None:
    ws = _sample_workspace()
    # When workbench ?sub=detail is present alongside inner ?tab=..., tab wins
    active = resolve_active_subpage(ws, query_params={"sub": "detail", "tab": "📊 控制性详细指标推演"})
    assert active.label == "📊 控制性详细指标推演"

    # When only ?sub=detail is present (no matching inner tab), defaults to first subpage without collision
    active_default = resolve_active_subpage(ws, query_params={"sub": "detail"})
    assert active_default.label == "📍 重点地块诊断雷达"

    # Backward compatibility: ?sub=<subpage_label> still resolves if ?tab= is absent
    active_legacy = resolve_active_subpage(ws, query_params={"sub": "🔄 Before/After 推演"})
    assert active_legacy.label == "🔄 Before/After 推演"


def test_build_stage_workspace_html_preserves_sub_and_uses_tab(monkeypatch) -> None:
    ws = _sample_workspace()
    monkeypatch.setattr(st, "query_params", {"sub": "detail"})
    html = build_stage_workspace_html(ws, ws.subpages[1])
    assert 'href="?sub=detail&tab=📍 重点地块诊断雷达"' in html
    assert 'href="?sub=detail&tab=📊 控制性详细指标推演"' in html


def test_city_design_workflow_subpage_resolvers_prioritize_tab() -> None:
    opts = ["🏙️ 3D 现状全息底座", "📊 MPI 更新潜力评估"]
    assert resolve_subpage_option(opts, query_params={"sub": "diagnosis", "tab": "📊 MPI 更新潜力评估"}) == 1
    assert resolve_subpage_value(opts, query_params={"sub": "diagnosis", "tab": "📊 MPI 更新潜力评估"}) == "📊 MPI 更新潜力评估"


def test_workbench_route_mappings_for_all_three_workbenches() -> None:
    wb1_text = (ROOT / "pages/01_全息空间诊断与数据沙盘.py").read_text(encoding="utf-8")
    wb2_text = (ROOT / "pages/02_多主体博弈与空间AIGC工坊.py").read_text(encoding="utf-8")
    wb3_text = (ROOT / "pages/03_数字图则与工程交付枢纽.py").read_text(encoding="utf-8")
    app_text = (ROOT / "app.py").read_text(encoding="utf-8")

    # Workbench 01 checks
    assert "render_site_ingestion_panel()" in wb1_text
    assert "render_site_ingestion_panel(title=" not in wb1_text
    assert "📤 16 类专项数据与调研资料逐项上传/替换" in wb1_text
    assert "if selected != WB1_OPTIONS[1]:" in wb1_text

    # Workbench 02 checks (Stage 06 quick panel + Stage 15 AIGC Studio tab)
    assert "✨ 空间 AIGC 推演工坊" in wb2_text
    assert '"aigc_studio"' in wb2_text
    assert "_render_stage06_quick_panel" in wb2_text
    assert "render_stage15_page" in wb2_text

    # Workbench 03 checks (Stage 16 Skill manual tab)
    assert "📖 智能体 Skill 规范手册" in wb3_text
    assert "render_stage16_page" in wb3_text

    # app.py checks (links for 15 and 16 + cache clear)
    assert "/02_多主体博弈与空间AIGC工坊?sub=aigc_studio" in app_text
    assert "/03_数字图则与工程交付枢纽?sub=skill" in app_text
    assert "stage_bus_cache.json" in app_text


def test_legacy_stage15_aigc_studio_root_and_custom_site(monkeypatch) -> None:
    st.session_state["_embedded_mode"] = True
    try:
        spec = importlib.util.spec_from_file_location("stage15_mod", ROOT / "src/legacy_pages/15_AIGC设计推演.py")
        assert spec and spec.loader
        mod15 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod15)

        assert mod15.ROOT == ROOT
        assert hasattr(mod15, "render_page")

        monkeypatch.setattr(mod15, "get_site_name", lambda: "南锣鼓巷更新片区")
        monkeypatch.setattr(mod15, "get_site_city", lambda: "北京市")
        desc = mod15._build_auto_scene_description()
        assert "长春水产大市场" not in desc
        assert "伊通河" not in desc
        assert "南锣鼓巷更新片区" in desc
    finally:
        st.session_state.pop("_embedded_mode", None)


def test_stage04_enrich_candidate_plots_varies_metrics_and_applies_overrides() -> None:
    from src.stages.stage04_diagnosis.page import _enrich_candidate_plots

    st.session_state["custom_plot_metrics_overrides"] = {
        "自定义地块B": {"poi": 33, "gvi": 27.5, "svf": 0.66, "area_ha": 4.2, "land_use": "商业服务业"}
    }
    try:
        raw_plots = [
            {"name": "自定义地块A", "land_use": "商业用地", "area_ha": 2.0, "poi": 10, "gvi": 15.0, "svf": 0.5},
            {"name": "自定义地块B", "land_use": "工业用地", "area_ha": 3.5, "poi": 10, "gvi": 15.0, "svf": 0.5},
            {"name": "自定义地块C", "land_use": "公园绿地", "area_ha": 1.8, "poi": 10, "gvi": 15.0, "svf": 0.5},
        ]
        enriched = _enrich_candidate_plots(raw_plots)
        assert len(enriched) == 3
        # Plot A and Plot C should not have identical default poi=10, gvi=15.0, svf=0.5
        assert (enriched[0]["poi"], enriched[0]["gvi"], enriched[0]["svf"]) != (
            enriched[2]["poi"],
            enriched[2]["gvi"],
            enriched[2]["svf"],
        )
        # Plot B override applied
        assert enriched[1]["poi"] == 33
        assert enriched[1]["gvi"] == 27.5
        assert enriched[1]["svf"] == 0.66
    finally:
        st.session_state.pop("custom_plot_metrics_overrides", None)


def test_stage08_landuse_normalization_and_baseline_pcts() -> None:
    from src.stages.stage08_master_plan.page import _compute_baseline_pcts, _normalize_landuse_category

    assert _normalize_landuse_category("residential") == "居住用地"
    assert _normalize_landuse_category("commercial") == "商业服务业"
    assert _normalize_landuse_category("office") == "商业办公"
    assert _normalize_landuse_category("park") == "公园与绿地"
    assert _normalize_landuse_category("school") == "公共设施"

    gdf = gpd.GeoDataFrame(
        {
            "Type": ["居住用地", "商业服务业", "公园与绿地"],
            "area_sqm": [5000.0, 3000.0, 2000.0],
            "in_study_area": [True, True, True],
        },
        geometry=[box(0, 0, 50, 100), box(50, 0, 80, 100), box(80, 0, 100, 100)],
        crs="EPSG:3857",
    )
    pcts = _compute_baseline_pcts(gdf)
    assert pcts == [50.0, 30.0, 0.0, 20.0, 0.0, 0.0]


def test_stage09_10_11_12_adapt_to_custom_site(monkeypatch) -> None:
    from src.stages.stage09_systems.page import _get_height_redlines
    from src.stages.stage10_detail_design import page as s10_page
    from src.stages.stage12_guideline import page as s12_page

    st.session_state["custom_site_context"] = {
        "city": "苏州市",
        "site_name": "平江路南片更新区",
        "area_ha": 95.0,
        "redlines": {
            "far_max": 2.0,
            "height_limit": 24.0,
            "building_density_max": 38.0,
            "greenery_ratio_min": 28.0,
        },
    }
    try:
        core_h, trans_h, dev_h = _get_height_redlines({}, "平江路南片更新区", "苏州市")
        assert (core_h, trans_h, dev_h) == (12, 24, 36)

        monkeypatch.setattr(s10_page, "get_site_name", lambda: "平江路南片更新区")
        monkeypatch.setattr(s10_page, "get_site_city", lambda: "苏州市")
        monkeypatch.setattr(
            s10_page,
            "get_active_candidate_plots",
            lambda: [{"name": "平江历史街坊A", "land_use": "商业用地", "area_ha": 3.2, "poi": 18, "gvi": 19.5, "svf": 0.55}],
        )
        merged_diags = s10_page._get_merged_plot_diagnostics()
        assert any(d["name"] == "平江历史街坊A" for d in merged_diags)

        s10_text = (ROOT / "src/stages/stage10_detail_design/page.py").read_text(encoding="utf-8")
        assert "/02_多主体博弈与空间AIGC工坊?sub=aigc_studio" in s10_text

        monkeypatch.setattr(s12_page, "get_site_name", lambda: "平江路南片更新区")
        monkeypatch.setattr(s12_page, "get_site_city", lambda: "苏州市")
        rl = s12_page._get_guideline_redlines({})
        assert rl["far_max"] == 2.0
        assert rl["height_max"] == 24.0
        assert rl["density_max"] == 38.0
        assert rl["green_min"] == 28.0

        fb_metrics = s12_page._get_fallback_gis_metrics()
        assert fb_metrics["boundary_area"] == 95.0 * 10000.0
    finally:
        st.session_state.pop("custom_site_context", None)
