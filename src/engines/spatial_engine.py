"""Spatial data engine: POI fusion, HUD statistics, skyline & street-view metrics.

Usage:
    from src.engines.spatial_engine import (
        get_merged_poi_data, get_hud_statistics,
        get_skyline_features, get_spatial_data,
    )
"""

import json
import logging

import numpy as np
import pandas as pd
import streamlit as st

from src.config import resolve_path, SHP_FILES, DATA_FILES

logger = logging.getLogger("ultimateDESIGN")


# ═══════════════════════════════════════════
# POI dual-source fusion
# ═══════════════════════════════════════════

@st.cache_data(ttl=3600)
def get_merged_poi_data(usecols=None) -> pd.DataFrame:
    """Merge two POI sources and de-duplicate by rounded lat/lng + name."""
    df1 = _safe_read_csv("data/Changchun_POI_Real.csv", usecols=usecols)
    # Changchun_POI_Baidu_New.csv may not exist in all deployments; treat as optional.
    df2 = _safe_read_csv("data/Changchun_POI_Baidu_New.csv", usecols=usecols)

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


def _safe_read_csv(path: str, usecols=None) -> pd.DataFrame:
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
def get_hud_statistics() -> dict:
    """Aggregate live statistics for the HUD overlay."""
    stats: dict = {}
    stats["poi_count"] = _safe_count(get_merged_poi_data, "N/A")
    stats["nlp_count"] = _safe_count_csv(str(DATA_FILES["nlp"]), "N/A")
    stats["gvi_count"] = _safe_count_csv(str(DATA_FILES["gvi"]), "N/A")
    stats["boundary_ha"] = _calc_boundary_ha("data/shp/Boundary_Scope.geojson")
    return stats


def _safe_count(getter, fallback):
    try:
        return len(getter()) if callable(getter) else len(pd.read_csv(str(getter), encoding="utf-8-sig"))
    except Exception:
        return fallback


def _safe_count_csv(path: str, fallback):
    try:
        p = resolve_path(path)
        if p.exists():
            return len(pd.read_csv(str(p), encoding="utf-8-sig"))
    except Exception:
        pass
    return fallback


def _calc_boundary_ha(geojson_path: str):
    try:
        p = resolve_path(geojson_path)
        with p.open("r", encoding="utf-8") as f:
            geo = json.load(f)
        total = 0.0
        for feat in geo.get("features", []):
            coords = np.array(feat["geometry"]["coordinates"][0])
            # Vectorized shoelace formula
            x, y = coords[:, 0], coords[:, 1]
            area_deg = abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / 2
            total += area_deg * 80 * 111 * 100
        return round(total, 1)
    except Exception:
        logger.warning("Boundary area calculation failed", exc_info=True)
        return "~156.4"


# ═══════════════════════════════════════════
# Skyline morphology
# ═══════════════════════════════════════════

@st.cache_data(ttl=3600)
def get_skyline_features() -> dict:
    """Extract max height, avg height, high-rise ratio, building count."""
    features = {"max_height": 0, "avg_height": 0, "high_rise_ratio": 0, "building_count": 0}
    try:
        import geopandas as gpd

        buildings_path = resolve_path(str(SHP_FILES["buildings"]))
        boundary_path = resolve_path(str(SHP_FILES["boundary"]))

        buildings = gpd.read_file(str(buildings_path))

        if boundary_path.exists():
            boundary = gpd.read_file(str(boundary_path))
            buildings = _filter_buildings_within_boundary(buildings, boundary)

        if "Floor" in buildings.columns:
            buildings["Height"] = pd.to_numeric(buildings["Floor"], errors="coerce").fillna(1) * 3.5
        elif "levels" in buildings.columns:
            buildings["Height"] = pd.to_numeric(buildings["levels"], errors="coerce").fillna(1) * 3.5
        else:
            buildings["Height"] = 3.5

        if not buildings.empty:
            features["building_count"] = int(len(buildings))
            features["max_height"] = round(float(buildings["Height"].max()), 1)
            features["avg_height"] = round(float(buildings["Height"].mean()), 1)
            high_rise = buildings[buildings["Height"] >= 24]
            features["high_rise_ratio"] = round(len(high_rise) / len(buildings) * 100, 1)
    except Exception:
        logger.warning("Skyline feature extraction failed", exc_info=True)
    return features


def _filter_buildings_within_boundary(buildings, boundary):
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

@st.cache_data(ttl=3600)
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

    # Vectorized gradient computation — avoids per-row Python function call
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

@st.cache_data(ttl=3600)
def get_road_network() -> gpd.GeoDataFrame:
    """Load the clipped road network data."""
    try:
        import geopandas as gpd
        path = resolve_path(str(SHP_FILES["roads"]))
        if path.exists():
            return gpd.read_file(str(path))
    except Exception:
        logger.warning("Failed to load road network", exc_info=True)
    return gpd.GeoDataFrame()

@st.cache_data(ttl=3600)
def get_rail_network() -> gpd.GeoDataFrame:
    """Load the clipped rail network data."""
    try:
        import geopandas as gpd
        path = resolve_path(str(SHP_FILES["rails"]))
        if path.exists():
            return gpd.read_file(str(path))
    except Exception:
        logger.warning("Failed to load rail network", exc_info=True)
    return gpd.GeoDataFrame()

@st.cache_data(ttl=3600)
def get_landuse_data() -> gpd.GeoDataFrame:
    """Load the clipped landuse data with standardized colors."""
    try:
        import geopandas as gpd
        path = resolve_path(str(SHP_FILES["landuse"]))
        if path.exists():
            return gpd.read_file(str(path))
    except Exception:
        logger.warning("Failed to load landuse data", exc_info=True)
    return gpd.GeoDataFrame()

def get_landuse_legend() -> list[dict]:
    """Get unique landuse types and their colors for legend display."""
    gdf = get_landuse_data()
    if gdf.empty or "Type" not in gdf.columns or "Color" not in gdf.columns:
        return []
    
    # Drop duplicates to get unique type-color pairs
    legend = gdf[["Type", "Color", "GB_Code"]].drop_duplicates().sort_values("GB_Code")
    return legend.to_dict("records")


def _generate_demo_spatial_data() -> pd.DataFrame:
    """Fallback demo data when source files are absent."""
    np.random.seed(42)
    lngs = np.random.normal(loc=125.3517, scale=0.005, size=150)
    lats = np.random.normal(loc=43.9116, scale=0.005, size=150)
    return pd.DataFrame({
        "ID": range(1, 151),
        "Lng": lngs,
        "Lat": lats,
        "GVI": np.random.randint(10, 50, size=150),
    })
