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
        water.plot(ax=ax, facecolor="#E8F4FC", edgecolor="none", zorder=1)
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax, facecolor="#F1F5F9", edgecolor="#E2E8F0", linewidth=0.2, zorder=2)
    if roads is not None and not roads.empty:
        # 1. 绘制灰色底图路网外廓 (道路底边)
        for lvl, lw, color in [(1, 5.5, "#94A3B8"), (2, 4.2, "#CBD5E1"), (3, 2.5, "#E2E8F0"), (4, 1.5, "#F1F5F9")]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax, color=color, linewidth=lw, capstyle="round", joinstyle="round", zorder=3)
        # 2. 绘制白色填充层 (道路内廓)
        for lvl, lw, color in [(1, 3.5, "#FFFFFF"), (2, 2.6, "#FFFFFF"), (3, 1.2, "#FFFFFF"), (4, 0.7, "#FFFFFF")]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax, color=color, linewidth=lw, capstyle="round", joinstyle="round", zorder=4)
        # 3. 双层描边叠画高亮规划道路：Level 1 (红色规划轴线/步行街) 与 Level 2 (橙色规划联系通道)
        sub_l1 = roads[roads['level'] == 1]
        if not sub_l1.empty:
            sub_l1.plot(ax=ax, color="#E11D48", linewidth=2.8, linestyle=(0, (6, 4)), capstyle="round", joinstyle="round", zorder=5)
        sub_l2 = roads[roads['level'] == 2]
        if not sub_l2.empty:
            sub_l2.plot(ax=ax, color="#EA580C", linewidth=2.0, linestyle=(0, (4, 3)), capstyle="round", joinstyle="round", zorder=5)
    if rails is not None and not rails.empty:
        rails.plot(ax=ax, color="#334155", linewidth=1.5, linestyle=(0, (5, 5)), zorder=5)

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("规划建议道路/步行街", "line_proposed_road"),
    ("现状城市主干路", "line_primary_road"),
    ("现状城市次干路", "line_secondary_road"),
    ("现状城市支路", "line_tertiary_road"),
    ("现状铁路", "line_rail"),
]

description_lines = [
    "1. 路网骨架：规划形成“三横三纵”的城市主次干路网骨架，提升地块对外的交通联系和连通度，实现内外交通的顺畅转换。",
    "2. 慢行慢游：加密内部支路网，优化慢行步道，提升街区可达性，建立对行人与自行车慢行友好的漫游系统，打通微循环瓶颈。",
    "3. TOD 开发：紧邻长春火车站与轨道交通站点，规划强化 TOD 交通枢纽的辐射带动作用，引导高密度、功能混合的公共交通导向型开发。"
]