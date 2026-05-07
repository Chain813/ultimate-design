"""阶段 08：总体城市设计 —— 概念总平面图生形 + AIGC 推演。"""

import streamlit as st
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.ui.module_summary import render_stage_summary
from src.workflow.stage_data_bus import save_stage_output, load_stage_output, render_evidence_chain_bar
from src.ui.drawing_prompt_ui import render_drawing_prompt_ui

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
    render_drawing_prompt_ui("08", key_prefix="p8", stage_title="总体城市设计")

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
