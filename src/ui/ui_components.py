import streamlit as st
from html import escape
from pathlib import Path
import os
import urllib.parse

from src.utils.service_check import check_engine_status, is_port_alive, EngineStatus

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
    
    # 🧪 5 大核心实验室导航架构
    nav_data = [
        {"lab": "01 资产测度", "path": "pages/1_数据底座与规划策略.py", "subs": ["MPI 更新潜力测度", "策略语义与红线", "多源异构底座"]},
        {"lab": "02 全息诊断", "path": "pages/2_现状空间全景诊断.py", "subs": ["3D 现状全息底座", "地块级诊断面板"]},
        {"lab": "03 方案模拟", "path": "pages/3_AIGC设计推演.py", "subs": ["AIGC 视觉图景衍生", "本地算力调度"]},
        {"lab": "04 博弈决策", "path": "pages/4_LLM博弈决策.py", "subs": ["多主体利益协商", "动态共识雷达", "图纸提示词助手"]},
        {"lab": "05 成果展示", "path": "pages/5_更新设计成果展示.py", "subs": ["3D 更新设计全景", "规划文本成果", "重点效果展示"]},
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
        flex-wrap: wrap !important;
        background: transparent !important; /* 移除整体背景，突出独立感 */
        padding: 0 !important;
        border: none !important;
        width: 100% !important;
        max-width: 100% !important;
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
        flex: 0 1 auto !important;
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
        return name

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
            sub_query = urllib.parse.quote(str(sub), safe="")
            nav_html += f'<a href="/{slug}?sub={sub_query}" target="_self" class="dropdown-item">{sub}</a>'
        
        nav_html += '</div></div></div></div>'
    
    nav_html += '</div></div>'
    st.markdown(nav_html, unsafe_allow_html=True)

    st.markdown("---")

# 🔗 导出别名以实现向后兼容 (修复新页面 ImportError)
show_nav_bar = render_top_nav

def render_engine_status_alert():
    """渲染极具冲击力的引擎未启动引导提示 (Apple/Cyber 风格)"""
    status = check_engine_status()

    # 只有当任一引擎离线时才显示
    if not status.sd or not status.gemma:
        alerts = []
        if not status.sd:
            alerts.append(
'<div style="display:flex; align-items:center; gap:18px;">'
'<span style="font-size:26px; filter:drop-shadow(0 0 8px rgba(239,68,68,0.5));">🎨</span>'
'<div>'
'<strong style="color:#fca5a5; font-size:15px; display:block; font-weight:800; letter-spacing:0.02em; text-shadow:0 2px 4px rgba(0,0,0,0.5);">视觉渲染引擎 (Stable Diffusion) 未启动</strong>'
'<p style="color:rgba(248,250,252,0.85); font-size:13px; margin:4px 0 0 0; line-height:1.4;">请启动 SD WebUI 并确保开启 <code style="background:rgba(0,0,0,0.4); padding:2px 6px; border-radius:6px; color:#f87171; font-family:monospace; border:1px solid rgba(239,68,68,0.2);">--api</code> 模式 (监听端口 7860)</p>'
'</div>'
'</div>'
            )
        if not status.gemma:
            alerts.append(
'<div style="display:flex; align-items:center; gap:18px;">'
'<span style="font-size:26px; filter:drop-shadow(0 0 8px rgba(239,68,68,0.5));">🧠</span>'
'<div>'
'<strong style="color:#fca5a5; font-size:15px; display:block; font-weight:800; letter-spacing:0.02em; text-shadow:0 2px 4px rgba(0,0,0,0.5);">决策博弈引擎 (Ollama/Gemma) 未就绪</strong>'
'<p style="color:rgba(248,250,252,0.85); font-size:13px; margin:4px 0 0 0; line-height:1.4;">请在终端运行: <code style="background:rgba(0,0,0,0.4); padding:2px 6px; border-radius:6px; color:#f87171; font-family:monospace; border:1px solid rgba(239,68,68,0.2);">ollama run gemma4:e2b-it-q4_K_M</code> (监听端口 11434)</p>'
'</div>'
'</div>'
            )

        st.markdown(f"""
<div style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.18), rgba(185, 28, 28, 0.12)); border: 1px solid rgba(239, 68, 68, 0.45); border-radius: 16px; padding: 22px 28px; margin: 30px 0; display: flex; flex-direction: column; gap: 20px; box-shadow: 0 12px 45px rgba(0, 0, 0, 0.35), inset 0 0 20px rgba(239, 68, 68, 0.08); backdrop-filter: blur(25px) saturate(180%); position: relative; z-index: 9999;">
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


def render_page_banner(title, description, eyebrow=None, tags=None, metrics=None):
    """渲染带指标和标签的统一页面头图区。"""
    load_global_css()
    tags = tags or []
    metrics = metrics or []

    tags_html = "".join(
        f'<span class="page-chip">{escape(str(tag))}</span>'
        for tag in tags
    )
    metrics_html = "".join(
        (
            '<div class="page-banner-metric">'
            f'<div class="page-banner-value">{escape(str(item.get("value", "")))}</div>'
            f'<div class="page-banner-label">{escape(str(item.get("label", "")))}</div>'
            f'<div class="page-banner-meta">{escape(str(item.get("meta", "")))}</div>'
            "</div>"
        )
        for item in metrics
    )

    eyebrow_html = ""
    if eyebrow:
        eyebrow_html = f'<div class="page-eyebrow">{escape(str(eyebrow))}</div>'

    html = (
        '<section class="page-banner">'
        '<div class="page-banner-copy">'
        f"{eyebrow_html}"
        f"<h1>{escape(str(title))}</h1>"
        f"<p>{escape(str(description))}</p>"
        f'<div class="page-chip-row">{tags_html}</div>'
        "</div>"
        f'<div class="page-banner-grid">{metrics_html}</div>'
        "</section>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_section_intro(title, description="", eyebrow=None):
    """渲染统一的段落引导标题。"""
    load_global_css()
    eyebrow_html = ""
    if eyebrow:
        eyebrow_html = f'<div class="section-eyebrow">{escape(str(eyebrow))}</div>'

    desc_html = ""
    if description:
        desc_html = f"<p>{escape(str(description))}</p>"

    html = (
        '<div class="section-intro">'
        f"{eyebrow_html}"
        f"<h2>{escape(str(title))}</h2>"
        f"{desc_html}"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_summary_cards(cards):
    """渲染统一的摘要指标卡片。"""
    load_global_css()
    parts = ['<div class="summary-grid">']
    for card in cards:
        parts.append(
            '<div class="summary-card">'
            f'<span class="summary-value">{escape(str(card.get("value", "")))}</span>'
            f'<h4>{escape(str(card.get("title", "")))}</h4>'
            f'<p>{escape(str(card.get("desc", "")))}</p>'
            "</div>"
        )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


CHART_PALETTE = [
    "#818cf8",
    "#34d399",
    "#f59e0b",
    "#f472b6",
    "#22d3ee",
    "#fb7185",
]


def get_chart_palette():
    """返回统一的图表色板。"""
    return list(CHART_PALETTE)


def rgba_from_hex(hex_color, alpha):
    """将十六进制颜色转为 rgba 字符串。"""
    color = hex_color.lstrip("#")
    if len(color) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    return f"rgba({red}, {green}, {blue}, {alpha})"


def apply_plotly_theme(fig, title=None, height=360, showlegend=True, legend_orientation="h"):
    """应用统一的二维图表主题。"""
    title_block = None
    if title:
        title_block = dict(text=title, x=0.0, xanchor="left", font=dict(size=15, color="#f8fafc"))

    fig.update_layout(
        title=title_block,
        height=height,
        showlegend=showlegend,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1"),
        margin=dict(l=20, r=20, t=58 if title else 24, b=20),
        legend=dict(
            orientation=legend_orientation,
            x=0,
            xanchor="left",
            y=1.02 if legend_orientation == "h" else 1,
            yanchor="bottom" if legend_orientation == "h" else "top",
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11, color="#94a3b8"),
        ),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(99,102,241,0.12)",
        linecolor="rgba(148,163,184,0.18)",
        zeroline=False,
        tickfont=dict(size=11, color="#cbd5e1"),
        title_font=dict(size=12, color="#94a3b8"),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(99,102,241,0.12)",
        linecolor="rgba(148,163,184,0.18)",
        zeroline=False,
        tickfont=dict(size=11, color="#cbd5e1"),
        title_font=dict(size=12, color="#94a3b8"),
    )
    return fig


def apply_plotly_polar_theme(fig, title=None, height=320, radial_range=None, accent_color="#818cf8"):
    """应用统一的极坐标雷达图主题。"""
    title_block = None
    if title:
        title_block = dict(text=title, font=dict(size=13, color=accent_color))

    fig.update_layout(
        title=title_block,
        height=height,
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"),
        margin=dict(l=34, r=34, t=44 if title else 20, b=20),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=radial_range or [0, 1],
                showticklabels=False,
                gridcolor="rgba(99,102,241,0.15)",
                linecolor="rgba(99,102,241,0.15)",
            ),
            angularaxis=dict(
                gridcolor="rgba(99,102,241,0.15)",
                linecolor="rgba(99,102,241,0.15)",
                color="#cbd5e1",
                tickfont=dict(size=10),
            ),
        ),
    )
    return fig


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
