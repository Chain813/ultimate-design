import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import os

# 🌟 强制隐藏侧边栏，设定宽屏模式
st.set_page_config(page_title="系统主页", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🎨 PREMIUM DESIGN SYSTEM v2.0 (首页专属增强)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    html, body, [class*="css"], .stApp, .stMarkdown, p, span, label { font-family: 'Inter', sans-serif !important; }

    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    footer { display: none !important; }

    .block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; max-width: 1500px; }
    .stApp { background: linear-gradient(135deg, #0a0f1e 0%, #0f172a 40%, #131b2e 70%, #0d1321 100%) !important; }

    /* 导航栏 */
    a[data-testid="stPageLink-NavLink"] {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.8)) !important;
        border: 1px solid rgba(99, 102, 241, 0.15) !important;
        border-radius: 10px !important; padding: 0.55rem 0.8rem !important;
        display: flex !important; justify-content: center !important; text-decoration: none !important;
        transition: all 0.35s cubic-bezier(0.4,0,0.2,1) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
    }
    a[data-testid="stPageLink-NavLink"]:hover {
        background: linear-gradient(145deg, rgba(99,102,241,0.15), rgba(139,92,246,0.12)) !important;
        border-color: rgba(99,102,241,0.5) !important; transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(99,102,241,0.2), 0 0 15px rgba(139,92,246,0.1) !important;
    }
    a[data-testid="stPageLink-NavLink"] p, a[data-testid="stPageLink-NavLink"] span {
        font-size: 15px !important; font-weight: 600 !important; color: #e2e8f0 !important;
        margin: 0 !important; letter-spacing: 0.02em !important;
    }

    h1, h2, h3, h4, h5, label, .stMarkdown p { color: #f8fafc !important; }
    hr { border: none !important; height: 1px !important; background: linear-gradient(90deg, transparent, rgba(99,102,241,0.3), transparent) !important; margin: 1.5rem 0 !important; }

    /* 主视觉玻璃面板 */
    .glass-hero {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.4), rgba(15, 23, 42, 0.6));
        backdrop-filter: blur(16px);
        border: 1px solid rgba(99, 102, 241, 0.12);
        border-radius: 20px;
        padding: 50px 40px;
        margin: 10px 0 30px 0;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255,255,255,0.05);
        position: relative;
        overflow: hidden;
    }
    .glass-hero::before {
        content: '';
        position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
        background: radial-gradient(circle at 30% 40%, rgba(99,102,241,0.06) 0%, transparent 50%),
                    radial-gradient(circle at 70% 60%, rgba(139,92,246,0.04) 0%, transparent 50%);
        animation: heroGlow 8s ease-in-out infinite alternate;
    }
    @keyframes heroGlow { 0% { opacity: 0.5; } 100% { opacity: 1; } }

    /* 模块卡片 */
    .module-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.5), rgba(15, 23, 42, 0.4));
        border: 1px solid rgba(99, 102, 241, 0.1);
        border-radius: 16px;
        padding: 24px;
        transition: all 0.4s cubic-bezier(0.4,0,0.2,1);
        cursor: pointer;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }
    .module-card::after {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(135deg, rgba(99,102,241,0.05), transparent);
        opacity: 0; transition: opacity 0.4s ease;
        border-radius: 16px;
    }
    .module-card:hover {
        border-color: rgba(99, 102, 241, 0.35);
        transform: translateY(-6px);
        box-shadow: 0 16px 48px rgba(99, 102, 241, 0.12), 0 0 20px rgba(139, 92, 246, 0.06);
    }
    .module-card:hover::after { opacity: 1; }

    /* AIGC 指挥台高亮入口 */
    .aigc-banner {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.08), rgba(236, 72, 153, 0.06));
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 14px;
        padding: 24px 28px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }
    .aigc-banner::before {
        content: '';
        position: absolute; top: 0; right: 0; width: 200px; height: 200px;
        background: radial-gradient(circle, rgba(139, 92, 246, 0.08), transparent);
    }

    ::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.3); border-radius: 3px; }

    /* 地图容器样式 */
    .map-container {
        border-radius: 18px;
        overflow: hidden;
        border: 1px solid rgba(99, 102, 241, 0.2);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🧭 顶部导航栏
# ==========================================
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
with col1: st.page_link("app.py", label="🏠 系统主页", use_container_width=True)
with col2: st.page_link("pages/1_数字孪生沙盘.py", label="🌳 数字孪生沙盘", use_container_width=True)
with col3: st.page_link("pages/2_AIGC风貌管控.py", label="🎨 风貌管控", use_container_width=True)
with col4: st.page_link("pages/3_交通与人口.py", label="🚥 交通与人口", use_container_width=True)
with col5: st.page_link("pages/4_数据管理中心.py", label="📊 数据管理", use_container_width=True)
with col6: st.page_link("pages/5_LLM 情感分析.py", label="💬 情感分析", use_container_width=True)
with col7: st.page_link("pages/6_数据总览.py", label="📋 数据总览", use_container_width=True)

# ==========================================
# 🏠 顶部主视觉区 (Hero Section)
# ==========================================
st.markdown("""
<div class="glass-hero">
    <h1 style="text-align: center; font-size: 2.6rem; margin-bottom: 8px; font-weight: 800;
               background: linear-gradient(135deg, #e2e8f0, #818cf8, #a78bfa);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
        🏙️ 长春伪满皇宫周边街区
    </h1>
    <h2 style="text-align: center; font-size: 1.5rem; margin-bottom: 12px; font-weight: 600;
               color: #c7d2fe !important; border: none; padding: 0;
               background: linear-gradient(135deg, #c7d2fe, #818cf8);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
        多模态微更新决策支持平台
    </h2>
    <p style="text-align: center; font-size: 0.95rem; color: #64748b !important; letter-spacing: 0.1em; margin-bottom: 28px;">
        Multi-modal Micro-renewal Decision Support System for Historic Districts
    </p>
    <hr style="border-color: rgba(99,102,241,0.15); margin: 24px 60px;">
    <p style="font-size: 1.05rem; line-height: 1.9; text-align: center; color: #94a3b8 !important; max-width: 900px; margin: 0 auto;">
        本平台整合了 <b style="color: #a5b4fc !important;">空间数字孪生 (Digital Twin)</b>、
        <b style="color: #a5b4fc !important;">计算机视觉 (CV)</b> 与
        <b style="color: #a5b4fc !important;">生成式大模型 (AIGC)</b> 技术，
        通过多源城市数据的跨尺度耦合，为历史工业街区的城市设计与微更新提供数据支撑与空间决策辅助。
    </p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 🚀 中部：AIGC 核心入口
# ==========================================
st.markdown("### ⚡ AIGC 风貌指挥台 (AIGC Console)")
st.markdown("""
<div class="aigc-banner">
    <h3 style="margin-top: 0; color: #c7d2fe !important;">🎨 AIGC 联觉推演系统</h3>
    <p style="color: #94a3b8 !important; line-height: 1.7; margin-bottom: 0;">
        输入地块现状照片，连接本地算力一键调用 <b style="color: #a5b4fc;">Stable Diffusion</b> 引擎，
        输出超高分辨率的概念风貌效果图。支持 <b style="color: #a5b4fc;">ControlNet</b> 深度/边缘精准控制。
    </p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 🗺️ 区域全景看板 (Interactive Map)
# ==========================================
st.markdown("### 🗺️ 街区范围及改造红线 (Project Boundary)")

# 载入 GeoJSON 并渲染地图
def render_project_map():
    # 中心点：长春伪满皇宫
    m = folium.Map(
        location=[43.903, 125.337],
        zoom_start=15,
        tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
    )
    
    geojson_path = "data/空间数据/Boundary_Scope.geojson"
    try:
        if os.path.exists(geojson_path):
            with open(geojson_path, 'r', encoding='utf-8') as f:
                geo_data = json.load(f)
            
            # 使用自定义样式渲染 GeoJSON
            folium.GeoJson(
                geo_data,
                style_function=lambda feature: {
                    'fillColor': feature['properties'].get('color', '#6366f1'),
                    'color': feature['properties'].get('color', '#6366f1'),
                    'weight': 2,
                    'fillOpacity': 0.35,
                },
                tooltip=folium.GeoJsonTooltip(fields=['name', 'description'], labels=True)
            ).add_to(m)
        else:
            st.error(f"❌ 未找到边界数据文件: {geojson_path}")
    except Exception as e:
        st.error(f"⚠️ 地图加载失败: {e}")

    # 渲染到 Streamlit 页面
    with st.container():
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        st_folium(m, width="100%", height=500, returned_objects=[])
        st.markdown('</div>', unsafe_allow_html=True)

render_project_map()

st.page_link("pages/2_AIGC风貌管控.py", label="🚀 立即进入 AIGC 实时推理工作站", use_container_width=True)

st.markdown("---")
st.markdown("### 🧭 核心子系统导览 (点击进入)")
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown('<div class="module-card">', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1524661135-423995f22d0b?q=80&w=800&auto=format&fit=crop",
             use_container_width=True)
    st.markdown("#### 🌳 模块 1：数字孪生沙盘")
    st.markdown(
        "<p style='color:#cbd5e1 !important; font-size:0.95rem; height: 45px;'>基于 DeepLabV3 的大规模绿视率 (GVI) 自动化测度与 3D 高精度落位。</p>",
        unsafe_allow_html=True)
    st.page_link("pages/1_数字孪生沙盘.py", label="🚀 启动数字沙盘", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="module-card">', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=800&auto=format&fit=crop",
             use_container_width=True)
    st.markdown("#### 🎨 模块 2：AIGC 风貌管控")
    st.markdown(
        "<p style='color:#cbd5e1 !important; font-size:0.95rem; height: 45px;'>基于 Stable Diffusion + ControlNet 的工业遗产风貌修缮与沉浸式推演。</p>",
        unsafe_allow_html=True)
    st.page_link("pages/2_AIGC风貌管控.py", label="🎨 启动风貌管控", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c3:
    st.markdown('<div class="module-card">', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1519501025264-65ba15a82390?q=80&w=800&auto=format&fit=crop",
             use_container_width=True)
    st.markdown("#### 🚥 模块 3：交通与人口")
    st.markdown(
        "<p style='color:#cbd5e1 !important; font-size:0.95rem; height: 45px;'>商业活力潮汐聚类与多模态公共交通路网的高通量空间耦合分析。</p>",
        unsafe_allow_html=True)
    st.page_link("pages/3_交通与人口.py", label="🚀 启动交通探针", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
c4, c5 = st.columns(2)

with c4:
    st.markdown('<div class="module-card">', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=800&auto=format&fit=crop",
             use_container_width=True)
    st.markdown("#### 📊 模块 4：数据管理中心")
    st.markdown(
        "<p style='color:#cbd5e1 !important; font-size:0.95rem; height: 45px;'>多源数据融合管理、上传更新与可视化分析的一站式平台。</p>",
        unsafe_allow_html=True)
    st.page_link("pages/4_数据管理中心.py", label="🚀 进入数据中心", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c5:
    st.markdown('<div class="module-card">', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1529156069898-49953e39b3ac?q=80&w=800&auto=format&fit=crop",
             use_container_width=True)
    st.markdown("#### 💬 模块 5：LLM 情感分析")
    st.markdown(
        "<p style='color:#cbd5e1 !important; font-size:0.95rem; height: 45px;'>基于大模型的社会情感计算、舆情热力图与智能决策建议。</p>",
        unsafe_allow_html=True)
    st.page_link("pages/5_LLM 情感分析.py", label="🚀 启动情感分析", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
