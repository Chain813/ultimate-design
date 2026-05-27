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
        water.plot(ax=ax, facecolor="#F1F5F9", edgecolor="none", zorder=1)
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax, facecolor="#F8FAFC", edgecolor="#E2E8F0", linewidth=0.2, zorder=0.8)
    if roads is not None and not roads.empty:
        roads.plot(ax=ax, color="#CBD5E1", linewidth=0.8, zorder=2)

    # Railway noise buffer zone (120m buffer)
    if rails is not None and not rails.empty:
        rail_buffer = rails.geometry.buffer(120)
        gpd.GeoDataFrame(geometry=rail_buffer, crs=rails.crs).plot(ax=ax, facecolor="#FECACA", edgecolor="#EF4444", alpha=0.3, hatch="//", zorder=1.5)
        rails.plot(ax=ax, color="#7F1D1D", linewidth=1.5, zorder=2)

    # Environment problem points (low GVI, street blockages, parking chaos)
    problem_pts = [
        ("低绿视率段 (GVI < 10%)", 125.3312, 43.9056),
        ("低绿视率段 (GVI < 10%)", 125.3482, 43.9026),
        ("街角消极空间", 125.3375, 43.9075),
        ("现状停车混乱节点", 125.3432, 43.9052),
        ("人行道破损严重段", 125.3348, 43.9042),
        ("中车厂区围墙割裂点", 125.3401, 43.9079),
    ]

    for name, lon, lat in problem_pts:
        px_p, py_p = get_xy(lon, lat)
        ax.plot(px_p, py_p, marker='^', markersize=9, color='#EF4444', markeredgecolor='#FFFFFF', markeredgewidth=1.5, zorder=6)
        txt = ax.text(px_p, py_p+50, name, color='#991B1B', ha='center', va='bottom', fontsize=11, fontweight='bold', zorder=7, fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=11))
        txt.set_path_effects([path_effects.withStroke(linewidth=2, foreground='#FFFFFF')])

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("铁路噪声负面影响带", "rect_noise_zone"),
    ("环境品质瓶颈/乱点", "marker_problem"),
    ("现状城市道路", "rect_road"),
    ("现状普通建筑", "rect_building_light")
]

description_lines = [
    "1. 噪声污染：京哈铁路线和亚泰大街快速路高架段对两侧街区产生严重的声环境污染，最大噪声带向两侧扩散达 100-120 米。",
    "2. 绿化短板：通过街景图像量化分析发现，长通路及老社区内部多段街道的绿视率（GVI）低于 10%，空间界面灰色硬质感过强。",
    "3. 空间割裂：中车长客厂区大面积封闭式围墙阻断了南北人行路径，导致周边老旧住宅社区内部微循环不畅，慢行系统断档。"
]