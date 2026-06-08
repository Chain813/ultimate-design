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
    
    ax.text(3.5, 93.6, "实施分期图", 
            color='#0F172A', ha='left', va='center',
            fontproperties=_font(font_prop, 26, "bold"), zorder=4)
    
    ax.text(3.5, 90.7, "科学统筹更新时序，制定近期启动、中期推进与远期展望分期开发计划，保障民生项目先行。", 
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

    # Color 5 key plots by phasing
    plot_stages = [
        # (phase_num, phase_label, stage_color)
        (1, "近期", "#22C55E"), # index 0: 老水产
        (1, "近期", "#22C55E"), # index 1: 一中北
        (3, "远期", "#A855F7"), # index 2: 食品市场
        (2, "中期", "#3B82F6"), # index 3: 清禾市场
        (2, "中期", "#3B82F6"), # index 4: 石油公司
    ]

    if key_plots is not None and not key_plots.empty:
        for idx, row in key_plots.iterrows():
            if idx < len(plot_stages):
                p_num, p_lbl, p_color = plot_stages[idx]
            else:
                p_num, p_lbl, p_color = 2, "中期", "#3B82F6"
            
            gpd.GeoSeries([row.geometry]).plot(ax=ax_map, facecolor=p_color, edgecolor="#1E293B",
                                               linewidth=2.0, alpha=0.85, zorder=3.8)
            geom = row.geometry
            cx_p, cy_p = geom.centroid.x, geom.centroid.y
            
            p_name = row.get('name', f"地块{idx+1}")
            # Label
            txt = ax_map.text(cx_p, cy_p, f"阶段 {p_num}\n({p_name})", color='#FFFFFF', ha='center', va='center',
                              fontproperties=_font(font_prop, 11, 'bold'), zorder=5)
            txt.set_path_effects([path_effects.withStroke(linewidth=3, foreground='#1E293B')])

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
    
    legend_items_data = [
        # Row 0
        ("规划研究范围", '#FF3B30', 'outline_boundary', 102.2, 106.2, 79.5),
        ("现状城市道路", '#CBD5E1', 'line', 120.7, 124.7, 79.5),
        # Row 1
        ("近期项目 (1-3年)", '#22C55E', 'rect_solid', 102.2, 106.2, 75.0),
        ("中期项目 (3-5年)", '#3B82F6', 'rect_solid', 120.7, 124.7, 75.0),
        # Row 2
        ("远期项目 (5-10年)", '#A855F7', 'rect_solid', 102.2, 106.2, 70.5)
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
    y_bar = 65.5
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
    
    desc_data = [
        ("1. 近期建设（1-3年）：优先启动水产批发市场及食品调料市场地块（绿色区），彻底拆除违章低效棚户区，配置邻里细胞生活盒子，缓解民生痛点。", 50.0),
        ("2. 中期推进（3-5年）：推进中车工业遗存活化区与光复路历史风貌带（蓝色区），将闲置旧厂房改建为数智文创街区，并打通东九、东十条瓶颈支路。", 34.0),
        ("3. 远期展望（5-10年）：实施清禾市场及石油公司周边低效老旧住宅微更新项目（紫色区），通过局部针灸织补，彻底完成全域公共绿地率35%的覆盖目标。", 18.0)
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
    ("近期实施项目 (1-3年)", "rect_phase_green"),
    ("中期实施项目 (3-5年)", "rect_phase_blue"),
    ("远期实施项目 (5-10年)", "rect_phase_purple")
]

description_lines = [
    "1. 近期建设（1-3年）：优先启动水产批发市场及食品调料市场地块（绿色区），彻底拆除违章低效棚户区，配置邻里细胞生活盒子，缓解民生痛点。",
    "2. 中期推进（3-5年）：推进中车工业遗存活化区与光复路历史风貌带（蓝色区），将闲置旧厂房改建为数智文创街区，并打通东九、东十条瓶颈支路。",
    "3. 远期展望（5-10年）：实施清禾市场及石油公司周边低效老旧住宅微更新项目（紫色区），通过局部针灸织补，彻底完成全域公共绿地率35%的覆盖目标。"
]