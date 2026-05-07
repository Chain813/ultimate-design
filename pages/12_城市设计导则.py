"""阶段 12：城市设计导则 —— 两步法 LLM 导则文本生成 + Word 导出。"""

import streamlit as st
from src.ui.design_system import render_page_banner, render_section_intro
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.ui.module_summary import render_stage_summary
from src.engines.llm_engine import call_llm_engine_stream, call_llm_engine
from src.workflow.stage_data_bus import save_stage_output, load_stage_output, render_evidence_chain_bar
from src.ui.streamlit_compat import stretch_width

st.set_page_config(page_title="12 城市设计导则", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()
render_engine_status_alert()

render_page_banner(
    title="城市设计导则",
    description="两步法生成：先梳理导则要素大纲，再扩展为完整导则文本。",
    eyebrow="Stage 12",
    tags=["导则文本", "两步法 LLM", "Word 导出", "管控条文"],
)
render_evidence_chain_bar("12", ["05", "06", "07", "12"])

with st.sidebar:
    model_tag = st.text_input("DeepSeek 模型标签", value="deepseek-v4-pro", key="p12_model")

SUB_OPTIONS = ["📜 导则文本生成", "📊 管控指标汇总"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

if selected_sub == "📜 导则文本生成":
    render_section_intro("规划导则自动生成", "两步法：先生成要素大纲 → 再扩展为完整导则文本。", eyebrow="LLM Two-Step")

    # 加载阶段数据
    s1 = load_stage_output("05", "diagnosis_report", "")
    s2 = load_stage_output("06", "case_benchmark", "")
    s3 = load_stage_output("06", "design_concept", "")
    s4 = load_stage_output("07", "strategy_matrix", "")

    # 加载空间数据
    try:
        from src.engines.spatial_engine import get_hud_statistics, get_skyline_features
        stats = get_hud_statistics()
        skyline = get_skyline_features()
        spatial_stats = (
            f"研究范围面积：{stats.get('boundary_ha', 150)}公顷\n"
            f"建筑总量：{skyline.get('building_count', 0)}栋\n"
            f"平均建筑高度：{skyline.get('avg_height', 0)}米\n"
            f"最高建筑：{skyline.get('max_height', 0)}米\n"
            f"高层建筑占比：{skyline.get('high_rise_ratio', 0)}%\n"
            f"POI数据量：{stats.get('poi_count', 0)}条"
        )
    except Exception:
        spatial_stats = "研究范围约150公顷，建筑约110,289栋"

    # RAG 政策检索
    try:
        from src.engines.guideline_prompt import retrieve_policy_context
        policy_context = retrieve_policy_context("城市更新 历史文化街区 保护 微更新 设计导则")
    except Exception:
        policy_context = ""

    # 状态显示
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("阶段一(诊断)", "✅" if s1 else "❌")
    c2.metric("阶段二(案例)", "✅" if s2 else "❌")
    c3.metric("阶段三(理念)", "✅" if s3 else "❌")
    c4.metric("阶段四(协商)", "✅" if s4 else "❌")

    st.markdown("---")

    # ========== 第一步：生成要素大纲 ==========
    st.markdown("### 第一步：生成导则要素大纲")
    st.caption("基于多阶段数据，梳理每章的核心论点、管控条文、量化指标和政策依据。")

    if st.button("📋 生成要素大纲", type="primary", key="s5_outline_btn", **stretch_width(st.button)):
        from src.engines.guideline_prompt import build_outline_prompt

        outline_prompt = build_outline_prompt(
            diagnosis=s1,
            case_benchmark=s2,
            design_concept=s3,
            strategy_matrix=s4,
            spatial_stats=spatial_stats,
            policy_context=policy_context,
        )

        with st.spinner("第一步：梳理导则要素大纲..."):
            outline_result = call_llm_engine(
                prompt=outline_prompt,
                system_prompt="你是长春市自然资源局首席规划师。请严格按照要求的格式生成要素大纲，每章都要有实质内容。",
                model=model_tag,
            )

        if outline_result and len(outline_result) > 200:
            st.session_state["guideline_outline"] = outline_result
            st.success(f"要素大纲生成完成（{len(outline_result)} 字）")
            with st.expander("📋 查看要素大纲", expanded=True):
                st.markdown(outline_result)
        else:
            st.error("要素大纲生成失败，请重试。")

    # 显示已有的大纲
    if st.session_state.get("guideline_outline"):
        with st.expander("📋 已生成的要素大纲", expanded=False):
            st.markdown(st.session_state["guideline_outline"])

    st.markdown("---")

    # ========== 第二步：扩展为完整文本 ==========
    st.markdown("### 第二步：扩展为完整导则文本")
    st.caption("基于要素大纲，扩展为完整的 10 章导则正文（目标 9200+ 字）。")

    outline = st.session_state.get("guideline_outline", "")

    if not outline:
        st.info("请先完成第一步，生成要素大纲。")
    else:
        if st.button("📄 扩展为完整导则", type="primary", key="s5_expand_btn", **stretch_width(st.button)):
            from src.engines.guideline_prompt import build_expansion_prompt

            expansion_prompt = build_expansion_prompt(
                outline=outline,
                diagnosis=s1,
                case_benchmark=s2,
                design_concept=s3,
                strategy_matrix=s4,
                spatial_stats=spatial_stats,
                policy_context=policy_context,
            )

            with st.spinner("第二步：扩展为完整导则文本（可能需要 1-2 分钟）..."):
                stream = call_llm_engine_stream(
                    prompt=expansion_prompt,
                    system_prompt="你是长春市自然资源局首席规划师。请将要素大纲扩展为完整的、可交付的城市设计导则正文。语言严谨、规范、专业。不得使用占位符。",
                    model=model_tag,
                )
                final = st.write_stream(stream)

            if isinstance(final, str) and len(final) > 500:
                st.session_state["stage5_output"] = final
                save_stage_output("12", "design_guideline", final)
                st.success(f"导则文本生成完成（{len(final)} 字）")

                # 导出按钮
                col_md, col_word = st.columns(2)
                with col_md:
                    report = (
                        f"# 城市设计导则\n\n"
                        f"## 要素大纲\n\n{outline}\n\n"
                        f"## 导则正文\n\n{final}"
                    )
                    st.download_button(
                        "📥 导出完整报告 (Markdown)",
                        report,
                        file_name="城市设计导则.md",
                        use_container_width=True,
                    )
                with col_word:
                    try:
                        from src.utils.document_generator import generate_official_word_doc
                        wb = generate_official_word_doc(
                            title="伪满皇宫周边街区微更新规划导则",
                            text_content=final,
                        )
                        if wb:
                            st.download_button(
                                "📥 导出红头公文 (Word)",
                                wb,
                                file_name="规划导则_红头.docx",
                                use_container_width=True,
                            )
                    except Exception:
                        pass

                st.toast("导则文本生成完成！", icon="📄")
            else:
                st.error("导则文本生成失败或内容过短，请重试。")

    # 显示已有的导则
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
    st.dataframe(pd.DataFrame(indicators), hide_index=True, **stretch_width(st.dataframe))

st.markdown("---")
render_stage_summary(
    stage_code="12",
    title="城市设计导则核心要点",
    findings=[
        {"point": "导则覆盖用地、强度、高度、界面、风貌、公共空间、慢行七大管控维度", "evidence": "城市设计导则标准体系"},
        {"point": "核心区限高≤9m，一般区≤18m，容积率≤1.4", "evidence": "历史文化名城保护规划约束"},
        {"point": "两步法生成：要素大纲 → 完整文本，确保导则质量", "evidence": "LLM 循证推演引擎"},
    ],
    methodology="两步法 LLM 生成：要素大纲 + 完整文本扩展，集成 RAG 政策检索",
    implication="为成果表达（Stage 13）提供了可交付的导则文本和管控指标体系",
)
