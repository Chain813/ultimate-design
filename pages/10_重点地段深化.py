"""阶段 10：重点地段深化 —— 地块选择 + 街景透视推演 + Before/After。"""

import streamlit as st
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.ui.module_summary import render_stage_summary
from src.engines.site_diagnostic_engine import get_plot_diagnostics
from src.engines.drawing_prompt_templates import get_templates_by_stage, build_drawing_prompt, generate_drawing_prompt_with_llm
from src.workflow.stage_data_bus import save_stage_output, load_stage_output, render_evidence_chain_bar

st.set_page_config(page_title="10 重点地段深化", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()
render_engine_status_alert()

render_page_banner(
    title="重点地段深化",
    description="选择 5 个重点地块进行节点级深化设计，配合 AIGC 街景透视推演和 Before/After 对比。",
    eyebrow="Stage 10",
    tags=["5 地块深化", "街景推演", "Before/After", "节点效果图"],
)
render_evidence_chain_bar("10", ["08", "09", "10"])

SUB_OPTIONS = ["📍 重点地块选择", "🖼️ 街景透视推演", "🖼️ 图纸提示词生成"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

if selected_sub == "📍 重点地块选择":
    render_section_intro("重点地块选择与诊断", "基于 MPI 排行和专业判断确定 5 个重点深化地块。", eyebrow="Key Plot Selection")

    diags = get_plot_diagnostics()
    if diags:
        render_summary_cards([
            {"value": len(diags), "title": "候选地块", "desc": "来自重点更新单元 GeoJSON"},
        ])

        plot_configs = {
            "站城门户更新地块": {"desc": "交通接驳、门户界面、客流导入", "keywords": ["站", "门户", "入口"]},
            "工业遗产活化地块": {"desc": "厂区改造、文创办公、开放街区", "keywords": ["厂", "工业", "中车"]},
            "老旧社区微更新地块": {"desc": "社区服务、适老设施、口袋公园", "keywords": ["社区", "住宅", "老旧"]},
            "历史风貌协调地块": {"desc": "界面修补、风貌控制、文化展示", "keywords": ["历史", "风貌", "皇宫"]},
            "文旅活力街巷地块": {"desc": "慢行街巷、文创消费、夜间活力", "keywords": ["商业", "街巷", "活力"]},
        }

        for plot_type, cfg in plot_configs.items():
            with st.expander(f"🏷️ {plot_type}", expanded=False):
                st.markdown(f"**定位：** {cfg['desc']}")
                candidates = [d["name"] for d in diags]
                selected = st.selectbox(f"选择地块", candidates, key=f"p10_{plot_type}")
                d = next(dd for dd in diags if dd["name"] == selected)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("MPI", d["mpi_score"])
                c2.metric("POI", d["poi_count"])
                c3.metric("GVI", f"{d['gvi_mean']}%")
                c4.metric("面积", f"{d['area_ha']} ha")
    else:
        st.warning("暂无地块诊断数据。")

elif selected_sub == "🖼️ 街景透视推演":
    render_section_intro("街景透视推演", "使用 AIGC 街区全景透视推演（ControlNet + SD）生成节点效果图。", eyebrow="Street View AIGC")
    st.info("💡 完整的街景透视推演面板（含底图上传、ControlNet 参数、历史画廊）请前往原 **AIGC设计推演** 页面操作。")

elif selected_sub == "🖼️ 图纸提示词生成":
    render_section_intro("深化设计类图纸提示词", "生成节点平面图、街道剖面图、效果图等。", eyebrow="Drawing Prompts")
    with st.sidebar:
        model_tag = st.text_input("Gemma 4 模型标签", value="gemma4:e2b-it-q4_K_M", key="p10_model")
    templates = get_templates_by_stage("10")
    if templates:
        selected_tmpl = st.selectbox("选择图纸模板", [t.name for t in templates])
        tmpl = next(t for t in templates if t.name == selected_tmpl)
        st.markdown(f"**{tmpl.description}**")
        prompt_text, _ = build_drawing_prompt(selected_tmpl)
        st.text_area("数据注入后的提示词", value=prompt_text, height=300)
        if st.button("🧠 调用 Gemma 4 生成", type="primary", use_container_width=True):
            with st.spinner("生成中..."):
                result = generate_drawing_prompt_with_llm(selected_tmpl, model=model_tag)
            st.text_area("完整提示词", value=result, height=400)
    else:
        st.info("暂无本阶段图纸模板。")

st.markdown("---")
diags = get_plot_diagnostics()
avg_mpi = sum(d["mpi_score"] for d in diags) / len(diags) if diags else 0
render_stage_summary(
    stage_code="10",
    title="重点地段深化设计要点",
    findings=[
        {"point": f"共 {len(diags)} 个候选地块，平均 MPI 得分 {avg_mpi:.1f}", "evidence": "地块诊断引擎数据"},
        {"point": "按 5 类主题定位筛选重点地块：站城门户、工业遗产、社区微更新、风貌协调、文旅活力", "evidence": "图册结构要求"},
        {"point": "每个地块配套 AIGC 街景透视推演和 Before/After 效果图", "evidence": "AIGC 推演引擎"},
    ],
    methodology="基于 MPI 排行 + 专业判断的地块筛选，配合 AIGC 节点级推演",
    implication="为实施路径（Stage 11）和城市设计导则（Stage 12）提供了落地设计依据",
)
