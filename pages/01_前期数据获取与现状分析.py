import streamlit as st

from src.ui.design_system import render_page_banner
from src.ui.app_shell import render_top_nav
from src.workflow.city_design_workflow import (
    board_stage_options,
    render_stage_workbench,
    resolve_stage_option,
    stage_code_from_option,
)


BOARD_KEY = "early"

st.set_page_config(page_title="前期数据获取与现状分析", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

render_page_banner(
    title="前期数据获取与现状分析",
    description="按 01-05 阶段组织边界、资料、调研、现状分析和问题诊断资源。",
    eyebrow="Board 01",
    tags=["01 任务解读", "02 资料收集", "03 现场调研", "04 现状分析", "05 问题诊断"],
    metrics=[
        {"value": "5", "label": "阶段", "meta": "01-05"},
        {"value": "5", "label": "已接入", "meta": "任务、资料、调研、现状、诊断"},
        {"value": "0", "label": "占位", "meta": "现场调研已独立成页"},
        {"value": "数据优先", "label": "板块逻辑", "meta": "先证据，后判断"},
    ],
)

options = board_stage_options(BOARD_KEY)
index = resolve_stage_option(BOARD_KEY)
selected_code = stage_code_from_option(options[index])

render_stage_workbench(selected_code)
