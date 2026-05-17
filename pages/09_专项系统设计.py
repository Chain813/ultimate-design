"""阶段 09：专项系统设计 —— 四大专项系统 LLM 深度策划。

基于 Stage 08 的空间结构推演，对四大专项系统进行深度设计：
1. 交通网络与 TOD
2. 公共空间与 15 分钟社区生活圈
3. 建筑形态与天际线控制
4. 风貌景观与历史保护

每个专项系统均由 LLM 基于量化空间数据深度策划，产出自动存入数据总线。
"""

import streamlit as st
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.ui.module_summary import render_stage_summary
from src.engines.llm_engine import call_llm_engine_stream
from src.engines.spatial_engine import get_hud_statistics, get_skyline_features
from src.engines.spatial_data_injector import (
    get_full_spatial_context,
    get_landuse_summary,
    get_poi_summary,
    get_gvi_summary,
    get_building_summary,
    get_traffic_summary,
    get_key_plots_summary,
)
from src.workflow.stage_data_bus import (
    save_stage_output, load_stage_output, render_evidence_chain_bar,
)
from src.workflow.stage_keys import SK
from src.ui.drawing_prompt_ui import render_drawing_prompt_ui
from src.ui.streamlit_compat import stretch_width

st.set_page_config(page_title="09 专项系统设计", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()
render_engine_status_alert()

stats = get_hud_statistics()
sky = get_skyline_features()

graphic_svg = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 200" width="100%" height="100%" style="max-width: 600px; filter: drop-shadow(0 15px 25px rgba(0,0,0,0.3));">
  <defs>
    <linearGradient id="g_base" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="rgba(30, 41, 59, 0.6)"/>
      <stop offset="100%" stop-color="rgba(15, 23, 42, 0.8)"/>
    </linearGradient>
    <linearGradient id="g_ai" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="rgba(56, 189, 248, 0.15)"/>
      <stop offset="100%" stop-color="rgba(15, 23, 42, 0.9)"/>
    </linearGradient>
    <linearGradient id="g_out" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="rgba(16, 185, 129, 0.2)"/>
      <stop offset="100%" stop-color="rgba(15, 23, 42, 0.9)"/>
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

  <path d="M 160 100 C 180 100, 180 32, 200 32" fill="none" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="4,3"/>
  <path d="M 160 100 C 180 100, 180 77, 200 77" fill="none" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="4,3"/>
  <path d="M 160 100 C 180 100, 180 122, 200 122" fill="none" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="4,3"/>
  <path d="M 160 100 C 180 100, 180 167, 200 167" fill="none" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="4,3"/>

  <path d="M 360 32 C 380 32, 380 100, 410 100" fill="none" stroke="#10b981" stroke-width="1.5" stroke-dasharray="4,3"/>
  <path d="M 360 77 C 380 77, 380 100, 410 100" fill="none" stroke="#10b981" stroke-width="1.5" stroke-dasharray="4,3"/>
  <path d="M 360 122 C 380 122, 380 100, 410 100" fill="none" stroke="#10b981" stroke-width="1.5" stroke-dasharray="4,3"/>
  <path d="M 360 167 C 380 167, 380 100, 410 100" fill="none" stroke="#10b981" stroke-width="1.5" stroke-dasharray="4,3"/>
  <polygon points="405,96 410,100 405,104" fill="#10b981"/>

  <rect x="10" y="70" width="150" height="60" rx="8" fill="url(#g_base)" stroke="#6366f1" stroke-width="2" filter="url(#f_indigo)"/>
  <text x="85" y="97" fill="#6366f1" font-size="13" font-family="sans-serif" text-anchor="middle" font-weight="bold">总体空间结构</text>
  <text x="85" y="116" fill="#cbd5e1" font-size="10" font-family="sans-serif" text-anchor="middle">Stage 08 策划基础</text>

  <rect x="200" y="15" width="160" height="34" rx="6" fill="url(#g_ai)" stroke="#38bdf8" stroke-width="1.5" filter="url(#f_cyan)"/>
  <text x="280" y="36" fill="#e2e8f0" font-size="11" font-family="sans-serif" text-anchor="middle" font-weight="bold">交通与 TOD 系统</text>

  <rect x="200" y="60" width="160" height="34" rx="6" fill="url(#g_ai)" stroke="#38bdf8" stroke-width="1.5" filter="url(#f_cyan)"/>
  <text x="280" y="81" fill="#e2e8f0" font-size="11" font-family="sans-serif" text-anchor="middle" font-weight="bold">公共空间与 15min 生活圈</text>

  <rect x="200" y="105" width="160" height="34" rx="6" fill="url(#g_ai)" stroke="#38bdf8" stroke-width="1.5" filter="url(#f_cyan)"/>
  <text x="280" y="126" fill="#e2e8f0" font-size="11" font-family="sans-serif" text-anchor="middle" font-weight="bold">建筑形态与天际控制</text>

  <rect x="200" y="150" width="160" height="34" rx="6" fill="url(#g_ai)" stroke="#38bdf8" stroke-width="1.5" filter="url(#f_cyan)"/>
  <text x="280" y="171" fill="#e2e8f0" font-size="11" font-family="sans-serif" text-anchor="middle" font-weight="bold">风貌景观与历史保护</text>

  <rect x="410" y="45" width="160" height="110" rx="10" fill="url(#g_out)" stroke="#10b981" stroke-width="2" filter="url(#f_emerald)"/>
  <text x="490" y="73" fill="#10b981" font-size="14" font-family="sans-serif" text-anchor="middle" font-weight="bold">专项控制图层</text>
  <text x="490" y="100" fill="#e2e8f0" font-size="10" font-family="sans-serif" text-anchor="middle">✓ 多维度 GIS 成果整合</text>
  <text x="490" y="120" fill="#e2e8f0" font-size="10" font-family="sans-serif" text-anchor="middle">✓ 量化指标精确控制</text>
  <text x="490" y="140" fill="#e2e8f0" font-size="10" font-family="sans-serif" text-anchor="middle">✓ 一键导出蓝图图集</text>

  <circle cx="160" cy="100" r="4" fill="#6366f1"/>
  <circle cx="410" cy="100" r="4" fill="#10b981"/>
</svg>
"""

render_page_banner(
    title="专项系统设计",
    description="基于 Stage 08 总体空间结构，对交通网络、公共空间、建筑形态和风貌景观"
                "四大专项系统进行 LLM 深度策划，每个专项均注入量化空间数据。",
    eyebrow="Stage 09",
    tags=["交通与TOD", "15分钟生活圈", "天际线控制", "风貌保护", "四专项并行"],
    metrics=[
        {"value": str(stats.get("poi_count", "N/A")), "label": "POI", "meta": "活力测度"},
        {"value": f"{sky.get('avg_height', 0)} m", "label": "平均层高", "meta": "形态控制"},
        {"value": f"{sky.get('high_rise_ratio', 0)}%", "label": "高层占比", "meta": "天际线"},
    ],
    graphic_html=graphic_svg
)
render_evidence_chain_bar("09", ["08", "09", "10"])

with st.sidebar:
    model_tag = st.selectbox(
        "DeepSeek 模型",
        ["deepseek-v4-flash", "deepseek-v4-pro"],
        index=1,
        key="p9_model",
        help="专项系统需要深度分析，建议使用 Pro 模型",
    )

SUB_OPTIONS = ["🚗 交通网络与TOD", "🌳 公共空间与15分钟圈", "🏛️ 建筑形态与天际线", "🎨 风貌景观与文保", "🖼️ 图纸提示词生成"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

# 加载 Stage 08 空间结构
spatial_structure = load_stage_output("08", SK.SPATIAL_STRUCTURE, "")

# ═══════════════════════════════════════════
# 空间数据面板 —— 始终显示
# ═══════════════════════════════════════════
with st.expander("📊 空间数据概览（驱动本阶段所有分析）", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### 🏘️ 土地利用")
        st.text(get_landuse_summary())
    with c2:
        st.markdown("#### 📍 POI 分布")
        poi_text = get_poi_summary()
        st.text(poi_text)
        if "暂不可用" in poi_text or "为空" in poi_text:
            st.warning("⚠️ POI 数据可能不完整，设施缺口分析将以现有数据为上限进行估算。")
    with c3:
        st.markdown("#### 🌿 街景品质 (GVI)")
        st.text(get_gvi_summary())

    c4, c5 = st.columns(2)
    with c4:
        st.markdown("#### 🏗️ 建筑形态")
        st.text(get_building_summary())
    with c5:
        st.markdown("#### 🚗 交通流量")
        traffic_text = get_traffic_summary()
        st.text(traffic_text)
        if "暂不可用" in traffic_text:
            st.warning("⚠️ 交通数据有限，分析将基于路网拓扑结构进行推演。")


# ═══════════════════════════════════════════
# 模块一：交通网络与 TOD
# ═══════════════════════════════════════════

if selected_sub == "🚗 交通网络与TOD":
    render_section_intro(
        "交通网络优化与 TOD 策略",
        "道路等级优化、慢行系统网络化、轨道站点 TOD 辐射范围及最后一公里接驳评估。",
        eyebrow="Traffic & TOD",
    )

    render_summary_cards([
        {"value": f"{sky.get('building_count', 0)}", "title": "建筑密度参照", "desc": "栋"},
        {"value": str(stats.get("poi_count", "N/A")), "title": "POI 总量", "desc": "活力基线"},
    ])

    if st.button("🚗 生成交通系统设计方案", type="primary", key="s9_traffic", **stretch_width(st.button)):
        spatial_ctx = get_full_spatial_context()
        prompt = f"""你是一位资深交通规划师，精通城市更新中的交通网络优化与 TOD 开发模式。

基于以下空间数据，为研究范围（伪满皇宫周边约150公顷）制定交通系统设计方案。

【上游空间结构（Stage 08）】：{spatial_structure[:2000] if spatial_structure else '一核两轴多片多节点'}
【全域空间数据】：{spatial_ctx[:3500]}

请生成【交通系统设计方案】（不限字数，务必详实）：

一、道路等级优化方案
  - 现状道路等级分布分析（结合路网数据）
  - 各等级道路的断面优化建议（车行道、人行道、绿化带宽度）
  - 交通组织与微循环改善

二、慢行系统网络化
  - 步行网络规划（主要步行轴线、串联节点）
  - 自行车道网络（与公共交通接驳）
  - 慢行系统与开放空间的耦合

三、轨道站点 TOD 策略
  - 轨道站点（轻轨/地铁）的 800m/1200m 辐射范围分析
  - 最后一公里接驳体系（公交、共享单车、步行）
  - TOD 开发强度分区建议

四、公交系统优化
  - 公交线路优化与站点加密建议
  - 社区巴士与定制公交方案
  - 公交-轨道换乘便利性提升

五、停车策略
  - 停车设施布局与共享停车方案
  - 路内停车整治与地下空间利用

每一条建议都必须引用空间数据中的具体数字，并指明空间落位。"""

        stream = call_llm_engine_stream(
            prompt=prompt,
            system_prompt="资深交通规划师，精通城市更新中的交通网络优化。所有方案必须落到空间上。",
            model=model_tag,
        )
        result = st.write_stream(stream)
        if isinstance(result, str) and len(result) > 200:
            save_stage_output("09", SK.TRAFFIC_SYSTEM, result)
            st.success(f"✅ 交通系统设计方案生成完成（{len(result)} 字）")

    saved = load_stage_output("09", SK.TRAFFIC_SYSTEM, "")
    if saved:
        with st.expander("📋 已生成的交通系统设计方案", expanded=False):
            st.markdown(saved)


# ═══════════════════════════════════════════
# 模块二：公共空间与 15 分钟生活圈
# ═══════════════════════════════════════════

elif selected_sub == "🌳 公共空间与15分钟圈":
    render_section_intro(
        "公共空间系统与 15 分钟社区生活圈",
        "基于 GVI 数据评估绿视率盲区，进行 15 分钟社区生活圈设施缺口测算。",
        eyebrow="Public Space & 15-min City",
    )

    render_summary_cards([
        {"value": str(stats.get("poi_count", "N/A")), "title": "POI 总量", "desc": "设施基线（数据可能不全）"},
    ])

    if st.button("🌳 生成公共空间系统设计方案", type="primary", key="s9_public", **stretch_width(st.button)):
        spatial_ctx = get_full_spatial_context()
        prompt = f"""你是一位资深景观与公共空间规划师，精通 15 分钟社区生活圈理论。

基于以下空间数据，为研究范围制定公共空间系统设计方案。

【上游空间结构（Stage 08）】：{spatial_structure[:2000] if spatial_structure else '一核两轴多片多节点'}
【全域空间数据】：{spatial_ctx[:3500]}

⚠️ 注意：POI 数据可能不完整，设施缺口分析应以现有数据为参考下限进行估算，
并明确标注"数据受限，实际缺口可能更大"。

请生成【公共空间系统设计方案】（不限字数，务必详实）：

一、绿视率盲区诊断
  - 基于 GVI 数据，识别绿视率低于 15% 的空间盲区
  - 盲区的空间分布特征与成因分析
  - 每个盲区的补绿策略（口袋公园/街角绿化/立体绿化）

二、公园绿地体系
  - 区级公园、社区公园、口袋公园的三级体系
  - 各级公园的选址建议（结合用地现状和可改造空间）
  - 绿地率目标与实现路径

三、15 分钟社区生活圈设施缺口
  - 医疗设施（社区卫生服务中心、诊所）
  - 教育设施（幼儿园、小学、中学）
  - 文体设施（社区活动中心、体育场地、图书角）
  - 商业便民设施（菜市场、便利店、药店）
  - 每类设施的现状数量、理论需求量、缺口量

四、开放空间网络
  - 主要开放空间节点及其串联路径
  - 滨水空间、铁路沿线空间的利用策略
  - 与慢行系统的耦合关系

五、适老化与无障碍改造
  - 社区公共空间的适老化设计要点
  - 无障碍通行网络

每一条建议都必须引用空间数据中的具体数字，并指明空间落位。"""

        stream = call_llm_engine_stream(
            prompt=prompt,
            system_prompt="资深公共空间规划师，精通15分钟生活圈与GVI绿视率分析。",
            model=model_tag,
        )
        result = st.write_stream(stream)
        if isinstance(result, str) and len(result) > 200:
            save_stage_output("09", SK.PUBLIC_SPACE, result)
            st.success(f"✅ 公共空间系统设计方案生成完成（{len(result)} 字）")

    saved = load_stage_output("09", SK.PUBLIC_SPACE, "")
    if saved:
        with st.expander("📋 已生成的公共空间系统设计方案", expanded=False):
            st.markdown(saved)


# ═══════════════════════════════════════════
# 模块三：建筑形态与天际线
# ═══════════════════════════════════════════

elif selected_sub == "🏛️ 建筑形态与天际线":
    render_section_intro(
        "建筑形态控制与天际线保护",
        "基于建筑高度数据推演天际线视廊，生成分区高度控制模型。",
        eyebrow="Building Form & Skyline",
    )

    render_summary_cards([
        {"value": sky.get("building_count", 0), "title": "建筑总量", "desc": "栋"},
        {"value": f"{sky.get('avg_height', 0)} m", "title": "平均高度", "desc": "全域"},
        {"value": f"{sky.get('max_height', 0)} m", "title": "最高建筑", "desc": "天际线峰值"},
        {"value": f"{sky.get('high_rise_ratio', 0)}%", "title": "高层占比", "desc": ">24m"},
    ])

    if st.button("🏛️ 生成建筑形态控制方案", type="primary", key="s9_building", **stretch_width(st.button)):
        spatial_ctx = get_full_spatial_context()
        prompt = f"""你是一位资深城市设计师，精通建筑形态控制与天际线保护。

基于以下空间数据，为研究范围制定建筑形态控制方案。

【上游空间结构（Stage 08）】：{spatial_structure[:2000] if spatial_structure else '一核两轴多片多节点'}
【建筑形态现状】：
  - 建筑总量: {sky.get('building_count', 0)} 栋
  - 平均高度: {sky.get('avg_height', 0)} m
  - 最高建筑: {sky.get('max_height', 0)} m
  - 高层占比(>24m): {sky.get('high_rise_ratio', 0)}%
【全域空间数据】：{spatial_ctx[:3000]}

【高度红线约束】：核心保护区限高 ≤9m，一般控制区限高 ≤18m。

请生成【建筑形态控制方案】（不限字数，务必详实）：

一、高度分区控制
  - 核心保护区（≤9m）：范围界定、适用建筑类型
  - 协调过渡区（≤18m）：范围界定、退台与过渡手法
  - 一般发展区（≤36m）：范围界定、高层布局原则
  以表格形式列出各分区的高度上限、适用区域和设计要求

二、天际线视廊保护
  - 核心视廊（从伪满皇宫向外的主要视线轴线）
  - 视廊内建筑高度递减策略
  - 天际线节奏设计（高低错落的韵律）

三、建筑密度控制
  - 各分区建筑密度上限
  - 建筑间距与日照要求
  - 围合式街区与通透式布局的适用场景

四、街墙界面控制
  - 贴线率要求（商业街区 vs 居住街区）
  - 底层架空与退台设计
  - 界面连续性与通透性平衡

五、建筑风貌引导
  - 屋顶形式（坡屋顶/平屋顶的适用区域）
  - 立面材质与色彩（结合历史风貌）
  - 细部构件引导（檐口、入口、阳台等）

每一条建议都必须引用现状建筑数据，并明确空间落位。"""

        stream = call_llm_engine_stream(
            prompt=prompt,
            system_prompt="资深城市设计师，精通建筑形态控制与天际线保护。方案必须有量化依据。",
            model=model_tag,
        )
        result = st.write_stream(stream)
        if isinstance(result, str) and len(result) > 200:
            save_stage_output("09", SK.BUILDING_FORM, result)
            st.success(f"✅ 建筑形态控制方案生成完成（{len(result)} 字）")

    saved = load_stage_output("09", SK.BUILDING_FORM, "")
    if saved:
        with st.expander("📋 已生成的建筑形态控制方案", expanded=False):
            st.markdown(saved)


# ═══════════════════════════════════════════
# 模块四：风貌景观与文保
# ═══════════════════════════════════════════

elif selected_sub == "🎨 风貌景观与文保":
    render_section_intro(
        "风貌景观设计与历史保护",
        "历史界面修补、材料与色彩提取体系、文保建筑周边环境整治。",
        eyebrow="Landscape & Heritage",
    )

    if st.button("🎨 生成风貌景观设计方案", type="primary", key="s9_landscape", **stretch_width(st.button)):
        spatial_ctx = get_full_spatial_context()
        prompt = f"""你是一位资深风貌景观设计师，精通历史街区保护与风貌修复。

基于以下空间数据，为研究范围制定风貌景观设计方案。

【上游空间结构（Stage 08）】：{spatial_structure[:2000] if spatial_structure else '一核两轴多片多节点'}
【全域空间数据】：{spatial_ctx[:3500]}
【历史背景】：研究范围以伪满皇宫为核心，周边存在大量日伪时期建筑遗存。

请生成【风貌景观设计方案】（不限字数，务必详实）：

一、风貌分区
  - 历史保护核心区（伪满皇宫周边）：严格保护策略
  - 风貌协调区：新旧对话策略
  - 现代发展区：当代城市设计策略
  以表格形式列出各分区的范围、风貌要求和管控要点

二、色彩控制体系
  - 基于历史建筑色彩提取的主色调谱系（如红砖、灰瓦、米黄墙面）
  - 各风貌分区的色彩导引（允许色/禁止色/强调色）
  - 广告标识与夜景照明的色彩协调

三、材料与质感控制
  - 传统材料复兴（砖、石、木、瓦）
  - 现代材料的融入方式（玻璃、金属、混凝土）
  - 铺装材料体系（主要街道、次要巷道、广场空间）

四、历史界面修补
  - 受损历史界面的修复策略
  - 缺失界面的织补手法（新建建筑如何延续历史肌理）
  - 文保建筑周边环境整治

五、景观节点设计导引
  - 主要景观节点的设计意向（广场、街角、口袋公园、滨水空间）
  - 景观家具与设施设计风格
  - 植物配置原则（乡土树种优先）

每一条建议都必须引用空间数据，并指明空间落位。"""

        stream = call_llm_engine_stream(
            prompt=prompt,
            system_prompt="资深风貌景观设计师，精通历史街区保护、色彩控制和材质体系。",
            model=model_tag,
        )
        result = st.write_stream(stream)
        if isinstance(result, str) and len(result) > 200:
            save_stage_output("09", SK.LANDSCAPE_STYLE, result)
            st.success(f"✅ 风貌景观设计方案生成完成（{len(result)} 字）")

    saved = load_stage_output("09", SK.LANDSCAPE_STYLE, "")
    if saved:
        with st.expander("📋 已生成的风貌景观设计方案", expanded=False):
            st.markdown(saved)


# ═══════════════════════════════════════════
# 模块五：图纸提示词生成
# ═══════════════════════════════════════════

elif selected_sub == "🖼️ 图纸提示词生成":
    render_drawing_prompt_ui("09", key_prefix="p9", stage_title="专项系统设计")


st.markdown("---")
render_stage_summary(
    stage_code="09",
    title="四大专项系统深度设计",
    findings=[
        {"point": f"交通系统覆盖道路分级、慢行网络化、TOD 最后一公里接驳评估", "evidence": "路网拓扑 + POI 空间分析"},
        {"point": f"公共空间系统完成绿视率盲区诊断与 15 分钟生活圈设施缺口测算", "evidence": "GVI 数据 + POI 设施分类"},
        {"point": f"建筑形态按三级分区控制高度（核心≤9m/过渡≤18m/一般≤36m），含天际线视廊保护", "evidence": "建筑底图高度统计"},
        {"point": "风貌景观建立色彩-材料-历史界面三位一体的设计体系", "evidence": "保护建筑数据 + 用地分类"},
    ],
    methodology="基于 DeepSeek V4 Pro 的四专项并行深度策划，全量注入空间数据",
    implication="为重点地段深化（Stage 10）提供了交通/空间/形态/风貌四大维度的设计约束和导引",
)
