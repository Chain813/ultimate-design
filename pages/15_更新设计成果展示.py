import json
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.config import ASSETS_DIR, DATA_DIR, DATA_FILES, DOCS_DIR, SHP_FILES, STATIC_DIR, get_static_url
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav
from src.workflow.city_design_workflow import resolve_subpage_option
from src.utils.document_generator import generate_official_word_doc


st.set_page_config(page_title="更新设计成果展示 | 05 实验室", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

TASK_BOOK_PATH = DOCS_DIR / "毕业设计任务书.pdf"
PROPOSAL_PATH = DOCS_DIR / "毕业设计开题报告.pdf"
PROTECTION_PLAN_PATH = DOCS_DIR / "伪满皇宫保护规划.pdf"


@st.cache_data(ttl=1800)
def load_base_map_data():
    def load_json(fp):
        with open(fp, "r", encoding="utf-8") as file_obj:
            return file_obj.read()

    building_data = f"'{get_static_url('buildings.geojson')}'" if (STATIC_DIR / "buildings.geojson").exists() else "null"
    boundary_data = load_json(str(SHP_FILES["boundary"])) if SHP_FILES["boundary"].exists() else "null"
    plots_data = load_json(str(SHP_FILES["plots"])) if SHP_FILES["plots"].exists() else "null"
    return building_data, boundary_data, plots_data


@st.cache_data(ttl=600)
def load_3d_data():
    points_df = pd.read_excel(DATA_FILES["points"])
    analysis_df = pd.read_csv(DATA_FILES["gvi"])
    if "Folder" in analysis_df.columns:
        analysis_df["ID"] = analysis_df["Folder"].str.replace("Point_", "").astype(int)
        analysis_df = analysis_df.groupby("ID").mean(numeric_only=True).reset_index()
    return pd.merge(points_df, analysis_df, on="ID", how="inner")


@st.cache_data(ttl=1800)
def count_geo_features(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return len(json.loads(path.read_text(encoding="utf-8")).get("features", []))
    except Exception:
        return 0


@st.cache_data(ttl=1800)
def read_binary(path: Path) -> bytes:
    if not path.exists():
        return b""
    return path.read_bytes()


def render_doc_card(title, badge, items):
    bullets = "".join(f"<li>{escape(item)}</li>" for item in items)
    st.markdown(
        f"""
        <div class="doc-card">
            <div class="doc-card-title">
                <h4>{escape(title)}</h4>
                <span class="doc-badge">{escape(badge)}</span>
            </div>
            <ul class="doc-list">{bullets}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_future_deckgl(is_3d=True, view_pitch=60, is_demo=True, is_xray=False):
    building_data, boundary_data, plots_data = load_base_map_data()

    with (ASSETS_DIR / "map3d_standalone.html").open("r", encoding="utf-8") as file_obj:
        html = file_obj.read()

    html = html.replace("/*__BUILDING_DATA__*/null/*__END_BUILDING__*/", building_data)
    html = html.replace("/*__BOUNDARY_DATA__*/null/*__END_BOUNDARY__*/", boundary_data)
    html = html.replace("/*__PLOTS_DATA__*/null/*__END_PLOTS__*/", plots_data)
    html = html.replace("/*__POI_DATA__*/null/*__END_POI__*/", "null")
    html = html.replace("/*__TRAFFIC_DATA__*/null/*__END_TRAFFIC__*/", "null")
    html = html.replace("/*__LANDUSE_DATA__*/null/*__END_LANDUSE__*/", "null")
    html = html.replace("/*__HEX_PAYLOAD__*/null/*__END_HEX_PAY__*/", "null")
    html = html.replace("/*__COL_PAYLOAD__*/null/*__END_COL_PAY__*/", "null")
    html = html.replace("/*__HEAT_PAYLOAD__*/null/*__END_HEAT_PAY__*/", "null")
    html = html.replace("/*__IS_3D__*/true/*__END_IS_3D__*/", "true" if is_3d else "false")
    html = html.replace("/*__SHOW_LIGHTING__*/true/*__END_LIGHTING__*/", "true")
    html = html.replace("/*__SUN_TIME__*/10/*__END_SUN_TIME__*/", "14")
    html = html.replace("/*__IS_XRAY__*/false/*__END_IS_XRAY__*/", "true" if is_xray else "false")
    html = html.replace("/*__IS_DEMO__*/false/*__END_IS_DEMO__*/", "true" if is_demo else "false")

    pipe_payload = "null"
    if is_xray:
        try:
            pipes = []
            for _, row in load_3d_data().iterrows():
                lng, lat = row["Lng"], row["Lat"]
                pipes.append({"path": [[lng, lat], [lng + 0.001, lat + 0.001]], "type": "water"})
                pipes.append({"path": [[lng, lat], [lng - 0.001, lat + 0.0005]], "type": "power"})
            pipe_payload = json.dumps(pipes)
        except Exception:
            pipe_payload = "null"

    html = html.replace("/*__PIPE_PAYLOAD__*/null/*__END_PIPE__*/", pipe_payload)
    html = html.replace("pitch: is_3d ? 45 : 0", f"pitch: {view_pitch}")

    st.markdown(
        """
        <style>
            iframe[title="st.iframe"] {
                border-radius: 14px !important;
                overflow: hidden !important;
                border: 1px solid rgba(99, 102, 241, 0.35);
                box-shadow: 0 14px 42px rgba(0, 0, 0, 0.38);
                margin-bottom: 16px !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    components.html(html, height=860, scrolling=False)


plots_count = count_geo_features(SHP_FILES["plots"])
buildings_count = count_geo_features(SHP_FILES["buildings"])

render_page_banner(
    title="更新设计成果展示",
    description="把留改拆总图、地下管网透视、规划导则和视觉成果汇成一套可直接交付的展示页面，形成从研究判断到方案表达的闭环。",
    eyebrow="Page 05",
    tags=["留改拆策略总图", "地下管网 X-Ray", "导则文本导出", "AIGC 效果图集"],
    metrics=[
        {"value": "5 个", "label": "深化地段", "meta": "与任务书要求的重点单元保持一致"},
        {"value": "15 处", "label": "历史建筑", "meta": "导则中重点保护的风貌资源"},
        {"value": plots_count, "label": "更新单元", "meta": "成果总图加载的核心地块"},
        {"value": buildings_count, "label": "建筑底图", "meta": "成果场景调用的现状建筑底板"},
    ],
)

if "lab05_active_sub" not in st.session_state:
    st.session_state.lab05_active_sub = "🏙️ 更新设计大地图"

tab_options = ["🏙️ 更新设计大地图", "📑 规划文本成果", "🖼️ 重点地块效果图"]
default_tab_index = tab_options.index(st.session_state.lab05_active_sub) if st.session_state.lab05_active_sub in tab_options else 0
default_tab_index = resolve_subpage_option(tab_options, default_index=default_tab_index)
if st.query_params.get("sub"):
    st.session_state.lab05_active_sub = tab_options[default_tab_index]
    st.session_state["lab05_switcher"] = tab_options[default_tab_index]
selected_sub = tab_options[default_tab_index]
st.session_state.lab05_active_sub = selected_sub
st.markdown("---")


if selected_sub == "🏙️ 更新设计大地图":
    render_section_intro(
        "留改拆总图与场景推演",
        "总图直接承接重点更新单元和建筑底图，用于展示保护、活化、拆除腾退和地下管网优化的综合结果。",
        eyebrow="Future Scenario Engine",
    )
    render_summary_cards(
        [
            {"value": "紫色", "title": "修缮保护", "desc": "对应历史风貌保护区和挂牌历史建筑。"},
            {"value": "黄色", "title": "功能活化", "desc": "对应低效厂房和商业裙楼的活化改造。"},
            {"value": "红色", "title": "拆除腾退", "desc": "对应低层违建和存在安全隐患的清退空间。"},
            {"value": "X-Ray", "title": "地下管网", "desc": "叠加查看水电等基础设施的微循环更新逻辑。"},
        ]
    )
    st.markdown(
        """
        <div class="content-panel">
            <h3>场景图例</h3>
            <div class="legend-strip">
                <span class="legend-item"><span class="legend-dot" style="background:#8b5cf6;"></span>修缮保护</span>
                <span class="legend-item"><span class="legend-dot" style="background:#f59e0b;"></span>功能改造</span>
                <span class="legend-item"><span class="legend-dot" style="background:#ef4444;"></span>拆除腾退</span>
                <span class="legend-item"><span class="legend-dot" style="background:#22c55e;"></span>绿地与开敞空间</span>
            </div>
            <div class="panel-caption">建议先查看标准场景，再叠加 X-Ray 观察基础设施韧性更新路径。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1, 1, 1.6])
    with ctrl_col1:
        enable_demo = st.checkbox("启动留改拆演示", value=True)
    with ctrl_col2:
        enable_xray = st.checkbox("叠加地下管网 X-Ray", value=False)
    with ctrl_col3:
        st.markdown(
            """
            <div class="note-panel">
                <p><strong>说明：</strong>当前总图优先承担成果表达功能，因此隐藏了现状 POI、交通热力等底层诊断图层，只保留成果所需的重点单元与建筑底板。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_future_deckgl(
        is_3d=True,
        view_pitch=65 if enable_xray else 45,
        is_demo=enable_demo,
        is_xray=enable_xray,
    )


elif selected_sub == "📑 规划文本成果":
    render_section_intro(
        "规划导则与交付依据",
        "将任务书、开题报告和保护规划中的关键要求整理为最终导则表达，并支持导出 Word 版成果。",
        eyebrow="Guideline Delivery",
    )

    render_summary_cards(
        [
            {"value": "任务书", "title": "边界要求", "desc": "锁定研究范围、5 个深化地段和成果深度。"},
            {"value": "开题报告", "title": "策略来源", "desc": "对齐 4 项痛点与 4 类设计策略。"},
            {"value": "保护规划", "title": "管控底线", "desc": "约束建筑高度、风貌修缮与基础设施改造。"},
            {"value": "Word", "title": "正式导出", "desc": "可直接导出带红头的阶段成果文件。"},
        ]
    )

    ref_col1, ref_col2 = st.columns([1.15, 0.85])
    with ref_col1:
        render_doc_card(
            "成果依据",
            "文档基准",
            [
                "《毕业设计任务书》锁定研究边界、成果要求和重点地段。",
                "《毕业设计开题报告》提供问题诊断、案例借鉴与策略主线。",
                "《伪满皇宫保护规划》补充高度、风貌和基础设施改造约束。",
            ],
        )
        st.markdown(
            """
            <div class="note-panel">
                <p><strong>成果口径：</strong>本页文本导则不再重复前端诊断过程，而是面向汇报和交付，集中表达“为什么改、改哪里、怎么改、如何落地”。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with ref_col2:
        task_bytes = read_binary(TASK_BOOK_PATH)
        proposal_bytes = read_binary(PROPOSAL_PATH)
        plan_bytes = read_binary(PROTECTION_PLAN_PATH)
        if task_bytes:
            st.download_button("📥 下载任务书", task_bytes, TASK_BOOK_PATH.name, "application/pdf", use_container_width=True)
        if proposal_bytes:
            st.download_button("📥 下载开题报告", proposal_bytes, PROPOSAL_PATH.name, "application/pdf", use_container_width=True)
        if plan_bytes:
            st.download_button("📥 下载保护规划", plan_bytes, PROTECTION_PLAN_PATH.name, "application/pdf", use_container_width=True)

    guide_tabs = st.tabs(["总则", "空间留改拆", "实施要点"])
    with guide_tabs[0]:
        st.markdown(
            """
            <div class="content-panel">
                <h3>1. 总则</h3>
                <ul class="status-list">
                    <li>以伪满皇宫周边历史街区为核心，兼顾历史保护、交通缝合和产业更新。</li>
                    <li>坚持“修旧如旧、针灸更新、设施完善、韧性提升”的总体原则。</li>
                    <li>通过数字孪生和 AI 辅助设计，把前期诊断成果转化为可执行的更新导则。</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with guide_tabs[1]:
        st.markdown(
            """
            <div class="content-panel">
                <h3>2. 空间留改拆策略</h3>
                <ul class="status-list">
                    <li><strong>历史风貌保护区：</strong>围绕伪满皇宫及周边 15 处历史建筑，严格控制外立面材质与尺度。</li>
                    <li><strong>功能活化改造区：</strong>针对低效厂房和商业裙楼导入文创零售、青年办公和复合服务。</li>
                    <li><strong>拆除腾退区：</strong>优先清理低层违建和存在安全隐患建筑，释放绿地与公共停车空间。</li>
                    <li><strong>地下基础设施：</strong>同步推进水电管线微循环更新，与地面空间品质提升联动。</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with guide_tabs[2]:
        st.markdown(
            """
            <div class="content-panel">
                <h3>3. 实施与交付要点</h3>
                <ul class="status-list">
                    <li>近期先行区聚焦中车老厂区、历史街区断点和环境品质低下节点。</li>
                    <li>导则交付应同步包含留改拆总图、重点节点效果图和阶段汇报文本。</li>
                    <li>后续可继续接入 03 页面生成的 AIGC 推演图，形成动态更新的成果包。</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    full_text = """
# 第一章 总则
## 1.1 规划目的
为贯彻落实长春市城市更新总体战略，科学指导宽城区伪满皇宫周边历史文化街区的保护与复兴工作，制定本导则。本导则汲取了多主体（公众、开发商、规划师）的大模型博弈共识。

## 1.2 规划原则
- 修旧如旧，存量提质：严格保护历史街区真实性。
- 针灸更新，活力激发：以微小尺度的介入带动全局活力。
- 设施完善，韧性提升：全面升级地下水电管网系统（见 X-Ray 管线规划图）。

# 第二章 空间留改拆策略分布
## 2.1 历史风貌保护区 (紫色区域)
涉及伪满皇宫及周边 15 处挂牌历史建筑。严格禁止改变外立面材质，允许内部进行符合现代安全标准的修缮。

## 2.2 功能活化改造区 (黄色区域)
对 80 年代建成的低效厂房及废弃商业裙楼进行“腾笼换鸟”，植入文创零售与青创办公空间。

## 2.3 拆除腾退区 (动态塌缩区域)
针对 MPI 评分极高且建筑老化严重、存在安全隐患的违章建筑实施拆除，释放的用地优先作为绿地口袋公园及公共停车场。
    """

    aigc_history = st.session_state.get("aigc_history", [])
    docx_io = generate_official_word_doc(
        title="宽城区历史文化街区微更新规划导则",
        text_content=full_text,
        aigc_history=aigc_history,
    )
    st.download_button(
        label="📥 一键导出带红头公文 (Word 格式，含 AIGC 图集)",
        data=docx_io,
        file_name="宽城区历史文化街区微更新规划导则(AI自动生成版).docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
        type="primary",
    )


elif selected_sub == "🖼️ 重点地块效果图":
    render_section_intro(
        "重点地块效果图集",
        "优先展示本次会话内生成的 AIGC 推演结果；若暂无记录，则回退为项目内置的本地成果示意图。",
        eyebrow="Visual Deliverables",
    )

    aigc_history = st.session_state.get("aigc_history", [])
    if aigc_history:
        latest_strategy = aigc_history[-1].get("strategy", "未命名策略")
        render_summary_cards(
            [
                {"value": len(aigc_history), "title": "推演记录", "desc": "本次会话内已生成的方案数量。"},
                {"value": latest_strategy, "title": "最新策略", "desc": "最近一次生成采用的风貌策略。"},
                {"value": "动态", "title": "成果来源", "desc": "直接调用 03 页面生成的会话图集。"},
            ]
        )

        history_cols = st.columns(min(3, len(aigc_history[-6:])))
        for idx, entry in enumerate(aigc_history[-6:]):
            with history_cols[idx % len(history_cols)]:
                st.markdown(
                    f"""
                    <div class="doc-card">
                        <img src="data:image/jpeg;base64,{entry['thumb_b64']}" style="width:100%; border-radius:10px; margin-bottom:10px;" />
                        <div class="doc-card-title">
                            <h4>{escape(entry.get("plot", "未命名地块"))}</h4>
                            <span class="doc-badge">{escape(entry.get("strategy", "未命名"))}</span>
                        </div>
                        <div class="doc-meta">方向：{escape(entry.get("direction", "未标注"))}</div>
                        <div class="panel-caption">{escape(entry.get("prompt_excerpt", ""))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        if st.button("🗑️ 清空推演历史", key="clear_lab05_history"):
            st.session_state["aigc_history"] = []
            st.rerun()
    else:
        st.markdown(
            """
            <div class="note-panel">
                <p><strong>当前没有会话内推演图：</strong>下方展示的是项目本地内置成果图，用于保证页面五在离线状态下依然完整可展示。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    local_gallery = [
        {
            "title": "节点 A：历史街道立面修缮",
            "path": ASSETS_DIR / "05_design_inference.png",
            "desc": "对应沿街历史建筑的立面治理、店招整理和步行界面修复。",
            "tags": ["来自 03 实验室", "历史保护", "立面修缮"],
        },
        {
            "title": "节点 B：数字孪生场景对照",
            "path": ASSETS_DIR / "03_digital_twin.png",
            "desc": "用于展示更新前后空间肌理与重点节点位置关系。",
            "tags": ["来自 02 实验室", "数字孪生", "总体场景"],
        },
        {
            "title": "节点 C：问题诊断到策略响应",
            "path": ASSETS_DIR / "04_urban_diagnosis.png",
            "desc": "把环境品质短板和后续设计介入点直接对应起来。",
            "tags": ["诊断转策略", "空间优化", "环境品质"],
        },
        {
            "title": "节点 D：地块与底图联动",
            "path": DATA_DIR / "GIS高对比度图纸.png",
            "desc": "用于汇报中叠加地块边界、留改拆策略和基础设施优化信息。",
            "tags": ["底图成果", "空间数据", "汇报表达"],
        },
    ]

    gallery_cols = st.columns(2)
    for idx, item in enumerate(local_gallery):
        with gallery_cols[idx % 2]:
            st.image(str(item["path"]), use_container_width=True)
            tags_html = "".join(f'<span class="gallery-tag">{escape(tag)}</span>' for tag in item["tags"])
            st.markdown(
                f"""
                <div class="gallery-card-body">
                    <h4>{escape(item["title"])}</h4>
                    <p>{escape(item["desc"])}</p>
                    <div class="gallery-tag-row">{tags_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
