import streamlit as st


def render_top_nav():
    st.markdown("""
    <style>
    /* ==========================================
       🎨 PREMIUM DESIGN SYSTEM v2.0
       Multi-modal Micro-renewal Decision Platform
       Base: Deep Space Dark + Glassmorphism
    ========================================== */

    /* --- Google Fonts 加载 --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* --- 全局字体基底 --- */
    html, body, [class*="css"], .stApp, .stMarkdown, p, span, label, li, td, th {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }

    /* --- 隐藏 Streamlit 默认框架 --- */
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    footer { display: none !important; }
    #MainMenu { display: none !important; }

    /* --- 主容器布局 --- */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 1600px;
    }

    /* ==========================================
       🌌 深空背景 + 微粒噪点纹理
    ========================================== */
    .stApp {
        background: linear-gradient(135deg, #0a0f1e 0%, #0f172a 40%, #131b2e 70%, #0d1321 100%) !important;
        background-attachment: fixed !important;
    }

    /* ==========================================
       🧭 顶部导航栏 (发光悬浮效果)
    ========================================== */
    a[data-testid="stPageLink-NavLink"] {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.8)) !important;
        border: 1px solid rgba(99, 102, 241, 0.15) !important;
        border-radius: 10px !important;
        padding: 0.55rem 0.8rem !important;
        display: flex !important;
        justify-content: center !important;
        text-decoration: none !important;
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
    }
    a[data-testid="stPageLink-NavLink"]:hover {
        background: linear-gradient(145deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.12)) !important;
        border-color: rgba(99, 102, 241, 0.5) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.2), 0 0 15px rgba(139, 92, 246, 0.1) !important;
    }
    a[data-testid="stPageLink-NavLink"] p,
    a[data-testid="stPageLink-NavLink"] span {
        font-size: 15px !important;
        font-weight: 600 !important;
        color: #e2e8f0 !important;
        margin: 0 !important;
        letter-spacing: 0.02em !important;
    }

    /* ==========================================
       📝 全局排版 (渐变标题 + 柔光文字)
    ========================================== */
    h1 {
        background: linear-gradient(135deg, #e2e8f0, #818cf8, #a78bfa) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
    }
    h2 {
        color: #e2e8f0 !important;
        font-weight: 700 !important;
        border-bottom: 2px solid rgba(99, 102, 241, 0.3);
        padding-bottom: 8px;
        letter-spacing: -0.01em !important;
    }
    h3 {
        color: #c7d2fe !important;
        font-weight: 600 !important;
    }
    h4, h5 {
        color: #a5b4fc !important;
        font-weight: 600 !important;
    }
    label, .stMarkdown p {
        color: #cbd5e1 !important;
        line-height: 1.7 !important;
    }

    /* ==========================================
       📊 Metric 指标卡片 (发光呼吸效果)
    ========================================== */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.5)) !important;
        border: 1px solid rgba(99, 102, 241, 0.12) !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stMetric"]:hover {
        border-color: rgba(99, 102, 241, 0.35) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.12) !important;
        transform: translateY(-2px) !important;
    }
    [data-testid="stMetricValue"] {
        color: #f1f5f9 !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    [data-testid="stMetricDelta"] {
        font-weight: 600 !important;
    }

    /* ==========================================
       🖼️ 侧边栏 (磨砂玻璃 + 边界发光)
    ========================================== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.95), rgba(10, 15, 30, 0.98)) !important;
        border-right: 1px solid rgba(99, 102, 241, 0.15) !important;
        backdrop-filter: blur(20px) !important;
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        transition: all 0.2s ease !important;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        color: #818cf8 !important;
    }

    /* --- 侧边栏表单控件 --- */
    div[data-baseweb="select"] > div,
    textarea, input,
    section[data-testid="stFileUploader"] {
        background-color: rgba(30, 41, 59, 0.6) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 8px !important;
        transition: border-color 0.3s ease !important;
    }
    div[data-baseweb="select"] > div:focus-within,
    textarea:focus, input:focus {
        border-color: rgba(99, 102, 241, 0.5) !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1) !important;
    }

    /* ==========================================
       📐 Plotly 图表容器 + DeckGL 3D 地图
    ========================================== */
    [data-testid="stDeckGlJsonChart"] {
        height: 75vh !important;
        min-height: 650px !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 1px solid rgba(99, 102, 241, 0.1) !important;
    }
    .stPlotlyChart {
        border-radius: 12px !important;
        overflow: hidden !important;
    }

    /* ==========================================
       🔲 通用表格样式
    ========================================== */
    [data-testid="stDataFrame"],
    .stDataFrame {
        border-radius: 10px !important;
        overflow: hidden !important;
    }
    [data-testid="stDataFrame"] th {
        background-color: rgba(30, 41, 59, 0.8) !important;
        color: #c7d2fe !important;
        font-weight: 600 !important;
    }

    /* ==========================================
       💊 Tab 组件
    ========================================== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(30, 41, 59, 0.5) !important;
        border-radius: 8px 8px 0 0 !important;
        color: #94a3b8 !important;
        padding: 8px 20px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(99, 102, 241, 0.15) !important;
        color: #a5b4fc !important;
        border-bottom: 2px solid #818cf8 !important;
    }

    /* ==========================================
       ⚡ 按钮组件 (渐变 + 呼吸)
    ========================================== */
    .stButton > button {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.15)) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        font-weight: 600 !important;
        padding: 8px 24px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.35), rgba(139, 92, 246, 0.3)) !important;
        border-color: rgba(99, 102, 241, 0.6) !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.2) !important;
        transform: translateY(-2px) !important;
    }

    /* ==========================================
       📢 Alert/Info/Warning/Error 组件
    ========================================== */
    [data-testid="stAlert"] {
        border-radius: 10px !important;
        border-left-width: 4px !important;
        backdrop-filter: blur(10px) !important;
    }

    /* ==========================================
       🎚️ Slider 滑块轨道美化
    ========================================== */
    .stSlider [data-baseweb="slider"] [role="slider"] {
        background-color: #818cf8 !important;
    }

    /* ==========================================
       📜 自适应滚动条美化
    ========================================== */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: rgba(15, 23, 42, 0.5); }
    ::-webkit-scrollbar-thumb {
        background: rgba(99, 102, 241, 0.3);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover { background: rgba(99, 102, 241, 0.5); }

    /* ==========================================
       ✨ 分割线美化
    ========================================== */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.3), transparent) !important;
        margin: 1.5rem 0 !important;
    }

    /* ==========================================
       🖼️ Expander 折叠面板
    ========================================== */
    [data-testid="stExpander"] {
        background: rgba(30, 41, 59, 0.4) !important;
        border: 1px solid rgba(99, 102, 241, 0.1) !important;
        border-radius: 10px !important;
    }
    [data-testid="stExpander"] summary {
        color: #c7d2fe !important;
        font-weight: 600 !important;
    }

    </style>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1: st.page_link("app.py", label="🏠 主页", use_container_width=True)
    with c2: st.page_link("pages/1_数字孪生沙盘.py", label="🌳 沙盘", use_container_width=True)
    with c3: st.page_link("pages/2_AIGC风貌管控.py", label="🎨 风貌", use_container_width=True)
    with c4: st.page_link("pages/3_交通与人口.py", label="🚥 交通", use_container_width=True)
    with c5: st.page_link("pages/4_数据管理中心.py", label="📊 数据", use_container_width=True)
    with c6: st.page_link("pages/5_LLM 情感分析.py", label="💬 情感", use_container_width=True)
    with c7: st.page_link("pages/6_数据总览.py", label="📋 总览", use_container_width=True)
    st.markdown("---")
