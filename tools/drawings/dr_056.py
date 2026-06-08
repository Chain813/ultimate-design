# -*- coding: utf-8 -*-
"""DR-056 绿地景观系统图"""
from pathlib import Path
import numpy as np
from shapely.geometry import Point
import matplotlib.font_manager as fm
import matplotlib.patheffects as path_effects
import matplotlib.patches as mpatches
import geopandas as gpd
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"
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

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop, *args, **kwargs):
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

    # 2. Main Title & Top Header Card
    header_shadow = mpatches.Rectangle((2.3, 88.7), 136.8, 7.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    header_bg = mpatches.Rectangle((2, 89.0), 136.8, 7.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(header_shadow)
    ax.add_patch(header_bg)

    accent_bar = mpatches.Rectangle((2, 95.7), 136.8, 0.6, facecolor='#D97706', edgecolor='none', zorder=3)
    ax.add_patch(accent_bar)

    ax.text(3.5, 93.6, "绿地景观系统图", 
            color='#0F172A', ha='left', va='center',
            fontproperties=_font(font_prop, 26, "bold"), zorder=4)
    
    ax.text(3.5, 90.7, "构建“一廊、多点、蓝绿交织”的开敞空间系统，提升绿地率至35%以上，降低街区热岛效应。", 
            color='#334155', ha='left', va='center',
            fontproperties=_font(font_prop, 15.0), zorder=4)

    # 3. Giant Map Card Container
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

    # Draw layers on ax_map
    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#D0E6F7", edgecolor="none", zorder=1.5)
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax_map, facecolor="#F8FAFC", edgecolor="#E2E8F0", linewidth=0.2, zorder=1)
    if landuse is not None and not landuse.empty:
        green_gdf = landuse[landuse['GB_Code'] == 'G']
        other_gdf = landuse[landuse['GB_Code'] != 'G']
        if not other_gdf.empty:
            other_gdf.plot(ax=ax_map, facecolor="#F1F5F9", edgecolor="#E2E8F0", linewidth=0.2, zorder=0.8)
        if not green_gdf.empty:
            green_gdf.plot(ax=ax_map, facecolor="#A7F3D0", edgecolor="#047857", linewidth=0.5, zorder=2)
    if key_plots is not None and not key_plots.empty:
        key_plots.plot(ax=ax_map, facecolor="#10B981", edgecolor="#047857", linewidth=1.5, alpha=0.9, zorder=2.5)
    if roads is not None and not roads.empty:
        roads.plot(ax=ax_map, color="#E2E8F0", linewidth=0.8, zorder=3)
    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#64748B", linewidth=1.0, linestyle=(0, (5, 5)), zorder=4)
    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=2.0, zorder=5.0)

    # Landmark labels
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
                          fontproperties=_font(font_prop, 11, 'bold'), zorder=10)
        txt.set_path_effects([path_effects.withStroke(linewidth=3, foreground='#FFFFFF')])

    # 3c. Draw wind rose on map
    rose_path = ASSETS_DIR / "windrose.png"
    if rose_path.exists():
        try:
            ax_rose = fig.add_axes([84.0/141.42, 72.0/100.0, 13.0/141.42, 13.0/100.0])
            ax_rose.set_axis_off()
            
            y_g, x_g = np.ogrid[-1:1:100j, -1:1:100j]
            r = np.sqrt(x_g**2 + y_g**2)
            alpha = np.clip(1.0 - r, 0, 1) * 0.50
            grad_img = np.ones((100, 100, 4))
            grad_img[..., 3] = alpha
            ax_rose.imshow(grad_img, zorder=0, extent=[0, 1, 0, 1], origin='lower')
            
            rose_img = Image.open(rose_path).convert("RGBA")
            rose_data = np.array(rose_img)
            rose_data[..., 0] = 0
            rose_data[..., 1] = 0
            rose_data[..., 2] = 0
            black_rose_img = Image.fromarray(rose_data)
            
            ax_rose.imshow(black_rose_img, zorder=1)
        except Exception as e:
            print(f"Error loading wind rose: {e}")

    # 4. Legend Card
    legend_shadow = mpatches.Rectangle((101.8, 61.7), 37.9, 25.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    legend_bg = mpatches.Rectangle((101.5, 62.0), 37.9, 25.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(legend_shadow)
    ax.add_patch(legend_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 86.1), 37.9, 1.2, facecolor='#D97706', edgecolor='none', zorder=3))

    ax.text(103.5, 83.8, "图例 / LEGEND", color='#D97706', ha='left', va='center',
            fontproperties=_font(font_prop, 13.5, 'bold'), zorder=4)

    legend_items_data = [
        ("规划研究范围", '#FF3B30', 'outline_boundary', 102.2, 106.2, 79.5),
        ("规划新增绿地/广场", '#10B981', 'rect_fill_border', 120.7, 124.7, 79.5, '#047857'),
        ("现状公园绿地", '#A7F3D0', 'rect_fill_border', 102.2, 106.2, 75.0, '#047857'),
        ("城市水系", '#D0E6F7', 'rect_fill_border', 120.7, 124.7, 75.0, 'none'),
        ("城市道路", '#E2E8F0', 'rect_fill_border', 102.2, 106.2, 70.5, 'none'),
        ("现状建筑", '#F8FAFC', 'rect_fill_border', 120.7, 124.7, 70.5, '#E2E8F0')
    ]

    for item in legend_items_data:
        label = item[0]
        color_code = item[1]
        style = item[2]
        x_sym = item[3]
        x_txt = item[4]
        y_val = item[5]
        edge_color = item[6] if len(item) > 6 else 'none'

        if style == 'outline_boundary':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='none', edgecolor=color_code, linewidth=1.8, zorder=4)
            ax.add_patch(rect)
        elif style == 'rect_fill_border':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor=color_code, edgecolor=edge_color, linewidth=1.2, zorder=4)
            ax.add_patch(rect)

        ax.text(x_txt, y_val, label, color='#334155', ha='left', va='center',
                fontproperties=_font(font_prop, 10.5), zorder=4)

    # Scale Bar
    y_bar = 64.6
    y_tick_min = y_bar - 0.6
    y_tick_max = y_bar + 0.6
    y_text_val = y_bar + 0.8
    y_ratio_val = y_bar - 0.8

    scale_len = 500 / (view_w / 96.0)
    x_start = 120.45 - scale_len / 2
    x_end = x_start + scale_len
    ax.plot([x_start, x_end], [y_bar, y_bar], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_start, x_start], [y_tick_min, y_tick_max], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_start + scale_len/2, x_start + scale_len/2], [y_tick_min, y_tick_max], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_end, x_end], [y_tick_min, y_tick_max], color='#0F172A', linewidth=1.5, zorder=4)
    
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

    # 5. Description Card
    desc_shadow = mpatches.Rectangle((101.8, 3.7), 37.9, 56.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    desc_bg = mpatches.Rectangle((101.5, 4.0), 37.9, 56.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(desc_shadow)
    ax.add_patch(desc_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 58.8), 37.9, 1.2, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(103.5, 56.2, "设计说明与规划指标 / DESCRIPTION", color='#D97706', ha='left', va='center',
            fontproperties=_font(font_prop, 13.5, 'bold'), zorder=4)
    
    desc_data = [
        ("1. 增量提质：针对现状公共绿地匮乏（仅占11.1%）与硬质化高污染弊端，通过存量地块置换与微更新拆建，将绿地及开敞空间占比提升至15.5%以上，使人均绿地面积翻番。", 50.0),
        ("2. 指标达标：规划在老社区、中车遗存外围增设6处雨水花园，使绿地率达到35%的国家健康宜居街区目标，将全街区平均绿视率（GVI）由8.7%大幅提升至28%以上。", 34.0),
        ("3. 蓝绿渗透：将伊通河滨水生态廊道引入街区内部，构建生态防洪堤坝与微型海绵渗水绿带，形成连贯的水绿开敞景观系统，解决街区内热岛效应。", 18.0)
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
    ("规划新增绿地/广场", "rect_green_planned"),
    ("现状公园绿地", "rect_green"),
    ("城市水系", "rect_water"),
    ("城市道路", "rect_road"),
    ("现状建筑", "rect_building")
]

description_lines = [
    "1. 增量提质：针对现状公共绿地匮乏（仅占11.1%）与硬质化高污染弊端，通过存量地块置换与微更新拆建，将绿地及开敞空间占比提升至15.5%以上，使人均绿地面积翻番。",
    "2. 指标达标：规划在老社区、中车遗存外围增设6处雨水花园，使绿地率达到35%的国家健康宜居街区目标，将全街区平均绿视率（GVI）由8.7%大幅提升至28%以上。",
    "3. 蓝绿渗透：将伊通河滨水生态廊道引入街区内部，构建生态防洪堤坝与微型海绵渗水绿带，形成连贯的水绿开敞景观系统，解决街区内热岛效应。"
]