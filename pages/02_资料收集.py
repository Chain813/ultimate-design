"""阶段 02：资料收集 —— 语义萃取引擎 + 空间数据资产清单 + 物理底座管理。"""

import json
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st
from markitdown import MarkItDown

from src.config import DATA_FILES, SHP_FILES
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav
from src.ui.module_summary import render_stage_summary
from src.ui.output_flow_panel import render_output_flow_prompt_panel
from src.ui.streamlit_compat import stretch_width
from src.workflow.stage_data_bus import save_stage_output, render_evidence_chain_bar
from src.workflow.template_assets import (
    get_template_asset_rows,
    get_template_asset_specs,
    get_uploaded_prompt_channels,
    load_template_asset_manifest,
    remove_template_asset,
    save_template_asset,
    summarize_template_assets_for_prompt,
)

st.set_page_config(page_title="02 资料收集", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

render_page_banner(
    title="资料收集",
    description="汇总空间数据资产、策略语义萃取和物理底座管理，确保数据基础完备。",
    eyebrow="Stage 02",
    tags=["空间数据资产", "语义萃取", "数据完备度"],
)
render_evidence_chain_bar("02", ["01", "02", "03", "04", "05"])

SUB_OPTIONS = ["📑 语义萃取引擎", "⚙️ 空间数据资产管理", "🧩 固定制图模板"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

if selected_sub == "📑 语义萃取引擎":
    render_section_intro("语义萃取引擎", "批量上传规划文档，转为可检索和引用的结构化文本。", eyebrow="MarkItDown")
    up_files = st.file_uploader("上传规划文档 (PDF/Word/PPT)", accept_multiple_files=True)
    if up_files and st.button("🚀 启动语义萃取", type="primary", **stretch_width(st.button)):
        res_list = []
        progress = st.progress(0)
        md_engine = MarkItDown()
        for idx, upload in enumerate(up_files):
            suffix = Path(upload.name).suffix or ".tmp"
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(upload.getbuffer())
                    temp_path = Path(tmp.name)
                res = md_engine.convert(str(temp_path))
                res_list.append({"file": upload.name, "text": res.text_content})
            except Exception as exc:
                res_list.append({"file": upload.name, "text": f"Error: {exc}"})
            finally:
                if temp_path and temp_path.exists():
                    temp_path.unlink()
            progress.progress((idx + 1) / len(up_files))
        st.session_state["extraction_res"] = res_list
        save_stage_output("02", "extracted_docs", len(res_list))
        st.success("语义萃取完成。")

    if "extraction_res" in st.session_state:
        results = st.session_state["extraction_res"]
        sel_file = st.selectbox("选择预览", [r["file"] for r in results])
        selected_text = next(r["text"] for r in results if r["file"] == sel_file)
        st.text_area("Markdown 预览", value=selected_text, height=420)

elif selected_sub == "⚙️ 空间数据资产管理":
    render_section_intro("空间数据资产台", "核对底座文件、查看数据挂载情况。", eyebrow="Spatial Assets")

    def _count(path):
        if not path.exists():
            return 0
        try:
            if str(path).endswith(".csv"):
                return len(pd.read_csv(path))
            return len(json.loads(path.read_text(encoding="utf-8")).get("features", []))
        except Exception:
            return 0

    inventory = [
        {"name": "规划边界", "path": SHP_FILES["boundary"], "count": _count(SHP_FILES["boundary"])},
        {"name": "重点更新单元", "path": SHP_FILES["plots"], "count": _count(SHP_FILES["plots"])},
        {"name": "建筑底图", "path": SHP_FILES["buildings"], "count": _count(SHP_FILES["buildings"])},
        {"name": "POI 数据", "path": DATA_FILES["poi"], "count": _count(DATA_FILES["poi"])},
        {"name": "交通数据", "path": DATA_FILES["traffic"], "count": _count(DATA_FILES["traffic"])},
        {"name": "街景分析", "path": DATA_FILES["gvi"], "count": _count(DATA_FILES["gvi"])},
        {"name": "情绪语料", "path": DATA_FILES["nlp"], "count": _count(DATA_FILES["nlp"])},
    ]
    total_loaded = sum(1 for i in inventory if i["count"] > 0)
    render_summary_cards([
        {"value": f"{total_loaded}/{len(inventory)}", "title": "已挂载数据集", "desc": "空间数据完备度"},
        {"value": sum(i["count"] for i in inventory), "title": "总记录数", "desc": "全部数据集记录合计"},
    ])

    rows = [{"数据集": i["name"], "记录数": i["count"], "状态": "✅ 已挂载" if i["count"] > 0 else "❌ 缺失"} for i in inventory]
    st.dataframe(pd.DataFrame(rows), hide_index=True, **stretch_width(st.dataframe))
    save_stage_output("02", "data_completeness", f"{total_loaded}/{len(inventory)}")

elif selected_sub == "🧩 固定制图模板":
    render_section_intro(
        "固定底图、范围、地块与图框",
        "提前上传不会被 AI 改写的制图资产，后续 Image 2.0 / SD 只生成分析覆盖层。",
        eyebrow="Locked Drawing Assets",
    )

    manifest = load_template_asset_manifest()
    rows = get_template_asset_rows(manifest)
    uploaded_count = sum(1 for row in rows if row["状态"] == "已上传")
    required_rows = [row for row in rows if row["必备"] == "是"]
    required_ready = sum(1 for row in required_rows if row["状态"] == "已上传")
    render_summary_cards(
        [
            {"value": f"{required_ready}/{len(required_rows)}", "title": "必备固定资产", "desc": "底图、红线、地块、图框"},
            {"value": f"{uploaded_count}/{len(rows)}", "title": "已上传通道", "desc": "可注入提示词的制图资产"},
        ]
    )

    with st.expander("前期需要提前准备哪些图", expanded=True):
        st.markdown(
            """
**必备四类**

1. 固定底图 / 正射影像：统一裁切后的卫星图、航拍图或无纹理 2D 底图。
2. 研究范围红线 / Mask：研究范围边界，优先 GeoJSON / SVG，其次透明 PNG 或黑白 mask。
3. 重点地块边界 / Mask：五个重点地块或重点更新单元边界，最好和研究范围使用同一坐标或同一图框。
4. 固定图框 / 出图版式：A3/A1/PPT 图框、标题栏、图例区、比例尺、指北针和安全边距。

**建议补充**

- 建筑肌理 / 建筑轮廓：用于总平面、建筑高度、风貌控制等图纸。
- 道路矢量 / 交通底图：用于道路交通、慢行、TOD、可达性分析。
- GIS 专题底图 / 用地图：用于用地现状、控规、更新潜力、生态或公共空间专题。
- 图例 / 色彩 / 风格参考：统一图册色彩、符号和版式气质。
            """
        )

    st.dataframe(pd.DataFrame(rows), hide_index=True, **stretch_width(st.dataframe))

    st.markdown("#### 上传入口")
    for spec in get_template_asset_specs():
        existing = manifest.get("assets", {}).get(spec.asset_id)
        status = "已上传" if existing else ("必备" if spec.required else "建议")
        with st.expander(f"{status} · {spec.label}", expanded=spec.required and not existing):
            st.caption(spec.description)
            st.caption(f"生成约束：{spec.generation_rule}")
            if existing:
                st.success(
                    f"当前文件：{existing.get('original_name', existing.get('filename', ''))} "
                    f"({existing.get('size_bytes', 0) / 1024:.1f} KB)"
                )
                if existing.get("note"):
                    st.caption(f"备注：{existing['note']}")

            upload = st.file_uploader(
                "选择文件并覆盖当前资产",
                type=list(spec.accepted_types),
                key=f"template_asset_upload_{spec.asset_id}",
            )
            note = st.text_input("备注 / 坐标口径 / 图框说明", value=existing.get("note", "") if existing else "", key=f"template_asset_note_{spec.asset_id}")
            col_save, col_remove = st.columns(2)
            if col_save.button(
                "保存 / 覆盖",
                key=f"template_asset_save_{spec.asset_id}",
                **stretch_width(col_save.button),
            ):
                if not upload:
                    st.warning("请先选择文件。")
                else:
                    save_template_asset(spec.asset_id, upload.name, bytes(upload.getbuffer()), note=note)
                    st.success("已保存。")
                    st.rerun()
            if existing and col_remove.button(
                "移除",
                key=f"template_asset_remove_{spec.asset_id}",
                **stretch_width(col_remove.button),
            ):
                remove_template_asset(spec.asset_id)
                st.warning("已移除该资产。")
                st.rerun()

    prompt_channels = get_uploaded_prompt_channels(manifest)
    save_stage_output("02", "template_assets", prompt_channels)
    save_stage_output("02", "template_asset_context", summarize_template_assets_for_prompt(manifest))

    with st.expander("将注入到提示词中的固定约束", expanded=False):
        st.code(summarize_template_assets_for_prompt(manifest), language="text")

    render_output_flow_prompt_panel(manifest, expanded=False)

st.markdown("---")
asset_manifest = load_template_asset_manifest()
asset_rows = get_template_asset_rows(asset_manifest)
asset_ready = sum(1 for row in asset_rows if row["状态"] == "已上传")
render_stage_summary(
    stage_code="02",
    title="数据资产完备度评估",
    findings=[
        {"point": "空间数据资产完备度评估完成", "evidence": "涵盖边界、地块、建筑、POI、交通、街景、情绪语料七类数据"},
        {"point": "语义萃取引擎支持 PDF/Word/PPT 批量转换", "evidence": "基于 MarkItDown 引擎"},
        {"point": f"固定制图模板资产已配置 {asset_ready}/{len(asset_rows)} 项", "evidence": "用于锁定底图、研究范围、重点地块和图框"},
    ],
    methodology="基于数据资产清单的逐项核验",
    implication="为现场调研（Stage 03）和现状分析（Stage 04）提供了完备的数据基础",
)
