"""阶段 09：专项系统设计 —— 轴测鸟瞰 + 3D 专项叠合 + 图纸提示词。"""

import streamlit as st
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.ui.module_summary import render_stage_summary
from src.engines.drawing_prompt_templates import get_templates_by_stage, build_drawing_prompt, generate_drawing_prompt_with_llm
from src.engines.spatial_engine import get_hud_statistics, get_skyline_features
from src.workflow.stage_data_bus import render_evidence_chain_bar

st.set_page_config(page_title="09 专项系统设计", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()
render_engine_status_alert()

stats = get_hud_statistics()
sky = get_skyline_features()

render_page_banner(
    title="专项系统设计",
    description="深化交通、公共空间、建筑形态和风貌景观等专项系统设计，配合轴测鸟瞰体块推演和图纸提示词生成。",
    eyebrow="Stage 09",
    tags=["交通系统", "公共空间", "风貌控制", "轴测推演", "图纸生成"],
    metrics=[
        {"value": str(stats.get("poi_count", "N/A")), "label": "POI", "meta": "活力测度"},
        {"value": f"{sky.get('avg_height', 0)} m", "label": "平均层高", "meta": "形态控制"},
        {"value": f"{sky.get('high_rise_ratio', 0)}%", "label": "高层占比", "meta": "天际线"},
    ],
)
render_evidence_chain_bar("09", ["08", "09", "10"])

SUB_OPTIONS = ["🏗️ 轴测鸟瞰体块模拟", "📐 专项系统分析", "🖼️ 图纸提示词生成"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

if selected_sub == "🏗️ 轴测鸟瞰体块模拟":
    render_section_intro("轴测鸟瞰空间体块模拟", "使用 AIGC 推演建筑体量和空间围合关系。", eyebrow="Axonometric Simulation")
    render_summary_cards([
        {"value": sky.get("building_count", 0), "title": "建筑", "desc": "栋"},
        {"value": f"{sky.get('max_height', 0)} m", "title": "最高", "desc": "天际线峰值"},
    ])
    st.info("💡 完整的轴测鸟瞰推演面板请前往原 **AIGC设计推演** 页面操作。")

elif selected_sub == "📐 专项系统分析":
    render_section_intro("专项系统空间叠合", "在 3D 底座上按专项系统切换图层分析。", eyebrow="System Overlay")

    systems = {
        "🚗 交通系统": {"desc": "道路等级、公交站点、停车设施、慢行网络", "layers": ["道路等级", "交通热点", "公交覆盖"]},
        "🌳 公共空间系统": {"desc": "公园、广场、街角空间、口袋公园", "layers": ["绿地分布", "公共空间节点", "服务半径"]},
        "🏛️ 建筑形态控制": {"desc": "高度分区、密度控制、街墙界面", "layers": ["建筑高度", "天际线", "界面连续性"]},
        "🎨 风貌景观": {"desc": "风貌分区、色彩控制、历史界面", "layers": ["风貌分类", "历史保护区", "视线通廊"]},
    }

    for sys_name, sys_info in systems.items():
        with st.expander(sys_name, expanded=False):
            st.markdown(f"**分析内容：** {sys_info['desc']}")
            st.markdown(f"**可用图层：** {' · '.join(sys_info['layers'])}")
            st.info("前往 3D 底座页面叠合查看具体空间分布。")

elif selected_sub == "🖼️ 图纸提示词生成":
    render_section_intro("专项系统图纸提示词", "生成道路交通、慢行系统、公共空间、历史文化展示等专项图纸。", eyebrow="Drawing Prompts")
    with st.sidebar:
        model_tag = st.text_input("Gemma 4 模型标签", value="gemma4:e2b-it-q4_K_M", key="p9_model")

    templates = get_templates_by_stage("09")
    if templates:
        selected_tmpl = st.selectbox("选择图纸模板", [t.name for t in templates])
        tmpl = next(t for t in templates if t.name == selected_tmpl)
        st.markdown(f"**图纸说明：** {tmpl.description}")
        prompt_text, _ = build_drawing_prompt(selected_tmpl)
        st.text_area("数据注入后的提示词", value=prompt_text, height=300)
        if st.button("🧠 调用 Gemma 4 生成", type="primary", use_container_width=True):
            with st.spinner("生成中..."):
                result = generate_drawing_prompt_with_llm(selected_tmpl, model=model_tag)
            st.text_area("完整 Image 2.0 提示词", value=result, height=400)
            st.download_button("📥 下载", result, file_name=f"{selected_tmpl}_prompt.md", mime="text/markdown", use_container_width=True)
    else:
        st.info("暂无本阶段图纸模板。")

st.markdown("---")
render_stage_summary(
    stage_code="09",
    title="专项系统叠合分析",
    findings=[
        {"point": f"建筑形态以低层多层为主，高层占比 {sky.get('high_rise_ratio', 0)}%", "evidence": "建筑底图空间分析"},
        {"point": f"POI 设施 {stats.get('poi_count', 'N/A')} 处，反映公共服务分布不均", "evidence": "POI 双源融合数据"},
        {"point": "道路交通、公共空间、风貌控制四大专项系统已建立分析框架", "evidence": "基于 3D 底座图层叠合"},
    ],
    methodology="基于 GIS 空间叠合分析与 AIGC 轴测推演",
    implication="为重点地段深化（Stage 10）提供了专项系统的空间约束和设计导引",
)
