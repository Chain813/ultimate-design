"""阶段 11：实施路径 —— 双层体系（全域 + 重点地块）+ LLM 深度策划。

第一层：全域实施路径（基础设施升级、政策投放、文旅线路等宏观骨架）
第二层：重点地块实施路径（资金筹措、业态进驻、改造节点等微观触媒）

下层（重点地块）必须明确标注其如何服务并驱动上层（全域）目标。
"""

import streamlit as st
from src.ui.design_system import render_page_banner, render_section_intro
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.ui.module_summary import render_stage_summary
from src.engines.llm_engine import call_llm_engine_stream
from src.engines.site_diagnostic_engine import get_plot_diagnostics
from src.engines.spatial_data_injector import (
    get_full_spatial_context,
    get_key_plots_summary,
)
from src.workflow.stage_data_bus import (
    save_stage_output, load_stage_output, render_evidence_chain_bar,
)
from src.workflow.stage_keys import SK
from src.ui.drawing_prompt_ui import render_drawing_prompt_ui
from src.ui.streamlit_compat import stretch_width

st.set_page_config(page_title="11 实施路径", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()
render_engine_status_alert()

render_page_banner(
    title="实施路径",
    description="双层实施体系：第一层为全域宏观骨架（基础设施、政策、文旅线路），"
                "第二层为重点地块微观触媒（改造节点、资金筹措、业态进驻），下层服务上层。",
    eyebrow="Stage 11",
    tags=["双层体系", "全域路径", "地块触媒", "分期实施"],
)
render_evidence_chain_bar("11", ["10", "11", "12"])

with st.sidebar:
    model_tag = st.selectbox(
        "DeepSeek 模型",
        ["deepseek-v4-flash", "deepseek-v4-pro"],
        index=1,
        key="p11_model",
    )

SUB_OPTIONS = [
    "🌐 第一层：全域实施路径",
    "📍 第二层：重点地块实施路径",
    "🏗️ 更新方式分类",
    "🖼️ 图纸提示词生成",
]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")


# ═══════════════════════════════════════════
# 第一层：全域实施路径
# ═══════════════════════════════════════════

if selected_sub == "🌐 第一层：全域实施路径":
    render_section_intro(
        "全域实施路径（宏观骨架）",
        "涵盖整个研究范围的基础设施升级时序、全域政策组合拳、"
        "文化旅游线路贯通工程等宏观层面的实施计划。",
        eyebrow="Region-wide Phasing",
    )

    # 加载前序数据
    strategy = load_stage_output("07", SK.STRATEGY_MATRIX, "")
    spatial_ctx = get_full_spatial_context()

    with st.expander("📊 前序策略矩阵与空间数据", expanded=False):
        if strategy:
            st.markdown(strategy)
        else:
            st.info("暂无策略矩阵数据（来自 Stage 07）。")
        st.text(get_key_plots_summary())

    if st.button("🌐 生成全域实施路径", type="primary", key="s11_region", **stretch_width(st.button)):
        prompt = f"""你是一位资深城市更新实施策划专家。

基于以下前期分析数据，制定覆盖**整个研究范围（伪满皇宫周边约150公顷）**的全域实施路径。

【策略矩阵】：{strategy[:2000] if strategy else '政策引导→产业导入→经济盘活→空间更新的良性循环'}
【空间数据】：{spatial_ctx[:3000]}

请生成【全域实施路径报告】，按以下框架展开：

一、近期行动（1-3年）—— 触媒激活与环境改善
  要求：详细列出每个行动项的空间范围、投资估算、实施主体、预期效果。
  至少包含：环境整治、口袋公园、慢行系统、导视系统、夜景照明、社区适老设施等。

二、中期建设（3-5年）—— 产业导入与功能升级
  要求：详细列出产业导入策略、功能置换方案、基础设施升级工程等。
  至少包含：文旅产业集群打造、商业业态升级、交通枢纽对接、公共空间系统建设等。

三、远期目标（5-10年）—— 品牌运营与持续发展
  要求：详细列出品牌塑造策略、长效运营机制、评估反馈系统等。
  至少包含：片区整体形象塑造、文旅品牌运营、智慧管理系统、碳中和目标等。

四、政策组合拳时序表
  以表格形式呈现各阶段需要投放的核心政策工具。

五、资金闭环模型
  说明各阶段的资金来源、投资回收路径和可持续运营模式。

每个实施项目都必须有理有据、详实到可操作层面。"""

        stream = call_llm_engine_stream(
            prompt=prompt,
            system_prompt="资深城市更新实施策划专家，精通分期实施和政策-资金-空间协调。",
            model=model_tag,
        )
        result = st.write_stream(stream)
        if isinstance(result, str) and len(result) > 200:
            save_stage_output("11", "region_phasing", result)
            st.success(f"全域实施路径生成完成（{len(result)} 字）")

    saved = load_stage_output("11", "region_phasing", "")
    if saved:
        with st.expander("📋 已生成的全域实施路径", expanded=False):
            st.markdown(saved)


# ═══════════════════════════════════════════
# 第二层：重点地块实施路径
# ═══════════════════════════════════════════

elif selected_sub == "📍 第二层：重点地块实施路径":
    render_section_intro(
        "重点地块实施路径（微观触媒）",
        "每个重点地块的具体改造节点、资金筹措方案、业态进驻时间表，"
        "且必须明确标注其如何服务并驱动全域目标。",
        eyebrow="Plot-level Trigger",
    )

    diags = get_plot_diagnostics()
    if not diags:
        st.warning("暂无地块诊断数据，请先完成 Stage 05 量化分析。")
        st.stop()

    # 按 MPI 排序
    diags_sorted = sorted(diags, key=lambda x: x["mpi_score"], reverse=True)

    selected_plot = st.selectbox(
        "选择重点地块",
        [d["name"] for d in diags_sorted],
        format_func=lambda n: f"{n} (MPI: {next(d['mpi_score'] for d in diags_sorted if d['name'] == n)})",
    )

    d = next(dd for dd in diags_sorted if dd["name"] == selected_plot)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("MPI 得分", d["mpi_score"])
    c2.metric("面积", f"{d['area_ha']} ha")
    c3.metric("GVI", f"{d['gvi_mean']}%")
    c4.metric("POI", d["poi_count"])

    region_plan = load_stage_output("11", "region_phasing", "")

    if st.button(f"📍 生成 {selected_plot} 实施路径", type="primary", **stretch_width(st.button)):
        prompt = f"""你是一位城市更新实施策划专家。

请为重点地块【{selected_plot}】制定详细的实施路径。

【地块数据】：
  - MPI 更新潜力: {d['mpi_score']}
  - 面积: {d['area_ha']} ha
  - 绿视率 GVI: {d['gvi_mean']}%
  - POI 密度: {d['poi_count']} 个
  - 情感指数: {d['sentiment_mean']}

【全域实施路径（本地块必须服务于此）】：
{region_plan[:2000] if region_plan else '近期触媒激活→中期产业导入→远期品牌运营'}

请生成【重点地块实施路径报告】：

一、地块定位与角色
  明确本地块在全域实施中的角色（如"启动引擎""文化节点""社区服务锚点"等），
  以及它如何驱动和服务全域目标。

二、近期改造行动（1-2年）
  详细列出每个改造节点、投资估算、实施主体、工期。

三、中期功能升级（2-5年）
  业态导入方案、功能置换计划、配套设施建设。

四、资金筹措方案
  明确资金来源：财政拨款、PPP、文旅运营收入、社会资本等配比。

五、业态进驻时间表
  以时间轴表格形式呈现各业态的进驻节点和招商策略。

六、风险与对策
  列出可能的实施风险及应对措施。

每一项都必须详实到可操作层面。"""

        stream = call_llm_engine_stream(
            prompt=prompt,
            system_prompt="资深城市更新实施策划专家，精通地块级操作和投融资安排。",
            model=model_tag,
        )
        result = st.write_stream(stream)
        if isinstance(result, str) and len(result) > 200:
            save_stage_output("11", f"plot_phasing_{selected_plot}", result)
            st.success(f"{selected_plot} 实施路径生成完成（{len(result)} 字）")


# ═══════════════════════════════════════════
# 更新方式分类
# ═══════════════════════════════════════════

elif selected_sub == "🏗️ 更新方式分类":
    render_section_intro(
        "建筑与用地更新方式分类",
        "按保护—修缮—改造—置换—拆建—微更新六类进行分类。",
        eyebrow="Update Classification",
    )

    categories = [
        {"类型": "保护", "适用对象": "文保单位、历史建筑", "策略": "原址保护、修旧如旧", "color": "🔴"},
        {"类型": "修缮", "适用对象": "风貌较好但老旧的建筑", "策略": "立面整治、结构加固", "color": "🟠"},
        {"类型": "改造", "适用对象": "功能落后、结构可利用", "策略": "功能置换、空间重组", "color": "🟡"},
        {"类型": "置换", "适用对象": "低效工业用地、仓储空间", "策略": "功能转型、产业导入", "color": "🔵"},
        {"类型": "拆除新建", "适用对象": "危房、严重低效区", "策略": "公共空间补充、设施重建", "color": "🟣"},
        {"类型": "微更新", "适用对象": "街角、巷道、社区公共空间", "策略": "渐进式提升、触媒激活", "color": "🟢"},
    ]

    import pandas as pd
    df = pd.DataFrame(categories)
    st.dataframe(df, hide_index=True, **stretch_width(st.dataframe))

elif selected_sub == "🖼️ 图纸提示词生成":
    render_drawing_prompt_ui("11", key_prefix="p11", stage_title="实施路径")


st.markdown("---")
render_stage_summary(
    stage_code="11",
    title="双层实施路径体系",
    findings=[
        {"point": "第一层全域实施路径覆盖近中远三期，含政策组合拳和资金闭环模型", "evidence": "全域空间数据 + 策略矩阵"},
        {"point": "第二层重点地块实施路径精细到改造节点和业态进驻时间表", "evidence": "MPI排行 + 地块空间诊断"},
        {"point": "下层（重点地块）明确服务上层（全域），构成'触媒激活→全域辐射'的嵌套体系", "evidence": "双层联动逻辑"},
    ],
    methodology="基于 DeepSeek API 深度策划 + MPI 数据驱动的分期时序映射",
    implication="为城市设计导则（Stage 12）提供了详实的管控实施框架和时序保障",
)
