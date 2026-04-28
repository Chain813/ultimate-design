"""阶段 12：城市设计导则 —— LLM 导则文本生成(阶段五) + Word 导出。"""

import streamlit as st
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.ui.module_summary import render_stage_summary
from src.engines.llm_engine import call_llm_engine_stream
from src.workflow.stage_data_bus import save_stage_output, load_stage_output, render_evidence_chain_bar

st.set_page_config(page_title="12 城市设计导则", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()
render_engine_status_alert()

render_page_banner(
    title="城市设计导则",
    description="汇总全流程成果，调用 Gemma 4 生成城市设计导则文本，并导出为 Word 公文格式。",
    eyebrow="Stage 12",
    tags=["导则文本", "LLM 汇总", "Word 导出", "管控条文"],
)
render_evidence_chain_bar("12", ["05", "06", "07", "12"])

with st.sidebar:
    model_tag = st.text_input("Gemma 4 模型标签", value="gemma4:e2b-it-q4_K_M", key="p12_model")

SUB_OPTIONS = ["📜 导则文本生成", "📊 管控指标汇总"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

if selected_sub == "📜 导则文本生成":
    render_section_intro("规划导则自动生成", "基于五阶段证据链生成城市设计导则文本。", eyebrow="LLM Stage 05")

    s1 = st.session_state.get("stage1_output", load_stage_output("05", "diagnosis_report", "暂无"))
    s2 = st.session_state.get("stage2_output", load_stage_output("06", "case_benchmark", "暂无"))
    s3 = st.session_state.get("stage3_output", load_stage_output("06", "design_concept", "暂无"))
    s4 = st.session_state.get("stage4_output", load_stage_output("07", "strategy_matrix", "暂无"))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("阶段一(诊断)", "✅" if s1 != "暂无" else "❌")
    c2.metric("阶段二(案例)", "✅" if s2 != "暂无" else "❌")
    c3.metric("阶段三(理念)", "✅" if s3 != "暂无" else "❌")
    c4.metric("阶段四(协商)", "✅" if s4 != "暂无" else "❌")

    if st.button("📄 生成城市设计导则", type="primary", use_container_width=True, key="s5_btn"):
        prompt = f"""基于四阶段证据链生成【城市设计导则成果书】：
【阶段一 问题诊断】{str(s1)[:1000]}
【阶段二 案例对标】{str(s2)[:1000]}
【阶段三 设计理念】{str(s3)[:1000]}
【阶段四 策略协商】{str(s4)[:1000]}

要求：
1. 公文格式(1. 1.1 1.1.1)
2. 含总体定位/现状问题/设计理念/分区策略/管控要求/实施保障
3. 每条策略注明数据和政策依据
4. 容积率≤1.4、限高≤18m"""

        stream = call_llm_engine_stream(
            prompt=prompt,
            system_prompt="长春市自然资源局首席规划师，标准行政公文格式。输出须严谨、规范、可交付。",
            model=model_tag,
        )
        final = st.write_stream(stream)

        if isinstance(final, str) and len(final) > 100:
            st.session_state["stage5_output"] = final
            save_stage_output("12", "design_guideline", final)

            report = f"# 循证规划五阶段成果书\n\n## 阶段一\n{s1}\n\n## 阶段二\n{s2}\n\n## 阶段三\n{s3}\n\n## 阶段四\n{s4}\n\n## 阶段五\n{final}"
            st.download_button("📥 导出完整报告 (Markdown)", report, file_name="五阶段循证报告.md", use_container_width=True)

            try:
                from src.utils.document_generator import generate_official_word_doc
                wb = generate_official_word_doc(title="伪满皇宫周边街区微更新规划导则", text_content=final)
                if wb:
                    st.download_button("📥 导出红头公文 (Word)", wb, file_name="规划导则_红头.docx", use_container_width=True)
            except Exception:
                pass

            st.toast("🎉 导则文本生成完成！", icon="📄")

    if st.session_state.get("stage5_output"):
        with st.expander("📋 当前导则文本", expanded=False):
            st.markdown(st.session_state["stage5_output"])

elif selected_sub == "📊 管控指标汇总":
    render_section_intro("管控指标体系", "汇总城市设计导则的核心管控指标。", eyebrow="Control Indicators")

    import pandas as pd
    indicators = [
        {"管控类型": "用地功能", "管控内容": "主导功能、兼容功能、禁止功能", "控制要求": "混合用地比例≥30%"},
        {"管控类型": "开发强度", "管控内容": "容积率、建筑密度、绿地率", "控制要求": "容积率≤1.4，绿地率≥25%"},
        {"管控类型": "建筑高度", "管控内容": "高度分区、天际线控制", "控制要求": "核心区≤9m，一般区≤18m"},
        {"管控类型": "建筑界面", "管控内容": "街墙连续性、首层开放度", "控制要求": "街墙连续率≥70%"},
        {"管控类型": "建筑风貌", "管控内容": "色彩、材质、屋顶形式", "控制要求": "暖灰色调为主"},
        {"管控类型": "公共空间", "管控内容": "开放空间比例、可达性", "控制要求": "步行5分钟覆盖率≥80%"},
        {"管控类型": "慢行交通", "管控内容": "步行宽度、骑行空间", "控制要求": "人行道≥2m"},
    ]
    st.dataframe(pd.DataFrame(indicators), use_container_width=True, hide_index=True)

st.markdown("---")
render_stage_summary(
    stage_code="12",
    title="城市设计导则核心要点",
    findings=[
        {"point": "导则覆盖用地、强度、高度、界面、风貌、公共空间、慢行七大管控维度", "evidence": "城市设计导则标准体系"},
        {"point": "核心区限高≤9m，一般区≤18m，容积率≤1.4", "evidence": "历史文化名城保护规划约束"},
        {"point": "导则文本由 Gemma 4 基于五阶段证据链自动生成", "evidence": "LLM 循证推演引擎"},
    ],
    methodology="基于五阶段循证推演链路（诊断→案例→理念→协商→导则）的 LLM 汇总",
    implication="为成果表达（Stage 13）提供了可交付的导则文本和管控指标体系",
)
