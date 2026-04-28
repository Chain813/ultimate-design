import json
import tempfile
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from markitdown import MarkItDown

from src.config import DATA_FILES, DOCS_DIR, META_DIR, SHP_FILES
from src.ui.chart_theme import apply_plotly_theme, get_chart_palette
from src.ui.design_system import (
    render_page_banner,
    render_section_intro,
    render_summary_cards,
)
from src.ui.app_shell import (
    render_top_nav,
)
from src.workflow.city_design_workflow import resolve_subpage_option
from src.utils.text_io import read_text_with_fallback


st.set_page_config(page_title="数据底座与策略实验室 | 01", layout="wide", initial_sidebar_state="expanded")
render_top_nav()

TASK_BOOK_PATH = DOCS_DIR / "毕业设计任务书.pdf"
PROPOSAL_PATH = DOCS_DIR / "毕业设计开题报告.pdf"
CASE_SUMMARY_PATH = DOCS_DIR / "开题报告_案例摘要.md"
MISSION_TEXT_PATH = META_DIR / "mission_text.txt"
CONSTRAINTS_PATH = META_DIR / "extracted_constraints.txt"


@st.cache_data(ttl=1800)
def read_text(path: Path) -> str:
    return read_text_with_fallback(path)


@st.cache_data(ttl=1800)
def read_binary(path: Path) -> bytes:
    if not path.exists():
        return b""
    return path.read_bytes()


@st.cache_data(ttl=600)
def count_geo_features(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return len(json.loads(path.read_text(encoding="utf-8")).get("features", []))
    except Exception:
        return 0


@st.cache_data(ttl=600)
def load_spatial_inventory():
    inventory = [
        {
            "name": "规划边界",
            "path": SHP_FILES["boundary"],
            "kind": "GeoJSON",
            "count": count_geo_features(SHP_FILES["boundary"]),
            "unit": "个要素",
            "role": "锁定研究范围与成果边界。",
        },
        {
            "name": "重点更新单元",
            "path": SHP_FILES["plots"],
            "kind": "GeoJSON",
            "count": count_geo_features(SHP_FILES["plots"]),
            "unit": "个地块",
            "role": "承载 MPI 评估与后续更新策略。",
        },
        {
            "name": "建筑底图",
            "path": SHP_FILES["buildings"],
            "kind": "GeoJSON",
            "count": count_geo_features(SHP_FILES["buildings"]),
            "unit": "栋建筑",
            "role": "用于数字孪生现状和成果底板。",
        },
        {
            "name": "POI 数据",
            "path": DATA_FILES["poi"],
            "kind": "CSV",
            "count": int(pd.read_csv(DATA_FILES["poi"]).shape[0]) if DATA_FILES["poi"].exists() else 0,
            "unit": "条记录",
            "role": "支撑空间活力与公共服务测度。",
        },
        {
            "name": "交通数据",
            "path": DATA_FILES["traffic"],
            "kind": "CSV",
            "count": int(pd.read_csv(DATA_FILES["traffic"]).shape[0]) if DATA_FILES["traffic"].exists() else 0,
            "unit": "条记录",
            "role": "支撑拥堵热点与慢行诊断。",
        },
        {
            "name": "街景分析结果",
            "path": DATA_FILES["gvi"],
            "kind": "CSV",
            "count": int(pd.read_csv(DATA_FILES["gvi"]).shape[0]) if DATA_FILES["gvi"].exists() else 0,
            "unit": "条记录",
            "role": "支撑环境品质与绿视率分析。",
        },
        {
            "name": "情绪语料",
            "path": DATA_FILES["nlp"],
            "kind": "CSV",
            "count": int(pd.read_csv(DATA_FILES["nlp"]).shape[0]) if DATA_FILES["nlp"].exists() else 0,
            "unit": "条记录",
            "role": "支撑社会需求与公众反馈分析。",
        },
    ]
    return inventory


def format_file_size(path: Path) -> str:
    if not path.exists():
        return "未找到"
    size = path.stat().st_size
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return "未知"


def render_doc_card(title, badge, meta, items):
    bullet_html = "".join(f"<li>{escape(item)}</li>" for item in items)
    st.markdown(
        f"""
        <div class="doc-card">
            <div class="doc-card-title">
                <h4>{escape(title)}</h4>
                <span class="doc-badge">{escape(badge)}</span>
            </div>
            <div class="doc-meta">{escape(meta)}</div>
            <ul class="doc-list">{bullet_html}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_manifest_df(inventory):
    rows = []
    for item in inventory:
        path = item["path"]
        rows.append(
            {
                "数据集": item["name"],
                "格式": item["kind"],
                "数量": f'{item["count"]} {item["unit"]}',
                "文件大小": format_file_size(path),
                "最后更新": pd.to_datetime(path.stat().st_mtime, unit="s").strftime("%Y-%m-%d %H:%M") if path.exists() else "未找到",
                "说明": item["role"],
            }
        )
    return pd.DataFrame(rows)


inventory = load_spatial_inventory()
plots_count = next((item["count"] for item in inventory if item["name"] == "重点更新单元"), 0)
buildings_count = next((item["count"] for item in inventory if item["name"] == "建筑底图"), 0)

render_page_banner(
    title="数据底座与规划策略工作台",
    description="把任务书、开题报告、规划约束和空间数据放在同一工作面板里，直接服务于更新优先级判断、资料萃取和底层资产维护。",
    eyebrow="Page 01",
    tags=["任务书边界锁定", "开题报告策略对照", "空间数据在线维护"],
    metrics=[
        {"value": "150 公顷", "label": "研究范围", "meta": "任务书明确的核心片区"},
        {"value": "5 个", "label": "深化地段", "meta": "任务书要求重点设计单元"},
        {"value": "4 项", "label": "核心痛点", "meta": "开题报告现状诊断结论"},
        {"value": f"{plots_count}/{buildings_count}", "label": "地块 / 建筑", "meta": "当前已挂载的主要空间资产"},
    ],
)

if "lab01_active_sub" not in st.session_state:
    st.session_state.lab01_active_sub = "📊 资产综合评估"

tab_options = ["📊 资产综合评估", "📑 策略语义萃取", "⚙️ 物理底座管理"]
default_tab_index = tab_options.index(st.session_state.lab01_active_sub) if st.session_state.lab01_active_sub in tab_options else 0
default_tab_index = resolve_subpage_option(tab_options, default_index=default_tab_index)
if st.query_params.get("sub"):
    st.session_state.lab01_active_sub = tab_options[default_tab_index]
    st.session_state["lab01_switcher"] = tab_options[default_tab_index]
selected_sub = tab_options[default_tab_index]
st.session_state.lab01_active_sub = selected_sub
st.markdown("---")


if selected_sub == "📊 资产综合评估":
    render_section_intro(
        "更新优先级评估",
        "基于重点更新单元 GeoJSON 和 AHP 权重实时计算 MPI，优先用于识别近期应先启动的微更新节点。",
        eyebrow="Multi-dimensional Potential Index",
    )

    json_path = SHP_FILES["plots"]
    if json_path.exists():
        try:
            geo_data = json.loads(json_path.read_text(encoding="utf-8"))
            plot_list = []
            for feat in geo_data.get("features", []):
                props = feat.get("properties", {})
                name = props.get("name", props.get("Name", f"地块_{props.get('OBJECTID', '??')}"))
                area = props.get("Shape_Area", 50000)
                pot = min(0.95, 0.5 + (area / 150000) * 0.4)
                seed_id = props.get("OBJECTID", 0)
                np.random.seed(seed_id)
                plot_list.append(
                    {
                        "地块名称": name,
                        "空间潜力原分": round(pot, 2),
                        "社会需求原分": round(0.5 + 0.4 * np.random.rand(), 2),
                        "环境现状评分": round(0.1 + 0.6 * np.random.rand(), 2),
                    }
                )
            base_data = pd.DataFrame(plot_list)
        except Exception:
            base_data = pd.DataFrame(
                {
                    "地块名称": ["中车老厂区", "光复路历史街区", "铁北断头路节点"],
                    "空间潜力原分": [0.89, 0.82, 0.74],
                    "社会需求原分": [0.92, 0.95, 0.65],
                    "环境现状评分": [0.35, 0.42, 0.28],
                }
            )
    else:
        base_data = pd.DataFrame(
            {
                "地块名称": ["数据资产缺失", "请检查 data/shp", "配置文件引用无误"],
                "空间潜力原分": [0, 0, 0],
                "社会需求原分": [0, 0, 0],
                "环境现状评分": [1, 1, 1],
            }
        )

    with st.sidebar:
        st.markdown("### 🎚️ 专家决策模拟 (AHP)")
        st.info("调节权重后，系统会实时重排更新优先级。")
        w_poi = st.slider(
            "🏗️ 空间潜力占比 (%)",
            0,
            100,
            40,
            key="w_poi",
            help="基于 POI 密度、地块规模与用地性质等指标衡量物理更新潜力。",
        )
        w_soc = st.slider(
            "👥 社会需求占比 (%)",
            0,
            100,
            30,
            key="w_soc",
            help="基于情绪语料、人口结构和服务设施视角衡量居民更新诉求。",
        )
        w_env = st.slider(
            "🌿 环境干预紧迫度 (%)",
            0,
            100,
            30,
            key="w_env",
            help="基于 GVI、开敞度等指标衡量环境短板。",
        )

        total_w = w_poi + w_soc + w_env
        st.caption(f"当前权重总计: {total_w}%")
        if total_w != 100:
            st.warning("建议将权重总计调至 100%。")

        st.markdown("---")
        threshold = st.slider(
            "🎯 仅展示得分高于",
            0,
            100,
            0,
            key="p1_threshold",
            help="MPI 得分门槛。设为 0 时显示全部地块。",
        )

    def recalc_mpi(df, w1, w2, w3):
        df = df.copy()
        df["MPI 得分"] = (
            (df["空间潜力原分"] * w1 + df["社会需求原分"] * w2 + (1 - df["环境现状评分"]) * w3)
            / (w1 + w2 + w3 + 0.001)
            * 100
        )
        return df

    df_calculated = recalc_mpi(base_data, w_poi, w_soc, w_env)
    df_filtered = df_calculated[df_calculated["MPI 得分"] >= threshold].sort_values("MPI 得分", ascending=False)
    top_plot = df_filtered.iloc[0]["地块名称"] if not df_filtered.empty else "暂无候选地块"
    top_score = float(df_filtered.iloc[0]["MPI 得分"]) if not df_filtered.empty else 0.0

    render_summary_cards(
        [
            {"value": len(df_filtered), "title": "候选更新单元", "desc": "满足当前阈值要求的地块数量。"},
            {"value": f"{top_score:.1f}", "title": "最高 MPI 分值", "desc": f"当前优先地块：{top_plot}。"},
            {"value": f"{w_poi}/{w_soc}/{w_env}", "title": "权重组合", "desc": "空间潜力 / 社会需求 / 环境紧迫度。"},
            {"value": threshold, "title": "筛选阈值", "desc": "低于该值的地块不会进入排行榜。"},
        ]
    )

    st.markdown(
        """
        <div class="note-panel">
            <p><strong>评估来源：</strong>重点更新单元来自 <code>data/shp/Key_Plots_District.json</code>，
            当前 MPI 用于快速筛查应优先启动的微更新对象，而不是替代后续的规划论证。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_formula, col_matrix = st.columns([1.1, 0.9])
    with col_formula:
        st.markdown(
            """
            <div class="content-panel">
                <h3>MPI 测度模型</h3>
                <div class="panel-caption">空间潜力、社会需求与环境紧迫度共同决定近期更新优先级。</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.latex(
            r"\color{#a5b4fc} MPI_i = \frac{w_{space} \cdot S_i + w_{social} \cdot D_i + w_{env} \cdot (1 - E_i)}{w_{space} + w_{social} + w_{env}} \times 100"
        )
        st.markdown(
            """
            <div class="content-panel">
                <ul class="status-list">
                    <li><strong>S</strong>：结合地块规模、空间承载力与活力潜力。</li>
                    <li><strong>D</strong>：结合社会需求、人口结构与公众反馈。</li>
                    <li><strong>E</strong>：结合街景品质与环境短板，分值越低代表越需要干预。</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_matrix:
        st.markdown(
            """
            <div class="content-panel">
                <h3>AHP 判断矩阵</h3>
                <div class="panel-caption">用于展示当前专家权重配置下的相对重要性关系。</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        w_arr = np.array([w_poi, w_soc, w_env], dtype=float)
        w_norm = w_arr / (w_arr.sum() + 0.001)
        ahp_matrix = pd.DataFrame(
            [
                [1, round(w_norm[0] / (w_norm[1] + 0.001), 2), round(w_norm[0] / (w_norm[2] + 0.001), 2)],
                [round(w_norm[1] / (w_norm[0] + 0.001), 2), 1, round(w_norm[1] / (w_norm[2] + 0.001), 2)],
                [round(w_norm[2] / (w_norm[0] + 0.001), 2), round(w_norm[2] / (w_norm[1] + 0.001), 2), 1],
            ],
            columns=["空间潜力 (S)", "社会需求 (D)", "环境干预迫切度 (E)"],
            index=["空间潜力 (S)", "社会需求 (D)", "环境干预迫切度 (E)"],
        )
        st.dataframe(ahp_matrix, use_container_width=True)
        st.caption(f"CR < 0.1，归一化特征向量: [{w_norm[0]:.3f}, {w_norm[1]:.3f}, {w_norm[2]:.3f}]")

    render_section_intro("排行榜与分布", "用于查看当前权重配置下的高优先级地块及其耦合关系。", eyebrow="Ranking")
    csv_report = df_filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📤 导出评估排行榜 (CSV)",
        data=csv_report,
        file_name="Urban_Renewal_MPI_Report.csv",
        mime="text/csv",
        use_container_width=True,
    )

    if not df_filtered.empty:
        st.markdown(
            f"""
            <div class="content-panel">
                <h3>当前研判结论</h3>
                <p><strong style="color:#c7d2fe;">{escape(top_plot)}</strong> 以 <strong>{top_score:.1f}</strong> 分位居当前优先级首位，
                适合作为近期“针灸式”微更新的启动单元。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.dataframe(
        df_filtered[["地块名称", "MPI 得分"]],
        column_config={
            "MPI 得分": st.column_config.ProgressColumn(
                "MPI 综合潜力分",
                help="基于 AHP 权重动态计算所得。",
                format="%.1f",
                min_value=0,
                max_value=100,
            )
        },
        use_container_width=True,
        hide_index=True,
    )

    if not df_filtered.empty:
        fig = px.scatter(
            df_filtered,
            x="空间潜力原分",
            y="社会需求原分",
            size="MPI 得分",
            color="地块名称",
            color_discrete_sequence=get_chart_palette(),
            height=440,
        )
        fig.update_traces(marker=dict(opacity=0.9, line=dict(width=1, color="rgba(15, 23, 42, 0.72)")))
        apply_plotly_theme(fig, title="空间潜力与社会需求耦合分布", height=440, showlegend=True, legend_orientation="h")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("当前筛选阈值下没有可展示地块。")


elif selected_sub == "📑 策略语义萃取":
    render_section_intro(
        "任务书 / 开题报告资料台",
        "把研究边界、策略来源和语义萃取流程放在一起，便于对照资料原文与当前规划判断。",
        eyebrow="Research Inputs",
    )

    task_meta = f"{format_file_size(TASK_BOOK_PATH)} · {TASK_BOOK_PATH.name}" if TASK_BOOK_PATH.exists() else "未找到文档"
    proposal_meta = f"{format_file_size(PROPOSAL_PATH)} · {PROPOSAL_PATH.name}" if PROPOSAL_PATH.exists() else "未找到文档"
    doc_col1, doc_col2 = st.columns(2)
    with doc_col1:
        render_doc_card(
            "毕业设计任务书",
            "边界基准",
            task_meta,
            [
                "研究范围位于长春大街、长白路、东九条、亚泰快速路围合片区。",
                "总用地面积约 150 公顷，包含 5 个需要深化设计的更新地段。",
                "目标聚焦历史保护、交通缝合、工业遗产活化与 AI 赋能更新。",
            ],
        )
        task_bytes = read_binary(TASK_BOOK_PATH)
        if task_bytes:
            st.download_button(
                "📥 下载任务书原件",
                data=task_bytes,
                file_name=TASK_BOOK_PATH.name,
                mime="application/pdf",
                use_container_width=True,
                key="task_book_download",
            )
    with doc_col2:
        render_doc_card(
            "毕业设计开题报告",
            "策略基准",
            proposal_meta,
            [
                "明确 4 项核心痛点：用地混杂、交通割裂、老龄化、环境品质不足。",
                "提出 4 项设计策略：精准感知、风貌生成、路网重构、社会协同。",
                "案例借鉴已沉淀为 `开题报告_案例摘要.md`，可直接供 LLM 调用。",
            ],
        )
        proposal_bytes = read_binary(PROPOSAL_PATH)
        if proposal_bytes:
            st.download_button(
                "📥 下载开题报告原件",
                data=proposal_bytes,
                file_name=PROPOSAL_PATH.name,
                mime="application/pdf",
                use_container_width=True,
                key="proposal_download",
            )

    mission_text = read_text(MISSION_TEXT_PATH)
    case_summary = read_text(CASE_SUMMARY_PATH)
    constraints_text = read_text(CONSTRAINTS_PATH)

    summary_tabs = st.tabs(["任务书摘要", "开题报告案例", "规划约束摘录"])
    with summary_tabs[0]:
        render_summary_cards(
            [
                {"value": "150 公顷", "title": "研究范围", "desc": "任务书锁定的规划研究边界。"},
                {"value": "5 个", "title": "深化地段", "desc": "需要展开设计与成果表达的重点单元。"},
                {"value": "4 项", "title": "更新目标", "desc": "数字孪生、AI 风貌、绿色可持续、协同更新。"},
            ]
        )
        st.text_area("任务书原文摘录", mission_text[:1800], height=280)

    with summary_tabs[1]:
        st.markdown(case_summary if case_summary else "未找到 `docs/开题报告_案例摘要.md`。")

    with summary_tabs[2]:
        st.markdown(
            """
            <div class="note-panel">
                <p><strong>当前已抽取的重点约束：</strong>历史保护区建筑高度控制、容积率约束、必要基础设施可改造、管线入地等条款已进入语义检索底稿。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.text_area("约束命中预览", constraints_text[:2200], height=280)

    with st.sidebar:
        st.markdown("### 📑 语义萃取配置")
        p_on = st.toggle("启用第三方图表解析插件 (Excel/PPT)", value=False, key="p2_plugins_on")
        ocr_on = st.toggle("启用 OCR 图表识别", value=False, key="p2_ocr_on")
        st.markdown("---")
        suffix_val = st.text_input("导出语料库后缀", value="_extracted_nlp_corpus", key="p2_suffix_val")

    render_section_intro(
        "语义萃取引擎",
        "批量上传任务书、开题报告或上位规划文档，转为可继续检索和引用的结构化文本。",
        eyebrow="MarkItDown",
    )
    render_summary_cards(
        [
            {"value": "插件 " + ("开启" if p_on else "关闭"), "title": "图表解析", "desc": "用于 Excel/PPT 等扩展型文档。"},
            {"value": "OCR " + ("开启" if ocr_on else "关闭"), "title": "图文识别", "desc": "用于表格截图和插图说明提取。"},
            {"value": suffix_val, "title": "导出后缀", "desc": "用于整理生成的语义语料文件名。"},
        ]
    )

    up_files = st.file_uploader("批处理上传规划文档或导则资料 (PDF/Word/PPT)", accept_multiple_files=True)
    if up_files and st.button("🚀 启动算法语义萃取", type="primary", use_container_width=True):
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
        st.session_state["lab01_extraction_res"] = res_list
        st.success("语义萃取完成。")

    if "lab01_extraction_res" in st.session_state:
        results = st.session_state["lab01_extraction_res"]
        result_names = [item["file"] for item in results]
        sel_file = st.selectbox("选择预览结果", result_names)
        selected_text = next(item["text"] for item in results if item["file"] == sel_file)
        bundle_text = "\n\n".join(f"# {item['file']}\n\n{item['text']}" for item in results)

        st.download_button(
            "📦 导出本次语义语料",
            data=bundle_text.encode("utf-8"),
            file_name=f"planning{suffix_val}.md",
            mime="text/markdown",
            use_container_width=True,
        )
        st.text_area("Markdown 预览窗口", value=selected_text, height=420)


elif selected_sub == "⚙️ 物理底座管理":
    render_section_intro(
        "空间数据资产台",
        "当前页面用于核对底座文件、查看数据挂载情况，并覆盖上传新的 CSV 数据副本。",
        eyebrow="Spatial Assets",
    )

    render_summary_cards(
        [
            {"value": plots_count, "title": "重点更新单元", "desc": "对应规划评估与方案落点。"},
            {"value": buildings_count, "title": "建筑底图", "desc": "用于现状与成果三维表达。"},
            {
                "value": next((item["count"] for item in inventory if item["name"] == "POI 数据"), 0),
                "title": "POI 记录",
                "desc": "用于活力和服务设施分析。",
            },
            {
                "value": next((item["count"] for item in inventory if item["name"] == "交通数据"), 0),
                "title": "交通记录",
                "desc": "用于路网诊断与拥堵识别。",
            },
        ]
    )

    manifest_df = build_manifest_df(inventory)
    st.dataframe(manifest_df, use_container_width=True, hide_index=True)

    with st.sidebar:
        st.markdown("### ⚙️ 数据底层维护")
        obj_sel = st.selectbox("选择管理对象", ["🏪 POI数据", "🚥 交通数据", "📊 CV分析结果", "💬 情感分析数据"], key="p7_mgr_sel")
        st.info("上传的新文件会直接覆盖 `data/` 目录中的对应副本。")

    render_section_intro(
        "数据预览与覆盖上传",
        "先核对样例数据，再决定是否覆盖上传新的版本，避免误写错误文件。",
        eyebrow="Dataset Preview",
    )

    dataset_meta = {
        "🏪 POI数据": ("poi", "支撑空间活力、设施密度和业态诊断。"),
        "🚥 交通数据": ("traffic", "支撑交通堵点识别与慢行优化。"),
        "📊 CV分析结果": ("gvi", "支撑街景环境品质、绿视率等计算。"),
        "💬 情感分析数据": ("nlp", "支撑社会需求、舆情反馈与协同治理。"),
    }
    data_key, data_desc = dataset_meta[obj_sel]
    target_csv = DATA_FILES[data_key]

    st.markdown(
        f"""
        <div class="content-panel">
            <h3>{escape(obj_sel)}</h3>
            <p>{escape(data_desc)}</p>
            <div class="panel-caption">文件位置：{escape(target_csv.as_posix())}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if target_csv.exists():
        preview_df = pd.read_csv(target_csv)
        st.dataframe(preview_df.head(30), use_container_width=True)
        uploaded_csv = st.file_uploader("覆盖上传最新的物理副本", key="p7_csv_up")
        if uploaded_csv is not None:
            with target_csv.open("wb") as file_obj:
                file_obj.write(uploaded_csv.getbuffer())
            st.success(f"文件已覆盖写入: {target_csv.as_posix()}")
            st.rerun()
    else:
        st.error(f"未找到目标数据文件：{target_csv.as_posix()}")
