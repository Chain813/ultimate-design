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
        roads.plot(ax=ax, color="#CBD5E1", linewidth=0.8, zorder=2)

    # Draw tourist routes (red thick lines) and historic markers (gold dots)
    t_path_pts = [
        (125.324761, 43.906852),
        (125.326120, 43.906852),
        (125.331051, 43.905996),
        (125.331673, 43.905778),
        (125.331673, 43.905533),
        (125.331691, 43.905085),
        (125.332088, 43.904700),
        (125.337773, 43.904749),
        (125.340664, 43.904796),
        (125.340727, 43.904385),
        (125.340925, 43.904011),
        (125.340860, 43.903652),
        (125.340928, 43.903325),
        (125.341210, 43.902995),
        (125.341424, 43.902848),
        (125.341210, 43.902995),
        (125.340928, 43.903325),
        (125.340860, 43.903652),
        (125.340925, 43.904011),
        (125.340727, 43.904385),
        (125.343002, 43.904804),
        (125.342981, 43.904899),
        (125.346493, 43.905366),
        (125.348163, 43.905631),
        (125.350431, 43.906419),
        (125.353383, 43.906434),
        (125.352606, 43.904315),
        (125.352564, 43.903931),
        (125.352538, 43.903518),
        (125.352606, 43.903221),
        (125.352747, 43.902924),
        (125.352992, 43.902639),
        (125.353388, 43.902323),
        (125.355235, 43.901173),
        (125.355673, 43.900838),
        (125.355996, 43.900466),
        (125.356210, 43.900109)
    ]
    from shapely.geometry import LineString
    t_line_geom = LineString([get_xy(lon, lat) for lon, lat in t_path_pts])
    gpd.GeoDataFrame(geometry=[t_line_geom], crs="EPSG:3857").plot(ax=ax, color="#EF4444", linewidth=3.5, zorder=4.5)

    hist_spots = [
        ("伪满皇宫博物院", 125.3422, 43.9036),
        ("中车厂区旧址", 125.3401, 43.9079),
        ("光复路老商业街", 125.3475, 43.9017),
        ("传统风貌保护区", 125.3385, 43.9051)
    ]

    for name, lon, lat in hist_spots:
        px_p, py_p = get_xy(lon, lat)
        ax.plot(px_p, py_p, marker='o', markersize=14, color='#D97706', markeredgecolor='#FFFFFF', markeredgewidth=2.0, zorder=5.0)
        txt = ax.text(px_p, py_p + 60, name, color='#78350F', ha='center', va='bottom', fontsize=12, fontweight='bold', zorder=6.0, fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=12))
        txt.set_path_effects([path_effects.withStroke(linewidth=2.5, foreground='#FFFFFF')])

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("文化探访展示路径", "line_trail_red"),
    ("关键历史文化展示节点", "marker_node_gold"),
    ("现状普通建筑", "rect_building_light")
]

description_lines = [
    "1. 展示路径：以近代风貌核心保护区为基础，构建两条历史文脉游赏展示路径，采用统一的标识系统与导游导视指引系统。",
    "2. 遗产标示：在伪满皇宫、中车老厂房、铁路老枕木等关键节点设立金属文化浮雕碑与解说板，形成“露天博物馆”体验。",
    "3. 视廊保护：严格保护从长春火车站、亚泰大街远眺伪满皇宫的 3 条重要风貌视线走廊，走廊范围内禁止悬挂大型广告牌。"
]