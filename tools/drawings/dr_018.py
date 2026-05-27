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
        conditions = [
            (buildings_copy["prop_style"] == "historical"),
            (buildings_copy["prop_style"] == "park"),
            (buildings_copy["prop_style"] == "normal") | (buildings_copy["prop_style"].isna())
        ]
        choices = [
            "#B45309", # historical: 历史保护风貌 (古铜/褐金)
            "#0F766E", # park: 附属景观风貌 (青绿)
            "#E2E8F0"  # normal: 现代普通风貌 (浅灰)
        ]
        buildings_copy["color"] = np.select(conditions, choices, default="#E2E8F0")
        buildings_copy.plot(ax=ax, color=buildings_copy["color"], edgecolor="#475569", linewidth=0.15, zorder=2)
    if roads is not None and not roads.empty:
        roads.plot(ax=ax, color="#CBD5E1", linewidth=0.8, zorder=3)
    if rails is not None and not rails.empty:
        rails.plot(ax=ax, color="#64748B", linewidth=1.0, linestyle=(0, (5, 5)), zorder=4)

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("历史保护风貌建筑", "rect_style_hist"),
    ("公建及附属景观风貌", "rect_style_park"),
    ("普通住宅与现代风貌", "rect_style_norm"),
    ("城市水系", "rect_water"),
    ("城市道路", "rect_road"),
]

description_lines = [
    "1. 风貌构成：区内历史保护风貌占比约3.2%，集中在伪满皇宫周边；普通居住风貌占主导，整体风貌协调度有待提升。",
    "2. 界面杂乱：局部街区存在杂乱搭接及立面风貌破损，严重削弱了历史文化街区的空间质量与文化氛围，缺乏统一的导则引导。",
    "3. 整治策略：实行分类整治，对历史建筑修缮复原，对普通住宅立面进行微改造协调，消除风貌冲突，营造和谐的历史共振街区。"
]