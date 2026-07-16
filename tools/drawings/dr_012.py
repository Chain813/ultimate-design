from pathlib import Path

import geopandas as gpd
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from shapely.geometry import Point

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
def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    fig = ax.get_figure()
    
    # 1. Setup A3 Main Canvas Coordinates
    ax.set_facecolor("#F8FAFC")
    ax.set_xlim(0, 141.42)
    ax.set_ylim(0, 100)
    
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
    
    ax.text(3.5, 93.6, "道路交通现状图", 
            color='#0F172A', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=26), zorder=4)
    
    ax.text(3.5, 90.7, "展示规划研究区域现状道路网络层级结构，诊断骨架路网格局及交通设施分布特征。", 
            color='#334155', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=15.0), zorder=4)

    # 3. Giant Map Card Container (X: 2.0 to 100.0, Y: 4.0 to 87.0)
    map_shadow = mpatches.Rectangle((2.3, 3.7), 98.0, 83.0, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    map_bg = mpatches.Rectangle((2.0, 4.0), 98.0, 83.0, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(map_shadow)
    ax.add_patch(map_bg)
    
    # Sub-axes for GIS map (Centered inside the container)
    ax_map = fig.add_axes([3.0 / 141.42, 5.0 / 100.0, 96.0 / 141.42, 81.0 / 100.0], facecolor="#F8FAFC", zorder=3)
    ax_map.set_xlim(cx - view_w / 2, cx + view_w / 2)
    ax_map.set_ylim(cy - view_h / 2, cy + view_h / 2)
    ax_map.set_axis_off()
    ax_map.set_aspect("equal")

    # 3b. Plot GIS Layers on sub-axes
    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#D0E6F7", edgecolor="none", zorder=1.5)
        
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax_map, facecolor="none", edgecolor="#475569", linewidth=0.15, alpha=0.3, zorder=1)
        
    if roads is not None and not roads.empty:
        # Outer thick line (shadow/border)
        for lvl, lw, color in [(1, 4.5, "#1E3A8A"), (2, 3.5, "#2563EB"), (3, 2.0, "#60A5FA"), (4, 1.2, "#93C5FD")]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax_map, color=color, linewidth=lw, capstyle="round", joinstyle="round", zorder=3)
        # Inner line (glow/center)
        for lvl, lw, color in [(1, 3.0, "#3B82F6"), (2, 2.2, "#60A5FA"), (3, 1.0, "#EFF6FF"), (4, 0.6, "#FFFFFF")]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax_map, color=color, linewidth=lw, capstyle="round", joinstyle="round", zorder=4)
                
    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#1E293B", linewidth=1.8, linestyle=(0, (5, 5)), zorder=5)
        
    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=6)

    # Plot key landmarks on spatial map (High contrast dark text with white outline)
    labels = [
        ("伪满皇宫博物院", 125.3422, 43.9036),
        ("光复路", 125.3475, 43.9017),
        ("伊通河沿岸公园", 125.3590, 43.9010),
        ("长春站", 125.3250, 43.9080),
        ("胜利公园", 125.3260, 43.8960)
    ]
    for name, lon, lat in labels:
        x_pt, y_pt = get_xy(lon, lat)
        ax_map.text(x_pt, y_pt, name, color='#0F172A', ha='center', va='center',
                    fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=11),
                    path_effects=[path_effects.withStroke(linewidth=3, foreground='#FFFFFF')], zorder=7)

    # Floating Windrose (Pure Black, 12.0 x 12.0) with soft white radial gradient backdrop
    rose_path = ASSETS_DIR / "长春市风玫瑰.png"
    if rose_path.exists():
        try:
            ax_rose = fig.add_axes([87.0 / 141.42, 72.5 / 100.0, 12.0 / 141.42, 12.0 / 100.0], facecolor='none', zorder=4)
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

    # 4. Legend Card (X: 101.5 to 139.4, Y: 67.0 to 87.0)
    legend_shadow = mpatches.Rectangle((101.8, 66.7), 37.9, 20.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    legend_bg = mpatches.Rectangle((101.5, 67.0), 37.9, 20.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(legend_shadow)
    ax.add_patch(legend_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 85.8), 37.9, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(103.5, 83.8, "图例 / LEGEND", color='#D97706', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13.5), zorder=4)
    
    # 6 Legend Items in a 2 columns x 3 rows grid
    legend_items_data = [
        # Row 0
        ("规划研究范围", '#FF3B30', 'outline_boundary', 102.2, 106.2, 80.5),
        ("城市主干路", '#3B82F6', 'line_thick', 120.7, 124.7, 80.5),
        # Row 1
        ("城市次干路", '#60A5FA', 'line_med', 102.2, 106.2, 76.5),
        ("城市支路", '#93C5FD', 'line_thin', 120.7, 124.7, 76.5),
        # Row 2
        ("现状铁路线", '#1E293B', 'line_rail', 102.2, 106.2, 72.5),
        ("现状建筑轮廓", '#475569', 'rect_outline', 120.7, 124.7, 72.5)
    ]
    
    for label, color_code, style, x_sym, x_txt, y_val in legend_items_data:
        if style == 'outline_boundary':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='none', edgecolor=color_code, linewidth=1.8, zorder=4)
            ax.add_patch(rect)
        elif style == 'rect_outline':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='none', edgecolor=color_code, linewidth=0.6, alpha=0.7, zorder=4)
            ax.add_patch(rect)
        elif style == 'line_thick':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color='#1E3A8A', linewidth=3.5, solid_capstyle='round', zorder=4)
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=2.0, solid_capstyle='round', zorder=5)
        elif style == 'line_med':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color='#2563EB', linewidth=2.5, solid_capstyle='round', zorder=4)
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=1.5, solid_capstyle='round', zorder=5)
        elif style == 'line_thin':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color='#60A5FA', linewidth=1.5, solid_capstyle='round', zorder=4)
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=0.8, solid_capstyle='round', zorder=5)
        elif style == 'line_rail':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=1.5, linestyle='--', zorder=4)
            
        ax.text(x_txt, y_val, label, color='#334155', ha='left', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], size=10.5), zorder=4)

    # 4b. Draw line-shaped scale bar centered inside the bottom row of the Legend Card
    scale_len = 500 / (view_w / 96.0) # Length in main axes units
    x_start = 120.45 - scale_len / 2
    x_end = x_start + scale_len
    y_bar = 69.2
    ax.plot([x_start, x_end], [y_bar, y_bar], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_start, x_start], [68.4, 70.0], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_start + scale_len/2, x_start + scale_len/2], [68.4, 70.0], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_end, x_end], [68.4, 70.0], color='#0F172A', linewidth=1.5, zorder=4)
    
    # Scale text labels (size 10.0)
    ax.text(x_start, 71.0, "0", color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.0), zorder=4)
    ax.text(x_start + scale_len/2, 71.0, "250m", color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.0), zorder=4)
    ax.text(x_end, 71.0, "500m", color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.0), zorder=4)
    
    scale_ratio = view_w / 0.31968
    scale_rounded = round(scale_ratio / 500) * 500
    ax.text((x_start + x_end)/2, 67.8, f"比例尺 1:{scale_rounded}", color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.5, weight='bold'), zorder=4)

    # 5. Description Card (X: 101.5 to 139.4, Y: 4.0 to 65.0)
    desc_shadow = mpatches.Rectangle((101.8, 3.7), 37.9, 61.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    desc_bg = mpatches.Rectangle((101.5, 4.0), 37.9, 61.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(desc_shadow)
    ax.add_patch(desc_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 63.8), 37.9, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(103.5, 61.0, "数据来源与诊断说明 / DATA SOURCES", color='#D97706', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13.5), zorder=4)
    
    # 3 Bullet description items wrapped at 44 visual-width units, font size 15.0
    desc_data = [
        ("1. 骨架路网：规划区以亚泰快速路、长白路为主干路网，呈现“宽马路、疏路网”格局，主干路宽度达40-50m，但次干路与支路严重不足，连通度低。", 55.0),
        ("2. 割裂严重：中部京哈铁路与西侧亚泰高架高强度割裂街区，南北及东西向连通度极差，现状交通设施及场站用地仅占2.6%，停车泊位缺口大。", 39.0),
        ("3. 支路瓶颈：现状支路网密度偏低且多为断头路，微循环不畅，步行环境与老旧小区机非混行严重，亟需通过增设12-15m级社区支路进行路网缝合。", 23.0)
    ]
    for text, y_pos in desc_data:
        wrapped_desc = wrap_text(text, max_len=44)
        y_text = y_pos
        for line in wrapped_desc.split('\n'):
            ax.text(103.5, y_text, line, color='#334155', ha='left', va='center',
                    fontproperties=fm.FontProperties(family=font_prop['family'], size=15.0), zorder=4)
            y_text -= 3.2

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("城市主干路", "line_primary_road_blue"),
    ("城市次干路", "line_secondary_road_blue"),
    ("城市支路", "line_tertiary_road_blue"),
    ("现状铁路线", "line_rail"),
    ("现状建筑轮廓", "rect_building_outline"),
]

description_lines = [
    "1. 骨架路网：规划区以亚泰快速路、长白路为主干路网，呈现“宽马路、疏路网”格局，主干路宽度达40-50m，但次干路与支路严重不足，连通度低。",
    "2. 割裂严重：中部京哈铁路与西侧亚泰高架高强度割裂街区，南北及东西向连通度极差，现状交通设施及场站用地仅占2.6%，停车泊位缺口大。",
    "3. 支路瓶颈：现状支路网密度偏低且多为断头路，微循环不畅，步行环境与老旧小区机非混行严重，亟需通过增设12-15m级社区支路进行路网缝合。"
]