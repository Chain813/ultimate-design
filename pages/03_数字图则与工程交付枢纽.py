"""工作台 3：数字图则与工程交付枢纽 (Delivery Hub)

聚合模块：
1. 工业级 AutoCAD DXF 矢量工程图纸导出 (原 Stage 13)
2. 城市设计数字导则 (Word 规范导出) (原 Stage 12)
3. 161 页 A3 规划成果图册与答辩 PPT (原 Stage 13)
4. 多专项系统深化与留改拆实施时序 (原 Stage 09 + 11)
"""

import streamlit as st

st.set_page_config(page_title="03 数字图则与工程交付枢纽", layout="wide", initial_sidebar_state="collapsed")

from src.ui.app_shell import render_engine_status_alert, render_logic_chain_stepper, render_top_nav
from src.ui.design_system import render_page_banner
from src.stages.stage13_outputs.page import render_page as render_stage13_page
from src.stages.stage12_guideline.page import render_page as render_stage12_page
from src.stages.stage09_systems.page import render_page as render_stage09_page
from src.stages.stage11_implementation.page import render_page as render_stage11_page

def main():
    render_top_nav()
    render_engine_status_alert()

    render_page_banner(
        title="数字图则与工程交付枢纽",
        description="工作台 03：工业级 AutoCAD DXF 矢量导出 · 法定设计导则 (Word) · 161 页答辩图册。实现从概念方案到工业级工程施工图纸与法定公文的真实闭环交付。",
        eyebrow="Workbench 03",
        tags=["AutoCAD 2000 DXF导出", "1:1米制工程图纸", "Word法定导则", "161页答辩图册", "全流程工程闭环"],
    )

    # 工作台内一级分流 Tab
    tab_deliver, tab_guideline, tab_systems, tab_time = st.tabs([
        "📐 工程图纸、DXF 导出与成果图册 (Stage 13)",
        "📜 城市设计数字导则 (Word 说明书) (Stage 12)",
        "🔧 多专项系统空间叠合 (Stage 09)",
        "📅 留改拆实施路径与时序 (Stage 11)",
    ])

    with tab_deliver:
        render_stage13_page()

    with tab_guideline:
        render_stage12_page()

    with tab_systems:
        render_stage09_page()

    with tab_time:
        render_stage11_page()

if __name__ == "__main__":
    main()
