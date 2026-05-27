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
    if water is not None and not water.empty:
        water.plot(ax=ax, facecolor="#0066CC", edgecolor="none", alpha=0.35, zorder=1.5)

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("重点更新地块", "rect_orange_border"),
    ("伊通河水系", "rect_water"),
    ("卫星遥感影像", "rect_sat_base")
]

description_lines = [
    "1. 遥感影像：本图底图采用高分辨率 Google Earth 卫星遥感影像（2024年最新数据），直观反映项目所在长春市宽城区伪满皇宫周边区域的真实地表覆盖与建筑空间密度。",
    "2. 蓝绿肌理：东侧伊通河生态廊道水体形态完整，但街区内部绿色开敞空间较少，植被覆盖主要呈线性分布在铁路线及道路两侧，亟需引入更多社区口袋公园。",
    "3. 建设状况：街区内现状以中低层高密度建筑群为主，东北侧存在大面积中车低效工业遗存与厂房，南侧及西侧以商旧住宅为主，空间肌理较为拥挤。"
]