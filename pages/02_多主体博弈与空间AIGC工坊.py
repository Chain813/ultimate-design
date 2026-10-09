"""工作台 2：多主体博弈与空间 AIGC 工坊 (Game & AIGC Studio)

聚合模块：
1. 多主体协同博弈与设计策略矩阵 (原 Stage 06 + 07)
2. 总体空间结构与用地沙盘 (原 Stage 08)
3. 重点地段 AIGC 意向深化与 Before/After 卷帘对比 (原 Stage 10 + 15)
"""

import streamlit as st

st.set_page_config(page_title="02 多主体博弈与空间AIGC工坊", layout="wide", initial_sidebar_state="collapsed")

from src.ui.app_shell import render_engine_status_alert, render_logic_chain_stepper, render_top_nav
from src.ui.design_system import render_page_banner
from src.stages.stage07_strategy.page import render_page as render_stage07_page
from src.stages.stage08_master_plan.page import render_page as render_stage08_page
from src.stages.stage10_detail_design.page import render_page as render_stage10_page

def main():
    render_top_nav()
    render_engine_status_alert()

    render_page_banner(
        title="多主体博弈与空间 AIGC 工坊",
        description="工作台 02：多主体协同博弈决策 · 总体空间结构沙盘 · GIS 刚性骨架 ControlNet 约束生形 · Before/After 卷帘对比。让 AI 在规划红线与法定控规约束下戴着镣铐跳舞，杜绝空间幻觉。",
        eyebrow="Workbench 02",
        tags=["多主体协商博弈", "拆改留共识平衡", "设计纲要自动生成", "GIS刚性AIGC生形", "Before/After对比"],
    )

    # 工作台内一级分流 Tab
    tab_game, tab_master, tab_detail = st.tabs([
        "🤝 多主体博弈与设计纲要 (Stage 07)",
        "🗺️ 总体空间结构沙盘 (Stage 08)",
        "🎨 重点地段 AIGC 生形与卷帘对比 (Stage 10/15)",
    ])

    with tab_game:
        render_stage07_page()

    with tab_master:
        render_stage08_page()

    with tab_detail:
        render_stage10_page()

if __name__ == "__main__":
    main()
