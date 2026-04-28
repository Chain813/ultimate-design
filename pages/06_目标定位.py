"""阶段 06：目标定位 —— LLM 案例对标(阶段二) + 设计理念(阶段三)。"""

import os
import streamlit as st
from src.ui.design_system import render_page_banner, render_section_intro
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.ui.module_summary import render_stage_summary
from src.engines.llm_engine import call_llm_engine_stream
from src.workflow.stage_data_bus import save_stage_output, load_stage_output, render_evidence_chain_bar

st.set_page_config(page_title="06 目标定位", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()
render_engine_status_alert()

render_page_banner(
    title="目标定位",
    description="先借鉴国内外案例经验，再融合前期诊断结果提炼设计愿景、目标体系和核心策略。",
    eyebrow="Stage 06",
    tags=["案例借鉴", "设计理念", "目标体系"],
)
render_evidence_chain_bar("06", ["05", "06", "07"])

with st.sidebar:
    model_tag = st.text_input("Gemma 4 模型标签", value="gemma4:e2b-it-q4_K_M", key="p6_model")

SUB_OPTIONS = ["📚 案例对标分析", "💡 设计理念提炼"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

if selected_sub == "📚 案例对标分析":
    render_section_intro("案例对标分析", "读取开题报告案例摘要，与阶段一问题清单做对标。", eyebrow="LLM Stage 02")
    case_context = ""
    case_path = "docs/开题报告_案例摘要.md"
    if os.path.exists(case_path):
        with open(case_path, "r", encoding="utf-8") as f:
            case_context = f.read()
        st.success(f"✅ 已加载案例文件（{len(case_context)} 字）")
    else:
        st.error("❌ 未找到 docs/开题报告_案例摘要.md")

    s1 = st.session_state.get("stage1_output", load_stage_output("05", "diagnosis_report", ""))

    if st.button("📖 生成案例对标报告", type="primary", key="s2_btn"):
        prompt = f"""基于开题报告案例：{case_context[:3000]}
以及阶段一诊断问题：{s1[:2000] if s1 else '用地混杂、交通割裂、老龄化、环境品质匮乏'}
生成【案例对标分析报告】：每个案例含【核心经验】【对标问题】【本地化建议】，最后提炼 3-4 条核心设计原则。"""
        stream = call_llm_engine_stream(prompt=prompt, system_prompt="城市更新比较研究专家。分析紧密结合长春铁北实际。", model=model_tag)
        result = st.write_stream(stream)
        if isinstance(result, str) and len(result) > 50:
            st.session_state["stage2_output"] = result
            save_stage_output("06", "case_benchmark", result)

    if st.session_state.get("stage2_output"):
        st.markdown("#### 📋 案例对标报告")
        st.markdown(st.session_state["stage2_output"])

elif selected_sub == "💡 设计理念提炼":
    render_section_intro("设计理念提炼", "融合前两阶段成果，提炼核心设计理念与策略。", eyebrow="LLM Stage 03")
    s1 = st.session_state.get("stage1_output", "")
    s2 = st.session_state.get("stage2_output", "")

    if st.button("💡 生成设计理念报告", type="primary", key="s3_btn"):
        prompt = f"""基于：
【问题】{s1[:1500] if s1 else '用地混杂、交通割裂、老龄化、环境品质匮乏'}
【案例】{s2[:1500] if s2 else '恩宁路微改造、白塔寺数字织补、国王十字站城融合、巴塞罗那超级街区'}
【主题】"数字孪生·古今共振——AI赋能下的伪满皇宫周边街区更新规划设计"
请生成【设计理念报告】：1个总体理念 + 4条策略（含理论依据、解决问题、案例支撑、空间方向）"""
        stream = call_llm_engine_stream(prompt=prompt, system_prompt="城乡规划学术导师，精通循证规划。", model=model_tag)
        result = st.write_stream(stream)
        if isinstance(result, str) and len(result) > 50:
            st.session_state["stage3_output"] = result
            save_stage_output("06", "design_concept", result)

    if st.session_state.get("stage3_output"):
        st.markdown("#### 📋 设计理念报告")
        st.markdown(st.session_state["stage3_output"])

st.markdown("---")
render_stage_summary(
    stage_code="06",
    title="设计愿景与目标体系",
    findings=[
        {"point": "借鉴广州永庆坊、北京白塔寺、伦敦国王十字等案例经验", "evidence": "开题报告案例摘要数据库"},
        {"point": "提炼'数字孪生·古今共振'的总体设计理念", "evidence": "融合前期诊断与案例对标"},
        {"point": "形成四大设计策略方向：精准感知、风貌生成、路网重构、社会协同", "evidence": "LLM 循证推演"},
    ],
    methodology="基于 Gemma 4 本地大模型的循证推演，融合案例对标与前期诊断",
    implication="为设计策略（Stage 07）的多主体协商提供了理念框架和策略方向",
)
