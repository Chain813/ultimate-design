# -*- coding: utf-8 -*-
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patheffects as path_effects
import matplotlib.patches as mpatches
import geopandas as gpd

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
    
    ax.text(3.5, 93.6, "五地块深化设计总图", 
            color='#0F172A', ha='left', va='center',
            fontproperties=_font(font_prop, 26, "bold"), zorder=4)
    
    ax.text(3.5, 90.7, "重点更新地段详细设计导则，指导具体地块按刚性指标与功能定位要求实施织补与功能活化。", 
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
        buildings.plot(ax=ax_map, facecolor="#F8FAFC", edgecolor="#94A3B8", linewidth=0.35, zorder=2.0)

    # Plot roads with detailed levels
    if roads is not None and not roads.empty:
        for lvl, lw, color in [(1, 1.8, "#94A3B8"), (2, 1.2, "#CBD5E1"), (3, 0.7, "#E2E8F0"), (4, 0.5, "#F1F5F9")]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax_map, color=color, linewidth=lw, capstyle="round", joinstyle="round", zorder=3.5)

    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#64748B", linewidth=1.2, linestyle=(0, (5, 5)), zorder=3.6)

    # Color 5 key plots with distinct colors and label with indicators from thesis
    plot_info = [
        ("御花园东巷文创街区", "3.71ha · FAR≤1.3 · 绿地率≥38%", "#F59E0B"), # Index 0: 老水产
        ("活态市集·风味院落", "16.83ha · FAR≤1.4 · 绿地率≥35%", "#EF4444"), # Index 1: 食品调料
        ("全龄共享生活社区", "2.78ha · FAR≤1.3 · 绿地率≥35%", "#22C55E"), # Index 2: 一中北
        ("历史界面缝合者", "2.47ha · FAR≤1.3 · 绿地率≥35%", "#8B5CF6"), # Index 3: 清禾
        ("宽城子能量花园", "1.30ha · FAR≤0.2 · 绿地率≥80%", "#3B82F6"), # Index 4: 石油
    ]

    if key_plots is not None and not key_plots.empty:
        for idx, row in key_plots.iterrows():
            if idx < len(plot_info):
                name, indicators, color = plot_info[idx]
            else:
                name, indicators, color = f"地块{idx+1}", "", "#94A3B8"
            
            gpd.GeoSeries([row.geometry]).plot(ax=ax_map, facecolor=color, edgecolor="#1E293B",
                                               linewidth=2.0, alpha=0.75, zorder=3.8)
            geom = row.geometry
            cx_p, cy_p = geom.centroid.x, geom.centroid.y
            
            # Name label
            txt1 = ax_map.text(cx_p, cy_p + 30, name, color='#FFFFFF', ha='center', va='bottom',
                               fontproperties=_font(font_prop, 11, 'bold'), zorder=5)
            txt1.set_path_effects([path_effects.withStroke(linewidth=3, foreground='#000000')])
            
            # Indicator label
            txt2 = ax_map.text(cx_p, cy_p - 30, indicators, color='#FFFFFF', ha='center', va='top',
                               fontproperties=_font(font_prop, 8.5), zorder=5)
            txt2.set_path_effects([path_effects.withStroke(linewidth=2, foreground='#000000')])

    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=5)

    # Landmark labels with white outline stroke shadows
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

    # 4. Legend Card (X: 101.5 to 139.4, Y: 57.0 to 87.0)
    leg_y_min = 57.0
    leg_height = 30.0
    legend_shadow = mpatches.Rectangle((101.8, leg_y_min - 0.3), 37.9, leg_height, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    legend_bg = mpatches.Rectangle((101.5, leg_y_min), 37.9, leg_height, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(legend_shadow)
    ax.add_patch(legend_bg)
    ax.add_patch(mpatches.Rectangle((101.5, leg_y_min + leg_height - 1.2), 37.9, 1.2, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(103.5, leg_y_min + leg_height - 3.2, "图例 / LEGEND", color='#D97706', ha='left', va='center',
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)
    
    legend_items_data = [
        # Row 0
        ("规划研究范围", '#FF3B30', 'outline_boundary', 102.2, 106.2, 79.5),
        ("现状城市道路", '#CBD5E1', 'line', 120.7, 124.7, 79.5),
        # Row 1
        ("御花园东巷文创街区", '#F59E0B', 'rect_solid', 102.2, 106.2, 75.8),
        ("全龄共享生活社区", '#22C55E', 'rect_solid', 120.7, 124.7, 75.8),
        # Row 2
        ("活态市集·风味院落", '#EF4444', 'rect_solid', 102.2, 106.2, 72.1),
        ("历史界面缝合者", '#8B5CF6', 'rect_solid', 120.7, 124.7, 72.1),
        # Row 3
        ("宽城子能量花园", '#3B82F6', 'rect_solid', 102.2, 106.2, 68.4)
    ]
    
    for label, color_code, style, x_sym, x_txt, y_val in legend_items_data:
        if style == 'outline_boundary':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='none', edgecolor=color_code, linewidth=1.8, zorder=4)
            ax.add_patch(rect)
        elif style == 'rect_solid':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor=color_code, edgecolor='#1E293B', linewidth=0.5, zorder=4)
            ax.add_patch(rect)
        elif style == 'line':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=2.0, zorder=4)
            
        ax.text(x_txt, y_val, label, color='#334155', ha='left', va='center',
                fontproperties=_font(font_prop, 10.5), zorder=4)

    # Scale Bar (centered under Legend Card)
    y_bar = 61.5
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

    # 5. Description Card (X: 101.5 to 139.4, Y: 4.0 to 55.0)
    desc_shadow = mpatches.Rectangle((101.8, 3.7), 37.9, 51.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    desc_bg = mpatches.Rectangle((101.5, 4.0), 37.9, 51.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(desc_shadow)
    ax.add_patch(desc_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 53.8), 37.9, 1.2, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(103.5, 51.2, "设计说明与规划指标 / DESCRIPTION", color='#D97706', ha='left', va='center',
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)
    
    desc_data = [
        ("1. 地块概况：5个重点更新地块总面积约27.09公顷，均以《伪满皇宫保护规划》建控地带内容积率≤1.4、建筑密度≤28%、绿地率≥30%及限高18米为刚性约束。", 45.0),
        ("2. 差异策略：老水产批发市场定位'御花园东巷文创街区'(FAR≤1.3)；食品调料市场采用'一核两带三组团'(FAR≤1.4)；石油公司以'能量花园'概念完全开放(FAR≤0.2，绿地率达85%)。", 29.0),
        ("3. 指标管控：各地块绿地率均超过35%（能量花园达85%），满足且优于保护规划要求；建筑高度主动控制在18米以下，确保与历史天际线协调。", 13.0)
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
    ("老水产批发市场 (3.71ha)", "rect_style_orange"),
    ("市一中北侧 (2.78ha)", "rect_style_green"),
    ("食品调料市场 (16.83ha)", "rect_height_red"),
    ("清禾市场 (2.47ha)", "rect_purple_fill"),
    ("石油公司 (1.30ha)", "rect_style_blue"),
]

description_lines = [
    "1. 地块概况：5个重点更新地块总面积约27.09公顷，均以《伪满皇宫保护规划》建控地带内容积率≤1.4、建筑密度≤28%、绿地率≥30%及限高18米为刚性约束。",
    "2. 差异策略：老水产批发市场定位'御花园东巷文创街区'(FAR≤1.3)；食品调料市场采用'一核两带三组团'(FAR≤1.4)；石油公司以'能量花园'概念完全开放(FAR≤0.2，绿地率达85%)。",
    "3. 指标管控：各地块绿地率均超过35%（能量花园达85%），满足且优于保护规划要求；建筑高度主动控制在18米以下，确保与历史天际线协调。"
]
