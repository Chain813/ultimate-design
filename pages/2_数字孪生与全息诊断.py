import streamlit as st
import pandas as pd
import pydeck as pdk
import os
import numpy as np
import math
import plotly.express as px
from ui_components import render_top_nav
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.geo_transform import bd09_to_wgs84
from core_engine import get_traffic_data

# ==========================================
# 💎 页面配置
# ==========================================
st.set_page_config(page_title="数字孪生与全息诊断 | 02 实验室", layout="wide", initial_sidebar_state="expanded")
render_top_nav()

@st.cache_data
def _load_3d_data():
    df_pts = pd.read_excel("data/Changchun_Precise_Points.xlsx")
    df_ana = pd.read_csv("data/GVI_Results_Analysis.csv")
    if 'Folder' in df_ana.columns:
        df_ana['ID'] = df_ana['Folder'].str.replace('Point_', '').astype(int)
        df_ana = df_ana.groupby('ID').mean(numeric_only=True).reset_index()
    return pd.merge(df_pts, df_ana, on='ID', how='inner')

# ==========================================
# 🌌 逻辑切换架构 (已对齐全局胶囊样式)
# ==========================================
# 使用 Session State 记忆当前 Tab
if 'lab02_active_sub' not in st.session_state:
    st.session_state.lab02_active_sub = "🏙️ 3D 空间全景"

# 顶部水平导航 (核心逻辑切换点)
selected_sub = st.radio(
    "功能选择",
    ["🏙️ 3D 空间全景", "🚦 交通与活力诊断", "🗳️ 评价数据与社会感知"],
    index=["🏙️ 3D 空间全景", "🚦 交通与活力诊断", "🗳️ 评价数据与社会感知"].index(st.session_state.lab02_active_sub),
    horizontal=True,
    key="lab02_switcher"
)
st.session_state.lab02_active_sub = selected_sub

st.markdown("---")

# ==========================================
# 🌌 模块 A: 3D 空间全景 (原 Page 3 全量还原)
# ==========================================
if selected_sub == "🏙️ 3D 空间全景":
    # --- 100% 还原 Page 3 侧边栏 ---
    with st.sidebar:
        st.markdown("### 🧬 02-3D 沙盘控制台")
        metric_sel = st.selectbox("核心指标渲染：", ["🌿 绿视率", "🌤️ 天空开阔度", "🧱 空间围合度", "⚠️ 视觉杂乱度"], key="p3_metric")
        metric_map = {"绿视率": "GVI", "天空开阔度": "SVF", "空间围合度": "Enclosure", "视觉杂乱度": "Clutter"}
        cur_m = next((v for k, v in metric_map.items() if k in metric_sel), "GVI")
        
        with st.expander("📖 查看指标释义", expanded=True):
            st.caption("GVI: 街道植被占比; SVF: 天空开放指数指标...")
        
        st.markdown("---")
        st.markdown("#### 👁️ 视角控制")
        v_mode_p3 = st.radio("视角模式", ["🦅 3D鸟瞰", "🗺️ 2D平面", "🚶 漫游视角"], key="p3_view")
        
        st.markdown("---")
        st.markdown("#### 🗼 渲染引擎参数")
        l_mode_p3 = st.radio("引擎模式", ["🗼 3D柱体", "🔥 2D热力", "🌌 双模融合"], key="p3_engine")
        elev_p3 = st.slider("柱体拉伸倍数", 1, 150, 40, key="p3_elev")
        rad_p3 = st.slider("柱体覆盖半径", 5, 80, 25, key="p3_rad")

    # --- 100% 还原 Page 3 主内容 (数据链路) ---
    try:
        df_3d = _load_3d_data().copy()
    except Exception as e:
        st.error(f"数据加载失败: {e}")
        df_3d = pd.DataFrame()

    if not df_3d.empty:
        min_v, max_v = df_3d[cur_m].min(), df_3d[cur_m].max()
        if min_v == max_v:
            max_v = min_v + 1
        df_3d["Dynamic_Color"] = df_3d[cur_m].apply(lambda v: [int(255*(1-(v-min_v)/(max_v-min_v))), int(200*math.sin((v-min_v)/(max_v-min_v)*math.pi)), int(255*((v-min_v)/(max_v-min_v))), 210])

        layers_3d = []
        if l_mode_p3 in ("🗼 3D柱体", "🌌 双模融合"):
            layers_3d.append(pdk.Layer("ColumnLayer", data=df_3d, get_position=["Lng", "Lat"], get_elevation=cur_m, elevation_scale=elev_p3, radius=rad_p3, extruded=True, get_fill_color="Dynamic_Color", pickable=True))
        if l_mode_p3 in ("🔥 2D热力", "🌌 双模融合"):
            layers_3d.append(pdk.Layer("HeatmapLayer", data=df_3d, get_position=["Lng", "Lat"], get_weight=cur_m, radius_pixels=rad_p3, opacity=0.6))

        pitch_3d = 45 if v_mode_p3 == "🦅 3D鸟瞰" else (60 if "漫游" in v_mode_p3 else 0)
        st.pydeck_chart(pdk.Deck(
            layers=layers_3d,
            initial_view_state=pdk.ViewState(latitude=43.91, longitude=125.35, zoom=14.8, pitch=pitch_3d),
            map_style="light"
        ))

# ==========================================
# 🌌 模块 B: 交通与活力诊断 (原 Page 4 全量还原)
# ==========================================
elif selected_sub == "🚦 交通与活力诊断":
    # --- 100% 还原 Page 4 侧边栏 ---
    with st.sidebar:
        st.markdown("### 🚥 04-交通诊断控制")
        cur_hr_p4 = st.slider("24H 动态潮汐推演", 0, 23, 8, key="p4_time")
        
        st.markdown("---")
        st.markdown("#### 🔭 诊断视角")
        v_mode_p4 = st.radio("诊断模式", ["🦅 鸟瞰视角", "🗺️ 上帝视角", "🚶 漫游视角"], key="p4_view")
        
        st.markdown("---")
        st.markdown("#### 📊 图层叠加开关")
        show_hex_p4 = st.checkbox("🔮 开启宏观蜂窝柱 (密度聚合)", value=True, key="p4_hex")
        show_poi_p4 = st.checkbox("🔍 透视实测 POI 点", value=False, key="p4_poi")
        show_traffic_p4 = st.checkbox("🚌 交通枢纽脉冲点", value=True, key="p4_traffic")
        
        if show_hex_p4:
            h_rad_p4 = st.slider("蜂窝半径 (米)", 20, 150, 60, key="p4_rad")
            h_elev_p4 = st.slider("活力拉伸倍数", 1.0, 15.0, 5.0, key="p4_elev")

    # --- 100% 还原 Page 4 数据内容 ---
    try:
        df_poi = pd.read_csv("data/Changchun_POI_Real.csv", encoding='utf-8-sig')
    except Exception as e:
        st.error(f"POI 数据加载失败: {e}")
        df_poi = pd.DataFrame()
    if not df_poi.empty:
        layers_p4 = []
        if show_hex_p4:
            layers_p4.append(pdk.Layer("HexagonLayer", data=df_poi, get_position=["Lng", "Lat"], radius=h_rad_p4, elevation_scale=h_elev_p4, extruded=True, color_range=[[241, 238, 246], [43, 140, 190], [4, 90, 141]]))

        if show_poi_p4:
            layers_p4.append(pdk.Layer(
                "ScatterplotLayer",
                data=df_poi,
                get_position=["Lng", "Lat"],
                get_radius=30,
                get_fill_color=[99, 102, 241, 180],
                pickable=True,
            ))

        if show_traffic_p4:
            df_traffic = get_traffic_data()
            layers_p4.append(pdk.Layer(
                "ScatterplotLayer",
                data=df_traffic,
                get_position=["Lng", "Lat"],
                get_radius="Weight",
                radius_scale=3,
                get_fill_color=[239, 68, 68, 200],
                pickable=True,
            ))

        pitch_p4 = 45 if "鸟瞰" in v_mode_p4 else (60 if "漫游" in v_mode_p4 else 0)
        st.pydeck_chart(pdk.Deck(layers=layers_p4, initial_view_state=pdk.ViewState(latitude=43.91, longitude=125.35, zoom=14.2, pitch=pitch_p4), map_style="light"))

# ==========================================
# 🌌 模块 C: 社会情感评价 (原 Page 8 全量还原)
# ==========================================
elif selected_sub == "🗳️ 评价数据与社会感知":
    # --- 100% 还原 Page 8 侧边栏 ---
    with st.sidebar:
        st.markdown("### ❤️ 08-舆情监测控制")
        dim_p8 = st.radio("分析维度", ["📊 整体分布", "🔥 负面热点", "💡 价值锚点", "📍 空间落点"], key="p8_dim")
        
        st.markdown("---")
        st.markdown("#### 🌐 平台数据源")
        src_p8 = st.radio("数据源筛选", ["全部平台", "新浪微博", "小红书", "抖音"], key="p8_src")
        
        st.markdown("---")
        st.markdown("#### 🏷️ 语义切片过滤")
        kw_p8 = st.text_area("关键词过滤 (建议回车分隔):", value="皇宫\n拥堵\n破旧", key="p8_kw")
        
        st.markdown("---")
        st.markdown("#### 🎨 热力图参数")
        heat_rad_p8 = st.slider("热力辐射半径", 10, 100, 50, key="p8_rad")
        heat_op_p8 = st.slider("热力透明度", 0.1, 1.0, 0.7, key="p8_op")

    # --- 100% 还原 Page 8 主内容 ---
    try:
        df_nlp = pd.read_csv("data/CV_NLP_RawData.csv", encoding='utf-8-sig')
    except:
        df_nlp = pd.read_csv("data/CV_NLP_RawData.csv", encoding='gbk')
    
    if not df_nlp.empty:
        # 🧪 100% 激活平台过滤与全量内容展示
        if src_p8 != "全部平台":
            # 采用模糊匹配规避编码差异 (如 "新浪微博" 匹配 "微博")
            filter_key = src_p8.replace("新浪", "")
            df_nlp = df_nlp[df_nlp['Source'].str.contains(filter_key, na=False, case=False)]
            
        st.markdown(f"#### 📊 分析维度: {dim_p8} | 来源: {src_p8} (当前可见: {len(df_nlp)} 条数据)")
        st.dataframe(df_nlp[["Text", "Keyword", "Source"]], use_container_width=True) # 移除 head()
        
        if 'Score' not in df_nlp.columns:
            from core_engine import classify_sentiment
            valid_texts = df_nlp['Text'].dropna().astype(str).tolist()
            _, scores = classify_sentiment(valid_texts)
            df_nlp['Score'] = scores[:len(df_nlp)]
        st.plotly_chart(px.histogram(df_nlp, x="Score", title="情感分布直方图 (基于当前筛选数据)", color_discrete_sequence=['#fb7185']))
