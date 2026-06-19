# -*- coding: utf-8 -*-
from shapely.geometry import Point
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
    
    ax.text(3.5, 93.6, "建筑更新控制图", 
            color='#0F172A', ha='left', va='center',
            fontproperties=_font(font_prop, 26, "bold"), zorder=4)
    
    ax.text(3.5, 90.7, "对历史风貌建筑、普通住宅、工业厂房等分类实施控制与引导，落实最小干预与渐进式更新要求。", 
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
    water_gdf = water
    if (water_gdf is None or water_gdf.empty) and landuse is not None and not landuse.empty:
        water_gdf = landuse[landuse['Color'] == '#7FFFFF']
        
    if water_gdf is not None and not water_gdf.empty:
        water_gdf.plot(ax=ax_map, facecolor="#D0E6F7", edgecolor="none", zorder=3.0)
        
    if buildings is not None and not buildings.empty:
        buildings_copy = buildings.copy()
        # Distances to Palace
        px_palace, py_palace = get_xy(125.3422, 43.9036)
        palace_pt = Point(px_palace, py_palace)
        dists = buildings_copy.geometry.distance(palace_pt)

        # Fallback check for prop_style column to prevent KeyError
        prop_style_col = buildings_copy["prop_style"] if "prop_style" in buildings_copy.columns else pd.Series([""] * len(buildings_copy))
        conditions = [
            (prop_style_col == "historical") | (dists <= 150),
            (dists > 150) & (dists <= 450),
            (buildings_copy["geometry"].centroid.x < 125.335) | (buildings_copy["geometry"].centroid.x > 125.346),
            (dists > 450)
        ]
        # LLM-guided color overrides
        c = params.get("color_overrides", {}) if params else {}
        choices = [
            c.get("heritage_core", "#B45309"),   # 保护修缮: 历史核心 (古铜)
            c.get("transition_zone", "#F59E0B"),  # 整治提升: 过渡风貌 (橙黄)
            c.get("micro_update", "#10B981"),     # 微更新: 老社区修补 (绿)
            c.get("functional_replace", "#3B82F6") # 功能置换: 工业转型 (蓝)
        ]
        buildings_copy["color"] = np.select(conditions, choices, default="#F59E0B")
        buildings_copy.plot(ax=ax_map, color=buildings_copy["color"], edgecolor="#1E293B", linewidth=0.35, zorder=2.0)

    if key_plots is not None and not key_plots.empty:
        key_plots.plot(ax=ax_map, facecolor="#A855F7", edgecolor="#7E22CE", linewidth=1.5, alpha=0.45, zorder=2.2)

    if roads is not None and not roads.empty:
        for lvl, lw, color in [(1, 1.8, "#94A3B8"), (2, 1.2, "#CBD5E1"), (3, 0.7, "#E2E8F0"), (4, 0.5, "#F1F5F9")]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax_map, color=color, linewidth=lw, capstyle="round", joinstyle="round", zorder=3.5)

    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#64748B", linewidth=1.2, linestyle=(0, (5, 5)), zorder=3.6)

    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=5)

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
        ("重点更新地块", '#A855F7', 'rect_purple_solid', 120.7, 124.7, 80.5),
        # Row 1
        ("保护修缮区", '#B45309', 'rect_solid', 102.2, 106.2, 77.2),
        ("整治提升区", '#F59E0B', 'rect_solid', 120.7, 124.7, 77.2),
        # Row 2
        ("微更新区", '#10B981', 'rect_solid', 102.2, 106.2, 73.9),
        ("功能置换区", '#3B82F6', 'rect_solid', 120.7, 124.7, 73.9)
    ]
    
    for label, color_code, style, x_sym, x_txt, y_val in legend_items_data:
        if style == 'outline_boundary':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='none', edgecolor=color_code, linewidth=1.8, zorder=4)
            ax.add_patch(rect)
        elif style == 'rect_purple_solid':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor=color_code, edgecolor='#7E22CE', linewidth=0.8, alpha=0.45, zorder=4)
            ax.add_patch(rect)
        elif style == 'rect_solid':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor=color_code, edgecolor='none', zorder=4)
            ax.add_patch(rect)
            
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
        ("1. 保护修缮：对历史风貌建筑坚持最小干预，保留建筑原始结构与外墙肌理，严格控制周边景观小品色调以防风貌退化。", 50.0),
        ("2. 保存整治：对普通住宅以立面整治、增加外保温及整理管线为主，不破坏原住宅格局，实施渐进式微更新更新。", 34.0),
        ("3. 功能置换：对中车厂房大跨度空间进行结构加固与重组，置换为高附加值的文创展厅、艺术沙龙与科技孵化园。", 18.0)
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
    ("重点更新地块 (拆改建)", "rect_purple_fill"),
    ("历史保护核心 (保护修缮)", "rect_style_hist"),
    ("风貌敏感地带 (整治提升)", "rect_style_orange"),
    ("老旧住宅社区 (微更新)", "rect_style_green"),
    ("工业仓储遗存 (功能置换)", "rect_style_blue")
]

description_lines = [
    "1. 保护修缮：对历史风貌建筑坚持最小干预，保留建筑原始结构与外墙肌理，严格控制周边景观小品色调以防风貌退化。",
    "2. 保存整治：对普通住宅以立面整治、增加外保温及整理管线为主，不破坏原住宅格局，实施渐进式微更新更新。",
    "3. 功能置换：对中车厂房大跨度空间进行结构加固与重组，置换为高附加值的文创展厅、艺术沙龙与科技孵化园。"
]
