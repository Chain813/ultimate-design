"""Stage 07: structured page renderer for strategy negotiation."""

import base64
import re
import time
from pathlib import Path

import streamlit as st

try:
    import streamlit.components.v1 as components
except ModuleNotFoundError:
    components = st.components.v1
from src.engines.llm_engine import call_llm_engine_stream
from src.engines.site_diagnostic_engine import generate_policy_matrix
from src.engines.spatial_data_injector import (
    get_full_spatial_context,
    get_key_plots_summary,
    get_landuse_summary,
)
from src.stages.common.workspace import render_stage_workspace
from src.stages.stage07_strategy.config import STAGE07_WORKSPACE
from src.ui.app_shell import (
    render_engine_status_alert,
    render_logic_chain_stepper,
    render_top_nav,
)
from src.ui.chart_theme import apply_plotly_polar_theme
from src.ui.design_system import render_page_banner, render_section_intro
from src.ui.module_summary import render_stage_summary
from src.ui.persistent_outputs import register_report_output
from src.ui.streamlit_compat import stretch_width
from src.workflow.approval_state import record_policy_review
from src.workflow.stage_data_bus import (
    load_stage_output,
    render_evidence_chain_bar,
    save_stage_output,
)
from src.workflow.stage_keys import SK

graphic_svg = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 200" width="100%" height="100%" style="max-width: 600px; filter: drop-shadow(0 8px 16px rgba(0,0,0,0.04));">
  <defs>
    <linearGradient id="g_base" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#f5f5f7"/>
    </linearGradient>
    <linearGradient id="g_out" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="rgba(52, 199, 89, 0.03)"/>
      <stop offset="100%" stop-color="rgba(52, 199, 89, 0.08)"/>
    </linearGradient>
  </defs>

  <!-- Left Side: Stacked Roles to Center Loop -->
  <path d="M 150 45 C 185 45, 175 100, 200 100" fill="none" stroke="#d1d1d6" stroke-width="1.5" stroke-dasharray="4,3"/>
  <path d="M 150 100 L 200 100" fill="none" stroke="#0071e3" stroke-width="2" stroke-dasharray="5,4"/>
  <path d="M 150 155 C 185 155, 175 100, 200 100" fill="none" stroke="#d1d1d6" stroke-width="1.5" stroke-dasharray="4,3"/>

  <!-- Left Stacked Role Nodes -->
  <rect x="10" y="25" width="140" height="40" rx="8" fill="url(#g_base)" stroke="#ff9500" stroke-width="1.2"/>
  <text x="80" y="42" fill="#ff9500" font-size="12" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle" font-weight="bold">居民代表</text>
  <text x="80" y="55" fill="#86868b" font-size="10" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle">权益与民生诉求</text>

  <rect x="10" y="80" width="140" height="40" rx="8" fill="url(#g_base)" stroke="#0071e3" stroke-width="1.5"/>
  <text x="80" y="97" fill="#0071e3" font-size="12" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle" font-weight="bold">开发运营商</text>
  <text x="80" y="110" fill="#1d1d1f" font-size="10" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle">资本与产业导入</text>

  <rect x="10" y="135" width="140" height="40" rx="8" fill="url(#g_base)" stroke="#af52de" stroke-width="1.2"/>
  <text x="80" y="152" fill="#af52de" font-size="12" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle" font-weight="bold">专业规划师</text>
  <text x="80" y="165" fill="#86868b" font-size="10" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle">空间与合规控制</text>

  <!-- Center Loop Track -->
  <path d="M 350 37 L 455 100 L 350 163 L 245 100 Z" fill="none" stroke="#5e5ce6" stroke-width="1.5" stroke-dasharray="5,4"/>
  
  <!-- Loop Direction Arrows -->
  <polygon points="402,65 406,72 397,71" fill="#5e5ce6"/>
  <polygon points="402,135 397,129 406,128" fill="#5e5ce6"/>
  <polygon points="297,135 293,128 302,129" fill="#5e5ce6"/>
  <polygon points="297,65 302,71 293,72" fill="#5e5ce6"/>

  <!-- Loop Nodes -->
  <rect x="290" y="20" width="120" height="34" rx="8" fill="url(#g_base)" stroke="#5e5ce6" stroke-width="1"/>
  <text x="350" y="41" fill="#1d1d1f" font-size="11" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle" font-weight="bold">政策引导 (RAG)</text>

  <rect x="410" y="83" width="90" height="34" rx="8" fill="url(#g_base)" stroke="#5e5ce6" stroke-width="1"/>
  <text x="455" y="104" fill="#1d1d1f" font-size="11" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle" font-weight="bold">产业导入</text>

  <rect x="290" y="146" width="120" height="34" rx="8" fill="url(#g_base)" stroke="#5e5ce6" stroke-width="1"/>
  <text x="350" y="167" fill="#1d1d1f" font-size="11" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle" font-weight="bold">经济盘活 (反哺)</text>

  <rect x="200" y="83" width="90" height="34" rx="8" fill="url(#g_base)" stroke="#5e5ce6" stroke-width="1"/>
  <text x="245" y="104" fill="#1d1d1f" font-size="11" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle" font-weight="bold">空间更新</text>

  <!-- Connection: Center Loop to Right Output -->
  <path d="M 500 100 L 540 100" fill="none" stroke="#34c759" stroke-width="2" stroke-dasharray="5,4"/>
  <polygon points="535,96 540,100 535,104" fill="#34c759"/>

  <!-- Right Output Card -->
  <rect x="540" y="40" width="130" height="120" rx="10" fill="url(#g_out)" stroke="#34c759" stroke-width="2"/>
  <text x="605" y="65" fill="#34c759" font-size="13" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle" font-weight="bold">策略共识矩阵</text>
  <text x="605" y="90" fill="#1d1d1f" font-size="10" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle">✓ 带政策依据 (RAG)</text>
  <text x="605" y="110" fill="#1d1d1f" font-size="10" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle">✓ 空间精确落位</text>
  <text x="605" y="130" fill="#1d1d1f" font-size="10" font-family="system-ui, -apple-system, sans-serif" text-anchor="middle">✓ 三方利益最优解</text>

  <circle cx="150" cy="100" r="4" fill="#0071e3"/>
  <circle cx="200" cy="100" r="4" fill="#0071e3"/>
</svg>
"""

def render_page() -> None:
    render_top_nav()
    render_engine_status_alert()

    render_page_banner(
        title="设计策略",
        description=(
            "三方角色（居民/运营商/规划师）围绕'政策引导→产业导入→经济盘活→空间更新'"
            "展开协同推演，形成带政策依据和空间落位的策略矩阵。"
        ),
        eyebrow="Stage 07",
        tags=["政经良性循环", "三方协同", "RAG 政策校验", "策略矩阵"],
        graphic_html=graphic_svg,
    )
    active = render_stage_workspace(STAGE07_WORKSPACE)
    render_evidence_chain_bar("07", list(STAGE07_WORKSPACE.evidence_stages))

    with st.sidebar:
        model_tag = st.selectbox(
            "DeepSeek 模型",
            ["deepseek-v4-flash", "deepseek-v4-pro"],
            index=0,
            key="p7_model",
        )
        temp = st.slider("决策倾向 (Temperature)", 0.0, 1.0, 0.7, key="p7_temp")
        enable_policy = st.checkbox("📜 启用政策合规校验", value=True, key="p7_policy")

    selected_sub = active.label
    st.markdown("---")
    if selected_sub == "⚖️ 多主体协同推演":
        render_section_intro(
            "三轮动态博弈协商推演",
            "三方角色（居民/运营商/规划师）围绕伪满皇宫文化IP与区域经济盘活，"
            "展开 3 轮递进式博弈协商：**陈述→交锋→妥协**，最终形成带政策依据的策略矩阵。",
            eyebrow="Multi-Round Negotiation",
        )

        # ── 动态因地制宜配置与上游 Stage 04 靶向地块读取 ──
        from src.config.site import get_site_config
        from src.engines.context_adaptive_engine import generate_adaptive_personas, infer_plot_diagnostics

        site_cfg = get_site_config()
        site_city = site_cfg.get("city", "当地") or "当地"

        target_plot_data = load_stage_output("04", "target_plot") or load_stage_output("05", "target_plot")
        if not target_plot_data or not isinstance(target_plot_data, dict):
            s_name = site_cfg.get("name", "更新示范地块") or "更新示范地块"
            target_plot_data = {
                "name": s_name,
                "land_use": "综合更新用地",
                "mpi": 85.0,
                "priority": "P1 优先更新",
                "issues": ["空间功能混杂低效", "公共服务设施短缺", "微气候与人居环境待改善"],
                "far_max": 1.4,
                "height_max": 18.0,
                "density_max": 35.0,
                "green_min": 25.0,
            }

        target_name = target_plot_data.get("name", "更新示范地块")
        target_landuse = target_plot_data.get("land_use", target_plot_data.get("type", "综合更新用地"))
        target_mpi = target_plot_data.get("mpi", 85.0)
        target_priority = target_plot_data.get("priority", "P1 优先更新")
        raw_issues = target_plot_data.get("issues", [])
        if not raw_issues:
            raw_issues = infer_plot_diagnostics(target_plot_data, site_cfg)
        target_issues = "、".join(raw_issues) if isinstance(raw_issues, list) else str(raw_issues)

        far_max = target_plot_data.get("far_max", 1.4)
        height_max = target_plot_data.get("height_max", 18.0)
        density_max = target_plot_data.get("density_max", 35.0)
        green_min = target_plot_data.get("green_min", 25.0)
        target_area = target_plot_data.get("area_ha", target_plot_data.get("area", 2.5))

        # 动态自生式生成该地块的 3 组本土利益相关方
        adaptive_personas = generate_adaptive_personas(
            site_context=site_cfg,
            target_plot=target_plot_data,
            regulatory_limits={"far_max": far_max, "height_max": height_max, "density_max": density_max, "green_min": green_min}
        )

        # ── 头像/配色/富文本渲染定义 ──
        _avatar_dir = Path("static/avatars")
        _avatar_map = {p["display_name"]: _avatar_dir / p["avatar_file"] for p in adaptive_personas}
        _color_map = {p["display_name"]: (p["color"], p["bg_color"], p["text_color"]) for p in adaptive_personas}
        for p in adaptive_personas:
            _color_map[p["role_title"]] = (p["color"], p["bg_color"], p["text_color"])
            _avatar_map[p["role_title"]] = _avatar_dir / p["avatar_file"]

        def _load_avatar_b64(path: Path) -> str:
            if path.exists():
                return base64.b64encode(path.read_bytes()).decode()
            return ""

        def md_to_html(text: str) -> str:
            if not text:
                return ""
            try:
                import markdown
                html = markdown.markdown(text, extensions=['extra', 'nl2br'])
            except ImportError:
                # 鲁棒的兜底解析器：在未安装 markdown 库时，防闪退并支持基础 Markdown 语法
                import html as html_esc
                escaped = html_esc.escape(text)
                # 支持粗体 **粗体**
                escaped = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', escaped)
                # 支持简单无序列表 - 列表项
                escaped = re.sub(r'^\s*[\-\*]\s+(.*?)$', r'<li>\1</li>', escaped, flags=re.MULTILINE)
                # 将没有 li 包裹的换行替换为 <br>
                escaped = escaped.replace('\n', '<br>')
                html = escaped
            
            # 微调对话框里的常见 HTML 元素间距，防止列表或段落过大影响排版
            html = html.replace("<p>", '<p style="margin: 0 0 6px 0; padding: 0;">')
            html = html.replace("<ul>", '<ul style="margin: 0 0 6px 0; padding-left: 18px; list-style-type: disc;">')
            html = html.replace("<ol>", '<ol style="margin: 0 0 6px 0; padding-left: 18px; list-style-type: decimal;">')
            html = html.replace("<li>", '<li style="margin: 0 0 3px 0;">')
            return html

        def _render_dialogue_static(name: str, thinking: str, formal: str, round_label: str):
            # 兼容性：模糊匹配名称，加载正确的配色和头像
            norm_name = name
            for k in _color_map:
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

            # 清理历史可能残留的 HTML 嵌套代码与冗余的前缀，并保留 Markdown 换行结构
            if thinking:
                if "<div" in thinking:
                    thinking = re.sub(r'<[^>]+>', ' ', thinking).replace("💭 思考过程 (Thinking Process)", "").strip()
                # 正则匹配剔除前缀及其多余的 markdown 符号，避免 ## 混入内容
                think_pattern = r"^(【思考过程】|\[思考过程\]|\*\*思考过程\*\*|###?\s*思考过程|思考过程[:：]\s*)"
                thinking = re.sub(think_pattern, "", thinking, flags=re.IGNORECASE).strip()
                thinking = re.sub(r'^[\s#\*：:]+', '', thinking).strip()
                # 仅合并水平空格，不破坏换行
                thinking = re.sub(r'[ \t]+', ' ', thinking)
                thinking = re.sub(r'\r\n', '\n', thinking)
                thinking = re.sub(r'\n\s*\n', '\n\n', thinking).strip()

            if formal:
                if "<div" in formal:
                    formal = re.sub(r'<[^>]+>', ' ', formal).strip()
                # 正则匹配剔除正式回复的各种前缀及其多余的 markdown 符号，避免 ## 混入内容
                formal_pattern = r"^(【正式回复】|\[正式回复\]|\*\*正式回复\*\*|###?\s*正式回复|正式回复[:：]|【正式发言】|\[正式发言\]|\*\*正式发言\*\*|###?\s*正式发言|正式发言[:：]|【正式方案】|\[正式方案\]|\*\*正式方案\*\*|###?\s*正式方案|正式方案[:：]\s*)"
                formal = re.sub(formal_pattern, "", formal, flags=re.IGNORECASE).strip()
                formal = re.sub(r'^[\s#\*：:]+', '', formal).strip()
                # 仅合并水平空格，不破坏换行，保持 Markdown 段落和列表项
                formal = re.sub(r'[ \t]+', ' ', formal)
                formal = re.sub(r'\r\n', '\n', formal)
                formal = re.sub(r'\n\s*\n', '\n\n', formal).strip()

            thinking_html = ""
            if thinking:
                thinking_formatted = md_to_html(thinking)
                thinking_html = (
                    f'<div style="font-size:11px;color:#64748b;background-color:rgba(0,0,0,0.02);'
                    f'border-left:3px solid #cbd5e1;padding:6px 10px;margin-bottom:8px;border-radius:4px;font-style:italic;">'
                    f'<span style="font-weight:bold;font-style:normal;color:#475569;display:block;'
                    f'margin-bottom:2px;font-size:10px;letter-spacing:0.05em;">💭 思考过程 (Thinking Process)</span>'
                    f'{thinking_formatted}'
                    f'</div>'
                )

            formal_formatted = md_to_html(formal) if formal else ""

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

        s3 = st.session_state.get(
            "stage3_output",
            load_stage_output("06", SK.DESIGN_CONCEPT, ""),
        )

        # ── 因地制宜博弈参数面板 ──
        with st.container(border=True):
            st.markdown("#### 🎯 因地制宜博弈参数面板")
            c_meta1, c_meta2, c_meta3, c_meta4 = st.columns(4)
            c_meta1.metric("当前靶向地块", target_name, help="Stage 04 定量诊断锁定靶向地块")
            c_meta2.metric("用地属性与规模", f"{target_landuse} ({target_area} ha)")
            c_meta3.metric("综合潜力评分 (MPI)", f"{target_mpi}", delta=target_priority)
            c_meta4.metric("法定控规红线", f"FAR ≤ {far_max} | 限高 ≤ {height_max}m")
            
            st.caption(f"🚨 **现状核心痛点**：{target_issues}")
            st.caption(f"📏 **法定控制红线**：容积率≤{far_max}，建筑限高≤{height_max}m，建筑密度≤{density_max}%，绿地率≥{green_min}%")

            st.markdown("##### 👥 三主体角色配置与谈判筹码（根据地块属性现场自生）")
            c_r1, c_r2, c_r3 = st.columns(3)
            for col, p in zip([c_r1, c_r2, c_r3], adaptive_personas):
                with col:
                    st.markdown(
                        f"""
                        <div style="background:{p['bg_color']}; border-left:4px solid {p['color']}; padding:10px 14px; border-radius:6px; margin-bottom:6px;">
                            <strong style="color:{p['text_color']}; font-size:14px;">{p['display_name']}</strong>
                            <div style="font-size:12px; color:#475569; margin-top:4px;"><b>身份：</b>{p['identity']}</div>
                            <div style="font-size:12px; color:#334155; margin-top:4px;"><b>切身诉求：</b>{p['core_demands'][:90]}...</div>
                            <div style="font-size:11px; color:#64748b; margin-top:4px;"><b>谈判筹码：</b>{p['bargaining_chips']}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        # 策划议题：严格锚定靶向地块
        default_proposal = ""
        if s3:
            default_proposal = s3[:300]
        else:
            default_proposal = (
                f"围绕 Stage 04 锁定的靶向更新地块【{target_name}】（{site_city}，用地性质：{target_landuse}，MPI综合评分 {target_mpi}，紧迫度 {target_priority}，核心痛点：{target_issues}），"
                f"在严格遵守法定控规红线（容积率≤{far_max}、建筑限高≤{height_max}m、绿地率≥{green_min}%）的前提下，"
                f"三主体展开因地制宜自治博弈协商：\n"
                f"1. {adaptive_personas[0]['role_title']}重点争取改善{target_issues}，配建普惠公共服务与适老无障碍活动空间；\n"
                f"2. {adaptive_personas[1]['role_title']}主张通过功能复合与活力商业业态保障投资回报与长效运营造血；\n"
                f"3. {adaptive_personas[2]['role_title']}坚守规划法定红线与视廊风貌，构建'政策引导→产业造血→经济反哺社区→空间针灸微更新'的最优共识解。"
            )
        proposal = st.text_area(
            "✍️ 策划议题（已严格锚定 Stage 04 靶向地块与因地制宜博弈焦点，可修改）",
            value=default_proposal,
            height=130,
        )

        if enable_policy and proposal:
            with st.expander("📜 政策合规校验 (RAG)", expanded=False):
                st.caption("🔍 对策划议题进行本地规划政策与合规性审查 (基于 RAG 检索法规库)")
                # 使用 session_state 缓存校验结果，避免页面加载时自动执行慢速 LLM 调用
                import hashlib
                _prop_hash = hashlib.md5(proposal.encode("utf-8")).hexdigest()
                _cache_key = f"policy_matrix_{_prop_hash}"
                if _cache_key not in st.session_state:
                    st.session_state[_cache_key] = None

                if st.session_state[_cache_key] is None:
                    if st.button("🔍 开始进行政策合规研判", key="btn_run_policy_check", use_container_width=True):
                        with st.spinner("AI 正在检索法规并进行合规研判..."):
                            matrix = generate_policy_matrix(proposal)
                            record_policy_review("07", SK.STRATEGY_MATRIX, matrix if matrix else [])
                            st.session_state[_cache_key] = matrix if matrix else []
                            st.rerun()
                else:
                    matrix = st.session_state[_cache_key]
                    if matrix:
                        for item in matrix:
                            note = item.get("compliance_note", "📋 参考")
                            if "违规" in note or "风险" in note or "⚠️" in note:
                                st.warning(f"**{item['source']}** {note}")
                            elif "合规" in note or "✅" in note:
                                st.success(f"**{item['source']}** {note}")
                            else:
                                st.info(f"**{item['source']}** {note}")
                    if st.button("🔄 重新进行合规研判", key="btn_re_run_policy_check", use_container_width=True):
                        st.session_state[_cache_key] = None
                        st.rerun()

        # 加载已有的历史对话
        saved_dialogues = load_stage_output("07", "negotiation_dialogues", [])

        run_negotiation = False
        if not saved_dialogues:
            if st.button("🚀 开启三方协同推演", type="primary", **stretch_width(st.button)):
                run_negotiation = True
        elif st.session_state.get("p7_running_negotiation", False):
            run_negotiation = True
        else:
            st.info("💡 已加载历史推演记录。您可以选择以传统卡片时间线查看，或启动交互式动画沙盘播放。")
            tab_list, tab_replay = st.tabs(["📝 传统卡片视角", "🎭 交互式博弈沙盘 (动画重放)"])
            
            with tab_list:
                current_round = ""
                for item in saved_dialogues:
                    if item["round_label"] != current_round:
                        current_round = item["round_label"]
                        st.subheader(f"🔄 {current_round}")
                    _render_dialogue_static(item["name"], item.get("thinking", ""), item["formal"], item["round_label"])
                
            with tab_replay:
                replay_html_path = Path("static/negotiation_replay.html")
                if replay_html_path.exists():
                    html_content = replay_html_path.read_text(encoding="utf-8")
                    components.html(html_content, height=750, scrolling=True)
                else:
                    st.warning("⚠️ 交互式重放文件未找到，请先重新运行推演以进行编译生成。")
                
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

                # ── 自动滚动辅助 ──
                # 通过 st.components.v1.html() 在前端启用高频定时器（100ms），
                # 在三方对话主动生成的过程中实现平滑、稳定、不卡顿的页面滚动。
                _SCROLL_JS = """
                <script>
                (function() {
                    var lastScrollHeights = {};
                    var targets = ['.stAppViewContainer', '.stMain', '.main', 'section.main',
                                   '[data-testid="stAppViewContainer"]', '[data-testid="stMain"]'];
                    
                    var scrollInterval = setInterval(function() {
                        try {
                            var p = window.parent.document;
                            var anyScrolled = false;
                            
                            for (var i = 0; i < targets.length; i++) {
                                var selector = targets[i];
                                var el = p.querySelector(selector);
                                if (el) {
                                    var currentHeight = el.scrollHeight;
                                    var currentTop = el.scrollTop;
                                    var clientHeight = el.clientHeight;
                                    
                                    var lastHeight = lastScrollHeights[selector] || clientHeight;
                                    
                                    // 判断在高度变化之前，用户是否处于贴近底部的区域（预留 150px 缓冲区）
                                    var wasAtBottom = (lastHeight - clientHeight - currentTop) < 150;
                                    
                                    // 仅当用户原本就在底部，且内容高度增加时，才执行下滑滚动
                                    if (wasAtBottom && currentHeight > lastHeight) {
                                        el.scrollTop = currentHeight;
                                        anyScrolled = true;
                                    }
                                    
                                    // 缓存当前高度
                                    lastScrollHeights[selector] = currentHeight;
                                }
                            }
                            
                            // 只有在子容器执行滚动时，才同步滚动全局 window 视口，避免强拉画面
                            if (anyScrolled) {
                                try {
                                    window.parent.scrollTo(0, p.body.scrollHeight);
                                    p.documentElement.scrollTop = p.documentElement.scrollHeight;
                                } catch(e) {}
                            }
                        } catch(err) {
                            // 跨域降级方案
                            try {
                                window.scrollTo(0, document.body.scrollHeight);
                            } catch(e) {}
                        }
                    }, 100);
                    
                    // 30分钟后自动清理定时器
                    setTimeout(function() {
                        clearInterval(scrollInterval);
                    }, 1800000);
                })();
                </script>
                """
                components.html(_SCROLL_JS, height=0, scrolling=False)

                # 跨阶段诊断数据安全加载 (打通 Stage 04/05 定量诊断与靶向地块)
                diag_report = load_stage_output("05", SK.DIAGNOSIS_REPORT) or load_stage_output("04", SK.DIAGNOSIS_REPORT, "")
                diag_summary = (
                    f"优先更新靶向地块: 【{target_name}】 (MPI综合潜力得分: {target_mpi}, 紧迫度: {target_priority});\n"
                    f"用地性质: {target_landuse} (占地约 {target_area} ha);\n"
                    f"地块现状核心痛点: {target_issues}"
                )
                if diag_report:
                    diag_summary += f"\n前期量化诊断核心问题: {diag_report[:600]}..."

                # 各方角色共享的空间背景
                shared_context = (
                    f"\n\n【现状定量诊断与更新靶向 (Stage 04/05)】：\n{diag_summary}"
                    f"\n\n【研究范围空间数据约束】：\n{spatial_ctx[:2500]}"
                    f"\n\n【上游设计目标 (Stage 06)】：\n{s3[:1500] if s3 else '暂无'}"
                    f"\n\n【法定控规红线】：容积率≤{far_max}，建筑限高≤{height_max}m，建筑密度≤{density_max}%，绿地率≥{green_min}%。"
                )
                cot = ("\n\n请用【思考过程】展示推理，【正式回复】给出建设性方案，"
                       "末行<SCORE:数值>打分(0-100)表示对方案的支持度。"
                       "注意：三方立场围绕靶向地块各抒诉求、相辅相成，共同推动良性循环。")

                roles = {
                    p["display_name"]: {
                        "system": p["system_prompt"] + shared_context + cot,
                        "color": p["color"],
                        "role_title": p["role_title"],
                    }
                    for p in adaptive_personas
                }

                # 动态满意度计算逻辑
                def calculate_dynamic_satisfaction(memory_text: str):
                    p_names = [p["display_name"] for p in adaptive_personas]
                    scores = {k: 50.0 for k in p_names}
                    # 尝试通过 LLM 语义评分
                    try:
                        from src.engines.llm_engine import call_llm_engine
                        from src.utils.llm_json_parser import parse_llm_json
                        
                        prompt = f"""
                        分析以下三个主体关于城市更新协商的对话文本，从语义上评估三方角色对当前方案的满意度得分（0-100分）。
                        
                        各方利益关注点：
                        - {p_names[0]}：{adaptive_personas[0]['core_demands']}
                        - {p_names[1]}：{adaptive_personas[1]['core_demands']}
                        - {p_names[2]}：{adaptive_personas[2]['core_demands']}
                        
                        协商对话文本：
                        {memory_text}
                        
                        请严格评估三方当前的态度是否在朝良性合作发展，计算出合理的分数。初始分为 50 分。每条满足或推进该角色利益的合理方案加分，损害利益的方案扣分。
                        请仅返回 JSON 格式结果，不要包含任何 markdown 块或多余文字：
                        {{
                            "{p_names[0]}": 分数(数字),
                            "{p_names[1]}": 分数(数字),
                            "{p_names[2]}": 分数(数字)
                        }}
                        """
                        resp = call_llm_engine(prompt=prompt, system_prompt="你是一位客观的城市规划博弈审计员。", model="deepseek-v4-flash")
                        parsed = parse_llm_json(resp, fallback=None)
                        if parsed and isinstance(parsed, dict):
                            valid = True
                            for k in scores:
                                if k not in parsed or not isinstance(parsed[k], (int, float)):
                                    valid = False
                            if valid:
                                return {k: min(100.0, max(0.0, float(parsed[k]))) for k in scores}
                    except Exception:
                        pass

                    # 降级退回到关键词匹配
                    kw_groups = [
                        ["绿", "公园", "配套", "社区", "医院", "生活", "便民", "养老", "口袋", "老龄", "居民", "人行道", "活动", "休憩", "共享", "适老"],
                        ["容积率", "收益", "商业", "运营", "产业", "投资", "回报", "品牌", "活力", "盈利", "客流", "商铺", "活化", "复合", "招商"],
                        ["规划", "控规", "限高", "合规", "风貌", "条例", "视廊", "数据", "红线", "导则", "退让", "绿地率", "密度", "指标", "法定"],
                    ]
                    for idx, kws in enumerate(kw_groups):
                        k_name = p_names[idx]
                        for kw in kws:
                            if kw in memory_text:
                                scores[k_name] += 6.0
                            
                    for k in scores:
                        scores[k] = min(100.0, max(0.0, scores[k]))
                    return scores



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
                    # 正则匹配“正式回复/发言/方案”的分界线，兼容各种中英文括号、符号和标题级数
                    pattern = r"(【正式回复】|\[正式回复\]|\*\*正式回复\*\*|###?\s*正式回复|正式回复[:：]|【正式发言】|\[正式发言\]|\*\*正式发言\*\*|###?\s*正式发言|正式发言[:：]|【正式方案】|\[正式方案\]|\*\*正式方案\*\*|###?\s*正式方案|正式方案[:：])"
                    match = re.search(pattern, raw_text)
                    
                    thinking_part = ""
                    formal_part = ""
                    
                    if match:
                        boundary_start = match.start()
                        boundary_end = match.end()
                        thinking_part = raw_text[:boundary_start].strip()
                        formal_part = raw_text[boundary_end:].strip()
                    else:
                        thinking_part = raw_text.strip()
                        formal_part = ""
                        
                    # 剔除思考过程的前缀和开头的乱七八糟字符（包括 markdown 符号）
                    think_pattern = r"^(【思考过程】|\[思考过程\]|\*\*思考过程\*\*|###?\s*思考过程|思考过程[:：]\s*)"
                    thinking_part = re.sub(think_pattern, "", thinking_part, flags=re.IGNORECASE).strip()
                    thinking_part = re.sub(r'^[\s#\*：:]+', '', thinking_part).strip()
                    
                    # 剔除正式回复开头的乱七八糟字符（包括 markdown 符号）
                    formal_part = re.sub(r'^[\s#\*：:]+', '', formal_part).strip()
                    
                    return thinking_part, formal_part



                def _render_dialogue_streaming(ph, name: str, thinking: str, formal: str, round_label: str):
                    # 兼容性：模糊匹配名称，加载正确的配色和头像
                    norm_name = name
                    for k in _color_map:
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
                        thinking_formatted = md_to_html(thinking)
                        thinking_html = (
                            f'<div style="font-size:11px;color:#64748b;background-color:rgba(0,0,0,0.02);'
                            f'border-left:3px solid #cbd5e1;padding:6px 10px;margin-bottom:8px;border-radius:4px;font-style:italic;">'
                            f'<span style="font-weight:bold;font-style:normal;color:#475569;display:block;'
                            f'margin-bottom:2px;font-size:10px;letter-spacing:0.05em;">💭 思考过程 (Thinking Process)</span>'
                            f'{thinking_formatted}'
                            f'</div>'
                        )

                    formal_formatted = md_to_html(formal) if formal else "<i>正在思考中...</i>"

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
                    ph.markdown(html_content, unsafe_allow_html=True)



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
                        accumulated = ""
                        last_render_t = 0.0
                        for token in stream:
                            accumulated += token
                            now = time.time()
                            if now - last_render_t >= 0.1:
                                thinking, formal = parse_streaming_text(accumulated)
                                formal_clean = re.sub(r"<SCORE:\s*\d+\s*>", "", formal)
                                _render_dialogue_streaming(stream_ph, name, thinking, formal_clean, ROUND_LABELS[round_idx])
                                last_render_t = now
                        status_ph.empty()
                        stream_ph.empty()
                        
                        if isinstance(accumulated, str) and accumulated:
                            thinking, formal = parse_streaming_text(accumulated)
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
                        time.sleep(0.05)
                    memory += f"\n=== {ROUND_LABELS[round_idx]} ===\n{round_memory}"

                # 根据多轮协商全文语义进行实际效用满意度换算
                voting_scores = calculate_dynamic_satisfaction(memory)
                st.session_state["p4_voting_scores"] = voting_scores
                save_stage_output("07", SK.VOTING_SCORES, voting_scores)

                full_log_content = "\n".join(detailed_log)
                st.session_state["p7_negotiation_log"] = full_log_content
                save_stage_output("07", SK.NEGOTIATION_RESULT, full_log_content)
                register_report_output(label="三方协商博弈推演记录", content=full_log_content, stage_code="07", key="negotiation_log")
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
                        f"资深城市更新策划师。策略须在【{target_name}】容积率≤{far_max}、"
                        f"建筑限高≤{height_max}m等法定红线约束下，构建政策-经济-空间的良性循环。"
                    ),
                    model=model_tag,
                )
                summary = st.write_stream(stream)
                if isinstance(summary, str):
                    st.session_state["stage4_output"] = summary
                    save_stage_output("07", SK.STRATEGY_MATRIX, summary)
                    save_stage_output("07", "target_plot", target_plot_data)
                    register_report_output(label="策略共识矩阵", content=summary, stage_code="07", key="strategy_matrix")

                    # 自动根据动态博弈结果与真实地块参数合成结构化《设计纲要》
                    try:
                        from src.workflow.design_context import build_design_context, synthesize_design_brief
                        b_ctx = build_design_context()
                        b_ctx.strategy_matrix = summary
                        b_ctx.negotiation_result = full_log_content
                        brief_content = synthesize_design_brief(b_ctx)
                        if brief_content:
                            save_stage_output("07", SK.DESIGN_BRIEF, brief_content)
                            register_report_output(label="设计纲要", content=brief_content, stage_code="07", key="design_brief")
                    except Exception as e:
                        logging.warning("Auto synthesize design brief error: %s", e)

                    # 自动重新生成重放网页与示意图成果
                    try:
                        from scripts.generate_negotiation_infographic import main as generate_infographic
                        from scripts.generate_negotiation_replay import main as generate_replay
                        generate_replay()
                        generate_infographic()
                    except Exception as e:
                        st.warning(f"自动编译成果失败: {e}")
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

        saved_matrix = load_stage_output("07", SK.STRATEGY_MATRIX, "")
        if saved_matrix:
            st.markdown("### 🏛️ 专家评审与工作流审批")
            from src.workflow.approval_state import (
                APPROVAL_ALLOWED_STATUSES,
                ApprovalStatus,
                load_approval_record,
                save_approval_record,
            )
            app_rec = load_approval_record("07", SK.STRATEGY_MATRIX)
            is_approved = app_rec.get("status") in APPROVAL_ALLOWED_STATUSES
            col_rev1, col_rev2 = st.columns([3, 1])
            with col_rev1:
                if is_approved:
                    st.success(f"✅ **策略共识矩阵已通过评审**（评审人: {app_rec.get('reviewer', '城市更新专家委员会')}）\n\n下游 Stage 08 总体城市设计前置门禁已成功解锁。")
                else:
                    st.info("📌 **当前状态：待专家评审**\n\n策略共识矩阵已生成，可提交专家评审并核准放行下游 Stage 08 总体城市设计。")
            with col_rev2:
                btn_label = "🔄 重新评审并核准" if is_approved else "🏛️ 提交专家评审（批准放行）"
                if st.button(btn_label, key="btn_p07_submit_approval", type="primary", use_container_width=True):
                    save_approval_record(
                        stage_code="07",
                        key=SK.STRATEGY_MATRIX,
                        status=ApprovalStatus.APPROVED,
                        reviewer="城市更新专家评审委员会",
                        comment="三方协同博弈策略矩阵与良性循环方案评审通过，准予进入下一阶段",
                    )
                    st.success("✅ 评审记录已保存，已成功解锁下游 Stage 08！")
                    st.rerun()

    elif selected_sub == "📊 共识雷达":
        render_section_intro("动态共识雷达", "查看三方协同推演后的共识度分布。", eyebrow="Consensus Radar")
        voting = st.session_state.get(
            "p4_voting_scores", load_stage_output("07", SK.VOTING_SCORES, {}),
        )
        if voting:
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=[*list(voting.values()), next(iter(voting.values()))],
                theta=[*list(voting.keys()), next(iter(voting.keys()))],
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
            # 展示并下载高分辨率示意图
            infographic_path = Path("static/negotiation_infographic.png")
            if infographic_path.exists():
                st.markdown("---")
                st.subheader("🎨 规划博弈协商成果示意图 (高分辨率成果板)")
                st.caption("以下为系统自动渲染生成的 1920x1080 博弈沙盘总结大图。")
                st.image(str(infographic_path), use_container_width=True)
                
                with open(infographic_path, "rb") as file:
                    btn = st.download_button(
                        label="💾 下载高分辨率示意图 (PNG)",
                        data=file,
                        file_name="negotiation_infographic.png",
                        mime="image/png",
                        use_container_width=True
                    )
        else:
            st.warning("暂无共识数据，请先完成多主体协同推演。")


    # ============================================================
    # 模块三：设计纲领提炼
    # ============================================================
    elif selected_sub == "📐 设计纲领提炼":
        render_section_intro(
            "设计纲领提炼",
            "补充设计依据、设计原则和设计定位。",
            eyebrow="Design Creed",
        )

        spatial_ctx = get_full_spatial_context()

        design_concept = load_stage_output("06", SK.DESIGN_CONCEPT, "")
        strategy_matrix = load_stage_output("07", SK.STRATEGY_MATRIX, "")
        negotiation_result = load_stage_output("07", SK.NEGOTIATION_RESULT, "")

        shared = f"""设计概念：{design_concept[:1500] if design_concept else '暂无'}
    策略矩阵：{strategy_matrix[:1500] if strategy_matrix else '暂无'}
    空间数据：{spatial_ctx[:1500]}"""

        # ── 3.1 设计依据 ──
        saved_basis = load_stage_output("07", SK.DESIGN_BASIS, "")
        with st.expander("📜 3.1 设计依据", expanded=bool(saved_basis) or True):
            st.caption("提炼上位规划、政策法规和案例分析的设计依据（~500字，供压缩为200字）。")
            if st.button("🧠 提炼设计依据", key="p07_basis", **stretch_width(st.button)):
                with st.spinner("LLM 提炼中..."):
                    prompt = f"""请提炼本研究的设计依据，撰写约500字的文本（将用于压缩为200字正文）。

    设计依据应涵盖：
    1. 上位规划依据（当地总体规划、国土空间规划、更新专项规划等）
    2. 政策法规依据（历史文化保护条例、城市更新政策等）
    3. 案例分析依据（国内外历史街区更新案例经验）

    {shared}

    只输出正文，不要标题。"""
                    result = call_llm_engine_stream(
                        prompt=prompt,
                        system_prompt="你是城乡规划专业的设计方法论专家。",
                        model="deepseek-v4-pro",
                    )
                    text = st.write_stream(result)
                    if isinstance(text, str) and len(text) > 50:
                        save_stage_output("07", SK.DESIGN_BASIS, text)
                        st.success(f"✅ 设计依据已生成（{len(text)} 字）")

            if saved_basis:
                st.markdown(saved_basis)

        # ── 3.2 设计原则 ──
        saved_principles = load_stage_output("07", SK.DESIGN_PRINCIPLES, "")
        with st.expander("📏 3.2 设计原则", expanded=bool(saved_principles)):
            st.caption("提炼保护优先、有机更新、多方参与等核心设计原则。")
            if st.button("🧠 提炼设计原则", key="p07_principles", **stretch_width(st.button)):
                with st.spinner("LLM 提炼中..."):
                    prompt = f"""请提炼本研究的设计原则，撰写约500字的文本（将用于压缩为200字正文）。

    设计原则应从以下产出中提取核心理念：
    1. 保护优先原则
    2. 有机更新原则
    3. 多方参与原则
    4. 文化传承原则

    {shared}

    只输出正文，不要标题。遵循严格的学术语言。"""
                    result = call_llm_engine_stream(
                        prompt=prompt,
                        system_prompt="你是城乡规划专业的设计方法论专家。",
                        model="deepseek-v4-pro",
                    )
                    text = st.write_stream(result)
                    if isinstance(text, str) and len(text) > 50:
                        save_stage_output("07", SK.DESIGN_PRINCIPLES, text)
                        st.success(f"✅ 设计原则已生成（{len(text)} 字）")

            if saved_principles:
                st.markdown(saved_principles)

        # ── 3.4 设计定位 ──
        saved_positioning = load_stage_output("07", SK.DESIGN_POSITIONING, "")
        with st.expander("📍 3.4 设计定位", expanded=bool(saved_positioning)):
            st.caption("提炼功能定位和空间形象定位。")
            if st.button("🧠 提炼设计定位", key="p07_positioning", **stretch_width(st.button)):
                with st.spinner("LLM 提炼中..."):
                    prompt = f"""请提炼本研究的设计定位，撰写约500字的文本（将用于压缩为200字正文）。

    设计定位应从以下产出中提取：
    1. 项目功能定位
    2. 空间形象定位（如"数字孪生·古今共振"）
    3. 与伪满皇宫、长春站等核心节点的关系定位

    {shared}

    只输出正文，不要标题。"""
                    result = call_llm_engine_stream(
                        prompt=prompt,
                        system_prompt="你是城乡规划专业的设计定位专家。",
                        model="deepseek-v4-pro",
                    )
                    text = st.write_stream(result)
                    if isinstance(text, str) and len(text) > 50:
                        save_stage_output("07", SK.DESIGN_POSITIONING, text)
                        st.success(f"✅ 设计定位已生成（{len(text)} 字）")

            if saved_positioning:
                st.markdown(saved_positioning)


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

    # 自动保障并合成设计纲要（在策略矩阵就绪后供下游总体设计与成果汇交读取）
    if saved_matrix:
        try:
            from src.workflow.design_context import ensure_design_brief
            ensure_design_brief()
        except Exception:
            pass

    # 业务逻辑主线推进导航
    render_logic_chain_stepper("07")

