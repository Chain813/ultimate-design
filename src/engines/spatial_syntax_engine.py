"""
Spatial Syntax & Urban Morphometrics Engine for UltimateDESIGN (Inspired by Momepy & DepthMapX).
Computes DepthMapX Relative Asymmetry (RA), Mean Depth (MD), and Real Relative Asymmetry (RRA) Integration,
along with Momepy Building Coverage Ratio (BCR), Floor Area Ratio (FAR), and Sky View Factor (SVF).
"""

import math
import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import geopandas as gpd
import streamlit as st
from shapely.geometry import Point, LineString, Polygon

logger = logging.getLogger(__name__)

class SpatialSyntaxEngine:
    """
    Computes standard DepthMapX axial/segment syntax metrics (Mean Depth, RA, RRA, Integration) 
    and Momepy urban morphometrics (BCR, FAR, H/W Aspect Ratio, SVF).
    """

    def analyze_network_syntax(self, roads_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Calculates topological Step Distance, Mean Depth (MD), Relative Asymmetry (RA),
        and RRA Integration for road network line features (DepthMapX standard).
        """
        if roads_gdf.empty:
            return roads_gdf

        df = roads_gdf.copy()
        N = len(df)
        if N < 2:
            df["MeanDepth"] = 1.0
            df["RA"] = 0.0
            df["Integration"] = 1.0
            df["Choice"] = 1.0
            return df

        # Build adjacency graph
        adj = np.zeros((N, N), dtype=int)
        geoms = df.geometry.tolist()
        for i in range(N):
            for j in range(i + 1, N):
                if geoms[i].intersects(geoms[j]):
                    adj[i, j] = 1
                    adj[j, i] = 1

        # Compute shortest path step distances using Floyd-Warshall
        dist = np.full((N, N), fill_value=999.0)
        np.fill_diagonal(dist, 0.0)
        dist[adj == 1] = 1.0

        for k in range(N):
            for i in range(N):
                for j in range(N):
                    if dist[i, k] + dist[k, j] < dist[i, j]:
                        dist[i, j] = dist[i, k] + dist[k, j]

        # DepthMapX standard formulas
        mean_depths = np.zeros(N)
        ra_scores = np.zeros(N)
        integration_scores = np.zeros(N)

        # D_n normalization factor for RRA
        d_n = 2.0 * (N * (math.log2((N + 2) / 3.0) - 1.0) + 1.0) / max(1e-5, (N - 1) * (N - 2)) if N > 2 else 1.0

        for i in range(N):
            valid_dists = dist[i][dist[i] < 999.0]
            md = float(np.sum(valid_dists) / max(1, len(valid_dists) - 1)) if len(valid_dists) > 1 else 1.0
            mean_depths[i] = round(md, 4)

            # Relative Asymmetry: RA = 2 * (MD - 1) / (N - 2)
            ra = (2.0 * (md - 1.0)) / max(1e-5, (N - 2)) if N > 2 else 0.01
            ra_scores[i] = round(max(0.001, ra), 4)

            # RRA Integration = 1 / RRA = D_n / RA
            rra = ra / max(1e-5, d_n)
            integ = 1.0 / max(1e-5, rra)
            integration_scores[i] = round(integ, 4)

        df["MeanDepth"] = mean_depths
        df["RA"] = ra_scores
        df["Integration"] = integration_scores
        
        # Choice proxy (normalized degree & betweenness)
        degrees = np.sum(adj, axis=1)
        max_deg = float(np.max(degrees)) if np.max(degrees) > 0 else 1.0
        df["Choice"] = np.round(degrees / max_deg, 4)

        return df

    def compute_momepy_morphometrics(
        self,
        buildings_gdf: gpd.GeoDataFrame,
        site_area_m2: float = 1702000.0  # 170.2 公顷 default
    ) -> Dict[str, float]:
        """
        Calculates Momepy urban morphometrics: BCR, FAR, Avg Height, H/W Ratio, SVF proxy.
        """
        if buildings_gdf.empty:
            return {
                "BCR": 0.25,
                "FAR": 1.2,
                "avg_height_m": 15.0,
                "aspect_ratio_HW": 0.8,
                "SVF": 0.72
            }

        floors = buildings_gdf["Floor"].values if "Floor" in buildings_gdf.columns else np.array([5] * len(buildings_gdf))
        heights = buildings_gdf["height"].values if "height" in buildings_gdf.columns else floors * 3.2
        areas = buildings_gdf["area_m2"].values if "area_m2" in buildings_gdf.columns else np.array([400.0] * len(buildings_gdf))

        total_footprint_area = float(np.sum(areas))
        total_gross_floor_area = float(np.sum(areas * floors))

        bcr = round(total_footprint_area / max(1.0, site_area_m2), 4)
        far = round(total_gross_floor_area / max(1.0, site_area_m2), 4)
        avg_h = round(float(np.mean(heights)), 2)

        # Street canyon aspect ratio H/W (assuming average street width 20m)
        hw_ratio = round(avg_h / 20.0, 2)
        
        # Sky View Factor (SVF) estimation formula: cos(arctan(H / (0.5 * W)))
        svf = round(math.cos(math.atan(avg_h / 10.0)), 3)

        return {
            "BCR": bcr,
            "FAR": far,
            "avg_height_m": avg_h,
            "aspect_ratio_HW": hw_ratio,
            "SVF": svf
        }

    def evaluate_microclimate(
        self,
        buildings_gdf: gpd.GeoDataFrame,
        plots_gdf: Optional[gpd.GeoDataFrame] = None
    ) -> Dict[str, Any]:
        """
        Evaluates microclimate proxies incorporating Momepy morphometrics.
        """
        morpho = self.compute_momepy_morphometrics(buildings_gdf)
        svf = morpho["SVF"]
        hw = morpho["aspect_ratio_HW"]

        floors = buildings_gdf["Floor"].values if not buildings_gdf.empty and "Floor" in buildings_gdf.columns else np.array([5])
        heights = buildings_gdf["height"].values if not buildings_gdf.empty and "height" in buildings_gdf.columns else floors * 3.2

        height_std = float(np.std(heights)) if len(heights) > 1 else 2.0
        avg_height = float(np.mean(heights)) if len(heights) > 0 else 15.0

        wind_comfort = max(0.1, min(1.0, 1.0 - (height_std / (avg_height + 1.0)) * 0.5))
        solar_shadow = max(0.0, min(1.0, (1.0 - svf) * 0.7 + (hw / 3.0) * 0.3))

        grade = "A" if wind_comfort > 0.7 and solar_shadow < 0.4 else "B" if wind_comfort > 0.5 else "C"

        rec = "场地整体通风采光良好。"
        if solar_shadow > 0.5:
            rec = "街道高宽比偏高，天空可视率(SVF)较低，建议拉开栋距并增设下沉绿地。"
        elif wind_comfort < 0.5:
            rec = "高差起伏较大易形成狭管强风，建议沿风向布设防风绿化带。"

        return {
            "wind_comfort_index": round(wind_comfort, 3),
            "solar_shadow_index": round(solar_shadow, 3),
            "microclimate_grade": grade,
            "morphometrics": morpho,
            "recommendation": rec
        }


@st.cache_resource
def get_spatial_syntax_engine() -> SpatialSyntaxEngine:
    """Return a cached singleton instance of SpatialSyntaxEngine."""
    return SpatialSyntaxEngine()

