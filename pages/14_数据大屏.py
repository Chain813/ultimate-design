"""14 · 数据大屏 — sc-datav 风格全屏数据可视化看板

将平台核心指标、3D 数字孪生底座与多维图表组织为大屏展示形式，
视觉风格与项目现有 Apple HIG 浅色主题保持一致。
"""

import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from src.config import get_static_url, get_map_viewport, get_site_name
from src.engines.spatial_engine import (
    get_hud_statistics,
    get_merged_poi_data,
    get_skyline_features,
)
from src.ui.app_shell import render_top_nav
from src.ui.digital_twin import load_map_data
from src.utils.runtime_flags import is_mobile_client


st.set_page_config(page_title="数据大屏", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

# ── 隐藏 Streamlit 默认间距，实现沉浸式大屏 ──
st.markdown("""<style>
.block-container{padding:0 !important;max-width:100% !important}
iframe[title="streamlit_app.components.v1.html"]{border:none !important}
@media (max-width: 768px) {
    iframe[title="streamlit_app.components.v1.html"] {
        height: 1650px !important;
    }
}
</style>""", unsafe_allow_html=True)



# ═══════════════════════════════════════════
# 📊 数据采集
# ═══════════════════════════════════════════

@st.cache_data(ttl=3600)
def _collect_datav_payload():
    """一次性采集所有大屏所需数据，缓存 1h。"""
    stats = get_hud_statistics()
    skyline = get_skyline_features()

    # POI 前 80 条用于滚动列表
    try:
        poi_df = get_merged_poi_data()
        poi_list = poi_df[["Name", "Lng", "Lat"]].head(80).to_dict(orient="records")
    except Exception:
        poi_list = []

    # 用地类型统计
    landuse_chart = []
    try:
        import geopandas as gpd
        lu_path = Path("data/gis/landuse_clipped.geojson")
        if lu_path.exists():
            gdf = gpd.read_file(str(lu_path))
            if "Type" in gdf.columns:
                counts = gdf["Type"].value_counts().head(8)
                landuse_chart = [{"name": str(k), "value": int(v)} for k, v in counts.items()]
    except Exception:
        pass

    # 建筑高度分段统计
    height_chart = []
    try:
        import geopandas as gpd
        b_path = Path("data/gis/Building_Footprints.geojson")
        if b_path.exists():
            gdf = gpd.read_file(str(b_path))
            col = "Floor" if "Floor" in gdf.columns else ("levels" if "levels" in gdf.columns else None)
            if col:
                import pandas as pd
                floors = pd.to_numeric(gdf[col], errors="coerce").dropna()
                heights = floors * 3.5
                bins = [0, 7, 14, 24, 50, 200]
                labels = ["≤2F", "3-4F", "5-7F", "8-14F", "15F+"]
                cats = pd.cut(heights, bins=bins, labels=labels)
                vc = cats.value_counts().reindex(labels, fill_value=0)
                height_chart = [{"name": n, "value": int(v)} for n, v in vc.items()]
    except Exception:
        pass

    return {
        "boundary_ha": stats.get("boundary_ha", "~170"),
        "building_count": skyline.get("building_count", 0),
        "poi_count": stats.get("poi_count", "N/A"),
        "gvi_count": stats.get("gvi_count", "N/A"),
        "max_height": skyline.get("max_height", 0),
        "avg_height": skyline.get("avg_height", 0),
        "high_rise_ratio": skyline.get("high_rise_ratio", 0),
        "poi_list": poi_list,
        "landuse_chart": landuse_chart,
        "height_chart": height_chart,
    }


# ═══════════════════════════════════════════
# 🖼️ 渲染大屏
# ═══════════════════════════════════════════

payload = _collect_datav_payload()

# 加载 GeoJSON 数据用于地图
bound_data_json = json.dumps(load_map_data("data/gis/Boundary_Scope.geojson")) or "null"
plots_data_json = json.dumps(load_map_data("data/gis/Key_Plots_District.json")) or "null"
building_url = get_static_url("buildings.geojson")

# 加载大屏 HTML 模板
template_path = Path("assets/datav_bigscreen.html")
if not template_path.exists():
    st.error("大屏模板文件 assets/datav_bigscreen.html 不存在。")
    st.stop()

html = template_path.read_text(encoding="utf-8")

# 注入数据
html = html.replace("/*__SITE_NAME__*/", get_site_name())
html = html.replace('/*__DV_MAP_CONFIG__*/{"center": [125.34064, 43.90095], "zoom": 14.4, "pitch": 65.0, "bearing": 30.0}/*__END_MAP_CONFIG__*/', json.dumps(get_map_viewport()))
html = html.replace("/*__DV_STATS__*/null/*__END__*/", json.dumps(payload, ensure_ascii=False))
html = html.replace("/*__DV_BOUNDARY__*/null/*__END__*/", bound_data_json)
html = html.replace("/*__DV_PLOTS__*/null/*__END__*/", plots_data_json)
html = html.replace("/*__DV_BUILDING_URL__*/null/*__END__*/", json.dumps(building_url))

is_mobile = is_mobile_client()
iframe_height = 1650 if is_mobile else 880
components.html(html, height=iframe_height, scrolling=is_mobile)

