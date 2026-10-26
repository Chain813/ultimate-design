"""Dual-Track Site Ingestion Panel for UltimateDESIGN.

Provides dual-track site onboarding:
- Mode A (Professional GIS Upload): Ingests GeoJSON, Shapefile (.zip), or DXF, automatically parsing
  bounding extents, centroids, metric areas, and plot features, saving to data/custom_site/.
- Mode B (Lightweight Bounding Box & Open Data): Coordinates / city name input with automated
  OpenStreetMap road network, landuse, and building footprint fetching via OSMDataFetcher.
- Statutory Regulatory Redline Limits: Configurable FAR, Height, Building Density, Greenery Ratio.
- RAG Task Book & Local Regulation Upload: Extracts text from .pdf/.docx/.md/.txt into RAG and stage_bus.
- Active Site Sync & One-Click Changchun Restore: Bridges data/custom_site/ to data/gis/ & static/ with safe backup.
"""

from __future__ import annotations

import io
import json
import logging
import math
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import geopandas as gpd
import streamlit as st
import yaml
from shapely.geometry import MultiPolygon, Polygon, box, mapping, shape
from shapely.ops import unary_union

from src.engines.context_adaptive_engine import (
    generate_adaptive_aigc_prompt,
    generate_adaptive_personas,
    get_utm_epsg_for_coordinates,
    infer_plot_diagnostics,
)
from src.engines.osm_fetcher import OSMDataFetcher, _map_landuse_standard

logger = logging.getLogger("ultimateDESIGN.site_ingestion")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "custom_site.json"
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "custom_site"
GIS_DIR = PROJECT_ROOT / "data" / "gis"
STATIC_DIR = PROJECT_ROOT / "static"
PROJECT_YAML_PATH = PROJECT_ROOT / "config" / "project.yaml"
BACKUP_CHANGCHUN_DIR = GIS_DIR / "backup_changchun_default"


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
    # Ensure viewport.center and candidate_plots are synchronized with center and plots
    if site_context.get("center") and "viewport" not in site_context:
        site_context["viewport"] = {
            "center": list(site_context["center"]),
            "zoom": 14.8,
            "pitch": 65.0,
            "bearing": 30.0,
        }
    if site_context.get("plots") and "candidate_plots" not in site_context:
        site_context["candidate_plots"] = site_context["plots"]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(site_context, f, ensure_ascii=False, indent=2)
    return path


# ═══════════════════════════════════════════════════════════════
# Backup, Sync & One-Click Restore Helpers
# ═══════════════════════════════════════════════════════════════

def ensure_changchun_backup(
    backup_dir: Optional[Union[str, Path]] = None,
    gis_dir: Optional[Union[str, Path]] = None,
    static_dir: Optional[Union[str, Path]] = None,
    project_yaml_path: Optional[Union[str, Path]] = None,
) -> Path:
    """Creates a safe backup of the original Changchun GIS, static, and project.yaml files before overwriting."""
    b_dir = Path(backup_dir) if backup_dir else BACKUP_CHANGCHUN_DIR
    g_dir = Path(gis_dir) if gis_dir else GIS_DIR
    s_dir = Path(static_dir) if static_dir else STATIC_DIR
    py_path = Path(project_yaml_path) if project_yaml_path else PROJECT_YAML_PATH
    marker_file = b_dir / "Boundary_Scope.geojson"
    if marker_file.exists() and (b_dir / "project.yaml").exists():
        return b_dir

    b_dir.mkdir(parents=True, exist_ok=True)
    static_b_dir = b_dir / "static"
    static_b_dir.mkdir(parents=True, exist_ok=True)

    gis_files_to_backup = [
        "Boundary_Scope.geojson",
        "Building_Footprints.geojson",
        "Key_Plots_District.json",
        "landuse_clipped.geojson",
        "road_clipped.geojson",
        "rail_clipped.geojson",
    ]
    for fname in gis_files_to_backup:
        src = g_dir / fname
        dst = b_dir / fname
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)

    static_files_to_backup = [
        "buildings.geojson",
        "landuse.geojson",
        "road_clipped.geojson",
        "rail_clipped.geojson",
        "boundary.geojson",
        "roads.geojson",
    ]
    for fname in static_files_to_backup:
        src = s_dir / fname
        if src.exists():
            dst_sub = static_b_dir / fname
            if not dst_sub.exists():
                shutil.copy2(src, dst_sub)
            dst_flat = b_dir / fname
            if not dst_flat.exists():
                shutil.copy2(src, dst_flat)

    if py_path.exists() and not (b_dir / "project.yaml").exists():
        shutil.copy2(py_path, b_dir / "project.yaml")

    logger.info(f"Changchun default site backup verified at {b_dir}")
    return b_dir


def _update_project_yaml_from_context(site_context: Dict[str, Any], project_yaml_path: Optional[Path] = None) -> None:
    """Updates config/project.yaml with the custom site's name, city, center, and area_ha."""
    py_path = project_yaml_path or PROJECT_YAML_PATH
    try:
        data: Dict[str, Any] = {}
        if py_path.exists():
            with open(py_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

        city = site_context.get("city") or "目标城市"
        name = site_context.get("name") or "自定义更新单元"
        center = site_context.get("center") or [125.34064, 43.90095]
        area_ha = site_context.get("area_ha") or 50.0

        data.setdefault("project", {})
        data["project"]["name"] = f"{city}{name}城市更新设计平台"

        data.setdefault("site", {})
        data["site"]["city"] = city
        data["site"]["name"] = name
        data["site"]["center"] = [float(center[0]), float(center[1])]
        data["site"]["area_ha"] = float(area_ha)
        data["site"].setdefault("viewport", {})
        data["site"]["viewport"]["center"] = [float(center[0]), float(center[1])]
        data["site"]["viewport"].setdefault("zoom", 14.6)
        data["site"]["viewport"].setdefault("pitch", 65.0)
        data["site"]["viewport"].setdefault("bearing", 30.0)

        py_path.parent.mkdir(parents=True, exist_ok=True)
        with open(py_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
    except Exception as e:
        logger.warning(f"Failed to update project.yaml: {e}")


def activate_custom_site_files(
    custom_dir: Optional[Union[str, Path]] = None,
    site_context: Optional[Dict[str, Any]] = None,
    gis_dir: Optional[Union[str, Path]] = None,
    static_dir: Optional[Union[str, Path]] = None,
    backup_dir: Optional[Union[str, Path]] = None,
    project_yaml_path: Optional[Union[str, Path]] = None,
) -> Dict[str, str]:
    """Bridges custom site GeoJSON files from data/custom_site/ to data/gis/, static/, and config/project.yaml.

    Automatically creates a one-time backup of the original Changchun site in data/gis/backup_changchun_default/
    before overwriting any active GIS or static files.
    """
    c_dir = Path(custom_dir) if custom_dir else DEFAULT_DATA_DIR
    g_dir = Path(gis_dir) if gis_dir else GIS_DIR
    s_dir = Path(static_dir) if static_dir else STATIC_DIR
    b_dir = Path(backup_dir) if backup_dir else BACKUP_CHANGCHUN_DIR
    py_path = Path(project_yaml_path) if project_yaml_path else PROJECT_YAML_PATH

    ensure_changchun_backup(b_dir, gis_dir=g_dir, static_dir=s_dir, project_yaml_path=py_path)
    c_dir.mkdir(parents=True, exist_ok=True)
    g_dir.mkdir(parents=True, exist_ok=True)
    s_dir.mkdir(parents=True, exist_ok=True)

    ctx = site_context
    if ctx is None:
        try:
            ctx = st.session_state.get("custom_site_context") or load_custom_site()
        except Exception:
            ctx = load_custom_site()

    # If custom_dir lacks boundary or plots but ctx has raw_geojson or bbox, generate them
    if ctx:
        if not (c_dir / "Boundary_Scope.geojson").exists() or not (c_dir / "Key_Plots_District.json").exists():
            save_mode_a_files(ctx, custom_dir=c_dir, auto_fetch_osm=False)

        # Ensure supplementary layers (buildings, roads, landuse) exist in custom_dir
        missing_supp = any(
            not (c_dir / f).exists()
            for f in ("Building_Footprints.geojson", "road_clipped.geojson", "landuse_clipped.geojson")
        )
        if missing_supp:
            bbox = ctx.get("bbox")
            center = ctx.get("center")
            if bbox and len(bbox) == 4 and bbox != [0.0, 0.0, 0.0, 0.0]:
                min_lon, min_lat, max_lon, max_lat = bbox
            elif center and len(center) == 2 and center != [0.0, 0.0]:
                min_lon, min_lat = center[0] - 0.006, center[1] - 0.006
                max_lon, max_lat = center[0] + 0.006, center[1] + 0.006
            else:
                min_lon, min_lat, max_lon, max_lat = 125.32, 43.88, 125.36, 43.91

            if abs(max_lon - min_lon) < 1e-4:
                min_lon -= 0.005
                max_lon += 0.005
            if abs(max_lat - min_lat) < 1e-4:
                min_lat -= 0.005
                max_lat += 0.005

            fetcher = OSMDataFetcher(timeout=15)
            utm_crs = f"EPSG:{get_utm_epsg_for_coordinates((min_lon + max_lon) / 2.0, (min_lat + max_lat) / 2.0)}"
            with tempfile.TemporaryDirectory() as tmp_osm:
                fetcher._generate_fallback_gdfs(min_lat, min_lon, max_lat, max_lon, utm_crs, output_dir=tmp_osm)
                for fname in (
                    "Boundary_Scope.geojson",
                    "Key_Plots_District.json",
                    "Building_Footprints.geojson",
                    "road_clipped.geojson",
                    "road_network_clipped.geojson",
                    "landuse_clipped.geojson",
                ):
                    src_f = Path(tmp_osm) / fname
                    dst_f = c_dir / fname
                    if src_f.exists() and not dst_f.exists():
                        shutil.copy2(src_f, dst_f)

    # Sync road_network_clipped.geojson <-> road_clipped.geojson if only one exists
    if (c_dir / "road_network_clipped.geojson").exists() and not (c_dir / "road_clipped.geojson").exists():
        shutil.copy2(c_dir / "road_network_clipped.geojson", c_dir / "road_clipped.geojson")
    elif (c_dir / "road_clipped.geojson").exists() and not (c_dir / "road_network_clipped.geojson").exists():
        shutil.copy2(c_dir / "road_clipped.geojson", c_dir / "road_network_clipped.geojson")

    synced: Dict[str, str] = {}

    # Copy to data/gis/
    gis_sync_list = [
        "Boundary_Scope.geojson",
        "Key_Plots_District.json",
        "Building_Footprints.geojson",
        "road_clipped.geojson",
        "landuse_clipped.geojson",
    ]
    for fname in gis_sync_list:
        src = c_dir / fname
        dst = g_dir / fname
        if src.exists():
            shutil.copy2(src, dst)
            synced[f"gis/{fname}"] = str(dst)

    # Copy to static/ for 3D Deck.GL viewer
    static_sync_map = {
        "Boundary_Scope.geojson": ["boundary.geojson"],
        "Building_Footprints.geojson": ["buildings.geojson"],
        "landuse_clipped.geojson": ["landuse.geojson"],
        "road_clipped.geojson": ["road_clipped.geojson", "roads.geojson"],
    }
    for src_name, dst_names in static_sync_map.items():
        src = c_dir / src_name
        if src.exists():
            for dst_name in dst_names:
                dst = s_dir / dst_name
                shutil.copy2(src, dst)
                synced[f"static/{dst_name}"] = str(dst)

    if ctx:
        _update_project_yaml_from_context(ctx, project_yaml_path=py_path)
        synced["config/project.yaml"] = str(py_path)

    try:
        st.cache_data.clear()
    except Exception:
        pass

    return synced


def restore_default_changchun_site(
    backup_dir: Optional[Union[str, Path]] = None,
    gis_dir: Optional[Union[str, Path]] = None,
    static_dir: Optional[Union[str, Path]] = None,
    project_yaml_path: Optional[Union[str, Path]] = None,
    custom_config_path: Optional[Union[str, Path]] = None,
) -> bool:
    """Restores the original Changchun default site files from data/gis/backup_changchun_default/."""
    b_dir = Path(backup_dir) if backup_dir else BACKUP_CHANGCHUN_DIR
    g_dir = Path(gis_dir) if gis_dir else GIS_DIR
    s_dir = Path(static_dir) if static_dir else STATIC_DIR
    py_path = Path(project_yaml_path) if project_yaml_path else PROJECT_YAML_PATH
    cfg_path = Path(custom_config_path) if custom_config_path else DEFAULT_CONFIG_PATH

    if b_dir.exists():
        gis_files = [
            "Boundary_Scope.geojson",
            "Building_Footprints.geojson",
            "Key_Plots_District.json",
            "landuse_clipped.geojson",
            "road_clipped.geojson",
            "rail_clipped.geojson",
        ]
        for fname in gis_files:
            src = b_dir / fname
            if src.exists():
                shutil.copy2(src, g_dir / fname)

        static_files = [
            "buildings.geojson",
            "landuse.geojson",
            "road_clipped.geojson",
            "rail_clipped.geojson",
            "boundary.geojson",
            "roads.geojson",
        ]
        for fname in static_files:
            src_sub = b_dir / "static" / fname
            src_flat = b_dir / fname
            if src_sub.exists():
                shutil.copy2(src_sub, s_dir / fname)
            elif src_flat.exists():
                shutil.copy2(src_flat, s_dir / fname)

        if (b_dir / "project.yaml").exists():
            shutil.copy2(b_dir / "project.yaml", py_path)

    if cfg_path.exists():
        try:
            cfg_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to remove {cfg_path}: {e}")

    try:
        st.session_state["custom_site_context"] = {}
        st.session_state.pop("_last_ingested_temp", None)
        st.cache_data.clear()
        st.cache_resource.clear()
    except Exception:
        pass

    return True


# ═══════════════════════════════════════════════════════════════
# Mode A: Parsing GIS / CAD Formats & Saving Custom Site Vectors
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
        raw_dict = json.loads(json.dumps(content))
    else:
        raise ValueError(f"Unsupported content type for GeoJSON parsing: {type(content)}")

    features = raw_dict.get("features", [])
    if not features:
        if raw_dict.get("type") == "Feature":
            features = [raw_dict]
        elif raw_dict.get("type") in ["Polygon", "MultiPolygon", "Point", "LineString", "GeometryCollection"]:
            features = [{"type": "Feature", "geometry": raw_dict, "properties": {}}]
        raw_dict = {"type": "FeatureCollection", "features": features}

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
        props = feat.get("properties")
        if not isinstance(props, dict):
            props = {}
            feat["properties"] = props

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
                    val = float(explicit_sqm)
                    if val > 0:
                        area_m2 = val
                except (ValueError, TypeError):
                    pass
            total_area_m2 += area_m2

            plot_name = (
                props.get("name")
                or props.get("Name")
                or props.get("NAME")
                or props.get("OBJECTID")
                or f"Plot_{idx + 1}"
            )
            land_use = (
                props.get("land_use")
                or props.get("landuse")
                or props.get("Type")
                or props.get("type")
                or props.get("用地性质")
                or "residential"
            )
            std = _map_landuse_standard(str(land_use))
            area_ha_val = round(area_m2 / 10000.0, 3)

            # Enrich feature properties in-place for downstream GIS engines
            props["OBJECTID"] = props.get("OBJECTID") or (idx + 1)
            props["name"] = str(plot_name)
            props["Name"] = str(plot_name)
            props["land_use"] = str(land_use)
            props["Type"] = std["Type"]
            props["type"] = std["type"]
            props["GB_Code"] = std["GB_Code"]
            props["Color"] = std["Color"]
            props["color"] = std["color"]
            props["Shape_Area"] = round(area_m2, 2)
            props["area_m2"] = round(area_m2, 2)
            props["area_ha"] = area_ha_val
            props.setdefault("FAR", std["FAR"])
            props.setdefault("poi", int(props.get("poi_count") or (15 + idx * 5)))
            props.setdefault("gvi", float(props.get("gvi_mean") or (16.0 + idx * 2.5)))
            props.setdefault("svf", float(props.get("svf_mean") or 0.55))

            parsed_plots.append({
                "id": idx + 1,
                "name": str(plot_name),
                "Name": str(plot_name),
                "land_use": str(land_use),
                "Type": std["Type"],
                "area_ha": area_ha_val,
                "area_m2": round(area_m2, 1),
                "Shape_Area": round(area_m2, 1),
                "FAR": float(props["FAR"]),
                "poi": int(props["poi"]),
                "gvi": float(props["gvi"]),
                "svf": float(props["svf"]),
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
        "candidate_plots": parsed_plots,
        "raw_geojson": raw_dict,
    }


def save_mode_a_files(
    parsed_result: Dict[str, Any],
    custom_dir: Optional[Union[str, Path]] = None,
    supplementary_files: Optional[Dict[str, bytes]] = None,
    auto_fetch_osm: bool = False,
) -> Path:
    """Saves Mode A uploaded vector data to data/custom_site/Boundary_Scope.geojson and Key_Plots_District.json.

    Ensures Name, Shape_Area (in m2), and area_ha attributes exist on every feature.
    Optionally writes supplementary layers or triggers OSM fetch for buildings/roads/landuse.
    """
    c_dir = Path(custom_dir) if custom_dir else DEFAULT_DATA_DIR
    c_dir.mkdir(parents=True, exist_ok=True)

    raw_geo = parsed_result.get("raw_geojson")
    bbox = parsed_result.get("bbox", [125.33, 43.89, 125.35, 43.91])
    total_area_m2 = float(parsed_result.get("total_area_m2") or (float(parsed_result.get("area_ha", 10.0)) * 10000.0))
    area_ha = round(total_area_m2 / 10000.0, 2)

    poly_geoms = []
    plot_features = []

    if raw_geo and isinstance(raw_geo, dict) and raw_geo.get("features"):
        for idx, feat in enumerate(raw_geo["features"]):
            geom_d = feat.get("geometry")
            if not geom_d:
                continue
            try:
                g = shape(geom_d)
                if g.geom_type in ("Polygon", "MultiPolygon"):
                    poly_geoms.append(g)
                else:
                    poly_geoms.append(g.buffer(0.0005))
            except Exception:
                continue
            props = dict(feat.get("properties") or {})
            p_name = props.get("Name") or props.get("name") or f"地块_{idx + 1}"
            p_area = float(props.get("Shape_Area") or props.get("area_m2") or (total_area_m2 / max(1, len(raw_geo["features"]))))
            std = _map_landuse_standard(props.get("land_use") or props.get("Type") or props.get("type") or "residential")
            props.update({
                "OBJECTID": idx + 1,
                "Name": str(p_name),
                "name": str(p_name),
                "Type": std["Type"],
                "type": std["type"],
                "land_use": str(props.get("land_use") or std["Type"]),
                "Shape_Area": round(p_area, 2),
                "area_m2": round(p_area, 2),
                "area_ha": round(p_area / 10000.0, 3),
                "FAR": float(props.get("FAR") or std["FAR"]),
                "poi": int(props.get("poi") or (15 + idx * 5)),
                "gvi": float(props.get("gvi") or (16.0 + idx * 2.5)),
                "svf": float(props.get("svf") or 0.55),
            })
            plot_features.append({
                "type": "Feature",
                "id": idx + 1,
                "properties": props,
                "geometry": mapping(poly_geoms[-1]),
            })

    if not poly_geoms:
        min_lon, min_lat, max_lon, max_lat = (
            bbox if (bbox and len(bbox) == 4 and bbox != [0.0, 0.0, 0.0, 0.0]) else [125.33, 43.89, 125.35, 43.91]
        )
        if abs(max_lon - min_lon) < 1e-5:
            min_lon -= 0.005
            max_lon += 0.005
        if abs(max_lat - min_lat) < 1e-5:
            min_lat -= 0.005
            max_lat += 0.005
        b_poly = box(min_lon, min_lat, max_lon, max_lat)
        poly_geoms = [b_poly]
        plot_features = [{
            "type": "Feature",
            "id": 1,
            "properties": {
                "OBJECTID": 1,
                "Name": parsed_result.get("name") or "核心更新单元",
                "name": parsed_result.get("name") or "核心更新单元",
                "Type": "商业服务业设施用地",
                "type": "commercial",
                "land_use": "商业服务业设施用地",
                "Shape_Area": round(total_area_m2, 2),
                "area_m2": round(total_area_m2, 2),
                "area_ha": area_ha,
                "FAR": 2.5,
                "poi": 22,
                "gvi": 18.0,
                "svf": 0.56,
            },
            "geometry": mapping(b_poly),
        }]

    union_geom = unary_union(poly_geoms)
    if union_geom.geom_type not in ("Polygon", "MultiPolygon"):
        union_geom = union_geom.convex_hull

    boundary_fc = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "id": 1,
            "properties": {
                "OBJECTID": 1,
                "Name": parsed_result.get("name") or "研究范围红线",
                "name": parsed_result.get("name") or "研究范围红线",
                "Shape_Area": round(total_area_m2, 2),
                "area_m2": round(total_area_m2, 2),
                "area_ha": area_ha,
            },
            "geometry": mapping(union_geom),
        }],
    }
    plots_fc = {
        "type": "FeatureCollection",
        "features": plot_features,
    }

    with open(c_dir / "Boundary_Scope.geojson", "w", encoding="utf-8") as f:
        json.dump(boundary_fc, f, ensure_ascii=False, indent=2)
    with open(c_dir / "Key_Plots_District.json", "w", encoding="utf-8") as f:
        json.dump(plots_fc, f, ensure_ascii=False, indent=2)

    if supplementary_files:
        supp_map = {
            "buildings": "Building_Footprints.geojson",
            "roads": "road_clipped.geojson",
            "landuse": "landuse_clipped.geojson",
        }
        for key, raw_bytes in supplementary_files.items():
            if raw_bytes and key in supp_map:
                out_p = c_dir / supp_map[key]
                out_p.write_bytes(raw_bytes)
                if key == "roads":
                    (c_dir / "road_network_clipped.geojson").write_bytes(raw_bytes)

    if auto_fetch_osm:
        b_bounds = union_geom.bounds
        min_lon, min_lat, max_lon, max_lat = b_bounds
        fetcher = OSMDataFetcher(timeout=15)
        with tempfile.TemporaryDirectory() as tmp_osm:
            fetcher.fetch_by_bbox(min_lat, min_lon, max_lat, max_lon, output_dir=tmp_osm)
            for fname in ("Building_Footprints.geojson", "road_clipped.geojson", "road_network_clipped.geojson", "landuse_clipped.geojson"):
                src_f = Path(tmp_osm) / fname
                dst_f = c_dir / fname
                if src_f.exists() and (not supplementary_files or fname not in [
                    "Building_Footprints.geojson" if supplementary_files.get("buildings") else "",
                    "road_clipped.geojson" if supplementary_files.get("roads") else "",
                    "landuse_clipped.geojson" if supplementary_files.get("landuse") else "",
                ]):
                    shutil.copy2(src_f, dst_f)

    return c_dir


def parse_shapefile_zip(zip_bytes: bytes) -> Dict[str, Any]:
    """Extracts zipped Shapefile and reads vector features into GeoJSON-equivalent context."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = Path(tmp_dir) / "upload.zip"
        zip_path.write_bytes(zip_bytes)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)

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
        is_wgs84 = -180.0 <= min_x <= 180.0 and -180.0 <= max_x <= 180.0 and -90.0 <= min_y <= 90.0 and -90.0 <= max_y <= 90.0

        if is_wgs84:
            bbox = [min_x, min_y, max_x, max_y]
            center = [(min_x + max_x) / 2.0, (min_y + max_y) / 2.0]
            utm_epsg = get_utm_epsg_for_coordinates(center[0], center[1])
            dx_m = max(50.0, (max_x - min_x) * 111320.0 * math.cos(math.radians(center[1])))
            dy_m = max(50.0, (max_y - min_y) * 111320.0)
            area_m2 = dx_m * dy_m * 0.6
        else:
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

    plots = [
        {
            "id": 1,
            "name": "CAD设计图层集成地块",
            "Name": "CAD设计图层集成地块",
            "land_use": "commercial",
            "Type": "商业服务业设施用地",
            "area_ha": area_ha,
            "area_m2": round(area_m2, 1),
            "Shape_Area": round(area_m2, 1),
            "FAR": 2.5,
            "poi": 20,
            "gvi": 15.0,
            "svf": 0.55,
            "geometry_type": "CAD_Composite",
        }
    ]
    return {
        "source_type": "dxf",
        "features_count": max(1, len(xs) // 4),
        "geometry_types": ["CAD_Entity_Group"],
        "bbox": bbox,
        "center": center,
        "utm_epsg": utm_epsg,
        "area_ha": area_ha,
        "total_area_m2": area_m2,
        "plots": plots,
        "candidate_plots": plots,
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
    """Fetches OpenStreetMap building footprints, road networks, and landuse, parsing them into custom site context."""
    center_lon = (min_lon + max_lon) / 2.0
    center_lat = (min_lat + max_lat) / 2.0
    utm_epsg = get_utm_epsg_for_coordinates(center_lon, center_lat)

    save_dir = output_dir or str(DEFAULT_DATA_DIR)
    fetcher = OSMDataFetcher(timeout=25)
    gdfs = fetcher.fetch_by_bbox(min_lat, min_lon, max_lat, max_lon, output_dir=save_dir)

    buildings_gdf = gdfs.get("buildings", gpd.GeoDataFrame())
    roads_gdf = gdfs.get("roads", gpd.GeoDataFrame())
    landuse_gdf = gdfs.get("landuse", gpd.GeoDataFrame())
    plots_gdf = gdfs.get("plots", gpd.GeoDataFrame())

    b_count = len(buildings_gdf)
    r_count = len(roads_gdf)
    l_count = len(landuse_gdf)

    b_area_m2 = float(buildings_gdf["area_m2"].sum()) if not buildings_gdf.empty and "area_m2" in buildings_gdf.columns else 0.0

    d_lat_m = (max_lat - min_lat) * 111320.0
    d_lon_m = (max_lon - min_lon) * 111320.0 * math.cos(math.radians(center_lat))
    scope_area_ha = round((d_lat_m * d_lon_m) / 10000.0, 2)

    bd_ratio = round((b_area_m2 / (d_lat_m * d_lon_m)), 3) if (d_lat_m * d_lon_m) > 0 else 0.35
    bd_ratio = min(0.85, max(0.10, bd_ratio))

    plots: List[Dict[str, Any]] = []
    source_plots_gdf = plots_gdf if not plots_gdf.empty else landuse_gdf
    if not source_plots_gdf.empty:
        for idx, (_, row) in enumerate(source_plots_gdf.head(5).iterrows()):
            p_name = str(row.get("Name") or row.get("name") or f"{city_name}片区地块_{idx + 1}")
            if p_name.startswith("重点更新单元_") and city_name:
                p_name = f"{city_name}{p_name}"
            p_sqm = float(row.get("Shape_Area") or row.get("area_m2") or (scope_area_ha * 10000.0 / max(1, len(source_plots_gdf))))
            p_ha = round(p_sqm / 10000.0, 2)
            plots.append({
                "id": idx + 1,
                "name": p_name,
                "Name": p_name,
                "land_use": str(row.get("Type") or row.get("type") or "residential"),
                "Type": str(row.get("Type") or "商业服务业设施用地"),
                "area_ha": p_ha,
                "area_m2": round(p_sqm, 1),
                "Shape_Area": round(p_sqm, 1),
                "FAR": float(row.get("FAR") or 2.2),
                "poi": int(row.get("poi") or (16 + idx * 6)),
                "gvi": float(row.get("gvi") or (15.0 + idx * 3.0)),
                "svf": float(row.get("svf") or 0.55),
                "building_density": bd_ratio,
            })
    else:
        plots.append({
            "id": 1,
            "name": f"{city_name}核心更新地块",
            "Name": f"{city_name}核心更新地块",
            "land_use": "mixed",
            "Type": "商业服务业设施用地",
            "area_ha": scope_area_ha,
            "area_m2": round(scope_area_ha * 10000.0, 1),
            "Shape_Area": round(scope_area_ha * 10000.0, 1),
            "FAR": 2.5,
            "poi": 25,
            "gvi": 18.0,
            "svf": 0.55,
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
        "candidate_plots": plots,
    }


# ═══════════════════════════════════════════════════════════════
# RAG Document & Task Book Ingestion Helper
# ═══════════════════════════════════════════════════════════════

def extract_text_from_uploaded_doc(filename: str, file_bytes: bytes) -> str:
    """Extracts plain text from uploaded .txt, .md, .docx, or .pdf files."""
    fname = filename.lower()
    if fname.endswith(".txt") or fname.endswith(".md"):
        return file_bytes.decode("utf-8", errors="ignore").strip()

    if fname.endswith(".docx"):
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception:
            try:
                import xml.etree.ElementTree as ET
                with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                    xml_content = zf.read("word/document.xml")
                tree = ET.fromstring(xml_content)
                return "".join(tree.itertext()).strip()
            except Exception as e:
                logger.warning(f"DOCX text extraction fallback failed: {e}")
                return file_bytes.decode("utf-8", errors="ignore").strip()

    if fname.endswith(".pdf"):
        for pdf_lib in ("pypdf", "PyPDF2"):
            try:
                mod = __import__(pdf_lib)
                reader = mod.PdfReader(io.BytesIO(file_bytes))
                pages = [page.extract_text() or "" for page in reader.pages]
                text = "\n".join(pages).strip()
                if text:
                    return text
            except Exception:
                continue
        try:
            import fitz
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            return "\n".join(page.get_text() for page in doc).strip()
        except Exception:
            pass

    return file_bytes.decode("utf-8", errors="ignore").strip()


def ingest_custom_rag_document(filename: str, file_bytes: bytes) -> str:
    """Extracts text from a task book / regulation file, injects it into RAG knowledge and stage_bus (01.project_info)."""
    text = extract_text_from_uploaded_doc(filename, file_bytes)
    if not text:
        return ""

    # 1. Try rag_engine.add_custom_document()
    injected = False
    try:
        from src.engines import rag_engine
        add_fn = getattr(rag_engine, "add_custom_document", None)
        if callable(add_fn):
            try:
                add_fn(content=text, source=filename)
            except TypeError:
                add_fn(filename, text)
            injected = True
    except Exception as e:
        logger.debug(f"rag_engine.add_custom_document call fallback: {e}")

    if not injected:
        try:
            rag_path = PROJECT_ROOT / "data" / "rag_knowledge.json"
            rag_data: Dict[str, Any] = {}
            if rag_path.exists():
                with open(rag_path, "r", encoding="utf-8") as f:
                    rag_data = json.load(f)
            chunk_id = f"custom_{Path(filename).stem}"
            rag_data[chunk_id] = {
                "content": text[:4000],
                "source": f"用户上传：{filename}",
                "custom": True,
            }
            rag_path.parent.mkdir(parents=True, exist_ok=True)
            with open(rag_path, "w", encoding="utf-8") as f:
                json.dump(rag_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to append custom document to rag_knowledge.json: {e}")

    # 2. Save to stage_bus ('01.project_info' and '01_project_info')
    try:
        from src.workflow.stage_data_bus import save_stage_output
        save_stage_output("01", "project_info", text)
    except Exception:
        pass
    try:
        st.session_state.setdefault("stage_bus", {})["01.project_info"] = text
        st.session_state.setdefault("stage_bus", {})["01_project_info"] = text
    except Exception:
        pass

    return text


# ═══════════════════════════════════════════════════════════════
# Streamlit Dual-Track Panel UI
# ═══════════════════════════════════════════════════════════════

def render_site_ingestion_panel(title: Optional[str] = None):
    """Renders the comprehensive dual-track site ingestion panel in Streamlit."""
    header_title = title or "🌐 双轨制地块接入与底模构建平台"

    # Initialize session state if missing
    if "custom_site_context" not in st.session_state:
        saved_site = load_custom_site()
        st.session_state["custom_site_context"] = saved_site if saved_site else {}

    current_site = st.session_state.get("custom_site_context", {})
    has_custom_active = bool(current_site and current_site.get("center"))
    has_pending_temp = bool(st.session_state.get("_last_ingested_temp") and not has_custom_active)
    custom_files_count = len(list(DEFAULT_DATA_DIR.glob("*.geojson"))) + len(list(DEFAULT_DATA_DIR.glob("*.json"))) if DEFAULT_DATA_DIR.exists() else 0

    if has_custom_active:
        status_badge_html = (
            '<span style="background: #ecfdf5; border: 1px solid #a7f3d0; color: #047857; '
            'padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">'
            '✅ 真实 GIS 底模已激活</span>'
        )
    elif has_pending_temp:
        status_badge_html = (
            '<span style="background: #fffbeb; border: 1px solid #fde68a; color: #b45309; '
            'padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">'
            '⏳ 待同步激活</span>'
        )
    else:
        status_badge_html = (
            '<span style="background: #f1f5f9; border: 1px solid #cbd5e1; color: #475569; '
            'padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">'
            '🏛️ 默认示范底模</span>'
        )

    files_badge_html = (
        f'<span style="background: #eef2ff; border: 1px solid #c7d2fe; color: #4338ca; '
        f'padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">'
        f'⚡ 已挂载图层 ({custom_files_count})</span>'
    )

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%);
                border: 1px solid rgba(0, 113, 227, 0.18); box-shadow: 0 4px 16px rgba(0, 113, 227, 0.05);
                border-radius: 14px; padding: 22px 26px; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
            <div>
                <h3 style="color: #1d1d1f; margin: 0 0 6px 0; font-size: 19px; font-weight: 600;">
                    {header_title}
                </h3>
                <p style="color: #515154; margin: 0; font-size: 13.5px;">
                    零预置模板 · 纯数据驱动 | 支持专业 GIS 矢量直传 (模式 A) 与全球任意城市坐标圈选抓取 (模式 B)
                </p>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                {status_badge_html}
                {files_badge_html}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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
    supp_files: Dict[str, bytes] = {}

    # ═══════════════════════════════════════════
    # Tab 1: Mode A
    # ═══════════════════════════════════════════
    with tab_mode_a:
        st.markdown("##### 📤 上传场地空间矢量文件")
        st.caption("支持 AutoCAD DXF、ESRI Shapefile (请打包为 .zip 压缩包上传)、GeoJSON (.json / .geojson)。")

        col_ma1, col_ma2 = st.columns(2)
        with col_ma1:
            mode_a_city = st.text_input("所属城市 (模式 A)", value=current_site.get("city", ""), key="mode_a_city_input", placeholder="如：武汉市、苏州市...")
        with col_ma2:
            mode_a_name = st.text_input("项目/地块名称 (模式 A)", value=current_site.get("name", ""), key="mode_a_name_input", placeholder="如：历史风貌街区更新单元")

        uploaded_file = st.file_uploader(
            "拖拽或浏览红线/地块矢量文件 (Boundary / Key Plots)",
            type=["geojson", "json", "zip", "dxf"],
            key="site_ingest_uploader",
        )

        with st.expander("➕ 可选：上传补充图层 (建筑轮廓 / 道路网 / 用地性质)，未上传将自动通过 OSM 补全", expanded=False):
            up_bldg = st.file_uploader("建筑轮廓 (Building_Footprints.geojson)", type=["geojson", "json"], key="supp_bldg_up")
            up_road = st.file_uploader("道路网 (road_clipped.geojson)", type=["geojson", "json"], key="supp_road_up")
            up_lu = st.file_uploader("用地性质 (landuse_clipped.geojson)", type=["geojson", "json"], key="supp_lu_up")
            if up_bldg is not None:
                supp_files["buildings"] = up_bldg.read()
            if up_road is not None:
                supp_files["roads"] = up_road.read()
            if up_lu is not None:
                supp_files["landuse"] = up_lu.read()

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
                    if mode_a_city:
                        parsed_result["city"] = mode_a_city
                    if mode_a_name:
                        parsed_result["name"] = mode_a_name
                    save_mode_a_files(
                        parsed_result,
                        custom_dir=DEFAULT_DATA_DIR,
                        supplementary_files=supp_files,
                        auto_fetch_osm=not bool(supp_files),
                    )
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
                        city_name=city_input or "目标城市",
                    )
                    parsed_result["name"] = site_label or f"{city_input or '目标城市'}更新片区"
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
    # Task Book & Local Regulation RAG Uploader
    # ═══════════════════════════════════════════
    st.markdown("---")
    st.markdown("##### 📚 上传项目任务书 / 属地规划法规 (注入 RAG 知识库)")
    st.caption("支持上传课程设计任务书、上位控规文本或地方条例 (.pdf, .docx, .md, .txt)，自动注入 RAG 检索引擎与 Stage 01 任务解读总线。")
    rag_doc_file = st.file_uploader(
        "📚 上传项目任务书 / 属地规划法规 (注入 RAG 知识库)",
        type=["pdf", "docx", "md", "txt"],
        key="site_rag_doc_uploader",
    )
    if rag_doc_file is not None:
        try:
            doc_bytes = rag_doc_file.read()
            extracted_txt = ingest_custom_rag_document(rag_doc_file.name, doc_bytes)
            if extracted_txt:
                st.success(f"✅ 已成功解析《{rag_doc_file.name}》（共 {len(extracted_txt)} 字）并注入 RAG 知识库与项目总线 (`01.project_info`)！")
        except Exception as e:
            st.warning(f"⚠️ 文档解析失败：{e}")

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

        inferred_diags = infer_plot_diagnostics(primary_plot, site_ctx)
        adaptive_personas = generate_adaptive_personas(site_ctx, primary_plot, current_regulatory)
        adaptive_aigc = generate_adaptive_aigc_prompt(site_ctx, primary_plot)

        with st.expander("🔍 真实痛点推断清单 (Inferred Plot Diagnostics)", expanded=True):
            for d in inferred_diags:
                st.markdown(f"- ⚠️ {d}")

        with st.expander("🎭 现场衍生 3 组利益相关方 (Dynamic Adaptive Personas)", expanded=False):
            p_cols = st.columns(3)
            persona_items = adaptive_personas.items() if isinstance(adaptive_personas, dict) else enumerate(adaptive_personas)
            for idx, (_, p_data) in enumerate(persona_items):
                with p_cols[idx % 3]:
                    st.markdown(f"**{p_data.get('name') or p_data.get('role_title', '利益主体')}**")
                    st.caption(f"立场：{p_data.get('stance', '协同博弈')}")
                    st.markdown("**核心利益点：**")
                    interests = p_data.get("core_interests") or [p_data.get("core_demands", "")]
                    for interest in interests:
                        st.markdown(f"• {interest}")

        with st.expander("🎨 气候与风貌自适应 AIGC 提示词预览 (Adaptive AIGC Prompt)", expanded=False):
            st.markdown(f"**微气候分区：** `{adaptive_aigc['climate_zone']}`")
            st.caption(f"气候特征：{adaptive_aigc['climate_features']}")
            st.markdown(f"**设计风格：** `{adaptive_aigc['design_style']}`")
            st.text_area("正向提示词 (Positive Prompt)", adaptive_aigc["prompt"], height=90)
            st.text_area("负向提示词 (Negative Prompt)", adaptive_aigc["negative_prompt"], height=60)

    # ═══════════════════════════════════════════
    # Persistence & One-Click Restore Buttons
    # ═══════════════════════════════════════════
    st.markdown("---")
    btn_col1, btn_col2 = st.columns([2, 1])
    with btn_col1:
        if st.button("💾 保存并应用场地底模 (Save to custom_site.json & Session)", type="primary", use_container_width=True):
            if not active_parsed or not active_parsed.get("center") or active_parsed.get("center") == [0.0, 0.0]:
                st.warning("请先通过模式 A 上传矢量文件或模式 B 抓取有效场地底模。")
                return

            final_context = dict(active_parsed)
            final_context["regulatory_limits"] = current_regulatory
            final_context["city"] = final_context.get("city") or "目标城市"
            final_context["name"] = final_context.get("name") or "自定义接入场地"

            try:
                primary_plot = final_context.get("plots", [{}])[0] if final_context.get("plots") else {}
                final_context["diagnostics"] = infer_plot_diagnostics(primary_plot, final_context)
                final_context["personas"] = generate_adaptive_personas(final_context, primary_plot, current_regulatory)
                final_context["aigc_prompt"] = generate_adaptive_aigc_prompt(final_context, primary_plot)
            except Exception as e:
                logger.warning(f"Error attaching inferences: {e}")

            st.session_state["custom_site_context"] = final_context
            saved_file = save_custom_site(final_context)
            activate_custom_site_files(custom_dir=DEFAULT_DATA_DIR, site_context=final_context)
            st.success(f"✅ 场地底模与指标已持久化保存至 `{saved_file}`，并已同步替换全站 3D 数字孪生与 GIS 引擎底图！")
            st.balloons()

    with btn_col2:
        if st.button("🔄 恢复长春伪满皇宫默认示范工程", use_container_width=True):
            restore_default_changchun_site()
            st.success("✅ 已成功恢复【长春伪满皇宫与周边街区】默认示范工程空间底模与配置！")


def get_active_candidate_plots() -> List[Dict[str, Any]]:
    """Returns candidate plots for the active site (custom uploaded or base GIS)."""
    custom_site = st.session_state.get("custom_site_context") or load_custom_site()
    if custom_site and (custom_site.get("plots") or custom_site.get("candidate_plots")):
        return custom_site.get("plots") or custom_site.get("candidate_plots")

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
                    "land_use": props.get("land_use") or props.get("Type") or props.get("type") or "商业用地",
                    "poi": int(props.get("poi") or props.get("poi_count", 20)),
                    "gvi": float(props.get("gvi") or props.get("gvi_mean", 15.0)),
                    "svf": float(props.get("svf") or props.get("svf_mean", 0.55)),
                })
            if plots:
                return plots
    except Exception as exc:
        logger.debug(f"Failed to read base GIS key plots: {exc}")

    return [
        {"name": "中心商业更新地块", "area_ha": 3.8, "land_use": "商业用地", "poi": 25, "gvi": 12.0, "svf": 0.58},
        {"name": "老旧生活居住组团", "area_ha": 5.2, "land_use": "居住用地", "poi": 12, "gvi": 18.0, "svf": 0.45},
        {"name": "工业遗存改造示范区", "area_ha": 6.5, "land_use": "工业/仓储用地", "poi": 8, "gvi": 8.5, "svf": 0.65},
    ]


def parse_plots_from_geojson(geojson_data: Any) -> List[Dict[str, Any]]:
    """Helper to parse and return plot list directly from GeoJSON."""
    parsed = parse_geojson_data(geojson_data)
    return parsed.get("plots", [])


def render_GIS_source_status_badge() -> None:
    """Renders a compact light-mode semantic status badge indicating active GIS source."""
    custom_site = st.session_state.get("custom_site_context") or load_custom_site()
    if custom_site and custom_site.get("center"):
        site_name = custom_site.get("name") or custom_site.get("city") or "自定义场地"
        st.markdown(
            f'<div style="display:inline-flex; align-items:center; gap:6px; background:#ecfdf5; '
            f'border:1px solid #a7f3d0; color:#047857; padding:4px 12px; border-radius:999px; '
            f'font-size:12px; font-weight:600; margin-bottom:8px;">'
            f'✅ 真实 GIS 底模已激活：{site_name}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="display:inline-flex; align-items:center; gap:6px; background:#f1f5f9; '
            'border:1px solid #cbd5e1; color:#475569; padding:4px 12px; border-radius:999px; '
            'font-size:12px; font-weight:600; margin-bottom:8px;">'
            '🏛️ 当前使用默认示范底模</div>',
            unsafe_allow_html=True,
        )


render_gis_source_status_badge = render_GIS_source_status_badge


def parse_site_geometry_from_geojson(geojson_data: Any, city: str = "目标城市", name: str = "自选场地") -> Dict[str, Any]:
    """Helper to parse site boundary and info from GeoJSON."""
    parsed = parse_geojson_data(geojson_data)
    parsed["city"] = city
    parsed["name"] = name
    return parsed
