from html import escape
from pathlib import Path

import streamlit as st

from src.ui.persistent_outputs import render_persistent_output_bar
from src.utils.service_check import check_engine_status
from src.workflow.city_design_workflow import (
    STAGE_LOOKUP,
    STAGE_MODULE_MAP,
    WORKFLOW_BOARDS,
    stage_primary_href,
)


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
        {"title": "数据大屏", "href": "/数据大屏", "modules": [
            {"title": "全屏监控看板", "href": "/数据大屏"},
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
        '<input type="checkbox" id="apple-menu-toggle" class="apple-menu-checkbox" />'
        '<label for="apple-menu-toggle" class="apple-menu-btn">'
        '<span class="apple-menu-icon"></span>'
        '</label>'
        f'<div class="apple-nav-items">{nav_items_html}</div>'
        '</div></div>'
    )


    st.markdown("<style>" + apple_css + "</style>" + full_html, unsafe_allow_html=True)
    render_persistent_output_bar()
    if st.session_state.get("presentation_mode", False):
        render_scrolling_control()
        render_auto_tour()
    render_presentation_toggle()
    render_settings_panel()
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
    from src.engines.copilot_engine import get_copilot_response, init_copilot_state
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


def render_auto_tour():
    """自动演示导览：自动按时间线切换页面，带进度指示器和倒计时。"""
    tour_js = r"""<script>
    (function(){
        if(window.__tourInited)return;window.__tourInited=1;

        const TOUR_STAGES = [
            {url:"/", label:"🏠 主页 - 项目概览", duration:45,
             desc:"展示项目名称、研究范围、四大核心能力卡片、算力HUD、3D数字孪生底座、模块入口"},
            {url:"/数据准备与任务解读?sub=数据上传中心", label:"📦 00 数据准备", duration:30,
             desc:"展示数据上传中心，说明16类空间/文本/街景数据的接入"},
            {url:"/资料收集与现场调研?sub=语义萃取引擎", label:"📋 01-02 资料收集", duration:25,
             desc:"展示语义萃取引擎，PDF/Markdown解析和空间数据资产管理"},
            {url:"/资料收集与现场调研?sub=现场调研", label:"📷 03 现场调研", duration:25,
             desc:"展示街景样本库，四方向全景照片和绿视率指标"},
            {url:"/现状分析与问题诊断?sub=3D现状全息底座", label:"🏗️ 04 现状分析", duration:50,
             desc:"3D全息底座：建筑图层、POI热力、街景品质柱体、天际线；操作：缓慢旋转/缩放地图"},
            {url:"/现状分析与问题诊断?sub=MPI更新潜力评估", label:"📊 05 问题诊断", duration:40,
             desc:"AHP权重滑块、MPI潜力排行、地块雷达图、一键导出诊断报告"},
            {url:"/目标定位", label:"🎯 06 目标定位", duration:25,
             desc:"设计理念提炼、愿景目标体系、案例对标借鉴"},
            {url:"/设计策略?sub=阶段四：问题-策略对应", label:"🤝 07 设计策略", duration:50,
             desc:"三主体博弈推演：居民/开发商/规划师对话、共识雷达、策略矩阵"},
            {url:"/总体城市设计", label:"🗺️ 08 总体城市设计", duration:40,
             desc:"空间结构推演、用地优化沙盘、AIGC总平面图生形"},
            {url:"/专项系统设计", label:"🔧 09 专项系统设计", duration:35,
             desc:"交通/TOD/生活圈/天际线/风貌景观四大专项"},
            {url:"/重点地段深化", label:"🔍 10 重点地段深化", duration:45,
             desc:"5个重点地块：诊断雷达、控规反推、人群画像、Before/After推演"},
            {url:"/实施路径", label:"📅 11 实施路径", duration:25,
             desc:"六种更新模式、三期时序甘特图、留改拆总图"},
            {url:"/城市设计导则", label:"📐 12 城市设计导则", duration:25,
             desc:"RAG政策检索、控制图则、Word说明书导出"},
            {url:"/成果表达", label:"🎁 13 成果表达", duration:30,
             desc:"A3图册成果画廊、图纸提示词助手、核心指标汇总"},
            {url:"/AIGC设计推演?sub=概念总平面图生形", label:"🎨 15 AIGC推演", duration:35,
             desc:"ControlNet空间约束、SD渲染管线、Before/After对比"},
            {url:"/制图与设计智能体Skill手册", label:"📖 16 智能体手册", duration:20,
             desc:"规划绘图Skill元指令定义与导出"}
        ];

        let currentIdx = 0, timerId = null, isRunning = false, remaining = 0;
        const progressBarW = 300;

        // 注入样式
        const sty = document.createElement('style');
        sty.innerHTML = `
#tour-hud{position:fixed;bottom:100px;right:20px;z-index:999998;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
#tour-hud .tour-panel{width:320px;background:rgba(15,23,42,0.94);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.12);border-radius:14px;box-shadow:0 10px 40px rgba(0,0,0,0.5);overflow:hidden;color:#f1f5f9}
#tour-hud .tour-header{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:rgba(30,41,59,0.5);border-bottom:1px solid rgba(255,255,255,0.06)}
#tour-hud .tour-header h4{margin:0;font-size:13px;font-weight:600;color:#f8fafc}
#tour-hud .tour-body{padding:12px 16px;display:flex;flex-direction:column;gap:10px}
#tour-hud .tour-info{font-size:12px;color:#94a3b8;line-height:1.5}
#tour-hud .tour-info strong{color:#f1f5f9;font-size:13px}
#tour-hud .tour-progress{height:4px;background:rgba(255,255,255,0.08);border-radius:2px;overflow:hidden}
#tour-hud .tour-progress-bar{height:100%;background:linear-gradient(90deg,#0071e3,#38bdf8);border-radius:2px;transition:width 0.3s linear}
#tour-hud .tour-timer{font-size:24px;font-weight:700;color:#38bdf8;text-align:center;font-variant-numeric:tabular-nums}
#tour-hud .tour-controls{display:flex;gap:6px}
#tour-hud .tour-btn{flex:1;padding:8px 12px;border-radius:8px;border:1px solid rgba(255,255,255,0.08);background:rgba(30,41,59,0.8);color:#f1f5f9;font-size:12px;cursor:pointer;transition:all 0.15s}
#tour-hud .tour-btn:hover{background:rgba(56,189,248,0.15);border-color:#38bdf8}
#tour-hud .tour-btn.primary{background:#0071e3;border-color:#0071e3;color:white}
#tour-hud .tour-btn.primary:hover{background:#1d93f5}
#tour-hud .tour-btn.skip{background:rgba(239,68,68,0.2);border-color:rgba(239,68,68,0.3)}
#tour-hud.closed .tour-panel{display:none}
#tour-hud.closed .tour-trigger{display:flex}
#tour-hud:not(.closed) .tour-trigger{display:none}
.tour-trigger{width:44px;height:44px;border-radius:50%;background:rgba(0,113,227,0.9);backdrop-filter:blur(10px);border:1px solid rgba(56,189,248,0.4);box-shadow:0 0 20px rgba(56,189,248,0.3);display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all 0.2s;animation:tour-pulse 2s infinite}
.tour-trigger:hover{transform:scale(1.1);box-shadow:0 0 30px rgba(56,189,248,0.5)}
@keyframes tour-pulse{0%,100%{box-shadow:0 0 20px rgba(56,189,248,0.3)}50%{box-shadow:0 0 35px rgba(56,189,248,0.6)}}
#tour-hud .tour-step-dots{display:flex;gap:3px;flex-wrap:wrap}
#tour-hud .tour-step-dot{width:8px;height:8px;border-radius:50%;background:rgba(255,255,255,0.15);transition:all 0.2s}
#tour-hud .tour-step-dot.done{background:#38bdf8}
#tour-hud .tour-step-dot.current{background:#0071e3;transform:scale(1.4);box-shadow:0 0 6px rgba(0,113,227,0.6)}
#tour-hud .tour-step-indicator{font-size:10px;color:#64748b;text-align:center}
`;
        document.head.appendChild(sty);

        // 构建DOM
        const container = document.createElement('div');
        container.id = 'tour-hud';
        container.className = 'closed';

        const dotsHtml = TOUR_STAGES.map((_,i)=>`<span class="tour-step-dot" id="tour-dot-${i}"></span>`).join('');

        container.innerHTML = `
<div class="tour-trigger" onclick="toggleTourHud()">🎬</div>
<div class="tour-panel">
  <div class="tour-header">
    <h4>🎬 自动演示导览</h4>
    <button style="background:transparent;border:none;color:#94a3b8;font-size:16px;cursor:pointer" onclick="toggleTourHud()">×</button>
  </div>
  <div class="tour-body">
    <div class="tour-info" id="tour-info">
      <strong>准备就绪</strong><br>
      共 ${TOUR_STAGES.length} 个阶段 · 总计约 ${Math.round(TOUR_STAGES.reduce((s,x)=>s+x.duration,0)/60)} 分钟
    </div>
    <div class="tour-step-indicator" id="tour-step-text">按 ▶ 开始自动导览</div>
    <div class="tour-step-dots" id="tour-dots">${dotsHtml}</div>
    <div class="tour-progress"><div class="tour-progress-bar" id="tour-progress-bar" style="width:0%"></div></div>
    <div class="tour-timer" id="tour-timer">--</div>
    <div class="tour-controls">
      <button class="tour-btn primary" id="tour-btn-start" onclick="tourStart()">▶️ 开始导览</button>
      <button class="tour-btn" id="tour-btn-next" onclick="tourNext()" disabled>⏭ 跳过</button>
    </div>
    <div style="font-size:10px;color:#64748b;text-align:center">
      快捷键: <code style="background:rgba(255,255,255,0.06);padding:1px 4px;border-radius:2px;color:#38bdf8">T</code> 开始/暂停 &nbsp;
      <code style="background:rgba(255,255,255,0.06);padding:1px 4px;border-radius:2px;color:#38bdf8">N</code> 下一阶段 &nbsp;
      <code style="background:rgba(255,255,255,0.06);padding:1px 4px;border-radius:2px;color:#38bdf8">H</code> 隐藏面板
    </div>
  </div>
</div>`;
        document.body.appendChild(container);

        // 全局函数
        window.toggleTourHud = function(){
            document.getElementById('tour-hud').classList.toggle('closed');
        };

        window.tourStart = function(){
            if(isRunning){ tourPause(); return; }
            isRunning = true;
            if(currentIdx >= TOUR_STAGES.length) currentIdx = 0;
            const btn = document.getElementById('tour-btn-start');
            btn.innerText = '⏸️ 暂停';
            btn.className = 'tour-btn';
            document.getElementById('tour-btn-next').disabled = false;
            tourGoTo(currentIdx);
        };

        window.tourPause = function(){
            isRunning = false;
            if(timerId){ clearInterval(timerId); timerId = null; }
            const btn = document.getElementById('tour-btn-start');
            btn.innerText = '▶️ 继续';
            btn.className = 'tour-btn primary';
        };

        window.tourNext = function(){
            if(currentIdx < TOUR_STAGES.length - 1){
                currentIdx++;
                tourGoTo(currentIdx);
            }
        };

        window.tourGoTo = function(idx){
            if(timerId){ clearInterval(timerId); timerId = null; }
            currentIdx = idx;
            const stage = TOUR_STAGES[idx];
            remaining = stage.duration;
            updateUI();

            // 导航到目标页面
            window.location.href = stage.url;

            // 更新进度条和计时器
            timerId = setInterval(function(){
                remaining--;
                if(remaining <= 0){
                    clearInterval(timerId); timerId = null;
                    if(isRunning && currentIdx < TOUR_STAGES.length - 1){
                        currentIdx++;
                        tourGoTo(currentIdx);
                    } else if(currentIdx >= TOUR_STAGES.length - 1){
                        tourComplete();
                    }
                }
                updateUI();
            }, 1000);
        };

        function updateUI(){
            const stage = TOUR_STAGES[currentIdx];
            const totalStages = TOUR_STAGES.length;
            const progress = ((currentIdx + (stage.duration - remaining) / stage.duration) / totalStages * 100).toFixed(1);

            document.getElementById('tour-info').innerHTML = `<strong>${stage.label}</strong><br>${stage.desc}`;
            document.getElementById('tour-step-text').innerText = `${currentIdx+1}/${totalStages} · ${stage.label.split(' ')[0]}`;
            document.getElementById('tour-progress-bar').style.width = progress + '%';
            document.getElementById('tour-timer').innerText = remaining > 0 ? remaining + 's' : '→';

            // 更新点状指示器
            for(let i=0; i<totalStages; i++){
                const dot = document.getElementById('tour-dot-'+i);
                if(!dot) continue;
                dot.className = 'tour-step-dot' + (i<currentIdx?' done':'') + (i===currentIdx?' current':'');
            }
        }

        function tourComplete(){
            isRunning = false;
            if(timerId){ clearInterval(timerId); timerId = null; }
            const btn = document.getElementById('tour-btn-start');
            btn.innerText = '✅ 导览完成';
            btn.className = 'tour-btn primary';
            btn.disabled = true;
            document.getElementById('tour-btn-next').disabled = true;
            document.getElementById('tour-info').innerHTML = '<strong>🎉 导览结束！</strong><br>全部16个阶段已展示完毕';
            document.getElementById('tour-timer').innerText = '✓';
            document.getElementById('tour-progress-bar').style.width = '100%';
            for(let i=0; i<TOUR_STAGES.length; i++){
                const dot = document.getElementById('tour-dot-'+i);
                if(dot) dot.className = 'tour-step-dot done';
            }
        }

        // 键盘快捷键
        document.addEventListener('keydown', function(e){
            if(e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) return;
            if(e.code === 'KeyT'){
                e.preventDefault();
                if(isRunning) tourPause(); else tourStart();
            } else if(e.code === 'KeyN'){
                e.preventDefault();
                if(isRunning || currentIdx < TOUR_STAGES.length - 1) tourNext();
            } else if(e.code === 'KeyH'){
                e.preventDefault();
                const hud = document.getElementById('auto-scroller-hud');
                if(hud) hud.style.display = (hud.style.display==='none')?'block':'none';
                toggleTourHud();
            }
        });
    })();
</script>"""
    st.markdown(tour_js, unsafe_allow_html=True)


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


def render_settings_panel():
    from src.config.user_settings import load_user_settings, save_user_settings
    with st.sidebar, st.expander("⚙️ 系统设置", expanded=False):
        settings = load_user_settings()
        
        # Form for settings editing
        new_settings = {}
        new_settings["DEEPSEEK_API_KEY"] = st.text_input(
            "DeepSeek API 密钥",
            value=settings.get("DEEPSEEK_API_KEY", ""),
            type="password",
            help="用于连接 DeepSeek API，输入后点击保存生效。"
        )
        new_settings["LLM_API_URL"] = st.text_input(
            "大模型接口地址",
            value=settings.get("LLM_API_URL", ""),
            help="如果使用中转或自定义 API 接口，请在此修改。"
        )
        new_settings["SD_WEBUI_URL"] = st.text_input(
            "SD WebUI 地址",
            value=settings.get("SD_WEBUI_URL", ""),
            help="Stable Diffusion WebUI 本地服务端口 (默认 7860)"
        )
        new_settings["OLLAMA_URL"] = st.text_input(
            "Ollama 地址",
            value=settings.get("OLLAMA_URL", ""),
            help="Ollama 本地大模型接口地址 (默认 11434)"
        )
        
        if st.button("💾 保存配置", key="save_settings_btn", use_container_width=True):
            if save_user_settings(new_settings):
                st.success("配置已保存，已自动应用于系统环境变量！")
                st.rerun()
            else:
                st.error("配置保存失败，请检查写入权限。")


from src.ui.chart_theme import (
    CHART_PALETTE,
    apply_plotly_polar_theme,
    apply_plotly_theme,
    get_chart_palette,
    rgba_from_hex,
)
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
