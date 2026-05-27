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
        buildings.plot(ax=ax, facecolor="#F1F5F9", edgecolor="#E2E8F0", linewidth=0.2, zorder=1)
    prot_path = STATIC_DIR / "protected_buildings.geojson"
    if prot_path.exists():
        try:
            protected = gpd.read_file(prot_path).to_crs(epsg=3857)
            protected.plot(ax=ax, facecolor="#D97706", edgecolor="#B45309", linewidth=0.5, alpha=0.9, zorder=2.2)
        except Exception as e:
            print(f"Error loading protected buildings: {e}")
    if roads is not None and not roads.empty:
        roads.plot(ax=ax, color="#CBD5E1", linewidth=0.8, zorder=3)
    if rails is not None and not rails.empty:
        rails.plot(ax=ax, color="#64748B", linewidth=1.0, linestyle=(0, (5, 5)), zorder=4)

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("重点历史/工业遗产建筑", "rect_heritage"),
    ("现状普通建筑", "rect_building_light"),
    ("城市水系", "rect_water"),
    ("城市道路", "rect_road"),
    ("现状铁路线", "line_rail")
]

description_lines = [
    "1. 遗产识别：片区内包含以伪满皇宫为核心的近代历史建筑群，以及东北侧中车长客厂区的大跨度工业厂房和铁轨遗存，是复合型城市遗产的关键载体。",
    "2. 价值评估：历史风貌核心保护区与中车厂区具有极高的建筑质量和空间识别度，是本次更新设计中严格执行“保留与修缮”的刚性管控区域。",
    "3. 活化思路：保护传统街区肌理与风貌界面的连续性，打通历史文化展示游线，将工业遗存置换为文创、博览和青年双创等活力复合功能。"
]