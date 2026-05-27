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
        buildings.plot(ax=ax, facecolor="#F8FAFC", edgecolor="#E2E8F0", linewidth=0.2, zorder=1)
    if landuse is not None and not landuse.empty:
        green_gdf = landuse[landuse['GB_Code'] == 'G']
        other_gdf = landuse[landuse['GB_Code'] != 'G']
        if not other_gdf.empty:
            other_gdf.plot(ax=ax, facecolor="#F1F5F9", edgecolor="#E2E8F0", linewidth=0.2, zorder=0.8)
        if not green_gdf.empty:
            green_gdf.plot(ax=ax, facecolor="#A7F3D0", edgecolor="#047857", linewidth=0.5, zorder=2)
    if key_plots is not None and not key_plots.empty:
        key_plots.plot(ax=ax, facecolor="#10B981", edgecolor="#047857", linewidth=1.5, alpha=0.9, zorder=2.5)
    if roads is not None and not roads.empty:
        roads.plot(ax=ax, color="#E2E8F0", linewidth=0.8, zorder=3)
    if rails is not None and not rails.empty:
        rails.plot(ax=ax, color="#64748B", linewidth=1.0, linestyle=(0, (5, 5)), zorder=4)

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("规划新增绿地/广场", "rect_green_planned"),
    ("现状公园绿地", "rect_green"),
    ("城市水系", "rect_water"),
    ("城市道路", "rect_road"),
    ("现状建筑", "rect_building")
]

description_lines = [
    "1. 生态骨架：以东侧伊通河滨水生态廊道为生态基底，向街区内部延伸多条绿色触角，构建“一廊多点”的生态空间格局。",
    "2. 公园绿地：规划多处社区公园、口袋公园与街头绿地，确保街区内居民实现“300米见绿、500米见园”的生态生活目标。",
    "3. 蓝绿交织：整合水系边缘与道路绿化带，增加透水铺装与雨水花园，构建海绵城市雨洪管理系统，兼具景观美学与生态韧性。"
]