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
        water.plot(ax=ax, facecolor="#D0E6F7", edgecolor="none", zorder=1.5)
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax, facecolor="none", edgecolor="#475569", linewidth=0.15, alpha=0.3, zorder=1)
    if roads is not None and not roads.empty:
        for lvl, lw, color in [(1, 4.5, "#1E3A8A"), (2, 3.5, "#2563EB"), (3, 2.0, "#60A5FA"), (4, 1.2, "#93C5FD")]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax, color=color, linewidth=lw, capstyle="round", joinstyle="round", zorder=3)
        for lvl, lw, color in [(1, 3.0, "#3B82F6"), (2, 2.2, "#60A5FA"), (3, 1.0, "#EFF6FF"), (4, 0.6, "#FFFFFF")]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax, color=color, linewidth=lw, capstyle="round", joinstyle="round", zorder=4)
    if rails is not None and not rails.empty:
        rails.plot(ax=ax, color="#1E293B", linewidth=1.8, linestyle=(0, (5, 5)), zorder=5)

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("城市主干路", "line_primary_road_blue"),
    ("城市次干路", "line_secondary_road_blue"),
    ("城市支路", "line_tertiary_road_blue"),
    ("现状铁路线", "line_rail"),
    ("现状建筑轮廓", "rect_building_outline"),
]

description_lines = [
    "1. 骨架路网：规划区内以亚泰大街快速路和长通路、凯旋路为主干路网，南北向贯穿良好，但高架道路对两侧街区存在一定的物理与视线割裂作用。",
    "2. 铁路线路：北部京哈铁路横穿，对地块形成严重的南北向交通阻隔。规划建议在更新改造中，增设跨铁人行天桥或地下通道以缝合城市南北片区。",
    "3. 慢行慢游：现状支路网密度偏低且不成系统，慢行体验较差。规划提出通过微循环道路改造和TOD联动，构建高品质、步行友好的慢游交通环线。"
]