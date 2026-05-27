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
    if landuse is not None and not landuse.empty:
        for color_hex, sub_df in landuse.groupby('Color'):
            sub_df.plot(ax=ax, facecolor=color_hex, edgecolor="#CBD5E1", linewidth=0.25, zorder=1)
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax, facecolor="none", edgecolor="#475569", linewidth=0.15, alpha=0.3, zorder=2)
    if water is not None and not water.empty:
        water.plot(ax=ax, facecolor="#D0E6F7", edgecolor="none", zorder=2.5)
    if roads is not None and not roads.empty:
        roads.plot(ax=ax, color="#E2E8F0", linewidth=0.8, alpha=0.8, zorder=3)
    if rails is not None and not rails.empty:
        rails.plot(ax=ax, color="#64748B", linewidth=1.0, linestyle=(0, (5, 5)), zorder=4)

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("居住用地 (R)", "rect_euluc_0"),
    ("商业办公 (B)", "rect_euluc_1"),
    ("商业服务业 (B)", "rect_euluc_2"),
    ("工业用地 (M)", "rect_euluc_3"),
    ("交通场站 (S)", "rect_euluc_4"),
    ("机场设施 (S)", "rect_euluc_5"),
    ("行政办公 (A)", "rect_euluc_6"),
    ("教育科研 (A)", "rect_euluc_7"),
    ("医疗卫生 (A)", "rect_euluc_8"),
    ("体育文化 (A)", "rect_euluc_9"),
    ("公园与绿地 (G)", "rect_euluc_10")
]

description_lines = [
    "1. 用地构成：项目区内以居住用地（R）和商业服务业设施用地（B）为主，主要分布在亚泰大街及长通路两侧。工业与仓储用地占比较低且多属需更新工业遗存。",
    "2. 混合利用：规划提倡在轨道站点及重点更新地段发展商住混合、文创混合等多功能混合用地（M），以提升地块经济与社会活力。",
    "3. 用地优化：通过盘活现状低效建设用地，增加公共服务设施用地（A） and 绿地与广场用地（G），改善居民 15 分钟生活圈的公共服务供给与空间品质。"
]