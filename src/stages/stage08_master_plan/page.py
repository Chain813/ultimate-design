"""阶段 08：总体城市设计 —— 空间结构推演 + 用地优化沙盘 + AIGC 生形。

基于 Stage 07 策略矩阵与全域空间数据，通过 LLM 深度策划完成：
1. 总体空间结构推演（一核两轴多片多节点）
2. 用地结构交互式优化沙盘（模拟功能占比调整的冲击）
3. 概念总平面图 AIGC 生形引导

所有产出自动存入数据总线，供 Stage 09/10/11/12 读取。
"""

from pathlib import Path

import streamlit as st

from src.engines.llm_engine import call_llm_engine_stream
from src.engines.spatial_data_injector import (
    generate_spatial_insights,
    get_building_summary,
    get_full_spatial_context,
    get_key_plots_summary,
    get_landuse_summary,
)
from src.engines.spatial_engine import get_hud_statistics, get_skyline_features
from src.stages.common.workspace import render_stage_workspace
from src.stages.stage08_master_plan.config import STAGE08_WORKSPACE
from src.ui.app_shell import (
    render_engine_status_alert,
    render_logic_chain_stepper,
    render_top_nav,
)
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.module_summary import render_stage_summary
from src.ui.streamlit_compat import stretch_width
from src.workflow.approval_state import StageDependency, render_dependency_gate
from src.workflow.stage_data_bus import (
    load_stage_output,
    render_evidence_chain_bar,
    save_stage_output,
)
from src.workflow.stage_keys import SK


def _normalize_landuse_category(raw_val: object) -> str:
    """将中英文/OSM/国标用地类型统一映射为沙盘标准类别。"""
    s = str(raw_val or "").strip().lower()
    if not s or s in ("none", "nan", "null"):
        return "居住用地"
    if any(k in s for k in ["居住", "住宅", "宅", "residential", "apartments", "house", "living", "r2"]):
        return "居住用地"
    if any(k in s for k in ["商务", "办公", "科研设计", "office", "business", "b2"]):
        return "商业办公"
    if any(k in s for k in ["商业", "商服", "零售", "集贸", "市场", "commercial", "retail", "shop", "market", "b1"]):
        return "商业服务业"
    if any(k in s for k in ["绿地", "公园", "游园", "广场", "生态", "草地", "林", "park", "green", "grass", "meadow", "forest", "garden", "recreation", "g1"]):
        return "公园与绿地"
    if any(k in s for k in ["公共", "行政", "教育", "学校", "科研", "医疗", "医院", "文化", "体育", "文体", "public", "school", "university", "college", "hospital", "clinic", "civic", "institutional", "community", "a1", "a2", "a3", "a4", "a5"]):
        return "公共设施"
    if any(k in s for k in ["工业", "仓储", "物流", "厂", "industrial", "warehouse", "manufacturing", "m1", "m2", "w1"]):
        return "工业用地"
    if any(k in s for k in ["道路", "交通", "市政", "场站", "停车", "铁路", "road", "railway", "transport", "parking", "utility", "s1"]):
        return "交通场站"
    return "居住用地"


@st.cache_resource
def _load_raw_landuse_gdf_cached(landuse_path_str: str, boundary_path_str: str, mtime_key: float):
    import geopandas as gpd
    import numpy as np

    path = Path(landuse_path_str)
    if not path.exists():
        return None
    gdf = gpd.read_file(str(path))
    if gdf.empty:
        return None
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    gdf_proj = gdf.to_crs(epsg=3857)
    gdf_proj["area_sqm"] = gdf_proj.geometry.area

    # 统一归一化 Type 字段，兼容自定义上传 GeoJSON 与 OSM 抓取的 landuse/type/land_use 等属性列
    type_col = None
    for candidate_col in ("Type", "type", "land_type", "landuse", "land_use", "LandUse", "fclass", "GB_Code", "amenity"):
        if candidate_col in gdf_proj.columns:
            type_col = candidate_col
            break
    if type_col is not None:
        gdf_proj["Type"] = gdf_proj[type_col].apply(_normalize_landuse_category)
    else:
        gdf_proj["Type"] = "居住用地"

    boundary_path = Path(boundary_path_str)
    if boundary_path.exists():
        try:
            boundary_gdf = gpd.read_file(str(boundary_path))
            if boundary_gdf.crs is None:
                boundary_gdf = boundary_gdf.set_crs(epsg=4326)
            boundary_proj = boundary_gdf.to_crs(epsg=3857)
            boundary_geom = boundary_proj.geometry.unary_union
            in_mask = gdf_proj.geometry.centroid.within(boundary_geom)
            # 若自定义数据与边界投影后无交集或全部在边界外，则保底使用全部图斑
            gdf_proj["in_study_area"] = in_mask if in_mask.any() else True
        except Exception:
            gdf_proj["in_study_area"] = True
    else:
        gdf_proj["in_study_area"] = True

    centroids = gdf_proj.geometry.centroid
    cx_s = centroids.x
    cy_s = centroids.y

    minx, miny, maxx, maxy = gdf_proj.total_bounds
    midx = (minx + maxx) / 2.0
    midy = (miny + maxy) / 2.0
    dx = (maxx - minx) if (maxx - minx) > 0 else 1000.0
    dy = (maxy - miny) if (maxy - miny) > 0 else 1000.0

    centers = {
        "居住用地": (midx - 0.2 * dx, midy),
        "商业服务业": (midx + 0.15 * dx, midy - 0.15 * dy),
        "商业办公": (midx - 0.25 * dx, midy + 0.25 * dy),
        "公园与绿地": (midx + 0.3 * dx, midy + 0.1 * dy),
        "公共设施": (midx, midy),
    }

    for cat, (cx, cy) in centers.items():
        dists = np.sqrt((cx_s - cx) ** 2 + (cy_s - cy) ** 2)
        max_d = dists.max() if dists.max() > 0 else 1.0
        gdf_proj[f"decay_{cat}"] = 1.0 - (dists / max_d)

    return gdf_proj


def load_raw_landuse_gdf():
    """加载当前激活基地的用地 GeoDataFrame（自动感知学生切换基地或新上传文件）。"""
    from src.config import GIS_FILES, resolve_path

    lu_path = resolve_path(str(GIS_FILES["landuse"]))
    bd_path = resolve_path(str(GIS_FILES["boundary"]))
    mtime = lu_path.stat().st_mtime if lu_path.exists() else 0.0
    return _load_raw_landuse_gdf_cached(str(lu_path), str(bd_path), mtime)


def _compute_baseline_pcts(gdf_proj) -> list[float]:
    """根据当前激活的用地 GeoDataFrame 实时计算 6 大类现状基线占比 (%)。"""
    default_baseline = [53.0, 15.5, 8.5, 5.5, 6.0, 11.5]
    if gdf_proj is None or gdf_proj.empty or "Type" not in gdf_proj.columns:
        return default_baseline
    try:
        gdf_in = gdf_proj[gdf_proj["in_study_area"]] if "in_study_area" in gdf_proj.columns else gdf_proj
        if gdf_in.empty:
            gdf_in = gdf_proj
        total_area = float(gdf_in["area_sqm"].sum())
        if total_area <= 0:
            return default_baseline
        grouped = gdf_in.groupby("Type")["area_sqm"].sum().to_dict()
        res = round(grouped.get("居住用地", 0.0) / total_area * 100.0, 1)
        com = round(grouped.get("商业服务业", 0.0) / total_area * 100.0, 1)
        off = round(grouped.get("商业办公", 0.0) / total_area * 100.0, 1)
        grn = round(grouped.get("公园与绿地", 0.0) / total_area * 100.0, 1)
        pub = round(grouped.get("公共设施", 0.0) / total_area * 100.0, 1)
        other = round(max(0.0, 100.0 - (res + com + off + grn + pub)), 1)
        return [res, com, off, grn, pub, other]
    except Exception:
        return default_baseline


def render_page() -> None:
    render_top_nav()
    render_engine_status_alert()

    stats = get_hud_statistics()
    sky = get_skyline_features()

    graphic_svg = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 200" width="100%" height="100%" style="max-width: 600px; filter: drop-shadow(0 8px 16px rgba(0,0,0,0.04));">
      <defs>
        <linearGradient id="g_base" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#ffffff"/>
          <stop offset="100%" stop-color="#f5f5f7"/>
        </linearGradient>
        <linearGradient id="g_out" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="rgba(175, 82, 222, 0.03)"/>
          <stop offset="100%" stop-color="rgba(175, 82, 222, 0.08)"/>
        </linearGradient>
      </defs>

      <path d="M 160 55 C 180 55, 180 45, 200 45" fill="none" stroke="#34c759" stroke-width="1.5" stroke-dasharray="4,3"/>
      <path d="M 160 55 C 180 55, 180 155, 200 155" fill="none" stroke="#d1d1d6" stroke-width="1" stroke-dasharray="3,3"/>
      <path d="M 160 145 C 180 145, 180 45, 200 45" fill="none" stroke="#d1d1d6" stroke-width="1" stroke-dasharray="3,3"/>
      <path d="M 160 145 C 180 145, 180 155, 200 155" fill="none" stroke="#0071e3" stroke-width="1.5" stroke-dasharray="4,3"/>

      <path d="M 360 45 C 385 45, 385 100, 410 100" fill="none" stroke="#af52de" stroke-width="2" stroke-dasharray="5,4"/>
      <path d="M 360 155 C 385 155, 385 100, 410 100" fill="none" stroke="#af52de" stroke-width="2" stroke-dasharray="5,4"/>
      <polygon points="405,96 410,100 405,104" fill="#af52de"/>

      <rect x="10" y="35" width="150" height="40" rx="8" fill="url(#g_base)" stroke="#34c759" stroke-width="1.2"/>
      <text x="85" y="52" fill="#34c759" font-size="12" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle" font-weight="bold">前期策略框架</text>
      <text x="85" y="66" fill="#86868b" font-size="9" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle">Stage 07 共识协议</text>

      <rect x="10" y="125" width="150" height="40" rx="8" fill="url(#g_base)" stroke="#0071e3" stroke-width="1.2"/>
      <text x="85" y="142" fill="#0071e3" font-size="12" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle" font-weight="bold">全域空间数据</text>
      <text x="85" y="156" fill="#86868b" font-size="9" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle">土地利用与建筑总量</text>

      <rect x="200" y="25" width="160" height="40" rx="8" fill="url(#g_base)" stroke="#0071e3" stroke-width="1.5"/>
      <text x="280" y="42" fill="#1d1d1f" font-size="12" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle" font-weight="bold">LLM 空间结构推演</text>
      <text x="280" y="56" fill="#0071e3" font-size="10" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle" font-weight="bold">DeepSeek 深度策划</text>

      <rect x="200" y="135" width="160" height="40" rx="8" fill="url(#g_base)" stroke="#0071e3" stroke-width="1.5"/>
      <text x="280" y="152" fill="#1d1d1f" font-size="12" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle" font-weight="bold">用地优化沙盘模拟</text>
      <text x="280" y="166" fill="#0071e3" font-size="10" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle" font-weight="bold">功能占比与冲击计算</text>

      <rect x="410" y="70" width="160" height="60" rx="10" fill="url(#g_out)" stroke="#af52de" stroke-width="2"/>
      <text x="490" y="97" fill="#af52de" font-size="14" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle" font-weight="bold">概念总平面 AIGC 生形</text>
      <text x="490" y="117" fill="#1d1d1f" font-size="11" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle">辅助形体生成与落位</text>

      <circle cx="160" cy="55" r="3" fill="#34c759"/>
      <circle cx="160" cy="145" r="3" fill="#0071e3"/>
      <circle cx="410" cy="100" r="3" fill="#af52de"/>
    </svg>
    """

    render_page_banner(
        title="总体城市设计",
        description="基于前期策略框架与全域空间数据，通过 LLM 深度推演完成空间结构策划、"
                    "用地结构优化沙盘模拟和 AIGC 辅助概念总平面图生形。",
        eyebrow="Stage 08",
        tags=["空间结构推演", "用地优化沙盘", "概念总平面", "AIGC 生形"],
        metrics=[
            {"value": str(stats.get("poi_count", "N/A")), "label": "POI", "meta": "活力测度"},
            {"value": f"{sky.get('avg_height', 0)} m", "label": "平均层高", "meta": "形态参考"},
            {"value": f"{sky.get('building_count', 0)}", "label": "建筑总量", "meta": "栋"},
        ],
        graphic_html=graphic_svg
    )
    render_evidence_chain_bar("08", ["07", "08", "09", "10"])

    with st.sidebar:
        model_tag = st.selectbox(
            "DeepSeek 模型",
            ["deepseek-v4-flash", "deepseek-v4-pro"],
            index=1,  # 空间结构推演属于深度策划任务，默认 Pro
            key="p8_model",
            help="deepseek-v4-pro 适合空间结构的深度推演，deepseek-v4-flash 适合快速迭代",
        )

    active = render_stage_workspace(STAGE08_WORKSPACE)
    selected_sub = active.label
    st.markdown("---")

    stage08_ready = render_dependency_gate(
        [StageDependency("07", SK.STRATEGY_MATRIX, "策略共识矩阵", approval_required=True)],
        title="Stage 08 生成前置条件",
    )
    if not stage08_ready:
        if st.checkbox("⚡ 快速推演模式（跳过前序依赖与审批，直接启用生成）", key="p08_bypass_gate", value=False):
            stage08_ready = True

    from src.config.site import get_site_city, get_site_config, get_site_name
    site_cfg = get_site_config()
    site_name = get_site_name() or site_cfg.get("name", "示范重点片区") or "示范重点片区"
    site_city = get_site_city() or site_cfg.get("city", "当地") or "当地"
    site_area = site_cfg.get("area_ha", 160)

    # ═══════════════════════════════════════════
    # 空间数据面板 —— 始终显示
    # ═══════════════════════════════════════════
    with st.expander("📊 空间数据概览（驱动本阶段所有分析）", expanded=False):
        t1, t2 = st.tabs(["📊 数据清单", "🧠 AI 深度空间洞察"])
        with t1:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("#### 🏘️ 土地利用")
                st.code(get_landuse_summary(), language="text")
            with c2:
                st.markdown("#### 🏗️ 建筑形态")
                st.code(get_building_summary(), language="text")
            with c3:
                st.markdown("#### 🏗️ 重点更新单元")
                st.code(get_key_plots_summary(), language="text")
        with t2:
            if "spatial_insights" not in st.session_state:
                st.session_state["spatial_insights"] = ""

            if st.session_state["spatial_insights"] == "":
                c_ins1, c_ins2 = st.columns([3, 1])
                with c_ins1:
                    st.caption("✨ AI 正在整合当前的研究范围土地利用、建筑总量、重点地块等 GIS 信息进行跨维度关联诊断。")
                with c_ins2:
                    if st.button("🧠 生成深度空间洞察", key="btn_gen_spatial_insights", use_container_width=True):
                        with st.spinner("AI 正在运行多维空间特征关联分析..."):
                            insights = generate_spatial_insights()
                            st.session_state["spatial_insights"] = insights
                            st.rerun()
            else:
                st.markdown(st.session_state["spatial_insights"])
                if st.button("🔄 重新分析", key="btn_re_spatial_insights"):
                    st.session_state["spatial_insights"] = ""
                    st.rerun()

    # ═══════════════════════════════════════════
    # 模块一：空间结构推演
    # ═══════════════════════════════════════════

    if selected_sub == "🗺️ 空间结构推演":
        render_section_intro(
            "总体空间结构推演",
            "基于 Stage 07 策略矩阵和全域空间数据，推演研究范围的"
            "总体空间结构（如'一核两轴多片多节点'），明确各片区的功能定位与空间组织。",
            eyebrow="Spatial Structure",
        )

        # 加载上游数据
        strategy = load_stage_output("07", SK.STRATEGY_MATRIX, "")
        design_concept = load_stage_output("06", SK.DESIGN_CONCEPT, "")
        design_brief = load_stage_output("07", SK.DESIGN_BRIEF, "")
        target_plot = load_stage_output("04", "target_plot", {}) or load_stage_output("07", "target_plot", {})

        with st.expander("📋 前序策略矩阵、设计纲要与靶向地块（来自 Stage 04/07）", expanded=False):
            if target_plot:
                st.markdown(
                    f"**🎯 靶向重点地块：** {target_plot.get('name', f'{site_name}首选更新单元')} | "
                    f"**MPI 得分：** {target_plot.get('mpi', 85.0)} | "
                    f"**更新等级：** {target_plot.get('priority', 'P1 优先更新')}"
                )
                if target_plot.get("issues"):
                    st.caption("现状短板：" + "、".join(target_plot["issues"]))
            if strategy:
                st.markdown(strategy)
            elif design_brief:
                st.markdown(design_brief)
            else:
                st.info("暂无策略矩阵数据，请先完成 Stage 07 三方协同推演。")

        # 高精度底图对照
        master_img = Path("output/high_precision/总体语义底稿图_Masterplan_Semantic.png")
        if master_img.exists():
            with st.expander("🗺️ 高精度语义底稿图（矢量渲染 300DPI）", expanded=False):
                st.image(str(master_img), caption="总体语义底稿图 — 研究范围及周边1km", use_container_width=True)

        if st.button(
            "🗺️ 生成空间结构推演报告",
            type="primary",
            key="s8_structure",
            disabled=not stage08_ready,
            **stretch_width(st.button),
        ):
            spatial_ctx = get_full_spatial_context()
            target_name = target_plot.get("name", f"{site_name}首选更新单元")
            target_mpi = target_plot.get("mpi", 85.0)
            target_issues_list = target_plot.get("issues", [])
            target_issues = "、".join(target_issues_list) if target_issues_list else "空间功能低效闲置、微循环交通不畅、公共空间品质不足"
            brief_text = str(design_brief or "")
            target_consensus = brief_text[:200] if brief_text else "因地制宜空间织补、保留重要肌理与风貌特征、完善公共服务配套、严守法定控规红线"

            prompt = f"""你是一位资深城市设计总师，精通空间结构分析与功能分区策划。

    基于以下前期分析数据，为**整个研究范围（{site_city}{site_name}，约{site_area}公顷）**推演总体空间结构。

    【前期设计目标（Stage 06）】：{str(design_concept or '')[:2000] or f'因地制宜·数智织补——AI赋能下的{site_city}{site_name}微更新规划设计'}
    【策略矩阵（Stage 07）】：{str(strategy or '')[:2000] or '政策引导→产业导入→经济盘活→空间更新的良性循环'}
    【设计纲要指导框架（Stage 07）】：{str(design_brief or '')[:2000] or '落实保护优先、空间织补、以点带面的总体要求'}
    【靶向更新地块与博弈共识】：重点靶向地块【{target_name}】（MPI更新潜力指数：{target_mpi}，现状短板：{target_issues}）。多主体博弈共识：{target_consensus}。
    【全域空间数据】：{spatial_ctx[:4000]}

    请生成【总体空间结构推演报告】，按以下框架展开（不限字数，务必详实）：

    一、总体空间结构概念
      - 提炼一句话概括空间结构（如"一核两轴多片多节点"）
      - 用 300 字以上阐释其内涵与逻辑，说明如何以【{target_name}】为针灸触媒辐射带动周边街区

    二、核心区域定位（逐片区展开）
      对每个片区/功能区，详细说明：
      - 范围描述（结合具体地块名称和面积数据，重点展开【{target_name}】片区的功能升级）
      - 功能定位（主导功能 + 辅助功能，严格落实"{target_consensus}"）
      - 开发强度建议（容积率、建筑密度、限高参考，严格落实属地法定控规红线）
      - 与周边片区的空间关系和交通联系

    三、轴线与廊道体系
      - 主轴（功能、空间特征、沿线节点）
      - 次轴与联络廊道（打通【{target_name}】与周边慢行开放空间渗透走廊，缝合周边街区肌理）
      - 绿色廊道与视线通廊（结合天际线与视廊保护要求）

    四、节点体系
      - 门户节点、文化节点、商业节点、社区节点等
      - 每个节点的空间定位和功能配置（将【{target_name}】定位为更新示范触媒节点）

    五、开发强度分区图则
      以表格形式列出各分区的容积率、建筑密度、绿地率、限高建议。
      | 分区名称 | 主导功能 | 容积率 | 建筑密度 | 绿地率 | 限高 |

    六、与前期策略的对应关系
      说明空间结构如何回应 Stage 06/07 的目标和策略，以及如何贯彻原住居民/使用者、投资开发运营商、规划监督责任人的三方因地制宜博弈共识。

    每一条论述都必须引用具体的空间数据（面积、比例、高度、POI 数量等），禁止空泛陈述。"""

            stream = call_llm_engine_stream(
                prompt=prompt,
                system_prompt=(
                    "资深城市设计总师。推演必须严格基于空间量化数据，"
                    "每个功能分区须落到具体的地块和面积，禁止泛泛而谈。"
                ),
                model=model_tag,
            )
            result = st.write_stream(stream)
            if isinstance(result, str) and len(result) > 200:
                save_stage_output("08", SK.SPATIAL_STRUCTURE, result)
                st.success(f"✅ 空间结构推演报告生成完成（{len(result)} 字），已存入数据总线。")

        saved_structure = load_stage_output("08", SK.SPATIAL_STRUCTURE, "")
        if saved_structure and not st.session_state.get("s8_structure"):
            with st.expander("📋 已生成的空间结构推演报告", expanded=True):
                st.markdown(saved_structure)

    # ═══════════════════════════════════════════
    # 模块二：用地结构优化沙盘
    # ═══════════════════════════════════════════

    elif selected_sub == "🎛️ 用地结构优化沙盘":
        gdf_proj = load_raw_landuse_gdf()
        baseline_pcts = _compute_baseline_pcts(gdf_proj)

        sandbox_data = load_stage_output("08", SK.LANDUSE_SANDBOX, {})
        if sandbox_data:
            if "sb_res" not in st.session_state:
                st.session_state["sb_res"] = sandbox_data.get("res_pct", 48)
            if "sb_com" not in st.session_state:
                st.session_state["sb_com"] = sandbox_data.get("com_pct", 16)
            if "sb_off" not in st.session_state:
                st.session_state["sb_off"] = sandbox_data.get("off_pct", 8)
            if "sb_green" not in st.session_state:
                st.session_state["sb_green"] = sandbox_data.get("green_pct", 10)
            if "sb_pub" not in st.session_state:
                st.session_state["sb_pub"] = sandbox_data.get("public_pct", 6)

        render_section_intro(
            "用地结构优化沙盘",
            "交互式模拟不同用地功能占比的调整方案，"
            "LLM 实时评估结构变动对经济活力、环境承载力和社区品质的冲击。",
            eyebrow="Landuse Sandbox",
        )

        render_summary_cards([
            {"value": "交互式推演", "title": "沙盘模式", "desc": "调整滑块，实时评估"},
            {"value": "数据驱动", "title": "评估依据", "desc": f"当前基地：{site_city}{site_name}"},
        ])

        st.markdown("#### 📐 当前用地结构（基线）")
        st.code(get_landuse_summary(), language="text")

        st.markdown("#### 🎛️ 目标用地结构调整")
        st.caption("拖动滑块模拟不同的用地功能占比方案，系统将评估其影响。")

        col_sandbox_left, col_sandbox_right = st.columns([1.1, 0.9])

        with col_sandbox_left:
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                res_pct = st.slider("🏠 居住用地占比 (%)", 5, 80, 48, key="sb_res")
                com_pct = st.slider("🏪 商业服务业用地占比 (%)", 2, 50, 16, key="sb_com")
                off_pct = st.slider("🏢 商务办公用地占比 (%)", 2, 40, 8, key="sb_off")
            with col_s2:
                green_pct = st.slider("🌳 公园绿地占比 (%)", 3, 50, 10, key="sb_green")
                public_pct = st.slider("🏛️ 公共设施用地占比 (%)", 2, 35, 6, key="sb_pub")
                total = res_pct + com_pct + off_pct + green_pct + public_pct
                remain = max(0, 100 - total)
                st.metric("📊 剩余（道路/市政等）", f"{remain}%")
                if total > 100:
                    st.error(f"⚠️ 功能用地占比之和 ({total}%) 超过 100%，请调整。")

            # 用地结构实时可视化对比图表
            try:
                import plotly.graph_objects as go
                categories = ["居住用地 🏠", "商业用地 🏪", "商务办公 🏢", "公园绿地 🌳", "公共设施 🏛️", "道路/市政 📊"]
                scenario_pcts = [res_pct, com_pct, off_pct, green_pct, public_pct, remain]

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    y=categories,
                    x=baseline_pcts,
                    name="现状基线 (Baseline)",
                    orientation="h",
                    marker=dict(color="rgba(148, 163, 184, 0.4)", line=dict(color="rgb(148, 163, 184)", width=1)),
                ))
                fig.add_trace(go.Bar(
                    y=categories,
                    x=scenario_pcts,
                    name="沙盘方案 (Scenario)",
                    orientation="h",
                    marker=dict(color="rgba(56, 189, 248, 0.8)", line=dict(color="rgb(56, 189, 248)", width=1)),
                ))

                fig.update_layout(
                    title=dict(text="📊 用地占比实时对比：现状基线 vs 沙盘方案", font=dict(color="#1e293b", size=14)),
                    barmode="group",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(
                        title=dict(text="占比 (%)", font=dict(color="#475569")),
                        tickfont=dict(color="#475569"),
                        gridcolor="rgba(148, 163, 184, 0.1)",
                        range=[0, 100],
                    ),
                    yaxis=dict(
                        tickfont=dict(color="#1e293b"),
                        autorange="reversed",
                    ),
                    legend=dict(
                        font=dict(color="#475569"),
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                    ),
                    height=320,
                    margin=dict(l=20, r=20, t=40, b=20),
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"图表加载失败：{e}")

        with col_sandbox_right:
            # 用地结构实时空间落位图
            try:
                if gdf_proj is not None and not gdf_proj.empty:
                    # 1. 计算研究范围内的目标面积
                    gdf_in = gdf_proj[gdf_proj["in_study_area"]]
                    total_area_in = gdf_in["area_sqm"].sum()
                    target_pcts = {
                        "居住用地": res_pct,
                        "商业服务业": com_pct,
                        "商业办公": off_pct,
                        "公园与绿地": green_pct,
                        "公共设施": public_pct,
                    }
                    target_areas = {k: total_area_in * (v / 100.0) for k, v in target_pcts.items()}

                    # 2. 计算各宗地关于各功能类别的得分 (考虑现状与空间中心邻近度)
                    scores = {}
                    for cat in target_pcts:
                        decay = gdf_proj[f"decay_{cat}"]
                        if cat == "公共设施":
                            is_orig = gdf_proj["Type"].isin(["公共设施", "医疗卫生", "教育科研", "体育文化", "行政办公"])
                        else:
                            is_orig = gdf_proj["Type"] == cat
                        scores[cat] = is_orig.astype(float) * 2.0 + decay * 1.0

                    # 3. 贪婪算法空间分配 (仅限研究范围内)
                    import pandas as pd
                    allocated = pd.Series(True, index=gdf_proj.index)
                    allocated[gdf_proj["in_study_area"]] = False
                    allocated_types = gdf_proj["Type"].copy()

                    # 按开发优先级排序分配
                    priority = ["商业服务业", "商业办公", "公园与绿地", "公共设施", "居住用地"]
                    for cat in priority:
                        target_a = target_areas[cat]
                        cat_scores = scores[cat].copy()
                        cat_scores[allocated] = -999.0
                        sorted_idx = cat_scores.sort_values(ascending=False).index

                        current_a = 0.0
                        for idx in sorted_idx:
                            if allocated[idx]:
                                continue
                            p_area = gdf_proj.loc[idx, "area_sqm"]
                            allocated_types.loc[idx] = cat
                            allocated[idx] = True
                            current_a += p_area
                            if current_a >= target_a:
                                break

                    # 研究范围内剩余未分配的地块作为道路/市政 (交通场站)
                    unallocated_in = (~allocated) & gdf_proj["in_study_area"]
                    allocated_types[unallocated_in] = "交通场站"

                    # 4. Matplotlib 绘制空间落位图
                    import matplotlib.font_manager as fm
                    import matplotlib.pyplot as plt
                    from matplotlib.patches import Patch

                    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun", "sans-serif"]
                    plt.rcParams["axes.unicode_minus"] = False

                    fig, ax = plt.subplots(figsize=(6, 5.5), facecolor="none")
                    fig.patch.set_alpha(0.0)
                    ax.patch.set_alpha(0.0)

                    color_map = {
                        "居住用地": "#FDE047",
                        "商业服务业": "#EF4444",
                        "商业办公": "#C084FC",
                        "公园与绿地": "#22C55E",
                        "公共设施": "#F87171",
                        "医疗卫生": "#F87171",
                        "教育科研": "#F87171",
                        "体育文化": "#F87171",
                        "行政办公": "#F87171",
                        "交通场站": "#94A3B8",
                        "工业用地": "#64748B",
                    }

                    gdf_out = gdf_proj[~gdf_proj["in_study_area"]]
                    if not gdf_out.empty:
                        colors_out = gdf_out["Type"].map(color_map).fillna("#CBD5E1")
                        gdf_out.plot(ax=ax, color=colors_out, edgecolor="#CBD5E1", linewidth=0.1, alpha=0.35)

                    if not gdf_in.empty:
                        allocated_types_in = allocated_types[gdf_proj["in_study_area"]]
                        colors_in = allocated_types_in.map(color_map).fillna("#CBD5E1")
                        gdf_in.plot(ax=ax, color=colors_in, edgecolor="#1E293B", linewidth=0.25, alpha=1.0)

                    ax.set_axis_off()

                    font_prop = fm.FontProperties(family=["Microsoft YaHei", "SimHei", "sans-serif"], size=8)
                    legend_elements = [
                        Patch(facecolor="#FDE047", edgecolor="#475569", label="居住用地 (R)"),
                        Patch(facecolor="#EF4444", edgecolor="#475569", label="商业服务 (B)"),
                        Patch(facecolor="#C084FC", edgecolor="#475569", label="商业办公 (B)"),
                        Patch(facecolor="#22C55E", edgecolor="#475569", label="公园绿地 (G)"),
                        Patch(facecolor="#F87171", edgecolor="#475569", label="公共设施 (A)"),
                        Patch(facecolor="#94A3B8", edgecolor="#475569", label="道路/市政 (S)"),
                    ]
                    ax.legend(handles=legend_elements, loc="lower left", prop=font_prop, facecolor="none", edgecolor="none", labelcolor="#1e293b")

                    plt.tight_layout()
                    st.pyplot(fig)
                else:
                    st.warning("⚠️ 无法加载用地数据进行空间分配模拟。")
            except Exception as e:
                st.error(f"空间落位图渲染失败：{e}")

        if total <= 100 and st.button(
            "🔍 评估此方案的影响",
            type="primary",
            key="s8_sandbox",
            disabled=not stage08_ready,
            **stretch_width(st.button),
        ):
            scenario = (
                f"居住 {res_pct}%, 商业 {com_pct}%, 办公 {off_pct}%, "
                f"绿地 {green_pct}%, 公共设施 {public_pct}%, 其他(道路/市政) {remain}%"
            )
            prompt = f"""你是一位城市规划经济学家，精通城市更新中的用地结构优化。

    研究范围（{site_city}{site_name}，约{site_area}公顷）的现状用地结构为：
    {get_landuse_summary()}

    规划师拟将用地结构调整为：
    {scenario}

    请评估此用地结构调整方案的影响，按以下维度展开（每个维度 200+ 字）：

    一、经济活力影响
      - 商业活力变化预判（结合 POI 密度现状）
      - 就业岗位变化估算
      - 税收和地价影响

    二、环境承载力影响
      - 绿地率变化与 GVI 改善预期
      - 开放空间可达性变化
      - 碳排放变化估算

    三、社区品质影响
      - 公共服务设施配比变化
      - 15 分钟生活圈覆盖度变化
      - 人口承载力变化

    四、风险提示
      - 此方案可能带来的负面效果
      - 建议的缓解措施

    五、综合评级
      以百分制打分（经济活力 / 环境承载 / 社区品质各占权重），并给出一句话结论。

    必须引用空间数据中的具体数字作为论据。"""

            stream = call_llm_engine_stream(
                prompt=prompt,
                system_prompt="城市规划经济学家，精通用地结构与经济活力的定量关系。",
                model=model_tag,
            )
            result = st.write_stream(stream)
            if isinstance(result, str) and len(result) > 100:
                save_stage_output("08", SK.LANDUSE_SANDBOX, {
                    "scenario": scenario,
                    "evaluation": result,
                    "res_pct": res_pct,
                    "com_pct": com_pct,
                    "off_pct": off_pct,
                    "green_pct": green_pct,
                    "public_pct": public_pct,
                    "remain": remain,
                })
                st.success("✅ 沙盘评估完成，已存入数据总线。")

        if sandbox_data and "evaluation" in sandbox_data and not st.session_state.get("s8_sandbox"):
            st.markdown("#### 📋 沙盘方案评估报告")
            st.info(f"方案：{sandbox_data['scenario']}")
            st.markdown(sandbox_data["evaluation"])

    st.markdown("---")
    render_stage_summary(
        stage_code="08",
        title="总体空间结构与用地优化",
        findings=[
            {"point": "空间结构推演基于全域量化数据，覆盖核心区、轴线、廊道、节点四大体系", "evidence": "Stage 07 策略矩阵 + 全域空间数据"},
            {"point": "用地结构优化沙盘支持交互式占比调整与 LLM 实时冲击评估", "evidence": "用地矢量基线 + 情景模拟"},
            {"point": "AIGC 辅助概念总平面生形，约束条件源自空间结构推演结果", "evidence": "Stable Diffusion + ControlNet"},
        ],
        methodology="基于 DeepSeek V4 Pro 的空间结构深度推演 + 用地结构交互式沙盘模拟",
        implication="为专项系统设计（Stage 09）和重点地段深化（Stage 10）提供了总体空间骨架和开发强度分区",
    )

    # 业务逻辑主线推进导航
    render_logic_chain_stepper("08")
