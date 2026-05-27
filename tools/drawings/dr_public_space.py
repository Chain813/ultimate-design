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
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax, facecolor="#F8FAFC", edgecolor="#E2E8F0", linewidth=0.2, zorder=0.8)
    if roads is not None and not roads.empty:
        roads.plot(ax=ax, color="#CBD5E1", linewidth=0.6, zorder=2)

    # Draw public spaces and their 300m walking radius buffers
    public_spaces_pts = [
        (125.3422, 43.9036, "宫廷前广场"),
        (125.3260, 43.8960, "胜利公园"),
        (125.3590, 43.9010, "伊通河湿地公园"),
        (125.3330, 43.9070, "老社区口袋公园"),
        (125.3465, 43.8995, "文创街角广场")
    ]

    for lon, lat, name in public_spaces_pts:
        px_p, py_p = get_xy(lon, lat)
        # Plot center
        ax.plot(px_p, py_p, marker='o', markersize=14, color='#10B981', markeredgecolor='#FFFFFF', markeredgewidth=2.0, zorder=5)
        # Plot buffer
        buf_geom = Point(px_p, py_p).buffer(300)
        gpd.GeoDataFrame(geometry=[buf_geom], crs="EPSG:3857").plot(ax=ax, facecolor="#D1FAE5", edgecolor="#059669", linewidth=0.8, alpha=0.22, zorder=1.5)
        # Label
        txt = ax.text(px_p, py_p + 45, name, color='#047857', ha='center', va='bottom', fontsize=11, fontweight='bold', zorder=6, fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=11))
        txt.set_path_effects([path_effects.withStroke(linewidth=2, foreground='#FFFFFF')])

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("核心广场景观节点", "marker_node_green"),
    ("口袋公园服务半径 (300m)", "rect_green_buffer"),
    ("现状水绿开敞空间", "rect_water")
]

description_lines = [
    "1. 广场节点：在伪满皇宫前及中车厂房东侧规划两处大型文化景观广场，作为城市大型公共活动与旅游集散的复合载体。",
    "2. 口袋公园：见缝插针地在居住社区内部增设 6 处口袋公园，确保规划区实现“300 米见绿、500 米见园”的服务全覆盖。",
    "3. 服务缓冲：为每个口袋公园划定 300 米服务半径分析缓冲（绿色圈），精准织补覆盖盲区，大幅度提升整体公共绿地均等化。"
]