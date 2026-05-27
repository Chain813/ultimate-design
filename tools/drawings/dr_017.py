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
        buildings_copy = buildings.copy()
        buildings_copy["Floor_num"] = pd.to_numeric(buildings_copy["Floor"], errors="coerce").fillna(1)
        conditions = [
            (buildings_copy["Floor_num"] <= 3),
            (buildings_copy["Floor_num"] >= 4) & (buildings_copy["Floor_num"] <= 7),
            (buildings_copy["Floor_num"] >= 8) & (buildings_copy["Floor_num"] <= 14),
            (buildings_copy["Floor_num"] >= 15) & (buildings_copy["Floor_num"] <= 20),
            (buildings_copy["Floor_num"] >= 21)
        ]
        choices = [
            "#FDE68A", # 1-3层: 黄
            "#F97316", # 4-7层: 橙
            "#EF4444", # 8-14层: 红
            "#B91C1C", # 15-20层: 深红
            "#7F1D1D"  # 21+层: 褐红
        ]
        buildings_copy["color"] = np.select(conditions, choices, default="#FDE68A")
        buildings_copy.plot(ax=ax, color=buildings_copy["color"], edgecolor="#475569", linewidth=0.15, zorder=2)
    if roads is not None and not roads.empty:
        roads.plot(ax=ax, color="#CBD5E1", linewidth=0.8, zorder=3)
    if rails is not None and not rails.empty:
        rails.plot(ax=ax, color="#64748B", linewidth=1.0, linestyle=(0, (5, 5)), zorder=4)

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("低层建筑 (1-3 层)", "rect_h1"),
    ("多层建筑 (4-7 层)", "rect_h2"),
    ("中高层建筑 (8-14 层)", "rect_h3"),
    ("高层建筑 (15-20 层)", "rect_h4"),
    ("超高层建筑 (21层以上)", "rect_h5"),
    ("城市水系", "rect_water"),
    ("城市道路", "rect_road"),
]

description_lines = [
    "1. 高度特征：区内建筑以低层（1-3层）和多层（4-7层）为主，集中分布在历史街区内部和老旧社区，空间肌理紧凑，尺度宜人。",
    "2. 高层分布：中高层与高层住宅主要零散分布在区位外围，对历史街区核心区及伪满皇宫周边产生了一定的视线廊道压力。",
    "3. 管控思路：规划提出结合视线敏感度分析，严格控制核心区新建建筑高度，禁止插建高层，保留历史空间原有的舒缓天际线。"
]