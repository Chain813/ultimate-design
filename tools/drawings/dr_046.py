# -*- coding: utf-8 -*-
"""DR-046 产业业态规划图 — 对应答辩稿 4.6 产业业态规划"""
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

    # 2. Main Title & Top Header Card (X: 2.0 to 139.4, Y: 89.0 to 96.3)
    header_shadow = mpatches.Rectangle((2.3, 88.7), 136.8, 7.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    header_bg = mpatches.Rectangle((2, 89.0), 136.8, 7.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(header_shadow)
    ax.add_patch(header_bg)
    
    # Gold top accent bar on the header card
    accent_bar = mpatches.Rectangle((2, 95.7), 136.8, 0.6, facecolor='#D97706', edgecolor='none', zorder=3)
    ax.add_patch(accent_bar)
    
    ax.text(3.5, 93.6, "产业业态规划图", 
            color='#0F172A', ha='left', va='center',
            fontproperties=_font(font_prop, 26, "bold"), zorder=4)
    
    ax.text(3.5, 90.7, "确立“三区一带”数字文创与全龄服务业态规划，实施低效存量空间功能置换，激活街区活力。", 
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

    # Draw water, buildings, roads, rails, and boundary on ax_map
    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#D0E6F7", edgecolor="none", zorder=1)
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax_map, facecolor="#F8FAFC", edgecolor="#E2E8F0", linewidth=0.15, zorder=0.8)
    if roads is not None and not roads.empty:
        roads.plot(ax=ax_map, color="#CBD5E1", linewidth=0.8, zorder=2)
    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#64748B", linewidth=1.2, linestyle=(0, (4, 4)), zorder=2.1)
    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=2.0, zorder=5.0)

    px_palace, py_palace = get_xy(125.3422, 43.9036)
    px_station, py_station = get_xy(125.3250, 43.9080)

    # Zone 1: 历史风貌核心体验区 (around palace)
    buf_palace = Point(px_palace, py_palace).buffer(350)
    gpd.GeoDataFrame(geometry=[buf_palace], crs="EPSG:3857").plot(
        ax=ax_map, facecolor="#FEF3C7", edgecolor="#B45309", linewidth=2.0, alpha=0.3, zorder=1.5)
    txt1 = ax_map.text(px_palace, py_palace-80, "历史风貌核心体验区", color='#78350F', ha='center', va='top',
            zorder=6, fontproperties=_font(font_prop, 12, 'bold'))
    txt1.set_path_effects([path_effects.withStroke(linewidth=2, foreground='#FFFFFF')])
    ax_map.text(px_palace, py_palace-140, "AIGC文创实验室·风貌认证零售", color='#92400E', ha='center', va='top',
            zorder=6, fontproperties=_font(font_prop, 9))

    # Zone 2: 站城融合门户区 (near station)
    buf_station = Point(px_station, py_station).buffer(280)
    gpd.GeoDataFrame(geometry=[buf_station], crs="EPSG:3857").plot(
        ax=ax_map, facecolor="#DBEAFE", edgecolor="#1D4ED8", linewidth=2.0, alpha=0.3, zorder=1.5)
    txt2 = ax_map.text(px_station, py_station+80, "站城融合门户区", color='#1E3A8A', ha='center', va='bottom',
            zorder=6, fontproperties=_font(font_prop, 12, 'bold'))
    txt2.set_path_effects([path_effects.withStroke(linewidth=2, foreground='#FFFFFF')])
    ax_map.text(px_station, py_station-30, "青年创业公社·文化市集", color='#1E40AF', ha='center', va='top',
            zorder=6, fontproperties=_font(font_prop, 9))

    # Zone 3: 全龄友好生活区 (south residential)
    px_life, py_life = get_xy(125.3380, 43.8980)
    buf_life = Point(px_life, py_life).buffer(350)
    gpd.GeoDataFrame(geometry=[buf_life], crs="EPSG:3857").plot(
        ax=ax_map, facecolor="#D1FAE5", edgecolor="#047857", linewidth=2.0, alpha=0.3, zorder=1.5)
    txt3 = ax_map.text(px_life, py_life, "全龄友好生活区", color='#064E3B', ha='center', va='center',
            zorder=6, fontproperties=_font(font_prop, 12, 'bold'))
    txt3.set_path_effects([path_effects.withStroke(linewidth=2, foreground='#FFFFFF')])
    ax_map.text(px_life, py_life-60, "社区食堂·日间照料·生活盒子", color='#065F46', ha='center', va='top',
            zorder=6, fontproperties=_font(font_prop, 9))

    # Belt: 文旅消费闭环带 (station → palace)
    belt_pts = [(125.325, 43.908), (125.335, 43.906), (125.342, 43.904)]
    belt_geom = LineString([get_xy(lon, lat) for lon, lat in belt_pts])
    gpd.GeoDataFrame(geometry=[belt_geom], crs="EPSG:3857").plot(
        ax=ax_map, color="#F43F5E", linewidth=5.0, alpha=0.7, zorder=4)
    mid = get_xy(125.335, 43.907)
    txt_belt = ax_map.text(mid[0], mid[1]+60, "文旅消费闭环带", color='#881337', ha='center', va='bottom',
            zorder=6, fontproperties=_font(font_prop, 11, 'bold'))
    txt_belt.set_path_effects([path_effects.withStroke(linewidth=2, foreground='#FFFFFF')])

    # Map Labels with corrected coordinates (with white text stroke shadows)
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

    # 3c. Draw wind rose on map (HUD)
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

    # 4. Legend Card (X: 101.5 to 139.4, Y: 62.0 to 87.0)
    legend_shadow = mpatches.Rectangle((101.8, 61.7), 37.9, 25.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    legend_bg = mpatches.Rectangle((101.5, 62.0), 37.9, 25.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(legend_shadow)
    ax.add_patch(legend_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 86.1), 37.9, 1.2, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(103.5, 83.8, "图例 / LEGEND", color='#D97706', ha='left', va='center',
            fontproperties=_font(font_prop, 13.5, 'bold'), zorder=4)
    
    # Legend Items
    legend_items_data = [
        ("规划研究范围", '#FF3B30', 'outline_boundary', 102.2, 106.2, 79.5),
        ("历史风貌核心体验区", '#FEF3C7', 'rect_fill_border', 120.7, 124.7, 79.5, '#B45309'),
        ("站城融合门户区", '#DBEAFE', 'rect_fill_border', 102.2, 106.2, 75.0, '#1D4ED8'),
        ("全龄友好生活区", '#D1FAE5', 'rect_fill_border', 120.7, 124.7, 75.0, '#047857'),
        ("文旅消费闭环带", '#F43F5E', 'line_thick', 102.2, 106.2, 70.5)
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
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=4.0, zorder=4)
            
        ax.text(x_txt, y_val, label, color='#334155', ha='left', va='center',
                fontproperties=_font(font_prop, 10.5), zorder=4)

    # Scale Bar (centered under Legend Card)
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
            fontproperties=_font(font_prop, 13.5, 'bold'), zorder=4)
    
    # 3 Bullet description items wrapped at 44 visual-width units, font size 15.0
    desc_data = [
        ("1. 三区定位：“古今共振·数智共生”产业布局，历史风貌核心区植入AIGC文创实验室，站城门户区布局青年创业公社，全龄友好区精准植入“生活盒子”。", 50.0),
        ("2. 一带串联：打造站城文旅消费闭环带，依托长春站东广场客流势能，串联文化市集与数字消费场景，形成数实融合创新孵化节点。", 34.0),
        ("3. 业态升级：摒弃单一文旅路径，确立“数字文创+全龄服务+遗产活化”三元动力结构，实施功能置换，激活MPI值48.3的失能存量空间。", 18.0)
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
    ("历史风貌核心体验区", "rect_style_orange"),
    ("站城融合门户区", "rect_style_blue"),
    ("全龄友好生活区", "rect_style_green"),
    ("文旅消费闭环带", "line_trail_red"),
]

description_lines = [
    "1. 三区定位：“古今共振·数智共生”产业布局，历史风貌核心区植入AIGC文创实验室，站城门户区布局青年创业公社，全龄友好区精准植入“生活盒子”。",
    "2. 一带串联：打造站城文旅消费闭环带，依托长春站东广场客流势能，串联文化市集与数字消费场景，形成数实融合创新孵化节点。",
    "3. 业态升级：摒弃单一文旅路径，确立“数字文创+全龄服务+遗产活化”三元动力结构，实施功能置换，激活MPI值48.3的失能存量空间。"
]
