import streamlit as st
from html import escape
from pathlib import Path
from src.workflow.city_design_workflow import (
    WORKFLOW_BOARDS, STAGE_LOOKUP, STAGE_MODULE_MAP, stage_primary_href,
)
from src.ui.persistent_outputs import render_persistent_output_bar
from src.utils.service_check import check_engine_status


def _build_nav_tree():
    tree = []
    for board in WORKFLOW_BOARDS:
        seen_titles = {}
        for code in board["stages"]:
            title = STAGE_LOOKUP[code]["title"]
            if title not in seen_titles:
                seen_titles[title] = {"title": title, "href": stage_primary_href(code), "modules": []}
            for mod in STAGE_MODULE_MAP.get(code, []):
                seen_titles[title]["modules"].append({"title": mod["title"], "href": mod["href"]})
        tree.append({"label": board["title"], "groups": list(seen_titles.values())})
    tree.append({"label": "智能工具", "groups": [
        {"title": "AIGC设计推演", "href": "/AIGC设计推演", "modules": [
            {"title": "概念总平面图生形", "href": "/AIGC设计推演?sub=概念总平面图生形"},
            {"title": "街区全景透视推演", "href": "/AIGC设计推演?sub=街区全景透视推演"},
            {"title": "轴测鸟瞰空间体块模拟", "href": "/AIGC设计推演?sub=轴测鸟瞰空间体块模拟"},
        ]},
        {"title": "智能体Skill手册", "href": "/制图与设计智能体Skill手册", "modules": [
            {"title": "制图技能规范", "href": "/制图与设计智能体Skill手册"},
            {"title": "多主体博弈沙盘", "href": "/制图与设计智能体Skill手册"},
        ]},
    ]})
    return tree


@st.cache_data
def _read_css_content(css_path: str, mtime: float):
    with open(css_path, "r", encoding="utf-8") as f:
        return f.read()


def _get_css_content():
    base_path = Path(__file__).parent.parent.parent
    css_path = base_path / "assets" / "style.css"
    if css_path.exists():
        return _read_css_content(str(css_path), css_path.stat().st_mtime)
    return ""


def load_global_css():
    css_content = _get_css_content()
    if css_content:
        st.markdown("<style>" + css_content + "</style>", unsafe_allow_html=True)


def _load_apple_nav_css():
    """加载 Apple HIG 导航栏样式"""
    base_path = Path(__file__).parent.parent.parent
    css_path = base_path / "assets" / "apple_nav.css"
    if css_path.exists():
        return _read_css_content(str(css_path), css_path.stat().st_mtime)
    return ""


def _href_to_route(href):
    if not href or href == "#":
        return "/"
    return href


# ── 板块显示名称 & 配色 ──
_BOARD_DISPLAY_NAMES = {
    "前期数据获取与现状分析": "前期分析诊断",
    "中期概念生成与应对策略": "中期策略生成",
    "后期设计生成与成果表达": "后期成果表达",
    "智能工具":               "智能工具",
}
_BOARD_COLORS = {
    "前期数据获取与现状分析": "#86868b",
    "中期概念生成与应对策略": "#a1a1a6",
    "后期设计生成与成果表达": "#98989d",
    "智能工具":               "#a78bfa",
}


def render_top_nav():
    """Apple HIG 风格固定顶部导航栏 — 纯 CSS 悬浮展开"""
    load_global_css()
    nav_tree = _build_nav_tree()
    apple_css = _load_apple_nav_css()

    st.markdown("""<style>
    [data-testid="stSidebarNav"]{display:none!important}
    .stApp{margin-top:0!important}
    .block-container{padding-top:72px!important}
    </style>""", unsafe_allow_html=True)

    # ── 构造导航项（dropdown 嵌套在 nav-item 内，CSS :hover 展开） ──
    nav_items_html = ""
    for board in nav_tree:
        display_name = _BOARD_DISPLAY_NAMES.get(board["label"], board["label"])
        accent = _BOARD_COLORS.get(board["label"], "#86868b")

        groups_html = ""
        for grp in board["groups"]:
            grp_route = _href_to_route(grp["href"])
            modules_html = ""
            for mod in grp["modules"]:
                mod_route = _href_to_route(mod["href"])
                modules_html += (
                    f'<a href="{mod_route}" target="_self" class="apple-dd-module">'
                    f'<span class="apple-dd-module-dot" style="background:{accent}"></span>'
                    f'{escape(mod["title"])}</a>'
                )
            groups_html += (
                f'<div class="apple-dd-group">'
                f'<a href="{grp_route}" target="_self" class="apple-dd-group-title">'
                f'{escape(grp["title"])}'
                f'<svg width="14" height="14" viewBox="0 0 14 14" fill="none" class="apple-dd-arrow">'
                f'<path d="M5 3L10 7L5 11" stroke="rgba(0,0,0,0.35)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
                f'</svg></a>'
                f'<div class="apple-dd-modules">{modules_html}</div></div>'
            )

        nav_items_html += (
            f'<div class="apple-nav-item">'
            f'<span>{escape(display_name)}</span>'
            f'<svg class="apple-nav-chevron" width="10" height="10" viewBox="0 0 10 10" fill="none">'
            f'<path d="M2.5 3.5L5 6.5L7.5 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
            f'</svg>'
            f'<div class="apple-dropdown"><div class="apple-dropdown-inner">{groups_html}</div></div>'
            f'</div>'
        )

    full_html = (
        '<div class="apple-nav-wrapper">'
        '<div class="apple-navbar-bar">'
        '<a href="/" target="_self" class="apple-nav-brand">'
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>'
        '<polyline points="9 22 9 12 15 12 15 22"></polyline></svg>'
        '<span>主页</span></a>'
        f'<div class="apple-nav-items">{nav_items_html}</div>'
        '</div></div>'
    )

    st.markdown("<style>" + apple_css + "</style>" + full_html, unsafe_allow_html=True)
    render_persistent_output_bar()
    render_scrolling_control()
    render_copilot_sidebar()


def render_scrolling_control():
    js_code = """<script>
    (function(){
        if(!window.__as){window.__as=1;
            var s=document.createElement('style');s.innerHTML='#auto-scroller-hud{position:fixed;bottom:20px;right:20px;z-index:999999;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;transition:all 0.3s ease}#auto-scroller-hud.closed .hud-panel{display:none}#auto-scroller-hud.closed .hud-trigger{display:flex}#auto-scroller-hud:not(.closed) .hud-panel{display:block}#auto-scroller-hud:not(.closed) .hud-trigger{display:none}.hud-trigger{width:44px;height:44px;border-radius:50%;background:rgba(30,41,59,0.85);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.15);box-shadow:0 4px 20px rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all 0.2s}.hud-trigger:hover{transform:scale(1.1);background:rgba(15,23,42,0.95);border-color:#38bdf8;box-shadow:0 0 15px rgba(56,189,248,0.4)}.hud-panel{width:250px;background:rgba(15,23,42,0.92);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.12);border-radius:14px;box-shadow:0 10px 40px rgba(0,0,0,0.5);overflow:hidden;color:#f1f5f9}.hud-header{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;background:rgba(30,41,59,0.5);border-bottom:1px solid rgba(255,255,255,0.06)}.hud-header h4{margin:0;font-size:12px;font-weight:600;color:#f8fafc}.hud-close-btn{background:transparent;border:none;color:#94a3b8;font-size:16px;cursor:pointer}.hud-body{padding:12px 14px;display:flex;flex-direction:column;gap:10px}.hud-row{display:flex;align-items:center;justify-content:space-between;font-size:12px}.hud-label{color:#94a3b8}.hud-value{font-weight:500}.hud-controls{display:flex;gap:6px;width:100%}.hud-btn{flex:1;padding:6px 10px;border-radius:6px;border:1px solid rgba(255,255,255,0.08);background:rgba(30,41,59,0.8);color:#f1f5f9;font-size:11px;cursor:pointer}.hud-btn.primary{background:#0071e3;border-color:#0071e3;color:white}.hud-shortcuts{border-top:1px solid rgba(255,255,255,0.06);padding-top:8px;margin-top:2px}.hud-shortcuts h5{margin:0 0 4px;font-size:10px;color:#64748b;text-transform:uppercase}.hud-shortcuts ul{margin:0;padding-left:0;list-style:none;display:flex;flex-direction:column;gap:3px}.hud-shortcuts li{font-size:10px;color:#94a3b8;display:flex;justify-content:space-between}.hud-shortcuts code{background:rgba(255,255,255,0.06);padding:1px 3px;border-radius:2px;color:#38bdf8}';document.head.appendChild(s);
            document.addEventListener('keydown',function(e){var t=e.target.tagName.toLowerCase();if(t==='input'||t==='textarea'||e.target.isContentEditable)return;if(e.code==='Space'){e.preventDefault();window.toggleScroll()}else if(e.code==='ArrowUp'){e.preventDefault();window.changeDirection(-1)}else if(e.code==='ArrowDown'){e.preventDefault();window.changeDirection(1)}else if(e.code==='ArrowLeft'){e.preventDefault();var s=document.getElementById('hud-speed-slider');if(s){window.updateSpeed(Math.max(0.2,parseFloat(s.value)-0.2))}}else if(e.code==='ArrowRight'){e.preventDefault();var s=document.getElementById('hud-speed-slider');if(s){window.updateSpeed(Math.min(10,parseFloat(s.value)+0.2))}}else if(e.code==='KeyH'){e.preventDefault();var h=document.getElementById('auto-scroller-hud');if(h)h.style.display=(h.style.display==='none')?'block':'none'}});
        }
        if(!document.getElementById('auto-scroller-hud')){var c=document.createElement('div');c.id='auto-scroller-hud';c.className='closed';c.innerHTML='<div class="hud-trigger" onclick="toggleScrollerHud()"><span>🎥</span></div><div class="hud-panel"><div class="hud-header"><h4>🎥 录屏自动滚动</h4><button class="hud-close-btn" onclick="toggleScrollerHud()">×</button></div><div class="hud-body"><div class="hud-row"><span class="hud-label">状态:</span><strong id="hud-status" class="hud-value paused">⏸️ 已暂停</strong></div><div class="hud-row hud-controls"><button id="btn-scroll-toggle" onclick="toggleScroll()" class="hud-btn primary">▶️ 开始</button><button onclick="changeDirection()" id="btn-direction" class="hud-btn">🔽 向下</button></div><div class="hud-row"><span class="hud-label">速度:</span><span id="hud-speed-label" class="hud-value">1.5 px/帧</span></div><div class="hud-row"><input type="range" id="hud-speed-slider" min="0.2" max="10" step="0.2" value="1.5" oninput="updateSpeed(this.value)"></div><div class="hud-shortcuts"><h5>快捷键:</h5><ul><li><code>[Space]</code> 播放/暂停</li><li><code>[↑]/[↓]</code> 方向</li><li><code>[←]/[→]</code> 速度</li><li><code>[H]</code> 隐藏</li></ul></div></div></div>';document.body.appendChild(c)}
        var speed=1.5,active=false,dir=1,pos=window.pageYOffset||0;
        window.toggleScrollerHud=function(){document.getElementById('auto-scroller-hud').classList.toggle('closed')};
        window.updateSpeed=function(v){speed=parseFloat(v);var l=document.getElementById('hud-speed-label');if(l)l.innerText=speed.toFixed(1)+' px/帧';document.getElementById('hud-speed-slider').value=v};
        window.toggleScroll=function(){active=!active;var b=document.getElementById('btn-scroll-toggle'),s=document.getElementById('hud-status');if(active){b.innerText='⏸️ 暂停';s.innerText='▶️ 滚动中';s.className='hud-value running';pos=window.pageYOffset||0;requestAnimationFrame(loop)}else{b.innerText='▶️ 开始';s.innerText='⏸️ 已暂停';s.className='hud-value paused'}};
        window.changeDirection=function(d){if(d!==undefined)dir=d;else dir*=-1;var b=document.getElementById('btn-direction');b.innerText=dir===1?'🔽 向下':'🔼 向上'};
        function loop(){if(!active)return;pos+=speed*dir;window.scrollTo(0,pos);var y=window.pageYOffset||0,m=document.documentElement.scrollHeight-window.innerHeight;if((dir===1&&y>=m-1)||(dir===-1&&y<=0))window.toggleScroll();else requestAnimationFrame(loop)}
    })();</script>"""
    st.markdown(js_code, unsafe_allow_html=True)


def render_copilot_sidebar():
    from src.engines.copilot_engine import init_copilot_state, get_copilot_response
    init_copilot_state()
    with st.sidebar:
        st.markdown("### 💬 AI 规划助手")
        st.caption("基于法规 RAG 的全生命周期 AI 助理。")
        st.markdown("""<style>.copilot-user{background-color:rgba(0,113,227,0.08);border-left:3px solid #0071e3;padding:8px 12px;border-radius:8px;margin:6px 0;font-size:13px;color:#1d1d1f}.copilot-ai{background-color:rgba(0,0,0,0.02);border-left:3px solid #86868b;padding:8px 12px;border-radius:8px;margin:6px 0;font-size:13px;color:#1d1d1f}</style>""", unsafe_allow_html=True)
        if st.session_state.get("copilot_history"):
            if st.button("🗑️ 清空对话", key="copilot_clear", use_container_width=True):
                st.session_state["copilot_history"] = []; st.rerun()
        st.markdown("---")
        for msg in st.session_state.get("copilot_history", []):
            role, content = msg["role"], msg["content"]
            if role == "user": st.markdown(f'<div class="copilot-user"><b>👤 规划师:</b> {escape(content)}</div>', unsafe_allow_html=True)
            else: st.markdown(f'<div class="copilot-ai"><b>🤖 Copilot:</b><br>{content}</div>', unsafe_allow_html=True)
        with st.form(key="copilot_chat", clear_on_submit=True):
            u = st.text_input("输入问题...", key="copilot_input")
            if st.form_submit_button("🚀 发送", use_container_width=True) and u.strip():
                with st.spinner("思考中..."): get_copilot_response(u.strip())
                st.rerun()


show_nav_bar = render_top_nav


def render_engine_status_alert():
    status = check_engine_status()
    if not status.sd or not status.gemma:
        alerts = []
        if not status.sd: alerts.append('<div style="display:flex;align-items:center;gap:18px"><span style="font-size:26px">🎨</span><div><strong style="color:#ff3b30;font-size:15px;display:block;font-weight:700">视觉渲染引擎 (Stable Diffusion) 未启动</strong><p style="color:#48484a;font-size:13px;margin:4px 0 0 0">请启动 SD WebUI 并开启 --api 模式 (端口 7860)</p></div></div>')
        if not status.gemma: alerts.append('<div style="display:flex;align-items:center;gap:18px"><span style="font-size:26px">🧠</span><div><strong style="color:#ff3b30;font-size:15px;display:block;font-weight:700">决策博弈引擎 未就绪</strong><p style="color:#48484a;font-size:13px;margin:4px 0 0 0">请在终端运行: <code>ollama run deepseek-v4-pro</code></p></div></div>')
        st.markdown(f'<div style="background:rgba(255,59,48,0.05);border:1px solid rgba(255,59,48,0.15);border-radius:16px;padding:22px 28px;margin:30px 0;display:flex;flex-direction:column;gap:20px;box-shadow:0 8px 30px rgba(0,0,0,0.04);backdrop-filter:blur(25px)">{"".join(alerts)}</div>', unsafe_allow_html=True)
        col_demo, _ = st.columns([1, 3])
        with col_demo:
            if st.button("🎭 切换演示模式", key="demo_toggle_alert"):
                st.session_state["demo_mode"] = not st.session_state.get("demo_mode", False); st.rerun()
    if st.session_state.get("demo_mode", False):
        st.markdown('<div style="background:rgba(74,222,128,0.1);border:1px solid rgba(74,222,128,0.3);border-radius:10px;padding:10px 18px;margin-top:8px"><span style="color:#4ADE80;font-weight:700">🎭 演示模式已激活</span></div>', unsafe_allow_html=True)


def render_presentation_toggle():
    with st.sidebar:
        with st.expander("🎬 演示控制", expanded=False):
            st.session_state["presentation_mode"] = st.toggle("演示模式", value=st.session_state.get("presentation_mode", False), key="pres_toggle")
            st.session_state["demo_mode"] = st.toggle("离线演示", value=st.session_state.get("demo_mode", False), key="demo_toggle_sidebar")


from src.ui.chart_theme import CHART_PALETTE, apply_plotly_polar_theme, apply_plotly_theme, get_chart_palette, rgba_from_hex  # noqa: E402,F401
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards  # noqa: E402,F401
