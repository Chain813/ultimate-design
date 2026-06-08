# -*- coding: utf-8 -*-
from shapely.geometry import Point, LineString
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patheffects as path_effects
import matplotlib.patches as mpatches
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

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop, params=None, *args, **kwargs):
    fig = ax.get_figure()
    
    # 1. Setup A3 Main Canvas Coordinates
    ax.set_facecolor("#F8FAFC")
    ax.set_xlim(0, 141.42)
    ax.set_ylim(0, 100)
    ax.set_axis_off()
    
    # Draw background grid
    for x in range(5, 140, 5):
        ax.plot([x, x], [0, 100], color='#E2E8F0', linestyle='-', linewidth=0.6, zorder=0, alpha=0.5)
    for y in range(5, 100, 5):
        ax.plot([0, 141.42], [y, y], color='#E2E8F0', linestyle='-', linewidth=0.6, zorder=0, alpha=0.5)
        
    # 2. Main Title & Top Header Card (X: 2.0 to 139.4, Y: 89.0 to 96.3)
    header_shadow = mpatches.Rectangle((2.3, 88.7), 136.8, 7.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    header_bg = mpatches.Rectangle((2, 89.0), 136.8, 7.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(header_shadow)
    ax.add_patch(header_bg)
    
    # Gold top accent bar on the header card
    accent_bar = mpatches.Rectangle((2, 95.7), 136.8, 0.6, facecolor='#D97706', edgecolor='none', zorder=3)
    ax.add_patch(accent_bar)
    
    ax.text(3.5, 93.6, "慢行系统规划图", 
            color='#0F172A', ha='left', va='center',
            fontproperties=_font(font_prop, 26, "bold"), zorder=4)
    
    ax.text(3.5, 90.7, "规划遗产漫游步道、邻里通勤步道与共享自行车道，构建绿色低碳、无障碍的慢行网络。", 
            color='#334155', ha='left', va='center',
            fontproperties=_font(font_prop, 15.0), zorder=4)

    # 3. Giant Map Card Container (X: 2.0 to 100.0, Y: 4.0 to 87.0)
    map_shadow = mpatches.Rectangle((2.3, 3.7), 98.0, 83.0, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    map_bg = mpatches.Rectangle((2.0, 4.0), 98.0, 83.0, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(map_shadow)
    ax.add_patch(map_bg)
    
    # 3b. Setup Map Sub-Axes (X: 4.0 to 98.0, Y: 6.0 to 85.0)
    ax_map = fig.add_axes([4.0/141.42, 6.0/100.0, 94.0/141.42, 79.0/100.0])
    ax_map.set_facecolor('#F1F5F9')
    ax_map.set_xlim(cx - view_w/2, cx + view_w/2)
    ax_map.set_ylim(cy - view_h/2, cy + view_h/2)
    ax_map.set_aspect('equal')
    ax_map.set_axis_off()

    # Plot GIS Base Layers
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax_map, facecolor="#F8FAFC", edgecolor="#94A3B8", linewidth=0.35, zorder=1.5)

    water_gdf = water
    if (water_gdf is None or water_gdf.empty) and landuse is not None and not landuse.empty:
        water_gdf = landuse[landuse['Color'] == '#7FFFFF']

    if water_gdf is not None and not water_gdf.empty:
        water_gdf.plot(ax=ax_map, facecolor="#D0E6F7", edgecolor="none", zorder=2.0)
        
    if roads is not None and not roads.empty:
        for lvl, lw, color in [(1, 1.8, "#CBD5E1"), (2, 1.2, "#CBD5E1"), (3, 0.7, "#CBD5E1"), (4, 0.5, "#CBD5E1")]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax_map, color=color, linewidth=lw, capstyle="round", joinstyle="round", zorder=2.5)

    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#94A3B8", linewidth=1.2, linestyle=(0, (5, 5)), zorder=2.6)

    # Draw the three slow traffic networks on top of base layers
    if roads is not None and not roads.empty:
        # 1. Tourist heritage path: Red thick line
        tourist_gdf = roads[roads['name'].str.contains('上海路|北京大街|光复路|东大桥|长白路|滨河', na=False)]
        if not tourist_gdf.empty:
            tourist_gdf.plot(
                ax=ax_map, color="#EF4444", linewidth=4.0, capstyle="round", joinstyle="round", zorder=4.2
            )

        # 2. Daily neighborhood walk path (Orange dashed)
        neighbor_gdf = roads[roads['name'].str.contains('重庆路|清明街|平治街|大马路|东二道街|东三道街|东四道街|自强街|永春路|陕西路|长江路|黑水路|马路', na=False)]
        if not neighbor_gdf.empty:
            neighbor_gdf.plot(
                ax=ax_map, color="#F97316", linewidth=2.5, linestyle="--", capstyle="round", joinstyle="round", zorder=4.1
            )

        # 3. Bike lane (Green solid)
        bike_gdf = roads[roads['name'].str.contains('亚泰大街|长春大街|人民大街|新发路|台北大街|吉林大路|凯旋路|临河街|东荣大路|远达大街', na=False)]
        if not bike_gdf.empty:
            bike_gdf.plot(
                ax=ax_map, color="#10B981", linewidth=3.0, capstyle="round", joinstyle="round", zorder=4.0
            )

    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=5)

    # Map Labels with corrected coordinates
    labels = [
        ("伪满皇宫博物院", 125.3422, 43.9036),
        ("光复路", 125.3395, 43.9016),
        ("伊通河沿岸公园", 125.3590, 43.9010),
        ("长春站", 125.3250, 43.9080),
        ("胜利公园", 125.3260, 43.8960)
    ]
    for name, lon, lat in labels:
        px, py = get_xy(lon, lat)
        ax_map.plot(px, py, marker='o', markersize=8, color='#FF9500', markeredgecolor='#FFFFFF', markeredgewidth=1.5, zorder=9)
        txt = ax_map.text(px, py + 70, name, color='#1d1d1f', ha='center', va='bottom',
                          fontproperties=_font(font_prop, 11, "bold"), zorder=10)
        txt.set_path_effects([path_effects.withStroke(linewidth=3, foreground='#FFFFFF')])

    # 4. Legend Card (X: 101.5 to 139.4, Y: 62.0 to 87.0)
    leg_y_min = 62.0
    leg_height = 25.0
    legend_shadow = mpatches.Rectangle((101.8, leg_y_min - 0.3), 37.9, leg_height, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    legend_bg = mpatches.Rectangle((101.5, leg_y_min), 37.9, leg_height, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(legend_shadow)
    ax.add_patch(legend_bg)
    ax.add_patch(mpatches.Rectangle((101.5, leg_y_min + leg_height - 1.2), 37.9, 1.2, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(103.5, leg_y_min + leg_height - 3.2, "图例 / LEGEND", color='#D97706', ha='left', va='center',
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)
    
    # Legend Items arranged in 3 rows
    legend_items_data = [
        # Row 0
        ("规划研究范围", '#FF3B30', 'outline_boundary', 102.2, 106.2, 80.5),
        ("现状城市道路", '#CBD5E1', 'line_road', 120.7, 124.7, 80.5),
        # Row 1
        ("文旅漫游步道", '#EF4444', 'line_trail_red', 102.2, 106.2, 77.2),
        ("社区邻里步道", '#F97316', 'line_trail_orange', 120.7, 124.7, 77.2),
        # Row 2
        ("共享骑行车道", '#10B981', 'line_trail_green', 102.2, 106.2, 73.9)
    ]
    
    for label, color_code, style, x_sym, x_txt, y_val in legend_items_data:
        if style == 'outline_boundary':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='none', edgecolor=color_code, linewidth=1.8, zorder=4)
            ax.add_patch(rect)
        elif style == 'line_road':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=1.8, zorder=4)
        elif style == 'line_trail_red':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=3.5, zorder=4)
        elif style == 'line_trail_orange':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=2.0, linestyle='--', zorder=4)
        elif style == 'line_trail_green':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=2.5, zorder=4)
            
        ax.text(x_txt, y_val, label, color='#334155', ha='left', va='center',
                fontproperties=_font(font_prop, 10.5), zorder=4)

    # Scale Bar (centered under Legend Card, y_bar = 64.6)
    y_bar = 64.6
    y_tick_min = y_bar - 0.6
    y_tick_max = y_bar + 0.6
    y_text_val = y_bar + 0.8
    y_ratio_val = y_bar - 0.8

    scale_len = 500 / (view_w / 96.0) # Length in main axes units
    x_start = 120.45 - scale_len / 2
    x_end = x_start + scale_len
    ax.plot([x_start, x_end], [y_bar, y_bar], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_start, x_start], [y_tick_min, y_tick_max], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_start + scale_len/2, x_start + scale_len/2], [y_tick_min, y_tick_max], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_end, x_end], [y_tick_min, y_tick_max], color='#0F172A', linewidth=1.5, zorder=4)
    
    # Scale labels
    ax.text(x_start, y_text_val, "0", color='#334155', ha='center', va='center',
            fontproperties=_font(font_prop, 10.0), zorder=4)
    ax.text(x_start + scale_len/2, y_text_val, "250m", color='#334155', ha='center', va='center',
            fontproperties=_font(font_prop, 10.0), zorder=4)
    ax.text(x_end, y_text_val, "500m", color='#334155', ha='center', va='center',
            fontproperties=_font(font_prop, 10.0), zorder=4)
    
    scale_ratio = view_w / 0.31968
    scale_rounded = int(round(scale_ratio / 500)) * 500
    ax.text((x_start + x_end)/2, y_ratio_val, f"比例尺 1:{scale_rounded}", color='#334155', ha='center', va='center',
            fontproperties=_font(font_prop, 10.5, 'bold'), zorder=4)

    # 5. Description Card (X: 101.5 to 139.4, Y: 4.0 to 60.0)
    desc_shadow = mpatches.Rectangle((101.8, 3.7), 37.9, 56.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    desc_bg = mpatches.Rectangle((101.5, 4.0), 37.9, 56.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(desc_shadow)
    ax.add_patch(desc_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 58.8), 37.9, 1.2, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(103.5, 56.2, "设计说明与规划指标 / DESCRIPTION", color='#D97706', ha='left', va='center',
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)
    
    # 3 Bullet description items wrapped at 44 visual-width units, font size 15.0
    desc_data = [
        ("1. 遗产大环：规划“长春站-伪满皇宫-中车遗存-伊通河”的4.2公里慢行文旅遗产环线，串联宽城区12处核心文旅地标与工业遗址。", 50.0),
        ("2. 绿道网络：沿亚泰高架下消极空间及铁路线绿带设置林荫自行车道，提供低碳骑行与日常通勤分流，改善街道空间的GVI（绿视率）。", 34.0),
        ("3. 适老微循环：老旧住宅区内加密邻里步行网络，全面推行无障碍慢行设计（宽度2.5m+，设坡道与盲道），保障老龄化社区30%老人的出行安全。", 18.0)
    ]
    for text, y_pos in desc_data:
        wrapped_desc = wrap_text(text, max_len=44)
        y_text = y_pos
        for line in wrapped_desc.split('\n'):
            ax.text(103.5, y_text, line, color='#334155', ha='left', va='center',
                    fontproperties=_font(font_prop, 15.0), zorder=4)
            y_text -= 3.2

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("现状城市道路", "rect_road"),
    ("文旅漫游遗产步道", "line_trail_red"),
    ("社区邻里步道", "line_trail_orange"),
    ("共享骑行车道", "line_trail_green")
]

description_lines = [
    "1. 遗产大环：规划“长春站-伪满皇宫-中车遗存-伊通河”的4.2公里慢行文旅遗产环线，串联宽城区12处核心文旅地标与工业遗址。",
    "2. 绿道网络：沿亚泰高架下消极空间及铁路线绿带设置林荫自行车道，提供低碳骑行与日常通勤分流，改善街道空间的GVI（绿视率）。",
    "3. 适老微循环：老旧住宅区内加密邻里步行网络，全面推行无障碍慢行设计（宽度2.5m+，设坡道与盲道），保障老龄化社区30%老人的出行安全。"
]
