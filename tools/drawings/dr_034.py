"""DR-039 总体策略图 — 对应答辩稿 3.5 设计策略"""
from pathlib import Path

import geopandas as gpd
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
import numpy as np
import pandas as pd
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"
GIS_DIR = ROOT / "data/gis"

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

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop, params=None, *args, **kwargs):
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
    
    ax.text(3.5, 93.6, "总体策略图", 
            color='#0F172A', ha='left', va='center', fontproperties=_font(font_prop, 26, "bold"), zorder=4)
    ax.text(3.5, 90.7, "整合微创修缮、细胞级微更新与慢行系统三大策略，构建古今共振的城市更新空间骨架。", 
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
        
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax_map, facecolor="#F8FAFC", edgecolor="#E2E8F0", linewidth=0.15, zorder=2.2)

    if roads is not None and not roads.empty:
        for lvl, lw, color in [(1, 1.8, "#94A3B8"), (2, 1.2, "#CBD5E1"), (3, 0.7, "#E2E8F0"), (4, 0.5, "#F1F5F9")]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax_map, color=color, linewidth=lw, capstyle="round", joinstyle="round", zorder=1.2)

    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#64748B", linewidth=1.2, linestyle=(0, (5, 5)), zorder=1.3)

    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=5)

    # ── Overlay Strategy Layer on ax_map ──
    # Resolve centroids of key plots to position neighborhood cells exactly on them
    if key_plots is not None and not key_plots.empty:
        # Plot key plots in soft green fill to link them to cell centers visually
        key_plots.plot(ax=ax_map, facecolor="#E6FDF0", edgecolor="#10B981", linewidth=0.8, alpha=0.5, zorder=2.5)
        
        geom_0 = key_plots.iloc[0].geometry.centroid
        geom_1 = key_plots.iloc[1].geometry.centroid
        geom_2 = key_plots.iloc[2].geometry.centroid
        geom_3 = key_plots.iloc[3].geometry.centroid
        geom_4 = key_plots.iloc[4].geometry.centroid
        x0, y0 = geom_0.x, geom_0.y
        x1, y1 = geom_1.x, geom_1.y
        x2, y2 = geom_2.x, geom_2.y
        x3, y3 = geom_3.x, geom_3.y
        x4, y4 = geom_4.x, geom_4.y
    else:
        # Safe fallback
        x0, y0 = get_xy(125.337, 43.905)
        x1, y1 = get_xy(125.345, 43.902)
        x2, y2 = get_xy(125.331, 43.908)
        x3, y3 = get_xy(125.350, 43.906)
        x4, y4 = get_xy(125.355, 43.909)

    # 1. Strategy 1: Palace 300m buffer
    px_palace, py_palace = get_xy(125.3422, 43.9036)
    circle_300 = mpatches.Circle((px_palace, py_palace), 300, facecolor='#FEF3C7', edgecolor='#D97706', linewidth=2.0, alpha=0.35, zorder=3.0)
    ax_map.add_patch(circle_300)

    # 2. Strategy 1: Historical corridor line
    corridor_pts = [(125.340, 43.906), (125.342, 43.905), (125.346, 43.904), (125.350, 43.903)]
    corridor_x, corridor_y = zip(*[get_xy(lon, lat) for lon, lat in corridor_pts])
    ax_map.plot(corridor_x, corridor_y, color='#D97706', linewidth=4.0, zorder=3.2)

    # 3. Strategy 2: 5 Cells (500m buffer circles)
    cells = [
        (x0, y0, "邻里细胞①\n(御花园东巷)"), 
        (x1, y1, "邻里细胞②\n(活态市集)"),
        (x2, y2, "邻里细胞③\n(全龄共享)"), 
        (x3, y3, "邻里细胞④\n(历史缝合)"),
        (x4, y4, "邻里细胞⑤\n(能量花园)"),
    ]
    for cx_cell, cy_cell, _name in cells:
        circle_500 = mpatches.Circle((cx_cell, cy_cell), 500, facecolor='#D1FAE5', edgecolor='#059669', linewidth=1.0, alpha=0.15, zorder=2.4)
        ax_map.add_patch(circle_500)
        # Center node dot
        ax_map.plot(cx_cell, cy_cell, marker='o', color='#10B981', markersize=5, markeredgecolor='#FFFFFF', markeredgewidth=1.0, zorder=3.3)

    # 4. Strategy 2: Slow-walk path (Dashed green line connecting nodes from west to east: 0 -> 2 -> 4 -> 1 -> 3)
    walk_x = [x0, x2, x4, x1, x3]
    walk_y = [y0, y2, y4, y1, y3]
    ax_map.plot(walk_x, walk_y, color='#059669', linewidth=2.0, linestyle='--', zorder=3.1)

    # ── Text Labels with outlines ──
    pe = [path_effects.withStroke(linewidth=2.5, foreground='#FFFFFF')]
    
    # Palace Dot & Label
    ax_map.plot(px_palace, py_palace, marker='o', color='#D97706', markersize=6, markeredgecolor='#FFFFFF', markeredgewidth=1.0, zorder=3.3)
    ax_map.text(px_palace, py_palace - 35, "伪满皇宫博物院\n(微创修缮核心)", color='#B45309', ha='center', va='top', fontproperties=_font(font_prop, 10, "bold"), path_effects=pe, zorder=3.4)

    # Corridor Label
    mid_x, mid_y = get_xy(125.345, 43.9042)
    ax_map.text(mid_x, mid_y + 35, "光复路历史风貌廊道", color='#B45309', ha='center', va='bottom', fontproperties=_font(font_prop, 10, "bold"), path_effects=pe, zorder=3.4)

    # Cell Labels
    for cx_cell, cy_cell, name in cells:
        ax_map.text(cx_cell, cy_cell - 35, name, color='#047857', ha='center', va='top', fontproperties=_font(font_prop, 9, "bold"), path_effects=pe, zorder=3.4)

    # Context Landmarks
    landmarks = [
        (125.325, 43.918, "长春站"),
        (125.323, 43.901, "胜利公园"),
        (125.362, 43.905, "伊通河沿岸公园")
    ]
    for lon, lat, name in landmarks:
        lx, ly = get_xy(lon, lat)
        ax_map.plot(lx, ly, marker='o', color='#64748B', markersize=4.5, markeredgecolor='#FFFFFF', markeredgewidth=1.0, zorder=3.3)
        ax_map.text(lx, ly - 35, name, color='#64748B', ha='center', va='top', fontproperties=_font(font_prop, 9, "bold"), path_effects=pe, zorder=3.4)

    # 4. Legend Card (X: 101.5 to 139.4, Y: 67.0 to 87.0)
    legend_shadow = mpatches.Rectangle((101.8, 66.7), 37.9, 20.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    legend_bg = mpatches.Rectangle((101.5, 67.0), 37.9, 20.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(legend_shadow)
    ax.add_patch(legend_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 85.8), 37.9, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(103.5, 82.8, "图例 / LEGEND", color='#D97706', ha='left', va='center',
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)
    
    legend_items_data = [
        ("规划研究范围", '#FF3B30', 'outline_boundary', 102.2, 106.2, 78.5),
        ("微创修缮核心", '#FEF3C7', 'rect_orange_solid', 120.7, 124.7, 78.5),
        ("光复路风貌廊道", '#D97706', 'line_solid', 102.2, 106.2, 74.0),
        ("邻里细胞盒 (500m)", '#D1FAE5', 'rect_green_solid', 120.7, 124.7, 74.0),
        ("适老慢行联络道", '#059669', 'line_dashed', 102.2, 106.2, 69.5)
    ]
    
    for label, color_code, style, x_sym, x_txt, y_val in legend_items_data:
        if style == 'outline_boundary':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='none', edgecolor=color_code, linewidth=1.8, zorder=4)
            ax.add_patch(rect)
        elif style == 'rect_orange_solid':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor=color_code, edgecolor='#D97706', linewidth=0.8, zorder=4)
            ax.add_patch(rect)
        elif style == 'rect_green_solid':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor=color_code, edgecolor='#059669', linewidth=0.8, zorder=4)
            ax.add_patch(rect)
        elif style == 'line_solid':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=3.0, zorder=4)
        elif style == 'line_dashed':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=2.0, linestyle='--', zorder=4)
            
        ax.text(x_txt, y_val, label, color='#334155', ha='left', va='center',
                fontproperties=_font(font_prop, 10.5), zorder=4)

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
    scale_rounded = round(scale_ratio / 500) * 500
    ax.text((x_start + x_end)/2, y_bar - 1.6, f"比例尺 1:{scale_rounded}", color='#334155', ha='center', va='center',
            fontproperties=_font(font_prop, 10.5, 'bold'), zorder=4)

    # 5. Description Card (X: 101.5 to 139.4, Y: 4.0 to 65.0)
    ax.add_patch(mpatches.Rectangle((101.8, 3.7), 37.9, 61.3, facecolor='#E2E8F0', edgecolor='none', zorder=1))
    ax.add_patch(mpatches.Rectangle((101.5, 4.0), 37.9, 61.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2))
    ax.add_patch(mpatches.Rectangle((101.5, 63.8), 37.9, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(103.5, 61.0, "设计策略解析 / THREE STRATEGIES", color='#D97706', ha='left', va='center',
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)
    
    desc_data = [
        ("1. 历史风貌微创修缮：在伪满皇宫外围 300m 缓冲带及光复路历史风貌廊道，构建本土地貌管控模型，保护并修复历史街区建筑肌理，延续城市文脉基因。", 55.0),
        ("2. 细胞级微更新：针对配套设施真空，在五个重点地块精准植入 500m 半径的“邻里细胞”服务圈，配置食堂、日托等公共设施以促进均等化。", 39.0),
        ("3. 慢行系统联络：以慢行联络道（绿色虚线）串联并缝合 5 个细胞的日常活动网络，打造高可达、有温度的适老日常交往街巷空间。", 23.0)
    ]
    for text, y_pos in desc_data:
        wrapped_desc = wrap_text(text, max_len=44)
        y_text = y_pos
        for line in wrapped_desc.split('\n'):
            ax.text(103.5, y_text, line, color='#334155', ha='left', va='center',
                    fontproperties=_font(font_prop, 15.0), zorder=4)
            y_text -= 3.2

        # Floating Windrose (Pure Black, 12.0 x 12.0) with soft white radial gradient backdrop
    try:
        from pathlib import Path as _Path

        import numpy as _np
        from PIL import Image as _PIL_Image
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
    ("微创修缮核心 (300m)", "rect_orange_fill"),
    ("光复路风貌廊道", "line_orange"),
    ("邻里细胞盒 (500m)", "rect_green_fill"),
    ("适老优先慢行联络道", "line_green_dashed")
]

description_lines = [
    "1. 历史风貌微创修缮：在伪满皇宫外围 300m 缓冲带及光复路历史风貌廊道，构建本土地貌管控模型，保护并修复历史街区建筑肌理，延续城市文脉基因。",
    "2. 细胞级微更新：针对配套设施真空，在五个重点地块精准植入 500m 半径的“邻里细胞”服务圈，配置食堂、日托等公共设施以促进均等化。",
    "3. 慢行系统联络：以慢行联络道（绿色虚线）串联并缝合 5 个细胞的日常活动网络，打造高可达、有温度的适老日常交往街巷空间。"
]
