import streamlit as st

from src.ui.design_system import render_page_banner, render_section_intro
from src.ui.app_shell import render_top_nav
from src.workflow.city_design_workflow import (
    board_stage_options,
    render_stage_workbench,
    resolve_stage_option,
    stage_code_from_option,
)


BOARD_KEY = "middle"

st.set_page_config(page_title="中期概念生成与应对策略", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

render_page_banner(
    title="中期概念生成与应对策略",
    description="按 06-07 阶段组织目标定位、概念提炼、策略生成和多主体协商资源。",
    eyebrow="Board 02",
    tags=["06 目标定位", "07 设计策略"],
    metrics=[
        {"value": "2", "label": "阶段", "meta": "06-07"},
        {"value": "策略", "label": "核心", "meta": "问题转目标"},
        {"value": "协商", "label": "方法", "meta": "多主体共识"},
        {"value": "矩阵", "label": "表达", "meta": "问题-策略响应"},
    ],
)

options = board_stage_options(BOARD_KEY)
index = resolve_stage_option(BOARD_KEY)
selected_code = stage_code_from_option(options[index])

render_stage_workbench(selected_code)
