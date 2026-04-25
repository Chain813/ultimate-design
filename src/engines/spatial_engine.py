"""Spatial data engine: POI fusion, HUD statistics, skyline & street-view metrics.

Usage:
    from src.engines.spatial_engine import (
        get_merged_poi_data, get_hud_statistics,
        get_skyline_features, get_spatial_data,
    )
"""

import json
import logging
import math
import os

import numpy as np
import pandas as pd
import streamlit as st

from src.config import resolve_path, SHP_FILES, DATA_FILES
from src.utils.exceptions import log_and_suppress

logger = logging.getLogger("ultimateDESIGN")


# ═══════════════════════════════════════════
# POI dual-source fusion
# ═══════════════════════════════════════════

@st.cache_data(ttl=600)
def get_merged_poi_data() -> pd.DataFrame:
    """Merge two POI sources and de-duplicate by rounded lat/lng + name."""
    df1 = _safe_read_csv("data/Changchun_POI_Real.csv")
    df2 = _safe_read_csv("data/Changchun_POI_Baidu_New.csv")

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


def _safe_read_csv(path: str) -> pd.DataFrame:
    try:
        resolved = resolve_path(path)
        if resolved.exists():
            return pd.read_csv(str(resolved), encoding="utf-8-sig")
    except Exception:
        logger.warning("Could not read %s", path, exc_info=True)
    return pd.DataFrame()


# ═══════════════════════════════════════════
# HUD dynamic statistics
# ═══════════════════════════════════════════

@st.cache_data(ttl=300)
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
            coords = feat["geometry"]["coordinates"][0]
            n = len(coords)
            area_deg = 0.0
            for i in range(n):
                j = (i + 1) % n
                area_deg += coords[i][0] * coords[j][1]
                area_deg -= coords[j][0] * coords[i][1]
            area_deg = abs(area_deg) / 2
            total += area_deg * 80 * 111 * 100
        return round(total, 1)
    except Exception:
        logger.warning("Boundary area calculation failed", exc_info=True)
        return "~156.4"


# ═══════════════════════════════════════════
# Skyline morphology
# ═══════════════════════════════════════════

@st.cache_data(ttl=1800)
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
            buildings = buildings[buildings.centroid.within(boundary.unary_union)]

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


# ═══════════════════════════════════════════
# Spatial GVI point data
# ═══════════════════════════════════════════

@st.cache_data(ttl=300)
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

    def _gradient(val):
        n = (val - min_v) / (max_v - min_v)
        return [int(255 * (1 - n)), int(200 * math.sin(n * math.pi)), int(255 * n), 255]

    df["Dynamic_Color"] = df["GVI"].apply(_gradient)
    return df


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
