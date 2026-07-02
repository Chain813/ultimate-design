"""阶段 00-01：数据准备与任务解读 —— 数据上传、获取教程、项目概况、任务书展示。"""

import json
import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import DATA_DIR, DOCS_DIR, META_DIR
from src.data import DATA_CATEGORIES, check_data_exists, get_data_readiness, get_data_size
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards, render_data_pipeline, render_mission_decoding_hud
from src.ui.app_shell import render_top_nav
from src.ui.module_summary import render_stage_summary
from src.ui.streamlit_compat import stretch_width
from src.workflow.stage_data_bus import save_stage_output, render_evidence_chain_bar
from src.workflow import resolve_subpage_value
from src.utils.text_io import read_text_with_fallback

st.set_page_config(page_title="00 数据准备与任务解读", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

TASK_BOOK_PATH = DOCS_DIR / "毕业设计任务书.pdf"
PROPOSAL_PATH = DOCS_DIR / "毕业设计开题报告.pdf"


# ============================================================
# 辅助函数
# ============================================================

def save_uploaded_file(uploaded_file, target_path: Path) -> bool:
    """保存上传的文件到目标路径。"""
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return True
    except Exception as e:
        st.error(f"保存失败: {e}")
        return False


def render_data_overview_table():
    """渲染数据概览表，带颜色编码。"""
    overview_rows = []
    for cat in DATA_CATEGORIES:
        exists = check_data_exists(cat["id"])
        if exists:
            status = "✅ 已上传"
        elif cat["required"]:
            status = "❌ 缺失 (必备)"
        else:
            status = "⚪ 可选"
        overview_rows.append({
            "类别": f"{cat['icon']} {cat['title']}",
            "格式": cat["format_desc"],
            "大小": get_data_size(cat["id"]),
            "状态": status,
        })
    st.dataframe(pd.DataFrame(overview_rows), hide_index=True, use_container_width=True)


def render_csv_preview(target: Path):
    """渲染 CSV 数据预览。"""
    try:
        df = pd.read_csv(target, nrows=5)
        st.markdown("**数据预览 (前 5 行)**:")
        st.dataframe(df, use_container_width=True)
    except Exception:
        logging.debug("CSV 预览失败: %s", target, exc_info=True)


def render_json_preview(target: Path):
    """渲染 JSON/GeoJSON 数据预览。"""
    try:
        with open(target, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "features" in data:
            st.markdown(f"**要素数量**: {len(data['features'])}")
        elif isinstance(data, dict):
            st.markdown(f"**键数量**: {len(data)}")
    except Exception:
        logging.debug("JSON 预览失败: %s", target, exc_info=True)


def render_tutorial_popover(cat: dict):
    """渲染教程弹出窗口。"""
    tutorial = cat["tutorial"]
    with st.popover("📖 查看获取教程"):
        st.markdown(f"**{tutorial['summary']}**")
        for method in tutorial["methods"]:
            st.markdown(f"**{method['name']}**")
            for step in method["steps"]:
                st.markdown(f"- {step}")
            if "tip" in method:
                st.info(f"💡 {method['tip']}")


def run_quality_check():
    """执行数据质量检查。"""
    results = []

    for cat in DATA_CATEGORIES:
        target = cat["target_path"]
        status = "未上传"
        issues = []
        record_count = 0

        if target.exists() or (target.is_dir() and any(target.iterdir())):
            status = "已上传"

            if target.suffix == ".csv":
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
                        lat_range = (43.5, 44.5)
                        lng_range = (125.0, 126.0)
                        out_lat = ((df["Lat"] < lat_range[0]) | (df["Lat"] > lat_range[1])).sum()
                        out_lng = ((df["Lng"] < lng_range[0]) | (df["Lng"] > lng_range[1])).sum()
                        if out_lat > 0:
                            issues.append(f"{out_lat} 条记录纬度超出长春范围")
                        if out_lng > 0:
                            issues.append(f"{out_lng} 条记录经度超出长春范围")

                except Exception as e:
                    issues.append(f"CSV 解析错误: {str(e)[:50]}")

            elif target.suffix in [".json", ".geojson"]:
                try:
                    with open(target, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict) and "features" in data:
                        record_count = len(data["features"])
                        if data.get("type") != "FeatureCollection":
                            issues.append("GeoJSON 类型不是 FeatureCollection")
                    elif isinstance(data, dict):
                        record_count = len(data)
                except json.JSONDecodeError as e:
                    issues.append(f"JSON 解析错误: {str(e)[:50]}")

            elif target.is_dir():
                point_dirs = [d for d in target.iterdir() if d.is_dir()]
                record_count = len(point_dirs)
                for pd_dir in point_dirs[:5]:
                    jpg_count = len(list(pd_dir.glob("*.jpg")))
                    if jpg_count < 4:
                        issues.append(f"{pd_dir.name} 仅有 {jpg_count} 张照片 (应为 4 张)")

        quality_score = "A" if not issues else ("B" if len(issues) <= 2 else "C")
        results.append({
            "类别": f"{cat['icon']} {cat['title']}",
            "状态": status,
            "记录数": record_count,
            "问题数": len(issues),
            "质量评级": quality_score,
            "详情": "; ".join(issues) if issues else "无问题",
        })

    return results


# ============================================================
# 页面顶部
# ============================================================
readiness = get_data_readiness()

render_page_banner(
    title="数据准备与任务解读",
    description="上传项目原始数据、查阅获取教程、锁定研究范围与任务要求。",
    eyebrow="Stage 00-01",
    tags=["数据上传", "数据获取", "任务书解析", "质量校验"],
    metrics=[
        {"value": f"{readiness['total']} 类", "label": "数据类别", "meta": "空间、POI、街景、文本、房价等"},
        {"value": "约160 公顷", "label": "研究范围", "meta": "任务书明确的核心片区"},
        {"value": "动态", "label": "深化单元", "meta": "按配置读取重点更新单元"},
    ],
    graphic_html=render_data_pipeline(as_html=True)
)
render_evidence_chain_bar("00", ["00", "01", "02", "03", "04", "05"])

render_summary_cards([
    {"value": f"{readiness['loaded']}/{readiness['total']}", "title": "已上传数据集", "desc": "数据类别完备度"},
    {"value": f"{readiness['required_loaded']}/{readiness['required_count']}", "title": "必备数据就绪", "desc": "核心数据完整性"},
    {"value": "✅" if readiness["is_ready"] else "⏳", "title": "数据就绪状态", "desc": "可否进入下一阶段"},
])

st.markdown("---")

# ============================================================
# 子标签选择
# ============================================================
SUB_OPTIONS = ["📦 数据上传中心", "📚 数据获取教程", "📋 项目概况与任务要求", "📊 数据质量检查"]
selected_sub = resolve_subpage_value(SUB_OPTIONS)
st.markdown("---")


# ============================================================
# 模块一：数据上传中心
# ============================================================
if selected_sub == "📦 数据上传中心":
    render_section_intro(
        "数据上传中心",
        "按类别上传原始数据文件，系统会自动保存到对应目录。",
        eyebrow="Upload Center",
    )

    render_data_overview_table()
    st.markdown("---")

    for cat in DATA_CATEGORIES:
        exists = check_data_exists(cat["id"])
        with st.expander(f"{cat['icon']} {cat['title']} {'✅' if exists else '❌'}", expanded=False):
            col_info, col_upload = st.columns([2, 1])

            with col_info:
                st.markdown(f"**说明**: {cat['description']}")
                st.markdown(f"**支持格式**: {cat['format_desc']}")
                st.markdown(f"**目标路径**: `{cat['target_path'].relative_to(DATA_DIR.parent)}`")

                if exists:
                    st.success(f"当前数据已存在 ({get_data_size(cat['id'])})")
                    target = cat["target_path"]
                    if target.suffix == ".csv":
                        render_csv_preview(target)
                    elif target.suffix in [".json", ".geojson"]:
                        render_json_preview(target)

                render_tutorial_popover(cat)

            with col_upload:
                uploaded_file = st.file_uploader(
                    f"上传 {cat['title']}",
                    type=[ext.lstrip(".") for ext in cat["accept"]],
                    key=f"upload_{cat['id']}",
                    help=f"支持格式: {', '.join(cat['accept'])}",
                )

                if uploaded_file:
                    st.markdown(f"**文件名**: {uploaded_file.name}")
                    st.markdown(f"**文件大小**: {uploaded_file.size / 1024:.1f} KB")

                    if st.button("💾 保存到项目", key=f"save_{cat['id']}", type="primary", use_container_width=True):
                        if save_uploaded_file(uploaded_file, cat["target_path"]):
                            st.success("✅ 保存成功!")
                            st.rerun()


# ============================================================
# 模块二：数据获取教程
# ============================================================
elif selected_sub == "📚 数据获取教程":
    render_section_intro(
        "数据获取教程",
        "详细了解每类数据的获取方式、格式要求和处理流程。",
        eyebrow="Tutorial Guide",
    )

    st.markdown("### 📋 教程目录")
    cols = st.columns(3)
    for idx, cat in enumerate(DATA_CATEGORIES):
        with cols[idx % 3]:
            st.markdown(f"- [{cat['icon']} {cat['title']}](#{cat['id']})")

    st.markdown("---")

    for cat in DATA_CATEGORIES:
        st.markdown(f'<a id="{cat["id"]}"></a>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"## {cat['icon']} {cat['title']}")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**数据格式**: {cat['format_desc']}")
            with col2:
                st.markdown(f"**是否必备**: {'是' if cat['required'] else '否'}")
            with col3:
                st.markdown(f"**目标路径**: `{cat['target_path'].name}`")

            st.markdown(f"**说明**: {cat['description']}")

            tutorial = cat["tutorial"]
            st.markdown("### 📖 获取方法")
            st.info(tutorial["summary"])

            for method_idx, method in enumerate(tutorial["methods"]):
                st.markdown(f"#### {method['name']}")
                for step in method["steps"]:
                    st.markdown(f"  {step}")
                if "code_example" in method:
                    st.code(method["code_example"], language="python")
                if "tip" in method:
                    st.warning(f"💡 **提示**: {method['tip']}")
                if method_idx < len(tutorial["methods"]) - 1:
                    st.markdown("---")

            st.markdown("### 📝 数据字段说明")
            st.code(tutorial["sample_fields"])

            st.markdown("### 📁 参考文件")
            st.markdown(tutorial["reference"])


# ============================================================
# 模块三：项目概况与任务要求 (原 Stage 01)
# ============================================================
elif selected_sub == "📋 项目概况与任务要求":
    render_section_intro("项目基本信息与任务要求", "锁定研究边界、设计深度和核心任务，核对任务书与开题报告。", eyebrow="Project Brief")

    # 项目概况
    info_data = {
        "项目名称": "AI赋能下的伪满皇宫周边街区更新规划设计",
        "设计类型": "城市更新 · 历史街区 · 数字孪生",
        "研究范围": "约160公顷，由长春大街、长白路、东九条、亚泰快速路围合",
        "设计深度": "总体城市设计 + 重点更新单元深化设计",
        "成果形式": "A3图册（≥60页）+ A1展板（≥3张）+ 规划文本 + PPT",
        "核心矛盾": "历史保护与活力不足、工业低效、社区老化、交通割裂",
        "技术特色": "GIS + CV + POI + NLP/LLM + AIGC + 数字孪生",
    }
    for k, v in info_data.items():
        st.markdown(f"**{k}**：{v}")

    save_stage_output("01", "project_info", info_data)

    st.markdown("---")

    # 任务书与开题报告
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("#### 📕 毕业设计任务书")
            st.caption("官方下发的设计要求与边界限定文件。")
            if TASK_BOOK_PATH.exists():
                st.download_button(
                    "📥 下载任务书 PDF",
                    TASK_BOOK_PATH.read_bytes(),
                    file_name=TASK_BOOK_PATH.name,
                    mime="application/pdf",
                    type="primary",
                    **stretch_width(st.download_button),
                )
            else:
                st.warning("未找到任务书文件。")

            mission_path = META_DIR / "mission_text.txt"
            if mission_path.exists():
                mission_text = read_text_with_fallback(mission_path)
                with st.expander("👁️ 查看任务书核心摘录", expanded=True):
                    st.markdown(
                        f'''<div style="font-size:13px; color:#48484a; line-height:1.6;
                        max-height:280px; overflow-y:auto; padding:12px;
                        background:rgba(0,0,0,0.03); border-radius:8px; border: 1px solid rgba(0,0,0,0.08);">
                        {mission_text[:1800].replace(chr(10), "<br>")}</div>''',
                        unsafe_allow_html=True
                    )

    with col2:
        with st.container(border=True):
            st.markdown("#### 📗 毕业设计开题报告")
            st.caption("前期调研、文献综述与核心技术路线推演报告。")
            if PROPOSAL_PATH.exists():
                st.download_button(
                    "📥 下载开题报告 PDF",
                    PROPOSAL_PATH.read_bytes(),
                    file_name=PROPOSAL_PATH.name,
                    mime="application/pdf",
                    type="primary",
                    **stretch_width(st.download_button),
                )
            else:
                st.warning("未找到开题报告文件。")

            with st.expander("👁️ 查看核心框架提纲", expanded=True):
                st.markdown(
                    '''<div style="font-size:13px; color:#48484a; line-height:1.6;
                    max-height:280px; overflow-y:auto; padding:12px;
                    background:rgba(0,0,0,0.03); border-radius:8px; border: 1px solid rgba(0,0,0,0.08);">
                    <b style="color:#1d1d1f;">第一部分：现状研判与问题痛点</b><br>
                    • 历史文脉断裂与空间感知弱化<br>
                    • 工业遗存与建筑资产闲置低效<br>
                    • 跨铁路交通微循环与慢行系统不畅<br><br>
                    <b style="color:#1d1d1f;">第二部分：目标定位与愿景</b><br>
                    数字孪生驱动的"古今共振"街区微更新规划<br><br>
                    <b style="color:#1d1d1f;">第三部分：拟采用的核心技术路线</b><br>
                    <code>GIS底座构建</code> ➔ <code>多源数据语义萃取</code> ➔ <code>AHP-MPI 潜力评估</code> ➔ <code>AIGC (SD/ControlNet) 推演</code>
                    </div>''',
                    unsafe_allow_html=True
                )


# ============================================================
# 模块四：数据质量检查
# ============================================================
elif selected_sub == "📊 数据质量检查":
    render_section_intro(
        "数据质量检查",
        "检查已上传数据的完整性、格式正确性和内容质量。",
        eyebrow="Quality Check",
    )

    if st.button("🔍 开始全面检查", type="primary", use_container_width=True):
        results = run_quality_check()

        st.markdown("### 📋 检查结果")
        df_results = pd.DataFrame(results)
        st.dataframe(df_results, hide_index=True, use_container_width=True)

        uploaded_count = sum(1 for r in results if r["状态"] == "已上传")
        issue_count = sum(1 for r in results if r["问题数"] > 0)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("已上传", f"{uploaded_count}/{len(results)}")
        with col2:
            st.metric("存在问题", f"{issue_count}")
        with col3:
            st.metric("数据完备度", f"{uploaded_count / len(results) * 100:.0f}%")

        save_stage_output("00", "data_quality_check", {
            "total": len(results),
            "uploaded": uploaded_count,
            "issues": issue_count,
            "details": results,
        })

        st.markdown("### 💡 质量建议")
        missing_cats = [r["类别"] for r in results if r["状态"] == "未上传"]
        if missing_cats:
            st.warning(f"以下数据尚未上传: {', '.join(missing_cats)}")
        if issue_count > 0:
            st.error(f"有 {issue_count} 个数据类别存在问题，请检查并修复。")
        if uploaded_count == len(results) and issue_count == 0:
            st.success("所有数据已就绪且质量良好，可以进入下一阶段!")


# ============================================================
# 底部
# ============================================================
st.markdown("---")

save_stage_output("00", "data_readiness", {
    "total_categories": readiness["total"],
    "loaded_count": readiness["loaded"],
    "required_loaded": readiness["required_loaded"],
    "is_ready": readiness["is_ready"],
})

render_stage_summary(
    stage_code="01",
    title="项目边界与任务要求锁定",
    findings=[
        {"point": "研究范围约 160 公顷，涵盖重点更新单元", "evidence": "任务书明确的核心片区边界"},
        {"point": "核心任务为系统性概念设计 + 数字孪生与 AIGC 推演表达", "evidence": "任务书核心任务条款"},
        {"point": "四大核心痛点：用地混杂、交通割裂、老龄化、环境品质不足", "evidence": "开题报告现状诊断结论"},
    ],
    methodology="基于毕业设计任务书与开题报告的文本解析",
    implication="为后续资料收集（Stage 02）和现场调研（Stage 03）提供了明确的工作边界",
)
