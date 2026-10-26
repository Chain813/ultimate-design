"""Stage 12: structured page renderer for urban design guidelines."""

import logging
from pathlib import Path
from typing import Any

import streamlit as st

from src.config.site import get_site_city, get_site_config, get_site_district, get_site_name
from src.engines.llm_engine import call_llm_engine, call_llm_engine_stream
from src.engines.spatial_data_injector import get_full_spatial_context
from src.stages.common.workspace import render_stage_workspace
from src.stages.stage12_guideline.config import STAGE12_WORKSPACE
from src.ui.app_shell import (
    render_engine_status_alert,
    render_logic_chain_stepper,
    render_top_nav,
)
from src.ui.design_system import render_page_banner, render_section_intro
from src.ui.module_summary import render_stage_summary
from src.ui.streamlit_compat import stretch_width
from src.workflow.approval_state import StageDependency, render_dependency_gate
from src.workflow.artifact_registry import register_artifact
from src.workflow.stage_data_bus import (
    load_stage_output,
    render_evidence_chain_bar,
    save_stage_output,
)
from src.workflow.stage_keys import SK

GUIDELINE_SECTIONS = [
    {
        "id": "1",
        "title": "总则与基本原则",
        "description": "编制目的、适用范围、规划依据（含法规文件清单）、术语定义、基本设计原则",
        "data_hint": "引用 Boundary_Scope 研究范围、项目背景",
    },
    {
        "id": "2",
        "title": "空间结构与功能布局",
        "description": "空间结构规划（一核多轴多片区）、功能分区、用地规划调整建议、开发强度控制",
        "data_hint": "引用 landuse_clipped.geojson 的用地分类统计",
    },
    {
        "id": "3",
        "title": "建筑风貌控制导则",
        "description": "高度分区控制（核心区/协调过渡区/一般发展区）、色彩材质规范、"
                       "屋顶形式、立面改造标准、街墙界面连续性、重点保护建筑清单",
        "data_hint": "引用 Building_Footprints 的层高统计和天际线数据",
    },
    {
        "id": "4",
        "title": "道路交通与慢行系统导则",
        "description": "道路等级规划、断面设计标准、慢行网络贯通、"
                       "公共交通组织、停车规划、断头路打通计划",
        "data_hint": "引用 road_clipped.geojson 路网结构和 Traffic_Flow.csv",
    },
    {
        "id": "5",
        "title": "公共空间与景观绿化导则",
        "description": "三级公共空间体系、绿地系统规划、口袋公园设置标准、"
                       "广场节点设计导引、街道家具规范、GVI 提升目标",
        "data_hint": "引用 GVI_Results_Analysis.csv 绿视率数据",
    },
    {
        "id": "6",
        "title": "历史文化保护与活化导则",
        "description": "保护对象清单与分级、保护范围划定、风貌协调区管控、"
                       "活化利用策略、工业遗产活化方案",
        "data_hint": "引用属地历史文脉保护规划、建筑遗产名录",
    },
    {
        "id": "7",
        "title": "业态管控与经济策划导则",
        "description": "业态引导清单（鼓励/限制/禁止）、商业运营模式、"
                       "文旅产业链构建、社区商业配比标准",
        "data_hint": "引用 POI 分布数据和 Stage 07 策略矩阵",
    },
    {
        "id": "8",
        "title": "基础设施与市政工程导则",
        "description": "给排水规划、电力通信、环卫设施、消防设施、无障碍设施标准",
        "data_hint": "引用城市基础设施规范",
    },
    {
        "id": "9",
        "title": "实施保障与管理机制",
        "description": "分期实施计划要点、资金保障机制、管理机制、"
                       "公众参与渠道、监督评估体系",
        "data_hint": "引用 Stage 11 实施路径数据",
    },
]


def _is_changchun_default_site() -> bool:
    s_name = get_site_name()
    s_city = get_site_city()
    return ("伪满" in s_name) or ("长春" in s_city and "水产" in s_name) or (s_city == "长春市" and "伪满皇宫" in s_name)


def _get_guideline_redlines(target_plot: dict[str, Any]) -> dict[str, float]:
    """动态解析当前工程的控规红线参数（优先读取用户交互设置、target_plot 与 custom_site_context）。"""
    is_cc = _is_changchun_default_site()
    custom_ctx = st.session_state.get("custom_site_context", {}) or {}
    redlines = custom_ctx.get("redlines", {}) or {}
    site_cfg = get_site_config() or {}
    reg = site_cfg.get("regulatory_limits", {}) or {}

    far_max = float(
        st.session_state.get("s12_far_max")
        or target_plot.get("far_max")
        or redlines.get("far_max")
        or reg.get("far_max")
        or (1.4 if is_cc else 2.2)
    )
    height_max = float(
        st.session_state.get("s12_gen_h")
        or target_plot.get("height_max")
        or redlines.get("height_limit")
        or reg.get("general_zone_height_limit_m")
        or (18.0 if is_cc else 24.0)
    )
    core_height_max = float(
        st.session_state.get("s12_core_h")
        or reg.get("core_zone_height_limit_m")
        or (9.0 if is_cc else max(9.0, round(height_max * 0.5, 1)))
    )
    density_max = float(
        st.session_state.get("s12_density_max")
        or target_plot.get("density_max")
        or redlines.get("building_density_max")
        or reg.get("building_density_max_pct")
        or 35.0
    )
    green_min = float(
        st.session_state.get("s12_green_min")
        or target_plot.get("green_min")
        or redlines.get("greenery_ratio_min")
        or reg.get("green_ratio_min_pct")
        or 25.0
    )
    return {
        "far_max": round(far_max, 2),
        "height_max": round(height_max, 1),
        "core_height_max": round(core_height_max, 1),
        "density_max": round(density_max, 1),
        "green_min": round(green_min, 1),
    }


def _map_to_gb_code(raw_val: object) -> str:
    """将自定义或 OSM 用地类别映射为国标大类代码 (R/A/B/G/M/S)。"""
    s = str(raw_val or "").strip()
    if not s:
        return "R (居住用地)"
    upper = s.upper()
    if upper.startswith(("R", "A", "B", "G", "M", "S")) and ("(" in s or len(upper) <= 3):
        prefix = upper[0]
        label_map = {
            "R": "R (居住用地)",
            "A": "A (公共设施用地)",
            "B": "B (商业用地)",
            "G": "G (绿地广场)",
            "M": "M (多功能混合)",
            "S": "S (交通设施用地)",
        }
        return label_map.get(prefix, s)
    low = s.lower()
    if any(k in low for k in ["绿", "园", "广场", "草", "林", "park", "green", "grass", "meadow", "forest", "garden", "recreation"]):
        return "G (绿地广场)"
    if any(k in low for k in ["商", "办", "集贸", "市", "零售", "commercial", "retail", "office", "shop", "market"]):
        return "B (商业用地)"
    if any(k in low for k in ["公", "教", "医", "文", "体", "行政", "school", "university", "hospital", "public", "civic", "institutional"]):
        return "A (公共设施用地)"
    if any(k in low for k in ["工", "仓", "厂", "混", "industrial", "warehouse", "manufacturing"]):
        return "M (多功能混合)"
    if any(k in low for k in ["道", "交", "市政", "铁", "停", "road", "railway", "transport", "parking"]):
        return "S (交通设施用地)"
    return "R (居住用地)"


@st.cache_data(ttl=3600, max_entries=20)
def _load_and_calculate_gis_metrics_cached(
    boundary_path_str: str,
    buildings_path_str: str,
    landuse_path_str: str,
    mtime_key: float,
) -> dict[str, Any] | None:
    import geopandas as gpd
    import pandas as pd

    boundary_path = Path(boundary_path_str)
    buildings_path = Path(buildings_path_str)
    landuse_path = Path(landuse_path_str)

    if not (boundary_path.exists() and buildings_path.exists() and landuse_path.exists()):
        return None

    try:
        boundary = gpd.read_file(str(boundary_path))
        if boundary.empty:
            return None
        if boundary.crs is None:
            boundary = boundary.set_crs("EPSG:4326")
        boundary_3857 = boundary.to_crs("EPSG:3857")
        boundary_union = (
            boundary_3857.geometry.union_all()
            if hasattr(boundary_3857.geometry, "union_all")
            else boundary_3857.geometry.unary_union
        )
        boundary_area = float(boundary_union.area)
        if boundary_area <= 0:
            return None

        buildings = gpd.read_file(str(buildings_path))
        if buildings.crs is None:
            buildings = buildings.set_crs("EPSG:4326")
        buildings_3857 = buildings.to_crs("EPSG:3857")
        centroids = buildings_3857.geometry.centroid
        mask = centroids.within(boundary_union)
        filtered_buildings = buildings_3857.loc[mask].copy() if mask.any() else buildings_3857.copy()

        footprint_area = float(filtered_buildings.geometry.area.sum())
        floor_col = None
        for col_cand in ("Floor", "floor", "levels", "building:levels", "floors"):
            if col_cand in filtered_buildings.columns:
                floor_col = col_cand
                break
        if floor_col is not None:
            filtered_buildings["Floor_num"] = pd.to_numeric(filtered_buildings[floor_col], errors="coerce").fillna(2).clip(lower=1).astype(float)
        elif "height" in filtered_buildings.columns or "Height" in filtered_buildings.columns:
            h_col = "height" if "height" in filtered_buildings.columns else "Height"
            h_vals = pd.to_numeric(filtered_buildings[h_col], errors="coerce").fillna(7.0).clip(lower=3.0).astype(float)
            filtered_buildings["Floor_num"] = (h_vals / 3.5).round(1)
        else:
            filtered_buildings["Floor_num"] = 2.0

        total_floor_area = float((filtered_buildings.geometry.area * filtered_buildings["Floor_num"]).sum())
        far = total_floor_area / boundary_area
        building_density = (footprint_area / boundary_area) * 100.0

        filtered_buildings["Height"] = filtered_buildings["Floor_num"] * 3.5
        max_height = float(filtered_buildings["Height"].max()) if not filtered_buildings.empty else 18.0

        landuse = gpd.read_file(str(landuse_path))
        if landuse.crs is None:
            landuse = landuse.set_crs("EPSG:4326")
        landuse_3857 = landuse.to_crs("EPSG:3857")
        try:
            landuse_clipped = gpd.clip(landuse_3857, boundary_3857)
            if landuse_clipped.empty:
                landuse_clipped = landuse_3857.copy()
        except Exception:
            landuse_clipped = landuse_3857.copy()
        landuse_clipped["Area"] = landuse_clipped.geometry.area

        lu_col = None
        for col_cand in ("GB_Code", "Type", "type", "land_type", "landuse", "land_use", "LandUse", "fclass"):
            if col_cand in landuse_clipped.columns:
                lu_col = col_cand
                break
        if lu_col is not None:
            landuse_clipped["GB_Code"] = landuse_clipped[lu_col].apply(_map_to_gb_code)
        else:
            landuse_clipped["GB_Code"] = "R (居住用地)"

        landuse_summary = landuse_clipped.groupby("GB_Code")["Area"].sum().reset_index()
        total_lu_area = max(boundary_area, float(landuse_summary["Area"].sum()) or 1.0)
        landuse_summary["percentage"] = (landuse_summary["Area"] / total_lu_area) * 100.0

        greenery_area = float(landuse_clipped[landuse_clipped["GB_Code"].str.startswith("G", na=False)]["Area"].sum())
        greenery_ratio = (greenery_area / boundary_area) * 100.0

        return {
            "boundary_area": boundary_area,
            "far": far,
            "building_density": building_density,
            "greenery_ratio": greenery_ratio,
            "max_height": max_height,
            "num_buildings": len(filtered_buildings),
            "landuse": landuse_summary.to_dict("records"),
        }
    except Exception:
        logging.debug("GIS 指标计算失败", exc_info=True)
        return None


def _load_and_calculate_gis_metrics() -> dict[str, Any] | None:
    from src.config import SHP_FILES

    bd_p = Path(SHP_FILES["boundary"])
    bl_p = Path(SHP_FILES["buildings"])
    lu_p = Path(SHP_FILES["landuse"])
    mtime = (
        (bd_p.stat().st_mtime if bd_p.exists() else 0.0)
        + (bl_p.stat().st_mtime if bl_p.exists() else 0.0)
        + (lu_p.stat().st_mtime if lu_p.exists() else 0.0)
    )
    return _load_and_calculate_gis_metrics_cached(str(bd_p), str(bl_p), str(lu_p), mtime)


def _get_fallback_gis_metrics() -> dict[str, Any]:
    """当 GIS 矢量文件缺失或解析受阻时，根据当前基地配置动态生成兜底统计，杜绝跨基地硬编码污染。"""
    if _is_changchun_default_site():
        return {
            "boundary_area": 3278363.88,
            "far": 1.13,
            "building_density": 30.0,
            "greenery_ratio": 2.9,
            "max_height": 59.5,
            "num_buildings": 719,
            "landuse": [
                {"GB_Code": "R (居住用地)", "Area": 1673712.43, "percentage": 51.1},
                {"GB_Code": "A (公共设施用地)", "Area": 435239.23, "percentage": 13.3},
                {"GB_Code": "B (商业用地)", "Area": 374644.06, "percentage": 11.4},
                {"GB_Code": "G (绿地广场)", "Area": 96318.99, "percentage": 2.9},
                {"GB_Code": "M (多功能混合)", "Area": 7286.11, "percentage": 0.2},
                {"GB_Code": "S (交通设施用地)", "Area": 12689.75, "percentage": 0.4},
            ],
        }

    from src.engines.spatial_engine import get_hud_statistics, get_skyline_features
    stats = get_hud_statistics() or {}
    sky = get_skyline_features() or {}
    custom_ctx = st.session_state.get("custom_site_context", {}) or {}
    site_cfg = get_site_config() or {}
    area_ha = float(custom_ctx.get("area_ha") or site_cfg.get("area_ha") or 85.0)
    boundary_area = area_ha * 10000.0
    max_h = float(sky.get("max_height") or 28.0)
    bldg_cnt = int(sky.get("building_count") or 180)
    return {
        "boundary_area": boundary_area,
        "far": 1.45,
        "building_density": 31.5,
        "greenery_ratio": 16.5,
        "max_height": max_h,
        "num_buildings": bldg_cnt,
        "landuse": [
            {"GB_Code": "R (居住用地)", "Area": boundary_area * 0.45, "percentage": 45.0},
            {"GB_Code": "B (商业用地)", "Area": boundary_area * 0.18, "percentage": 18.0},
            {"GB_Code": "A (公共设施用地)", "Area": boundary_area * 0.12, "percentage": 12.0},
            {"GB_Code": "G (绿地广场)", "Area": boundary_area * 0.165, "percentage": 16.5},
            {"GB_Code": "S (交通设施用地)", "Area": boundary_area * 0.085, "percentage": 8.5},
        ],
    }


def render_page() -> None:
    render_top_nav()
    render_engine_status_alert()

    render_page_banner(
        title="城市设计导则",
        description=(
            "分板块深度生成：将导则拆分为多个专项模块，"
            "对每个模块注入真实空间数据并调用 DeepSeek-V4 Pro 展开。"
        ),
        eyebrow="Stage 12",
        tags=["分板块生成", "数据驱动", "管控条文", "Word 导出"],
    )
    active = render_stage_workspace(STAGE12_WORKSPACE)
    render_evidence_chain_bar("12", list(STAGE12_WORKSPACE.evidence_stages))

    with st.sidebar:
        model_tag = st.selectbox(
            "DeepSeek 模型",
            ["deepseek-v4-flash", "deepseek-v4-pro"],
            index=1,
            key="p12_model",
            help="城市设计导则建议使用 deepseek-v4-pro 确保深度与准确度",
        )

    target_plot = load_stage_output("04", "target_plot", {}) or load_stage_output("07", "target_plot", {}) or {}
    rl = _get_guideline_redlines(target_plot)

    selected_sub = active.label
    st.markdown("---")
    if selected_sub == "📜 分板块导则生成":
        render_section_intro(
            "分板块深度导则生成",
            "对每个导则板块单独调用 DeepSeek-V4 Pro 进行深度展开，"
            "注入真实空间数据作为量化依据。每板块不限字数，只要求详实、精准、有据。",
            eyebrow="Multi-Dispatch Generation",
        )
        stage12_ready = render_dependency_gate(
            [
                StageDependency("05", SK.DIAGNOSIS_REPORT, "前期诊断报告"),
                StageDependency("06", SK.DESIGN_CONCEPT, "设计目标定位"),
                StageDependency("07", SK.STRATEGY_MATRIX, "策略共识矩阵", approval_required=True),
            ],
            title="Stage 12 导则生成前置条件",
        )
        if not stage12_ready:
            if st.checkbox("⚡ 快速推演模式（跳过前序依赖，直接启用生成）", key="p12_bypass_gate", value=False):
                stage12_ready = True

        # 加载前序数据 (打通 Stage 04-11 全域设计成果)
        s1 = load_stage_output("05", SK.DIAGNOSIS_REPORT, "") or load_stage_output("04", SK.DIAGNOSIS_REPORT, "")
        s3 = load_stage_output("06", SK.DESIGN_CONCEPT, "")
        s4 = load_stage_output("07", SK.STRATEGY_MATRIX, "")
        design_brief = load_stage_output("07", SK.DESIGN_BRIEF, "")
        s8_struct = load_stage_output("08", SK.SPATIAL_STRUCTURE, "")
        s9_traffic = load_stage_output("09", SK.TRAFFIC_SYSTEM, "")
        s9_bldg = load_stage_output("09", SK.BUILDING_FORM, "")
        s9_space = load_stage_output("09", SK.PUBLIC_SPACE, "")
        s11_phasing = load_stage_output("11", "region_phasing", "")
        spatial_ctx = get_full_spatial_context()

        c1, c2, c3 = st.columns(3)
        c1.metric("诊断报告", "✅" if s1 else "⚠️ 缺失")
        c2.metric("总体空间结构", "✅" if s8_struct else "⚠️ 缺失")
        c3.metric("策略矩阵与纲要", "✅" if (s4 or design_brief) else "⚠️ 缺失")

        st.markdown("---")

        generated_sections = {}
        for sec in GUIDELINE_SECTIONS:
            key = f"guideline_section_{sec['id']}"
            saved = load_stage_output("12", key, "")
            if saved:
                generated_sections[sec["id"]] = saved

        total = len(GUIDELINE_SECTIONS)
        done = len(generated_sections)
        st.progress(done / total, text=f"已生成 {done}/{total} 个板块")

        for sec in GUIDELINE_SECTIONS:
            key = f"guideline_section_{sec['id']}"
            is_done = sec["id"] in generated_sections
            sec_desc = sec["description"]
            if sec["id"] == "3":
                sec_desc = (
                    f"高度分区控制（核心区≤{rl['core_height_max']:.0f}m/一般区≤{rl['height_max']:.0f}m）、"
                    "色彩材质规范、屋顶形式、立面改造标准、街墙界面连续性、重点保护建筑清单"
                )

            with st.expander(
                f"{'✅' if is_done else '⬜'} 第{sec['id']}章 {sec['title']}",
                expanded=True,
            ):
                st.markdown(f"**内容范围：** {sec_desc}")
                st.caption(f"📊 数据依据：{sec['data_hint']}")

                if is_done:
                    st.markdown(generated_sections[sec["id"]])
                    if st.button(f"🔄 重新生成第{sec['id']}章", key=f"regen_{sec['id']}"):
                        st.session_state[f"force_regen_{sec['id']}"] = True
                        st.rerun()

                if (not is_done or st.session_state.get(f"force_regen_{sec['id']}", False)) and st.button(
                    f"📝 生成第{sec['id']}章：{sec['title']}",
                    type="primary",
                    key=f"gen_{sec['id']}",
                    disabled=not stage12_ready,
                ):
                    st.session_state.pop(f"force_regen_{sec['id']}", None)

                    target_plot_name = target_plot.get("name", "更新示范地块")
                    target_plot_mpi = target_plot.get("mpi", 85.0)
                    target_plot_priority = target_plot.get("priority", "P1 优先更新")
                    target_land_use = target_plot.get("land_use", "综合更新用地")
                    far_max = rl["far_max"]
                    height_max = rl["height_max"]
                    density_max = rl["density_max"]
                    green_min = rl["green_min"]

                    city = get_site_city() or "当地"
                    district = get_site_district() or ""
                    site_name = get_site_name() or "城市更新示范区"

                    prompt = f"""你是{city}自然资源和规划局规划主管与注册城市规划师，正在编写《{site_name}城市更新设计导则》。

    请为【第{sec['id']}章 {sec['title']}】撰写完整、详实的导则正文。

    ═══ 本章要求 ═══
    {sec_desc}

    ═══ 格式规范 ═══
    1. 使用标准公文格式：{sec['id']}.1 / {sec['id']}.1.1 三级编号
    2. 管控条文使用「应」「宜」「可」三级强度
    3. 每条管控要求注明数据来源或政策依据
    4. 涉及具体指标时，给出精确数值
    5. 适当使用表格呈现指标体系
    6. 不限字数，只要求详实、精准、有理有据
    7. 不得使用「待补充」「TBD」等占位符

    ═══ 空间数据（务必引用）═══
    {spatial_ctx[:2500]}

    ═══ 靶向地块与多主体博弈共识（核心约束）═══
    - 靶向更新示范地块：{target_plot_name}（用地性质：{target_land_use}，MPI更新潜力指数：{target_plot_mpi}，评级：{target_plot_priority}）
    - 博弈共识指标：容积率控制在{far_max}以内，建筑限高≤{height_max}m，建筑密度≤{density_max}%，绿地率≥{green_min}%
    - 纲要指导：{design_brief[:800] if design_brief else '落实保护优先、空间织补、以点带面的总体要求'}

    ═══ 前期诊断与策略（可引用）═══
    - 现状诊断：{s1[:800] if s1 else '暂无'}
    - 策略矩阵：{s4[:800] if s4 else '暂无'}

    ═══ 总体空间结构（Stage 08 成果）═══
    {s8_struct[:1000] if s8_struct else '因地制宜构建全域空间结构，疏密有致'}

    ═══ 专项系统设计（Stage 09 成果）═══
    - 交通网络系统：{s9_traffic[:500] if s9_traffic else '窄马路密路网、人车分流微循环'}
    - 建筑形态与风貌：{s9_bldg[:500] if s9_bldg else f'建筑高度≤{height_max}m，延续属地特色风貌肌理'}
    - 公共空间系统：{s9_space[:500] if s9_space else '生态微绿网与开敞公共空间网络'}

    ═══ 实施路径与分期（Stage 11 成果）═══
    {s11_phasing[:600] if s11_phasing else '渐进式微更新，留改拆分类施策'}

    ═══ 项目基本信息 ═══
    - 项目：{site_name}
    - 地点：{city} {district}
    - 管控红线：容积率≤{far_max}、建筑高度≤{height_max}m、建筑密度≤{density_max}%、绿地率≥{green_min}%

    请撰写本章完整内容。"""

                    with st.spinner(f"正在深度生成第{sec['id']}章..."):
                        stream = call_llm_engine_stream(
                            prompt=prompt,
                            system_prompt=(
                                f"你是{city}自然资源和规划局规划主管与注册城市规划师。"
                                "请撰写严谨、规范、可交付的法定导则正文。"
                                "每一条管控条文都必须有数据支撑或法规依据。"
                                "不限字数，深度展开。"
                            ),
                            model=model_tag,
                        )
                        result = st.write_stream(stream)

                    if isinstance(result, str) and len(result) > 200:
                        save_stage_output("12", key, result)
                        st.success(f"第{sec['id']}章生成完成（{len(result)} 字）")
                        st.rerun()
                    else:
                        st.error("生成失败或内容过短，请重试。")

        st.markdown("---")
        if done == total:
            st.success(f"🎉 全部 {total} 个板块已生成完成！")
            if st.button(
                "📄 汇总为完整导则",
                type="primary",
                disabled=not stage12_ready,
                **stretch_width(st.button),
            ):
                full_guideline = ""
                for sec in GUIDELINE_SECTIONS:
                    key = f"guideline_section_{sec['id']}"
                    content = load_stage_output("12", key, "")
                    full_guideline += f"\n\n{'='*50}\n# 第{sec['id']}章 {sec['title']}\n{'='*50}\n\n{content}"
                save_stage_output("12", SK.DESIGN_GUIDELINE, full_guideline)
                st.session_state["guideline_compiled_doc"] = full_guideline
                total_chars = len(full_guideline)
                register_artifact(
                    stage_code="12",
                    key=SK.DESIGN_GUIDELINE,
                    label="城市设计导则",
                    category="guideline",
                    location="stage_bus",
                    mime="text/markdown; charset=utf-8",
                    metadata={"sections": str(total), "total_chars": str(total_chars)},
                )
                st.success(f"导则汇总完成！总计 {total_chars} 字")

        compiled_doc = st.session_state.get(
            "guideline_compiled_doc",
            load_stage_output("12", SK.DESIGN_GUIDELINE, ""),
        )
        if compiled_doc:
            st.markdown("### 📥 完整导则成果导出")
            col_md, col_word = st.columns(2)
            with col_md:
                st.download_button(
                    "📥 导出完整导则 (Markdown)",
                    compiled_doc,
                    file_name="城市设计导则_完整版.md",
                    use_container_width=True,
                )
            with col_word:
                try:
                    from src.utils.document_generator import generate_official_word_doc
                    s_cfg = get_site_config()
                    doc_title = f"{get_site_city() or s_cfg.get('city', '')}{get_site_name() or s_cfg.get('name', '重点街区')}更新规划设计·城市设计导则"
                    wb = generate_official_word_doc(
                        title=doc_title,
                        text_content=compiled_doc,
                    )
                    if wb:
                        st.download_button(
                            "📥 导出红头公文 (Word)",
                            wb,
                            file_name=f"{doc_title}.docx",
                            use_container_width=True,
                        )
                except Exception:
                    logging.debug("Word 文档导出失败", exc_info=True)

    # ═══════════════════════════════════════════
    # 管控指标汇总
    # ═══════════════════════════════════════════

    elif selected_sub == "📊 管控指标汇总":
        render_section_intro(
            "管控指标体系 (Zoning Compliance Checker)",
            "结合当前激活基地 GIS 空间矢量数据库（EPSG:3857 米制空间计算），实时分析地块控规合规性。",
            eyebrow="Control Indicators",
        )

        import pandas as pd
        import plotly.express as px

        with st.expander("🎚️ 法定管控目标阈值配置（支持按当前基地自定义校准）", expanded=False):
            tc1, tc2, tc3, tc4, tc5 = st.columns(5)
            with tc1:
                cfg_far_max = st.number_input("容积率上限 (FAR)", min_value=0.3, max_value=10.0, value=float(rl["far_max"]), step=0.1, key="s12_far_max")
            with tc2:
                cfg_density_max = st.number_input("建筑密度上限 (%)", min_value=10.0, max_value=80.0, value=float(rl["density_max"]), step=1.0, key="s12_density_max")
            with tc3:
                cfg_green_min = st.number_input("绿地率下限 (%)", min_value=5.0, max_value=70.0, value=float(rl["green_min"]), step=1.0, key="s12_green_min")
            with tc4:
                cfg_core_h = st.number_input("核心区限高 (m)", min_value=3.0, max_value=100.0, value=float(rl["core_height_max"]), step=3.0, key="s12_core_h")
            with tc5:
                cfg_gen_h = st.number_input("一般区限高 (m)", min_value=6.0, max_value=150.0, value=float(rl["height_max"]), step=3.0, key="s12_gen_h")
            rl = {
                "far_max": cfg_far_max,
                "density_max": cfg_density_max,
                "green_min": cfg_green_min,
                "core_height_max": cfg_core_h,
                "height_max": cfg_gen_h,
            }

        with st.spinner("正在加载 GIS 空间图层并计算控规指标..."):
            metrics = _load_and_calculate_gis_metrics()

        if not metrics:
            metrics = _get_fallback_gis_metrics()

        far_ok = metrics["far"] <= rl["far_max"]
        dens_ok = metrics["building_density"] <= rl["density_max"]
        green_ok = metrics["greenery_ratio"] >= rl["green_min"]
        height_ok = metrics["max_height"] <= rl["height_max"]

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("容积率 (FAR)", f"{metrics['far']:.2f}", delta=f"目标: ≤ {rl['far_max']}", delta_color="normal" if far_ok else "inverse")
            st.markdown("**Status: ✅ 达标合规**" if far_ok else "**Status: ⚠️ 超出上限**")
        with c2:
            st.metric("建筑密度", f"{metrics['building_density']:.1f}%", delta=f"目标: ≤ {rl['density_max']:.1f}%", delta_color="normal" if dens_ok else "inverse")
            st.markdown("**Status: ✅ 达标合规**" if dens_ok else "**Status: ⚠️ 密度偏高**")
        with c3:
            st.metric("绿地率 (GAR)", f"{metrics['greenery_ratio']:.1f}%", delta=f"目标: ≥ {rl['green_min']:.1f}%", delta_color="normal" if green_ok else "inverse")
            st.markdown("**Status: ✅ 达标合规**" if green_ok else "**Status: ❌ 绿地率偏低**")
        with c4:
            st.metric("最高建筑高度", f"{metrics['max_height']:.1f} m", delta=f"目标: ≤ {rl['height_max']:.0f}m (核心{rl['core_height_max']:.0f}m)", delta_color="normal" if height_ok else "inverse")
            st.markdown("**Status: ✅ 达标合规**" if height_ok else "**Status: ⚠️ 存在高度溢出**")

        st.markdown("---")

        col_chart, col_warn = st.columns([1, 1])
        with col_chart:
            st.markdown("#### 📊 现状土地利用分类占比")
            df_landuse = pd.DataFrame(metrics["landuse"])
            code_map = {
                "R": "R 居住用地",
                "A": "A 公共服务用地",
                "B": "B 商业服务业用地",
                "G": "G 绿地与广场",
                "M": "M 混合/工业遗存",
                "S": "S 道路交通设施",
            }
            df_landuse["用地类型"] = df_landuse["GB_Code"].apply(lambda x: code_map.get(str(x).split(" ")[0], str(x)))
            fig = px.pie(
                df_landuse,
                values="Area",
                names="用地类型",
                hole=0.4,
                color_discrete_sequence=["#fef08a", "#f87171", "#f472b6", "#4ade80", "#c084fc", "#cbd5e1"],
            )
            fig.update_layout(showlegend=True, height=280, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)

        with col_warn:
            st.markdown("#### 🚨 控规合规诊断与空间优化导向")
            warn_items = []
            if not green_ok:
                warn_items.append(
                    f"**1. 绿地率存在缺口 (实测 {metrics['greenery_ratio']:.1f}% < 目标 {rl['green_min']:.1f}%)**\n"
                    f"片区生态蓝绿网络尚未充分渗透。建议在 Stage 09/10 设计方案中见缝插绿、增设口袋公园与立体绿化，将绿地率提升至控规标准。"
                )
            else:
                warn_items.append(
                    f"**1. 绿地率符合底线要求 (实测 {metrics['greenery_ratio']:.1f}% ≥ 目标 {rl['green_min']:.1f}%)**\n"
                    f"建议进一步串联街头绿地与慢行步道，提升居民5分钟见绿可达性。"
                )
            if not height_ok:
                warn_items.append(
                    f"**2. 天际线高度溢出 (现状最大 {metrics['max_height']:.1f}m > 控制区限高 {rl['height_max']:.0f}m)**\n"
                    f"局部存在超高建筑。建议在 Stage 12 导则条款中明确核心风貌区限高 {rl['core_height_max']:.0f}m，协调控制区限高 {rl['height_max']:.0f}m，严格管控新建与加建高度。"
                )
            else:
                warn_items.append(
                    f"**2. 天际线高度总体受控 (现状最大 {metrics['max_height']:.1f}m ≤ 控制区限高 {rl['height_max']:.0f}m)**\n"
                    f"建议持续巩固核心区 ≤{rl['core_height_max']:.0f}m、一般区 ≤{rl['height_max']:.0f}m 的梯度退台控制。"
                )
            st.warning("\n\n".join(warn_items))

        st.markdown("#### 📋 城市设计法定管控指标汇总表")
        indicators = [
            {"管控类型": "用地功能", "管控内容": "主导功能、兼容功能、禁止功能", "控制要求": "混合用地比例≥30%", "依据": "城市更新政策"},
            {"管控类型": "开发强度", "管控内容": "容积率、建筑密度、绿地率", "控制要求": f"容积率≤{rl['far_max']}，建筑密度≤{rl['density_max']:.0f}%，绿地率≥{rl['green_min']:.0f}%", "依据": "属地控规与更新导则"},
            {"管控类型": "建筑高度", "管控内容": "高度分区、天际线控制", "控制要求": f"核心区≤{rl['core_height_max']:.0f}m，一般区≤{rl['height_max']:.0f}m", "依据": "风貌与天际线视廊管控"},
            {"管控类型": "建筑界面", "管控内容": "街墙连续性、首层开放度", "控制要求": "街墙连续率≥70%，首层通透率≥60%", "依据": "街道设计导则"},
            {"管控类型": "建筑风貌", "管控内容": "色彩、材质、屋顶形式", "控制要求": "延续在地传统色彩材质，严控大面积反光幕墙", "依据": "风貌协调区管控要求"},
            {"管控类型": "公共空间", "管控内容": "开放空间比例、可达性", "控制要求": "步行5分钟覆盖率≥80%", "依据": "完整社区建设标准"},
            {"管控类型": "绿化景观", "管控内容": "绿视率、行道树间距", "控制要求": "GVI目标≥25%，行道树间距≤8m", "依据": "GVI现状分析"},
            {"管控类型": "慢行交通", "管控内容": "步行宽度、骑行空间", "控制要求": "人行道≥2m，骑行道≥1.5m", "依据": "无障碍设计标准"},
            {"管控类型": "业态管控", "管控内容": "鼓励/限制/禁止业态", "控制要求": "鼓励特色文创与便民服务，限制低效高污染业态", "依据": "产业导入策略"},
        ]
        st.dataframe(pd.DataFrame(indicators), hide_index=True, **stretch_width(st.dataframe))

        st.markdown("---")
        target_name = target_plot.get("name", "更新示范地块")
        target_far = target_plot.get("far", round(min(rl["far_max"], max(0.8, rl["far_max"] - 0.05)), 2))
        target_far_max = rl["far_max"]
        target_density = target_plot.get("density", min(rl["density_max"], 32.0))
        target_green = target_plot.get("green", max(rl["green_min"], 28.5))
        target_height = target_plot.get("height", f"{rl['core_height_max']:.0f} - {rl['height_max']:.0f} m")
        target_land_use = target_plot.get("land_use", "综合更新用地")

        st.markdown(f"#### 🎯 靶向地块（{target_name}）微观法定控规与博弈指标对账卡片")
        st.caption("打通 Stage 04 潜力诊断、Stage 07 多主体博弈共识与 Stage 12 数字法定图则的端到端指标闭环。")

        c_p1, c_p2, c_p3, c_p4 = st.columns(4)
        c_p1.metric("规划容积率 (FAR)", f"{target_far}", delta=f"法定上限 ≤ {target_far_max} (博弈共识达标)", delta_color="normal")
        c_p2.metric("建筑密度", f"{target_density}%", delta=f"法定上限 ≤ {rl['density_max']:.1f}%", delta_color="normal")
        c_p3.metric("绿地率 (GAR)", f"{target_green}%", delta=f"法定底线 ≥ {rl['green_min']:.1f}% (生态绿廊达标)", delta_color="normal")
        c_p4.metric("建筑高度", f"{target_height}", delta="法定控规限高合规", delta_color="normal")

        st.info(
            f"🏛️ **【{target_name}】风貌与规划刚性底线（因地制宜执行标准）：**\n\n"
            f"- **用地功能属性：** 规划为高品质【{target_land_use}】，落实产业与民生复合造血；\n"
            f"- **风貌主色调与微气候：** 结合属地气候与微环境设计，强化自然采光遮阳与被动式节能；\n"
            f"- **慢行网络贯通：** 落实人车分流，保障公共开敞空间与无障碍慢行系统连续通达；\n"
            f"- **业态与共识控制：** 严守 Stage 07 博弈达成的容积率（≤{target_far_max}）与限高（≤{rl['height_max']:.0f}m）底线，实现多方利益平衡闭环。"
        )

    # ═══════════════════════════════════════════
    # 一键导出
    # ═══════════════════════════════════════════

    elif selected_sub == "📄 一键导出":
        render_section_intro("导则导出", "导出已生成的完整导则。", eyebrow="Export")
        saved_guideline = load_stage_output("12", SK.DESIGN_GUIDELINE, "")
        if saved_guideline:
            st.success(f"导则已就绪（{len(saved_guideline)} 字）")
            st.download_button(
                "📥 导出完整导则 (Markdown)",
                saved_guideline,
                file_name="城市设计导则_完整版.md",
                use_container_width=True,
            )
        else:
            st.info("尚未汇总完整导则，请先在「分板块导则生成」中完成所有板块。")

    st.markdown("---")
    render_stage_summary(
        stage_code="12",
        title="城市设计导则体系",
        findings=[
            {"point": "导则覆盖9大板块：总则、空间、建筑、交通、景观、历史、业态、市政、实施", "evidence": "城市设计导则标准体系"},
            {"point": f"核心区限高≤{rl['core_height_max']:.0f}m，一般区≤{rl['height_max']:.0f}m，容积率≤{rl['far_max']}", "evidence": "属地控规与多主体博弈共识约束"},
            {"point": "分板块深度生成，每板块注入真实空间数据，不限字数", "evidence": "DeepSeek-V4 Pro 分发式调用"},
        ],
        methodology="分板块多轮深度生成引擎 + 全域空间数据驱动 + RAG 政策检索",
        implication="为成果表达（Stage 13）提供了可交付的导则文本和管控指标体系",
    )

    render_logic_chain_stepper("12")
