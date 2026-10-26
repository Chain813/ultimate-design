"""工作台 2：多主体博弈与空间 AIGC 工坊 (Game & AIGC Studio)

聚合模块：
1. 多主体协同博弈与设计策略矩阵 (原 Stage 06 + 07)
2. 总体空间结构与用地沙盘 (原 Stage 08)
3. 重点地段深化设计 (原 Stage 10)
4. 空间 AIGC 推演工坊 (原 Stage 15)
"""

from importlib import import_module
from pathlib import Path

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
    "🔍 重点地段深化",
    "✨ 空间 AIGC 推演工坊",
]

WB2_OPTION_TO_PARAM = {
    WB2_OPTIONS[0]: "strategy",
    WB2_OPTIONS[1]: "master_plan",
    WB2_OPTIONS[2]: "aigc",
    WB2_OPTIONS[3]: "aigc_studio",
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
    "节点": WB2_OPTIONS[2],
    "重点": WB2_OPTIONS[2],
    "重点地段": WB2_OPTIONS[2],
    "卷帘": WB2_OPTIONS[2],
    "aigc_studio": WB2_OPTIONS[3],
    "studio": WB2_OPTIONS[3],
    "15": WB2_OPTIONS[3],
    "生形": WB2_OPTIONS[3],
    "透视": WB2_OPTIONS[3],
    "鸟瞰": WB2_OPTIONS[3],
}


def _render_stage06_quick_panel() -> None:
    """在 Stage 07 博弈前提供 Stage 06 目标定位与案例对标快捷生成面板，打通 Stage 12 依赖门控。"""
    from src.config.site import get_site_city, get_site_name
    from src.engines.llm_engine import call_llm_engine_stream
    from src.engines.spatial_data_injector import get_full_spatial_context
    from src.ui.streamlit_compat import stretch_width
    from src.workflow.stage_data_bus import load_stage_output, save_stage_output
    from src.workflow.stage_keys import SK

    saved_case = load_stage_output("06", SK.CASE_BENCHMARK, "")
    saved_concept = load_stage_output("06", SK.DESIGN_CONCEPT, "")

    with st.expander(
        f"🎯 Stage 06 目标定位与案例对标 ({'✅ 已就绪' if saved_concept else '⏳ 建议先生成宏观目标定位'})",
        expanded=False,
    ):
        site_city = get_site_city() or "当地"
        site_name = get_site_name() or "更新示范街区"
        c_s6_1, c_s6_2 = st.columns(2)
        with c_s6_1:
            if st.button("📖 一键生成案例对标报告 (Stage 06)", key="wb2_s06_case_btn", **stretch_width(st.button)):
                spatial_ctx = get_full_spatial_context()
                case_context = ""
                case_path = Path("docs/开题报告_案例摘要.md")
                if case_path.exists():
                    case_context = case_path.read_text(encoding="utf-8")[:2000]
                prompt = (
                    f"请结合【{site_city}{site_name}】空间数据与国内外标杆更新案例，撰写【案例对标分析报告】，"
                    f"提炼 3-4 条本地化核心设计原则。\n\n案例参考：{case_context}\n\n空间数据：{spatial_ctx[:2000]}"
                )
                stream = call_llm_engine_stream(
                    prompt=prompt,
                    system_prompt=f"你是城市更新比较研究专家，紧密结合{site_city}{site_name}实际空间数据进行对标。",
                    model="deepseek-v4-flash",
                )
                res = st.write_stream(stream)
                if isinstance(res, str) and len(res) > 30:
                    save_stage_output("06", SK.CASE_BENCHMARK, res)
                    saved_case = res
                    st.success("✅ 案例对标报告已存入 Stage 06 总线！")
            if saved_case:
                st.caption(f"已存档案例对标（{len(saved_case)} 字）")

        with c_s6_2:
            if st.button("🎯 一键生成全域设计目标定位 (Stage 06)", type="primary", key="wb2_s06_concept_btn", **stretch_width(st.button)):
                spatial_ctx = get_full_spatial_context()
                s1 = load_stage_output("05", SK.DIAGNOSIS_REPORT, "") or load_stage_output("04", SK.DIAGNOSIS_REPORT, "")
                prompt = (
                    f"请基于前期诊断与全域空间数据，为【{site_city}{site_name}】制定【全域设计目标策划报告】，"
                    f"包含：一、总体设计愿景；二、分层目标体系；三、区域经济策划方向；四、土地利用优化建议。\n\n"
                    f"前期诊断：{s1[:1200] if s1 else '存量空间低效、慢行割裂、绿视率不足'}\n\n空间数据：{spatial_ctx[:2500]}"
                )
                stream = call_llm_engine_stream(
                    prompt=prompt,
                    system_prompt="你是资深城乡规划学术导师，严格基于空间量化数据制定全域设计目标体系。",
                    model="deepseek-v4-flash",
                )
                res = st.write_stream(stream)
                if isinstance(res, str) and len(res) > 30:
                    save_stage_output("06", SK.DESIGN_CONCEPT, res)
                    saved_concept = res
                    st.success("✅ 全域设计目标定位已存入 Stage 06 总线！")
            if saved_concept:
                st.caption(f"已存档全域设计目标（{len(saved_concept)} 字）")


def render_stage15_page() -> None:
    """加载并执行 Stage 15 空间 AIGC 推演工坊页面。"""
    mod15 = import_module("src.legacy_pages.15_AIGC设计推演")
    if hasattr(mod15, "render_page"):
        mod15.render_page()


def main():
    render_top_nav()
    render_engine_status_alert()

    render_page_banner(
        title="多主体博弈与空间 AIGC 工坊",
        description="工作台 02：多主体协同博弈决策 · 总体空间结构沙盘 · 重点地段深化 · GIS 刚性骨架 ControlNet 约束生形。让 AI 在规划红线与法定控规约束下戴着镣铐跳舞，杜绝空间幻觉。",
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

    # 严禁同时执行 Stage 07、08、10、15！按需懒加载并由嵌入模式包裹
    try:
        st.session_state["_embedded_mode"] = True
        if selected == WB2_OPTIONS[0]:
            _render_stage06_quick_panel()
            render_stage07_page()
        elif selected == WB2_OPTIONS[1]:
            render_stage08_page()
        elif selected == WB2_OPTIONS[2]:
            render_stage10_page()
        elif selected == WB2_OPTIONS[3]:
            render_stage15_page()
    finally:
        st.session_state["_embedded_mode"] = False


if __name__ == "__main__":
    main()
