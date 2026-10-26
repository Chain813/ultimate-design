"""Spatial data engine: POI fusion, HUD statistics, skyline & street-view metrics.

Usage:
    from src.engines.spatial_engine import (
        get_merged_poi_data, get_hud_statistics,
        get_skyline_features, get_spatial_data,
    )
"""

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from src.config import DATA_FILES, GIS_FILES, SHP_FILES, resolve_path

logger = logging.getLogger("ultimateDESIGN")


def _load_active_custom_site() -> dict[str, Any]:
    """Load active custom site context from session_state or config/custom_site.json."""
    try:
        cs = st.session_state.get("custom_site_context")
        if cs and isinstance(cs, dict) and cs.get("center"):
            return cs
    except Exception:
        pass
    try:
        p = resolve_path("config/custom_site.json")
        if p.exists():
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and data.get("center"):
                    return data
    except Exception:
        pass
    return {}


# ═══════════════════════════════════════════
# POI dual-source fusion
# ═══════════════════════════════════════════

@st.cache_data(ttl=3600, max_entries=20)
def get_merged_poi_data(usecols=None) -> pd.DataFrame:
    """Merge two POI sources and de-duplicate by rounded lat/lng + name."""
    df1 = _safe_read_csv(str(DATA_FILES["poi"]), usecols=usecols)
    df2 = _safe_read_csv(str(DATA_FILES["poi_secondary"]), usecols=usecols)

    if not df1.empty and not df2.empty:
        df_merged = pd.concat([df1, df2], ignore_index=True)
        if "Lng" in df_merged.columns and "Lat" in df_merged.columns:
            return (
                df_merged
                .assign(Lng_round=df_merged["Lng"].round(4),
                        Lat_round=df_merged["Lat"].round(4))
                .drop_duplicates(subset=["Lng_round", "Lat_round", "Name"])
                .drop(columns=["Lng_round", "Lat_round"])
            )
        return df_merged
    return df1 if not df1.empty else df2


def _safe_read_csv(path: str, usecols: list[str] | None = None) -> pd.DataFrame:
    try:
        resolved = resolve_path(path)
        if resolved.exists():
            return pd.read_csv(str(resolved), encoding="utf-8-sig", usecols=usecols)
    except Exception:
        logger.warning("Could not read %s", path, exc_info=True)
    return pd.DataFrame()


# ═══════════════════════════════════════════
# HUD dynamic statistics
# ═══════════════════════════════════════════

@st.cache_data(ttl=1800)
def get_hud_statistics() -> dict[str, Any]:
    """Aggregate live statistics for the HUD overlay."""
    stats: dict[str, Any] = {}
    custom_site = _load_active_custom_site()

    if custom_site:
        city_str = str(custom_site.get("city", ""))
        name_str = str(custom_site.get("name", ""))
        is_changchun = "长春" in city_str or "伪满" in name_str
        bbox = custom_site.get("bbox")

        # Check if any POIs from merged data actually fall within the custom site's bbox
        poi_in_bbox = 0
        if bbox and len(bbox) == 4:
            try:
                df_poi = get_merged_poi_data()
                if not df_poi.empty and "Lng" in df_poi.columns and "Lat" in df_poi.columns:
                    mask = (
                        (df_poi["Lng"] >= bbox[0]) & (df_poi["Lng"] <= bbox[2]) &
                        (df_poi["Lat"] >= bbox[1]) & (df_poi["Lat"] <= bbox[3])
                    )
                    poi_in_bbox = int(mask.sum())
            except Exception:
                poi_in_bbox = 0

        if not is_changchun and poi_in_bbox == 0:
            plots = custom_site.get("plots") or custom_site.get("candidate_plots") or []
            plot_pois = sum(int(p.get("poi") or p.get("poi_count") or 0) for p in plots if isinstance(p, dict))
            b_cnt = int(custom_site.get("building_count") or custom_site.get("features_count") or 0)
            stats["poi_count"] = custom_site.get("poi_count") or (plot_pois if plot_pois > 0 else max(15, b_cnt * 3))
            stats["nlp_count"] = custom_site.get("nlp_count") or max(10, len(plots) * 12)
            stats["gvi_count"] = custom_site.get("gvi_count") or max(12, len(plots) * 15)
            stats["boundary_ha"] = custom_site.get("area_ha") or _calc_boundary_ha(str(GIS_FILES["boundary"]))
            return stats

    stats["poi_count"] = _safe_count(get_merged_poi_data, "N/A")
    stats["nlp_count"] = _safe_count_csv(str(DATA_FILES["nlp"]), "N/A")
    stats["gvi_count"] = _safe_count_csv(str(DATA_FILES["gvi"]), "N/A")
    stats["boundary_ha"] = _calc_boundary_ha(str(GIS_FILES["boundary"]))
    return stats


def _safe_count(getter: Callable | str, fallback: Any) -> Any:
    try:
        return len(getter()) if callable(getter) else len(pd.read_csv(str(getter), encoding="utf-8-sig"))
    except Exception:
        return fallback


def _safe_count_csv(path: str, fallback: Any) -> Any:
    try:
        p = resolve_path(path)
        if p.exists():
            return len(pd.read_csv(str(p), encoding="utf-8-sig"))
    except Exception:
        pass
    return fallback


def _calc_boundary_ha(geojson_path: str) -> float | str:
    try:
        p = resolve_path(geojson_path)
        if p.exists():
            with p.open("r", encoding="utf-8") as f:
                geo = json.load(f)
            total_m2 = 0.0
            import pyproj
            from shapely.geometry import shape
            geod = pyproj.Geod(ellps="WGS84")
            for feat in geo.get("features", []):
                geom = shape(feat["geometry"])
                area_m2, _ = geod.geometry_area_perimeter(geom)
                total_m2 += abs(area_m2)
            if total_m2 > 0:
                return round(total_m2 / 10000.0, 1)
    except Exception:
        logger.warning("Boundary area calculation failed", exc_info=True)

    # Check custom_site.json / session_state before falling back to "~156.4"
    custom_site = _load_active_custom_site()
    if custom_site and custom_site.get("area_ha"):
        try:
            return round(float(custom_site["area_ha"]), 1)
        except (ValueError, TypeError):
            pass
    return "~156.4"


# ═══════════════════════════════════════════
# Skyline morphology
# ═══════════════════════════════════════════

@st.cache_data(ttl=3600, max_entries=20)
def get_skyline_features() -> dict[str, Any]:
    """Extract max height, avg height, high-rise ratio, building count."""
    features = {"max_height": 0, "avg_height": 0, "high_rise_ratio": 0, "building_count": 0}
    try:
        import geopandas as gpd

        buildings_path = resolve_path(str(SHP_FILES["buildings"]))
        boundary_path = resolve_path(str(SHP_FILES["boundary"]))

        buildings = gpd.read_file(str(buildings_path))

        if boundary_path.exists():
            boundary = gpd.read_file(str(boundary_path))
            filtered = _filter_buildings_within_boundary(buildings, boundary)
            if not filtered.empty:
                buildings = filtered

        # Support Floor, levels, building:levels, and height/Height columns
        height_series = pd.Series(np.nan, index=buildings.index, dtype=float)
        if "Floor" in buildings.columns:
            height_series = height_series.fillna(pd.to_numeric(buildings["Floor"], errors="coerce") * 3.5)
        if "levels" in buildings.columns:
            height_series = height_series.fillna(pd.to_numeric(buildings["levels"], errors="coerce") * 3.5)
        if "building:levels" in buildings.columns:
            height_series = height_series.fillna(pd.to_numeric(buildings["building:levels"], errors="coerce") * 3.5)
        if "height" in buildings.columns:
            height_series = height_series.fillna(pd.to_numeric(buildings["height"], errors="coerce"))
        if "Height" in buildings.columns:
            height_series = height_series.fillna(pd.to_numeric(buildings["Height"], errors="coerce"))

        buildings["Height"] = height_series.fillna(3.5)

        if not buildings.empty:
            features["building_count"] = len(buildings)
            features["max_height"] = round(float(buildings["Height"].max()), 1)
            features["avg_height"] = round(float(buildings["Height"].mean()), 1)
            high_rise = buildings[buildings["Height"] >= 24]
            features["high_rise_ratio"] = round(len(high_rise) / len(buildings) * 100, 1)
    except Exception:
        logger.warning("Skyline feature extraction failed", exc_info=True)
    return features


def _filter_buildings_within_boundary(buildings: Any, boundary: Any) -> Any:
    """Filter buildings by centroid within boundary using a projected CRS."""
    if buildings.empty or boundary.empty:
        return buildings.iloc[0:0].copy()

    buildings = _ensure_crs(buildings)
    boundary = _ensure_crs(boundary)
    if boundary.crs != buildings.crs:
        boundary = boundary.to_crs(buildings.crs)

    buildings_projected, boundary_projected = _project_for_geometry_ops(buildings, boundary)
    boundary_union = (
        boundary_projected.geometry.union_all()
        if hasattr(boundary_projected.geometry, "union_all")
        else boundary_projected.geometry.unary_union
    )
    centroid_mask = buildings_projected.geometry.centroid.within(boundary_union)
    return buildings.loc[centroid_mask].copy()


def _ensure_crs(gdf, default_crs: str = "EPSG:4326"):
    if gdf.crs is None:
        return gdf.set_crs(default_crs, allow_override=True)
    return gdf


def _normalize_to_wgs84(gdf):
    """Ensure GeoDataFrame uses WGS-84 with longitude-first axis order."""
    if gdf.empty:
        return gdf
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326", allow_override=True)
    try:
        epsg = gdf.crs.to_epsg()
    except Exception:
        epsg = None
    if epsg is not None and epsg != 4326:
        try:
            gdf = gdf.to_crs("EPSG:4326")
        except Exception:
            logger.warning("CRS reprojection to EPSG:4326 failed, keeping original CRS")
    return gdf


def _project_for_geometry_ops(buildings, boundary):
    try:
        target_crs = boundary.estimate_utm_crs() or buildings.estimate_utm_crs()
    except Exception:
        target_crs = None

    if target_crs is None and buildings.crs and buildings.crs.is_geographic:
        target_crs = "EPSG:3857"

    if target_crs is None:
        return buildings, boundary
    return buildings.to_crs(target_crs), boundary.to_crs(target_crs)


# ═══════════════════════════════════════════
# Spatial GVI point data
# ═══════════════════════════════════════════

@st.cache_data(ttl=3600, max_entries=20)
def get_spatial_data() -> pd.DataFrame:
    """Merge base spatial points with GVI analysis results."""
    base_path = resolve_path(str(DATA_FILES["points"]))
    gvi_path = resolve_path(str(DATA_FILES["gvi"]))

    try:
        df_base = pd.read_excel(str(base_path))
        df_gvi = pd.read_csv(str(gvi_path))
        if "Folder" in df_gvi.columns:
            df_gvi["ID"] = df_gvi["Folder"].str.replace("Point_", "").astype(int)
            df_gvi = df_gvi.groupby("ID").mean(numeric_only=True).reset_index()
        df = pd.merge(df_base, df_gvi, on="ID", how="inner")
    except Exception:
        logger.warning("Spatial data files missing, using demo data", exc_info=True)
        df = _generate_demo_spatial_data()

    if "GVI" not in df.columns:
        df["GVI"] = 0
    df = df.dropna(subset=["Lng", "Lat"])

    min_v, max_v = df["GVI"].min(), df["GVI"].max()
    if min_v == max_v:
        max_v = min_v + 1

    n_arr = (df["GVI"].values - min_v) / (max_v - min_v)
    r = (255 * (1 - n_arr)).astype(int)
    g = (200 * np.sin(n_arr * np.pi)).astype(int)
    b = (255 * n_arr).astype(int)
    a = np.full_like(r, 255)
    df["Dynamic_Color"] = list(np.column_stack([r, g, b, a]).tolist())
    return df


# ═══════════════════════════════════════════
# Road, Rail and Landuse loading
# ═══════════════════════════════════════════

@st.cache_data(ttl=3600, max_entries=20)
def get_road_network() -> "pd.DataFrame":
    """Load the clipped road network data."""
    try:
        import geopandas as gpd
        path = resolve_path(str(SHP_FILES["roads"]))
        if path.exists():
            return _normalize_to_wgs84(gpd.read_file(str(path)))
    except Exception:
        logger.warning("Failed to load road network", exc_info=True)
    return pd.DataFrame()


@st.cache_data(ttl=3600, max_entries=20)
def get_rail_network() -> "pd.DataFrame":
    """Load the clipped rail network data."""
    try:
        import geopandas as gpd
        path = resolve_path(str(SHP_FILES["rails"]))
        if path.exists():
            return _normalize_to_wgs84(gpd.read_file(str(path)))
    except Exception:
        logger.warning("Failed to load rail network", exc_info=True)
    return pd.DataFrame()


@st.cache_data(ttl=3600, max_entries=20)
def get_landuse_data() -> "pd.DataFrame":
    """Load the clipped landuse data with standardized colors."""
    try:
        import geopandas as gpd
        path = resolve_path(str(SHP_FILES["landuse"]))
        if path.exists():
            return _normalize_to_wgs84(gpd.read_file(str(path)))
    except Exception:
        logger.warning("Failed to load landuse data", exc_info=True)
    return pd.DataFrame()


def get_landuse_legend() -> list[dict]:
    """Get unique landuse types and their colors for legend display (supports both uppercase and lowercase columns)."""
    gdf = get_landuse_data()
    if gdf.empty:
        return []

    df = pd.DataFrame(gdf.drop(columns="geometry", errors="ignore"))

    type_col = "Type" if "Type" in df.columns else ("type" if "type" in df.columns else None)
    color_col = "Color" if "Color" in df.columns else ("color" if "color" in df.columns else None)
    gb_col = "GB_Code" if "GB_Code" in df.columns else ("gb_code" if "gb_code" in df.columns else None)

    if not type_col or not color_col:
        return []

    def _norm_color(c: Any) -> str:
        if isinstance(c, (list, tuple)) and len(c) >= 3:
            try:
                return "#{:02X}{:02X}{:02X}".format(int(c[0]), int(c[1]), int(c[2]))
            except Exception:
                return "#C0C0C0"
        return str(c or "#C0C0C0")

    def _infer_gb(t: Any) -> str:
        s = str(t or "").lower()
        if "居" in s or "res" in s:
            return "R"
        if "商" in s or "com" in s or "retail" in s or "office" in s:
            return "B"
        if "绿" in s or "park" in s or "grass" in s or "forest" in s or "green" in s:
            return "G"
        if "公" in s or "医" in s or "教" in s or "pub" in s or "inst" in s:
            return "A"
        if "工" in s or "ind" in s:
            return "M"
        return "U"

    legend_df = pd.DataFrame({
        "Type": df[type_col].astype(str),
        "Color": df[color_col].apply(_norm_color),
        "GB_Code": df[gb_col].astype(str) if gb_col else df[type_col].apply(_infer_gb),
    })

    legend = legend_df.drop_duplicates(subset=["Type", "Color", "GB_Code"]).sort_values("GB_Code")
    return legend.to_dict("records")


def _generate_demo_spatial_data() -> pd.DataFrame:
    """Fallback demo data when source files are absent."""
    np.random.seed(42)
    from src.config import get_site_center
    center = get_site_center()
    lngs = np.random.normal(loc=center[0], scale=0.005, size=150)
    lats = np.random.normal(loc=center[1], scale=0.005, size=150)
    return pd.DataFrame({
        "ID": range(1, 151),
        "Lng": lngs,
        "Lat": lats,
        "GVI": np.random.randint(10, 50, size=150),
    })
