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
    # Renders the beautiful masterplan landuse layout
    if landuse is not None and not landuse.empty:
        for color_hex, sub_df in landuse.groupby('Color'):
            sub_df.plot(ax=ax, facecolor=color_hex, edgecolor="#F1F5F9", linewidth=0.2, zorder=1)
    # Highlight green spaces and water
    if water is not None and not water.empty:
        water.plot(ax=ax, facecolor="#93C5FD", edgecolor="none", zorder=2)
    if key_plots is not None and not key_plots.empty:
        # Color key plots differently to show proposed layout (Red for commercial, Green for park, Yellow for housing)
        colors_kp = ["#FCA5A5", "#FDE047", "#A7F3D0", "#FCA5A5", "#93C5FD"]
        for idx, row in key_plots.iterrows():
            gpd.GeoSeries([row.geometry]).plot(ax=ax, facecolor=colors_kp[idx % len(colors_kp)], edgecolor="#E11D48", linewidth=1.0, zorder=2.2)

    # Proposed roads: solid white lines with dark casing
    if roads is not None and not roads.empty:
        roads.plot(ax=ax, color="#C8D4E3", linewidth=1.5, zorder=3)
        # Add proposed minor road network lines
        if key_plots is not None and not key_plots.empty:
            proposed_lines = []
            for geom in key_plots.geometry:
                if geom.is_valid and not geom.is_empty:
                    # Draw a loop pathway inside the key plot polygon (inward buffer)
                    for buf_dist in [-20, -12, -8]:
                        inner = geom.buffer(buf_dist)
                        if inner is not None and not inner.is_empty:
                            bnd = inner.boundary
                            if bnd is not None and not bnd.is_empty:
                                proposed_lines.append(bnd)
                                break
            if proposed_lines:
                proposed_gdf = gpd.GeoDataFrame(geometry=proposed_lines, crs=key_plots.crs)
                proposed_gdf.plot(ax=ax, color="#FFFFFF", linewidth=3.0, zorder=3.5)
                proposed_gdf.plot(ax=ax, color="#FF2D55", linewidth=1.2, linestyle="-", zorder=3.6)

    # Buildings: white with dark outlines
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax, facecolor="#FFFFFF", edgecolor="#1E293B", linewidth=0.25, alpha=0.9, zorder=4)

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("居住社区规划", "rect_plan_yellow"),
    ("商业文创策划", "rect_plan_red"),
    ("规划新增绿地", "rect_plan_green"),
    ("规划水系整治", "rect_plan_blue"),
    ("规划新增密集路网", "line_plan_road"),
    ("工业仓储遗存", "rect_style_blue"),
    ("行政与教育办公", "rect_euluc_6"),
    ("现状城市道路", "rect_road"),
    ("现状普通建筑", "rect_building_light")
]

description_lines = [
    "1. 规划依据：依据《长春市城市总体规划》与文物保护红线，顺应‘数字孪生·古今共振’更新策略，缝合历史城区与现代空间。",
    "2. 规划布局：商业与文创混合区沿沿线两侧布置；老旧社区内部主要进行绿化修补与微更新，维持低层低容积率的历史肌理。",
    "3. 景观骨架：构建环历史核心区的绿色开敞环线，并与东侧伊通河生态廊道绿带无缝对接，实现蓝绿网络与城市空间融合。"
]