"""阶段 08：总体城市设计 —— 概念总平面图生形 + AIGC 推演。"""

import streamlit as st
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.ui.module_summary import render_stage_summary
from src.engines.drawing_prompt_templates import get_templates_by_stage, build_drawing_prompt, generate_drawing_prompt_with_llm
from src.workflow.stage_data_bus import save_stage_output, load_stage_output, render_evidence_chain_bar

st.set_page_config(page_title="08 总体城市设计", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()
render_engine_status_alert()

render_page_banner(
    title="总体城市设计",
    description="基于前期策略框架，通过 AIGC 辅助完成概念总平面图生形和空间结构推演。",
    eyebrow="Stage 08",
    tags=["概念总平面", "空间结构", "AIGC 生形"],
)
render_evidence_chain_bar("08", ["07", "08", "09", "10"])

SUB_OPTIONS = ["🗺️ 概念总平面图生形", "🖼️ 图纸提示词生成"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

if selected_sub == "🗺️ 概念总平面图生形":
    render_section_intro("概念总平面图生形", "使用 Stable Diffusion + ControlNet 约束生成总体空间意向。", eyebrow="Master Plan Generation")

    render_summary_cards([
        {"value": "SD + ControlNet", "title": "生成引擎", "desc": "约束条件下的空间推演"},
        {"value": "Canny/MLSD/Depth", "title": "约束算子", "desc": "支持多种空间控制"},
    ])

    st.info("💡 完整的 AIGC 推演面板（含底图上传、约束参数、Before/After 对比）请前往原 **AIGC设计推演** 页面操作。"
            "\n\n本页面聚焦于总体层面的概念生形和图纸提示词生成。")

    strategy = load_stage_output("07", "strategy_matrix", "")
    if strategy:
        with st.expander("📋 前序策略矩阵（来自 Stage 07）", expanded=False):
            st.markdown(strategy)

    save_stage_output("08", "status", "已就绪")

elif selected_sub == "🖼️ 图纸提示词生成":
    render_section_intro("总体设计类图纸提示词", "生成总平面图、鸟瞰图、功能布局图等。", eyebrow="Drawing Prompts")
    with st.sidebar:
        model_tag = st.text_input("Gemma 4 模型标签", value="gemma4:e2b-it-q4_K_M", key="p8_model")

    # 合并所有可用的总体设计模板
    all_names = ["总平面图", "鸟瞰效果图", "功能布局图", "土地利用规划图"]
    templates = get_templates_by_stage("08")
    tmpl_names = [t.name for t in templates] if templates else []
    # 对于没有预设模板的图纸，提供通用生成
    available = tmpl_names if tmpl_names else all_names

    selected_tmpl = st.selectbox("选择图纸类型", available)
    if selected_tmpl in tmpl_names:
        prompt_text, _ = build_drawing_prompt(selected_tmpl)
        st.text_area("数据注入后的提示词", value=prompt_text, height=300)
        if st.button("🧠 调用 Gemma 4 生成", type="primary", use_container_width=True):
            with st.spinner("生成中..."):
                result = generate_drawing_prompt_with_llm(selected_tmpl, model=model_tag)
            st.text_area("完整 Image 2.0 提示词", value=result, height=400)
    else:
        st.info(f"「{selected_tmpl}」暂无预设模板，请使用通用图纸提示词助手。")

st.markdown("---")
render_stage_summary(
    stage_code="08",
    title="总体空间结构研判",
    findings=[
        {"point": "空间结构采用'一核两轴多片多节点'的组织模式", "evidence": "伪满皇宫文化核心 + 站城活力轴 + 工业遗产更新轴"},
        {"point": "AIGC 辅助生成概念总平面和轴测鸟瞰意向方案", "evidence": "Stable Diffusion + ControlNet 约束推演"},
    ],
    methodology="基于 Stable Diffusion 的约束条件空间推演",
    implication="为专项系统设计（Stage 09）提供了总体空间骨架",
)
