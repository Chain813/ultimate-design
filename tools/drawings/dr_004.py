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
    # Default: 现状区位图 (Location Map)
    if water is not None and not water.empty:
        water.plot(ax=ax, facecolor="#D0E6F7", edgecolor="none", zorder=1)
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax, facecolor="#FFFFFF", edgecolor="#E5E5E7", linewidth=0.35, zorder=2)
    if roads is not None and not roads.empty:
        for lvl, lw in [(1, 3.8), (2, 3.0), (3, 2.2), (4, 1.6)]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax, color="#C7C7CC", linewidth=lw, capstyle="round", joinstyle="round", zorder=3)
        for lvl, lw in [(1, 2.6), (2, 2.0), (3, 1.2), (4, 0.8)]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax, color="#E5E5EA", linewidth=lw, capstyle="round", joinstyle="round", zorder=4)
    if rails is not None and not rails.empty:
        rails.plot(ax=ax, color="#48484A", linewidth=1.5, linestyle=(0, (5, 5)), zorder=5)

# Default: 现状区位图 (Location Map)
legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("重点更新地块", "rect_orange_border"),
    ("现状建筑", "rect_building"),
    ("城市水系 (伊通河等)", "rect_water"),
    ("现状铁路 (京哈线等)", "line_rail"),
    ("城市道路", "rect_road")
]

# 现状区位图 (Location Map)
description_lines = [
    "1. 地理区位：本项目位于吉林省长春市宽城区历史文化核心街区，紧邻长春火车站与伪满皇宫博物院，是连接历史风貌区与现代城市中心的关键枢纽地带。",
    "2. 规划范围：规划研究范围东至伊通河、西至亚泰大街、南至长通路、北至京哈铁路，总规划研究面积约150公顷。包含5大重点更新地块。",
    "3. 指标现状：核心区现状路网密度6.2km/km²，建筑密度42%，水绿覆盖率约12.4%。规划定位为“数字孪生·古今共振”的历史风貌与双创活力街区。"
]