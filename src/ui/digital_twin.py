import json
import os

import pandas as pd
import streamlit as st

try:
    import streamlit.components.v1 as components
except ModuleNotFoundError:
    components = st.components.v1
from pathlib import Path

from src.config import DATA_FILES, GIS_FILES, get_map_viewport, get_static_url
from src.engines.spatial_engine import get_hud_statistics, get_merged_poi_data, get_skyline_features


@st.cache_data(ttl=3600, max_entries=20)
def load_map_data(file_path):
    """缓存 GeoJSON 文件读取，避免重复磁盘 IO。"""
    path = Path(file_path)
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

@st.cache_data(ttl=86400)
def _load_map_html_template(_mtime: float = 0.0):
    """缓存 HTML 模板读取，避免每次交互都重新读磁盘。_mtime 作为缓存键。"""
    template_path = Path("assets/map3d_standalone.html")
    if not template_path.exists():
        return "<h3>Map template not found</h3>"
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@st.cache_data(ttl=3600, max_entries=20)
def _load_traffic_json():
    """缓存交通数据的 JSON 序列化结果。"""
    try:
        # 尝试读取交通数据
        path = Path(DATA_FILES["traffic"])
        if path.exists():
            df_tr = pd.read_csv(path, encoding='utf-8-sig').fillna("")
            return json.dumps(df_tr[['Lng', 'Lat', 'Name']].to_dict(orient="records"))
    except Exception:
        pass
    return "null"

@st.cache_data(ttl=3600, max_entries=20)
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

    # ── 图层控制面板：紧凑双行 pill-checkbox 样式 ──────────────────────────
    st.markdown(f"""
    <style>
    [data-testid="stCheckbox"][id^="map_"][id$="_{key_suffix}"] > label {{
        background: rgba(0,0,0,0.03);
        border: 1px solid rgba(0,0,0,0.09);
        border-radius: 20px;
        padding: 2px 10px 2px 6px;
        font-size: 12px;
        white-space: nowrap;
        transition: background 0.15s;
    }}
    [data-testid="stCheckbox"][id^="map_"][id$="_{key_suffix}"] > label:hover {{
        background: rgba(0,112,243,0.06);
        border-color: rgba(0,112,243,0.25);
    }}
    </style>
    """, unsafe_allow_html=True)

    # 第一行：基础底图图层
    row1 = st.columns(6)
    with row1[0]:
        show_boundary = st.checkbox("🔲 规划红线", value=True, key=f"map_boundary_{key_suffix}")
    with row1[1]:
        show_plots = st.checkbox("✴️ 重点更新单元", value=True, key=f"map_plots_{key_suffix}")
    with row1[2]:
        show_buildings = st.checkbox("🏢 建筑轮廓", value=True, key=f"map_buildings_{key_suffix}")
    with row1[3]:
        show_bstyle = st.checkbox("🎨 风貌色彩", value=False, key=f"map_bstyle_{key_suffix}")
    with row1[4]:
        show_landuse = st.checkbox("🧬 规划用地底色", value=False, key=f"map_landuse_{key_suffix}")
    with row1[5]:
        show_lighting = st.checkbox("☀️ 仿真光照", value=is_3d_mode, key=f"map_lighting_{is_3d_mode}_{key_suffix}")

    # 第二行：专项分析图层
    row2 = st.columns(6)
    with row2[0]:
        show_poi = st.checkbox("📍 POI 设施分布", value=False, key=f"map_poi_{key_suffix}")
    with row2[1]:
        show_traffic = st.checkbox("🚦 交通拥堵热点", value=False, key=f"map_traffic_{key_suffix}")
    with row2[2]:
        show_rail = st.checkbox("🚆 铁路轨道", value=False, key=f"map_rail_{key_suffix}")
    with row2[3]:
        show_road = st.checkbox("🛣️ 道路网", value=False, key=f"map_road_{key_suffix}")
    with row2[4]:
        show_syntax = st.checkbox("🔗 空间句法", value=False, key=f"map_syntax_{key_suffix}")
    with row2[5]:
        show_quality = st.checkbox("📊 街景空间品质", value=False, key=f"map_quality_{key_suffix}")

    sun_time = st.slider("🕐 日照推演 (00:00 - 23:00)", 0, 23, 10, key=f"map_sun_time_{key_suffix}")

    # 空间句法指标切换
    syntax_metric = "integration_norm"
    if show_syntax:
        st.markdown("---")
        s_cols = st.columns(4)
        with s_cols[0]:
            syntax_type = st.selectbox(
                "🔗 空间句法分析指标",
                ["全局整合度 (Integration)", "全局穿行度 (Choice)"],
                index=0,
                key=f"map_syntax_type_{key_suffix}"
            )
            syntax_metric = "integration_norm" if "整合度" in syntax_type else "choice_norm"

    # 1. 准备序列化数据
    b_data_json = f"'{get_static_url('buildings.geojson')}'" if show_buildings else "null"
    shadow_data_json = f"'{get_static_url('building_shadows.geojson')}'" if (show_buildings and show_lighting) else "null"
    bound_data_json = json.dumps(load_map_data(str(GIS_FILES["boundary"]))) if show_boundary else "null"
    plots_data_json = json.dumps(load_map_data(str(GIS_FILES["plots"]))) if show_plots else "null"
    poi_data_json = _load_poi_json() if show_poi else "null"
    traffic_data_json = _load_traffic_json() if show_traffic else "null"
    landuse_data_json = f"'{get_static_url('landuse.geojson')}'" if show_landuse else "null"
    rail_data_json = f"'{get_static_url('rail_clipped.geojson')}'" if show_rail else "null"
    road_data_json = f"'{get_static_url('road_clipped.geojson')}'" if show_road else "null"
    import time as _time
    _syntax_cache_bust = int(_time.time())
    syntax_data_json = f"'{get_static_url('road_syntax.geojson')}?v={_syntax_cache_bust}'" if show_syntax else "null"

    col_payload_json = "null"
    heat_payload_json = "null"

    if show_quality:
        st.markdown("---")
        q_cols = st.columns(4)
        with q_cols[0]:
            quality_metric = st.selectbox(
                "指标选择",
                ["GVI (绿视率)", "SVF (天空开敞度)", "Enclosure (街道围合感)", "Clutter (视觉杂乱度)"],
                index=0,
                key=f"map_metric_{key_suffix}"
            )
        with q_cols[1]:
            quality_mode = st.radio(
                "展现形式",
                ["3D 柱体", "2D 热力图", "双模融合"],
                index=0,
                horizontal=True,
                key=f"map_qmode_{key_suffix}"
            )
        with q_cols[2]:
            quality_rad = st.slider("柱体/热力半径 (m)", 5, 80, 25, key=f"map_qrad_{key_suffix}")
        with q_cols[3]:
            quality_elev = st.slider("柱体拉伸倍数", 1, 150, 10, key=f"map_qelev_{key_suffix}")

        try:
            import math

            from src.engines.spatial_engine import get_spatial_data
            df_3d = get_spatial_data().copy()
            
            metric_map = {
                "GVI (绿视率)": "GVI",
                "SVF (天空开敞度)": "SVF",
                "Enclosure (街道围合感)": "Enclosure",
                "Clutter (视觉杂乱度)": "Clutter"
            }
            cur_m = metric_map[quality_metric]
            for c in ["GVI", "SVF", "Enclosure", "Clutter"]:
                if c not in df_3d.columns:
                    df_3d[c] = 0.0
            
            min_v = df_3d[cur_m].min()
            max_v = df_3d[cur_m].max()
            if min_v == max_v:
                max_v = min_v + 1.0
            
            df_3d["Dynamic_Color"] = df_3d[cur_m].apply(lambda v: [
                int(255 * (1 - (v - min_v) / (max_v - min_v))),
                int(200 * math.sin((v - min_v) / (max_v - min_v) * math.pi)),
                int(255 * ((v - min_v) / (max_v - min_v))),
                210
            ])
            
            if quality_mode in ("3D 柱体", "双模融合"):
                col_payload_json = json.dumps({
                    "data": df_3d[['Lng', 'Lat', cur_m, 'Dynamic_Color', 'ID']].to_dict(orient='records'),
                    "metric": cur_m,
                    "elevationScale": quality_elev,
                    "radius": quality_rad
                })
            
            if quality_mode in ("2D 热力图", "双模融合"):
                heat_payload_json = json.dumps({
                    "data": df_3d[['Lng', 'Lat', cur_m]].to_dict(orient='records'),
                    "metric": cur_m,
                    "radius": quality_rad
                })
        except Exception as e:
            st.error(f"加载空间品质数据失败: {e!s}")

    # 2. 填充模板
    try:
        template_path = Path("assets/map3d_standalone.html")
        _mtime = template_path.stat().st_mtime if template_path.exists() else 0.0
        html_template = _load_map_html_template(_mtime)
        map_config_json = json.dumps(get_map_viewport())
        html_template = html_template.replace('/*__MAP_CONFIG__*/{"center": [125.34064, 43.90095], "zoom": 14.4, "pitch": 73.0, "bearing": 45.0}/*__END_MAP_CONFIG__*/', map_config_json)
        html_template = html_template.replace("/*__BUILDING_DATA__*/null/*__END_BUILDING__*/", b_data_json)
        html_template = html_template.replace("/*__SHADOW_DATA__*/null/*__END_SHADOW__*/", shadow_data_json)
        html_template = html_template.replace("/*__BOUNDARY_DATA__*/null/*__END_BOUNDARY__*/", bound_data_json)
        html_template = html_template.replace("/*__PLOTS_DATA__*/null/*__END_PLOTS__*/", plots_data_json)
        html_template = html_template.replace("/*__POI_DATA__*/null/*__END_POI__*/", poi_data_json)
        html_template = html_template.replace("/*__TRAFFIC_DATA__*/null/*__END_TRAFFIC__*/", traffic_data_json)
        html_template = html_template.replace("/*__LANDUSE_DATA__*/null/*__END_LANDUSE__*/", landuse_data_json)
        html_template = html_template.replace("/*__RAIL_DATA__*/null/*__END_RAIL__*/", rail_data_json)
        html_template = html_template.replace("/*__ROAD_DATA__*/null/*__END_ROAD__*/", road_data_json)
        html_template = html_template.replace("/*__SYNTAX_DATA__*/null/*__END_SYNTAX__*/", syntax_data_json)
        html_template = html_template.replace("/*__SYNTAX_METRIC__*/'integration_norm'/*__END_SYNTAX_METRIC__*/", f"'{syntax_metric}'")
        html_template = html_template.replace("/*__IS_3D__*/true/*__END_IS_3D__*/", "true" if is_3d_mode else "false")
        html_template = html_template.replace("/*__SHOW_BUILDING_STYLE__*/false/*__END_SHOW_BUILDING_STYLE__*/", "true" if show_bstyle else "false")
        html_template = html_template.replace("/*__SHOW_LIGHTING__*/true/*__END_LIGHTING__*/", "true" if show_lighting else "false")
        html_template = html_template.replace("/*__SUN_TIME__*/10/*__END_SUN_TIME__*/", str(sun_time))
        html_template = html_template.replace("/*__COL_PAYLOAD__*/null/*__END_COL_PAY__*/", col_payload_json)
        html_template = html_template.replace("/*__HEAT_PAYLOAD__*/null/*__END_HEAT_PAY__*/", heat_payload_json)
        html_template = html_template.replace("/*__HEX_PAYLOAD__*/null/*__END_HEX_PAY__*/", "null")
        html_template = html_template.replace("/*__PIPE_PAYLOAD__*/null/*__END_PIPE__*/", "null")
        
        st.markdown("""<style>
            iframe[title="st.iframe"] { border-radius: 18px !important; overflow: hidden !important; border: 1px solid rgba(0, 0, 0, 0.08); box-shadow: 0 12px 30px rgba(0, 0, 0, 0.04); }
        </style>""", unsafe_allow_html=True)
        components.html(html_template, height=height, scrolling=False)
    except Exception as e:
        st.error(f"地图组件核心加载失败: {e!s}")
