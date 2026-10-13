"""工作台 3：数字图则与工程交付枢纽 (Delivery Hub)

聚合模块：
1. 工业级 AutoCAD DXF 矢量工程图纸导出 (原 Stage 13)
2. 城市设计数字导则 (Word 规范导出) (原 Stage 12)
3. 161 页 A3 规划成果图册与答辩 PPT (原 Stage 13)
4. 多专项系统深化与留改拆实施时序 (原 Stage 09 + 11)
"""

import streamlit as st

st.set_page_config(page_title="03 数字图则与工程交付枢纽", layout="wide", initial_sidebar_state="collapsed")

from src.ui.app_shell import render_engine_status_alert, render_top_nav
from src.ui.design_system import render_page_banner, render_workbench_subnav
from src.stages.stage13_outputs.page import render_page as render_stage13_page
from src.stages.stage12_guideline.page import render_page as render_stage12_page
from src.stages.stage09_systems.page import render_page as render_stage09_page
from src.stages.stage11_implementation.page import render_page as render_stage11_page


WB3_OPTIONS = [
    "📐 工程图纸与 AutoCAD DXF 导出 (Stage 13)",
    "📜 城市设计数字导则 (Word 规范) (Stage 12)",
    "🔧 多专项系统空间叠合 (Stage 09)",
    "📅 留改拆实施时序总图 (Stage 11)",
]

WB3_OPTION_TO_PARAM = {
    WB3_OPTIONS[0]: "delivery",
    WB3_OPTIONS[1]: "guideline",
    WB3_OPTIONS[2]: "systems",
    WB3_OPTIONS[3]: "timing",
}

WB3_PARAM_TO_OPTION = {
    "delivery": WB3_OPTIONS[0],
    "deliver": WB3_OPTIONS[0],
    "dxf": WB3_OPTIONS[0],
    "cad": WB3_OPTIONS[0],
    "13": WB3_OPTIONS[0],
    "16": WB3_OPTIONS[0],
    "成果": WB3_OPTIONS[0],
    "图纸": WB3_OPTIONS[0],
    "guideline": WB3_OPTIONS[1],
    "12": WB3_OPTIONS[1],
    "导则": WB3_OPTIONS[1],
    "word": WB3_OPTIONS[1],
    "规范": WB3_OPTIONS[1],
    "systems": WB3_OPTIONS[2],
    "system": WB3_OPTIONS[2],
    "09": WB3_OPTIONS[2],
    "专项": WB3_OPTIONS[2],
    "叠合": WB3_OPTIONS[2],
    "timing": WB3_OPTIONS[3],
    "time": WB3_OPTIONS[3],
    "implementation": WB3_OPTIONS[3],
    "11": WB3_OPTIONS[3],
    "时序": WB3_OPTIONS[3],
    "实施": WB3_OPTIONS[3],
    "留改拆": WB3_OPTIONS[3],
}


def main():
    render_top_nav()
    render_engine_status_alert()

    render_page_banner(
        title="数字图则与工程交付枢纽",
        description="工作台 03：工业级 AutoCAD DXF 矢量导出 · 法定设计导则 (Word) · 161 页答辩图册。实现从概念方案到工业级工程施工图纸与法定公文的真实闭环交付。",
        eyebrow="Workbench 03",
        tags=["AutoCAD 2000 DXF导出", "1:1米制工程图纸", "Word法定导则", "161页答辩图册", "全流程工程闭环"],
    )

    selected = render_workbench_subnav(
        options=WB3_OPTIONS,
        option_to_param=WB3_OPTION_TO_PARAM,
        param_to_option=WB3_PARAM_TO_OPTION,
        default_sub="delivery",
        widget_key="wb3_sub_nav",
    )

    # 按需条件渲染 (Lazy Rendering) + 嵌入模式防嵌套保护
    try:
        st.session_state["_embedded_mode"] = True
        if selected == WB3_OPTIONS[0]:
            render_stage13_page()
        elif selected == WB3_OPTIONS[1]:
            render_stage12_page()
        elif selected == WB3_OPTIONS[2]:
            render_stage09_page()
        elif selected == WB3_OPTIONS[3]:
            render_stage11_page()
    finally:
        st.session_state["_embedded_mode"] = False


if __name__ == "__main__":
    main()
