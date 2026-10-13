"""工作台 2：多主体博弈与空间 AIGC 工坊 (Game & AIGC Studio)

聚合模块：
1. 多主体协同博弈与设计策略矩阵 (原 Stage 06 + 07)
2. 总体空间结构与用地沙盘 (原 Stage 08)
3. 重点地段 AIGC 意向深化与 Before/After 卷帘对比 (原 Stage 10 + 15)
"""

import streamlit as st

st.set_page_config(page_title="02 多主体博弈与空间AIGC工坊", layout="wide", initial_sidebar_state="collapsed")

from src.ui.app_shell import render_engine_status_alert, render_top_nav
from src.ui.design_system import render_page_banner, render_workbench_subnav
from src.stages.stage07_strategy.page import render_page as render_stage07_page
from src.stages.stage08_master_plan.page import render_page as render_stage08_page
from src.stages.stage10_detail_design.page import render_page as render_stage10_page


WB2_OPTIONS = [
    "🤝 多主体博弈决策与设计纲要 (Stage 07)",
    "🗺️ 总体空间结构沙盘 (Stage 08)",
    "🎨 重点地段 AIGC 生形与卷帘对比 (Stage 10/15)",
]

WB2_OPTION_TO_PARAM = {
    WB2_OPTIONS[0]: "strategy",
    WB2_OPTIONS[1]: "master_plan",
    WB2_OPTIONS[2]: "aigc",
}

WB2_PARAM_TO_OPTION = {
    "strategy": WB2_OPTIONS[0],
    "game": WB2_OPTIONS[0],
    "06": WB2_OPTIONS[0],
    "07": WB2_OPTIONS[0],
    "博弈": WB2_OPTIONS[0],
    "策略": WB2_OPTIONS[0],
    "纲要": WB2_OPTIONS[0],
    "目标": WB2_OPTIONS[0],
    "master_plan": WB2_OPTIONS[1],
    "masterplan": WB2_OPTIONS[1],
    "master": WB2_OPTIONS[1],
    "08": WB2_OPTIONS[1],
    "总体": WB2_OPTIONS[1],
    "空间结构": WB2_OPTIONS[1],
    "用地": WB2_OPTIONS[1],
    "aigc": WB2_OPTIONS[2],
    "detail": WB2_OPTIONS[2],
    "10": WB2_OPTIONS[2],
    "15": WB2_OPTIONS[2],
    "生形": WB2_OPTIONS[2],
    "重点": WB2_OPTIONS[2],
    "重点地段": WB2_OPTIONS[2],
    "卷帘": WB2_OPTIONS[2],
    "透视": WB2_OPTIONS[2],
    "鸟瞰": WB2_OPTIONS[2],
}


def main():
    render_top_nav()
    render_engine_status_alert()

    render_page_banner(
        title="多主体博弈与空间 AIGC 工坊",
        description="工作台 02：多主体协同博弈决策 · 总体空间结构沙盘 · GIS 刚性骨架 ControlNet 约束生形 · Before/After 卷帘对比。让 AI 在规划红线与法定控规约束下戴着镣铐跳舞，杜绝空间幻觉。",
        eyebrow="Workbench 02",
        tags=["多主体协商博弈", "拆改留共识平衡", "设计纲要自动生成", "GIS刚性AIGC生形", "Before/After对比"],
    )

    from src.workflow.stage_data_bus import load_stage_output
    target_p = load_stage_output("04", "target_plot") or load_stage_output("07", "target_plot")
    if target_p and isinstance(target_p, dict):
        p_name = target_p.get("name", "靶向地块")
        p_mpi = target_p.get("mpi", "--")
        p_lu = target_p.get("land_use", target_p.get("type", "更新地块"))
        st.info(f"🎯 **当前工作台靶向锁定地块**：【{p_name}】（用地：{p_lu}，MPI综合潜力：{p_mpi}）—— 多主体博弈推演与空间 AIGC 生形已因地制宜联动。")


    selected = render_workbench_subnav(
        options=WB2_OPTIONS,
        option_to_param=WB2_OPTION_TO_PARAM,
        param_to_option=WB2_PARAM_TO_OPTION,
        default_sub="strategy",
        widget_key="wb2_sub_nav",
    )

    # 严禁同时执行 Stage 07、08、10！按需懒加载并由嵌入模式包裹
    try:
        st.session_state["_embedded_mode"] = True
        if selected == WB2_OPTIONS[0]:
            render_stage07_page()
        elif selected == WB2_OPTIONS[1]:
            render_stage08_page()
        elif selected == WB2_OPTIONS[2]:
            render_stage10_page()
    finally:
        st.session_state["_embedded_mode"] = False


if __name__ == "__main__":
    main()
