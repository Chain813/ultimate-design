# -*- coding: utf-8 -*-
from shapely.geometry import Point
import pandas as pd
import numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"
GIS_DIR = ROOT / "data/gis"
ASSETS_DIR = ROOT / "assets"

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patheffects as path_effects
import geopandas as gpd
from PIL import Image

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    px_palace, py_palace = get_xy(125.3422, 43.9036)
    if water is not None and not water.empty:
        water.plot(ax=ax, facecolor="#F1F5F9", edgecolor="none", zorder=1.2)
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax, facecolor="#FFFFFF", edgecolor="#E2E8F0", linewidth=0.2, zorder=0.8)
    if roads is not None and not roads.empty:
        roads.plot(ax=ax, color="#E2E8F0", linewidth=0.6, zorder=1)

    # Calculate 2D Heritage Value Heatmap using numpy Gaussian decay
    grid_x, grid_y = np.mgrid[cx-view_w/2:cx+view_w/2:120j, cy-view_h/2:cy+view_h/2:120j]
    grid_z = np.zeros_like(grid_x)

    centers = [(px_palace, py_palace, 1.2)]
    prot_path = STATIC_DIR / "protected_buildings.geojson"
    if prot_path.exists():
        try:
            prot_gdfs = gpd.read_file(prot_path).to_crs(epsg=3857)
            for _, row in prot_gdfs.iterrows():
                centers.append((row.geometry.centroid.x, row.geometry.centroid.y, 0.6))
        except Exception:
            pass

    for cx_p, cy_p, w in centers:
        dist_sq = (grid_x - cx_p)**2 + (grid_y - cy_p)**2
        grid_z += w * np.exp(-dist_sq / (2 * 350**2)) # Decay radius: 350m

    # Draw contours
    ax.contourf(grid_x, grid_y, grid_z, levels=14, cmap='YlOrRd', alpha=0.55, zorder=1.5)

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("核心遗产价值最高点", "rect_heatmap_high"),
    ("风貌过渡控制价值中", "rect_heatmap_med"),
    ("外围本底遗产价值低", "rect_heatmap_low"),
    ("现状普通建筑", "rect_building_light")
]

description_lines = [
    "1. 价值核心：热力图呈现出显著的“一核两带”格局，以伪满皇宫博物院近代历史保护群为绝对的遗产价值红区核心。",
    "2. 工业遗存：东北侧中车长客旧厂房及历史铁轨展示线构成了次一级的工业遗产文化脉络带，具有极高的重构与活化开发潜力。",
    "3. 空间导向：价值热力衰减直接决定了开发建设的严格风貌敏感区分区，越靠近高热力值点，新建建筑的体量与材质控制越严格。"
]