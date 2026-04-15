import streamlit as st
import pandas as pd
import pydeck as pdk
import os
import numpy as np
import math

# 🌟 强制展开侧边栏
st.set_page_config(page_title="数字孪生沙盘 | 微更新平台", layout="wide", initial_sidebar_state="expanded")

import streamlit as st
from ui_components import render_top_nav # 引入外援


render_top_nav() # 一行代码搞定几十行的 CSS 和导航栏！

# 下面接着写你这一页的核心业务逻辑...
st.markdown("<h2>150 公顷核心区：多维空间语义测度与微更新靶点落位</h2>", unsafe_allow_html=True)


# ==========================================
# 1. 挂载四维数据底座
# ==========================================
@st.cache_data
def load_data():
    base_path = "data/Changchun_Precise_Points.xlsx"
    gvi_path = "data/GVI_Results_Analysis.csv"
    if not os.path.exists(base_path): base_path = "../" + base_path
    if not os.path.exists(gvi_path): gvi_path = "../" + gvi_path

    try:
        df_base = pd.read_excel(base_path)
        df_gvi = pd.read_csv(gvi_path)

        if 'Folder' in df_gvi.columns:
            df_gvi['ID'] = df_gvi['Folder'].str.replace('Point_', '').astype(int)
            df_gvi = df_gvi.groupby('ID').mean().reset_index()

        df = pd.merge(df_base, df_gvi, on='ID', how='inner')
    except Exception as e:
        lngs = np.random.normal(loc=125.3517, scale=0.005, size=300)
        lats = np.random.normal(loc=43.9116, scale=0.005, size=300)
        df = pd.DataFrame({
            "ID": range(1, 301), "Lng": lngs, "Lat": lats,
            "GVI": np.random.randint(10, 50, size=300),
            "SVF": np.random.randint(10, 60, size=300),
            "Enclosure": np.random.randint(30, 80, size=300),
            "Clutter": np.random.randint(0, 20, size=300)
        })

    for col in ["GVI", "SVF", "Enclosure", "Clutter"]:
        if col not in df.columns: df[col] = 0

    df["Plot_ID"] = "环境感知节点 " + df["ID"].astype(str)
    df["Type"] = "街景视觉评估 (DeepLabV3+)"
    df["Strategy"] = "多维空间品质测度"
    df = df.dropna(subset=['Lng', 'Lat'])
    return df


df_merged = load_data()

# ==========================================
# 2. 侧边栏：多维战术控制台
# ==========================================
with st.sidebar:
    st.markdown("#### 🎯 核心空间指标切换")
    metric_choice = st.selectbox("选择要渲染的城市维度：", [
        "🌿 绿视率 (GVI) - 生态与自然",
        "🌤️ 天空开阔度 (SVF) - 采光与压抑感",
        "🧱 空间围合度 (Enclosure) - 街道边界感",
        "⚠️ 视觉杂乱度 (Clutter) - 设施混乱度"
    ])

    metric_map = {
        "🌿 绿视率 (GVI) - 生态与自然": "GVI",
        "🌤️ 天空开阔度 (SVF) - 采光与压抑感": "SVF",
        "🧱 空间围合度 (Enclosure) - 街道边界感": "Enclosure",
        "⚠️ 视觉杂乱度 (Clutter) - 设施混乱度": "Clutter"
    }
    current_metric = metric_map[metric_choice]

    with st.expander("📖 查看四维空间指标学术释义"):
        st.markdown("""
        - **🌿 绿视率 (GVI):** 人眼视野中植物像素占比。
        - **🌤️ 天空开阔度 (SVF):** 天空无遮挡像素占比。
        - **🧱 空间围合度 (Enclosure):** 建筑+围墙+植物占比总和。
        - **⚠️ 视觉杂乱度 (Clutter):** 杆线/围栏/交通牌等冗余设施占比。
        """)

    st.markdown("---")
    st.markdown("#### 👁️ 视角控制")
    v_m = st.radio("模式", ["🦅 3D鸟瞰视角", "🗺️ 2D平面视角", "🚶 低空漫游视角"], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("#### ⚙️ 柱体与热力图精密调参")
    layer_mode = st.radio("选择可视化引擎：", ["🗼 3D 物理柱体", "🔥 2D 辐射热力图", "🌌 双模态融合显示"])

    if "柱体" in layer_mode or "融合" in layer_mode:
        col_elev = st.slider("🗼 柱体高度拉伸倍数", 1, 50, 20, 1)
        col_radius = st.slider("📏 柱体粗细 (覆盖半径)", 5, 80, 25, 5)
    if "热力图" in layer_mode or "融合" in layer_mode:
        heat_radius = st.slider("🔥 热力辐射半径", 10, 100, 40, 5)

# ==========================================
# 🚀 核心升级：数据自适应冷暖色渐变引擎
# ==========================================
min_v = df_merged[current_metric].min() if not df_merged.empty else 0
max_v = df_merged[current_metric].max() if not df_merged.empty else 100
if min_v == max_v: max_v = min_v + 1

# ==========================================
# 🚀 核心升级：数据自适应冷暖色渐变引擎 (🚨 反转冷暖映射)
# ==========================================
min_v = df_merged[current_metric].min() if not df_merged.empty else 0
max_v = df_merged[current_metric].max() if not df_merged.empty else 100
if min_v == max_v: max_v = min_v + 1


def get_gradient_color(val):
    # 将数值标准化到 0 ~ 1 之间
    n = (val - min_v) / (max_v - min_v)

    # 🚨 颜色通道已翻转！
    # 数值低(n趋近0) -> r趋近255 (红色)
    # 数值高(n趋近1) -> b趋近255 (蓝色)
    r = int(255 * (1 - n))
    b = int(255 * n)
    g = int(200 * math.sin(n * math.pi))  # 保持中间过渡色的亮度

    return [r, g, b, 255]


df_merged["Dynamic_Color"] = df_merged[current_metric].apply(get_gradient_color)

# ==========================================
# 3. 百度坐标解密与 5大干预靶点
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


bd_lngs = [125.346912, 125.355170, 125.346943, 125.360106, 125.349551]
bd_lats = [43.915586, 43.915339, 43.912892, 43.908314, 43.906248]
wgs_lngs, wgs_lats = zip(*[bd09_to_wgs84(lon, lat) for lon, lat in zip(bd_lngs, bd_lats)])

target_plots = pd.DataFrame({
    "Plot_ID": ["📌 地块 1", "📌 地块 2", "📌 地块 3", "📌 地块 4", "📌 地块 5"],
    "Lng": wgs_lngs, "Lat": wgs_lats,
    "Type": ["非正式商业/铁皮房蔓延区", "铁路割裂/低密居住环境", "老旧居住区/高密度混杂", "早市/低效棚场", "中石油闲置/边角废弃地"],
    "Strategy": ["功能置换与停车立体化", "跨铁路线缝合与品质提升", "社区微更新与立面改造", "市井文化保留与空间梳理", "街角口袋公园与创客置入"],
    "GVI": ["核心靶点"] * 5, "SVF": ["核心靶点"] * 5, "Enclosure": ["核心靶点"] * 5, "Clutter": ["核心靶点"] * 5
})

# ==========================================
# 4. 构建动态 PyDeck 图层 (🗼 3D 玻璃晶体阵列版)
# ==========================================
c_lng, c_lat = sum(wgs_lngs) / len(wgs_lngs), sum(wgs_lats) / len(wgs_lats)
params = {"🦅 3D鸟瞰视角": (50, 15, 14.8), "🗺️ 2D平面视角": (0, 0, 14.2), "🚶 低空漫游视角": (65, 45, 15.5)}
v_pitch, v_bearing, v_zoom = params[v_m]
layers_to_render = []

if "柱体" in layer_mode or "融合" in layer_mode:
    # 🚨 王者归来：带高度的 3D 半透明六边形晶体柱！
    layer_col = pdk.Layer(
        "ColumnLayer",
        data=df_merged,
        get_position=["Lng", "Lat"],
        get_elevation=current_metric,   # ✅ 恢复高度数据绑定，柱子重新拔地而起！
        elevation_scale=col_elev,       # ✅ 恢复侧边栏高度拉伸滑块控制
        radius=col_radius,              # ✅ 恢复正常的网格粗细
        disk_resolution=6,              # 🔮 保持极具科技感的六边形形态
        extruded=True,                  # 🗼 核心：开启 3D 立体拉伸！
        get_fill_color="Dynamic_Color", # 🎨 保持“低红高蓝”的自适应冷暖色带
        opacity=0.75,                   # 🪟 保持 25% 的高级玻璃透明度，不遮挡底图
        pickable=True,
        auto_highlight=True
    )
    layers_to_render.append(layer_col)

if "热力图" in layer_mode or "融合" in layer_mode:
    layer_heat = pdk.Layer(
        "HeatmapLayer",
        data=df_merged,
        opacity=0.8,
        get_position=["Lng", "Lat"],
        get_weight=current_metric,
        radiusPixels=heat_radius
    )
    layers_to_render.append(layer_heat)

# 干预靶点与红色预警圈保持不变
layers_to_render.append(pdk.Layer("ScatterplotLayer", data=target_plots, get_position=["Lng", "Lat"], get_radius=90,
                                  get_fill_color=[231, 76, 60, 160], get_line_color=[255, 255, 255, 255],
                                  lineWidthMinPixels=3, stroked=True, pickable=True))

layers_to_render.append(
    pdk.Layer("TextLayer", data=target_plots, get_position=["Lng", "Lat"], get_text="Plot_ID", get_size=20,
              get_color=[200, 40, 40, 255], get_alignment_baseline="'bottom'", get_pixel_offset=[0, -30]))


# ==========================================
# 5. 渲染巨幕与动态体检报告大屏
# ==========================================
map_col, data_col = st.columns([4, 1])

with map_col:
    tooltip_html = """
    <div style="font-family: 'Helvetica Neue', Arial, sans-serif; padding: 10px; min-width: 220px;">
        <h4 style="margin: 0 0 8px 0; color: #e74c3c;">{Plot_ID}</h4>
        <div style="font-size: 13px; color: #333; margin-bottom: 8px;">
            <b>当前显示属性：</b>{Type}<br/>
            <b>干预策略：</b><span style="color: #2980b9; font-weight: bold;">{Strategy}</span>
        </div>
        <hr style="margin: 8px 0; border: 0.5px solid #ccc;"/>
        <table style="width: 100%; font-size: 12px; color: #444;">
            <tr><td>🌿 绿视率:</td><td style="text-align: right; font-weight: bold;">{GVI}%</td></tr>
            <tr><td>🌤️ 天空开阔度:</td><td style="text-align: right; font-weight: bold;">{SVF}%</td></tr>
            <tr><td>🧱 空间围合度:</td><td style="text-align: right; font-weight: bold;">{Enclosure}%</td></tr>
            <tr><td>⚠️ 视觉杂乱度:</td><td style="text-align: right; font-weight: bold; color: #e74c3c;">{Clutter}%</td></tr>
        </table>
    </div>
    """
    r = pdk.Deck(
        layers=layers_to_render,
        initial_view_state=pdk.ViewState(longitude=c_lng, latitude=c_lat, zoom=v_zoom, pitch=v_pitch,
                                         bearing=v_bearing),
        map_style="light", # ☀️ 核心：底图切换为明亮模式
        tooltip={"html": tooltip_html, "style": {"backgroundColor": "rgba(255,255,255,0.95)", "borderRadius": "8px", "color": "#333"}}
    )
    st.pydeck_chart(r, use_container_width=True)

# ---> 下方 data_col (右侧图表区) 的代码保持原样不动！

with data_col:
    st.markdown("### 📊 区域动态体检表")
    st.markdown("---")

    avg_val = df_merged[current_metric].mean() if not df_merged.empty else 0
    max_val = df_merged[current_metric].max() if not df_merged.empty else 0

    with st.container(): st.metric(f"🎯 全区平均 {current_metric}", f"{avg_val:.1f}%")
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(): st.metric(f"🔥 最高峰值区域", f"{max_val:.1f}%", f"极值点侦测")
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(): st.metric("🌐 有效采样基站", f"{len(df_merged)} 个", "持续扩容中")

    st.markdown("---")
    st.markdown("#### 📖 空间病理学释义")

    explanations = {
        "GVI": "🌿 **绿视率 (Green View Index):** 代表人眼真实视野中绿色植被的面积占比。数值越高，说明街道生态绿化水平越好，自然亲和力越强。",
        "SVF": "🌤️ **天空开阔度 (Sky View Factor):** 代表视野中天空的无遮挡占比。反映街道的开阔度与采光条件。老城区SVF过低通常意味着空间压抑或存在违建；但过高也可能导致夏季缺乏林荫遮挡。",
        "Enclosure": "🧱 **空间围合度 (Street Enclosure):** 建筑、墙体与植物在视野中的占比总和。反映空间的“边界感”与“安全感”。优秀的商业街通常具有适宜的围合度，而废弃厂区往往围合度极差，呈现空旷荒凉感。",
        "Clutter": "⚠️ **视觉杂乱度 (Visual Clutter):** 电线杆、交通牌、路灯、铁栅栏等冗余设施的占比。该数值越高，说明街道视觉品质越低，基础设施缺乏统筹规划，是典型的“城市衰败（Urban Decay）”特征。"
    }

    st.info(explanations[current_metric])