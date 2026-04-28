import streamlit as st

from src.ui.design_system import render_page_banner, render_section_intro
from src.ui.app_shell import render_top_nav
from src.workflow.city_design_workflow import (
    board_stage_options,
    render_stage_workbench,
    resolve_stage_option,
    stage_code_from_option,
)


BOARD_KEY = "late"

st.set_page_config(page_title="后期设计生成与成果表达", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

render_page_banner(
    title="后期设计生成与成果表达",
    description="按 08-13 阶段组织总体设计、专项系统、重点深化、实施路径、导则和成果表达资源。",
    eyebrow="Board 03",
    tags=["08 总体城市设计", "09 专项系统设计", "10 重点地段深化", "11 实施路径", "12 城市设计导则", "13 成果表达"],
    metrics=[
        {"value": "6", "label": "阶段", "meta": "08-13"},
        {"value": "方案", "label": "核心", "meta": "空间落地"},
        {"value": "导则", "label": "管控", "meta": "实施约束"},
        {"value": "交付", "label": "输出", "meta": "图册 / 文本 / Word"},
    ],
)

options = board_stage_options(BOARD_KEY)
index = resolve_stage_option(BOARD_KEY)
selected_code = stage_code_from_option(options[index])

render_stage_workbench(selected_code)
