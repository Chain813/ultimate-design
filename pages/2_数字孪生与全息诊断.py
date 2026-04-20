import streamlit as st
import pandas as pd
import pydeck as pdk
import os
import numpy as np
import math
import plotly.express as px
from src.ui.ui_components import render_top_nav
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils.geo_transform import bd09_to_wgs84
from src.engines.core_engine import get_traffic_data

# ==========================================
# 💎 页面配置
# ==========================================
st.set_page_config(page_title="数字孪生与全息诊断 | 02 实验室", layout="wide", initial_sidebar_state="expanded")
render_top_nav()

import json
import streamlit.components.v1 as components

@st.cache_data
def load_base_map_data():
    def load_json(fp):
        with open(fp, 'r', encoding='utf-8') as f: return f.read()
    
    # [性能更新] 针对建筑巨量轮廓数据采取前端分流加载，不在此进行字符串序列化
    b_data = "'/app/static/buildings.geojson'" if os.path.exists("static/buildings.geojson") else "null"
    bound_data = load_json("data/shp/Boundary_Scope.geojson") if os.path.exists("data/shp/Boundary_Scope.geojson") else "null"
    plots_data = load_json("data/shp/Key_Plots_District.json") if os.path.exists("data/shp/Key_Plots_District.json") else "null"
    return b_data, bound_data, plots_data

def render_advanced_deckgl(is_3d=True, view_pitch=45, show_build=True, show_poi=False, show_traffic=False, show_lighting=True, sun_time=10, hex_payload="null", col_payload="null", heat_payload="null"):
    b_data, bound_data, plots_data = load_base_map_data()
    if not show_build: b_data = "null"
    
    # 动态支持由于交互开关触发的数据表加载
    poi_data_json = "null"
    if show_poi:
        try:
            df_poi = pd.read_csv("data/Changchun_POI_Real.csv", encoding='utf-8-sig').fillna("")
            poi_data_json = json.dumps(df_poi[['Lng', 'Lat', 'Name']].to_dict(orient="records"))
        except: pass
        
    traffic_data_json = "null"
    if show_traffic:
        try:
            df_tr = pd.read_csv("data/Changchun_Traffic_Real.csv", encoding='utf-8-sig').fillna("")
            traffic_data_json = json.dumps(df_tr[['Lng', 'Lat', 'Name']].to_dict(orient="records"))
        except: pass

    with open("assets/map3d_standalone.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    html = html.replace("/*__BUILDING_DATA__*/null/*__END_BUILDING__*/", b_data)
    html = html.replace("/*__BOUNDARY_DATA__*/null/*__END_BOUNDARY__*/", bound_data)
    html = html.replace("/*__PLOTS_DATA__*/null/*__END_PLOTS__*/", plots_data)
    html = html.replace("/*__POI_DATA__*/null/*__END_POI__*/", poi_data_json)
    html = html.replace("/*__TRAFFIC_DATA__*/null/*__END_TRAFFIC__*/", traffic_data_json)
    html = html.replace("/*__IS_3D__*/true/*__END_IS_3D__*/", "true" if is_3d else "false")
    # 注入光照显示与时间标志
    html = html.replace("/*__SHOW_LIGHTING__*/true/*__END_LIGHTING__*/", "true" if show_lighting else "false")
    html = html.replace("/*__SUN_TIME__*/10/*__END_SUN_TIME__*/", str(sun_time))
    
    # 注入高级分析图层荷载
    html = html.replace("/*__HEX_PAYLOAD__*/null/*__END_HEX_PAY__*/", hex_payload)
    html = html.replace("/*__COL_PAYLOAD__*/null/*__END_COL_PAY__*/", col_payload)
    html = html.replace("/*__HEAT_PAYLOAD__*/null/*__END_HEAT_PAY__*/", heat_payload)
    
    # 修正相机视角
    html = html.replace("pitch: is_3d ? 45 : 0", f"pitch: {view_pitch}")
    
    st.markdown("""<style>
        iframe[title="st.iframe"] { border-radius: 12px !important; overflow: hidden !important; border: 1px solid rgba(99, 102, 241, 0.4); box-shadow: 0 10px 40px rgba(0,0,0,0.5); }
    </style>""", unsafe_allow_html=True)
    components.html(html, height=720, scrolling=False)

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
    # 📐 核心算法支撑：MPI 计算公式 (融合演示面板)
    st.markdown("""
    <style>
    .mpi-card-p2 {
        background: rgba(99, 102, 241, 0.05);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 25px;
    }
    .mpi-label-p2 {
        color: #a5b4fc;
        font-size: 0.85rem;
        font-weight: 700;
        margin-bottom: 12px;
        display: block;
    }
    .mpi-desc-p2 {
        color: #94a3b8;
        font-size: 0.75rem;
        margin-top: 12px;
        border-top: 1px solid rgba(148, 163, 184, 0.1);
        padding-top: 10px;
    }
    </style>
    <div class="mpi-card-p2">
        <span class="mpi-label-p2">🧪 多维更新潜力指数 (MPI) 测度深度模型</span>
    """, unsafe_allow_html=True)
    
    st.latex(r"\color{#a5b4fc} MPI_i = \frac{w_{space} \cdot S_i + w_{social} \cdot D_i + w_{env} \cdot (1 - E_i)}{w_{space} + w_{social} + w_{env}} \times 100")
    
    st.markdown("""
        <div class="mpi-desc-p2">
            <b>变量定义:</b> $S_i$ 空间潜力 | $D_i$ 社会需求 | $E_i$ 环境现状 | $w$ 专家权重
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
        show_light_p3 = st.checkbox("☀️ 开启仿真光照", value=True, key="p3_light")
        sun_time_p3 = st.slider("🕐 日照推演 (0-23)", 0, 23, 10, key="p3_sun_time")
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

        col_payload = "null"
        if l_mode_p3 in ("🗼 3D柱体", "🌌 双模融合"):
            col_payload = json.dumps({
                "data": df_3d[['Lng', 'Lat', cur_m, 'Dynamic_Color', 'ID']].to_dict(orient='records'),
                "metric": cur_m,
                "elevationScale": elev_p3,
                "radius": rad_p3
            })
            
        heat_payload = "null"
        if l_mode_p3 in ("🔥 2D热力", "🌌 双模融合"):
            heat_payload = json.dumps({
                "data": df_3d[['Lng', 'Lat', cur_m]].to_dict(orient='records'),
                "metric": cur_m,
                "radius": rad_p3
            })

        pitch_3d = 45 if v_mode_p3 == "🦅 3D鸟瞰" else (60 if "漫游" in v_mode_p3 else 0)
        render_advanced_deckgl(
            is_3d=(v_mode_p3 != "🗺️ 2D平面"),
            view_pitch=pitch_3d,
            show_build=True, 
            show_poi=False, 
            show_traffic=False,
            show_lighting=show_light_p3,
            sun_time=sun_time_p3,
            col_payload=col_payload,
            heat_payload=heat_payload
        )

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
        show_build_p4 = st.checkbox("🏢 3D 建筑仿真模型", value=True, key="p4_build")
        show_light_p4 = st.checkbox("☀️ 开启仿真光照", value=True, key="p4_light")
        sun_time_p4 = st.slider("🕐 日照推演 (0-23)", 0, 23, 10, key="p4_sun_time")
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
        hex_payload = "null"
        if show_hex_p4:
            hex_payload = json.dumps({
                "data": df_poi[['Lng', 'Lat']].to_dict(orient='records'),
                "radius": h_rad_p4,
                "elevationScale": h_elev_p4
            })
            
        pitch_p4 = 45 if "鸟瞰" in v_mode_p4 else (60 if "漫游" in v_mode_p4 else 0)
        render_advanced_deckgl(
            is_3d=(v_mode_p4 != "🗺️ 上帝视角"),
            view_pitch=pitch_p4,
            show_build=show_build_p4, 
            show_poi=show_poi_p4, 
            show_traffic=show_traffic_p4,
            show_lighting=show_light_p4,
            sun_time=sun_time_p4,
            hex_payload=hex_payload
        )

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
        
        fig = px.histogram(df_nlp, x="Score", title="社会情感分布态势 (情感值范围 -1 至 1)", color_discrete_sequence=['#818cf8'])
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            bargap=0.1,
            margin=dict(l=40, r=40, t=60, b=40),
            xaxis=dict(showgrid=True, gridcolor='rgba(99, 102, 241, 0.1)', title="情感极值 (Score)"),
            yaxis=dict(showgrid=True, gridcolor='rgba(99, 102, 241, 0.1)', title="频次数 (Count)"),
            font=dict(color="#94a3b8")
        )
        fig.update_traces(marker_line_width=0, opacity=0.85, marker=dict(color='#818cf8'))
        st.plotly_chart(fig, use_container_width=True)

