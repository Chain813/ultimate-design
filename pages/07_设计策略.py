"""阶段 07：设计策略 —— 多主体多轮博弈协商推演 + 共识雷达。

三方角色（居民代表、开发运营商、规划师）围绕"政策引导→产业导入→经济反哺→空间更新"
的良性循环展开 **3 轮动态博弈协商**（陈述→交锋→妥协），最终形成带政策依据的策略矩阵。

所有讨论都必须基于 Stage 05/06 的量化空间数据。
"""

import base64
import time
import re
from pathlib import Path
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
        "三轮动态博弈协商推演",
        "三方角色（居民/运营商/规划师）围绕伪满皇宫文化IP与区域经济盘活，"
        "展开 3 轮递进式博弈协商：**陈述→交锋→妥协**，最终形成带政策依据的策略矩阵。",
        eyebrow="Multi-Round Negotiation",
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

    # 加载已有的历史对话
    saved_dialogues = load_stage_output("07", "negotiation_dialogues", [])

    run_negotiation = False
    if not saved_dialogues:
        if st.button("🚀 开启三方协同推演", type="primary", **stretch_width(st.button)):
            run_negotiation = True
    elif st.session_state.get("p7_running_negotiation", False):
        run_negotiation = True
    else:
        st.info("💡 已加载历史推演记录。如果您想重新生成，请点击下方的“重新开启推演”按钮。")
        current_round = ""
        for item in saved_dialogues:
            if item["round_label"] != current_round:
                current_round = item["round_label"]
                st.subheader(f"🔄 {current_round}")
            _render_dialogue_static(item["name"], item.get("thinking", ""), item["formal"], item["round_label"])
            
        if st.button("🔄 重新开启三方协同推演", type="secondary", **stretch_width(st.button)):
            save_stage_output("07", "negotiation_dialogues", [])
            st.session_state["p7_running_negotiation"] = True
            st.rerun()

    if run_negotiation:
        if not proposal:
            st.warning("请输入策划议题。")
            st.session_state["p7_running_negotiation"] = False
        else:
            spatial_ctx = get_full_spatial_context()

            # 注入客户端 MutationObserver 自动向下滑动脚本（仅在推演运行期间有效）
            st.markdown("""
            <script>
                const observer = new MutationObserver(() => {
                    const scrollTarget = window.parent.document.querySelector('.stMain') || window.parent.document.querySelector('.main') || window.parent;
                    if (scrollTarget) {
                        scrollTarget.scrollTop = scrollTarget.scrollHeight;
                    }
                });
                observer.observe(document.body, { childList: true, subtree: true });
            </script>
            """, unsafe_allow_html=True)

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
            # 动态满意度计算逻辑
            def calculate_dynamic_satisfaction(memory_text: str):
                scores = {
                    "👥 居民代表（老王）": 50.0,
                    "💰 文旅运营商（赵总）": 50.0,
                    "📐 规划师（李工）": 50.0
                }
                # 尝试通过 LLM 语义评分
                try:
                    from src.engines.llm_engine import call_llm_engine
                    from src.utils.llm_json_parser import parse_llm_json
                    
                    prompt = f"""
                    分析以下三个主体关于城市更新协商的对话文本，从语义上评估三方角色对当前方案的满意度得分（0-100分）。
                    
                    各方利益关注点：
                    - 👥 居民代表：绿化、配套、生活便利、社区医疗、菜场养老等民生品质。
                    - 💰 文旅运营商：投资回报、文旅商业品牌、容积率可行性、经济收益及活化运营。
                    - 📐 规划师：历史文化名城保护、限高合规、视廊控制、指标红线合规。
                    
                    协商对话文本：
                    {memory_text}
                    
                    请严格评估三方当前的态度是否在朝良性合作发展，计算出合理的分数。初始分为 50 分。每条满足或推进该角色利益的合理方案加分，损害利益的方案扣分。
                    请仅返回 JSON 格式结果，不要包含任何 markdown 块或多余文字：
                    {{
                        "👥 居民代表（老王）": 分数(数字),
                        "💰 文旅运营商（赵总）": 分数(数字),
                        "📐 规划师（李工）": 分数(数字)
                    }}
                    """
                    resp = call_llm_engine(prompt=prompt, system_prompt="你是一位客观的城市规划博弈审计员。", model="deepseek-v4-flash")
                    parsed = parse_llm_json(resp, fallback=None)
                    if parsed and isinstance(parsed, dict):
                        valid = True
                        for k in scores.keys():
                            if k not in parsed or not isinstance(parsed[k], (int, float)):
                                valid = False
                        if valid:
                            return {k: min(100.0, max(0.0, float(parsed[k]))) for k in scores.keys()}
                except Exception:
                    pass

                # 降级退回到关键词匹配
                community_keywords = ["绿", "公园", "配套", "社区", "医院", "菜市", "养老", "口袋", "老年", "居民", "人行道", "活动", "活动中心", "休憩"]
                developer_keywords = ["容积率", "收益", "文旅", "商业", "民宿", "运营", "产业", "投资", "回报", "品牌", "特色餐饮", "盈利", "客流", "商铺"]
                planner_keywords = ["历史保护", "紫线", "限高", "合规", "风貌", "条例", "保护区", "天际线", "视廊", "数据", "红线", "导则", "退让", "绿地率"]
                
                for kw in community_keywords:
                    if kw in memory_text:
                        scores["👥 居民代表（老王）"] += 7.0
                for kw in developer_keywords:
                    if kw in memory_text:
                        scores["💰 文旅运营商（赵总）"] += 7.0
                for kw in planner_keywords:
                    if kw in memory_text:
                        scores["📐 规划师（李工）"] += 7.0
                        
                for k in scores:
                    scores[k] = min(100.0, max(0.0, scores[k]))
                return scores

            # ── 头像加载 ──
            _avatar_dir = Path("static/avatars")
            _avatar_map = {
                "🏠 居民代表（老王）": _avatar_dir / "avatar_laowang.png",
                "💰 文旅运营商（赵总）": _avatar_dir / "avatar_zhaozong.png",
                "📐 规划师（李工）": _avatar_dir / "avatar_ligong.png",
            }
            _color_map = {
                "🏠 居民代表（老王）": ("#f59e0b", "#fffbeb", "#b45309"),
                "💰 文旅运营商（赵总）": ("#10b981", "#ecfdf5", "#065f46"),
                "📐 规划师（李工）": ("#6366f1", "#eef2ff", "#3730a3"),
            }

            def _load_avatar_b64(path: Path) -> str:
                if path.exists():
                    return base64.b64encode(path.read_bytes()).decode()
                return ""

            def _render_dialogue(name: str, text: str, round_label: str):
                border_c, bg_c, text_c = _color_map.get(name, ("#94a3b8", "#f8fafc", "#334155"))
                avatar_b64 = _load_avatar_b64(_avatar_map.get(name, Path("")))
                avatar_html = (
                    f'<img src="data:image/png;base64,{avatar_b64}" '
                    f'style="width:52px;height:52px;border-radius:50%;object-fit:cover;'
                    f'border:2px solid {border_c};flex-shrink:0;" />'
                ) if avatar_b64 else f'<div style="width:52px;height:52px;border-radius:50%;background:{border_c};flex-shrink:0;"></div>'
                st.markdown(f"""
                <div style="display:flex;gap:14px;align-items:flex-start;margin-bottom:18px;">
                    {avatar_html}
                    <div style="flex:1;background:{bg_c};border-left:4px solid {border_c};
                                border-radius:8px;padding:14px 18px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                        <div style="font-weight:700;color:{text_c};font-size:1.05em;margin-bottom:4px;">
                            {name} <span style="font-size:0.8em;color:#94a3b8;font-weight:400;">· {round_label}</span>
                        </div>
                        <div style="color:#1e293b;font-size:0.95em;line-height:1.65;">{text}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # ── 多轮博弈主循环 ──
            NUM_ROUNDS = 3
            ROUND_LABELS = ["第一轮：方案陈述", "第二轮：利益交锋", "第三轮：妥协共识"]
            ROUND_INSTRUCTIONS = [
                "请基于策划议题提出你的初步方案与核心利益诉求。",
                "请阅读前一轮各方的方案，指出你认为的核心冲突焦点，并表达你的交锋意见。",
                "请基于前两轮的讨论，提出具体的折中妥协条件（例如用配建公共设施换取指标让步），给出你的最终支持度。",
            ]

            def parse_streaming_text(raw_text: str):
                thinking_part = ""
                formal_part = ""
                if "【正式回复】" in raw_text:
                    parts = raw_text.split("【正式回复】", 1)
                    thinking_part = parts[0].replace("【思考过程】", "").strip()
                    formal_part = parts[1].strip()
                elif "【思考过程】" in raw_text:
                    thinking_part = raw_text.replace("【思考过程】", "").strip()
                else:
                    thinking_part = raw_text.strip()
                return thinking_part, formal_part

            def md_to_html(text: str) -> str:
                if not text:
                    return ""
                # Convert ***text*** or ___text___ to <strong><em>text</em></strong>
                text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<strong><em>\1</em></strong>', text)
                text = re.sub(r'___(.*?)___', r'<strong><em>\1</em></strong>', text)
                # Convert **text** or __text__ to <strong>text</strong>
                text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
                text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', text)
                # Convert *text* or _text_ to <em>text</em>
                text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
                text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)
                # Convert `code` to <code>
                text = re.sub(r'`(.*?)`', r'<code style="background:rgba(0,0,0,0.05);padding:2px 4px;border-radius:3px;font-family:monospace;">\1</code>', text)
                return text

            def _render_dialogue_streaming(ph, name: str, thinking: str, formal: str, round_label: str):
                # 兼容性：模糊匹配名称，加载正确的配色和头像
                norm_name = name
                for k in _color_map.keys():
                    if k in name or name in k or re.sub(r'[^\w\u4e00-\u9fa5]', '', k) == re.sub(r'[^\w\u4e00-\u9fa5]', '', name):
                        norm_name = k
                        break

                border_c, bg_c, text_c = _color_map.get(norm_name, ("#94a3b8", "#f8fafc", "#334155"))
                avatar_b64 = _load_avatar_b64(_avatar_map.get(norm_name, Path("")))
                avatar_html = (
                    f'<img src="data:image/png;base64,{avatar_b64}" '
                    f'style="width:52px;height:52px;border-radius:50%;object-fit:cover;'
                    f'border:2px solid {border_c};flex-shrink:0;" />'
                ) if avatar_b64 else f'<div style="width:52px;height:52px;border-radius:50%;background:{border_c};flex-shrink:0;"></div>'

                thinking_html = ""
                if thinking:
                    thinking_formatted = md_to_html(thinking).replace("\n", "<br>")
                    thinking_html = (
                        f'<div style="font-size:11px;color:#64748b;background-color:rgba(0,0,0,0.02);'
                        f'border-left:3px solid #cbd5e1;padding:6px 10px;margin-bottom:8px;border-radius:4px;font-style:italic;">'
                        f'<span style="font-weight:bold;font-style:normal;color:#475569;display:block;'
                        f'margin-bottom:2px;font-size:10px;letter-spacing:0.05em;">💭 思考过程 (Thinking Process)</span>'
                        f'{thinking_formatted}'
                        f'</div>'
                    )

                formal_formatted = md_to_html(formal).replace("\n", "<br>") if formal else "<i>正在思考中...</i>"

                scroll_script = (
                    f'<script>'
                    f'var scrollTarget = window.parent.document.querySelector(".stMain") || window.parent.document.querySelector(".main") || window.parent;'
                    f'if (scrollTarget) {{'
                    f'scrollTarget.scrollTop = scrollTarget.scrollHeight;'
                    f'}}'
                    f'</script>'
                )

                html_content = (
                    f'<div style="display:flex;gap:14px;align-items:flex-start;margin-bottom:18px;">'
                    f'{avatar_html}'
                    f'<div style="flex:1;background:{bg_c};border-left:4px solid {border_c};'
                    f'border-radius:8px;padding:14px 18px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">'
                    f'<div style="font-weight:700;color:{text_c};font-size:1.05em;margin-bottom:4px;">'
                    f'{norm_name} <span style="font-size:0.8em;color:#94a3b8;font-weight:400;">· {round_label}</span>'
                    f'</div>'
                    f'{thinking_html}'
                    f'<div style="color:#1e293b;font-size:0.95em;line-height:1.65;">{formal_formatted}</div>'
                    f'</div>'
                    f'</div>'
                    f'{scroll_script}'
                )
                ph.markdown(html_content, unsafe_allow_html=True)

            def _render_dialogue_static(name: str, thinking: str, formal: str, round_label: str):
                # 兼容性：模糊匹配名称，加载正确的配色和头像
                norm_name = name
                for k in _color_map.keys():
                    if k in name or name in k or re.sub(r'[^\w\u4e00-\u9fa5]', '', k) == re.sub(r'[^\w\u4e00-\u9fa5]', '', name):
                        norm_name = k
                        break

                border_c, bg_c, text_c = _color_map.get(norm_name, ("#94a3b8", "#f8fafc", "#334155"))
                avatar_b64 = _load_avatar_b64(_avatar_map.get(norm_name, Path("")))
                avatar_html = (
                    f'<img src="data:image/png;base64,{avatar_b64}" '
                    f'style="width:52px;height:52px;border-radius:50%;object-fit:cover;'
                    f'border:2px solid {border_c};flex-shrink:0;" />'
                ) if avatar_b64 else f'<div style="width:52px;height:52px;border-radius:50%;background:{border_c};flex-shrink:0;"></div>'

                # 清理历史可能残留的 HTML 嵌套代码与冗余的前缀
                if thinking:
                    if "<div" in thinking:
                        thinking = re.sub(r'<[^>]+>', ' ', thinking).replace("💭 思考过程 (Thinking Process)", "").strip()
                    # 去除前缀
                    thinking = re.sub(r'[\*#]*思考过程[\*#]*\s*[:：]?', '', thinking)
                    thinking = re.sub(r'【思考过程】', '', thinking)
                    thinking = re.sub(r'\s+', ' ', thinking).strip()

                if formal:
                    if "<div" in formal:
                        formal = re.sub(r'<[^>]+>', ' ', formal).strip()
                    # 去除前缀
                    formal = re.sub(r'[\*#]*正式回复[\*#]*\s*[:：]?', '', formal)
                    formal = re.sub(r'【正式回复】', '', formal)
                    formal = re.sub(r'\s+', ' ', formal).strip()

                thinking_html = ""
                if thinking:
                    thinking_formatted = md_to_html(thinking).replace("\n", "<br>")
                    thinking_html = (
                        f'<div style="font-size:11px;color:#64748b;background-color:rgba(0,0,0,0.02);'
                        f'border-left:3px solid #cbd5e1;padding:6px 10px;margin-bottom:8px;border-radius:4px;font-style:italic;">'
                        f'<span style="font-weight:bold;font-style:normal;color:#475569;display:block;'
                        f'margin-bottom:2px;font-size:10px;letter-spacing:0.05em;">💭 思考过程 (Thinking Process)</span>'
                        f'{thinking_formatted}'
                        f'</div>'
                    )

                formal_formatted = md_to_html(formal).replace("\n", "<br>") if formal else ""

                html_content = (
                    f'<div style="display:flex;gap:14px;align-items:flex-start;margin-bottom:18px;">'
                    f'{avatar_html}'
                    f'<div style="flex:1;background:{bg_c};border-left:4px solid {border_c};'
                    f'border-radius:8px;padding:14px 18px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">'
                    f'<div style="font-weight:700;color:{text_c};font-size:1.05em;margin-bottom:4px;">'
                    f'{norm_name} <span style="font-size:0.8em;color:#94a3b8;font-weight:400;">· {round_label}</span>'
                    f'</div>'
                    f'{thinking_html}'
                    f'<div style="color:#1e293b;font-size:0.95em;line-height:1.65;">{formal_formatted}</div>'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(html_content, unsafe_allow_html=True)

            voting_scores = {}
            memory = ""
            detailed_log = []
            new_dialogues_list = []
            
            detailed_log.append(f"# 城市更新三方多轮博弈协商推演记录\n\n**策划议题**：{proposal}\n\n---\n")

            for round_idx in range(NUM_ROUNDS):
                st.subheader(f"🔄 {ROUND_LABELS[round_idx]}")
                round_memory = ""
                detailed_log.append(f"## {ROUND_LABELS[round_idx]}\n")
                for name, cfg in roles.items():
                    dp = f"【当前轮次】{ROUND_LABELS[round_idx]}\n{ROUND_INSTRUCTIONS[round_idx]}\n\n策划议题：\n{proposal}"
                    if memory:
                        dp += f"\n\n【前序各轮发言记录】：\n{memory[-3000:]}"
                    if round_memory:
                        dp += f"\n\n【本轮已有发言】：\n{round_memory}"
                    stream = call_llm_engine_stream(
                        prompt=dp, system_prompt=cfg["system"], model=model_tag,
                    )
                    status_ph = st.empty()
                    status_ph.write(f"💬 **{name}** 发言中...")
                    stream_ph = st.empty()
                    with stream_ph:
                        resp = st.write_stream(stream)
                    status_ph.empty()
                    stream_ph.empty()
                    
                    if isinstance(resp, str):
                        thinking, formal = parse_streaming_text(resp)
                    else:
                        thinking, formal = "", ""
                    formal_clean = re.sub(r"<SCORE:\s*\d+\s*>", "", formal)
                    
                    _render_dialogue_static(name, thinking, formal_clean, ROUND_LABELS[round_idx])
                    
                    new_dialogues_list.append({
                        "round_label": ROUND_LABELS[round_idx],
                        "name": name,
                        "thinking": thinking,
                        "formal": formal_clean
                    })

                    detailed_log.append(f"### {name}\n")
                    if thinking:
                        detailed_log.append(f"**💭 思考过程**：\n> {thinking}\n\n")
                    detailed_log.append(f"**💬 正式回复**：\n{formal_clean}\n\n")
                    
                    round_memory += f"[{name}]: {formal_clean}\n---\n"
                    time.sleep(0.3)
                memory += f"\n=== {ROUND_LABELS[round_idx]} ===\n{round_memory}"

            # 根据多轮协商全文语义进行实际效用满意度换算
            voting_scores = calculate_dynamic_satisfaction(memory)
            st.session_state["p4_voting_scores"] = voting_scores
            save_stage_output("07", SK.VOTING_SCORES, voting_scores)

            full_log_content = "\n".join(detailed_log)
            st.session_state["p7_negotiation_log"] = full_log_content
            save_stage_output("07", SK.NEGOTIATION_RESULT, full_log_content)
            save_stage_output("07", "negotiation_dialogues", new_dialogues_list)

            # 生成策略矩阵
            sp = (
                f"基于三方 **3轮博弈协商** 推演记录，生成Markdown表格【策略矩阵】：\n{memory[:4000]}\n\n"
                f"格式：| 策略方向 | 具体举措 | 政策依据 | 空间落位 | 资金逻辑 | 协同度 |\n\n"
                f"要求：\n"
                f"1. 每条策略必须有明确的空间落位（具体到哪个地块或哪条路段）\n"
                f"2. 必须体现'政策→产业→经济→空间'的良性循环逻辑\n"
                f"3. 重点体现第三轮妥协阶段达成的折中条件"
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
            st.session_state["p7_running_negotiation"] = False

    # 总是展示导出本次思考过程的下载按钮
    saved_negotiation_log = st.session_state.get(
        "p7_negotiation_log",
        load_stage_output("07", SK.NEGOTIATION_RESULT, ""),
    )
    if saved_negotiation_log:
        st.markdown("### 📥 协商结果导出")
        st.download_button(
            label="💾 导出本次三方协商博弈与完整思考过程",
            data=saved_negotiation_log,
            file_name="urban_regeneration_negotiation_log.md",
            mime="text/markdown",
            use_container_width=True,
        )
    else:
        # 为避免首次加载页面显示空按钮而没有协商，只有在有数据时显示
        pass

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
            mode="lines+markers+text",
            text=[f"<b>{v}分</b>" for v in voting.values()] + [""],
            textposition="top center",
            textfont=dict(size=13, color="#4f46e5")
        ))
        apply_plotly_polar_theme(fig, title="三方协同共识度", height=380, radial_range=[0, 100])
        st.plotly_chart(fig, **stretch_width(st.plotly_chart))
        
        # 满意度预警机制
        under_60_roles = [k for k, v in voting.items() if v < 60]
        if under_60_roles:
            st.warning(f"⚠️ 当前共识满意度较低：{', '.join(under_60_roles)} 的满意度低于 60%，存在主体利益受损，建议在上方重新发起策划协商以盘活良性循环。")
        else:
            st.success("✅ 三方达成高度共识！所有主体的利益满意度均达到 60% 以上，协同性高。")
    else:
        st.warning("暂无共识数据，请先完成多主体协同推演。")

elif selected_sub == "🖼️ 图纸提示词生成":
    render_drawing_prompt_ui("07", key_prefix="p7", stage_title="设计策略")


st.markdown("---")
render_stage_summary(
    stage_code="07",
    title="三轮博弈协商策略矩阵与良性循环",
    findings=[
        {"point": "三方角色（居民/运营商/规划师）经过 3 轮递进式博弈协商达成共识", "evidence": "LLM 多轮动态博弈推演"},
        {"point": "策略矩阵包含策略-举措-政策依据-空间落位-资金逻辑对应关系", "evidence": "多轮协商自动汇总"},
        {"point": "第三轮妥协阶段产出具体的折中条件与利益交换方案", "evidence": "全域空间数据驱动"},
    ],
    methodology="基于 DeepSeek API 的三轮动态博弈协商 + RAG 政策合规预审 + 全域空间数据注入",
    implication="为总体城市设计（Stage 08）提供了经过多轮博弈验证的策略框架与空间落位指引",
)
