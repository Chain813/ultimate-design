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
        buildings.plot(ax=ax, facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=0.2, zorder=0.8)
    if roads is not None and not roads.empty:
        roads.plot(ax=ax, color="#E2E8F0", linewidth=0.8, zorder=2)

    # Color 5 key plots by phasing
    if key_plots is not None and not key_plots.empty:
        # Staging colors: Green (1-3 yrs), Blue (3-5 yrs), Purple (5-10 yrs)
        stage_colors = ["#22C55E", "#22C55E", "#A855F7", "#3B82F6", "#3B82F6"]
        for idx, row in key_plots.iterrows():
            gpd.GeoSeries([row.geometry]).plot(ax=ax, facecolor=stage_colors[idx % len(stage_colors)], edgecolor="#1E293B", linewidth=1.5, alpha=0.85, zorder=3)
            # Label
            geom = row.geometry
            txt = ax.text(geom.centroid.x, geom.centroid.y, f"阶段 {1 if idx < 2 else (3 if idx == 2 else 2)}\n({row.get('name')})", color='#FFFFFF', ha='center', va='center', fontsize=12, fontweight='bold', zorder=4, fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=12))
            txt.set_path_effects([path_effects.withStroke(linewidth=2, foreground='#1E293B')])

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("近期实施项目 (1-3年)", "rect_phase_green"),
    ("中期实施项目 (3-5年)", "rect_phase_blue"),
    ("远期实施项目 (5-10年)", "rect_phase_purple")
]

description_lines = [
    "1. 近期建设（1-3年）：优先启动水产批发市场及食品调料市场地块（绿色区），置换为社区商业与公共停车场以疏导人流。",
    "2. 中期推进（3-5年）：推进中车工业遗存活化项目（蓝色区），将旧厂房改建为数智文创街区，并缝合被铁路线阻断的路网。",
    "3. 远期展望（5-10年）：实施清禾市场及石油公司周边低效住宅微更新项目（紫色区），彻底完成全区公共绿地与设施配套。"
]