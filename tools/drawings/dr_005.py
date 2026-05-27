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
        buildings.plot(ax=ax, facecolor="#F1F5F9", edgecolor="#CBD5E1", linewidth=0.2, zorder=1)
    if roads is not None and not roads.empty:
        roads.plot(ax=ax, color="#E2E8F0", linewidth=0.8, zorder=2)
    if rails is not None and not rails.empty:
        rails.plot(ax=ax, color="#94A3B8", linewidth=1.0, linestyle=(0, (5, 5)), zorder=3)
    if key_plots is not None and not key_plots.empty:
        key_plots.plot(ax=ax, facecolor="#DBEAFE", edgecolor="#2563EB", linewidth=1.8, alpha=0.7, zorder=4)
        for idx, row in key_plots.iterrows():
            geom = row.geometry
            cx_kp = geom.centroid.x
            cy_kp = geom.centroid.y
            name_kp = row.get("name", f"地块 {idx+1}")
            txt = ax.text(cx_kp, cy_kp, name_kp, color='#1E40AF', ha='center', va='center', fontsize=12, fontweight='bold', zorder=5, fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=12))
            txt.set_path_effects([path_effects.withStroke(linewidth=2, foreground='#FFFFFF')])

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("五大重点更新地块", "rect_blue_fill"),
    ("现状建筑", "rect_building"),
    ("城市道路", "rect_road"),
    ("伊通河水系", "rect_water"),
]

description_lines = [
    "1. 核心范围：规划确定的更新改造研究边界西起亚泰大街，东至伊通河，南至长通路，北至京哈铁路，总用地面积约为 150 公顷。",
    "2. 重点地块：规划重点针对片区内 5 个低效国有或集体资产地块进行城市设计与活力针灸，包括老水产批发市场 and 中车旧厂区等。",
    "3. 现状本底：周边路网成熟，紧邻长春站交通门户，是缝合老宽城铁北地区与长春历史文化中轴线的空间关键锁扣。"
]