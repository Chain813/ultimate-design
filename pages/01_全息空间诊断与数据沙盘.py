"""工作台 1：全息空间诊断与数据沙盘 (Data & Diagnosis Workbench)

聚合模块：
1. 3D 现状空间底座与问题诊断 (原 Stage 04 + 数据大屏)
2. AHP-MPI 空间潜力诊断与地块雷达 (原 Stage 05)
3. 多源空间资产与现场调研档案 (原 Stage 00 + 02)
"""

import streamlit as st

st.set_page_config(page_title="01 全息空间诊断与数据沙盘", layout="wide", initial_sidebar_state="collapsed")

from src.ui.app_shell import render_engine_status_alert, render_logic_chain_stepper, render_top_nav
from src.ui.design_system import render_page_banner, render_section_intro
from src.stages.stage04_diagnosis.page import render_page as render_stage04_page

def main():
    render_top_nav()
    render_engine_status_alert()

    render_page_banner(
        title="全息空间诊断与数据沙盘",
        description="工作台 01：全域空间资产治理 · AHP-MPI 空间更新潜力诊断 · 3D 全息沙盘。以量化空间数据为依据，精准锁定优先更新靶向地块。",
        eyebrow="Workbench 01",
        tags=["3D 数字孪生底座", "AHP-MPI 空间潜力模型", "地块多维雷达诊断", "空间资产全生命周期"],
    )

    # 工作台内一级分流 Tab
    tab_diag, tab_assets, tab_datav = st.tabs([
        "🏢 空间诊断与 AHP-MPI 潜力沙盘",
        "📦 多源空间资产与调研资料",
        "🖥️ 全屏空间监控大屏",
    ])

    with tab_diag:
        # 直接调用成熟的 Stage 04-05 深度工作区（含 3D 现状、MPI 测度、雷达诊断与 AI 报告）
        render_stage04_page()

    with tab_assets:
        render_section_intro("多源空间数据资产与现场调研", "查看规划红线、建筑底模、街景采样点及政策法规库等底层支撑资料。", eyebrow="Spatial Assets")
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

    with tab_datav:
        render_section_intro("全屏空间数据大屏", "沉浸式三维态势感知、POI 空间热力与全域天际线监控。", eyebrow="Datav Screen")
        from src.ui.digital_twin import render_digital_twin_map, render_skyline_hud
        render_digital_twin_map(key_suffix="wb1_datav")
        render_skyline_hud()

if __name__ == "__main__":
    main()
