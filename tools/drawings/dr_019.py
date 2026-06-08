# -*- coding: utf-8 -*-
from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"

# Use the DR-013/DR-004 style full-page layout instead of the standard A3 title frame.
NO_FRAME = True

def wrap_text(text, max_len=30):
    lines = []
    current = []
    width = 0
    for char in text:
        char_w = 2 if ord(char) > 127 else 1
        if char == "\n":
            lines.append("".join(current))
            current = []
            width = 0
            continue
        if width + char_w > max_len:
            lines.append("".join(current))
            current = [char]
            width = char_w
        else:
            current.append(char)
            width += char_w
    if current:
        lines.append("".join(current))
    return "\n".join(lines)

def _font(font_prop, size, weight="normal"):
    return fm.FontProperties(family=font_prop["family"], size=size, weight=weight)

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop, *args, **kwargs):
    fig = ax.get_figure()

    ax.set_facecolor("#F8FAFC")
    ax.set_xlim(0, 141.42)
    ax.set_ylim(0, 100)
    ax.set_axis_off()

    # Draw grid
    for x in range(5, 140, 5):
        ax.plot([x, x], [0, 100], color="#E2E8F0", linewidth=0.6, alpha=0.5, zorder=0)
    for y in range(5, 100, 5):
        ax.plot([0, 141.42], [y, y], color="#E2E8F0", linewidth=0.6, alpha=0.5, zorder=0)

    # Header Panel
    ax.add_patch(mpatches.Rectangle((2.3, 88.7), 136.8, 7.3, facecolor="#E2E8F0", edgecolor="none", zorder=1))
    ax.add_patch(mpatches.Rectangle((2.0, 89.0), 136.8, 7.3, facecolor="#FFFFFF", edgecolor="#CBD5E1", linewidth=1.2, zorder=2))
    ax.add_patch(mpatches.Rectangle((2.0, 95.7), 136.8, 0.6, facecolor="#D97706", edgecolor="none", zorder=3))
    
    ax.text(3.5, 93.6, "历史建筑与工业遗产分布图", color="#0F172A", ha="left", va="center",
            fontproperties=_font(font_prop, 26, "bold"), zorder=4)
    ax.text(3.5, 90.7, "展示项目在长春市宽城区伪满皇宫及周边中车长客厂区近代历史保护建筑与工业遗产分布现状。",
            color="#334155", ha="left", va="center", fontproperties=_font(font_prop, 15.0), zorder=4)

    # Main map on the left
    ax.add_patch(mpatches.Rectangle((2.3, 3.7), 98.0, 83.0, facecolor="#E2E8F0", edgecolor="none", zorder=1))
    ax.add_patch(mpatches.Rectangle((2.0, 4.0), 98.0, 83.0, facecolor="#FFFFFF", edgecolor="#CBD5E1", linewidth=1.2, zorder=2))
    
    # Exact sub-axes of DR-004
    ax_map = fig.add_axes([3.0 / 141.42, 5.0 / 100.0, 96.0 / 141.42, 81.0 / 100.0], facecolor="#F8FAFC", zorder=3)
    ax_map.set_xlim(cx - view_w / 2, cx + view_w / 2)
    ax_map.set_ylim(cy - view_h / 2, cy + view_h / 2)
    ax_map.set_axis_off()
    ax_map.set_aspect("equal")

    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#D0E6F7", edgecolor="none", zorder=1)
        
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax_map, facecolor="#E2E8F0", edgecolor="#CBD5E1", linewidth=0.2, zorder=2)
        
    prot_path = STATIC_DIR / "protected_buildings.geojson"
    if prot_path.exists():
        try:
            protected = gpd.read_file(prot_path).to_crs(epsg=3857)
            protected.plot(ax=ax_map, facecolor="#D97706", edgecolor="#B45309", linewidth=0.5, alpha=1.0, zorder=2.5)
        except Exception as e:
            print(f"Error loading protected buildings: {e}")
            
    if roads is not None and not roads.empty:
        for lvl, lw in [(1, 3.8), (2, 3.0), (3, 2.2), (4, 1.6)]:
            sub_gdf = roads[roads["level"] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax_map, color="#94A3B8", linewidth=lw, capstyle="round", joinstyle="round", zorder=3)
        for lvl, lw in [(1, 2.6), (2, 2.0), (3, 1.2), (4, 0.8)]:
            sub_gdf = roads[roads["level"] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax_map, color="#E2E8F0", linewidth=lw, capstyle="round", joinstyle="round", zorder=4)
                
    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#475569", linewidth=1.8, linestyle=(0, (6, 6)), zorder=5)
        
    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=7)

    # Right legend card
    ax.add_patch(mpatches.Rectangle((101.8, 66.7), 37.9, 20.3, facecolor="#E2E8F0", edgecolor="none", zorder=1))
    ax.add_patch(mpatches.Rectangle((101.5, 67.0), 37.9, 20.3, facecolor="#FFFFFF", edgecolor="#CBD5E1", linewidth=1.2, zorder=2))
    ax.add_patch(mpatches.Rectangle((101.5, 85.8), 37.9, 1.5, facecolor="#D97706", edgecolor="none", zorder=3))
    ax.text(103.5, 82.8, "图例 / LEGEND", color="#D97706", ha="left", va="center",
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)

    legend_rows = [
        ("规划研究范围", "outline_red"),
        ("城市道路", "road"),
        ("重点历史/工业遗产", "rect_heritage"),
        ("现状普通建筑", "building"),
        ("城市水系", "water"),
        ("现状铁路线", "rail"),
    ]
    for i, (label, style) in enumerate(legend_rows):
        x = 103.5 + (i % 2) * 18.0
        y = 80.0 - (i // 2) * 3.3
        if style == "outline_red":
            ax.add_patch(mpatches.Rectangle((x, y - 0.8), 2.7, 1.7, facecolor="none", edgecolor="#FF3B30", linewidth=1.8, zorder=4))
        elif style == "rect_heritage":
            ax.add_patch(mpatches.Rectangle((x, y - 0.8), 2.7, 1.7, facecolor="#D97706", edgecolor="#B45309", linewidth=0.5, zorder=4))
        elif style == "building":
            ax.add_patch(mpatches.Rectangle((x, y - 0.8), 2.7, 1.7, facecolor="#E2E8F0", edgecolor="#CBD5E1", linewidth=0.5, zorder=4))
        elif style == "water":
            ax.add_patch(mpatches.Rectangle((x, y - 0.8), 2.7, 1.7, facecolor="#D0E6F7", edgecolor="none", zorder=4))
        elif style == "road":
            ax.add_patch(mpatches.Rectangle((x, y - 0.55), 2.7, 1.1, facecolor="#E2E8F0", edgecolor="none", zorder=4))
        elif style == "rail":
            ax.plot([x, x + 2.7], [y, y], color="#475569", linewidth=1.8, linestyle=(0, (5, 4)), zorder=4)
        ax.text(x + 3.6, y, label, color="#334155", ha="left", va="center",
                fontproperties=_font(font_prop, 13.5), zorder=4)

    # Scale Bar
    scale_len = 500 / (view_w / 96.0)
    x_start = 120.45 - scale_len / 2
    x_end = x_start + scale_len
    y_bar = 68.7
    ax.plot([x_start, x_end], [y_bar, y_bar], color="#0F172A", linewidth=1.5, zorder=4)
    for x_tick in [x_start, x_start + scale_len / 2, x_end]:
        ax.plot([x_tick, x_tick], [y_bar - 0.8, y_bar + 0.8], color="#0F172A", linewidth=1.5, zorder=4)
    ax.text(x_start, 70.5, "0", color="#334155", ha="center", va="center", fontproperties=_font(font_prop, 11), zorder=4)
    ax.text(x_start + scale_len / 2, 70.5, "250m", color="#334155", ha="center", va="center", fontproperties=_font(font_prop, 11), zorder=4)
    ax.text(x_end, 70.5, "500m", color="#334155", ha="center", va="center", fontproperties=_font(font_prop, 11), zorder=4)
    scale_ratio = view_w / 0.31968
    scale_rounded = int(round(scale_ratio / 500)) * 500
    ax.text((x_start + x_end) / 2, 67.4, f"比例尺 1:{scale_rounded}", color="#334155", ha="center", va="center",
            fontproperties=_font(font_prop, 11, "bold"), zorder=4)

    # Right explanation card
    ax.add_patch(mpatches.Rectangle((101.8, 3.7), 37.9, 61.3, facecolor="#E2E8F0", edgecolor="none", zorder=1))
    ax.add_patch(mpatches.Rectangle((101.5, 4.0), 37.9, 61.3, facecolor="#FFFFFF", edgecolor="#CBD5E1", linewidth=1.2, zorder=2))
    ax.add_patch(mpatches.Rectangle((101.5, 63.8), 37.9, 1.5, facecolor="#D97706", edgecolor="none", zorder=3))
    ax.text(103.5, 61.0, "遗产说明 / HERITAGE ANALYSIS", color="#D97706", ha="left", va="center",
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)

    rows = [
        ("1. 遗产识别", "片区内包含以伪满皇宫为核心的近代历史建筑群，以及东北侧中车长客厂区的大跨度工业厂房与铁轨遗存，是复合型城市遗产的关键载体。"),
        ("2. 价值评估", "历史风貌核心保护区与中车厂区具有极高的建筑质量和空间识别度，是本次更新设计中严格执行“保留与修缮”的刚性管控区域。"),
        ("3. 活化思路", "保护传统街区肌理与风貌界面的连续性，打通历史文化展示游线，将工业遗存置换为文创、博览和青年双创等活力复合功能。"),
    ]
    y = 56.0
    for title, body in rows:
        ax.text(103.5, y, title, color="#0F172A", ha="left", va="top",
                fontproperties=_font(font_prop, 15.0, "bold"), zorder=4)
        y -= 2.5
        for line in wrap_text(body, 44).split("\n"):
            ax.text(103.5, y, line, color="#334155", ha="left", va="top",
                    fontproperties=_font(font_prop, 15.0), zorder=4)
            y -= 2.85
        y -= 2.2

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("重点历史/工业遗产建筑", "rect_heritage"),
    ("现状普通建筑", "rect_building_light"),
    ("城市水系", "rect_water"),
    ("城市道路", "rect_road"),
    ("现状铁路线", "line_rail")
]

description_lines = [
    "1. 遗产识别：片区内包含以伪满皇宫为核心的近代历史建筑群，以及东北侧中车长客厂区的大跨度工业厂房与铁轨遗存，是复合型城市遗产的关键载体。",
    "2. 价值评估：历史风貌核心保护区与中车厂区具有极高的建筑质量和空间识别度，是本次更新设计中严格执行“保留与修缮”的刚性管控区域。",
    "3. 活化思路：保护传统街区肌理与风貌界面的连续性，打通历史文化展示游线，将工业遗存置换为文创、博览和青年双创等活力复合功能。"
]