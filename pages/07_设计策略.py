"""阶段 07：设计策略 —— LLM 多主体协商(阶段四) + 共识雷达。"""

import time
import re
import json
import streamlit as st
import plotly.graph_objects as go
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.chart_theme import apply_plotly_polar_theme
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.ui.module_summary import render_stage_summary
from src.engines.llm_engine import call_llm_engine_stream
from src.engines.site_diagnostic_engine import generate_policy_matrix
from src.engines.drawing_prompt_templates import get_templates_by_stage, build_drawing_prompt, generate_drawing_prompt_with_llm
from src.workflow.stage_data_bus import save_stage_output, load_stage_output, render_evidence_chain_bar
from src.utils.runtime_flags import is_demo_mode

st.set_page_config(page_title="07 设计策略", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()
render_engine_status_alert()

render_page_banner(
    title="设计策略",
    description="通过三角色（居民、开发商、规划师）多主体博弈协商，形成带政策依据和空间落位的策略矩阵。",
    eyebrow="Stage 07",
    tags=["三角色协商", "RAG 政策校验", "共识雷达", "策略矩阵"],
)
render_evidence_chain_bar("07", ["05", "06", "07"])

with st.sidebar:
    model_tag = st.text_input("Gemma 4 模型标签", value="gemma4:e2b-it-q4_K_M", key="p7_model")
    temp = st.slider("决策倾向 (Temperature)", 0.0, 1.0, 0.7, key="p7_temp")
    enable_policy = st.checkbox("📜 启用政策合规校验", value=True, key="p7_policy")

SUB_OPTIONS = ["⚖️ 多主体协商推演", "📊 共识雷达", "🖼️ 图纸提示词生成"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

if selected_sub == "⚖️ 多主体协商推演":
    render_section_intro("多主体博弈推演", "让三类角色围绕设计策略展开协商。", eyebrow="LLM Stage 04")

    s3 = st.session_state.get("stage3_output", load_stage_output("06", "design_concept", ""))
    proposal = st.text_area("✍️ 微更新构思或争议点", value=s3[:300] if s3 else "", height=120)

    if enable_policy and proposal:
        with st.expander("📜 政策合规校验 (RAG)", expanded=False):
            matrix = generate_policy_matrix(proposal)
            if matrix:
                for item in matrix:
                    st.markdown(f"**{item['source']}** {item['compliance_note']}")

    if st.button("🚀 开启多方协商推演", use_container_width=True, type="primary"):
        if not proposal:
            st.warning("请输入提案内容。")
        else:
            constraint = "\n\n【红线】：容积率≤1.4，限高≤18m（核心区≤9m），遵守《长春市历史文化名城保护条例》。"
            cot = "\n\n请用【思考过程】展示推理，【正式回复】给出立场，末行<SCORE:数值>打分(0-100)。"
            roles = {
                "🏠 老王": {"system": "你是老王，铁北住了30年的居委会代表。惦记菜市场、看病方便。" + constraint + cot, "color": "#f59e0b"},
                "💰 赵总": {"system": "你是赵总，商业开发运营者。想争取更高容积率但知道1.4红线。" + constraint + cot, "color": "#10b981"},
                "📐 李工": {"system": "你是李工，注册规划师。坚持法定红线，关注天际线视廊。" + constraint + cot, "color": "#6366f1"},
            }
            voting_scores = {}
            memory = ""
            for name, cfg in roles.items():
                st.markdown(f"**{name}**")
                dp = f"针对提案发表看法：\n{proposal}"
                if memory:
                    dp += f"\n\n【其他方观点】：\n{memory}"
                stream = call_llm_engine_stream(prompt=dp, system_prompt=cfg["system"], model=model_tag)
                resp = st.write_stream(stream)
                if isinstance(resp, str):
                    clean = resp.split("【正式回复】")[-1].split("<SCORE:")[0].strip() if "【正式回复】" in resp else resp
                    memory += f"[{name}]: {clean}\n---\n"
                    m = re.search(r"<SCORE:\s*(\d+)\s*>", resp)
                    voting_scores[name] = max(0, min(100, int(m.group(1)) if m else 50))
                time.sleep(0.3)

            st.session_state["p4_voting_scores"] = voting_scores
            save_stage_output("07", "voting_scores", voting_scores)

            sp = f"基于博弈记录生成Markdown表格【问题-策略对应表】：\n{memory[:3000]}\n格式：| 问题 | 策略 | 政策依据 | 空间落位 | 共识度 |"
            stream = call_llm_engine_stream(prompt=sp, system_prompt="高级城市更新研究员。策略须在容积率≤1.4、限高≤18m约束下。", model=model_tag)
            summary = st.write_stream(stream)
            if isinstance(summary, str):
                st.session_state["stage4_output"] = summary
                save_stage_output("07", "strategy_matrix", summary)

elif selected_sub == "📊 共识雷达":
    render_section_intro("动态共识雷达", "查看多主体协商后的共识度分布。", eyebrow="Consensus Radar")
    voting = st.session_state.get("p4_voting_scores", load_stage_output("07", "voting_scores", {}))
    if voting:
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=list(voting.values()) + [list(voting.values())[0]],
            theta=list(voting.keys()) + [list(voting.keys())[0]],
            fill="toself", fillcolor="rgba(99,102,241,0.15)", line=dict(color="#818cf8", width=2),
        ))
        apply_plotly_polar_theme(fig, title="多主体共识度", height=380, radial_range=[0, 100])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("暂无共识数据，请先完成多主体协商推演。")

elif selected_sub == "🖼️ 图纸提示词生成":
    render_section_intro("策略类图纸提示词", "生成更新模式分区图、空间结构规划图等。", eyebrow="Drawing Prompts")
    templates = get_templates_by_stage("07")
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

st.markdown("---")
render_stage_summary(
    stage_code="07",
    title="多方共识与策略矩阵",
    findings=[
        {"point": "三角色（居民/开发商/规划师）围绕更新策略完成多轮协商", "evidence": "LLM 模拟三方立场博弈"},
        {"point": "策略矩阵包含问题-策略-政策依据-空间落位对应关系", "evidence": "协商推演自动汇总"},
    ],
    methodology="基于 Gemma 4 的多主体智能协商推演 + RAG 政策合规预审",
    implication="为总体城市设计（Stage 08）提供了策略框架和空间落位指引",
)
