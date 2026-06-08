# -*- coding: utf-8 -*-
from shapely.geometry import Point
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"
GIS_DIR = ROOT / "data/gis"
ASSETS_DIR = ROOT / "assets"

NO_FRAME = True

def wrap_text(text, max_len=44):
    wrapped_lines = []
    for part in text.split('\n'):
        current_line = []
        current_width = 0
        for char in part:
            char_w = 2 if ord(char) > 127 else 1
            if current_width + char_w > max_len:
                wrapped_lines.append("".join(current_line))
                current_line = [char]
                current_width = char_w
            else:
                current_line.append(char)
                current_width += char_w
        if current_line:
            wrapped_lines.append("".join(current_line))
    return '\n'.join(wrapped_lines)

def _font(font_prop, size, weight="normal"):
    return fm.FontProperties(family=font_prop["family"], size=size, weight=weight)

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop, params=None):
    fig = ax.get_figure()

    # 1. Setup A3 Canvas Coordinates
    ax.set_facecolor("#F8FAFC")
    ax.set_xlim(0, 141.42)
    ax.set_ylim(0, 100)
    ax.set_axis_off()

    # Draw background grid
    for x in range(5, 140, 5):
        ax.plot([x, x], [0, 100], color='#E2E8F0', linestyle='-', linewidth=0.6, zorder=0, alpha=0.5)
    for y in range(5, 100, 5):
        ax.plot([0, 141.42], [y, y], color='#E2E8F0', linestyle='-', linewidth=0.6, zorder=0, alpha=0.5)

    # 2. Header Panel
    ax.add_patch(mpatches.Rectangle((2.3, 88.7), 136.8, 7.3, facecolor='#E2E8F0', edgecolor='none', zorder=1))
    ax.add_patch(mpatches.Rectangle((2.0, 89.0), 136.8, 7.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2))
    ax.add_patch(mpatches.Rectangle((2.0, 95.7), 136.8, 0.6, facecolor='#D97706', edgecolor='none', zorder=3))

    ax.text(3.5, 93.6, "建筑高度控制图", 
            color='#0F172A', ha='left', va='center', fontproperties=_font(font_prop, 26, "bold"), zorder=4)
    ax.text(3.5, 90.7, "展示伪满皇宫核心保护区及周边的视线走廊与高度管控引导分区，保障历史风貌环境完整性。", 
            color='#334155', ha='left', va='center', fontproperties=_font(font_prop, 15.0), zorder=4)

    # 3. Main Map Card Container (X: 2.0 to 100.0, Y: 4.0 to 87.0)
    ax.add_patch(mpatches.Rectangle((2.3, 3.7), 98.0, 83.0, facecolor='#E2E8F0', edgecolor='none', zorder=1))
    ax.add_patch(mpatches.Rectangle((2.0, 4.0), 98.0, 83.0, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2))

    # Sub-axes for GIS map
    ax_map = fig.add_axes([3.0 / 141.42, 5.0 / 100.0, 96.0 / 141.42, 81.0 / 100.0], facecolor="#F8FAFC", zorder=3)
    ax_map.set_xlim(cx - view_w / 2, cx + view_w / 2)
    ax_map.set_ylim(cy - view_h / 2, cy + view_h / 2)
    ax_map.set_axis_off()
    ax_map.set_aspect("equal")

    # Plot GIS Base Layers
    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#D0E6F7", edgecolor="none", zorder=1)

    # Draw Height limit overlay buffer circles around Palace
    px_palace, py_palace = get_xy(125.3422, 43.9036)
    palace_pt = Point(px_palace, py_palace)
    r1 = 450
    r2 = 900
    if params and "buffer_radii" in params:
        r1 = params["buffer_radii"].get("heritage", 450)
        r2 = params["buffer_radii"].get("transition", 900)

    buf_450 = palace_pt.buffer(r1)
    buf_900 = palace_pt.buffer(r2)

    # Overlay circles are clipped to the study boundary
    if boundary is not None and not boundary.empty:
        bnd_geom = boundary.unary_union
        overlay_450 = buf_450.intersection(bnd_geom)
        overlay_900 = buf_900.intersection(bnd_geom)

        gpd.GeoDataFrame(geometry=[overlay_450], crs="EPSG:3857").plot(
            ax=ax_map, facecolor="#EF4444", edgecolor="#EF4444", alpha=0.08, linewidth=1.2, linestyle='--', zorder=1.5
        )
        gpd.GeoDataFrame(geometry=[overlay_900.difference(overlay_450)], crs="EPSG:3857").plot(
            ax=ax_map, facecolor="#F59E0B", edgecolor="#F59E0B", alpha=0.06, linewidth=1.2, linestyle='--', zorder=1.4
        )

    # Draw Building Footprints Color-coded by height regulation
    if buildings is not None and not buildings.empty:
        buildings_copy = buildings.copy()
        dists = buildings_copy.geometry.distance(palace_pt)
        centroids = buildings_copy.geometry.centroid
        is_inside = centroids.within(bnd_geom)

        # Existing height coloring for outside buildings
        buildings_copy["Floor_num"] = pd.to_numeric(buildings_copy["Floor"], errors="coerce").fillna(1)
        exist_conds = [
            (buildings_copy["Floor_num"] <= 3),
            (buildings_copy["Floor_num"] >= 4) & (buildings_copy["Floor_num"] <= 7),
            (buildings_copy["Floor_num"] >= 8) & (buildings_copy["Floor_num"] <= 14),
            (buildings_copy["Floor_num"] >= 15) & (buildings_copy["Floor_num"] <= 20),
            (buildings_copy["Floor_num"] >= 21)
        ]
        exist_choices = [
            "#FEF3C7", # 1-3层: 淡黄
            "#FDBA74", # 4-7层: 淡橙
            "#FCA5A5", # 8-14层: 淡红
            "#EF4444", # 15-20层: 红
            "#991B1B"  # 21+层: 深红
        ]
        exist_color = np.select(exist_conds, exist_choices, default="#FEF3C7")

        # Control height coloring for inside buildings
        control_conds = [
            (dists <= r1),
            (dists > r1) & (dists <= r2),
            (dists > r2)
        ]
        control_choices = [
            "#EF4444", # 限高 9m (红)
            "#F59E0B", # 限高 18m (黄)
            "#3B82F6"  # 限高 24m (蓝)
        ]
        control_color = np.select(control_conds, control_choices, default="#3B82F6")

        buildings_copy["color"] = np.where(is_inside, control_color, exist_color)
        buildings_copy.plot(ax=ax_map, color=buildings_copy["color"], edgecolor="#64748B", linewidth=0.2, zorder=2.2)

    if roads is not None and not roads.empty:
        for lvl, lw, color in [(1, 1.8, "#94A3B8"), (2, 1.2, "#CBD5E1"), (3, 0.7, "#E2E8F0"), (4, 0.5, "#F1F5F9")]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax_map, color=color, linewidth=lw, capstyle="round", joinstyle="round", zorder=1.2)

    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#64748B", linewidth=1.2, linestyle=(0, (5, 5)), zorder=1.3)

    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=5)

    # Plot landmark labels
    for name, lon, lat in [("伪满皇宫博物院", 125.3422, 43.9036),
                            ("光复路", 125.3395, 43.9016),
                            ("长春站", 125.3250, 43.9080),
                            ("胜利公园", 125.3260, 43.8960)]:
        x_pt, y_pt = get_xy(lon, lat)
        ax_map.text(x_pt, y_pt, name, color='#475569', ha='center', va='bottom',
                    fontproperties=_font(font_prop, 9.0, 'bold'),
                    path_effects=[path_effects.withStroke(linewidth=2.0, foreground='#FFFFFF')], zorder=5)

    # 4. Legend Card (X: 101.5 to 139.4, Y: 67.0 to 87.0)
    legend_shadow = mpatches.Rectangle((101.8, 66.7), 37.9, 20.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    legend_bg = mpatches.Rectangle((101.5, 67.0), 37.9, 20.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(legend_shadow)
    ax.add_patch(legend_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 85.8), 37.9, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(103.5, 82.8, "图例 / LEGEND", color='#D97706', ha='left', va='center',
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)

    legend_items_data = [
        ("规划研究范围", '#FF3B30', 'outline_boundary', 102.2, 106.2, 79.5),
        ("城市道路", '#94A3B8', 'line_road', 120.7, 124.7, 79.5),
        ("核心视线保护区(≤9m)", '#EF4444', 'rect_color', 102.2, 106.2, 75.0),
        ("风貌过渡协调区(≤18m)", '#F59E0B', 'rect_color', 120.7, 124.7, 75.0),
        ("外围活力开发区(≤24m)", '#3B82F6', 'rect_color', 102.2, 106.2, 70.5),
        ("现状普通建筑", '#FEF3C7', 'rect_existing', 120.7, 124.7, 70.5)
    ]

    for label, color_code, style, x_sym, x_txt, y_val in legend_items_data:
        if style == 'outline_boundary':
            ax.add_patch(mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='none', edgecolor=color_code, linewidth=1.8, zorder=4))
        elif style == 'line_road':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=1.5, zorder=4)
        elif style == 'rect_color':
            ax.add_patch(mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor=color_code, edgecolor='none', alpha=0.9, zorder=4))
        elif style == 'rect_existing':
            ax.add_patch(mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor=color_code, edgecolor='#64748B', linewidth=0.3, zorder=4))
        ax.text(x_txt, y_val, label, color='#334155', ha='left', va='center',
                fontproperties=_font(font_prop, 10.0), zorder=4)

    # Scale Bar
    scale_len = 500 / (view_w / 96.0)
    x_start = 120.45 - scale_len / 2
    x_end = x_start + scale_len
    y_bar = 67.4
    ax.plot([x_start, x_end], [y_bar, y_bar], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_start, x_start], [y_bar - 0.8, y_bar + 0.8], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_start + scale_len/2, x_start + scale_len/2], [y_bar - 0.8, y_bar + 0.8], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_end, x_end], [y_bar - 0.8, y_bar + 0.8], color='#0F172A', linewidth=1.5, zorder=4)
    ax.text(x_start, y_bar + 1.5, "0", color='#334155', ha='center', va='center', fontproperties=_font(font_prop, 10.0), zorder=4)
    ax.text(x_start + scale_len/2, y_bar + 1.5, "250m", color='#334155', ha='center', va='center', fontproperties=_font(font_prop, 10.0), zorder=4)
    ax.text(x_end, y_bar + 1.5, "500m", color='#334155', ha='center', va='center', fontproperties=_font(font_prop, 10.0), zorder=4)
    scale_ratio = view_w / 0.31968
    scale_rounded = int(round(scale_ratio / 500)) * 500
    ax.text((x_start + x_end)/2, y_bar - 1.6, f"比例尺 1:{scale_rounded}", color='#334155', ha='center', va='center',
            fontproperties=_font(font_prop, 10.5, 'bold'), zorder=4)

    # 5. Description Card (X: 101.5 to 139.4, Y: 4.0 to 65.0)
    ax.add_patch(mpatches.Rectangle((101.8, 3.7), 37.9, 61.3, facecolor='#E2E8F0', edgecolor='none', zorder=1))
    ax.add_patch(mpatches.Rectangle((101.5, 4.0), 37.9, 61.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2))
    ax.add_patch(mpatches.Rectangle((101.5, 63.8), 37.9, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))

    ax.text(103.5, 61.0, "高度控制分区说明 / HEIGHT CONTROL", color='#D97706', ha='left', va='center',
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)

    desc_data = [
        ("1. 核心保护：伪满皇宫博物院周边 300 米核心保护带内建筑高度限制为 9 米（红色），杜绝一切插建高层，严格守护历史建筑风貌本底与视线通廊。", 53.0),
        ("2. 风貌过渡：300-600 米建设控制地带内限高 18 米（黄色），规划建议以 3-5 层坡屋顶中式现代建筑为主，与皇宫历史尺度形成平缓过渡。", 36.0),
        ("3. 外围开发：600 米外站城融合区及主要干道沿线，高度限值放宽至 24 米（蓝色），并可结合具体地块局部开发高层，平衡历史保护与活力开发的需求。", 19.0)
    ]
    for text, y_pos in desc_data:
        wrapped_desc = wrap_text(text, max_len=44)
        y_text = y_pos
        for line in wrapped_desc.split('\n'):
            ax.text(103.5, y_text, line, color='#334155', ha='left', va='center',
                    fontproperties=_font(font_prop, 14.0), zorder=4)
            y_text -= 3.2

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("核心视线保护区 (≤9m)", "rect_height_red"),
    ("风貌过渡协调区 (≤18m)", "rect_height_yellow"),
    ("外围活力开发区 (≤24m)", "rect_height_blue")
]

description_lines = [
    "1. 核心保护：伪满皇宫博物院周边300米核心保护带内建筑高度限制为9米（红色），杜绝一切插建高层，严格守护历史建筑环境本底。",
    "2. 风貌过渡：300-600米建设控制地带内限高18米（黄色），建议以3-5层坡屋顶中式现代风貌为主，与皇宫尺度形成缓和过渡天际线。",
    "3. 外围开发：600米外站城融合区及主要干道沿线，高度限值放宽至24-50米（蓝色），支持局部复合开发，实现空间高效率与历史风貌的平衡。"
]