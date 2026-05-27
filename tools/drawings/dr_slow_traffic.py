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
        water.plot(ax=ax, facecolor="#E2F0FD", edgecolor="none", zorder=1)
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax, facecolor="#F8FAFC", edgecolor="#E2E8F0", linewidth=0.15, zorder=0.8)
    if roads is not None and not roads.empty:
        roads.plot(ax=ax, color="#CBD5E1", linewidth=0.8, capstyle="round", joinstyle="round", zorder=2)

    # Draw three types of pedestrian/cycling paths
    # 1. Tourist heritage path: Station -> Palace -> Industry Heritage (Red thick line)
    t_path_pts = [
        (125.3250, 43.9080), # Station
        (125.3340, 43.9060), 
        (125.3422, 43.9036), # Palace
        (125.3470, 43.9010),
        (125.3580, 43.9010)  # Yitong river
    ]
    from shapely.geometry import LineString
    t_line_geom = LineString([get_xy(lon, lat) for lon, lat in t_path_pts])
    gpd.GeoDataFrame(geometry=[t_line_geom], crs="EPSG:3857").plot(ax=ax, color="#EF4444", linewidth=4.0, capstyle="round", joinstyle="round", zorder=5)

    # 2. Daily neighborhood walk path (Orange dashed)
    d_path_pts = [
        (125.3320, 43.9000),
        (125.3340, 43.9040),
        (125.3410, 43.9080),
        (125.3460, 43.9060)
    ]
    d_line_geom = LineString([get_xy(lon, lat) for lon, lat in d_path_pts])
    gpd.GeoDataFrame(geometry=[d_line_geom], crs="EPSG:3857").plot(ax=ax, color="#F97316", linewidth=2.5, linestyle="--", capstyle="round", joinstyle="round", zorder=4.5)

    # 3. Bike lane (Green solid)
    b_path_pts = [
        (125.3280, 43.9080),
        (125.3380, 43.9080),
        (125.3480, 43.9050),
        (125.3580, 43.9040)
    ]
    b_line_geom = LineString([get_xy(lon, lat) for lon, lat in b_path_pts])
    gpd.GeoDataFrame(geometry=[b_line_geom], crs="EPSG:3857").plot(ax=ax, color="#10B981", linewidth=3.0, capstyle="round", joinstyle="round", zorder=4)

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("文旅漫游遗产步道 (Red)", "line_trail_red"),
    ("社区邻里慢行步道 (Orange)", "line_trail_orange"),
    ("城市共享骑行车道 (Green)", "line_trail_green"),
    ("现状城市道路", "rect_road")
]

description_lines = [
    "1. 漫游步道：规划长春站-伪满皇宫-中车遗产-伊通河 the 4.2 公里文旅慢行大环线（红色），串联沿线 12 处核心文旅景点。",
    "2. 绿道骑行：沿伊通河及铁路线边缘布置林荫骑行专用车道（绿色），支持共享单车与绿色健康通勤，实现人车分流安全出行。",
    "3. 邻里步行：老旧住宅区内增设“邻里漫步小径”（橙色），结合口袋公园布置健身设施，完善居民 5 分钟步行微系统。"
]