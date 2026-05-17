"""阶段 10：重点地段深化 —— 微观人群画像 + 控规指标反推 + 地块深化设计。

基于 Stage 08/09 的总体结构和专项策略，对每个重点地块进行：
1. 空间诊断指标展示与雷达图可视化
2. 控制性详细指标反推（容积率/建筑密度/绿地率/限高）
3. 目标人群行为画像（基于地块名称/功能定位、NLP 情感得分、POI 构成）
4. 空间深化设计方案
5. Before/After 街景推演对比

所有产出自动存入数据总线，供 Stage 11/12 读取。
"""

import streamlit as st
import plotly.graph_objects as go
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.chart_theme import apply_plotly_polar_theme
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.ui.module_summary import render_stage_summary
from src.engines.llm_engine import call_llm_engine_stream
from src.engines.site_diagnostic_engine import get_plot_diagnostics
from src.engines.spatial_data_injector import (
    get_full_spatial_context,
    get_plot_context,
    get_poi_summary,
)
from src.workflow.stage_data_bus import (
    save_stage_output, load_stage_output, render_evidence_chain_bar,
)
from src.workflow.stage_keys import SK
from src.ui.drawing_prompt_ui import render_drawing_prompt_ui
from src.ui.streamlit_compat import stretch_width

st.set_page_config(page_title="10 重点地段深化", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()
render_engine_status_alert()

graphic_svg = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 200" width="100%" height="100%" style="max-width: 580px; filter: drop-shadow(0 15px 25px rgba(0,0,0,0.3));">
  <defs>
    <linearGradient id="g_base" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="rgba(30, 41, 59, 0.6)"/>
      <stop offset="100%" stop-color="rgba(15, 23, 42, 0.8)"/>
    </linearGradient>
    <linearGradient id="g_ai" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="rgba(56, 189, 248, 0.25)"/>
      <stop offset="100%" stop-color="rgba(15, 23, 42, 0.95)"/>
    </linearGradient>
    <linearGradient id="g_out" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="rgba(16, 185, 129, 0.25)"/>
      <stop offset="100%" stop-color="rgba(15, 23, 42, 0.95)"/>
    </linearGradient>
    
    <filter id="f_cyan" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="5" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
    <filter id="f_indigo" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="5" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
    <filter id="f_emerald" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="5" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>

  <circle cx="340" cy="100" r="110" fill="none" stroke="rgba(99, 102, 241, 0.15)" stroke-width="1.5" stroke-dasharray="6,4"/>
  <circle cx="340" cy="100" r="75" fill="none" stroke="rgba(56, 189, 248, 0.2)" stroke-width="1" stroke-dasharray="4,2"/>

  <path d="M 340 100 L 170 45" fill="none" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="4,3"/>
  <polygon points="208,53 200,48 205,58" fill="#38bdf8"/>

  <path d="M 340 100 L 170 155" fill="none" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="4,3"/>
  <polygon points="208,147 205,142 200,152" fill="#38bdf8"/>

  <path d="M 340 100 L 510 45" fill="none" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="4,3"/>
  <polygon points="472,53 475,58 480,48" fill="#38bdf8"/>

  <path d="M 340 100 L 510 155" fill="none" stroke="#10b981" stroke-width="2" stroke-dasharray="5,4" filter="url(#f_emerald)"/>
  <polygon points="472,147 480,152 475,142" fill="#10b981"/>

  <circle cx="340" cy="100" r="45" fill="url(#g_ai)" stroke="#38bdf8" stroke-width="2.5" filter="url(#f_cyan)"/>
  <text x="340" y="96" fill="#38bdf8" font-size="14" font-family="sans-serif" text-anchor="middle" font-weight="bold">重点地块</text>
  <text x="340" y="113" fill="#bae6fd" font-size="11" font-family="sans-serif" text-anchor="middle">微观深化中枢</text>

  <rect x="100" y="22" width="140" height="46" rx="6" fill="url(#g_base)" stroke="#334155" stroke-width="1"/>
  <text x="170" y="40" fill="#e2e8f0" font-size="13" font-family="sans-serif" text-anchor="middle" font-weight="bold">空间诊断雷达图</text>
  <text x="170" y="55" fill="#94a3b8" font-size="10" font-family="sans-serif" text-anchor="middle">六维诊断 &amp; 瓶颈分析</text>

  <rect x="100" y="132" width="140" height="46" rx="6" fill="url(#g_base)" stroke="#334155" stroke-width="1"/>
  <text x="170" y="150" fill="#e2e8f0" font-size="13" font-family="sans-serif" text-anchor="middle" font-weight="bold">控规指标反推</text>
  <text x="170" y="165" fill="#94a3b8" font-size="10" font-family="sans-serif" text-anchor="middle">开发容积率/密度反推</text>

  <rect x="440" y="22" width="140" height="46" rx="6" fill="url(#g_base)" stroke="#334155" stroke-width="1"/>
  <text x="510" y="40" fill="#e2e8f0" font-size="13" font-family="sans-serif" text-anchor="middle" font-weight="bold">目标人群行为画像</text>
  <text x="510" y="55" fill="#94a3b8" font-size="10" font-family="sans-serif" text-anchor="middle">群体细分与NLP诉求</text>

  <rect x="440" y="132" width="140" height="46" rx="6" fill="url(#g_out)" stroke="#10b981" stroke-width="2" filter="url(#f_emerald)"/>
  <text x="510" y="150" fill="#10b981" font-size="13" font-family="sans-serif" text-anchor="middle" font-weight="bold">地块改造深化方案</text>
  <text x="510" y="165" fill="#e2e8f0" font-size="10" font-family="sans-serif" text-anchor="middle">空间方案与街景比对</text>
</svg>
"""

render_page_banner(
    title="重点地段深化",
    description="对每个重点地块进行微观级深化设计：空间诊断雷达图、控制性详细指标反推、"
                "目标人群行为画像和完整的地块改造设计方案。",
    eyebrow="Stage 10",
    tags=["地块诊断雷达", "控规指标反推", "人群画像", "深化设计", "Before/After"],
    graphic_html=graphic_svg
)
render_evidence_chain_bar("10", ["08", "09", "10"])

with st.sidebar:
    model_tag = st.selectbox(
        "DeepSeek 模型",
        ["deepseek-v4-flash", "deepseek-v4-pro"],
        index=1,
        key="p10_model",
        help="地块深化设计属于深度策划任务，建议使用 Pro 模型",
    )

SUB_OPTIONS = [
    "📍 重点地块诊断雷达",
    "📊 控制性详细指标推演",
    "👥 目标人群与行为画像",
    "🏗️ 空间深化设计方案",
    "🔄 Before/After 推演",
    "🖼️ 图纸提示词生成",
]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

# 预加载地块诊断数据
diags = get_plot_diagnostics()
if not diags:
    st.warning("⚠️ 暂无地块诊断数据，请先完成 Stage 05 量化分析。")
    st.stop()

diags_sorted = sorted(diags, key=lambda x: x["mpi_score"], reverse=True)

# 地块选择器 —— 在所有模块中共用
selected_plot = st.selectbox(
    "选择重点地块",
    [d["name"] for d in diags_sorted],
    format_func=lambda n: f"{n} (MPI: {next(d['mpi_score'] for d in diags_sorted if d['name'] == n)})",
    key="p10_plot_selector",
)
d = next(dd for dd in diags_sorted if dd["name"] == selected_plot)

# 显示地块基本指标
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("MPI 得分", d["mpi_score"])
c2.metric("面积", f"{d['area_ha']} ha")
c3.metric("GVI", f"{d['gvi_mean']}%")
c4.metric("SVF", f"{d['svf_mean']}")
c5.metric("POI", d["poi_count"])
c6.metric("情感指数", d["sentiment_mean"])

st.markdown("---")


# ═══════════════════════════════════════════
# 模块一：重点地块诊断雷达图
# ═══════════════════════════════════════════

if selected_sub == "📍 重点地块诊断雷达":
    render_section_intro(
        "重点地块多维诊断雷达图",
        "可视化地块在更新潜力(MPI)、绿视率(GVI)、天空可视(SVF)、围合度、POI密度等维度的表现。",
        eyebrow="Plot Diagnostic Radar",
    )

    # 绘制雷达图
    categories = ["MPI 更新潜力", "绿视率(GVI)", "天空可视(SVF)", "围合度", "POI密度"]
    # 归一化到 0-100
    mpi_norm = min(100, d["mpi_score"])
    gvi_norm = min(100, d["gvi_mean"] * 2)  # GVI 一般 0-50，放大到 0-100
    svf_norm = min(100, d["svf_mean"] * 100) if d["svf_mean"] < 1 else d["svf_mean"]
    enc_norm = min(100, d["enclosure_mean"] * 100) if d["enclosure_mean"] < 1 else d["enclosure_mean"]
    poi_norm = min(100, d["poi_count"] * 5)  # 假设 20 个 POI 为满分

    values = [mpi_norm, gvi_norm, svf_norm, enc_norm, poi_norm]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(99, 102, 241, 0.15)",
        line=dict(color="#818cf8", width=2),
        name=selected_plot,
    ))
    apply_plotly_polar_theme(fig, title=f"{selected_plot} — 多维诊断", height=420, radial_range=[0, 100])
    st.plotly_chart(fig, **stretch_width(st.plotly_chart))

    # 短板诊断
    st.markdown("#### 🔍 短板自动诊断")
    weaknesses = []
    if d["gvi_mean"] < 15:
        weaknesses.append(f"🌿 绿视率仅 {d['gvi_mean']}%，远低于 15% 宜居基准，需大规模补绿")
    if d["poi_count"] < 5:
        weaknesses.append(f"📍 POI 仅 {d['poi_count']} 个，商业活力严重不足")
    if d["mpi_score"] > 60:
        weaknesses.append(f"📈 MPI 得分 {d['mpi_score']}，更新潜力大但现状条件差")
    if d["svf_mean"] and d["svf_mean"] < 0.3:
        weaknesses.append(f"☁️ SVF 仅 {d['svf_mean']}，街道压迫感强，需打开天空视野")

    if weaknesses:
        for w in weaknesses:
            st.warning(w)
    else:
        st.success("✅ 该地块各维度指标均衡，建议以品质提升为主。")


# ═══════════════════════════════════════════
# 模块二：控制性详细指标推演
# ═══════════════════════════════════════════

elif selected_sub == "📊 控制性详细指标推演":
    render_section_intro(
        "控制性详细指标推演",
        "LLM 根据地块面积、MPI 得分和上游空间结构，反推容积率(FAR)、建筑密度、绿地率、限高等核心控规指标。",
        eyebrow="Regulatory Metrics",
    )

    spatial_structure = load_stage_output("08", SK.SPATIAL_STRUCTURE, "")
    building_form = load_stage_output("09", SK.BUILDING_FORM, "")
    plot_ctx = get_plot_context(selected_plot)

    if st.button(f"📊 推演 {selected_plot} 的控规指标", type="primary", key="s10_metrics", **stretch_width(st.button)):
        prompt = f"""你是一位注册城乡规划师，精通控制性详细规划指标的确定。

请为重点地块【{selected_plot}】反推控制性详细指标。

【地块空间诊断数据】：
{plot_ctx}

【上游空间结构（Stage 08）】：{spatial_structure[:1500] if spatial_structure else '暂无'}
【上游建筑形态控制（Stage 09）】：{building_form[:1500] if building_form else '核心保护区≤9m，一般控制区≤18m'}

【高度红线约束】：核心保护区限高≤9m，一般控制区限高≤18m，容积率≤1.4。

请生成【控制性详细指标报告】：

一、核心控规指标建议
  以表格形式列出：
  | 指标 | 建议值 | 推导依据 |
  包含：容积率(FAR)、建筑密度(%)、绿地率(%)、建筑限高(m)、建筑后退红线(m)

二、开发强度测算
  - 可建设用地面积估算
  - 地上建筑面积估算
  - 人口承载力估算

三、配套设施指标
  - 停车位配建标准
  - 公共服务设施配建要求
  - 市政设施用地预留

四、与全域控制的协调
  说明本地块的指标如何与周边地块、全域目标协调一致。

所有指标必须有定量依据，结合地块面积 ({d['area_ha']} ha)、
MPI 得分 ({d['mpi_score']})、现状 GVI ({d['gvi_mean']}%) 等数据进行推导。"""

        stream = call_llm_engine_stream(
            prompt=prompt,
            system_prompt="注册城乡规划师，精通控制性详细规划指标确定。每个指标须有量化推导依据。",
            model=model_tag,
        )
        result = st.write_stream(stream)
        if isinstance(result, str) and len(result) > 200:
            save_stage_output("10", f"{SK.PLOT_METRICS}_{selected_plot}", result)
            st.success(f"✅ {selected_plot} 控规指标推演完成（{len(result)} 字）")

    saved = load_stage_output("10", f"{SK.PLOT_METRICS}_{selected_plot}", "")
    if saved:
        with st.expander("📋 已生成的控规指标", expanded=False):
            st.markdown(saved)


# ═══════════════════════════════════════════
# 模块三：目标人群与行为画像
# ═══════════════════════════════════════════

elif selected_sub == "👥 目标人群与行为画像":
    render_section_intro(
        "目标人群与行为画像",
        "基于地块名称（反映功能定位）、NLP 情感得分和周边 POI 构成，"
        "生成 3 个典型人群画像及其 24 小时活动轨迹。",
        eyebrow="User Personas",
    )

    plot_ctx = get_plot_context(selected_plot)
    poi_summary = get_poi_summary()

    if st.button(f"👥 生成 {selected_plot} 的人群画像", type="primary", key="s10_persona", **stretch_width(st.button)):
        prompt = f"""你是一位城市社会学家和行为心理学家，精通城市更新中的人群需求分析。

请为重点地块【{selected_plot}】生成 3 个典型目标人群画像。

⚠️ 重要：地块名称【{selected_plot}】本身反映了该地块的主要功能定位和历史角色，
请务必以此作为人群画像的核心参照。例如，若地块名称含"工业"，
则应包含与产业转型相关的人群（如"文创工作者"）；若含"社区/住宅"，
则应包含居住相关人群（如"退休居民"）。

【地块空间诊断数据】：
{plot_ctx}

【研究范围 POI 分布】：
{poi_summary}

【NLP 情感分析结论】：
  - 情感指数: {d['sentiment_mean']}（正值表示正面情绪主导）
  - POI 密度: {d['poi_count']} 个（反映功能活力）
  - 绿视率: {d['gvi_mean']}%（反映环境品质感知）

请生成【目标人群画像报告】，包含 3 个典型人群：

对每个人群画像，详细展开（每个画像至少 400 字）：

一、基本画像
  - 昵称（如"文创青年小李"）
  - 年龄/职业/居住状态
  - 与本地块的关系（居民/通勤者/访客/创业者）
  - 为什么会出现在这个地块（与地块名称/功能定位的关联）

二、24 小时活动轨迹
  按时间线描述一天中在本地块及周边的行为（早/中/晚/夜），
  每个活动节点须标注：
  - 活动内容
  - 所需空间类型（菜市场/公园/咖啡馆/步行道等）
  - 当前空间是否能满足需求

三、痛点与期望
  - 当前空间中的 3 个核心痛点
  - 对未来改造的 3 个期望
  - 每个痛点/期望必须对应具体的空间数据

四、对设计的启示
  - 此人群画像如何指导本地块的空间设计
  - 应配置哪些功能和设施来满足其需求

最后，生成一段【综合人群需求矩阵】总结，
将 3 个画像的需求交叉对比，找到共性需求和差异化需求。"""

        stream = call_llm_engine_stream(
            prompt=prompt,
            system_prompt=(
                "城市社会学家和行为心理学家。画像必须基于地块名称所反映的功能定位、"
                "量化数据和真实的城市生活逻辑，不可天马行空。"
            ),
            model=model_tag,
        )
        result = st.write_stream(stream)
        if isinstance(result, str) and len(result) > 200:
            save_stage_output("10", f"{SK.PLOT_PERSONAS}_{selected_plot}", result)
            st.success(f"✅ {selected_plot} 人群画像生成完成（{len(result)} 字）")

    saved = load_stage_output("10", f"{SK.PLOT_PERSONAS}_{selected_plot}", "")
    if saved:
        with st.expander("📋 已生成的人群画像", expanded=False):
            st.markdown(saved)


# ═══════════════════════════════════════════
# 模块四：空间深化设计方案
# ═══════════════════════════════════════════

elif selected_sub == "🏗️ 空间深化设计方案":
    render_section_intro(
        "空间深化设计方案",
        "综合控规指标、人群需求和上游所有专项策略，生成完整的地块改造设计方案。",
        eyebrow="Plot Design Scheme",
    )

    # 加载所有前置数据
    spatial_structure = load_stage_output("08", SK.SPATIAL_STRUCTURE, "")
    traffic = load_stage_output("09", SK.TRAFFIC_SYSTEM, "")
    public_space = load_stage_output("09", SK.PUBLIC_SPACE, "")
    building_form = load_stage_output("09", SK.BUILDING_FORM, "")
    landscape = load_stage_output("09", SK.LANDSCAPE_STYLE, "")
    plot_metrics = load_stage_output("10", f"{SK.PLOT_METRICS}_{selected_plot}", "")
    plot_personas = load_stage_output("10", f"{SK.PLOT_PERSONAS}_{selected_plot}", "")
    plot_ctx = get_plot_context(selected_plot)

    with st.expander("📊 前序数据汇总", expanded=False):
        data_status = {
            "Stage 08 空间结构": "✅" if spatial_structure else "❌",
            "Stage 09 交通系统": "✅" if traffic else "❌",
            "Stage 09 公共空间": "✅" if public_space else "❌",
            "Stage 09 建筑形态": "✅" if building_form else "❌",
            "Stage 09 风貌景观": "✅" if landscape else "❌",
            f"Stage 10 {selected_plot} 控规指标": "✅" if plot_metrics else "❌",
            f"Stage 10 {selected_plot} 人群画像": "✅" if plot_personas else "❌",
        }
        for k, v in data_status.items():
            st.markdown(f"{v} {k}")
        if "❌" in data_status.values():
            st.warning("部分前序数据尚未生成，设计方案将基于已有数据进行策划。")

    if st.button(f"🏗️ 生成 {selected_plot} 深化设计方案", type="primary", key="s10_design", **stretch_width(st.button)):
        # 组装上下文（截取以控制 token 用量）
        upstream = f"""
【地块诊断】：{plot_ctx}
【控规指标】：{plot_metrics[:1000] if plot_metrics else '容积率≤1.4，核心区限高≤9m'}
【人群画像】：{plot_personas[:1500] if plot_personas else '暂无'}
【空间结构】：{spatial_structure[:800] if spatial_structure else '暂无'}
【交通策略】：{traffic[:500] if traffic else '暂无'}
【公共空间】：{public_space[:500] if public_space else '暂无'}
【建筑形态】：{building_form[:500] if building_form else '暂无'}
【风貌景观】：{landscape[:500] if landscape else '暂无'}"""

        prompt = f"""你是一位城市设计深化方案主创设计师，精通从策划到落地的全流程。

请为重点地块【{selected_plot}】（面积 {d['area_ha']} ha, MPI {d['mpi_score']}）
生成一份完整的深化设计方案。

{upstream}

请生成【地块深化设计方案】（不限字数，追求详实与专业，力求可直接指导施工图阶段）：

一、地块定位与角色
  - 在全域空间结构中的角色定位
  - 核心设计理念（一句话 + 300 字阐释）
  - 与地块名称所蕴含的功能定位的呼应

二、空间布局方案
  - 功能分区（生活区、商业区、公共活动区、绿化区等）
  - 主要出入口与内部流线
  - 建筑布局原则（围合式/散点式/沿街式）

三、功能业态策划
  - 主导业态与支撑业态配比
  - 首层商业业态引导（基于人群画像需求）
  - 文化功能植入策略（结合伪满皇宫文化IP）

四、交通组织
  - 车行/步行/自行车的交通分流
  - 停车解决方案
  - 与周边路网的接驳

五、景观设计导引
  - 中心景观节点设计意向
  - 沿街界面景观处理
  - 植物配置方案

六、建筑设计导引
  - 建筑体量与高度控制
  - 立面材质与色彩（结合风貌要求）
  - 屋顶形式与第五立面

七、市政与智慧系统
  - 雨水管理与海绵设施
  - 智慧路灯与物联网基础设施
  - 地下空间利用

八、实施建议
  - 分期建设时序
  - 关键启动项目
  - 预估投资概算

每一条设计决策都必须追溯到其数据依据（MPI/GVI/POI/面积/人群需求等）。"""

        stream = call_llm_engine_stream(
            prompt=prompt,
            system_prompt="城市设计深化方案主创设计师。方案须详实到可指导施工图，每个设计决策须有数据支撑。",
            model=model_tag,
        )
        result = st.write_stream(stream)
        if isinstance(result, str) and len(result) > 300:
            save_stage_output("10", f"{SK.PLOT_DESIGN}_{selected_plot}", result)
            st.success(f"✅ {selected_plot} 深化设计方案生成完成（{len(result)} 字）")

    saved = load_stage_output("10", f"{SK.PLOT_DESIGN}_{selected_plot}", "")
    if saved:
        with st.expander("📋 已生成的深化设计方案", expanded=False):
            st.markdown(saved)


# ═══════════════════════════════════════════
# 模块五：Before/After 推演
# ═══════════════════════════════════════════

elif selected_sub == "🔄 Before/After 推演":
    render_section_intro(
        "Before/After 街景推演对比",
        "展示 AIGC 渲染前后的街景效果对比。",
        eyebrow="Before / After",
    )

    st.info("💡 完整的 AIGC 推演面板（含底图上传、ControlNet 参数、Before/After 生成）"
            "请前往 **AIGC设计推演** 页面操作。\n\n"
            "本模块自动展示 session 中已生成的渲染结果。")

    # 检查 session 中是否有 AIGC 结果
    aigc_keys = [k for k in st.session_state.keys() if "sd_result" in k]
    if aigc_keys:
        st.markdown(f"#### 🖼️ 已生成 {len(aigc_keys)} 张渲染结果")
        cols = st.columns(min(3, len(aigc_keys)))
        for i, key in enumerate(aigc_keys[:6]):
            with cols[i % 3]:
                img = st.session_state[key]
                st.image(img, caption=key.replace("_sd_result", ""), use_container_width=True)
    else:
        st.warning("暂无 AIGC 渲染结果。请先在 **AIGC设计推演** 页面生成街景效果图。")


# ═══════════════════════════════════════════
# 模块六：图纸提示词生成
# ═══════════════════════════════════════════

elif selected_sub == "🖼️ 图纸提示词生成":
    render_drawing_prompt_ui("10", key_prefix="p10", stage_title="重点地段深化")


st.markdown("---")
avg_mpi = sum(d_item["mpi_score"] for d_item in diags) / len(diags) if diags else 0
render_stage_summary(
    stage_code="10",
    title="重点地段微观级深化设计",
    findings=[
        {"point": f"共 {len(diags)} 个候选地块，平均 MPI 得分 {avg_mpi:.1f}，每个地块配有多维诊断雷达图", "evidence": "地块诊断引擎数据"},
        {"point": "控制性详细指标由 LLM 根据面积、MPI、GVI 等反推容积率/密度/绿地率/限高", "evidence": "Stage 08 开发强度分区 + 地块诊断"},
        {"point": "目标人群画像基于地块名称（功能定位）+ NLP 情感 + POI 构成生成 24 小时行为轨迹", "evidence": "NLP 情感数据 + POI 分类统计"},
        {"point": "深化设计方案综合控规/人群/交通/景观/建筑五大维度，可直接指导施工图阶段", "evidence": "Stage 08-10 全链路数据融合"},
    ],
    methodology="基于 DeepSeek V4 Pro 的微观级 LLM 深度策划 + 多维空间数据交叉验证",
    implication="为实施路径（Stage 11）和城市设计导则（Stage 12）提供了详实的落地设计依据",
)
