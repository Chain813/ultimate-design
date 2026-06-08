# -*- coding: utf-8 -*-
from pathlib import Path

import geopandas as gpd
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"

# Use the DR-013-style full-page layout instead of the standard A3 title frame.
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

    # Match DR-013: light drawing grid, full-page composition, no standard title frame.
    for x in range(5, 140, 5):
        ax.plot([x, x], [0, 100], color="#E2E8F0", linewidth=0.6, alpha=0.5, zorder=0)
    for y in range(5, 100, 5):
        ax.plot([0, 141.42], [y, y], color="#E2E8F0", linewidth=0.6, alpha=0.5, zorder=0)

    # Header, using DR-013 type scale.
    ax.add_patch(mpatches.Rectangle((2.3, 88.7), 136.8, 7.3, facecolor="#E2E8F0", edgecolor="none", zorder=1))
    ax.add_patch(mpatches.Rectangle((2.0, 89.0), 136.8, 7.3, facecolor="#FFFFFF", edgecolor="#CBD5E1", linewidth=1.2, zorder=2))
    ax.add_patch(mpatches.Rectangle((2.0, 95.7), 136.8, 0.6, facecolor="#D97706", edgecolor="none", zorder=3))
    ax.text(3.5, 93.6, "现状区位图", color="#0F172A", ha="left", va="center",
            fontproperties=_font(font_prop, 26, "bold"), zorder=4)
    ax.text(3.5, 90.7, "展示项目在长春市宽城区伪满皇宫周边的城市区位、交通联系、更新地块与周边蓝绿空间关系。",
            color="#334155", ha="left", va="center", fontproperties=_font(font_prop, 15.0), zorder=4)

    # Main map on the left.
    ax.add_patch(mpatches.Rectangle((2.3, 3.7), 98.0, 83.0, facecolor="#E2E8F0", edgecolor="none", zorder=1))
    ax.add_patch(mpatches.Rectangle((2.0, 4.0), 98.0, 83.0, facecolor="#FFFFFF", edgecolor="#CBD5E1", linewidth=1.2, zorder=2))
    ax_map = fig.add_axes([3.0 / 141.42, 5.0 / 100.0, 96.0 / 141.42, 81.0 / 100.0], facecolor="#F8FAFC", zorder=3)
    ax_map.set_xlim(cx - view_w / 2, cx + view_w / 2)
    ax_map.set_ylim(cy - view_h / 2, cy + view_h / 2)
    ax_map.set_axis_off()
    ax_map.set_aspect("equal")

    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#D0E6F7", edgecolor="none", zorder=1)
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax_map, facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=0.18, zorder=2)
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
    if key_plots is not None and not key_plots.empty:
        key_plots.plot(ax=ax_map, facecolor="#F59E0B", edgecolor="#D97706", linewidth=1.6, alpha=0.42, zorder=6)
    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=7)

    labels = [
        ("长春站", 125.3250, 43.9080),
        ("伪满皇宫博物院", 125.3422, 43.9036),
        ("光复路", 125.3475, 43.9017),
        ("伊通河沿岸公园", 125.3590, 43.9010),
        ("胜利公园", 125.3260, 43.8960),
    ]
    for name, lon, lat in labels:
        px, py = get_xy(lon, lat)
        ax_map.plot(px, py, marker="o", markersize=8, color="#FF9500", markeredgecolor="#FFFFFF", markeredgewidth=1.6, zorder=9)
        txt = ax_map.text(px, py + 70, name, color="#0F172A", ha="center", va="bottom",
                          fontproperties=_font(font_prop, 12, "bold"), zorder=10)
        txt.set_path_effects([path_effects.withStroke(linewidth=3, foreground="#FFFFFF")])

    # Right legend card.
    ax.add_patch(mpatches.Rectangle((101.8, 66.7), 37.9, 20.3, facecolor="#E2E8F0", edgecolor="none", zorder=1))
    ax.add_patch(mpatches.Rectangle((101.5, 67.0), 37.9, 20.3, facecolor="#FFFFFF", edgecolor="#CBD5E1", linewidth=1.2, zorder=2))
    ax.add_patch(mpatches.Rectangle((101.5, 85.8), 37.9, 1.5, facecolor="#D97706", edgecolor="none", zorder=3))
    ax.text(103.5, 82.8, "图例 / LEGEND", color="#D97706", ha="left", va="center",
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)

    legend_rows = [
        ("规划研究范围", "outline_red"),
        ("重点更新地块", "outline_orange"),
        ("现状建筑", "building"),
        ("城市水系", "water"),
        ("现状铁路", "rail"),
        ("城市道路", "road"),
    ]
    for i, (label, style) in enumerate(legend_rows):
        x = 103.5 + (i % 2) * 18.0
        y = 80.0 - (i // 2) * 3.3
        if style == "outline_red":
            ax.add_patch(mpatches.Rectangle((x, y - 0.8), 2.7, 1.7, facecolor="none", edgecolor="#FF3B30", linewidth=1.8, zorder=4))
        elif style == "outline_orange":
            ax.add_patch(mpatches.Rectangle((x, y - 0.8), 2.7, 1.7, facecolor="none", edgecolor="#F59E0B", linewidth=1.8, zorder=4))
        elif style == "building":
            ax.add_patch(mpatches.Rectangle((x, y - 0.8), 2.7, 1.7, facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=1.0, zorder=4))
        elif style == "water":
            ax.add_patch(mpatches.Rectangle((x, y - 0.8), 2.7, 1.7, facecolor="#D0E6F7", edgecolor="none", zorder=4))
        elif style == "rail":
            ax.plot([x, x + 2.7], [y, y], color="#475569", linewidth=1.8, linestyle=(0, (5, 4)), zorder=4)
        elif style == "road":
            ax.add_patch(mpatches.Rectangle((x, y - 0.55), 2.7, 1.1, facecolor="#E2E8F0", edgecolor="none", zorder=4))
        ax.text(x + 3.6, y, label, color="#334155", ha="left", va="center",
                fontproperties=_font(font_prop, 13.5), zorder=4)

    scale_len = 500 / (view_w / 96.0)
    x_start = 120.45 - scale_len / 2
    x_end = x_start + scale_len
    y_bar = 68.7
    ax.plot([x_start, x_end], [y_bar, y_bar], color="#0F172A", linewidth=1.5, zorder=4)
    for x in [x_start, x_start + scale_len / 2, x_end]:
        ax.plot([x, x], [y_bar - 0.8, y_bar + 0.8], color="#0F172A", linewidth=1.5, zorder=4)
    ax.text(x_start, 70.5, "0", color="#334155", ha="center", va="center", fontproperties=_font(font_prop, 11), zorder=4)
    ax.text(x_start + scale_len / 2, 70.5, "250m", color="#334155", ha="center", va="center", fontproperties=_font(font_prop, 11), zorder=4)
    ax.text(x_end, 70.5, "500m", color="#334155", ha="center", va="center", fontproperties=_font(font_prop, 11), zorder=4)
    scale_ratio = view_w / 0.31968
    scale_rounded = int(round(scale_ratio / 500)) * 500
    ax.text((x_start + x_end) / 2, 67.4, f"比例尺 1:{scale_rounded}", color="#334155", ha="center", va="center",
            fontproperties=_font(font_prop, 11, "bold"), zorder=4)

    # Right explanation card.
    ax.add_patch(mpatches.Rectangle((101.8, 3.7), 37.9, 61.3, facecolor="#E2E8F0", edgecolor="none", zorder=1))
    ax.add_patch(mpatches.Rectangle((101.5, 4.0), 37.9, 61.3, facecolor="#FFFFFF", edgecolor="#CBD5E1", linewidth=1.2, zorder=2))
    ax.add_patch(mpatches.Rectangle((101.5, 63.8), 37.9, 1.5, facecolor="#D97706", edgecolor="none", zorder=3))
    ax.text(103.5, 61.0, "区位说明 / LOCATION ANALYSIS", color="#D97706", ha="left", va="center",
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)

    rows = [
        ("1. 城市区位", "项目位于长春市宽城区伪满皇宫邻近区域，西接长春站交通枢纽，东临伊通河生态廊道，是历史文化展示与站城更新转换的重要界面。"),
        ("2. 场地范围", "研究范围约150公顷，北至长白路、南接长春大街、西临亚泰大街、东至东九条及伊通河沿线，覆盖老城居住、工业遗存与公共服务片区。"),
        ("3. 更新指向", "重点更新地块沿铁路、光复路和博物院周边分布，承担补绿地、织慢行、修复风貌和植入公共服务的综合更新任务。"),
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
    ("重点更新地块", "rect_orange_border"),
    ("现状建筑", "rect_building"),
    ("城市水系", "rect_water"),
    ("现状铁路", "line_rail"),
    ("城市道路", "rect_road"),
]

description_lines = [
    "1. 城市区位：项目位于长春市宽城区伪满皇宫邻近区域，西接长春站交通枢纽，东临伊通河生态廊道，是历史文化展示与站城更新转换的重要界面。",
    "2. 场地范围：研究范围约150公顷，北至长白路、南接长春大街、西临亚泰大街、东至东九条及伊通河沿线，覆盖老城居住、工业遗存与公共服务片区。",
    "3. 更新指向：重点更新地块沿铁路、光复路和博物院周边分布，承担补绿地、织慢行、修复风貌和植入公共服务的综合更新任务。",
]
