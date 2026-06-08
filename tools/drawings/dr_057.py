# -*- coding: utf-8 -*-
"""DR-057 历史文化展示系统图"""
from pathlib import Path
import numpy as np
from shapely.geometry import Point, LineString
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

    ax.text(3.5, 93.6, "历史文化展示系统图", 
            color='#0F172A', ha='left', va='center',
            fontproperties=_font(font_prop, 26, "bold"), zorder=4)
    
    ax.text(3.5, 90.7, "构建“站-城-宫-河”一体化文化探访展示路径，加强历史遗存保护与视觉通廊控制。", 
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
        water.plot(ax=ax_map, facecolor="#D0E6F7", edgecolor="none", zorder=1)
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax_map, facecolor="#F8FAFC", edgecolor="#E2E8F0", linewidth=0.2, zorder=0.8)
    if roads is not None and not roads.empty:
        roads.plot(ax=ax_map, color="#CBD5E1", linewidth=0.8, zorder=2)
    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#64748B", linewidth=1.2, linestyle=(0, (4, 4)), zorder=2.1)
    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=2.0, zorder=5.0)

    # Draw tourist routes (red thick lines)
    t_path_pts = [
        (125.324761, 43.906852),
        (125.326120, 43.906852),
        (125.331051, 43.905996),
        (125.331673, 43.905778),
        (125.331673, 43.905533),
        (125.331691, 43.905085),
        (125.332088, 43.904700),
        (125.337773, 43.904749),
        (125.340664, 43.904796),
        (125.340727, 43.904385),
        (125.340925, 43.904011),
        (125.340860, 43.903652),
        (125.340928, 43.903325),
        (125.341210, 43.902995),
        (125.341424, 43.902848),
        (125.341210, 43.902995),
        (125.340928, 43.903325),
        (125.340860, 43.903652),
        (125.340925, 43.904011),
        (125.340727, 43.904385),
        (125.343002, 43.904804),
        (125.342981, 43.904899),
        (125.346493, 43.905366),
        (125.348163, 43.905631),
        (125.350431, 43.906419),
        (125.353383, 43.906434),
        (125.352606, 43.904315),
        (125.352564, 43.903931),
        (125.352538, 43.903518),
        (125.352606, 43.903221),
        (125.352747, 43.902924),
        (125.352992, 43.902639),
        (125.353388, 43.902323),
        (125.355235, 43.901173),
        (125.355673, 43.900838),
        (125.355996, 43.900466),
        (125.356210, 43.900109)
    ]
    t_line_geom = LineString([get_xy(lon, lat) for lon, lat in t_path_pts])
    gpd.GeoDataFrame(geometry=[t_line_geom], crs="EPSG:3857").plot(ax=ax_map, color="#EF4444", linewidth=3.5, zorder=4.5)

    # Key historical spots (gold dots)
    hist_spots = [
        ("伪满皇宫博物院", 125.3422, 43.9036),
        ("中车厂区旧址", 125.3401, 43.9079),
        ("光复路老商业街", 125.3475, 43.9017),
        ("传统风貌保护区", 125.3385, 43.9051)
    ]
    for name, lon, lat in hist_spots:
        px_p, py_p = get_xy(lon, lat)
        ax_map.plot(px_p, py_p, marker='o', markersize=14, color='#D97706', markeredgecolor='#FFFFFF', markeredgewidth=2.0, zorder=5.0)
        txt = ax_map.text(px_p, py_p + 70, name, color='#78350F', ha='center', va='bottom', zorder=6.0,
                          fontproperties=_font(font_prop, 12, 'bold'))
        txt.set_path_effects([path_effects.withStroke(linewidth=2.5, foreground='#FFFFFF')])

    # Other non-conflicting reference landmarks
    ref_labels = [
        ("长春站", 125.3250, 43.9080),
        ("胜利公园", 125.3260, 43.8960),
        ("伊通河沿岸公园", 125.3590, 43.9010)
    ]
    for name, lon, lat in ref_labels:
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
        ("文化探访展示路径", '#EF4444', 'line_thick', 120.7, 124.7, 79.5),
        ("关键展示节点", '#D97706', 'circle_node', 102.2, 106.2, 75.0),
        ("现状普通建筑", '#F8FAFC', 'rect_fill_border', 120.7, 124.7, 75.0, '#E2E8F0')
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
        elif style == 'line_thick':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=3.5, zorder=4)
        elif style == 'circle_node':
            ax.plot(x_sym + 1.5, y_val, marker='o', markersize=8, color=color_code, markeredgecolor='#FFFFFF', markeredgewidth=1.0, zorder=4)

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
        ("1. 探访路径：规划“站-城-宫-河”一体化文化探访展示路径，沿东十条及光复路老商业街布置，串联伪满皇宫与中车厂区，促进文旅人流融合。", 50.0),
        ("2. 节点标识：在伪满皇宫旧址、中车工业遗存等设立4处核心地标解说标识，并增设AR数字化虚拟展牌，打造线上线下一体化“露天博物馆”。", 34.0),
        ("3. 视廊控制：划定“长春火车站-伪满皇宫”、“亚泰大街-皇宫同德殿”等3条绝对视觉通廊控制线，禁止任何超出风貌限高及视线遮挡的广告与建构筑物。", 18.0)
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
    ("文化探访展示路径", "line_trail_red"),
    ("关键历史文化展示节点", "marker_node_gold"),
    ("现状普通建筑", "rect_building_light")
]

description_lines = [
    "1. 探访路径：规划“站-城-宫-河”一体化文化探访展示路径，沿东十条及光复路老商业街布置，串联伪满皇宫与中车厂区，促进文旅人流融合。",
    "2. 节点标识：在伪满皇宫旧址、中车工业遗存等设立4处核心地标解说标识，并增设AR数字化虚拟展牌，打造线上线下一体化“露天博物馆”。",
    "3. 视廊控制：划定“长春火车站-伪满皇宫”、“亚泰大街-皇宫同德殿”等3条绝对视觉通廊控制线，禁止任何超出风貌限高及视线遮挡的广告与建构筑物。"
]