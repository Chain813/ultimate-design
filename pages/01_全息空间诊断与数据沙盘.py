"""工作台 1：全息空间诊断与数据沙盘 (Data & Diagnosis Workbench)

聚合模块：
1. 3D 现状空间底座与问题诊断 (原 Stage 04 + 数据大屏)
2. AHP-MPI 空间潜力诊断与地块雷达 (原 Stage 05)
3. 多源空间资产与现场调研档案 (原 Stage 00 + 02)
4. 双轨制空间地块自主接入引擎 (GeoJSON 上传 / 在线圈选 OSM 抓取)
"""

from pathlib import Path
import zipfile

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

    # 双轨接入引擎常驻嵌入 (无多余 title 关键字参数，防止 TypeError)
    render_site_ingestion_panel()

    # 动态显示已挂载的候选地块资产
    cand_plots = get_active_candidate_plots()
    active_site = st.session_state.get("active_site_info") or st.session_state.get("custom_site_context")
    site_title = active_site.get("name", "当前工程") if active_site else "基准示范工程"
    total_area = sum(float(p.get("area_ha", 0)) for p in cand_plots)

    st.markdown(f"""
    <div style="background: #ffffff; border: 1px solid rgba(0, 113, 227, 0.2); box-shadow: 0 2px 8px rgba(0, 113, 227, 0.05); border-radius: 10px; padding: 12px 18px; margin: 16px 0;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="color: #0071e3; font-size: 18px;">📍</span>
                <span style="color: #515154; font-weight: 600; font-size: 14px;">当前已挂载候选地块池：</span>
                <span style="color: #0071e3; font-weight: 700; font-size: 13px; background: rgba(0, 113, 227, 0.08); border: 1px solid rgba(0, 113, 227, 0.2); padding: 2px 10px; border-radius: 6px;">{site_title}</span>
            </div>
            <div style="color: #515154; font-size: 12px;">
                地块单元数: <span style="color: #1d1d1f; font-weight: 600;">{len(cand_plots)} 个</span> ｜ 估算总规模: <span style="color: #0071e3; font-weight: 600;">{total_area:.2f} ha</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    from src.data import DATA_CATEGORIES, check_data_exists, get_data_readiness, get_data_size
    readiness = get_data_readiness()
    st.metric("核心数据完备度", f"{readiness['loaded']}/{readiness['total']} 类已入库", f"必备就绪率: {readiness['required_loaded']}/{readiness['required_count']}")
    
    # 资产网格
    cols = st.columns(3)
    for idx, cat in enumerate(DATA_CATEGORIES):
        with cols[idx % 3]:
            exists = check_data_exists(cat["id"])
            status_icon = "🟢 已挂载" if exists else ("🔴 必备缺失" if cat["required"] else "⚪ 可选")
            badge_color = "#047857" if exists else ("#b91c1c" if cat["required"] else "#515154")
            badge_bg = "#ecfdf5" if exists else ("#fef2f2" if cat["required"] else "#f5f5f7")
            badge_border = "#a7f3d0" if exists else ("#fecaca" if cat["required"] else "#e5e5ea")
            cat_title = cat.get("title") or cat.get("name", "")
            cat_icon = cat.get("icon", "📄")
            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid rgba(0, 0, 0, 0.08); box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02); border-radius: 12px; padding: 14px 16px; margin-bottom: 12px;">
                <div style="font-weight: 600; color: #1d1d1f; font-size: 14px;">{cat_icon} {cat_title}</div>
                <div style="font-size: 12px; color: #515154; margin: 4px 0 8px 0;">{cat.get('description', '')}</div>
                <span style="display: inline-block; font-size: 11.5px; color: {badge_color}; background: {badge_bg}; border: 1px solid {badge_border}; padding: 2px 8px; border-radius: 6px; font-weight: 600;">{status_icon} ({get_data_size(cat['id'])})</span>
            </div>
            """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════
    # 📤 16 类专项数据与调研资料逐项上传/替换
    # ═══════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📤 16 类专项数据与调研资料逐项上传/替换")
    st.caption("支持全球任意城市与自选课题场地的数据直传替换，无经纬度地域范围硬编码限制，上传后自动刷新全局空间缓存。")

    cat_map = {
        f"{c.get('icon', '📄')} {c.get('title') or c.get('name', '')} ({'必备' if c.get('required') else '可选'})": c
        for c in DATA_CATEGORIES
    }
    selected_cat_label = st.selectbox(
        "选择要上传或替换的数据类别：",
        list(cat_map.keys()),
        key="wb1_cat_select",
    )
    sel_cat = cat_map[selected_cat_label]
    target_path = Path(sel_cat["target_path"])
    accept_exts = [ext.lstrip(".") for ext in sel_cat.get("accept", [])]

    col_u1, col_u2 = st.columns([1.2, 1.0])
    with col_u1:
        st.info(
            f"**目标存储路径**：`{target_path}`\n\n"
            f"**格式规范**：{sel_cat.get('format_desc', '标准格式')}\n\n"
            f"**说明**：{sel_cat.get('description', '')}"
        )
        tut = sel_cat.get("tutorial", {})
        if tut:
            with st.expander("📖 查看该类数据获取与制备教程", expanded=False):
                st.markdown(f"**概要**：{tut.get('summary', '')}")
                if tut.get("sample_fields"):
                    st.caption(f"字段示例：{tut['sample_fields']}")
                for m in tut.get("methods", []):
                    st.markdown(f"**{m.get('name', '')}**")
                    for step in m.get("steps", []):
                        st.markdown(f"- {step}")

    with col_u2:
        uploaded_cat_file = st.file_uploader(
            f"上传【{sel_cat.get('title') or sel_cat.get('name', '')}】数据文件",
            type=accept_exts if accept_exts else None,
            key=f"wb1_cat_uploader_{sel_cat['id']}",
        )
        if uploaded_cat_file is not None:
            if st.button(
                f"💾 确认写入并替换【{sel_cat.get('title') or sel_cat.get('name', '')}】",
                type="primary",
                key=f"wb1_cat_save_btn_{sel_cat['id']}",
                **stretch_width(st.button),
            ):
                try:
                    raw_bytes = uploaded_cat_file.getvalue()
                    if target_path.suffix == "":
                        # 目录型资产（如街景照片或历史影像）
                        target_path.mkdir(parents=True, exist_ok=True)
                        if uploaded_cat_file.name.lower().endswith(".zip"):
                            import io
                            with zipfile.ZipFile(io.BytesIO(raw_bytes), "r") as zf:
                                zf.extractall(target_path)
                        else:
                            out_file = target_path / uploaded_cat_file.name
                            out_file.write_bytes(raw_bytes)
                    else:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        target_path.write_bytes(raw_bytes)
                    st.cache_data.clear()
                    st.success(f"✅ 已成功保存至 `{target_path}` 并清理全局数据缓存！")
                except Exception as exc:
                    st.error(f"❌ 文件写入失败：{exc}")


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

    selected = render_workbench_subnav(
        options=WB1_OPTIONS,
        option_to_param=WB1_OPTION_TO_PARAM,
        param_to_option=WB1_PARAM_TO_OPTION,
        default_sub="diagnosis",
        widget_key="wb1_sub_nav",
    )

    # 仅在非「多源空间资产与调研资料」标签页时渲染顶部折叠面板，防止与 _render_wb1_assets 内部面板产生 DuplicateWidgetID 冲突
    if selected != WB1_OPTIONS[1]:
        with st.expander("🌐 双轨制地块与工程接入 (支持随时自主上传 GeoJSON 或在线圈选新范围)", expanded=st.session_state.get("show_ingestion_panel", False)):
            render_site_ingestion_panel()

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
