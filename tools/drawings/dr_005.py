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
    # 1. 绘制遥感卫星底图
    sat_path = STATIC_DIR / "assets/generated_base/satellite_cropped.png"
    if sat_path.exists():
        try:
            sat_img = Image.open(sat_path)
            extent = [cx - view_w / 2, cx + view_w / 2, cy - view_h / 2, cy + view_h / 2]
            ax.imshow(sat_img, extent=extent, zorder=0)
        except Exception as e:
            print(f"Error loading satellite image: {e}")
            ax.text(cx, cy, "卫星遥感底图加载失败", ha='center', va='center', fontsize=24, color='#FF3B30', fontproperties=fm.FontProperties(family=font_prop['family']))
    else:
        ax.text(cx, cy, "卫星遥感底图未找到", ha='center', va='center', fontsize=24, color='#8E8E93', fontproperties=fm.FontProperties(family=font_prop['family']))

    # 2. 叠加半透明蓝色伊通河水系以增加可读性
    if water is not None and not water.empty:
        water.plot(ax=ax, facecolor="#0066CC", edgecolor="none", alpha=0.35, zorder=1)

    # 3. 绘制研究范围边界外的半透明掩膜遮罩（使研究范围之外白化，高亮核心研究范围内区域）
    try:
        from shapely.geometry import box
        large_box = box(cx - view_w, cy - view_h, cx + view_w, cy + view_h)
        boundary_union = boundary.geometry.union_all() if hasattr(boundary.geometry, "union_all") else boundary.geometry.unary_union
        mask_poly = large_box.difference(boundary_union)
        gpd.GeoSeries([mask_poly]).plot(ax=ax, facecolor="#FAFAFC", alpha=0.45, edgecolor="none", zorder=3)
    except Exception as e:
        print(f"Error drawing boundary mask: {e}")

    # 4. 绘制铁路线（仅在核心高亮区域内可见，且zorder高于外部遮罩）
    if rails is not None and not rails.empty:
        rails.plot(ax=ax, color="#475569", linewidth=1.2, linestyle=(0, (5, 5)), zorder=4)

    # 5. 绘制五大重点更新地块高亮范围
    if key_plots is not None and not key_plots.empty:
        # 半透明浅蓝色填充
        key_plots.plot(ax=ax, facecolor="#3B82F6", alpha=0.25, edgecolor="none", zorder=4.8)
        # 深蓝色边界线
        key_plots.plot(ax=ax, facecolor="none", edgecolor="#2563EB", linewidth=2.2, zorder=5)
        
        for idx, row in key_plots.iterrows():
            geom = row.geometry
            cx_kp = geom.centroid.x
            cy_kp = geom.centroid.y
            name_kp = row.get("name", f"地块 {idx+1}")
            txt = ax.text(cx_kp, cy_kp, name_kp, color='#1D4ED8', ha='center', va='center', 
                          fontsize=12, fontweight='bold', zorder=6, 
                          fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=12))
            txt.set_path_effects([path_effects.withStroke(linewidth=3, foreground='#FFFFFF')])

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("五大重点更新地块", "rect_blue_fill"),
    ("伊通河水系", "rect_water"),
    ("卫星遥感影像", "rect_sat_base"),
]

description_lines = [
    "1. 核心范围：规划确定的更新改造研究边界西起亚泰大街，东至伊通河，南至长通路，北至京哈铁路，总用地面积约为 150 公顷。",
    "2. 重点地块：规划重点针对片区内 5 个低效国有或集体资产地块进行城市设计与活力针灸，包括老水产批发市场和中车旧厂区等。",
    "3. 现状本底：周边路网成熟，紧邻长春站交通门户，是缝合老宽城铁北地区与长春历史文化中轴线的空间关键锁扣。"
]