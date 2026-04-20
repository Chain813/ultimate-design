import streamlit as st
from pathlib import Path
import os
import urllib.parse
import socket

def load_global_css():
    """加载全局统一的样式文件 (通过绝对路径确保子页面调用正常)"""
    base_path = Path(__file__).parent
    css_path = base_path / "assets" / "style.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            # 🚨 严禁使用 f-string 注入 CSS，否则其中的 {} 会被解析导致报错或失效
            css_content = f.read()
            st.markdown("<style>" + css_content + "</style>", unsafe_allow_html=True)

def render_top_nav():
    """下一代全景悬停导航栏 (Multi-level Hover Dropdown)"""
    load_global_css()
    
    # 🧪 4 大实验室导航架构
    nav_data = [
        {"lab": "01 数据策略", "path": "pages/1_数据底座与规划策略.py", "subs": ["MPI 资产评估", "规划策略萃取", "底座文件管理"]},
        {"lab": "02 全息诊断", "path": "pages/2_数字孪生与全息诊断.py", "subs": ["3D 区域全景", "交通潮汐诊断", "社会情感评价"]},
        {"lab": "03 方案推演", "path": "pages/3_AIGC设计推演.py", "subs": ["AIGC 影像生成"]},
        {"lab": "04 决策博弈", "path": "pages/4_LLM博弈决策.py", "subs": ["LLM 多方协商"]},
    ]

    # 💎 CSS3 悬停交互引擎
    st.markdown(f"""
    <style>
    :root {{ --apple-bg: rgba(22, 22, 23, 0.85); }}
    
    /* 🍏 Apple 风格顶部主轴 (对比度优化版) */
    .nav-bar {{
        position: fixed; top: 0; left: 0; width: 100%; height: 50px; /* 锁定 50px 高度 */
        background: var(--apple-bg);
        backdrop-filter: saturate(180%) blur(20px);
        display: flex; justify-content: center; align-items: center;
        z-index: 999999; border-bottom: 1px solid rgba(255,255,255,0.08);
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
    }}
    
    .nav-container {{
        width: 100%; max-width: 1000px; display: flex; justify-content: space-around;
        padding: 0 20px;
    }}
    
    .nav-item {{
        color: rgba(245, 245, 247, 0.95); font-size: 13px; font-weight: 600; /* 回归 13px */
        cursor: pointer; position: relative;
        height: 50px; display: flex; align-items: center;
        padding: 0 15px; letter-spacing: 0.03em;
        text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        transition: color 0.3s;
    }}
    
    .nav-item:hover {{ color: #ffffff; text-shadow: 0 0 10px rgba(0, 113, 227, 0.5); }}
    
    /* 彻底杜绝主页及所有链接的下划线与蓝色 (全状态封锁) */
    .nav-bar a, .nav-bar a:link, .nav-bar a:visited, .nav-bar a:active {{
        text-decoration: none !important;
        color: rgba(245, 245, 247, 0.95) !important;
    }}
    .nav-bar a:hover {{
        color: #ffffff !important;
    }}
    
    /* 🍏 全宽沉浸下拉菜单 (跟随 50px 偏移) */
    .dropdown-content {{
        position: fixed; top: 50px; left: 0; width: 100vw; height: 0;
        background: rgba(10, 10, 12, 0.98);
        backdrop-filter: saturate(180%) blur(40px);
        overflow: hidden; opacity: 0; visibility: hidden;
        /* 核心：增加 0.1s 的闭合延迟 (transition-delay) */
        transition: height 0.4s cubic-bezier(0.4, 0, 0.2, 1) 0.1s, 
                    opacity 0.3s ease 0.1s, 
                    visibility 0s linear 0.5s;
        display: flex; justify-content: center;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }}
    
    /* 激活态：取消延迟，实现瞬时开启 */
    .nav-item:hover .dropdown-content {{
        height: 280px; opacity: 1; visibility: visible;
        transition-delay: 0s;
    }}
    
    .submenu-container {{
        width: 100%; max-width: 1000px; padding: 40px 20px;
        display: flex; gap: 80px; align-items: flex-start;
    }}
    
    .submenu-column {{ display: flex; flex-direction: column; gap: 12px; }}
    .submenu-title {{ color: #a1a1a6; font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 10px; }}
    
    .dropdown-item {{
        color: #ffffff; font-size: 20px; font-weight: 700; text-decoration: none !important;
        transition: color 0.2s, transform 0.2s; white-space: nowrap;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }}
    
    .dropdown-item:hover {{ color: #0071e3; }} /* Apple Blue 强调色 */
    
    /* 让子项逐个浮现的微动效 */
    .nav-item:hover .dropdown-item {{
        animation: fadeInUp 0.5s ease forwards; opacity: 0;
    }}
    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* 🍏 Apple 风格分段控制器 (Segmented Control) 独立胶囊版 */
    div[data-testid="stRadio"] > div[role="radiogroup"] {{
        display: flex !important;
        flex-direction: row !important;
        background: transparent !important; /* 移除整体背景，突出独立感 */
        padding: 0 !important;
        border: none !important;
        width: fit-content !important;
        gap: 12px !important; /* 增加胶囊间的间隙 */
        margin: 15px 0 !important;
    }}
    
    /* 🚀 外科手术式：仅隐藏第一个子容器（圆圈），强制显示文字 */
    div[data-testid="stRadio"] label > div:first-child {{
        display: none !important;
        width: 0 !important;
        height: 0 !important;
        position: absolute !important;
    }}
    
    /* 强力保活：确保文字及其父容器可见 */
    div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"],
    div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p {{
        visibility: visible !important;
        display: block !important;
        opacity: 1 !important;
        color: inherit !important;
        width: 100% !important;
        text-align: center !important;
        margin: 0 !important;
    }}

    /* 极致去除 BaseWeb 的背景与阴影干扰 */
    div[data-testid="stRadio"] [data-baseweb="radio"],
    div[data-testid="stRadio"] [role="radiogroup"] div {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    
    /* 每一个选项都成为一个独立的胶囊 */
    div[data-testid="stRadio"] label {{
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        padding: 10px 24px !important;
        border-radius: 50px !important; /* 纯圆形胶囊 */
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        cursor: pointer !important;
        margin: 0 !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
    }}
    
    /* 选中状态：页面变亮，呈现亮色胶囊 */
    div[data-testid="stRadio"] label:has(input:checked) {{
        background: #818cf8 !important; /* 核心亮度来源 */
        border: 1px solid #a5b4fc !important;
        box-shadow: 0 0 20px rgba(129, 140, 248, 0.5), 0 4px 10px rgba(0,0,0,0.3) !important;
        transform: scale(1.05) !important; /* 选中的轻微放大感 */
    }}
    
    /* 文字颜色在选中时强制设为极高对比度的纯白 */
    div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p {{
        font-size: 14px !important;
        font-weight: 600 !important;
        color: rgba(255, 255, 255, 0.6) !important;
        transition: color 0.3s !important;
    }}
    
    div[data-testid="stRadio"] label:has(input:checked) p {{
        color: #ffffff !important;
        font-weight: 800 !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }}
    
    /* 悬停态：细腻的亮度提升 */
    div[data-testid="stRadio"] label:hover:not(:has(input:checked)) {{
        background: rgba(255, 255, 255, 0.12) !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        transform: translateY(-2px);
    }}
    
    /* 弥补顶部高度 */
    .stApp {{ margin-top: 50px !important; }}
    </style>
    """, unsafe_allow_html=True)

    # --- 🏗️ 构造全宽导航 HTML ---
    import urllib.parse
    
    def get_nav_slug(p):
        name = os.path.basename(p).replace(".py", "")
        if "_" in name and name.split("_")[0].isdigit():
            name = name.split("_", 1)[1]
        return urllib.parse.quote(name)

    nav_html = '<div class="nav-bar"><div class="nav-container">'
    nav_html += '<a href="/" target="_self" class="nav-item" style="text-decoration: none !important; color: rgba(245, 245, 247, 0.95) !important; font-weight: 900 !important; font-size: 24px !important;">主页</a>'
    
    for item in nav_data:
        slug = get_nav_slug(item['path'])
        nav_html += f'''
        <div class="nav-item">
            {item['lab']}
            <div class="dropdown-content">
                <div class="submenu-container">
                    <div class="submenu-column">
                        <div class="submenu-title">功能子项探取</div>
        '''
        # 子项横向分布 (如果子项多，可以分 Column，目前先统一排布)
        for sub in item['subs']:
            nav_html += f'<a href="/{slug}" target="_self" class="dropdown-item">{sub}</a>'
        
        nav_html += '</div></div></div></div>'
    
    nav_html += '</div></div>'
    st.markdown(nav_html, unsafe_allow_html=True)

    st.markdown("---")

# 🔗 导出别名以实现向后兼容 (修复新页面 ImportError)
show_nav_bar = render_top_nav

def check_engine_status():
    """统一检测核心引擎状态 (SD=7860, Ollama=11434)"""
    def check_port(port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                return s.connect_ex(('127.0.0.1', port)) == 0
        except:
            return False
            
    return {
        "sd": check_port(7860),
        "gemma": check_port(11434)
    }

def render_engine_status_alert():
    """渲染极具冲击力的引擎未启动引导提示 (Apple/Cyber 风格)"""
    status = check_engine_status()

    # 只有当任一引擎离线时才显示
    if not status["sd"] or not status["gemma"]:
        alerts = []
        if not status["sd"]:
            alerts.append("""
                <div style="display:flex; align-items:center; gap:18px;">
                    <span style="font-size:26px; filter:drop-shadow(0 0 8px rgba(239,68,68,0.5));">🎨</span>
                    <div>
                        <strong style="color:#fca5a5; font-size:15px; display:block; font-weight:800; letter-spacing:0.02em; text-shadow:0 2px 4px rgba(0,0,0,0.5);">视觉渲染引擎 (Stable Diffusion) 未启动</strong>
                        <p style="color:rgba(248,250,252,0.85); font-size:13px; margin:4px 0 0 0; line-height:1.4;">请启动 SD WebUI 并确保开启 <code style="background:rgba(0,0,0,0.4); padding:2px 6px; border-radius:6px; color:#f87171; font-family:monospace; border:1px solid rgba(239,68,68,0.2);">--api</code> 模式 (监听端口 7860)</p>
                    </div>
                </div>
            """)
        if not status["gemma"]:
            alerts.append("""
                <div style="display:flex; align-items:center; gap:18px;">
                    <span style="font-size:26px; filter:drop-shadow(0 0 8px rgba(239,68,68,0.5));">🧠</span>
                    <div>
                        <strong style="color:#fca5a5; font-size:15px; display:block; font-weight:800; letter-spacing:0.02em; text-shadow:0 2px 4px rgba(0,0,0,0.5);">决策博弈引擎 (Ollama/Gemma) 未就绪</strong>
                        <p style="color:rgba(248,250,252,0.85); font-size:13px; margin:4px 0 0 0; line-height:1.4;">请在终端运行: <code style="background:rgba(0,0,0,0.4); padding:2px 6px; border-radius:6px; color:#f87171; font-family:monospace; border:1px solid rgba(239,68,68,0.2);">ollama run gemma4:e2b-it-q4_K_M</code> (监听端口 11434)</p>
                    </div>
                </div>
            """)

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.18), rgba(185, 28, 28, 0.12));
                    border: 1px solid rgba(239, 68, 68, 0.45); border-radius: 16px;
                    padding: 22px 28px; margin: 30px 0; display: flex; flex-direction: column; gap: 20px;
                    box-shadow: 0 12px 45px rgba(0, 0, 0, 0.35), inset 0 0 20px rgba(239, 68, 68, 0.08);
                    backdrop-filter: blur(25px) saturate(180%); position: relative; overflow: hidden; z-index: 9999;">
            <div style="position: absolute; top: 0; left: 0; width: 5px; height: 100%; background: #ef4444; box-shadow: 0 0 20px rgba(239, 68, 68, 0.6);"></div>
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
