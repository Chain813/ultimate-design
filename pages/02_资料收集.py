"""阶段 02：资料收集 —— 语义萃取引擎 + 空间数据资产清单 + 物理底座管理。"""

import json
import tempfile
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st
from markitdown import MarkItDown

from src.config import DATA_FILES, DOCS_DIR, META_DIR, SHP_FILES
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav
from src.ui.module_summary import render_stage_summary
from src.workflow.stage_data_bus import save_stage_output, render_evidence_chain_bar
from src.utils.text_io import read_text_with_fallback

st.set_page_config(page_title="02 资料收集", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

render_page_banner(
    title="资料收集",
    description="汇总空间数据资产、策略语义萃取和物理底座管理，确保数据基础完备。",
    eyebrow="Stage 02",
    tags=["空间数据资产", "语义萃取", "数据完备度"],
)
render_evidence_chain_bar("02", ["01", "02", "03", "04", "05"])

SUB_OPTIONS = ["📑 语义萃取引擎", "⚙️ 空间数据资产管理"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

if selected_sub == "📑 语义萃取引擎":
    render_section_intro("语义萃取引擎", "批量上传规划文档，转为可检索和引用的结构化文本。", eyebrow="MarkItDown")
    up_files = st.file_uploader("上传规划文档 (PDF/Word/PPT)", accept_multiple_files=True)
    if up_files and st.button("🚀 启动语义萃取", type="primary", use_container_width=True):
        res_list = []
        progress = st.progress(0)
        md_engine = MarkItDown()
        for idx, upload in enumerate(up_files):
            suffix = Path(upload.name).suffix or ".tmp"
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
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    save_stage_output("02", "data_completeness", f"{total_loaded}/{len(inventory)}")

st.markdown("---")
render_stage_summary(
    stage_code="02",
    title="数据资产完备度评估",
    findings=[
        {"point": "空间数据资产完备度评估完成", "evidence": "涵盖边界、地块、建筑、POI、交通、街景、情绪语料七类数据"},
        {"point": "语义萃取引擎支持 PDF/Word/PPT 批量转换", "evidence": "基于 MarkItDown 引擎"},
    ],
    methodology="基于数据资产清单的逐项核验",
    implication="为现场调研（Stage 03）和现状分析（Stage 04）提供了完备的数据基础",
)
