"""阶段 04：现状分析 —— 3D 全息底座 + POI/交通图层。

引导用户前往 3D 底座查看，同时提供图纸提示词生成。
"""

import streamlit as st
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.ui.module_summary import render_stage_summary
from src.engines.spatial_engine import get_hud_statistics, get_skyline_features
from src.engines.drawing_prompt_templates import get_templates_by_stage, build_drawing_prompt, generate_drawing_prompt_with_llm
from src.workflow.stage_data_bus import save_stage_output, render_evidence_chain_bar

st.set_page_config(page_title="04 现状分析", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

stats = get_hud_statistics()
sky = get_skyline_features()

render_page_banner(
    title="现状分析",
    description="基于 3D 全息底座，综合用地、建筑、交通、POI 和街景品质指标进行空间现状综合分析。",
    eyebrow="Stage 04",
    tags=["3D 数字孪生", "POI 活力", "街景品质", "天际线"],
    metrics=[
        {"value": str(stats.get("poi_count", "N/A")), "label": "POI 记录", "meta": "功能活力测度"},
        {"value": str(sky.get("building_count", 0)), "label": "建筑", "meta": "栋"},
        {"value": f"{sky.get('avg_height', 0)} m", "label": "平均高度", "meta": "建筑形态"},
        {"value": f"{sky.get('high_rise_ratio', 0)}%", "label": "高层占比", "meta": "天际线控制"},
    ],
)
render_evidence_chain_bar("04", ["01", "02", "03", "04", "05"])

SUB_OPTIONS = ["🏙️ 3D 现状全息底座", "🖼️ 图纸提示词生成"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

if selected_sub == "🏙️ 3D 现状全息底座":
    render_section_intro("3D 现状全息底座", "综合建筑体量、用地类型、POI 分布、交通热点和街景品质指标的三维可视化。", eyebrow="Digital Twin")

    render_summary_cards([
        {"value": stats.get("boundary_ha", "~156"), "title": "研究范围", "desc": "公顷"},
        {"value": sky.get("building_count", 0), "title": "建筑总数", "desc": "栋"},
        {"value": f"{sky.get('max_height', 0)} m", "title": "最高建筑", "desc": "天际线峰值"},
        {"value": stats.get("gvi_count", "N/A"), "title": "街景样本", "desc": "GVI/SVF 采样点"},
    ])

    st.info("💡 完整的 3D 交互底座请前往原 **现状空间全景诊断** 页面查看。本页面提供数据概览和图纸生成功能。")

    save_stage_output("04", "poi_count", stats.get("poi_count", 0))
    save_stage_output("04", "building_count", sky.get("building_count", 0))
    save_stage_output("04", "avg_height", sky.get("avg_height", 0))

elif selected_sub == "🖼️ 图纸提示词生成":
    render_section_intro("现状分析类图纸提示词", "基于空间数据生成专业图纸提示词。", eyebrow="Drawing Prompts")
    with st.sidebar:
        model_tag = st.text_input("Gemma 4 模型标签", value="gemma4:e2b-it-q4_K_M", key="p4_model")
    templates = get_templates_by_stage("04")
    if templates:
        selected_tmpl = st.selectbox("选择图纸模板", [t.name for t in templates])
        tmpl = next(t for t in templates if t.name == selected_tmpl)
        st.markdown(f"**{tmpl.description}**")
        prompt_text, _ = build_drawing_prompt(selected_tmpl)
        st.text_area("数据注入后的提示词", value=prompt_text, height=300)
        if st.button("🧠 调用 Gemma 4 生成", type="primary", use_container_width=True):
            with st.spinner("生成中..."):
                result = generate_drawing_prompt_with_llm(selected_tmpl, model=model_tag)
            st.text_area("完整 Image 2.0 提示词", value=result, height=400)
    else:
        st.info("暂无本阶段图纸模板。")

st.markdown("---")
render_stage_summary(
    stage_code="04",
    title="现状空间特征综述",
    findings=[
        {"point": f"研究范围内共 {sky.get('building_count', 0)} 栋建筑，平均高度 {sky.get('avg_height', 0)} 米", "evidence": "建筑底图 GeoJSON 空间分析"},
        {"point": f"高层建筑（≥24m）占比 {sky.get('high_rise_ratio', 0)}%，片区以低层和多层为主", "evidence": "天际线形态分析"},
        {"point": f"POI 设施 {stats.get('poi_count', 'N/A')} 条，街景采样点 {stats.get('gvi_count', 'N/A')} 个", "evidence": "空间引擎 HUD 统计"},
    ],
    methodology="基于 GIS 空间数据和街景图像的多源融合分析",
    implication="为问题诊断（Stage 05）提供了现状空间特征的定量基础",
)
