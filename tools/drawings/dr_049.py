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
    if water is not None and not water.empty:
        water.plot(ax=ax, facecolor="#D0E6F7", edgecolor="none", zorder=1)
    if roads is not None and not roads.empty:
        roads.plot(ax=ax, color="#E2E8F0", linewidth=0.8, zorder=2)

    # Draw height limit buffer overlay circles around Palace
    px_palace, py_palace = get_xy(125.3422, 43.9036)
    palace_pt = Point(px_palace, py_palace)
    # Expand buffer radius: 450m and 900m
    buf_450 = palace_pt.buffer(450)
    buf_900 = palace_pt.buffer(900)

    # Overlay circles are clipped to the study boundary
    bnd_geom = boundary.unary_union
    overlay_450 = buf_450.intersection(bnd_geom)
    overlay_900 = buf_900.intersection(bnd_geom)

    gpd.GeoDataFrame(geometry=[overlay_450], crs="EPSG:3857").plot(ax=ax, facecolor="#FCA5A5", edgecolor="#EF4444", alpha=0.25, zorder=1.5)
    gpd.GeoDataFrame(geometry=[overlay_900.difference(overlay_450)], crs="EPSG:3857").plot(ax=ax, facecolor="#FEF08A", edgecolor="#EAB308", alpha=0.20, zorder=1.4)

    # Color building footprints by height regulation inside boundary, and existing height outside
    if buildings is not None and not buildings.empty:
        buildings_copy = buildings.copy()
        # Calculate distance to Palace
        dists = buildings_copy.geometry.distance(palace_pt)
        # Check if building is inside boundary (using centroid)
        centroids = buildings_copy.geometry.centroid
        is_inside = centroids.within(bnd_geom)

        # Existing height coloring for outside buildings
        buildings_copy["Floor_num"] = pd.to_numeric(buildings_copy["Floor"], errors="coerce").fillna(1)
        exist_conds = [
            (buildings_copy["Floor_num"] <= 3),
            (buildings_copy["Floor_num"] >= 4) & (buildings_copy["Floor_num"] <= 7),
            (buildings_copy["Floor_num"] >= 8) & (buildings_copy["Floor_num"] <= 14),
            (buildings_copy["Floor_num"] >= 15) & (buildings_copy["Floor_num"] <= 20),
            (buildings_copy["Floor_num"] >= 21)
        ]
        exist_choices = [
            "#FDE68A", # 1-3层: 黄
            "#F97316", # 4-7层: 橙
            "#EF4444", # 8-14层: 红
            "#B91C1C", # 15-20层: 深红
            "#7F1D1D"  # 21+层: 褐红
        ]
        exist_color = np.select(exist_conds, exist_choices, default="#FDE68A")

        # Control height coloring for inside buildings
        control_conds = [
            (dists <= 450),
            (dists > 450) & (dists <= 900),
            (dists > 900)
        ]
        control_choices = [
            "#EF4444", # 限高 9m (红)
            "#EAB308", # 限高 18m (黄)
            "#3B82F6"  # 限高 24m (蓝)
        ]
        control_color = np.select(control_conds, control_choices, default="#3B82F6")

        # Combine based on whether they are inside study boundary
        buildings_copy["color"] = np.where(is_inside, control_color, exist_color)
        buildings_copy.plot(ax=ax, color=buildings_copy["color"], edgecolor="#1E293B", linewidth=0.2, zorder=2.2)

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("核心视线保护区 (≤9m)", "rect_height_red"),
    ("风貌过渡协调区 (≤18m)", "rect_height_yellow"),
    ("外围活力开发区 (≤24m)", "rect_height_blue")
]

description_lines = [
    "1. 核心高度：伪满皇宫博物院周边 300 米绝对控制区内，新建建筑限高 9 米（对应红色区），保持原有舒缓平滑的空间天际线。",
    "2. 风貌协调：300-600 米风貌过渡区内，限高 18 米（黄色区），新建建筑宜为 4-5 层，以多层及连续坡屋顶形式为主。",
    "3. 活力开发：600 米以外 of 城市外围及亚泰大街沿线，限高 24 米（蓝色区），支持局部地块进行适当的高效率活力功能开发。"
]