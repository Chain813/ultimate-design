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
)
from src.engines.spatial_engine import get_hud_statistics, get_skyline_features
from src.workflow.stage_data_bus import (
    save_stage_output, load_stage_output, render_evidence_chain_bar,
)
from src.workflow.stage_keys import SK
from src.ui.drawing_prompt_ui import render_drawing_prompt_ui
from src.ui.streamlit_compat import stretch_width

st.set_page_config(page_title="08 总体城市设计", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()
render_engine_status_alert()

stats = get_hud_statistics()
sky = get_skyline_features()

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
    if saved_structure:
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

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        res_pct = st.slider("🏠 居住用地占比 (%)", 20, 70, 50, key="sb_res")
        com_pct = st.slider("🏪 商业服务业用地占比 (%)", 5, 40, 20, key="sb_com")
        off_pct = st.slider("🏢 商务办公用地占比 (%)", 3, 25, 10, key="sb_off")
    with col_s2:
        green_pct = st.slider("🌳 公园绿地占比 (%)", 5, 30, 12, key="sb_green")
        public_pct = st.slider("🏛️ 公共设施用地占比 (%)", 3, 20, 8, key="sb_pub")
        total = res_pct + com_pct + off_pct + green_pct + public_pct
        remain = max(0, 100 - total)
        st.metric("📊 剩余（道路/市政等）", f"{remain}%")
        if total > 100:
            st.error(f"⚠️ 功能用地占比之和 ({total}%) 超过 100%，请调整。")

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
            save_stage_output("08", SK.LANDUSE_SANDBOX, {"scenario": scenario, "evaluation": result})
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
