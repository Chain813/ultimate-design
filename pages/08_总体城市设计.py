"""阶段 08：总体城市设计 —— 空间结构推演 + 用地优化沙盘 + AIGC 生形。

基于 Stage 07 策略矩阵与全域空间数据，通过 LLM 深度策划完成：
1. 总体空间结构推演（一核两轴多片多节点）
2. 用地结构交互式优化沙盘（模拟功能占比调整的冲击）
3. 概念总平面图 AIGC 生形引导

所有产出自动存入数据总线，供 Stage 09/10/11/12 读取。
"""

from pathlib import Path

import streamlit as st
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.ui.module_summary import render_stage_summary
from src.engines.llm_engine import call_llm_engine_stream
from src.engines.spatial_data_injector import (
    get_full_spatial_context,
    get_landuse_summary,
    get_key_plots_summary,
    get_building_summary,
    generate_spatial_insights,
)
from src.engines.spatial_engine import get_hud_statistics, get_skyline_features
from src.workflow.stage_data_bus import (
    save_stage_output, load_stage_output, render_evidence_chain_bar,
)
from src.workflow.stage_keys import SK
from src.ui.drawing_prompt_ui import render_drawing_prompt_ui
from src.ui.streamlit_compat import stretch_width

@st.cache_resource
def load_raw_landuse_gdf():
    import geopandas as gpd
    import numpy as np
    from shapely.geometry import Point
    from src.config import resolve_path, GIS_FILES
    
    path = resolve_path(str(GIS_FILES["landuse"]))
    if not path.exists():
        return None
    gdf = gpd.read_file(str(path))
    gdf_proj = gdf.to_crs(epsg=3857)
    gdf_proj["area_sqm"] = gdf_proj.geometry.area
    
    # Identify features within the research scope (boundary)
    boundary_path = resolve_path(str(GIS_FILES["boundary"]))
    if boundary_path.exists():
        boundary_gdf = gpd.read_file(str(boundary_path))
        boundary_proj = boundary_gdf.to_crs(epsg=3857)
        boundary_geom = boundary_proj.geometry.unary_union
        gdf_proj["in_study_area"] = gdf_proj.geometry.centroid.within(boundary_geom)
    else:
        gdf_proj["in_study_area"] = True
    
    # Calculate centroids
    centroids = gdf_proj.geometry.centroid
    cx_s = centroids.x
    cy_s = centroids.y
    
    # Predefine centers in EPSG:3857
    def get_xy(lon, lat):
        p = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(epsg=3857)
        return p.iloc[0].x, p.iloc[0].y
        
    centers = {
        "居住用地": get_xy(125.3350, 43.9030),      # 社区中西侧居住组团
        "商业服务业": get_xy(125.3475, 43.9017),    # 商业街区/光复路
        "商业办公": get_xy(125.3250, 43.9080),      # 长春站站前枢纽
        "公园与绿地": get_xy(125.3590, 43.9010),    # 伊通河沿岸生态带
        "公共设施": get_xy(125.3422, 43.9036)       # 伪满皇宫核心区
    }
    
    # Precompute distance decay for each category
    for cat, (cx, cy) in centers.items():
        dists = np.sqrt((cx_s - cx)**2 + (cy_s - cy)**2)
        max_d = dists.max() if dists.max() > 0 else 1.0
        gdf_proj[f"decay_{cat}"] = 1.0 - (dists / max_d)
        
    return gdf_proj

st.set_page_config(page_title="08 总体城市设计", layout="wide", initial_sidebar_state="collapsed")
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

SUB_OPTIONS = ["🗺️ 空间结构推演", "🎛️ 用地结构优化沙盘", "🖼️ 图纸提示词生成"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

# ═══════════════════════════════════════════
# 空间数据面板 —— 始终显示
# ═══════════════════════════════════════════
with st.expander("📊 空间数据概览（驱动本阶段所有分析）", expanded=False):
    t1, t2 = st.tabs(["📊 数据清单", "🧠 AI 深度空间洞察"])
    with t1:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("#### 🏘️ 土地利用")
            st.text(get_landuse_summary())
        with c2:
            st.markdown("#### 🏗️ 建筑形态")
            st.text(get_building_summary())
        with c3:
            st.markdown("#### 🏗️ 重点更新单元")
            st.text(get_key_plots_summary())
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

    with st.expander("📋 前序策略矩阵（来自 Stage 07）", expanded=False):
        if strategy:
            st.markdown(strategy)
        else:
            st.info("暂无策略矩阵数据，请先完成 Stage 07 三方协同推演。")

    # 高精度底图对照
    master_img = Path("output/high_precision/总体语义底稿图_Masterplan_Semantic.png")
    if master_img.exists():
        with st.expander("🗺️ 高精度语义底稿图（矢量渲染 300DPI）", expanded=False):
            st.image(str(master_img), caption="总体语义底稿图 — 研究范围及周边1km", use_container_width=True)

    if st.button("🗺️ 生成空间结构推演报告", type="primary", key="s8_structure", **stretch_width(st.button)):
        spatial_ctx = get_full_spatial_context()
        prompt = f"""你是一位资深城市设计总师，精通空间结构分析与功能分区策划。

基于以下前期分析数据，为**整个研究范围（伪满皇宫周边约150公顷）**推演总体空间结构。

【前期设计目标（Stage 06）】：{design_concept[:2000] if design_concept else '数字孪生·古今共振——AI赋能下的伪满皇宫周边街区更新'}
【策略矩阵（Stage 07）】：{strategy[:2000] if strategy else '政策引导→产业导入→经济盘活→空间更新的良性循环'}
【全域空间数据】：{spatial_ctx[:4000]}

请生成【总体空间结构推演报告】，按以下框架展开（不限字数，务必详实）：

一、总体空间结构概念
  - 提炼一句话概括空间结构（如"一核两轴多片多节点"）
  - 用 300 字以上阐释其内涵与逻辑

二、核心区域定位（逐片区展开）
  对每个片区/功能区，详细说明：
  - 范围描述（结合具体地块名称和面积数据）
  - 功能定位（主导功能 + 辅助功能）
  - 开发强度建议（容积率、建筑密度、限高参考）
  - 与周边片区的空间关系和交通联系

三、轴线与廊道体系
  - 主轴（功能、空间特征、沿线节点）
  - 次轴与联络廊道
  - 绿色廊道与视线通廊（结合天际线保护要求）

四、节点体系
  - 门户节点、文化节点、商业节点、社区节点等
  - 每个节点的空间定位和功能配置

五、开发强度分区图则
  以表格形式列出各分区的容积率、建筑密度、绿地率、限高建议。
  | 分区名称 | 主导功能 | 容积率 | 建筑密度 | 绿地率 | 限高 |

六、与前期策略的对应关系
  说明空间结构如何回应 Stage 06/07 的目标和策略。

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
        with st.expander("📋 已生成的空间结构推演报告", expanded=False):
            st.markdown(saved_structure)


# ═══════════════════════════════════════════
# 模块二：用地结构优化沙盘
# ═══════════════════════════════════════════

elif selected_sub == "🎛️ 用地结构优化沙盘":
    render_section_intro(
        "用地结构优化沙盘",
        "交互式模拟不同用地功能占比的调整方案，"
        "LLM 实时评估结构变动对经济活力、环境承载力和社区品质的冲击。",
        eyebrow="Landuse Sandbox",
    )

    render_summary_cards([
        {"value": "交互式推演", "title": "沙盘模式", "desc": "调整滑块，实时评估"},
        {"value": "数据驱动", "title": "评估依据", "desc": "基于现状空间数据"},
    ])

    st.markdown("#### 📐 当前用地结构（基线）")
    st.text(get_landuse_summary())

    st.markdown("#### 🎛️ 目标用地结构调整")
    st.caption("拖动滑块模拟不同的用地功能占比方案，系统将评估其影响。")

    col_sandbox_left, col_sandbox_right = st.columns([1.1, 0.9])

    with col_sandbox_left:
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            res_pct = st.slider("🏠 居住用地占比 (%)", 20, 70, 48, key="sb_res")
            com_pct = st.slider("🏪 商业服务业用地占比 (%)", 5, 40, 16, key="sb_com")
            off_pct = st.slider("🏢 商务办公用地占比 (%)", 3, 25, 8, key="sb_off")
        with col_s2:
            green_pct = st.slider("🌳 公园绿地占比 (%)", 5, 30, 10, key="sb_green")
            public_pct = st.slider("🏛️ 公共设施用地占比 (%)", 3, 20, 6, key="sb_pub")
            total = res_pct + com_pct + off_pct + green_pct + public_pct
            remain = max(0, 100 - total)
            st.metric("📊 剩余（道路/市政等）", f"{remain}%")
            if total > 100:
                st.error(f"⚠️ 功能用地占比之和 ({total}%) 超过 100%，请调整。")

        # 用地结构实时可视化对比图表
        try:
            import plotly.graph_objects as go
            categories = ["居住用地 🏠", "商业用地 🏪", "商务办公 🏢", "公园绿地 🌳", "公共设施 🏛️", "道路/市政 📊"]
            baseline_pcts = [53.0, 15.5, 8.5, 5.5, 6.0, 11.5]
            scenario_pcts = [res_pct, com_pct, off_pct, green_pct, public_pct, remain]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=categories,
                x=baseline_pcts,
                name="现状基线 (Baseline)",
                orientation='h',
                marker=dict(color='rgba(148, 163, 184, 0.4)', line=dict(color='rgb(148, 163, 184)', width=1))
            ))
            fig.add_trace(go.Bar(
                y=categories,
                x=scenario_pcts,
                name="沙盘方案 (Scenario)",
                orientation='h',
                marker=dict(color='rgba(56, 189, 248, 0.8)', line=dict(color='rgb(56, 189, 248)', width=1))
            ))

            fig.update_layout(
                title=dict(text="📊 用地占比实时对比：现状基线 vs 沙盘方案", font=dict(color="#1e293b", size=14)),
                barmode='group',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(
                    title=dict(text="占比 (%)", font=dict(color="#475569")),
                    tickfont=dict(color="#475569"),
                    gridcolor='rgba(148, 163, 184, 0.1)',
                    range=[0, 100]
                ),
                yaxis=dict(
                    tickfont=dict(color="#1e293b"),
                    autorange="reversed"
                ),
                legend=dict(
                    font=dict(color="#475569"),
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                height=320,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"图表加载失败：{e}")

    with col_sandbox_right:
        # 用地结构实时空间落位图
        try:
            gdf_proj = load_raw_landuse_gdf()
            if gdf_proj is not None and not gdf_proj.empty:
                # 1. 计算研究范围内的目标面积
                gdf_in = gdf_proj[gdf_proj["in_study_area"]]
                total_area_in = gdf_in["area_sqm"].sum()
                target_pcts = {
                    "居住用地": res_pct,
                    "商业服务业": com_pct,
                    "商业办公": off_pct,
                    "公园与绿地": green_pct,
                    "公共设施": public_pct
                }
                target_areas = {k: total_area_in * (v / 100.0) for k, v in target_pcts.items()}
                
                # 2. 计算各宗地关于各功能类别的得分 (考虑现状与空间中心邻近度)
                scores = {}
                for cat in target_pcts.keys():
                    decay = gdf_proj[f"decay_{cat}"]
                    if cat == "公共设施":
                        is_orig = gdf_proj["Type"].isin(['医疗卫生', '教育科研', '体育文化', '行政办公'])
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
                import matplotlib.pyplot as plt
                from matplotlib.patches import Patch
                import matplotlib.font_manager as fm
                
                # 设置全局中文字体，防止 matplotlib 显示豆腐块
                plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun', 'sans-serif']
                plt.rcParams['axes.unicode_minus'] = False
                
                fig, ax = plt.subplots(figsize=(6, 5.5), facecolor='none')
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
                    "工业用地": "#64748B"
                }
                
                # 绘制研究范围外的地块 (半透明淡化处理)
                gdf_out = gdf_proj[~gdf_proj["in_study_area"]]
                if not gdf_out.empty:
                    colors_out = gdf_out["Type"].map(color_map).fillna("#CBD5E1")
                    gdf_out.plot(ax=ax, color=colors_out, edgecolor="#CBD5E1", linewidth=0.1, alpha=0.35)
                
                # 绘制研究范围内的地块 (全不透明高亮显示)
                if not gdf_in.empty:
                    allocated_types_in = allocated_types[gdf_proj["in_study_area"]]
                    colors_in = allocated_types_in.map(color_map).fillna("#CBD5E1")
                    gdf_in.plot(ax=ax, color=colors_in, edgecolor="#1E293B", linewidth=0.25, alpha=1.0)
                
                ax.set_axis_off()
                
                # 添加图例，并设置支持中文的字体属性与深色文字
                font_prop = fm.FontProperties(family=['Microsoft YaHei', 'SimHei', 'sans-serif'], size=8)
                legend_elements = [
                    Patch(facecolor='#FDE047', edgecolor='#475569', label='居住用地 (R)'),
                    Patch(facecolor='#EF4444', edgecolor='#475569', label='商业服务 (B)'),
                    Patch(facecolor='#C084FC', edgecolor='#475569', label='商业办公 (B)'),
                    Patch(facecolor='#22C55E', edgecolor='#475569', label='公园绿地 (G)'),
                    Patch(facecolor='#F87171', edgecolor='#475569', label='公共设施 (A)'),
                    Patch(facecolor='#94A3B8', edgecolor='#475569', label='道路/市政 (S)'),
                ]
                ax.legend(handles=legend_elements, loc='lower left', prop=font_prop, facecolor='none', edgecolor='none', labelcolor='#1e293b')
                
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.warning("⚠️ 无法加载用地数据进行空间分配模拟。")
        except Exception as e:
            st.error(f"空间落位图渲染失败：{e}")


    if total <= 100 and st.button("🔍 评估此方案的影响", type="primary", key="s8_sandbox", **stretch_width(st.button)):
        spatial_ctx = get_full_spatial_context()
        scenario = (
            f"居住 {res_pct}%, 商业 {com_pct}%, 办公 {off_pct}%, "
            f"绿地 {green_pct}%, 公共设施 {public_pct}%, 其他(道路/市政) {remain}%"
        )
        prompt = f"""你是一位城市规划经济学家，精通城市更新中的用地结构优化。

研究范围（伪满皇宫周边约150公顷）的现状用地结构为：
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
                "remain": remain
            })
            st.success("✅ 沙盘评估完成，已存入数据总线。")


# ═══════════════════════════════════════════
# 模块三：图纸提示词生成
# ═══════════════════════════════════════════

elif selected_sub == "🖼️ 图纸提示词生成":
    render_drawing_prompt_ui("08", key_prefix="p8", stage_title="总体城市设计")


st.markdown("---")
render_stage_summary(
    stage_code="08",
    title="总体空间结构与用地优化",
    findings=[
        {"point": "空间结构推演基于全域量化数据，覆盖核心区、轴线、廊道、节点四大体系", "evidence": "Stage 07 策略矩阵 + 全域空间数据"},
        {"point": "用地结构优化沙盘支持交互式占比调整与 LLM 实时冲击评估", "evidence": "landuse_clipped.geojson 基线 + 情景模拟"},
        {"point": "AIGC 辅助概念总平面生形，约束条件源自空间结构推演结果", "evidence": "Stable Diffusion + ControlNet"},
    ],
    methodology="基于 DeepSeek V4 Pro 的空间结构深度推演 + 用地结构交互式沙盘模拟",
    implication="为专项系统设计（Stage 09）和重点地段深化（Stage 10）提供了总体空间骨架和开发强度分区",
)
