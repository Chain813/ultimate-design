"""阶段 00：数据准备 —— 已有数据上传与获取教程。"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import DATA_DIR
from src.data import DATA_CATEGORIES, check_data_exists, get_data_readiness, get_data_size
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav
from src.workflow.stage_data_bus import save_stage_output, render_evidence_chain_bar

st.set_page_config(page_title="00 数据准备", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()


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
        pass


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
        pass


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

                    # 检查必要字段
                    field_map = {
                        "poi": ["Name", "Lat", "Lng"],
                        "traffic": ["Name", "Type", "Lat", "Lng"],
                        "gvi": ["ID", "GVI", "SVF", "Enclosure", "Clutter"],
                    }
                    if cat["id"] in field_map:
                        missing = [c for c in field_map[cat["id"]] if c not in df.columns]
                        if missing:
                            issues.append(f"缺少字段: {', '.join(missing)}")

                    # 检查空值
                    null_cols = df.columns[df.isnull().any()].tolist()
                    if null_cols:
                        issues.append(f"含空值字段: {', '.join(null_cols)}")

                    # 检查坐标范围
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
# 页面渲染
# ============================================================

# 页面顶部
readiness = get_data_readiness()

render_page_banner(
    title="数据准备",
    description="上传项目所需的各类原始数据，确保后续分析流程数据完备。",
    eyebrow="Stage 00",
    tags=["数据上传", "数据获取", "格式规范", "质量校验"],
    metrics=[
        {"value": f"{readiness['total']} 类", "label": "数据类别", "meta": "空间、POI、街景、文本、房价等"},
        {"value": "25+", "label": "数据文件", "meta": "支撑 13 阶段工作流"},
        {"value": "6 种", "label": "数据格式", "meta": "CSV / GeoJSON / XLSX / JPG / TIF"},
    ],
)
render_evidence_chain_bar("00", ["00", "01", "02", "03", "04", "05"])

# 数据完备度
render_summary_cards([
    {"value": f"{readiness['loaded']}/{readiness['total']}", "title": "已上传数据集", "desc": "数据类别完备度"},
    {"value": f"{readiness['required_loaded']}/{readiness['required_count']}", "title": "必备数据就绪", "desc": "核心数据完整性"},
    {"value": "✅" if readiness["is_ready"] else "⏳", "title": "数据就绪状态", "desc": "可否进入下一阶段"},
])

st.markdown("---")

# 功能模块选择
SUB_OPTIONS = ["📦 数据上传中心", "📚 数据获取教程", "📊 数据质量检查"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
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

    # 教程目录
    st.markdown("### 📋 教程目录")
    cols = st.columns(3)
    for idx, cat in enumerate(DATA_CATEGORIES):
        with cols[idx % 3]:
            st.markdown(f"- [{cat['icon']} {cat['title']}](#{cat['id']})")

    st.markdown("---")

    # 详细教程
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
# 模块三：数据质量检查
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
st.markdown(
    """
    <div style="text-align: center; padding: 20px; opacity: 0.6;">
        <p>数据准备完成后，请前往 <b>Stage 01 任务解读</b> 开始正式工作流</p>
    </div>
    """,
    unsafe_allow_html=True,
)

save_stage_output("00", "data_readiness", {
    "total_categories": readiness["total"],
    "loaded_count": readiness["loaded"],
    "required_loaded": readiness["required_loaded"],
    "is_ready": readiness["is_ready"],
})
