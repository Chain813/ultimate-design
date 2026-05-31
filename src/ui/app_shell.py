import streamlit as st
from html import escape
from pathlib import Path
from src.workflow.city_design_workflow import WORKFLOW_BOARDS, STAGE_LOOKUP, stage_primary_href

from src.utils.service_check import check_engine_status

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
    """加载全局统一的样式文件 (通过缓存优化减少磁盘 IO)"""
    css_content = _get_css_content()
    if css_content:
        st.markdown("<style>" + css_content + "</style>", unsafe_allow_html=True)

def render_top_nav():
    """下一代全景悬停导航栏 (Multi-level Hover Dropdown)"""
    load_global_css()

    nav_data = [
        {
            "lab": board["title"],
            "path": board["path"],
            "subs": [
                {"label": f"{code} {STAGE_LOOKUP[code]['title']}", "href": stage_primary_href(code)}
                for code in board["stages"]
            ],
        }
        for board in WORKFLOW_BOARDS
    ]

    # 💎 CSS3 悬停交互引擎
    st.markdown("""
    <style>
    :root { --apple-bg: rgba(255, 255, 255, 0.8); }

    /* 🍏 Apple 风格顶部主轴 (对比度优化版) */
    .nav-bar {
        position: fixed; top: 0; left: 0; width: 100%; height: 50px; /* 锁定 50px 高度 */
        background: var(--apple-bg);
        backdrop-filter: saturate(180%) blur(20px);
        display: flex; justify-content: center; align-items: center;
        z-index: 999999; border-bottom: 1px solid rgba(0, 0, 0, 0.08);
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
    }

    .nav-container {
        width: 100%; max-width: 1000px; display: flex; justify-content: space-around;
        padding: 0 20px;
    }

    .nav-item {
        color: rgba(0, 0, 0, 0.8); font-size: 13px; font-weight: 600; /* 回归 13px */
        cursor: pointer; position: relative;
        height: 50px; display: flex; align-items: center;
        padding: 0 15px; letter-spacing: 0.03em;
        text-shadow: none;
        transition: color 0.3s;
    }

    .nav-item:hover { color: #0071e3; }

    /* 彻底杜绝主页及所有链接的下划线与蓝色 (全状态封锁) */
    .nav-bar a, .nav-bar a:link, .nav-bar a:visited, .nav-bar a:active {
        text-decoration: none !important;
        color: rgba(0, 0, 0, 0.8) !important;
    }
    .nav-bar a:hover {
        color: #0071e3 !important;
    }

    /* 🍏 卡片式悬浮下拉菜单 (跟随 50px 偏移) */
    .dropdown-content {
        position: absolute; top: 50px; left: 50%; transform: translateX(-50%) translateY(10px);
        width: 240px; max-height: 0;
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(25px) saturate(190%);
        border-radius: 16px;
        border: 1px solid rgba(0, 0, 0, 0.06);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08), 0 1px 3px rgba(0, 0, 0, 0.02);
        overflow: hidden; opacity: 0; visibility: hidden;
        transition: max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1) 0.1s,
                    opacity 0.25s ease 0.1s,
                    visibility 0s linear 0.4s,
                    transform 0.3s cubic-bezier(0.4, 0, 0.2, 1) 0.1s;
        z-index: 999999;
    }

    /* 尖角 */
    .dropdown-content::before {
        content: "";
        position: absolute; top: -6px; left: 50%; transform: translateX(-50%) rotate(45deg);
        width: 10px; height: 10px; background: rgba(255, 255, 255, 0.85);
        border-left: 1px solid rgba(0, 0, 0, 0.06);
        border-top: 1px solid rgba(0, 0, 0, 0.06);
        z-index: 1;
    }

    /* 激活态：取消延迟，实现渐近开启 */
    .nav-item:hover .dropdown-content {
        max-height: 320px; opacity: 1; visibility: visible;
        transform: translateX(-50%) translateY(0);
        transition-delay: 0s;
    }

    .submenu-container {
        width: 100%; padding: 16px 12px;
        display: flex; flex-direction: column; gap: 12px;
        box-sizing: border-box;
    }

    .submenu-column { display: flex; flex-direction: column; gap: 6px; width: 100%; }
    .submenu-title { color: #86868b; font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px; padding-left: 12px; }

    .dropdown-item {
        color: #1d1d1f; font-size: 14px; font-weight: 500; text-decoration: none !important;
        transition: background-color 0.2s, color 0.2s; white-space: nowrap;
        padding: 8px 12px; border-radius: 8px;
        display: block; width: 100%; box-sizing: border-box;
        text-shadow: none;
    }

    .dropdown-item:hover { 
        background-color: rgba(0, 113, 227, 0.08);
        color: #0071e3 !important; 
    }

    /* 🍏 Apple 风格分段控制器 (Segmented Control) 独立胶囊版 */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        background: transparent !important; /* 移除整体背景，突出独立感 */
        padding: 0 !important;
        border: none !important;
        width: 100% !important;
        max-width: 100% !important;
        gap: 12px !important; /* 增加胶囊间的间隙 */
        margin: 15px 0 !important;
    }

    /* 🚀 外科手术式：仅隐藏第一个子容器（圆圈），强制显示文字 */
    div[data-testid="stRadio"] label > div:first-child {
        display: none !important;
        width: 0 !important;
        height: 0 !important;
        position: absolute !important;
    }

    /* 强力保活：确保文字及其父容器可见 */
    div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"],
    div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p {
        visibility: visible !important;
        display: block !important;
        opacity: 1 !important;
        color: inherit !important;
        width: 100% !important;
        text-align: center !important;
        margin: 0 !important;
    }

    /* 极致去除 BaseWeb 的背景与阴影干扰 */
    div[data-testid="stRadio"] [data-baseweb="radio"],
    div[data-testid="stRadio"] [role="radiogroup"] div {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* 每一个选项都成为一个独立的胶囊 */
    div[data-testid="stRadio"] label {
        flex: 0 1 auto !important;
        background: rgba(0, 0, 0, 0.03) !important;
        border: 1px solid rgba(0, 0, 0, 0.06) !important;
        padding: 10px 24px !important;
        border-radius: 50px !important; /* 纯圆形胶囊 */
        transition: background-color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease !important;
        cursor: pointer !important;
        margin: 0 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
    }

    /* 选中状态：页面变亮，呈现亮色胶囊 */
    div[data-testid="stRadio"] label:has(input:checked) {
        background: #0071e3 !important; /* 核心亮度来源 */
        border: 1px solid #0071e3 !important;
        box-shadow: 0 4px 12px rgba(0, 113, 227, 0.25) !important;
        transform: scale(1.02) !important; /* 选中的轻微放大感 */
    }

    /* 文字颜色在选中时强制设为极高对比度的纯白 */
    div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p {
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #48484a !important;
        transition: color 0.3s !important;
    }

    div[data-testid="stRadio"] label:has(input:checked) p {
        color: #ffffff !important;
        font-weight: 800 !important;
        text-shadow: none !important;
    }

    /* 悬停态：细腻的亮度提升 */
    div[data-testid="stRadio"] label:hover:not(:has(input:checked)) {
        background: rgba(0, 0, 0, 0.06) !important;
        border: 1px solid rgba(0, 0, 0, 0.12) !important;
        transform: none !important;
    }

    /* 弥补顶部高度 */
    .stApp { margin-top: 50px !important; }
    </style>
    """, unsafe_allow_html=True)

    # --- 🏗️ 构造全宽导航 HTML ---
    nav_html = '<div class="nav-bar"><div class="nav-container">'
    nav_html += '<a href="/" target="_self" class="nav-item" style="text-decoration: none !important; color: #1d1d1f !important; font-weight: 900 !important; font-size: 24px !important;">主页</a>'

    for item in nav_data:
        nav_html += f'''
        <div class="nav-item">
            {item['lab']}
            <div class="dropdown-content">
                <div class="submenu-container">
                    <div class="submenu-column">
                        <div class="submenu-title">专业流程子页面</div>
        '''
        # 子项横向分布 (如果子项多，可以分 Column，目前先统一排布)
        for sub in item['subs']:
            nav_html += f'<a href="{escape(sub["href"])}" target="_self" class="dropdown-item">{escape(sub["label"])}</a>'

        nav_html += '</div></div></div></div>'

    # ➕ 附加智能设计工具下拉菜单
    nav_html += '''
    <div class="nav-item">
        智能工具 ⚙️
        <div class="dropdown-content">
            <div class="submenu-container">
                <div class="submenu-column">
                    <div class="submenu-title">AI 与表达智能工具</div>
                    <a href="/视频生成" target="_self" class="dropdown-item">🎥 14 视频生成</a>
                    <a href="/AIGC设计推演" target="_self" class="dropdown-item">🎨 15 AIGC设计推演</a>
                    <a href="/制图与设计智能体Skill手册" target="_self" class="dropdown-item">📘 16 智能体Skill手册</a>
                </div>
            </div>
        </div>
    </div>
    '''

    nav_html += '</div></div>'
    st.markdown(nav_html, unsafe_allow_html=True)

    st.markdown("---")
    render_scrolling_control()
    render_copilot_sidebar()


def render_scrolling_control():
    """在页面底部注入高科技录屏自动滑动控制 HUD (带快捷键 & 可隐藏)"""
    import base64
    
    js_code = """
    (function() {
        if (!window.__autoScrollerLoaded) {
            window.__autoScrollerLoaded = true;
            
            // 1. 动态注入 CSS
            if (!document.getElementById('auto-scroller-style')) {
                const style = document.createElement('style');
                style.id = 'auto-scroller-style';
                style.innerHTML = `
                #auto-scroller-hud {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    z-index: 999999;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                }
                #auto-scroller-hud.closed .hud-panel {
                    display: none;
                }
                #auto-scroller-hud.closed .hud-trigger {
                    display: flex;
                }
                #auto-scroller-hud:not(.closed) .hud-panel {
                    display: block;
                }
                #auto-scroller-hud:not(.closed) .hud-trigger {
                    display: none;
                }
                .hud-trigger {
                    width: 44px;
                    height: 44px;
                    border-radius: 50%;
                    background: rgba(30, 41, 59, 0.85);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255,255,255,0.1);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                .hud-trigger:hover {
                    transform: scale(1.1);
                    background: rgba(15, 23, 42, 0.95);
                    border-color: #38bdf8;
                    box-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
                }
                .hud-icon {
                    font-size: 18px;
                }
                .hud-panel {
                    width: 250px;
                    background: rgba(15, 23, 42, 0.92);
                    backdrop-filter: blur(20px);
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    border-radius: 14px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.1);
                    overflow: hidden;
                    color: #f1f5f9;
                }
                .hud-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 10px 14px;
                    background: rgba(30, 41, 59, 0.5);
                    border-bottom: 1px solid rgba(255,255,255,0.06);
                }
                .hud-header h4 {
                    margin: 0;
                    font-size: 12px;
                    font-weight: 600;
                    color: #f8fafc;
                }
                .hud-close-btn {
                    background: transparent;
                    border: none;
                    color: #94a3b8;
                    font-size: 16px;
                    cursor: pointer;
                    transition: color 0.2s;
                    line-height: 1;
                }
                .hud-close-btn:hover {
                    color: #f1f5f9;
                }
                .hud-body {
                    padding: 12px 14px;
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                }
                .hud-row {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    font-size: 12px;
                }
                .hud-label {
                    color: #94a3b8;
                }
                .hud-value {
                    font-weight: 500;
                }
                .hud-value.paused {
                    color: #f59e0b;
                }
                .hud-value.running {
                    color: #10b981;
                }
                .hud-controls {
                    display: flex;
                    gap: 6px;
                    width: 100%;
                }
                .hud-btn {
                    flex: 1;
                    padding: 6px 10px;
                    border-radius: 6px;
                    border: 1px solid rgba(255,255,255,0.08);
                    background: rgba(30, 41, 59, 0.8);
                    color: #f1f5f9;
                    font-size: 11px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                    outline: none;
                }
                .hud-btn:hover {
                    background: rgba(51, 65, 85, 0.9);
                    border-color: rgba(255,255,255,0.15);
                }
                .hud-btn.primary {
                    background: #0071e3;
                    border-color: #0071e3;
                    color: white;
                }
                .hud-btn.primary:hover {
                    background: #147ce5;
                    box-shadow: 0 0 8px rgba(0, 113, 227, 0.3);
                }
                .hud-quick-actions {
                    display: flex;
                    gap: 6px;
                }
                .hud-btn-sm {
                    flex: 1;
                    padding: 4px 8px;
                    border-radius: 5px;
                    border: 1px solid rgba(255,255,255,0.05);
                    background: rgba(30, 41, 59, 0.5);
                    color: #cbd5e1;
                    font-size: 10px;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .hud-btn-sm:hover {
                    background: rgba(51, 65, 85, 0.7);
                    color: #f8fafc;
                }
                #hud-speed-slider {
                    width: 100%;
                    height: 3px;
                    border-radius: 2px;
                    background: #334155;
                    outline: none;
                    -webkit-appearance: none;
                }
                #hud-speed-slider::-webkit-slider-thumb {
                    -webkit-appearance: none;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    background: #38bdf8;
                    cursor: pointer;
                    box-shadow: 0 0 4px rgba(56, 189, 248, 0.5);
                    transition: transform 0.1s;
                }
                #hud-speed-slider::-webkit-slider-thumb:hover {
                    transform: scale(1.2);
                }
                .hud-shortcuts {
                    border-top: 1px solid rgba(255,255,255,0.06);
                    padding-top: 8px;
                    margin-top: 2px;
                }
                .hud-shortcuts h5 {
                    margin: 0 0 4px 0;
                    font-size: 10px;
                    color: #64748b;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }
                .hud-shortcuts ul {
                    margin: 0;
                    padding-left: 0;
                    list-style: none;
                    display: flex;
                    flex-direction: column;
                    gap: 3px;
                }
                .hud-shortcuts li {
                    font-size: 10px;
                    color: #94a3b8;
                    display: flex;
                    justify-content: space-between;
                }
                .hud-shortcuts code {
                    background: rgba(255,255,255,0.06);
                    padding: 1px 3px;
                    border-radius: 2px;
                    color: #38bdf8;
                    font-family: monospace;
                }
                `;
                document.head.appendChild(style);
            }

            // 2. 键盘快捷键监听 (仅绑定一次)
            if (!window.__autoScrollerEventsRegistered) {
                window.__autoScrollerEventsRegistered = true;
                
                document.addEventListener('keydown', function(e) {
                    const tag = e.target.tagName.toLowerCase();
                    if (tag === 'input' || tag === 'textarea' || e.target.isContentEditable) {
                        return;
                    }

                    if (e.code === 'Space') {
                        e.preventDefault();
                        window.toggleScroll();
                    } else if (e.code === 'ArrowUp') {
                        e.preventDefault();
                        window.changeDirection(-1);
                    } else if (e.code === 'ArrowDown') {
                        e.preventDefault();
                        window.changeDirection(1);
                    } else if (e.code === 'ArrowLeft') {
                        e.preventDefault();
                        const slider = document.getElementById('hud-speed-slider');
                        if (slider) {
                            const val = Math.max(0.2, parseFloat(slider.value) - 0.2);
                            window.updateSpeed(val);
                        }
                    } else if (e.code === 'ArrowRight') {
                        e.preventDefault();
                        const slider = document.getElementById('hud-speed-slider');
                        if (slider) {
                            const val = Math.min(10, parseFloat(slider.value) + 0.2);
                            window.updateSpeed(val);
                        }
                    } else if (e.code === 'KeyH') {
                        e.preventDefault();
                        const hud = document.getElementById('auto-scroller-hud');
                        if (hud) {
                            const curr = hud.style.display;
                            hud.style.display = (curr === 'none') ? 'block' : 'none';
                        }
                    }
                });
            }
        }

        // 3. 动态渲染 HUD 容器 (若不存在)
        if (!document.getElementById('auto-scroller-hud')) {
            const container = document.createElement('div');
            container.id = 'auto-scroller-hud';
            container.className = 'closed';
            container.innerHTML = `
              <div id="scroller-trigger" class="hud-trigger" onclick="toggleScrollerHud()">
                <span class="hud-icon">🎥</span>
              </div>
              <div class="hud-panel">
                <div class="hud-header">
                  <h4>🎥 录屏自动滚动</h4>
                  <button class="hud-close-btn" onclick="toggleScrollerHud()">×</button>
                </div>
                <div class="hud-body">
                  <div class="hud-row">
                    <span class="hud-label">状态:</span>
                    <strong id="hud-status" class="hud-value paused">⏸️ 已暂停</strong>
                  </div>
                  <div class="hud-row hud-controls">
                    <button id="btn-scroll-toggle" onclick="toggleScroll()" class="hud-btn primary">▶️ 开始</button>
                    <button onclick="changeDirection()" id="btn-direction" class="hud-btn">🔽 向下滚动</button>
                  </div>
                  <div class="hud-row">
                    <span class="hud-label">速度:</span>
                    <span id="hud-speed-label" class="hud-value">1.5 px/帧</span>
                  </div>
                  <div class="hud-row">
                    <input type="range" id="hud-speed-slider" min="0.2" max="10" step="0.2" value="1.5" oninput="updateSpeed(this.value)">
                  </div>
                  <div class="hud-row hud-quick-actions">
                    <button onclick="scrollToTop()" class="hud-btn-sm">🔝 回顶部</button>
                    <button onclick="scrollToBottom()" class="hud-btn-sm">🔚 到尾部</button>
                  </div>
                  <div class="hud-shortcuts">
                    <h5>快捷键:</h5>
                    <ul>
                      <li><code>[Space]</code> 播放/暂停</li>
                      <li><code>[↑] / [↓]</code> 切换滚动方向</li>
                      <li><code>[←] / [→]</code> 减速/加速</li>
                      <li><code>[H]</code> 彻底隐藏控制面板</li>
                    </ul>
                  </div>
                </div>
              </div>
            `;
            document.body.appendChild(container);
        }

        // 4. 事件控制函数定义 (全局暴露)
        let scrollSpeed = 1.5;
        let scrolling = false;
        let direction = 1;
        let exactScrollY = window.pageYOffset || document.documentElement.scrollTop;

        window.toggleScrollerHud = function() {
            const hud = document.getElementById('auto-scroller-hud');
            if (hud) hud.classList.toggle('closed');
        };

        window.updateSpeed = function(val) {
            scrollSpeed = parseFloat(val);
            const lbl = document.getElementById('hud-speed-label');
            if (lbl) lbl.innerText = scrollSpeed.toFixed(1) + ' px/帧';
            const slider = document.getElementById('hud-speed-slider');
            if (slider) slider.value = val;
        };

        window.toggleScroll = function() {
            scrolling = !scrolling;
            const btn = document.getElementById('btn-scroll-toggle');
            const status = document.getElementById('hud-status');
            
            if (scrolling) {
                if (btn) btn.innerText = '⏸️ 暂停';
                if (status) {
                    status.innerText = '▶️ 滚动中';
                    status.className = 'hud-value running';
                }
                exactScrollY = window.pageYOffset || document.documentElement.scrollTop;
                requestAnimationFrame(scrollLoop);
            } else {
                if (btn) btn.innerText = '▶️ 开始';
                if (status) {
                    status.innerText = '⏸️ 已暂停';
                    status.className = 'hud-value paused';
                }
            }
        };

        window.changeDirection = function(newDir) {
            if (newDir !== undefined) {
                direction = newDir;
            } else {
                direction = direction === 1 ? -1 : 1;
            }
            const btn = document.getElementById('btn-direction');
            if (btn) {
                btn.innerText = direction === 1 ? '🔽 向下滚动' : '🔼 向上滚动';
            }
        };

        window.scrollToTop = function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
            exactScrollY = 0;
        };

        window.scrollToBottom = function() {
            window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'smooth' });
            exactScrollY = document.documentElement.scrollHeight;
        };

        function scrollLoop() {
            if (!scrolling) return;
            exactScrollY += scrollSpeed * direction;
            window.scrollTo(0, exactScrollY);
            
            const currentY = window.pageYOffset || document.documentElement.scrollTop;
            const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
            
            if (direction === 1 && currentY >= maxScroll - 1) {
                window.toggleScroll();
            } else if (direction === -1 && currentY <= 0) {
                window.toggleScroll();
            } else {
                requestAnimationFrame(scrollLoop);
            }
        }
    })();
    """
    
    b64_js = base64.b64encode(js_code.encode("utf-8")).decode("utf-8")
    st.markdown(
        f'<img src="x" onerror="eval(atob(\'{b64_js}\'))" style="display:none;" />',
        unsafe_allow_html=True
    )


def render_copilot_sidebar():
    """在所有页面的 Streamlit 侧边栏常驻 AI 规划助手，保持对话历史。"""
    from src.engines.copilot_engine import init_copilot_state, get_copilot_response
    
    init_copilot_state()
    
    with st.sidebar:
        st.markdown("### 💬 UltimateDESIGN AI 规划助手")
        st.caption("基于法规 RAG 与阶段总线的全生命周期 AI 助理。")
        
        # 1. 对话气泡样式
        st.markdown("""
        <style>
        .copilot-user {
            background-color: rgba(0, 113, 227, 0.08);
            border-left: 3px solid #0071e3;
            padding: 8px 12px;
            border-radius: 8px;
            margin: 6px 0;
            font-size: 13px;
            color: #1d1d1f;
        }
        .copilot-ai {
            background-color: rgba(0, 0, 0, 0.02);
            border-left: 3px solid #86868b;
            padding: 8px 12px;
            border-radius: 8px;
            margin: 6px 0;
            font-size: 13px;
            color: #1d1d1f;
        }
        </style>
        """, unsafe_allow_html=True)

        # 2. 清空对话按钮
        if st.session_state["copilot_history"]:
            if st.button("🗑️ 清空对话记录", key="copilot_clear_btn", use_container_width=True):
                st.session_state["copilot_history"] = []
                st.rerun()
                
        st.markdown("---")

        # 3. 渲染历史记录
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state["copilot_history"]:
                role = msg["role"]
                content = msg["content"]
                if role == "user":
                    st.markdown(f'<div class="copilot-user"><b>👤 规划师:</b> {escape(content)}</div>', unsafe_allow_html=True)
                else:
                    # AI 答复可能包含 markdown 格式，因此不进行 html 逃逸，直接用 markdown 渲染
                    st.markdown(f'<div class="copilot-ai"><b>🤖 Copilot:</b><br>{content}</div>', unsafe_allow_html=True)
        
        # 4. 输入框表单
        with st.form(key="copilot_chat_form", clear_on_submit=True):
            user_msg = st.text_input("输入您的问题...", placeholder="例如：伪满皇宫周边限高要求是多少？", key="copilot_input_widget")
            submit = st.form_submit_button("🚀 发送", use_container_width=True)
            if submit and user_msg.strip():
                with st.spinner("AI 思考中..."):
                    get_copilot_response(user_msg.strip())
                st.rerun()

# 🔗 导出别名以实现向后兼容 (修复新页面 ImportError)
show_nav_bar = render_top_nav

def render_engine_status_alert():
    """渲染极具冲击力的引擎未启动引导提示 (Apple/Light 风格)"""
    status = check_engine_status()

    # 只有当任一引擎离线时才显示
    if not status.sd or not status.gemma:
        alerts = []
        if not status.sd:
            alerts.append(
'<div style="display:flex; align-items:center; gap:18px;">'
'<span style="font-size:26px;">🎨</span>'
'<div>'
'<strong style="color:#d70015; font-size:15px; display:block; font-weight:700; letter-spacing:0.02em;">视觉渲染引擎 (Stable Diffusion) 未启动</strong>'
'<p style="color:#48484a; font-size:13px; margin:4px 0 0 0; line-height:1.4;">请启动 SD WebUI 并确保开启 <code style="background:rgba(0,0,0,0.04); padding:2px 6px; border-radius:6px; color:#d70015; font-family:monospace; border:1px solid rgba(255,59,48,0.15);">--api</code> 模式 (监听端口 7860)</p>'
'</div>'
'</div>'
            )
        if not status.gemma:
            alerts.append(
'<div style="display:flex; align-items:center; gap:18px;">'
'<span style="font-size:26px;">🧠</span>'
'<div>'
'<strong style="color:#d70015; font-size:15px; display:block; font-weight:700; letter-spacing:0.02em;">决策博弈引擎 (Ollama/Gemma) 未就绪</strong>'
'<p style="color:#48484a; font-size:13px; margin:4px 0 0 0; line-height:1.4;">请在终端运行: <code style="background:rgba(0,0,0,0.04); padding:2px 6px; border-radius:6px; color:#d70015; font-family:monospace; border:1px solid rgba(255,59,48,0.15);">ollama run deepseek-v4-pro</code> (监听端口 11434)</p>'
'</div>'
'</div>'
            )

        st.markdown(f"""
<div style="background: rgba(255, 59, 48, 0.05); border: 1px solid rgba(255, 59, 48, 0.15); border-radius: 16px; padding: 22px 28px; margin: 30px 0; display: flex; flex-direction: column; gap: 20px; box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04); backdrop-filter: blur(25px) saturate(180%); position: relative; z-index: 9999;">
<div style="position: absolute; top: 0; left: 0; width: 5px; height: 100%; background: #ff3b30;"></div>
{"".join(alerts)}
</div>
""", unsafe_allow_html=True)

        col_demo, _ = st.columns([1, 3])
        with col_demo:
            if st.button("🎭 切换演示模式", key="demo_toggle_alert"):
                st.session_state["demo_mode"] = not st.session_state.get("demo_mode", False)
                st.rerun()

    if st.session_state.get("demo_mode", False):
        st.markdown("""
        <div style="background: rgba(74, 222, 128, 0.1); border: 1px solid rgba(74, 222, 128, 0.3);
             border-radius: 10px; padding: 10px 18px; margin-top: 8px;">
            <span style="color: #4ADE80; font-weight: 700;">🎭 演示模式已激活</span>
            <span style="color: #94a3b8; font-size: 13px; margin-left: 10px;">SD/LLM 将使用预置数据响应</span>
        </div>
        """, unsafe_allow_html=True)


def render_presentation_toggle():
    """侧边栏演示控制面板"""
    with st.sidebar:
        with st.expander("🎬 演示控制", expanded=False):
            pres_mode = st.toggle("演示模式 (隐藏调试信息)",
                                   value=st.session_state.get("presentation_mode", False),
                                   key="pres_toggle")
            st.session_state["presentation_mode"] = pres_mode

            demo_mode = st.toggle("离线演示 (SD/LLM 预置数据)",
                                   value=st.session_state.get("demo_mode", False),
                                   key="demo_toggle_sidebar")
            st.session_state["demo_mode"] = demo_mode


# Compatibility exports: new pages should import these from
# src.ui.design_system and src.ui.chart_theme directly.
from src.ui.chart_theme import (  # noqa: E402,F401
    CHART_PALETTE,
    apply_plotly_polar_theme,
    apply_plotly_theme,
    get_chart_palette,
    rgba_from_hex,
)
from src.ui.design_system import (  # noqa: E402,F401
    render_page_banner,
    render_section_intro,
    render_summary_cards,
)
