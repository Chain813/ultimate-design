"""Dual-Track Site Ingestion Panel for UltimateDESIGN.

Provides dual-track site onboarding:
- Mode A (Professional GIS Upload): Ingests GeoJSON, Shapefile (.zip), or DXF, automatically parsing
  bounding extents, centroids, metric areas, and plot features.
- Mode B (Lightweight Bounding Box & Open Data): Coordinates / city name input with automated
  OpenStreetMap road network and building footprint fetching via OSMDataFetcher.
- Statutory Regulatory Redline Limits: Configurable FAR, Height, Building Density, Greenery Ratio.
- Persistence: Saves custom site context to st.session_state["custom_site_context"] and config/custom_site.json.
"""

from __future__ import annotations

import io
import json
import logging
import math
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import geopandas as gpd
import streamlit as st
from shapely.geometry import Polygon, MultiPolygon, shape, box

from src.engines.context_adaptive_engine import (
    get_utm_epsg_for_coordinates,
    infer_plot_diagnostics,
    generate_adaptive_personas,
    generate_adaptive_aigc_prompt,
)
from src.engines.osm_fetcher import OSMDataFetcher

logger = logging.getLogger("ultimateDESIGN.site_ingestion")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "custom_site.json"
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "custom_site"


# ═══════════════════════════════════════════════════════════════
# Persistence Helpers
# ═══════════════════════════════════════════════════════════════

def load_custom_site(config_path: Optional[Union[str, Path]] = None) -> Optional[Dict[str, Any]]:
    """Loads custom site context from JSON configuration file."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load custom site from {path}: {e}")
        return None


def save_custom_site(
    site_context: Dict[str, Any],
    config_path: Optional[Union[str, Path]] = None,
) -> Path:
    """Saves custom site context dictionary to JSON configuration file."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(site_context, f, ensure_ascii=False, indent=2)
    return path


# ═══════════════════════════════════════════════════════════════
# Mode A: Parsing GIS / CAD Formats
# ═══════════════════════════════════════════════════════════════

def parse_geojson_data(content: Union[str, bytes, Dict[str, Any]]) -> Dict[str, Any]:
    """Parses GeoJSON data and derives spatial boundaries, centroid, metric area, and plot attributes.

    Args:
        content: GeoJSON string, bytes, or parsed dict.

    Returns:
        Dict[str, Any]: Structured site context with bbox, center, area_ha, and features.
    """
    if isinstance(content, bytes):
        raw_dict = json.loads(content.decode("utf-8"))
    elif isinstance(content, str):
        raw_dict = json.loads(content)
    elif isinstance(content, dict):
        raw_dict = content
    else:
        raise ValueError(f"Unsupported content type for GeoJSON parsing: {type(content)}")

    features = raw_dict.get("features", [])
    if not features:
        if raw_dict.get("type") == "Feature":
            features = [raw_dict]
        elif raw_dict.get("type") in ["Polygon", "MultiPolygon", "Point", "LineString", "GeometryCollection"]:
            # Wrapped single geometry
            features = [{"type": "Feature", "geometry": raw_dict, "properties": {}}]

    all_lons: List[float] = []
    all_lats: List[float] = []
    geom_types = set()
    parsed_plots: List[Dict[str, Any]] = []

    total_area_m2 = 0.0

    for idx, feat in enumerate(features):
        geom_dict = feat.get("geometry")
        if not geom_dict:
            continue
        g_type = geom_dict.get("type", "")
        geom_types.add(g_type)
        props = feat.get("properties", {}) or {}

        try:
            geom_obj = shape(geom_dict)
            bounds = geom_obj.bounds  # (minx, miny, maxx, maxy)
            all_lons.extend([bounds[0], bounds[2]])
            all_lats.extend([bounds[1], bounds[3]])

            # Calculate metric area via UTM projection
            feat_center_lon = (bounds[0] + bounds[2]) / 2.0
            feat_center_lat = (bounds[1] + bounds[3]) / 2.0
            epsg = get_utm_epsg_for_coordinates(feat_center_lon, feat_center_lat)

            gdf_single = gpd.GeoDataFrame([{"geometry": geom_obj}], crs="EPSG:4326")
            gdf_utm = gdf_single.to_crs(f"EPSG:{epsg}")
            area_m2 = float(gdf_utm.geometry.area.iloc[0]) if geom_obj.geom_type in ["Polygon", "MultiPolygon"] else 0.0
            explicit_sqm = props.get("Shape_Area") or props.get("area_sqm") or props.get("area_m2")
            if explicit_sqm is not None:
                try:
                    area_m2 = float(explicit_sqm)
                except (ValueError, TypeError):
                    pass
            total_area_m2 += area_m2

            plot_name = props.get("name") or props.get("NAME") or props.get("OBJECTID") or f"Plot_{idx + 1}"
            land_use = (
                props.get("land_use")
                or props.get("landuse")
                or props.get("type")
                or props.get("用地性质")
                or "residential"
            )

            parsed_plots.append({
                "id": idx + 1,
                "name": str(plot_name),
                "land_use": str(land_use),
                "area_ha": round(area_m2 / 10000.0, 3),
                "area_m2": round(area_m2, 1),
                "geometry_type": g_type,
                "properties": props,
            })
        except Exception as e:
            logger.debug(f"Error computing geometry for feature {idx}: {e}")

    if all_lons and all_lats:
        bbox = [min(all_lons), min(all_lats), max(all_lons), max(all_lats)]
        center = [(bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0]
    else:
        bbox = [0.0, 0.0, 0.0, 0.0]
        center = [0.0, 0.0]

    area_ha = round(total_area_m2 / 10000.0, 2)
    utm_epsg = get_utm_epsg_for_coordinates(center[0], center[1]) if center != [0.0, 0.0] else 32650

    return {
        "source_type": "geojson",
        "features_count": len(features),
        "feature_count": len(features),
        "geometry_types": sorted(list(geom_types)),
        "bbox": bbox,
        "center": center,
        "utm_epsg": utm_epsg,
        "area_ha": area_ha,
        "total_area_m2": round(total_area_m2, 1),
        "plots": parsed_plots,
        "raw_geojson": raw_dict,
    }


def parse_shapefile_zip(zip_bytes: bytes) -> Dict[str, Any]:
    """Extracts zipped Shapefile and reads vector features into GeoJSON-equivalent context."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = Path(tmp_dir) / "upload.zip"
        zip_path.write_bytes(zip_bytes)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)

        # Find .shp file
        shp_files = list(Path(tmp_dir).glob("**/*.shp"))
        if not shp_files:
            raise FileNotFoundError("未在上传的压缩包中找到 .shp 格式矢量文件。")

        gdf = gpd.read_file(str(shp_files[0]))
        if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")
        elif not gdf.crs:
            gdf.set_crs("EPSG:4326", inplace=True)

        geojson_str = gdf.to_json()
        result = parse_geojson_data(geojson_str)
        result["source_type"] = "shapefile"
        return result


def parse_dxf_data(dxf_bytes: bytes) -> Dict[str, Any]:
    """Parses DXF ASCII stream, extracting approximate extents and entities."""
    text_content = dxf_bytes.decode("utf-8", errors="ignore")
    lines = [line.strip() for line in text_content.splitlines()]

    # Extract coordinate tags 10..13 (X), 20..23 (Y)
    xs: List[float] = []
    ys: List[float] = []

    i = 0
    while i < len(lines) - 1:
        code = lines[i]
        val = lines[i + 1]
        if code in ["10", "11", "12", "13"]:
            try:
                xs.append(float(val))
            except ValueError:
                pass
        elif code in ["20", "21", "22", "23"]:
            try:
                ys.append(float(val))
            except ValueError:
                pass
        i += 2

    if xs and ys:
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        # Check if coordinates look like WGS84 (lon: -180..180, lat: -90..90) or local projected
        is_wgs84 = -180.0 <= min_x <= 180.0 and -180.0 <= max_x <= 180.0 and -90.0 <= min_y <= 90.0 and -90.0 <= max_y <= 90.0

        if is_wgs84:
            bbox = [min_x, min_y, max_x, max_y]
            center = [(min_x + max_x) / 2.0, (min_y + max_y) / 2.0]
            utm_epsg = get_utm_epsg_for_coordinates(center[0], center[1])
            dx_m = max(50.0, (max_x - min_x) * 111320.0 * math.cos(math.radians(center[1])))
            dy_m = max(50.0, (max_y - min_y) * 111320.0)
            area_m2 = dx_m * dy_m * 0.6
        else:
            # Local coordinate system fallback
            bbox = [min_x, min_y, max_x, max_y]
            center = [(min_x + max_x) / 2.0, (min_y + max_y) / 2.0]
            utm_epsg = 32650
            dx_m = max(50.0, max_x - min_x)
            dy_m = max(50.0, max_y - min_y)
            area_m2 = dx_m * dy_m * 0.6

        area_ha = max(0.1, round(area_m2 / 10000.0, 2))
    else:
        bbox = [0.0, 0.0, 0.0, 0.0]
        center = [0.0, 0.0]
        utm_epsg = 32650
        area_ha = 5.0
        area_m2 = 50000.0

    return {
        "source_type": "dxf",
        "features_count": max(1, len(xs) // 4),
        "geometry_types": ["CAD_Entity_Group"],
        "bbox": bbox,
        "center": center,
        "utm_epsg": utm_epsg,
        "area_ha": area_ha,
        "total_area_m2": area_m2,
        "plots": [
            {
                "id": 1,
                "name": "CAD设计图层集成地块",
                "land_use": "commercial",
                "area_ha": area_ha,
                "area_m2": area_m2,
                "geometry_type": "CAD_Composite",
            }
        ],
    }


# ═══════════════════════════════════════════════════════════════
# Mode B: Open Data Auto-fetch via OSMFetcher
# ═══════════════════════════════════════════════════════════════

def ingest_from_osm_bbox(
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    city_name: str = "目标城市",
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetches OpenStreetMap building footprints, road networks, and landuse, parsing them into custom site context.

    Args:
        min_lat: Southern latitude bound.
        min_lon: Western longitude bound.
        max_lat: Northern latitude bound.
        max_lon: Eastern longitude bound.
        city_name: Name of the city for contextual derivation.
        output_dir: Directory to save generated GeoJSON assets.

    Returns:
        Dict[str, Any]: Ingested site data.
    """
    center_lon = (min_lon + max_lon) / 2.0
    center_lat = (min_lat + max_lat) / 2.0
    utm_epsg = get_utm_epsg_for_coordinates(center_lon, center_lat)

    save_dir = output_dir or str(DEFAULT_DATA_DIR)
    fetcher = OSMDataFetcher(timeout=25)
    gdfs = fetcher.fetch_by_bbox(min_lat, min_lon, max_lat, max_lon, output_dir=save_dir)

    buildings_gdf = gdfs.get("buildings", gpd.GeoDataFrame())
    roads_gdf = gdfs.get("roads", gpd.GeoDataFrame())
    landuse_gdf = gdfs.get("landuse", gpd.GeoDataFrame())

    b_count = len(buildings_gdf)
    r_count = len(roads_gdf)
    l_count = len(landuse_gdf)

    b_area_m2 = float(buildings_gdf["area_m2"].sum()) if not buildings_gdf.empty and "area_m2" in buildings_gdf.columns else 0.0

    # Total bounding box scope area in ha
    d_lat_m = (max_lat - min_lat) * 111320.0
    d_lon_m = (max_lon - min_lon) * 111320.0 * math.cos(math.radians(center_lat))
    scope_area_ha = round((d_lat_m * d_lon_m) / 10000.0, 2)

    # Inferred building density
    bd_ratio = round((b_area_m2 / (d_lat_m * d_lon_m)), 3) if (d_lat_m * d_lon_m) > 0 else 0.35
    bd_ratio = min(0.85, max(0.10, bd_ratio))

    # Formulate sample plots from landuse or buildings
    plots: List[Dict[str, Any]] = []
    if not landuse_gdf.empty:
        for idx, row in landuse_gdf.head(5).iterrows():
            plots.append({
                "id": int(idx) + 1,
                "name": str(row.get("name") or f"{city_name}片区地块_{idx + 1}"),
                "land_use": str(row.get("type") or "residential"),
                "area_ha": round(scope_area_ha / max(1, len(landuse_gdf)), 2),
                "building_density": bd_ratio,
            })
    else:
        plots.append({
            "id": 1,
            "name": f"{city_name}核心更新地块",
            "land_use": "mixed",
            "area_ha": scope_area_ha,
            "building_density": bd_ratio,
        })

    return {
        "source_type": "osm_fetch",
        "city": city_name,
        "bbox": [min_lon, min_lat, max_lon, max_lat],
        "center": [center_lon, center_lat],
        "utm_epsg": utm_epsg,
        "area_ha": scope_area_ha,
        "building_count": b_count,
        "road_count": r_count,
        "landuse_count": l_count,
        "building_density": bd_ratio,
        "total_building_footprint_m2": round(b_area_m2, 1),
        "plots": plots,
    }


# ═══════════════════════════════════════════════════════════════
# Streamlit Dual-Track Panel UI
# ═══════════════════════════════════════════════════════════════

def render_site_ingestion_panel():
    """Renders the comprehensive dual-track site ingestion panel in Streamlit."""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                border: 1px solid #334155; border-radius: 14px; padding: 22px 26px; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <h3 style="color: #f8fafc; margin: 0 0 6px 0; font-size: 19px; font-weight: 600;">
                    🌐 双轨制地块接入与底模构建平台
                </h3>
                <p style="color: #94a3b8; margin: 0; font-size: 13.5px;">
                    零预置模板 · 纯数据驱动 | 支持专业 GIS 矢量直传 (模式 A) 与全球任意城市坐标圈选抓取 (模式 B)
                </p>
            </div>
            <div style="background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3);
                        padding: 6px 14px; border-radius: 20px; color: #60a5fa; font-size: 12px; font-weight: 600;">
                ⚡ 动态因地制宜推断已就绪
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session state if missing
    if "custom_site_context" not in st.session_state:
        saved_site = load_custom_site()
        st.session_state["custom_site_context"] = saved_site if saved_site else {}

    current_site = st.session_state.get("custom_site_context", {})

    # Display active site status badge if loaded
    if current_site and current_site.get("center"):
        c_lon, c_lat = current_site.get("center", [0, 0])
        s_area = current_site.get("area_ha", 0)
        s_name = current_site.get("name") or current_site.get("city") or "自定义场地"
        s_epsg = current_site.get("utm_epsg", get_utm_epsg_for_coordinates(c_lon, c_lat))
        st.success(
            f"📍 **当前已生效场地底模**：【{s_name}】| 中心坐标：({c_lon:.5f}, {c_lat:.5f}) | "
            f"面积：{s_area} ha | 投影基准：EPSG:{s_epsg}"
        )

    # Tabs for Dual Track Ingestion (with fallback for headless test runners)
    try:
        tabs = st.tabs([
            "📁 模式 A：专业数据上传 (GeoJSON / SHP / DXF)",
            "🌐 模式 B：公开底模自动抓取 (城市名/坐标/范围 -> OSM)",
        ])
        if len(tabs) >= 2:
            tab_mode_a, tab_mode_b = tabs[0], tabs[1]
        else:
            from contextlib import nullcontext
            tab_mode_a, tab_mode_b = nullcontext(), nullcontext()
    except Exception:
        from contextlib import nullcontext
        tab_mode_a, tab_mode_b = nullcontext(), nullcontext()

    parsed_result: Optional[Dict[str, Any]] = None

    # ═══════════════════════════════════════════
    # Tab 1: Mode A
    # ═══════════════════════════════════════════
    with tab_mode_a:
        st.markdown("##### 📤 上传场地空间矢量文件")
        st.caption("支持 AutoCAD DXF、ESRI Shapefile (请打包为 .zip 压缩包上传)、GeoJSON (.json / .geojson)。")

        uploaded_file = st.file_uploader(
            "拖拽或浏览矢量底模文件",
            type=["geojson", "json", "zip", "dxf"],
            key="site_ingest_uploader",
        )

        if uploaded_file is not None:
            filename = uploaded_file.name.lower()
            file_bytes = uploaded_file.read()

            try:
                with st.spinner(f"正在解析矢量数据【{uploaded_file.name}】并计算投影坐标与面积..."):
                    if filename.endswith(".geojson") or filename.endswith(".json"):
                        parsed_result = parse_geojson_data(file_bytes)
                    elif filename.endswith(".zip"):
                        parsed_result = parse_shapefile_zip(file_bytes)
                    elif filename.endswith(".dxf"):
                        parsed_result = parse_dxf_data(file_bytes)

                if parsed_result:
                    st.session_state["_last_ingested_temp"] = parsed_result
                    st.toast("✅ 专业矢量底模解析成功！", icon="🎉")
            except Exception as e:
                st.error(f"❌ 解析失败：{str(e)}")
                logger.error("Error during file ingestion", exc_info=True)

    # ═══════════════════════════════════════════
    # Tab 2: Mode B
    # ═══════════════════════════════════════════
    with tab_mode_b:
        st.markdown("##### 🌍 输入城市名称与目标经纬度圈选底模")
        st.caption("无需准备专业 GIS 图纸，输入全球任意坐标，系统自动调用 Overpass API 抓取高精度建筑轮廓与路网。")

        col_b1, col_b2 = st.columns([1, 2])
        with col_b1:
            city_input = st.text_input("城市名称", value=current_site.get("city", ""), placeholder="如：北京市、上海市、广州市、成都市...")
            site_label = st.text_input("场地名称", value=current_site.get("name", ""), placeholder="如：老工业厂区更新单元、滨水街区")

        with col_b2:
            col_b_lon, col_b_lat, col_b_rad = st.columns(3)
            default_center = current_site.get("center", [125.34064, 43.90095])
            with col_b_lon:
                lon_val = st.number_input("中心经度 (Lon)", value=float(default_center[0]), format="%.5f")
            with col_b_lat:
                lat_val = st.number_input("中心纬度 (Lat)", value=float(default_center[1]), format="%.5f")
            with col_b_rad:
                radius_m = st.number_input("抓取半径范围 (米)", min_value=300, max_value=3000, value=800, step=100)

        if st.button("🚀 自动抓取路网与建筑底模 (OSM Fetch)", type="primary", use_container_width=True):
            try:
                f_lon = float(lon_val)
                f_lat = float(lat_val)
                f_rad = float(radius_m)
            except (ValueError, TypeError):
                f_lon, f_lat, f_rad = 125.34064, 43.90095, 800.0

            d_lat = f_rad / 111320.0
            d_lon = f_rad / (111320.0 * math.cos(math.radians(f_lat)))
            min_lat = f_lat - d_lat
            max_lat = f_lat + d_lat
            min_lon = f_lon - d_lon
            max_lon = f_lon + d_lon

            with st.spinner(f"正在向 OpenStreetMap 检索【{city_input}】({f_lon:.4f}, {f_lat:.4f}) 周边底模要素..."):
                try:
                    parsed_result = ingest_from_osm_bbox(
                        min_lat=min_lat,
                        min_lon=min_lon,
                        max_lat=max_lat,
                        max_lon=max_lon,
                        city_name=city_input,
                    )
                    parsed_result["name"] = site_label
                    st.session_state["_last_ingested_temp"] = parsed_result
                    st.toast("✅ OpenStreetMap 底模抓取与投影完成！", icon="🚀")
                except Exception as e:
                    st.error(f"❌ 抓取底模失败：{str(e)}")
                    logger.error("OSM fetch failed", exc_info=True)

    # Use latest parsed data or stored temp data
    active_parsed = parsed_result or st.session_state.get("_last_ingested_temp") or current_site

    # Display Ingestion Metrics Card
    if active_parsed and active_parsed.get("center") and active_parsed.get("center") != [0.0, 0.0]:
        st.markdown("---")
        st.markdown("##### 📊 解析结果与空间量化指标")
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        center_coords = active_parsed.get("center", [0, 0])
        utm_code = active_parsed.get("utm_epsg") or get_utm_epsg_for_coordinates(center_coords[0], center_coords[1])
        m_col1.metric("中心坐标", f"{center_coords[0]:.4f}°E, {center_coords[1]:.4f}°N")
        m_col2.metric("标准 UTM 投影", f"EPSG:{utm_code}")
        m_col3.metric("场地总面积", f"{active_parsed.get('area_ha', 0)} ha")
        features_num = active_parsed.get("features_count") or (active_parsed.get("building_count", 0) + active_parsed.get("road_count", 0))
        m_col4.metric("解析要素总数", f"{features_num} 项")

    # ═══════════════════════════════════════════
    # Statutory Regulatory Redline Limits Section
    # ═══════════════════════════════════════════
    st.markdown("---")
    st.markdown("##### 📏 当地法定控规红线指标设置 (Statutory Regulatory Limits)")
    st.caption("自由设定规划红线指标底线，引擎将结合真实红线约束推演博弈人设与空间策略。")

    reg_limits = current_site.get("regulatory_limits", {})
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    with col_r1:
        far_val = st.number_input("容积率上限 (FAR Max)", min_value=0.5, max_value=10.0, value=float(reg_limits.get("far", 2.5)), step=0.1)
    with col_r2:
        height_val = st.number_input("建筑限高上限 (Height Limit / m)", min_value=6.0, max_value=250.0, value=float(reg_limits.get("height_limit", 36.0)), step=1.0)
    with col_r3:
        bd_max_val = st.slider("建筑密度上限", min_value=10, max_value=70, value=int(reg_limits.get("building_density_max", 0.35) * 100 if reg_limits.get("building_density_max", 0.35) <= 1.0 else reg_limits.get("building_density_max", 35)), format="%d%%") / 100.0
    with col_r4:
        green_min_val = st.slider("绿地率底线", min_value=10, max_value=60, value=int(reg_limits.get("greenery_ratio_min", 0.30) * 100 if reg_limits.get("greenery_ratio_min", 0.30) <= 1.0 else reg_limits.get("greenery_ratio_min", 30)), format="%d%%") / 100.0

    current_regulatory = {
        "far": far_val,
        "height_limit": height_val,
        "building_density_max": bd_max_val,
        "greenery_ratio_min": green_min_val,
    }

    # ═══════════════════════════════════════════
    # Real-Time Context-Adaptive Inference Preview
    # ═══════════════════════════════════════════
    if active_parsed and active_parsed.get("center") and active_parsed.get("center") != [0.0, 0.0]:
        st.markdown("---")
        st.markdown("##### ⚡ 核心推断引擎联动预览 (Context-Adaptive Live Inferences)")

        primary_plot = active_parsed.get("plots", [{}])[0] if active_parsed.get("plots") else {}
        if not primary_plot.get("area_ha"):
            primary_plot["area_ha"] = active_parsed.get("area_ha", 5.0)

        site_ctx = {
            "city": active_parsed.get("city") or current_site.get("city") or "目标城市",
            "district": active_parsed.get("district", ""),
            "name": active_parsed.get("name") or current_site.get("name") or "更新项目",
            "center": active_parsed.get("center"),
            "lat": active_parsed.get("center")[1],
            "lon": active_parsed.get("center")[0],
        }

        # 1. Pain points diagnostics
        inferred_diags = infer_plot_diagnostics(primary_plot, site_ctx)

        # 2. Adaptive personas
        adaptive_personas = generate_adaptive_personas(site_ctx, primary_plot, current_regulatory)

        # 3. Adaptive AIGC Prompt
        adaptive_aigc = generate_adaptive_aigc_prompt(site_ctx, primary_plot)

        with st.expander("🔍 真实痛点推断清单 (Inferred Plot Diagnostics)", expanded=True):
            for d in inferred_diags:
                st.markdown(f"- ⚠️ {d}")

        with st.expander("🎭 现场衍生 3 组利益相关方 (Dynamic Adaptive Personas)", expanded=False):
            p_cols = st.columns(3)
            for idx, (p_key, p_data) in enumerate(adaptive_personas.items()):
                with p_cols[idx % 3]:
                    st.markdown(f"**{p_data['name']}**")
                    st.caption(f"立场：{p_data['stance']}")
                    st.markdown("**核心利益点：**")
                    for interest in p_data["core_interests"]:
                        st.markdown(f"• {interest}")

        with st.expander("🎨 气候与风貌自适应 AIGC 提示词预览 (Adaptive AIGC Prompt)", expanded=False):
            st.markdown(f"**微气候分区：** `{adaptive_aigc['climate_zone']}`")
            st.caption(f"气候特征：{adaptive_aigc['climate_features']}")
            st.markdown(f"**设计风格：** `{adaptive_aigc['design_style']}`")
            st.text_area("正向提示词 (Positive Prompt)", adaptive_aigc["prompt"], height=90)
            st.text_area("负向提示词 (Negative Prompt)", adaptive_aigc["negative_prompt"], height=60)

    # ═══════════════════════════════════════════
    # Persistence Button
    # ═══════════════════════════════════════════
    st.markdown("---")
    if st.button("💾 保存并应用场地底模 (Save to custom_site.json & Session)", type="primary", use_container_width=True):
        if not active_parsed or not active_parsed.get("center") or active_parsed.get("center") == [0.0, 0.0]:
            st.warning("请先通过模式 A 上传矢量文件或模式 B 抓取有效场地底模。")
            return

        final_context = dict(active_parsed)
        final_context["regulatory_limits"] = current_regulatory
        final_context["city"] = final_context.get("city") or "目标城市"
        final_context["name"] = final_context.get("name") or "自定义接入场地"

        # Attach derived inferences
        try:
            primary_plot = final_context.get("plots", [{}])[0] if final_context.get("plots") else {}
            final_context["diagnostics"] = infer_plot_diagnostics(primary_plot, final_context)
            final_context["personas"] = generate_adaptive_personas(final_context, primary_plot, current_regulatory)
            final_context["aigc_prompt"] = generate_adaptive_aigc_prompt(final_context, primary_plot)
        except Exception as e:
            logger.warning(f"Error attaching inferences: {e}")

        st.session_state["custom_site_context"] = final_context
        saved_file = save_custom_site(final_context)
        st.success(f"✅ 场地底模与指标已持久化保存至 `{saved_file}` 并成功载入当前工作台 Session！")
        st.balloons()


def get_active_candidate_plots() -> List[Dict[str, Any]]:
    """Returns candidate plots for the active site (custom uploaded or base GIS)."""
    # 1. Check session_state or custom_site.json
    custom_site = st.session_state.get("custom_site_context") or load_custom_site()
    if custom_site and custom_site.get("plots"):
        return custom_site["plots"]

    # 2. Check base GIS key plots file
    try:
        from src.config.paths import SHP_FILES
        p_path = SHP_FILES.get("plots")
        if p_path and Path(p_path).exists():
            with open(p_path, "r", encoding="utf-8") as f:
                geo = json.load(f)
            plots = []
            for idx, feat in enumerate(geo.get("features", [])):
                props = feat.get("properties", {})
                name = props.get("name") or props.get("Name") or f"地块_{idx+1}"
                sqm = props.get("Shape_Area") or 35000.0
                plots.append({
                    "name": name,
                    "area_ha": round(float(sqm) / 10000.0, 2),
                    "land_use": props.get("land_use") or props.get("type") or "商业用地",
                    "poi": int(props.get("poi_count", 20)),
                    "gvi": float(props.get("gvi_mean", 15.0)),
                    "svf": float(props.get("svf_mean", 0.55)),
                })
            if plots:
                return plots
    except Exception as exc:
        logger.debug(f"Failed to read base GIS key plots: {exc}")

    # 3. Universal sensible fallback candidate plots
    return [
        {"name": "中心商业更新地块", "area_ha": 3.8, "land_use": "商业用地", "poi": 25, "gvi": 12.0, "svf": 0.58},
        {"name": "老旧生活居住组团", "area_ha": 5.2, "land_use": "居住用地", "poi": 12, "gvi": 18.0, "svf": 0.45},
        {"name": "工业遗存改造示范区", "area_ha": 6.5, "land_use": "工业/仓储用地", "poi": 8, "gvi": 8.5, "svf": 0.65},
    ]


def parse_plots_from_geojson(geojson_data: Any) -> List[Dict[str, Any]]:
    """Helper to parse and return plot list directly from GeoJSON."""
    parsed = parse_geojson_data(geojson_data)
    return parsed.get("plots", [])


def parse_site_geometry_from_geojson(geojson_data: Any, city: str = "目标城市", name: str = "自选场地") -> Dict[str, Any]:
    """Helper to parse site boundary and info from GeoJSON."""
    parsed = parse_geojson_data(geojson_data)
    parsed["city"] = city
    parsed["name"] = name
    return parsed

