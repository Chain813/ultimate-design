import streamlit as st
import pandas as pd
import pydeck as pdk
import os
import numpy as np
import math

st.set_page_config(page_title="交通与人口 | 微更新平台", layout="wide", initial_sidebar_state="expanded")

import streamlit as st
from ui_components import render_top_nav # 引入外援


render_top_nav() # 一行代码搞定几十行的 CSS 和导航栏！

# 下面接着写你这一页的核心业务逻辑...
st.markdown("<h2>历史街区交通枢纽与商业活力耦合分析</h2>", unsafe_allow_html=True)

# ==========================================
# 🗺️ 核心算法：百度坐标 (BD-09) 转 WGS-84
# ==========================================
def bd09_to_wgs84(bd_lon, bd_lat):
    x_pi, pi = 3.14159265358979324 * 3000.0 / 180.0, 3.1415926535897932384626
    a, ee = 6378245.0, 0.00669342162296594323
    x, y = bd_lon - 0.0065, bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * x_pi)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * x_pi)
    gcj_lon, gcj_lat = z * math.cos(theta), z * math.sin(theta)

    def transformlat(lng, lat):
        ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat + 0.2 * math.sqrt(abs(lng))
        ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 * math.sin(2.0 * lng * pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(lat * pi) + 40.0 * math.sin(lat / 3.0 * pi)) * 2.0 / 3.0
        ret += (160.0 * math.sin(lat / 12.0 * pi) + 320 * math.sin(lat * pi / 30.0)) * 2.0 / 3.0
        return ret

    def transformlng(lng, lat):
        ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng * lat + 0.1 * math.sqrt(abs(lng))
        ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 * math.sin(2.0 * lng * pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(lng * pi) + 40.0 * math.sin(lng / 3.0 * pi)) * 2.0 / 3.0
        ret += (150.0 * math.sin(lng / 12.0 * pi) + 300.0 * math.sin(lng / 30.0 * pi)) * 2.0 / 3.0
        return ret

    dlat, dlon = transformlat(gcj_lon - 105.0, gcj_lat - 35.0), transformlng(gcj_lon - 105.0, gcj_lat - 35.0)
    radlat = gcj_lat / 180.0 * pi
    magic = 1 - ee * math.sin(radlat) * math.sin(radlat)
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlon = (dlon * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    return gcj_lon - dlon, gcj_lat - dlat

@st.cache_data
def load_data(filename):
    if not os.path.exists(filename): filename = "../" + filename
    return pd.read_csv(filename) if os.path.exists(filename) else None

@st.cache_data
def load_base_points():
    f = "data/Changchun_Precise_Points.xlsx"
    if not os.path.exists(f): f = "../" + f
    return pd.read_excel(f) if os.path.exists(f) else None

df_poi = load_data("data/Changchun_POI_Real.csv")
df_traffic = load_data("data/Changchun_Traffic_Real.csv")
df_base = load_base_points()

if df_poi is not None and 'Type' in df_poi.columns:
    df_poi['Category'] = df_poi['Type']
    df_poi['Name'] = df_poi.get('Name', '商业网点')

if df_traffic is not None:
    def classify_and_color(row):
        text = str(row.get('Name', '')) + str(row.get('Type', ''))
        if '地铁' in text or '轻轨' in text:
            return pd.Series(['轻轨站或地铁站', [231, 76, 60, 220]])
        elif '铁路' in text or '站' in text:
            return pd.Series(['铁路及铁路站', [142, 68, 173, 220]])
        elif '公交' in text or '客运' in text:
            return pd.Series(['公交站', [46, 204, 113, 220]])
        elif '停车' in text:
            return pd.Series(['停车场', [52, 152, 219, 220]])
        else:
            return pd.Series(['其他交通设施', [149, 165, 166, 200]])

    df_traffic[['Category', 'Color']] = df_traffic.apply(classify_and_color, axis=1)

@st.cache_data
def generate_dynamic_traffic():
    cong_bd_lngs = [125.360106, 125.355170, 125.346943]
    cong_bd_lats = [43.908314, 43.915339, 43.912892]
    cong_wgs = [bd09_to_wgs84(lon, lat) for lon, lat in zip(cong_bd_lngs, cong_bd_lats)]

    df_cong = pd.DataFrame({
        "Name": ["早市核心拥堵段", "铁道口车流瓶颈", "老旧小区出入口"],
        "Lng": [p[0] for p in cong_wgs],
        "Lat": [p[1] for p in cong_wgs],
        "Congestion_Base": [85, 90, 65],
        "Category": ["动态拥堵监控"] * 3
    })

    dead_bd_lngs = [125.353000, 125.348000, 125.358000]
    dead_bd_lats = [43.914000, 43.907000, 43.910000]
    dead_wgs = [bd09_to_wgs84(lon, lat) for lon, lat in zip(dead_bd_lngs, dead_bd_lats)]

    df_dead = pd.DataFrame({
        "Name": ["铁路割裂断头路", "厂房围墙阻断", "违建侵占盲道"],
        "Lng": [p[0] for p in dead_wgs],
        "Lat": [p[1] for p in dead_wgs],
        "Category": ["路网贯通靶点"] * 3
    })

    pop_df = pd.DataFrame({
        "时间": range(24),
        "商业/早市活力": [10, 5, 2, 5, 20, 80, 150, 200, 180, 120, 90, 80, 70, 60, 50, 40, 30, 20, 15, 10, 8, 5, 5, 10],
        "居住区晚高峰": [50, 50, 40, 40, 60, 100, 80, 50, 40, 40, 40, 45, 50, 45, 40, 50, 80, 150, 180, 200, 150, 100, 80, 60]
    }).set_index("时间")
    return df_cong, df_dead, pop_df

df_cong, df_dead, df_pop = generate_dynamic_traffic()

with st.sidebar:
    st.markdown("#### ⏳ 24H 动态潮汐推演")
    current_hour = st.slider("滑动时间轴查看交通变化", 0, 23, 8, 1, format="%d:00")
    st.markdown("---")
    st.markdown("#### 👁️ 视角控制")
    v_m = st.radio("模式", ["🦅 鸟瞰视角", "🗺️ 上帝视角", "🚶 漫游视角"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("#### 📊 商业活力图层")
    show_hex = st.checkbox("🔮 开启宏观蜂窝柱 (密度聚合)", value=True)
    if show_hex:
        h_r = st.slider("蜂窝网格半径 (米)", 20, 150, 50, 10)
        e_s = st.slider("活力高度拉伸倍数", 0.5, 10.0, 3.0, 0.5)

    show_poi_raw = st.checkbox("🔍 透视微观商铺点(显示名称)", value=False)
    st.markdown("---")
    st.markdown("#### 🚥 路网与交通层")
    show_traffic = st.checkbox("🚌 交通枢纽脉冲点", value=True)
    show_cong = st.checkbox("🔥 路口拥堵热力图", value=True)
    show_dead = st.checkbox("🚧 断头路与修复靶点", value=True)

c_lng, c_lat = (df_base['Lng'].mean(), df_base['Lat'].mean()) if df_base is not None else (125.315, 43.902)
params = {"🦅 鸟瞰视角": (50, 15, 14.5), "🗺️ 上帝视角": (0, 0, 14), "🚶 漫游视角": (60, 45, 15.5)}
v_pitch, v_bearing, v_zoom = params[v_m]
layers_to_render = []

if df_poi is not None and show_hex:
    layers_to_render.append(pdk.Layer(
        "HexagonLayer", data=df_poi, get_position=["Lng", "Lat"], radius=h_r,
        elevation_scale=e_s, elevation_range=[0, 300], extruded=True, coverage=0.88,
        wireframe=True, opacity=0.75, pickable=True,
        color_range=[[241, 238, 246, 180], [208, 209, 230, 180], [166, 189, 219, 180], [116, 169, 207, 180], [43, 140, 190, 180], [4, 90, 141, 180]]
    ))

if df_poi is not None and show_poi_raw:
    layers_to_render.append(pdk.Layer(
        "ScatterplotLayer", data=df_poi, get_position=["Lng", "Lat"], get_radius=12,
        get_fill_color=[255, 20, 147, 240], get_line_color=[255, 255, 255, 255], lineWidthMinPixels=2, pickable=True, auto_highlight=True
    ))

if df_traffic is not None and show_traffic:
    layers_to_render.append(pdk.Layer(
        "ScatterplotLayer", data=df_traffic, get_position=["Lng", "Lat"], get_radius=15,
        get_fill_color="Color", get_line_color=[255, 255, 255, 200], lineWidthMinPixels=1, pickable=True, auto_highlight=True
    ))

if show_cong:
    time_multiplier = 1.5 if current_hour in [7, 8, 9, 17, 18, 19] else (0.3 if current_hour < 6 else 1.0)
    df_cong["Dynamic_Weight"] = df_cong["Congestion_Base"] * time_multiplier
    layers_to_render.append(
        pdk.Layer("HeatmapLayer", data=df_cong, opacity=0.8, get_position=["Lng", "Lat"], get_weight="Dynamic_Weight", radiusPixels=70)
    )

if show_dead:
    layers_to_render.append(pdk.Layer(
        "ScatterplotLayer", data=df_dead, get_position=["Lng", "Lat"], get_radius=30,
        get_fill_color=[241, 196, 15, 255], get_line_color=[255, 255, 255, 200], lineWidthMinPixels=3, stroked=True, pickable=True
    ))

radar_tooltip = {
    "html": "<b>{Name}</b><br/>分类: <span style='color: #e74c3c;'>{Category}</span><br/>(部分图层聚合值为: {elevationValue})",
    "style": {"backgroundColor": "rgba(255, 255, 255, 0.95)", "color": "#2c3e50", "borderRadius": "8px"}
}

map_col, data_col = st.columns([4, 1.2])

with map_col:
    r = pdk.Deck(layers=layers_to_render, initial_view_state=pdk.ViewState(longitude=c_lng, latitude=c_lat, zoom=v_zoom, pitch=v_pitch, bearing=v_bearing), map_style="light", tooltip=radar_tooltip)
    st.pydeck_chart(r, use_container_width=True)

with data_col:
    st.markdown("### 📊 基础设施洞察")
    if df_traffic is not None and df_poi is not None:
        counts = df_traffic['Category'].value_counts()
        c1, c2 = st.columns(2)
        c1.metric("🛍️ 商业 POI", f"{len(df_poi)}")
        c2.metric("🚌 公交节点", f"{counts.get('公交站', 0)}")

    st.markdown("---")
    st.markdown(f"#### 📈 24H 人口潮汐 ({current_hour}:00)")
    st.line_chart(df_pop, use_container_width=True, height=200)

    st.markdown("#### 🧠 诊断与对策")
    if 7 <= current_hour <= 9:
        st.error("🚨 早高峰预警：早市/枢纽区域拥堵。建议优先贯通【铁路割裂断头路】，分散过境车流。")
    elif 17 <= current_hour <= 20:
        st.warning("⚠️ 晚高峰预警：居住区承载受限。建议结合【废弃厂房/边角地】置换为立体停车设施。")
    else:
        st.success("✅ 流量平稳：建议在此基础流态下，重点推进微观空间路权恢复及慢行系统优化。")