# -*- coding: utf-8 -*-
from shapely.geometry import Point, LineString
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

    ax.text(3.5, 93.6, "道路交通系统规划图", 
            color='#0F172A', ha='left', va='center', fontproperties=_font(font_prop, 26, "bold"), zorder=4)
    ax.text(3.5, 90.7, "基于空间句法全局整合度诊断，识别出由于铁轨屏障与内部支路匮乏而导致的街区交通孤岛病灶。", 
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
        water.plot(ax=ax_map, facecolor="#E2F0FD", edgecolor="none", zorder=1)

    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax_map, facecolor="#F1F5F9", edgecolor="#CBD5E1", linewidth=0.2, zorder=0.8)

    # Load and Plot Space Syntax Integration subtle background
    syntax_path = STATIC_DIR / "road_syntax.geojson"
    if syntax_path.exists():
        try:
            roads_syntax = gpd.read_file(syntax_path)
            if roads_syntax.crs != boundary.crs:
                roads_syntax = roads_syntax.to_crs(boundary.crs)
            # Plot syntax background
            roads_syntax.plot(ax=ax_map, column='integration_norm', cmap='coolwarm', alpha=0.35, linewidth=1.5, zorder=1.1)
        except Exception as e:
            print(f"Error loading space syntax overlay: {e}")

    # Plot existing road network as overlay
    if roads is not None and not roads.empty:
        for lvl, lw, color in [(1, 1.8, "#64748B"), (2, 1.2, "#94A3B8"), (3, 0.7, "#CBD5E1"), (4, 0.5, "#E2E8F0")]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax_map, color=color, linewidth=lw, capstyle="round", joinstyle="round", zorder=1.2)

    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#334155", linewidth=1.5, linestyle=(0, (5, 5)), zorder=1.3)

    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=5)

    # 3c. Proposed road network overlays removed per user request (planned road network is unreasonable)
    proposed_links = []

    # Plot landmark labels
    for name, lon, lat in [("伪满皇宫博物院", 125.3422, 43.9036),
                            ("光复路", 125.3395, 43.9016),
                            ("长春站", 125.3250, 43.9080),
                            ("胜利公园", 125.3260, 43.8960)]:
        x_pt, y_pt = get_xy(lon, lat)
        ax_map.text(x_pt, y_pt, name, color='#475569', ha='center', va='bottom',
                    fontproperties=_font(font_prop, 9.0, 'bold'),
                    path_effects=[path_effects.withStroke(linewidth=2.0, foreground='#FFFFFF')], zorder=5)

    # Intervention annotations removed per user request

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
        ("现状城市道路", '#94A3B8', 'line_road', 120.7, 124.7, 79.5),
        ("现状铁路线", '#334155', 'line_rail', 102.2, 106.2, 75.0),
        ("空间整合度 (Rn)", '#8B5CF6', 'syntax_bar', 120.7, 124.7, 75.0)
    ]

    for label, color_code, style, x_sym, x_txt, y_val in legend_items_data:
        if style == 'outline_boundary':
            ax.add_patch(mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='none', edgecolor=color_code, linewidth=1.8, zorder=4))
        elif style == 'line_road':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=1.5, zorder=4)
        elif style == 'line_proposed':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=2.0, linestyle='--', zorder=4)
        elif style == 'line_proposed_solid':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=2.0, zorder=4)
        elif style == 'line_rail':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=1.2, linestyle='--', zorder=4)
        elif style == 'syntax_bar':
            # Mini coolwarm gradient segment
            ax.add_patch(mpatches.Rectangle((x_sym, y_val - 0.6), 1.5, 1.2, facecolor='#3B82F6', zorder=4))
            ax.add_patch(mpatches.Rectangle((x_sym + 1.5, y_val - 0.6), 1.5, 1.2, facecolor='#EF4444', zorder=4))
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

    # 5. Description Card (X: 101.5 to 139.4, Y: 4.0 to 65.0)
    ax.add_patch(mpatches.Rectangle((101.8, 3.7), 37.9, 61.3, facecolor='#E2E8F0', edgecolor='none', zorder=1))
    ax.add_patch(mpatches.Rectangle((101.5, 4.0), 37.9, 61.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2))
    ax.add_patch(mpatches.Rectangle((101.5, 63.8), 37.9, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))

    ax.text(103.5, 61.0, "交通规划诊断说明 / TRANSPORTATION PLAN", color='#D97706', ha='left', va='center',
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)

    desc_data = [
        ("1. 句法可达性诊断：基于空间句法全局整合度分析，由于北部铁路线的强物理阻隔，地块内部与外部骨干路网的联系严重受阻，空间通达度呈现强烈的边缘低迷态势。", 53.0),
        ("2. 街区微循环病灶：现状街区内部缺乏毛细血管式的支路与低速街巷网，机动车与行人过分集聚于外围边界主干道，导致地块核心文保区沦为交通活性死角。", 36.0),
        ("3. 整合度空间异质：句法整合度呈环状外溢，核心保护区内部的商业与文旅活力缺乏微循环网络支撑，无法形成有效的慢行渗透与空间集聚网络。", 19.0)
    ]
    for text, y_pos in desc_data:
        wrapped_desc = wrap_text(text, max_len=44)
        y_text = y_pos
        for line in wrapped_desc.split('\n'):
            ax.text(103.5, y_text, line, color='#334155', ha='left', va='center',
                    fontproperties=_font(font_prop, 14.0), zorder=4)
            y_text -= 2.8

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("现状主干路", "line_primary_road"),
    ("现状次干路", "line_secondary_road"),
    ("现状支路", "line_tertiary_road"),
    ("现状铁路", "line_rail")
]

description_lines = [
    "1. 句法可达性诊断：基于空间句法全局整合度分析，由于北部铁路线的强物理阻隔，地块内部与外部骨干路网的联系严重受阻，空间通达度呈现强烈的边缘低迷态势。",
    "2. 街区微循环病灶：现状街区内部缺乏毛细血管式的支路与低速街巷网，机动车与行人过分集聚于外围边界主干道，导致地块核心文保区沦为交通活性死角。",
    "3. 整合度空间异质：句法整合度呈环状外溢，核心保护区内部的商业与文旅活力缺乏微循环网络支撑，无法形成有效的慢行渗透与空间集聚网络。"
]