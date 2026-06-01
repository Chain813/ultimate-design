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

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop, params=None):
    px_palace, py_palace = get_xy(125.3422, 43.9036)
    px_station, py_station = get_xy(125.3250, 43.9080)
    px_river, py_river = get_xy(125.3590, 43.9010)
    if water is not None and not water.empty:
        water.plot(ax=ax, facecolor="#E6F2FC", edgecolor="none", zorder=1)
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax, facecolor="#F1F5F9", edgecolor="#94A3B8", linewidth=0.35, zorder=0.8)
    if roads is not None and not roads.empty:
        roads.plot(ax=ax, color="#94A3B8", linewidth=1.1, zorder=2)

    # 1. Plot Core (Palace)
    ax.plot(px_palace, py_palace, marker='*', markersize=26, color='#F59E0B', markeredgecolor='#FFFFFF', markeredgewidth=2.5, zorder=9)
    txt = ax.text(px_palace, py_palace + 110, "历史文化共振核心", color='#B45309', ha='center', va='bottom', fontsize=18, fontweight='bold', zorder=10, fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=18))
    txt.set_path_effects([path_effects.withStroke(linewidth=3, foreground='#FFFFFF')])

    # 2. Plot Axes
    # Station-Palace Linkage Axis
    ax.annotate("", xy=(px_palace, py_palace), xytext=(px_station, py_station),
                arrowprops=dict(arrowstyle="->", color="#F97316", lw=5.5, alpha=0.8, ls="-"), zorder=8)
    ax.text((px_palace + px_station)/2, (py_palace + py_station)/2 + 50, "站城文脉联动主轴", color='#C2410C', ha='center', va='bottom', fontsize=14, fontweight='bold', zorder=9, rotation=10, fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=14))

    # Waterfront Ecology Axis
    ax.annotate("", xy=(px_river, py_river), xytext=(px_palace, py_palace),
                arrowprops=dict(arrowstyle="->", color="#06B6D4", lw=4.5, alpha=0.8, ls="--"), zorder=8)
    ax.text((px_palace + px_river)/2, (py_palace + py_river)/2 + 50, "生态文旅向心带", color='#0891B2', ha='center', va='bottom', fontsize=12, fontweight='bold', zorder=9, rotation=-5, fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=12))

    # 3. Yitong river ecological belt highlight
    if water is not None and not water.empty:
        water.plot(ax=ax, facecolor="#A5F3FC", edgecolor="#0891B2", linewidth=2.0, alpha=0.7, zorder=1.5)

    # 4. Highlight key plots as red/orange nodes
    if key_plots is not None and not key_plots.empty:
        key_plots.geometry.centroid.plot(ax=ax, marker='o', markersize=200, color='none', edgecolor='#EF4444', linewidth=2.0, zorder=7.5)
        key_plots.geometry.centroid.plot(ax=ax, marker='o', markersize=50, color='#EF4444', zorder=7.6)
        for idx, row in key_plots.iterrows():
            geom = row.geometry
            ax.text(geom.centroid.x, geom.centroid.y - 80, f"活力节点 {idx+1}", color='#B91C1C', ha='center', va='top', fontsize=11, fontweight='bold', zorder=9, fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=11))

    # 5. LLM-guided annotations and highlights
    if params:
        for ann in params.get("annotations", []):
            try:
                ax_x, ax_y = get_xy(ann["x"], ann["y"])
                txt = ax.text(ax_x, ax_y, ann["text"], color=ann.get("color", "#333333"),
                             ha='center', va='bottom', fontsize=ann.get("fontsize", 9),
                             fontweight='bold', zorder=11,
                             fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=ann.get("fontsize", 9)))
                txt.set_path_effects([path_effects.withStroke(linewidth=2, foreground='#FFFFFF')])
            except Exception:
                pass

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("历史文化共振核心", "star_core"),
    ("站城文脉联动主轴", "line_arrow_orange"),
    ("生态文旅向心带", "line_arrow_cyan"),
    ("更新活力触媒节点", "marker_node_red")
]

description_lines = [
    "1. 规划结构：形成“一核、双轴、五地块”的总体更新规划结构。一核指历史文化共振核，双轴为站城联动轴与生态延伸轴。",
    "2. 站城联动：打通长春站至伪满皇宫的空间轴线，利用高品质慢行商业街与视觉廊道建立两者的物理与文化强关联。",
    "3. 节点触媒：以 5 个更新活力节点为针灸触点，激活周边消极的街区本底，促进历史风貌区与现代化城市的无缝衔接。"
]