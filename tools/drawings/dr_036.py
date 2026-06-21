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
    forbidden_start = set("，。、；：？！）】』」》〉〕”’）,.?!;:)】")
    forbidden_end = set("（【『「《〈〔“‘（([【")
    
    def char_width(c):
        return 2 if ord(c) > 127 else 1

    lines = []
    for part in text.split('\n'):
        if not part:
            lines.append("")
            continue
        current_line = ""
        current_w = 0
        i = 0
        while i < len(part):
            char = part[i]
            w = char_width(char)
            if current_w + w <= 44:
                current_line += char
                current_w += w
                i += 1
            else:
                if not current_line:
                    current_line = char
                    current_w = w
                    i += 1
                else:
                    if part[i] in forbidden_start:
                        current_line += part[i]
                        i += 1
                        while i < len(part) and part[i] in forbidden_start:
                            current_line += part[i]
                            i += 1
                    while current_line and current_line[-1] in forbidden_end:
                        i -= 1
                        current_line = current_line[:-1]
                if current_line:
                    lines.append(current_line)
                current_line = ""
                current_w = 0
        if current_line:
            lines.append(current_line)
    return '\n'.join(lines)
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

    ax.text(3.5, 93.6, "总体空间结构规划图", 
            color='#0F172A', ha='left', va='center', fontproperties=_font(font_prop, 26, "bold"), zorder=4)
    ax.text(3.5, 90.7, "构建“一核、一廊、多点”的针灸式规划更新空间骨架，打通站城文脉主轴，激活五大活力触媒节点。", 
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

    if roads is not None and not roads.empty:
        roads.plot(ax=ax_map, color="#CBD5E1", linewidth=0.8, zorder=1.1)

    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#64748B", linewidth=1.2, linestyle=(0, (4, 4)), zorder=1.2)

    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=2.5, zorder=5)

    # Coordinates for landmarks and nodes
    px_palace, py_palace = get_xy(125.3422, 43.9036)
    px_station, py_station = get_xy(125.3250, 43.9080)
    px_river, py_river = get_xy(125.3590, 43.9010)
    px_park, py_park = get_xy(125.3260, 43.8960)
    px_guangfu, py_guangfu = get_xy(125.3435, 43.9015)

    # 4. Draw Core and Axes
    # 4a. 站城文脉联动主轴 (Station to Palace)
    # Glow effect
    ax_map.plot([px_station, px_palace], [py_station, py_palace], color='#F97316', linewidth=9.0, alpha=0.28, zorder=3.8)
    # Solid line
    ax_map.plot([px_station, px_palace], [py_station, py_palace], color='#F97316', linewidth=4.0, zorder=3.9)

    # 4b. 生态文旅向心带 (Palace to River Park)
    # Glow effect
    ax_map.plot([px_palace, px_river], [py_palace, py_river], color='#06B6D4', linewidth=8.0, alpha=0.28, zorder=3.8)
    # Dashed line
    ax_map.plot([px_palace, px_river], [py_palace, py_river], color='#06B6D4', linewidth=3.5, linestyle='--', zorder=3.9)

    # 4c. Star for Palace Core
    ax_map.plot(px_palace, py_palace, marker='*', markersize=18, color='#EAB308', 
                markeredgecolor='#FFFFFF', markeredgewidth=1.8, zorder=4.8)

    # 5. Draw 5 key nodes (snapped exactly from Key_Plots_District.json centroids)
    node_coords = [
        (125.333536, 43.907389, "活力商办节点", 55),
        (125.341750, 43.906706, "活力节点 2", 55),
        (125.333542, 43.904235, "活力节点 3", -65),
        (125.346951, 43.899892, "活力节点 4", -65),
        (125.336475, 43.898121, "活力节点 5", -65)
    ]

    for idx, (lon, lat, label, offset_y) in enumerate(node_coords):
        nx, ny = get_xy(lon, lat)
        # Glow outer ring
        ax_map.plot(nx, ny, marker='o', markersize=20, color='#EF4444', alpha=0.2, zorder=4.3)
        # Main red marker
        ax_map.plot(nx, ny, marker='o', markersize=10, color='#EF4444', 
                    markeredgecolor='#FFFFFF', markeredgewidth=1.5, zorder=4.5)
        # Node text label
        ax_map.text(nx, ny + offset_y, label, color='#DC2626', ha='center', va='center',
                    fontproperties=_font(font_prop, 8.5, 'bold'),
                    path_effects=[path_effects.withStroke(linewidth=2.0, foreground='#FFFFFF')], zorder=5.0)

    # 6. Text Labels for Axes and Core
    # Axis 1 Text (Station to Palace)
    mid_x1, mid_y1 = (px_station + px_palace)/2, (py_station + py_palace)/2
    ax_map.text(mid_x1, mid_y1 + 110, "站城文脉联动主轴", color='#EA580C', ha='center', va='center',
                rotation=-7, fontproperties=_font(font_prop, 9.5, 'bold'),
                path_effects=[path_effects.withStroke(linewidth=2.5, foreground='#FFFFFF')], zorder=5.0)

    # Axis 2 Text (Palace to River)
    mid_x2, mid_y2 = (px_palace + px_river)/2, (py_palace + py_river)/2
    ax_map.text(mid_x2, mid_y2 + 95, "生态文旅向心带", color='#0891B2', ha='center', va='center',
                rotation=-3, fontproperties=_font(font_prop, 8.5, 'bold'),
                path_effects=[path_effects.withStroke(linewidth=2.5, foreground='#FFFFFF')], zorder=5.0)

    # Core Label
    ax_map.text(px_palace, py_palace + 85, "历史文化共振核心", color='#D97706', ha='center', va='center',
                fontproperties=_font(font_prop, 10.0, 'bold'),
                path_effects=[path_effects.withStroke(linewidth=2.5, foreground='#FFFFFF')], zorder=5.0)

    # 7. Landmarks (Orange Dots & Black Labels)
    landmarks = [
        ("长春站", px_station, py_station),
        ("胜利公园", px_park, py_park),
        ("光复路", px_guangfu, py_guangfu),
        ("伪满皇宫博物院", px_palace, py_palace),
        ("伊通河沿岸公园", px_river, py_river)
    ]
    for name, lx, ly in landmarks:
        # Avoid drawing dot exactly over Palace star or other main markers
        if name != "伪满皇宫博物院":
            ax_map.plot(lx, ly, marker='o', markersize=6, color='#F97316', zorder=4.6)
        
        # Label offset
        offset_y = 60 if name in ["长春站", "伊通河沿岸公园"] else -60
        ha_align = 'center'
        if name == "长春站": ha_align = 'left'
        if name == "伊通河沿岸公园": ha_align = 'right'
        
        ax_map.text(lx, ly + offset_y, name, color='#1E293B', ha=ha_align, va='center',
                    fontproperties=_font(font_prop, 8.5, 'bold'),
                    path_effects=[path_effects.withStroke(linewidth=2.0, foreground='#FFFFFF')], zorder=4.9)

    # 8. Legend Card (X: 101.5 to 139.4, Y: 67.0 to 87.0)
    legend_shadow = mpatches.Rectangle((101.8, 66.7), 37.9, 20.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    legend_bg = mpatches.Rectangle((101.5, 67.0), 37.9, 20.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(legend_shadow)
    ax.add_patch(legend_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 85.8), 37.9, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))

    ax.text(103.5, 82.8, "图例 / LEGEND", color='#D97706', ha='left', va='center',
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)

    legend_items_data = [
        ("规划研究范围", '#FF3B30', 'outline_boundary', 102.2, 106.2, 79.5),
        ("历史文化共振核心", '#EAB308', 'star', 120.7, 124.7, 79.5),
        ("站城文脉联动主轴", '#F97316', 'line_solid', 102.2, 106.2, 75.0),
        ("生态文旅向心带", '#06B6D4', 'line_dashed', 120.7, 124.7, 75.0),
        ("更新活力触媒节点", '#EF4444', 'circle_node', 102.2, 106.2, 70.5),
        ("现状基础设施", '#94A3B8', 'line_thin', 120.7, 124.7, 70.5)
    ]

    for label, color_code, style, x_sym, x_txt, y_val in legend_items_data:
        if style == 'outline_boundary':
            ax.add_patch(mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='none', edgecolor=color_code, linewidth=1.8, zorder=4))
        elif style == 'line_solid':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=2.5, zorder=4)
        elif style == 'line_dashed':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=2.0, linestyle='--', zorder=4)
        elif style == 'star':
            ax.plot(x_sym + 1.5, y_val, marker='*', markersize=8, color=color_code, markeredgecolor='#FFFFFF', markeredgewidth=0.8, zorder=4)
        elif style == 'circle_node':
            ax.plot(x_sym + 1.5, y_val, marker='o', markersize=6, color=color_code, markeredgecolor='#FFFFFF', markeredgewidth=0.8, zorder=4)
        elif style == 'line_thin':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=1.0, zorder=4)
        
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

    # 9. Description Card (X: 101.5 to 139.4, Y: 4.0 to 65.0)
    ax.add_patch(mpatches.Rectangle((101.8, 3.7), 37.9, 61.3, facecolor='#E2E8F0', edgecolor='none', zorder=1))
    ax.add_patch(mpatches.Rectangle((101.5, 4.0), 37.9, 61.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2))
    ax.add_patch(mpatches.Rectangle((101.5, 63.8), 37.9, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))

    ax.text(103.5, 61.0, "空间结构设计说明 / SPATIAL STRUCTURE", color='#D97706', ha='left', va='center',
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)

    desc_data = [
        # Bullet 1 manually broken
        ("1. 规划结构：提出“一核一廊多点”的针灸式规划\n   更新结构，一核为伪满皇宫文旅体验核，一廊为\n   光复路历史风貌轴，多点为五大更新活力触媒。", 53.0),
        # Bullet 2 manually broken
        ("2. 廊道缝合：打通站城文脉联动主轴，缝合被京\n   哈铁路割裂的南北空间联系，引导城市人流从\n   火车站进入皇宫风貌区，修复风貌廊道天际线。", 37.0),
        # Bullet 3 manually broken
        ("3. 针灸触媒：重点规划活力商办节点（节点1）、\n   工业遗产文化体验区（节点2）、历史街区（节\n   点3）、滨水生态公园（节点4）及生活服务盒\n   （节点5）等5处触媒，激活街区活力。", 21.0)
    ]
    for text, y_pos in desc_data:
        y_text = y_pos
        for line in text.split('\n'):
            ax.text(103.5, y_text, line, color='#334155', ha='left', va='center',
                    fontproperties=_font(font_prop, 14.0), zorder=4)
            y_text -= 3.2

        # Floating Windrose (Pure Black, 12.0 x 12.0) with soft white radial gradient backdrop
    try:
        from PIL import Image as _PIL_Image
        import numpy as _np
        from pathlib import Path as _Path
        _assets_dir = _Path(__file__).resolve().parent.parent.parent / "assets"
        _rose_path = _assets_dir / "长春市风玫瑰.png"
        if _rose_path.exists():
            ax_rose = fig.add_axes([87.0 / 141.42, 72.5 / 100.0, 12.0 / 141.42, 12.0 / 100.0], facecolor='none', zorder=4)
            ax_rose.set_axis_off()
            
            # Draw a soft white radial gradient backdrop
            _y_g, _x_g = _np.ogrid[-1:1:100j, -1:1:100j]
            _r = _np.sqrt(_x_g**2 + _y_g**2)
            _alpha = _np.clip(1.0 - _r, 0, 1) * 0.50
            _grad_img = _np.ones((100, 100, 4))
            _grad_img[..., 3] = _alpha
            ax_rose.imshow(_grad_img, zorder=0, extent=[0, 1, 0, 1], origin='lower')
            
            _rose_img = _PIL_Image.open(_rose_path).convert("RGBA")
            _rose_data = _np.array(_rose_img)
            _rose_data[..., 0] = 0
            _rose_data[..., 1] = 0
            _rose_data[..., 2] = 0
            _black_rose_img = _PIL_Image.fromarray(_rose_data)
            
            ax_rose.imshow(_black_rose_img, zorder=1)
    except Exception as e:
        print(f"Error loading wind rose in {__file__}: {e}")

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("历史文化共振核心", "star_core"),
    ("站城文脉联动主轴", "line_orange"),
    ("生态文旅向心带", "line_dashed_cyan"),
    ("更新活力触媒节点", "marker_node_red")
]

description_lines = [
    "1. 规划结构：提出“一核一廊多点”的针灸式规划更新结构，一核为伪满皇宫文旅体验核，一廊为光复路历史风貌轴，多点为五大更新活力触媒。",
    "2. 廊道缝合：打通站城文脉联动主轴，缝合被京哈铁路割裂的南北空间联系，引导城市人流从火车站进入皇宫风貌区，修复风貌廊道天际线。",
    "3. 针灸触媒：重点规划活力商办节点（节点1）、工业遗产文化体验区（节点2）、历史街区（节点3）、滨水生态公园（节点4）及生活服务盒（节点5）等5处触媒，激活街区活力。"
]