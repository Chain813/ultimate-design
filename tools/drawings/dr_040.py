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
        water.plot(ax=ax, facecolor="#E2F0FD", edgecolor="none", zorder=1.5)
    if roads is not None and not roads.empty:
        roads.plot(ax=ax, color="#CBD5E1", linewidth=0.8, zorder=2)
    if rails is not None and not rails.empty:
        rails.plot(ax=ax, color="#64748B", linewidth=1.0, linestyle=(0, (5, 5)), zorder=3)

    # Color building footprints by update mode
    if buildings is not None and not buildings.empty:
        buildings_copy = buildings.copy()
        # Distances to Palace
        px_palace, py_palace = get_xy(125.3422, 43.9036)
        palace_pt = Point(px_palace, py_palace)
        dists = buildings_copy.geometry.distance(palace_pt)

        conditions = [
            (buildings_copy["prop_style"] == "historical") | (dists <= 150),
            (dists > 150) & (dists <= 450),
            (buildings_copy["geometry"].centroid.x < 125.335) | (buildings_copy["geometry"].centroid.x > 125.346),
            (dists > 450)
        ]
        choices = [
            "#B45309", # 保护修缮: 历史核心 (古铜)
            "#F59E0B", # 整治提升: 过渡风貌 (橙黄)
            "#10B981", # 微更新: 老社区修补 (绿)
            "#3B82F6"  # 功能置换: 工业转型 (蓝)
        ]
        buildings_copy["color"] = np.select(conditions, choices, default="#F59E0B")
        buildings_copy.plot(ax=ax, color=buildings_copy["color"], edgecolor="#475569", linewidth=0.15, zorder=2.2)

    if key_plots is not None and not key_plots.empty:
        key_plots.plot(ax=ax, facecolor="#A855F7", edgecolor="#7E22CE", linewidth=1.5, alpha=0.8, zorder=2.5)

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("重点更新地块 (拆改建)", "rect_purple_fill"),
    ("历史保护核心 (保护修缮)", "rect_style_hist"),
    ("风貌敏感地带 (整治提升)", "rect_style_orange"),
    ("老旧住宅社区 (微更新)", "rect_style_green"),
    ("工业仓储遗存 (功能置换)", "rect_style_blue")
]

description_lines = [
    "1. 保护修缮：针对伪满皇宫等 3.2% 的历史建筑，执行原地原风貌修缮，划定绝对保护红线，禁止任何形式的加建与插建高层。",
    "2. 整治提升：对风貌过渡区的老旧公建及沿街界面，统一立面风貌导则，拆除杂乱违建，使建筑色调、材质与历史保护区协调。",
    "3. 置换与微更新：对中车低效工业厂房进行功能重组与置换，置换为青年文创；对老社区实施微改造，盘活边角地增加活动场地。"
]