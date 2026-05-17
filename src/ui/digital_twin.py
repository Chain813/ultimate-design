import json
import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from src.config import get_static_url
from src.engines.spatial_engine import get_hud_statistics, get_skyline_features, get_merged_poi_data

@st.cache_data(ttl=3600)
def load_map_data(file_path):
    """缓存 GeoJSON 文件读取，避免重复磁盘 IO。"""
    path = Path(file_path)
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

@st.cache_data(ttl=3600)
def _load_map_html_template():
    """缓存 HTML 模板读取，避免每次交互都重新读磁盘。"""
    template_path = Path("assets/map3d_standalone.html")
    if not template_path.exists():
        return "<h3>Map template not found</h3>"
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@st.cache_data(ttl=3600)
def _load_traffic_json():
    """缓存交通数据的 JSON 序列化结果。"""
    try:
        # 尝试读取交通数据
        path = Path("data/csv/Changchun_Traffic_Real.csv")
        if path.exists():
            df_tr = pd.read_csv(path, encoding='utf-8-sig').fillna("")
            return json.dumps(df_tr[['Lng', 'Lat', 'Name']].to_dict(orient="records"))
    except Exception:
        pass
    return "null"

@st.cache_data(ttl=3600)
def _load_poi_json():
    """缓存 POI 数据的 JSON 序列化结果。"""
    try:
        df_poi = get_merged_poi_data().fillna("")
        if not df_poi.empty:
            return json.dumps(df_poi[['Lng', 'Lat', 'Name']].to_dict(orient="records"))
    except Exception:
        pass
    return "null"

def render_skyline_hud():
    """在地图下方渲染横向天际线指标面板"""
    skyline_stats = get_skyline_features()
    st.markdown(f"""
    <div class="skyline-panel">
        <div class="row">
            <div class="metric">
                <div class="metric-label" style="color: #818cf8;">🏙️ 区域天际线地标高度</div>
                <div class="metric-value">{skyline_stats['max_height']}<span class="metric-unit">m</span></div>
            </div>
            <div class="metric">
                <div class="metric-label" style="color: #10b981;">🏢 平均建筑高度</div>
                <div class="metric-value">{skyline_stats['avg_height']}<span class="metric-unit">m</span></div>
            </div>
            <div class="metric">
                <div class="metric-label" style="color: #f59e0b;">📈 高层建筑占比</div>
                <div class="metric-value">{skyline_stats['high_rise_ratio']}<span class="metric-unit">%</span></div>
            </div>
            <div class="metric" style="border-right: none;">
                <div class="metric-label" style="color: #ec4899;">🏗️ 测区建筑总数</div>
                <div class="metric-value">{skyline_stats['building_count']}<span class="metric-unit">栋</span></div>
            </div>
        </div>
        <div class="footnote">
            * 注：天际线高度数据基于建筑基底 Floor 字段按标准层高 3.5m 换算所得
        </div>
    </div>
    """, unsafe_allow_html=True)

@st.fragment
def render_digital_twin_map(height=650, key_suffix=""):
    """使用 @st.fragment 封装地图，图层切换只刷新本块。"""
    view_mode = st.radio(
        "🗺️ 视图模式",
        ["🦅 3D 仿真视角", "🗺️ 2D 空间肌理"],
        index=0, horizontal=True, key=f"map_view_mode_{key_suffix}"
    )
    is_3d_mode = "3D" in view_mode

    layer_cols = st.columns(8)
    with layer_cols[0]:
        show_boundary = st.checkbox("🔲 规划红线", value=True, key=f"map_boundary_{key_suffix}")
    with layer_cols[1]:
        show_plots = st.checkbox("✴️ 重点更新单元", value=True, key=f"map_plots_{key_suffix}")
    with layer_cols[2]:
        show_buildings = st.checkbox("🏢 建筑轮廓", value=True, key=f"map_buildings_{key_suffix}")
    with layer_cols[3]:
        show_poi = st.checkbox("📍 POI 设施分布", value=False, key=f"map_poi_{key_suffix}")
    with layer_cols[4]:
        show_traffic = st.checkbox("🚦 交通拥堵热点", value=False, key=f"map_traffic_{key_suffix}")
    with layer_cols[5]:
        show_landuse = st.checkbox("🧬 规划用地底色", value=False, key=f"map_landuse_{key_suffix}")
    with layer_cols[6]:
        show_rail = st.checkbox("🚆 铁路轨道", value=False, key=f"map_rail_{key_suffix}")
    with layer_cols[7]:
        show_road = st.checkbox("🛣️ 道路网", value=False, key=f"map_road_{key_suffix}")

    show_lighting = st.checkbox("☀️ 开启仿真光照", value=is_3d_mode, key=f"map_lighting_{key_suffix}")
    sun_time = st.slider("🕐 日照推演 (00:00 - 23:00)", 0, 23, 10, key=f"map_sun_time_{key_suffix}")

    # 1. 准备序列化数据
    b_data_json = f"'{get_static_url('buildings.geojson')}'" if show_buildings else "null"
    bound_data_json = json.dumps(load_map_data("data/gis/Boundary_Scope.geojson")) if show_boundary else "null"
    plots_data_json = json.dumps(load_map_data("data/gis/Key_Plots_District.json")) if show_plots else "null"
    poi_data_json = _load_poi_json() if show_poi else "null"
    traffic_data_json = _load_traffic_json() if show_traffic else "null"
    landuse_data_json = f"'{get_static_url('landuse.geojson')}'" if show_landuse else "null"
    rail_data_json = f"'{get_static_url('rail_clipped.geojson')}'" if show_rail else "null"
    road_data_json = f"'{get_static_url('road_clipped.geojson')}'" if show_road else "null"

    # 2. 填充模板
    try:
        html_template = _load_map_html_template()
        html_template = html_template.replace("/*__BUILDING_DATA__*/null/*__END_BUILDING__*/", b_data_json)
        html_template = html_template.replace("/*__BOUNDARY_DATA__*/null/*__END_BOUNDARY__*/", bound_data_json)
        html_template = html_template.replace("/*__PLOTS_DATA__*/null/*__END_PLOTS__*/", plots_data_json)
        html_template = html_template.replace("/*__POI_DATA__*/null/*__END_POI__*/", poi_data_json)
        html_template = html_template.replace("/*__TRAFFIC_DATA__*/null/*__END_TRAFFIC__*/", traffic_data_json)
        html_template = html_template.replace("/*__LANDUSE_DATA__*/null/*__END_LANDUSE__*/", landuse_data_json)
        html_template = html_template.replace("/*__RAIL_DATA__*/null/*__END_RAIL__*/", rail_data_json)
        html_template = html_template.replace("/*__ROAD_DATA__*/null/*__END_ROAD__*/", road_data_json)
        html_template = html_template.replace("/*__IS_3D__*/true/*__END_IS_3D__*/", "true" if is_3d_mode else "false")
        html_template = html_template.replace("/*__SHOW_LIGHTING__*/true/*__END_LIGHTING__*/", "true" if show_lighting else "false")
        html_template = html_template.replace("/*__SUN_TIME__*/10/*__END_SUN_TIME__*/", str(sun_time))
        
        st.markdown("""<style>
            iframe[title="st.iframe"] { border-radius: 18px !important; overflow: hidden !important; border: 1px solid rgba(99, 102, 241, 0.4); box-shadow: 0 10px 40px rgba(0,0,0,0.5); }
        </style>""", unsafe_allow_html=True)
        components.html(html_template, height=height, scrolling=False)
    except Exception as e:
        st.error(f"地图组件核心加载失败: {str(e)}")
