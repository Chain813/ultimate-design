"""工作台 1：全息空间诊断与数据沙盘 (Data & Diagnosis Workbench)

聚合模块：
1. 3D 现状空间底座与问题诊断 (原 Stage 04 + 数据大屏)
2. AHP-MPI 空间潜力诊断与地块雷达 (原 Stage 05)
3. 多源空间资产与现场调研档案 (原 Stage 00 + 02)
4. 双轨制空间地块自主接入引擎 (GeoJSON 上传 / 在线圈选 OSM 抓取)
"""

import streamlit as st

st.set_page_config(page_title="01 全息空间诊断与数据沙盘", layout="wide", initial_sidebar_state="collapsed")

from src.ui.app_shell import render_engine_status_alert, render_top_nav
from src.ui.design_system import (
    render_page_banner,
    render_section_intro,
    render_workbench_subnav,
)
from src.stages.stage04_diagnosis.page import render_page as render_stage04_page
from src.ui.site_ingestion_panel import get_active_candidate_plots, render_site_ingestion_panel
from src.ui.streamlit_compat import stretch_width


WB1_OPTIONS = [
    "🏢 空间诊断与 AHP-MPI 潜力沙盘",
    "📦 多源空间资产与调研资料",
    "🖥️ 全屏空间监控大屏",
]

WB1_OPTION_TO_PARAM = {
    WB1_OPTIONS[0]: "diagnosis",
    WB1_OPTIONS[1]: "assets",
    WB1_OPTIONS[2]: "datav",
}

WB1_PARAM_TO_OPTION = {
    "diagnosis": WB1_OPTIONS[0],
    "diag": WB1_OPTIONS[0],
    "04": WB1_OPTIONS[0],
    "05": WB1_OPTIONS[0],
    "现状": WB1_OPTIONS[0],
    "潜力": WB1_OPTIONS[0],
    "诊断": WB1_OPTIONS[0],
    "assets": WB1_OPTIONS[1],
    "asset": WB1_OPTIONS[1],
    "00": WB1_OPTIONS[1],
    "01": WB1_OPTIONS[1],
    "02": WB1_OPTIONS[1],
    "03": WB1_OPTIONS[1],
    "资料": WB1_OPTIONS[1],
    "资产": WB1_OPTIONS[1],
    "数据准备": WB1_OPTIONS[1],
    "上传": WB1_OPTIONS[1],
    "datav": WB1_OPTIONS[2],
    "screen": WB1_OPTIONS[2],
    "14": WB1_OPTIONS[2],
    "大屏": WB1_OPTIONS[2],
    "监控": WB1_OPTIONS[2],
    "全屏": WB1_OPTIONS[2],
}


def _render_wb1_assets():
    render_section_intro("多源空间数据资产与现场调研", "查看规划红线、建筑底模、街景采样点及政策法规库等底层支撑资料，支持双轨自主接入。", eyebrow="Spatial Assets")

    # 双轨接入引擎常驻嵌入
    render_site_ingestion_panel(title="空间数据资产上传与项目红线双轨接入")

    # 动态显示已挂载的候选地块资产
    cand_plots = get_active_candidate_plots()
    active_site = st.session_state.get("active_site_info")
    site_title = active_site.get("name", "当前工程") if active_site else "基准示范工程"
    total_area = sum(float(p.get("area_ha", 0)) for p in cand_plots)

    st.markdown(f"""
    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 10px; padding: 12px 18px; margin: 16px 0;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="color: #38bdf8; font-size: 18px;">📍</span>
                <span style="color: #f8fafc; font-weight: 600; font-size: 14px;">当前已挂载候选地块池：【{site_title}】</span>
            </div>
            <div style="color: #94a3b8; font-size: 12px;">
                地块单元数: <span style="color: #38bdf8; font-weight: 600;">{len(cand_plots)} 个</span> ｜ 估算总规模: <span style="color: #38bdf8; font-weight: 600;">{total_area:.2f} ha</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    from src.data import DATA_CATEGORIES, check_data_exists, get_data_readiness
    readiness = get_data_readiness()
    st.metric("核心数据完备度", f"{readiness['loaded']}/{readiness['total']} 类已入库", f"必备就绪率: {readiness['required_loaded']}/{readiness['required_count']}")
    
    # 资产网格
    cols = st.columns(3)
    for idx, cat in enumerate(DATA_CATEGORIES):
        with cols[idx % 3]:
            exists = check_data_exists(cat["id"])
            status_icon = "🟢 已挂载" if exists else ("🔴 必备缺失" if cat["required"] else "⚪ 可选")
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px 16px; margin-bottom: 12px;">
                <div style="font-weight: 600; color: #f8fafc; font-size: 14px;">{cat['name']}</div>
                <div style="font-size: 12px; color: #94a3b8; margin: 4px 0;">{cat.get('description', '')}</div>
                <div style="font-size: 12px; color: {'#4ade80' if exists else '#f87171'}; font-weight: 500;">{status_icon}</div>
            </div>
            """, unsafe_allow_html=True)


def _render_wb1_datav():
    render_section_intro("全屏空间数据大屏", "沉浸式三维态势感知、POI 空间热力与全域天际线监控。", eyebrow="Datav Screen")
    from src.ui.digital_twin import render_digital_twin_map, render_skyline_hud
    render_digital_twin_map(key_suffix="wb1_datav")
    render_skyline_hud()


def main():
    render_top_nav()
    render_engine_status_alert()

    render_page_banner(
        title="全息空间诊断与数据沙盘",
        description="工作台 01：全域空间资产治理 · AHP-MPI 空间更新潜力诊断 · 3D 全息沙盘。以量化空间数据为依据，精准锁定优先更新靶向地块。",
        eyebrow="Workbench 01",
        tags=["3D 数字孪生底座", "AHP-MPI 空间潜力模型", "地块多维雷达诊断", "空间资产全生命周期"],
    )

    # 顶部双轨制地块与项目工程接入快捷折叠面板
    with st.expander("🌐 双轨制地块与工程接入 (支持随时自主上传 GeoJSON 或在线圈选新范围)", expanded=st.session_state.get("show_ingestion_panel", False)):
        render_site_ingestion_panel()

    selected = render_workbench_subnav(
        options=WB1_OPTIONS,
        option_to_param=WB1_OPTION_TO_PARAM,
        param_to_option=WB1_PARAM_TO_OPTION,
        default_sub="diagnosis",
        widget_key="wb1_sub_nav",
    )

    # 按需条件渲染 (Lazy Rendering) + 嵌入模式防嵌套保护
    try:
        st.session_state["_embedded_mode"] = True
        if selected == WB1_OPTIONS[0]:
            render_stage04_page()
        elif selected == WB1_OPTIONS[1]:
            _render_wb1_assets()
        elif selected == WB1_OPTIONS[2]:
            _render_wb1_datav()
    finally:
        st.session_state["_embedded_mode"] = False


if __name__ == "__main__":
    main()
