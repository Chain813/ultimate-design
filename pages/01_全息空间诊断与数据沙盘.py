"""工作台 1：全息空间诊断与数据沙盘 (Data & Diagnosis Workbench)

聚合模块：
1. 3D 现状空间底座与问题诊断 (原 Stage 04 + 数据大屏)
2. AHP-MPI 空间潜力诊断与地块雷达 (原 Stage 05)
3. 多源空间资产与现场调研档案 (原 Stage 00 + 02)
4. 双轨制空间地块自主接入引擎 (GeoJSON 上传 / 在线圈选 OSM 抓取)
"""

from pathlib import Path
import json
import logging
import tempfile
import zipfile

import pandas as pd
import streamlit as st

st.set_page_config(page_title="01 全息空间诊断与数据沙盘", layout="wide", initial_sidebar_state="collapsed")

from src.config import CSV_DIR, STREETVIEW_DIR, resolve_path
from src.ui.app_shell import render_engine_status_alert, render_top_nav
from src.ui.design_system import (
    render_page_banner,
    render_section_intro,
    render_workbench_subnav,
)
from src.stages.stage04_diagnosis.page import render_page as render_stage04_page
from src.ui.site_ingestion_panel import get_active_candidate_plots, render_site_ingestion_panel
from src.ui.streamlit_compat import stretch_width
from src.workflow.stage_data_bus import load_stage_output, save_stage_output


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

    # ═══════════════════════════════════════════════════════════════
    # 🛠️ 资料治理、语义萃取与现场街景核验工具
    # ═══════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 🛠️ 资料治理、语义萃取与现场街景核验工具")
    st.caption("在同一工作台内完成规划任务书语义萃取、16 类数据在线质量体检及街景采样点实景巡检。")

    with st.expander("📑 规划文档语义萃取引擎 (PDF / Word / PPT → Markdown)", expanded=False):
        if "extraction_res" not in st.session_state:
            st.session_state["extraction_res"] = load_stage_output("02", "extraction_res", [])
        st.caption("批量上传规划任务书、上位规划或调研文档，提取为结构化 Markdown 文本供后续阶段引用。")
        up_docs = st.file_uploader(
            "上传规划文档 (PDF / Word / PPT / TXT / MD)",
            type=["pdf", "docx", "doc", "pptx", "ppt", "txt", "md"],
            accept_multiple_files=True,
            key="wb1_semantic_extract_uploader",
        )
        if up_docs and st.button("🚀 启动语义萃取", type="primary", key="wb1_semantic_extract_btn", **stretch_width(st.button)):
            from markitdown import MarkItDown

            res_list = []
            progress = st.progress(0)
            md_engine = MarkItDown()
            for idx, upload in enumerate(up_docs):
                suffix = Path(upload.name).suffix or ".tmp"
                temp_path = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(upload.getbuffer())
                        temp_path = Path(tmp.name)
                    converted = md_engine.convert(str(temp_path))
                    res_list.append({"file": upload.name, "text": converted.text_content})
                except Exception as exc:
                    res_list.append({"file": upload.name, "text": f"Error: {exc}"})
                finally:
                    if temp_path and temp_path.exists():
                        temp_path.unlink()
                progress.progress((idx + 1) / len(up_docs))
            st.session_state["extraction_res"] = res_list
            save_stage_output("02", "extraction_res", res_list)
            save_stage_output("02", "extracted_docs", len(res_list))
            st.success(f"✅ 已完成 {len(res_list)} 份规划文档语义萃取并同步写入数据总线。")

        extract_results = st.session_state.get("extraction_res", [])
        if extract_results:
            sel_options = [r.get("file", f"文档_{i+1}") for i, r in enumerate(extract_results)]
            sel_file = st.selectbox("选择预览萃取文本", sel_options, key="wb1_extract_preview_select")
            selected_text = next((r.get("text", "") for r in extract_results if r.get("file") == sel_file), "")
            st.text_area("Markdown 结构化文本预览", value=selected_text, height=320, key="wb1_extract_preview_area")
            st.download_button(
                "📥 下载萃取结果 (.md)",
                selected_text.encode("utf-8"),
                file_name=f"{Path(sel_file).stem}_extracted.md",
                mime="text/markdown",
                key="wb1_extract_download_btn",
                **stretch_width(st.download_button),
            )
        else:
            st.info("💡 暂无萃取文本，可在此上传 PDF/Word/PPT 文档后点击「启动语义萃取」。")

    with st.expander("🔍 16 类空间与业务数据在线质量体检", expanded=False):
        st.caption("检查已挂载数据的完整性、必填字段与 WGS-84 全球合法经纬度范围（无城市预设偏置）。")
        if st.button("🔍 开始全面检查", type="primary", key="wb1_quality_check_btn", **stretch_width(st.button)):
            q_results = run_assets_quality_check()
            df_q = pd.DataFrame(q_results)
            uploaded_count = sum(1 for r in q_results if r["状态"] == "已上传")
            issue_count = sum(1 for r in q_results if r["问题数"] > 0)

            qc1, qc2, qc3 = st.columns(3)
            qc1.metric("已上传类别", f"{uploaded_count}/{len(q_results)}")
            qc2.metric("存在问题数", f"{issue_count}")
            qc3.metric("数据完备度", f"{uploaded_count / max(1, len(q_results)) * 100:.0f}%")

            st.dataframe(df_q, hide_index=True, **stretch_width(st.dataframe))
            save_stage_output("00", "data_quality_check", {
                "total": len(q_results),
                "uploaded": uploaded_count,
                "issues": issue_count,
                "details": q_results,
            })

            missing_cats = [r["类别"] for r in q_results if r["状态"] == "未上传"]
            if missing_cats:
                st.warning(f"以下类别尚未上传：{', '.join(missing_cats)}")
            if issue_count > 0:
                st.error(f"共检测到 {issue_count} 类数据存在质量问题，请核查详情列修复。")
            if uploaded_count == len(q_results) and issue_count == 0:
                st.success("✅ 全部 16 类数据均已就绪且通过 A 级质量体检！")

    with st.expander("📍 街景采样点 4 方向实景巡检 (0° / 90° / 180° / 270°)", expanded=False):
        _render_streetview_inspection_panel()


def run_assets_quality_check() -> list[dict]:
    """对 DATA_CATEGORIES 定义的 16 类空间与业务数据执行通用质量体检（支持全球任意 WGS-84 坐标）。"""
    from src.data import DATA_CATEGORIES

    results: list[dict] = []
    for cat in DATA_CATEGORIES:
        target = Path(cat["target_path"])
        status = "未上传"
        issues: list[str] = []
        record_count = 0

        has_data = target.is_dir() and any(target.iterdir()) if target.exists() and target.is_dir() else target.exists()
        if has_data:
            status = "已上传"
            if target.suffix.lower() == ".csv":
                try:
                    df = pd.read_csv(target)
                    record_count = len(df)
                    field_map = {
                        "poi": ["Name", "Lat", "Lng"],
                        "traffic": ["Name", "Type", "Lat", "Lng"],
                        "gvi": ["ID", "GVI", "SVF", "Enclosure", "Clutter"],
                    }
                    if cat["id"] in field_map:
                        missing = [c for c in field_map[cat["id"]] if c not in df.columns]
                        if missing:
                            issues.append(f"缺少字段: {', '.join(missing)}")

                    null_cols = df.columns[df.isnull().any()].tolist()
                    if null_cols:
                        issues.append(f"含空值字段: {', '.join(null_cols)}")

                    if "Lat" in df.columns and "Lng" in df.columns:
                        lats = pd.to_numeric(df["Lat"], errors="coerce")
                        lngs = pd.to_numeric(df["Lng"], errors="coerce")
                        out_lat = int(((lats < -90.0) | (lats > 90.0)).sum())
                        out_lng = int(((lngs < -180.0) | (lngs > 180.0)).sum())
                        if out_lat > 0:
                            issues.append(f"{out_lat} 条记录纬度超出 WGS-84 合法范围 [-90, 90]")
                        if out_lng > 0:
                            issues.append(f"{out_lng} 条记录经度超出 WGS-84 合法范围 [-180, 180]")
                except Exception as exc:
                    issues.append(f"CSV 解析错误: {str(exc)[:60]}")

            elif target.suffix.lower() in (".json", ".geojson"):
                try:
                    data = json.loads(target.read_text(encoding="utf-8"))
                    if isinstance(data, dict) and "features" in data:
                        record_count = len(data["features"])
                        if data.get("type") != "FeatureCollection":
                            issues.append("GeoJSON 类型不是 FeatureCollection")
                    elif isinstance(data, dict):
                        record_count = len(data)
                except Exception as exc:
                    issues.append(f"JSON 解析错误: {str(exc)[:60]}")

            elif target.is_dir():
                point_dirs = [d for d in target.iterdir() if d.is_dir()]
                record_count = len(point_dirs)
                for pd_dir in point_dirs[:5]:
                    jpg_count = len(list(pd_dir.glob("*.jpg")))
                    if jpg_count < 4:
                        issues.append(f"{pd_dir.name} 仅有 {jpg_count} 张照片 (应为 4 张)")

        if status == "未上传":
            quality_score = "待上传"
        else:
            quality_score = "A" if not issues else ("B" if len(issues) <= 2 else "C")

        results.append({
            "类别": f"{cat.get('icon', '📄')} {cat.get('title') or cat.get('name', '')}",
            "状态": status,
            "记录数": record_count,
            "问题数": len(issues),
            "质量评级": quality_score,
            "详情": "; ".join(issues) if issues else ("尚未上传" if status == "未上传" else "无问题"),
        })

    return results


def _find_streetview_points_csv(csv_dir: Path) -> Path | None:
    """定位含 ID/Lat/Lng 列的街景采样点坐标 CSV 文件。"""
    preferred = csv_dir / "Changchun_Precise_Points.csv"
    if preferred.exists():
        return preferred
    if csv_dir.exists():
        for cand in sorted(csv_dir.glob("*.csv")):
            try:
                cols = set(pd.read_csv(cand, nrows=0).columns)
                if {"ID", "Lat", "Lng"}.issubset(cols):
                    return cand
            except Exception:
                continue
    return None


def _render_streetview_inspection_panel() -> None:
    """渲染街景采样点 2D 地图与 0°/90°/180°/270° 四方向实景巡检。"""
    sv_root = resolve_path(str(STREETVIEW_DIR))
    csv_path = _find_streetview_points_csv(resolve_path(str(CSV_DIR)))

    available_ids: list[int] = []
    if sv_root.exists():
        for d in sv_root.iterdir():
            if d.is_dir() and d.name.startswith("Point_"):
                try:
                    available_ids.append(int(d.name.split("_")[1]))
                except (IndexError, ValueError):
                    continue

    if not csv_path or not available_ids:
        st.markdown(
            """<div style="background:#f5f5f7; border:1px solid rgba(0,0,0,0.08); border-radius:10px; padding:14px 16px; color:#515154; font-size:13px;">
            💡 当前场地尚未挂载四方向街景样本库（需在上方「16 类专项数据上传」中补充街景照片压缩包与采样点坐标 CSV 后启用交互巡检）。
            </div>""",
            unsafe_allow_html=True,
        )
        return

    try:
        df_all = pd.read_csv(csv_path)
        df_all["ID"] = df_all["ID"].astype(int)
        df_points = df_all[df_all["ID"].isin(available_ids)].copy()
        df_points["name"] = df_points["ID"].apply(lambda x: f"Point_{x}")
    except Exception as exc:
        st.warning(f"街景采样点坐标表解析失败：{exc}")
        return

    if df_points.empty:
        st.info("采样点坐标表与本地街景目录无交集点位。")
        return

    valid_ids = [int(x) for x in df_points["ID"].tolist()]
    saved_pid = load_stage_output("03", "selected_point_id", valid_ids[0])
    if "selected_point_id" not in st.session_state or st.session_state.selected_point_id not in valid_ids:
        st.session_state.selected_point_id = saved_pid if saved_pid in valid_ids else valid_ids[0]

    col_title, col_nav = st.columns([2, 1])
    with col_title:
        st.markdown("#### 2D 街区采样点分布图 (Apple HIG Light)")
        st.caption("🔍 点击地图点位或使用右侧下拉快捷跳转，下方自动联动 4 方向街景实拍")
    with col_nav:
        cur_idx = valid_ids.index(st.session_state.selected_point_id) if st.session_state.selected_point_id in valid_ids else 0
        selected_id_nav = st.selectbox(
            "采样点快捷跳转",
            valid_ids,
            format_func=lambda x: f"Point_{x}",
            index=cur_idx,
            label_visibility="collapsed",
            key="wb1_sv_point_select",
        )
        if selected_id_nav != st.session_state.selected_point_id:
            st.session_state.selected_point_id = selected_id_nav
            save_stage_output("03", "selected_point_id", selected_id_nav)

    import plotly.graph_objects as go

    colors = ["#ef4444" if pid == st.session_state.selected_point_id else "#0071e3" for pid in df_points["ID"]]
    sizes = [16 if pid == st.session_state.selected_point_id else 9 for pid in df_points["ID"]]
    fig = go.Figure()
    fig.add_trace(
        go.Scattermapbox(
            lon=df_points["Lng"],
            lat=df_points["Lat"],
            mode="markers",
            marker=dict(size=sizes, color=colors, opacity=0.9),
            text=df_points["name"],
            hoverinfo="text",
            customdata=df_points["ID"],
        )
    )
    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=dict(lat=float(df_points["Lat"].mean()), lon=float(df_points["Lng"].mean())),
            zoom=13.5,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=360,
        showlegend=False,
        dragmode="pan",
    )
    event_data = st.plotly_chart(
        fig,
        on_select="rerun",
        config={"displayModeBar": False, "scrollZoom": True},
        key="wb1_sv_mapbox_chart",
        **stretch_width(st.plotly_chart),
    )
    if event_data and "selection" in event_data and event_data["selection"].get("points"):
        try:
            p_idx = event_data["selection"]["points"][0]["point_index"]
            new_id = int(df_points.iloc[p_idx]["ID"])
            if new_id != st.session_state.selected_point_id:
                st.session_state.selected_point_id = new_id
                save_stage_output("03", "selected_point_id", new_id)
        except Exception:
            logging.debug("街景图点选解析跳过", exc_info=True)

    cur_id = st.session_state.selected_point_id
    cur_name = f"Point_{cur_id}"
    p_path = sv_root / cur_name
    img_cols = st.columns(4)
    for i, heading in enumerate((0, 90, 180, 270)):
        with img_cols[i]:
            i_path = p_path / f"heading_{heading}.jpg"
            if i_path.exists():
                st.image(str(i_path), caption=f"{cur_name} · {heading}°", **stretch_width(st.image))
            else:
                st.caption(f"缺少 {heading}° 图像")
    save_stage_output("03", "survey_points", len(df_points))
    save_stage_output("03", "current_view", cur_name)


def _render_wb1_datav():
    render_section_intro("全屏空间数据大屏", "sc-datav 沉浸式全域态势监控看板与轻量 3D 交互沙盘双模切换。", eyebrow="Datav Screen")
    from src.ui.digital_twin import render_datav_bigscreen, render_digital_twin_map, render_skyline_hud

    mode = st.radio(
        "大屏视图模式",
        ["🖥️ sc-datav 综合态势大屏", "🏙️ 轻量 3D 交互沙盘"],
        index=0,
        horizontal=True,
        key="wb1_datav_mode",
        label_visibility="collapsed",
    )
    if mode.startswith("🖥️"):
        render_datav_bigscreen()
    else:
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
