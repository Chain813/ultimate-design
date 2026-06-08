# -*- coding: utf-8 -*-
"""DR-039 总体策略图 — 对应答辩稿 3.5 设计策略"""
from pathlib import Path
import numpy as np
from shapely.geometry import Point
import matplotlib.font_manager as fm
import matplotlib.patheffects as path_effects
import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    if water is not None and not water.empty:
        water.plot(ax=ax, facecolor="#D0E6F7", edgecolor="none", zorder=1)
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax, facecolor="#F8FAFC", edgecolor="#E2E8F0", linewidth=0.15, zorder=0.8)
    if roads is not None and not roads.empty:
        roads.plot(ax=ax, color="#CBD5E1", linewidth=0.8, zorder=2)

    px_palace, py_palace = get_xy(125.3422, 43.9036)

    # Strategy 1: 历史风貌"微创修缮与活化" — 300m buffer around palace
    buf_300 = Point(px_palace, py_palace).buffer(300)
    gpd.GeoDataFrame(geometry=[buf_300], crs="EPSG:3857").plot(
        ax=ax, facecolor="#FEF3C7", edgecolor="#D97706", linewidth=2.0, alpha=0.3, zorder=1.5)
    ax.text(px_palace, py_palace + 80, "微创修缮核心", color='#92400E', ha='center', va='bottom',
            fontsize=13, fontweight='bold', zorder=6,
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13))

    # 光复路历史风貌廊道
    from shapely.geometry import LineString
    corridor_pts = [(125.340, 43.906), (125.342, 43.905), (125.346, 43.904), (125.350, 43.903)]
    corridor_geom = LineString([get_xy(lon, lat) for lon, lat in corridor_pts])
    gpd.GeoDataFrame(geometry=[corridor_geom], crs="EPSG:3857").plot(
        ax=ax, color="#D97706", linewidth=4.0, linestyle="-", zorder=4)
    mid_pt = get_xy(125.345, 43.9045)
    txt = ax.text(mid_pt[0], mid_pt[1]+60, "光复路历史风貌廊道", color='#78350F', ha='center', va='bottom',
            fontsize=11, fontweight='bold', zorder=6,
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=11))
    txt.set_path_effects([path_effects.withStroke(linewidth=2, foreground='#FFFFFF')])

    # Strategy 2: "细胞级"微更新 — 5 neighborhood cells with 500m radius
    cells = [
        (125.332, 43.905, "邻里细胞①"), (125.338, 43.900, "邻里细胞②"),
        (125.345, 43.907, "邻里细胞③"), (125.350, 43.901, "邻里细胞④"),
        (125.328, 43.900, "邻里细胞⑤"),
    ]
    for lon, lat, name in cells:
        px, py = get_xy(lon, lat)
        ax.plot(px, py, marker='o', markersize=14, color='#10B981', markeredgecolor='#FFFFFF', markeredgewidth=2.0, zorder=5)
        buf = Point(px, py).buffer(500)
        gpd.GeoDataFrame(geometry=[buf], crs="EPSG:3857").plot(
            ax=ax, facecolor="#D1FAE5", edgecolor="#059669", linewidth=0.8, alpha=0.18, zorder=1.3)
        txt2 = ax.text(px, py+50, name, color='#047857', ha='center', va='bottom', fontsize=10, fontweight='bold', zorder=6,
                fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=10))
        txt2.set_path_effects([path_effects.withStroke(linewidth=2, foreground='#FFFFFF')])

    # Slow-walk path connecting cells
    walk_pts = [(125.328, 43.900), (125.332, 43.905), (125.338, 43.900), (125.345, 43.907), (125.350, 43.901)]
    walk_geom = LineString([get_xy(lon, lat) for lon, lat in walk_pts])
    gpd.GeoDataFrame(geometry=[walk_geom], crs="EPSG:3857").plot(
        ax=ax, color="#059669", linewidth=2.5, linestyle="--", zorder=3.5)

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("微创修缮核心 (300m缓冲)", "rect_style_orange"),
    ("光复路历史风貌廊道", "line_trail_orange"),
    ("邻里细胞·生活盒子 (500m)", "marker_node_green"),
    ("适老优先慢行道", "line_trail_green"),
]

description_lines = [
    "1. 历史风貌微创修缮：在伪满皇宫外围300m缓冲带及光复路历史风貌廊道，构建本地化AIGC风貌管控模型，强制校验重点地块改造方案的文化基因延续。",
    "2. 细胞级微更新：针对POI真空矛盾，精准植入5个半径约500米的“邻里细胞”生活盒子，配建日间照料、社区食堂等适老设施≥2000㎡。",
    "3. 社区动脉搭桥：沿居住区至市场路径铺设适老优先慢行道，系统化缝合全龄友好社区网络，实现“从交通节点向城市客厅的转型”。"
]
