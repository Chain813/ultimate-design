"""阶段 07：设计策略 —— 多主体协同良性循环推演 + 共识雷达。

三方角色（居民代表、开发运营商、规划师）不再产生对立冲突，
而是围绕"政策引导→产业导入→经济反哺→空间更新"的良性循环展开协同推演。

所有讨论都必须基于 Stage 05/06 的量化空间数据。
"""

import time
import re
import streamlit as st
import plotly.graph_objects as go
from src.ui.design_system import render_page_banner, render_section_intro
from src.ui.chart_theme import apply_plotly_polar_theme
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.ui.module_summary import render_stage_summary
from src.engines.llm_engine import call_llm_engine_stream
from src.engines.site_diagnostic_engine import generate_policy_matrix
from src.engines.spatial_data_injector import (
    get_full_spatial_context,
    get_landuse_summary,
    get_key_plots_summary,
)
from src.workflow.stage_data_bus import (
    save_stage_output, load_stage_output, render_evidence_chain_bar,
)
from src.workflow.stage_keys import SK
from src.ui.drawing_prompt_ui import render_drawing_prompt_ui
from src.ui.streamlit_compat import stretch_width

st.set_page_config(page_title="07 设计策略", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()
render_engine_status_alert()

graphic_svg = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 200" width="100%" height="100%" style="max-width: 600px; filter: drop-shadow(0 15px 25px rgba(0,0,0,0.3));">
  <defs>
    <linearGradient id="g_base" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="rgba(30, 41, 59, 0.6)"/>
      <stop offset="100%" stop-color="rgba(15, 23, 42, 0.8)"/>
    </linearGradient>
    <linearGradient id="g_out" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="rgba(16, 185, 129, 0.15)"/>
      <stop offset="100%" stop-color="rgba(15, 23, 42, 0.9)"/>
    </linearGradient>
    
    <filter id="f_cyan" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="5" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
    <filter id="f_indigo" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="5" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
    <filter id="f_emerald" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="5" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>

  <!-- Left Side: Stacked Roles to Center Loop -->
  <path d="M 150 45 C 185 45, 175 100, 200 100" fill="none" stroke="#475569" stroke-width="1.5" stroke-dasharray="4,3"/>
  <path d="M 150 100 L 200 100" fill="none" stroke="#38bdf8" stroke-width="2" stroke-dasharray="5,4" filter="url(#f_cyan)"/>
  <path d="M 150 155 C 185 155, 175 100, 200 100" fill="none" stroke="#475569" stroke-width="1.5" stroke-dasharray="4,3"/>

  <!-- Left Stacked Role Nodes -->
  <rect x="10" y="25" width="140" height="40" rx="6" fill="url(#g_base)" stroke="#334155" stroke-width="1"/>
  <text x="80" y="42" fill="#38bdf8" font-size="12" font-family="sans-serif" text-anchor="middle" font-weight="bold">居民代表</text>
  <text x="80" y="56" fill="#94a3b8" font-size="10" font-family="sans-serif" text-anchor="middle">权益与民生诉求</text>

  <rect x="10" y="80" width="140" height="40" rx="6" fill="url(#g_base)" stroke="#38bdf8" stroke-width="1.5" filter="url(#f_cyan)"/>
  <text x="80" y="97" fill="#e2e8f0" font-size="12" font-family="sans-serif" text-anchor="middle" font-weight="bold">开发运营商</text>
  <text x="80" y="111" fill="#bae6fd" font-size="10" font-family="sans-serif" text-anchor="middle">资本与产业导入</text>

  <rect x="10" y="135" width="140" height="40" rx="6" fill="url(#g_base)" stroke="#334155" stroke-width="1"/>
  <text x="80" y="152" fill="#38bdf8" font-size="12" font-family="sans-serif" text-anchor="middle" font-weight="bold">专业规划师</text>
  <text x="80" y="166" fill="#94a3b8" font-size="10" font-family="sans-serif" text-anchor="middle">空间与合规控制</text>

  <!-- Center Loop Track -->
  <path d="M 350 37 L 455 100 L 350 163 L 245 100 Z" fill="none" stroke="#6366f1" stroke-width="2" stroke-dasharray="5,4" filter="url(#f_indigo)"/>
  
  <!-- Loop Direction Arrows -->
  <polygon points="402,65 406,72 397,71" fill="#6366f1"/>
  <polygon points="402,135 397,129 406,128" fill="#6366f1"/>
  <polygon points="297,135 293,128 302,129" fill="#6366f1"/>
  <polygon points="297,65 302,71 293,72" fill="#6366f1"/>

  <!-- Loop Nodes -->
  <rect x="290" y="20" width="120" height="34" rx="6" fill="url(#g_base)" stroke="#6366f1" stroke-width="1"/>
  <text x="350" y="41" fill="#e2e8f0" font-size="11" font-family="sans-serif" text-anchor="middle" font-weight="bold">政策引导 (RAG)</text>

  <rect x="410" y="83" width="90" height="34" rx="6" fill="url(#g_base)" stroke="#6366f1" stroke-width="1"/>
  <text x="455" y="104" fill="#e2e8f0" font-size="11" font-family="sans-serif" text-anchor="middle" font-weight="bold">产业导入</text>

  <rect x="290" y="146" width="120" height="34" rx="6" fill="url(#g_base)" stroke="#6366f1" stroke-width="1"/>
  <text x="350" y="167" fill="#e2e8f0" font-size="11" font-family="sans-serif" text-anchor="middle" font-weight="bold">经济盘活 (反哺)</text>

  <rect x="200" y="83" width="90" height="34" rx="6" fill="url(#g_base)" stroke="#6366f1" stroke-width="1"/>
  <text x="245" y="104" fill="#e2e8f0" font-size="11" font-family="sans-serif" text-anchor="middle" font-weight="bold">空间更新</text>

  <!-- Connection: Center Loop to Right Output -->
  <path d="M 500 100 L 540 100" fill="none" stroke="#10b981" stroke-width="2" stroke-dasharray="5,4" filter="url(#f_emerald)"/>
  <polygon points="535,96 540,100 535,104" fill="#10b981"/>

  <!-- Right Output Card -->
  <rect x="540" y="40" width="130" height="120" rx="10" fill="url(#g_out)" stroke="#10b981" stroke-width="2" filter="url(#f_emerald)"/>
  <text x="605" y="65" fill="#10b981" font-size="13" font-family="sans-serif" text-anchor="middle" font-weight="bold">策略共识矩阵</text>
  <text x="605" y="90" fill="#e2e8f0" font-size="10" font-family="sans-serif" text-anchor="middle">✓ 带政策依据 (RAG)</text>
  <text x="605" y="110" fill="#e2e8f0" font-size="10" font-family="sans-serif" text-anchor="middle">✓ 空间精确落位</text>
  <text x="605" y="130" fill="#e2e8f0" font-size="10" font-family="sans-serif" text-anchor="middle">✓ 三方利益最优解</text>

  <circle cx="150" cy="100" r="4" fill="#38bdf8"/>
  <circle cx="200" cy="100" r="4" fill="#38bdf8"/>
</svg>
"""

render_page_banner(
    title="设计策略",
    description="三方角色（居民/运营商/规划师）围绕'政策引导→产业导入→经济盘活→空间更新'"
                "的良性循环展开协同推演，形成带政策依据 and 空间落位的策略矩阵。",
    eyebrow="Stage 07",
    tags=["政经良性循环", "三方协同", "RAG 政策校验", "策略矩阵"],
    graphic_html=graphic_svg
)
render_evidence_chain_bar("07", ["05", "06", "07"])

with st.sidebar:
    model_tag = st.selectbox(
        "DeepSeek 模型",
        ["deepseek-v4-flash", "deepseek-v4-pro"],
        index=1,
        key="p7_model",
    )
    temp = st.slider("决策倾向 (Temperature)", 0.0, 1.0, 0.7, key="p7_temp")
    enable_policy = st.checkbox("📜 启用政策合规校验", value=True, key="p7_policy")

SUB_OPTIONS = ["⚖️ 多主体协同推演", "📊 共识雷达", "🖼️ 图纸提示词生成"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")


if selected_sub == "⚖️ 多主体协同推演":
    render_section_intro(
        "政策-经济-空间良性循环推演",
        "三方角色不再对立冲突，而是围绕如何利用伪满皇宫文化IP、"
        "盘活区域经济、反哺全域公共空间展开协同策划。",
        eyebrow="Synergistic Loop",
    )

    # 加载上游数据
    s3 = st.session_state.get(
        "stage3_output",
        load_stage_output("06", SK.DESIGN_CONCEPT, ""),
    )

    # 显示空间数据约束
    with st.expander("📊 本轮推演的空间数据约束", expanded=False):
        st.text(get_landuse_summary())
        st.text(get_key_plots_summary())

    # 策划议题：基于上游目标自动生成
    default_proposal = ""
    if s3:
        default_proposal = s3[:300]
    proposal = st.text_area(
        "✍️ 策划议题（基于 Stage 06 设计目标自动填充，可修改）",
        value=default_proposal if default_proposal else
              "如何利用伪满皇宫文化IP与区位优势，通过政策引导、产业导入和空间更新的协同，"
              "盘活整个研究范围的经济活力，并使其辐射至全区乃至全城？",
        height=120,
    )

    if enable_policy and proposal:
        with st.expander("📜 政策合规校验 (RAG)", expanded=False):
            matrix = generate_policy_matrix(proposal)
            if matrix:
                for item in matrix:
                    st.markdown(f"**{item['source']}** {item['compliance_note']}")

    if st.button("🚀 开启三方协同推演", type="primary", **stretch_width(st.button)):
        if not proposal:
            st.warning("请输入策划议题。")
        else:
            spatial_ctx = get_full_spatial_context()

            # 各方角色共享的空间背景
            shared_context = (
                f"\n\n【研究范围空间数据约束】：\n{spatial_ctx[:2500]}"
                f"\n\n【上游设计目标】：\n{s3[:1500] if s3 else '暂无'}"
                f"\n\n【红线】：容积率≤1.4，核心区限高≤9m，一般区限高≤18m，遵守《长春市历史文化名城保护条例》。"
            )
            cot = ("\n\n请用【思考过程】展示推理，【正式回复】给出建设性方案，"
                   "末行<SCORE:数值>打分(0-100)表示对方案的支持度。"
                   "注意：三方立场是相辅相成的，共同推动良性循环。")

            roles = {
                "🏠 居民代表（老王）": {
                    "system": (
                        "你是老王，在伪满皇宫周边住了30年的社区代表。"
                        "你支持改造，期盼更好的菜市场、社区医院和绿化。"
                        "你关注政策如何让改造惠及原住民、改善老年人生活。"
                        "你的立场是与开发商和规划师协同合作，共同推动社区更新。"
                        + shared_context + cot
                    ),
                    "color": "#f59e0b",
                },
                "💰 文旅运营商（赵总）": {
                    "system": (
                        "你是赵总，专注文旅商业运营的企业家。"
                        "你看好伪满皇宫的文化IP和区位价值。"
                        "你想导入文创品牌、特色餐饮和精品民宿。"
                        "你理解容积率1.4的红线约束，但你认为通过文旅品牌溢价可以实现投资回报。"
                        "你的核心观点是'政策引导+产业导入→经济盘活→反哺公共空间'的良性循环。"
                        "你与居民和规划师相辅相成，共同构建可持续运营模式。"
                        + shared_context + cot
                    ),
                    "color": "#10b981",
                },
                "📐 规划师（李工）": {
                    "system": (
                        "你是李工，注册规划师，精通城市更新法规和空间分析。"
                        "你基于空间数据进行科学研判，关注天际线视廊保护和历史风貌。"
                        "你认为通过精准的政策工具（如历史风貌保护红利、文旅税收优惠）"
                        "可以引导开发商和居民实现共赢。"
                        "你的任务是将各方诉求整合为有法定依据、有空间落位的策略。"
                        "你与居民和运营商相辅相成，确保方案既合规又可行。"
                        + shared_context + cot
                    ),
                    "color": "#6366f1",
                },
            }
            voting_scores = {}
            memory = ""
            for name, cfg in roles.items():
                st.markdown(f"**{name}**")
                dp = f"针对以下策划议题发表建设性方案：\n{proposal}"
                if memory:
                    dp += f"\n\n【其他方的建设性方案】：\n{memory}"
                stream = call_llm_engine_stream(
                    prompt=dp, system_prompt=cfg["system"], model=model_tag,
                )
                resp = st.write_stream(stream)
                if isinstance(resp, str):
                    clean = (
                        resp.split("【正式回复】")[-1].split("<SCORE:")[0].strip()
                        if "【正式回复】" in resp else resp
                    )
                    memory += f"[{name}]: {clean}\n---\n"
                    m = re.search(r"<SCORE:\s*(\d+)\s*>", resp)
                    voting_scores[name] = max(0, min(100, int(m.group(1)) if m else 50))
                time.sleep(0.3)

            st.session_state["p4_voting_scores"] = voting_scores
            save_stage_output("07", SK.VOTING_SCORES, voting_scores)

            # 生成策略矩阵
            sp = (
                f"基于三方协同推演记录，生成Markdown表格【策略矩阵】：\n{memory[:3000]}\n\n"
                f"格式：| 策略方向 | 具体举措 | 政策依据 | 空间落位 | 资金逻辑 | 协同度 |\n\n"
                f"要求：\n"
                f"1. 每条策略必须有明确的空间落位（具体到哪个地块或哪条路段）\n"
                f"2. 必须体现'政策→产业→经济→空间'的良性循环逻辑\n"
                f"3. 各方立场相辅相成，不得有冲突条目"
            )
            stream = call_llm_engine_stream(
                prompt=sp,
                system_prompt=(
                    "资深城市更新策划师。策略须在容积率≤1.4、"
                    "核心区限高≤9m约束下，构建政策-经济-空间的良性循环。"
                ),
                model=model_tag,
            )
            summary = st.write_stream(stream)
            if isinstance(summary, str):
                st.session_state["stage4_output"] = summary
                save_stage_output("07", SK.STRATEGY_MATRIX, summary)

elif selected_sub == "📊 共识雷达":
    render_section_intro("动态共识雷达", "查看三方协同推演后的共识度分布。", eyebrow="Consensus Radar")
    voting = st.session_state.get(
        "p4_voting_scores", load_stage_output("07", SK.VOTING_SCORES, {}),
    )
    if voting:
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=list(voting.values()) + [list(voting.values())[0]],
            theta=list(voting.keys()) + [list(voting.keys())[0]],
            fill="toself",
            fillcolor="rgba(99,102,241,0.15)",
            line=dict(color="#818cf8", width=2),
        ))
        apply_plotly_polar_theme(fig, title="三方协同共识度", height=380, radial_range=[0, 100])
        st.plotly_chart(fig, **stretch_width(st.plotly_chart))
    else:
        st.warning("暂无共识数据，请先完成多主体协同推演。")

elif selected_sub == "🖼️ 图纸提示词生成":
    render_drawing_prompt_ui("07", key_prefix="p7", stage_title="设计策略")


st.markdown("---")
render_stage_summary(
    stage_code="07",
    title="三方协同策略矩阵与良性循环",
    findings=[
        {"point": "三方角色（居民/运营商/规划师）围绕文化IP经济盘活展开协同策划", "evidence": "LLM 三方协同推演"},
        {"point": "策略矩阵包含策略-举措-政策依据-空间落位-资金逻辑对应关系", "evidence": "协同推演自动汇总"},
        {"point": "构建'政策精准引导→文旅产业导入→经济反哺公共空间→人居价值双提升'闭环", "evidence": "全域空间数据驱动"},
    ],
    methodology="基于 DeepSeek API 的三方协同推演 + RAG 政策合规预审 + 全域空间数据注入",
    implication="为总体城市设计（Stage 08）提供了策略框架、空间落位指引和政策-经济闭环逻辑",
)
