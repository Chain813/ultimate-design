"""阶段 11：实施路径 —— 更新方式分类 + 分期实施 + LLM 五阶段汇总。"""

import streamlit as st
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.ui.module_summary import render_stage_summary
from src.engines.drawing_prompt_templates import get_templates_by_stage, build_drawing_prompt, generate_drawing_prompt_with_llm
from src.workflow.stage_data_bus import load_stage_output, render_evidence_chain_bar

st.set_page_config(page_title="11 实施路径", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()
render_engine_status_alert()

render_page_banner(
    title="实施路径",
    description="确定保护、修缮、改造、置换和微更新五类更新方式，并制定近中远期分期实施计划。",
    eyebrow="Stage 11",
    tags=["五类更新", "分期实施", "近期行动"],
)
render_evidence_chain_bar("11", ["10", "11", "12"])

SUB_OPTIONS = ["🏗️ 更新方式分类", "📅 分期实施计划", "🖼️ 图纸提示词生成"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

if selected_sub == "🏗️ 更新方式分类":
    render_section_intro("建筑与用地更新方式分类", "按保护—修缮—改造—置换—拆建—微更新六类进行分类。", eyebrow="Update Classification")

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
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.info("💡 留改拆总图请前往原 **更新设计成果展示** 页面查看 GIS 图层标注。")

elif selected_sub == "📅 分期实施计划":
    render_section_intro("近中远期分期实施", "按三期推进更新实施。", eyebrow="Phasing")

    phases = {
        "🟢 近期（1-3年）": ["环境整治与界面清理", "口袋公园和街角微更新", "社区适老设施补充", "导视系统和夜景照明", "长春站接驳通道优化"],
        "🔵 中期（3-5年）": ["中车厂区工业遗产活化", "光复路商业业态升级", "重点地块功能置换", "慢行系统贯通", "公共空间系统建设"],
        "🟣 远期（5-10年）": ["片区整体城市形象塑造", "文旅品牌运营体系", "智慧城市管理系统", "碳中和与韧性设计", "长期运营评估反馈"],
    }

    for phase, items in phases.items():
        with st.expander(phase, expanded=True):
            for item in items:
                st.checkbox(item, value=False, key=f"phase_{item}")

elif selected_sub == "🖼️ 图纸提示词生成":
    render_section_intro("实施类图纸提示词", "生成分期实施图、更新方式分类图等。", eyebrow="Drawing Prompts")
    with st.sidebar:
        model_tag = st.text_input("Gemma 4 模型标签", value="gemma4:e2b-it-q4_K_M", key="p11_model")
    templates = get_templates_by_stage("11")
    if templates:
        selected_tmpl = st.selectbox("选择图纸模板", [t.name for t in templates])
        tmpl = next(t for t in templates if t.name == selected_tmpl)
        st.markdown(f"**{tmpl.description}**")
        prompt_text, _ = build_drawing_prompt(selected_tmpl)
        st.text_area("数据注入后的提示词", value=prompt_text, height=300)
        if st.button("🧠 调用 Gemma 4 生成", type="primary", use_container_width=True):
            with st.spinner("生成中..."):
                result = generate_drawing_prompt_with_llm(selected_tmpl, model=model_tag)
            st.text_area("完整提示词", value=result, height=400)
    else:
        st.info("暂无本阶段图纸模板。")

st.markdown("---")
render_stage_summary(
    stage_code="11",
    title="实施路径与分期计划",
    findings=[
        {"point": "按六类更新方式分类处置：保护、修缮、改造、置换、拆建、微更新", "evidence": "城市更新设计规范"},
        {"point": "三期实施推进：近期环境整治、中期功能置换、远期品牌塑造", "evidence": "分期实施计划"},
        {"point": "近期行动优先聚焦社区微更新和长春站接驳优化", "evidence": "MPI 优先级排序 + 居民需求"},
    ],
    methodology="基于城市更新分类管控与分期推进策略",
    implication="为城市设计导则（Stage 12）提供了管控实施框架",
)
