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
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"
GIS_DIR = ROOT / "data/gis"
ASSETS_DIR = ROOT / "assets"

# Bypasses the default A3 title frame
NO_FRAME = True

def wrap_text(text, max_len=44):
    wrapped_lines = []
    for part in text.split('\n'):
        current_line = []
        current_width = 0
        for char in part:
            # Chinese and full-width punctuation count as 2, ASCII characters count as 1
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
    
    # Teal top accent bar on the header card
    accent_bar = mpatches.Rectangle((2, 95.7), 136.8, 0.6, facecolor='#0D9488', edgecolor='none', zorder=3)
    ax.add_patch(accent_bar)
    
    ax.text(3.5, 93.6, "用地现状分析图", 
            color='#0F172A', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=26), zorder=4)
    
    ax.text(3.5, 90.7, "展示研究区域现状多类别城市土地利用的空间分布，剖析功能构成特征及用地配比结构关系。", 
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
    if landuse is not None and not landuse.empty:
        for color_hex, sub_df in landuse.groupby('Color'):
            sub_df.plot(ax=ax_map, facecolor=color_hex, edgecolor="#CBD5E1", linewidth=0.25, zorder=1)
            
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax_map, facecolor="none", edgecolor="#475569", linewidth=0.15, alpha=0.3, zorder=2)
        
    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#D0E6F7", edgecolor="none", zorder=2.5)
        
    if roads is not None and not roads.empty:
        roads.plot(ax=ax_map, color="#E2E8F0", linewidth=0.8, alpha=0.8, zorder=3)
        
    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#64748B", linewidth=1.0, linestyle=(0, (5, 5)), zorder=4)
        
    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=4)

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
                    path_effects=[path_effects.withStroke(linewidth=3, foreground='#FFFFFF')], zorder=5)

    # Floating Windrose (Pure Black, 12.0 x 12.0) with soft white radial gradient backdrop (Shifted slightly down)
    rose_path = ASSETS_DIR / "长春市风玫瑰.png"
    if rose_path.exists():
        try:
            ax_rose = fig.add_axes([87.0 / 141.42, 72.5 / 100.0, 12.0 / 141.42, 12.0 / 100.0], facecolor='none', zorder=4)
            ax_rose.set_axis_off()
            
            # Generate a beautiful soft white radial gradient background
            y_g, x_g = np.ogrid[-1:1:100j, -1:1:100j]
            r = np.sqrt(x_g**2 + y_g**2)
            alpha = np.clip(1.0 - r, 0, 1) * 0.50
            grad_img = np.ones((100, 100, 4))
            grad_img[..., 3] = alpha
            ax_rose.imshow(grad_img, zorder=0, extent=[0, 1, 0, 1], origin='lower')
            
            # Convert wind rose to pure black in memory
            rose_img = Image.open(rose_path).convert("RGBA")
            rose_data = np.array(rose_img)
            rose_data[..., 0] = 0
            rose_data[..., 1] = 0
            rose_data[..., 2] = 0
            black_rose_img = Image.fromarray(rose_data)
            
            ax_rose.imshow(black_rose_img, zorder=1)
        except Exception as e:
            print(f"Error loading wind rose: {e}")

    # 4. Legend Card (X: 101.5 to 139.4, Y: 67.0 to 87.0) — Compressed layout
    legend_shadow = mpatches.Rectangle((101.8, 66.7), 37.9, 20.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    legend_bg = mpatches.Rectangle((101.5, 67.0), 37.9, 20.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(legend_shadow)
    ax.add_patch(legend_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 85.8), 37.9, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(103.5, 83.8, "图例 / LEGEND", color='#D97706', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13.5), zorder=4)
    
    # 12 Legend Items arranged in a compact 3 columns x 4 rows grid
    # Column 0: X_sym = 102.2, X_txt = 105.7
    # Column 1: X_sym = 114.7, X_txt = 118.2
    # Column 2: X_sym = 127.2, X_txt = 130.7
    # Row Y: 81.2, 78.2, 75.2, 72.2
    legend_items_data = [
        # Row 0
        ("研究范围", '#FF3B30', 'outline', 102.2, 105.7, 81.2),
        ("居住用地 (R)", '#FFFF00', 'fill', 114.7, 118.2, 81.2),
        ("商业办公 (B)", '#E60000', 'fill', 127.2, 130.7, 81.2),
        # Row 1
        ("商业服务 (B)", '#FF7F00', 'fill', 102.2, 105.7, 78.2),
        ("工业用地 (M)", '#AA7855', 'fill', 114.7, 118.2, 78.2),
        ("交通场站 (S)", '#9C9C9C', 'fill', 127.2, 130.7, 78.2),
        # Row 2
        ("机场设施 (S)", '#686868', 'fill', 102.2, 105.7, 75.2),
        ("行政办公 (A)", '#FF7F7F', 'fill', 114.7, 118.2, 75.2),
        ("教育科研 (A)", '#FF7FFF', 'fill', 127.2, 130.7, 75.2),
        # Row 3
        ("医疗卫生 (A)", '#FF7FBF', 'fill', 102.2, 105.7, 72.2),
        ("体育文化 (A)", '#7FFFFF', 'fill', 114.7, 118.2, 72.2),
        ("公园绿地 (G)", '#38A800', 'fill', 127.2, 130.7, 72.2)
    ]
    
    for label, color_code, style, x_sym, x_txt, y_val in legend_items_data:
        if style == 'outline':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.8, facecolor='none', edgecolor=color_code, linewidth=1.8, zorder=4)
        else:
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.8, facecolor=color_code, edgecolor='#CBD5E1', linewidth=0.5, zorder=4)
        ax.add_patch(rect)
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
    
    # Scale text labels (size 10.5)
    ax.text(x_start, 71.0, "0", color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.0), zorder=4)
    ax.text(x_start + scale_len/2, 71.0, "250m", color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.0), zorder=4)
    ax.text(x_end, 71.0, "500m", color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.0), zorder=4)
    
    scale_ratio = view_w / 0.31968
    scale_rounded = int(round(scale_ratio / 500)) * 500
    ax.text((x_start + x_end)/2, 67.8, f"比例尺 1:{scale_rounded}", color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.5, weight='bold'), zorder=4)

    # 5. Description Card (X: 101.5 to 139.4, Y: 4.0 to 65.0) — Extended vertically!
    desc_shadow = mpatches.Rectangle((101.8, 3.7), 37.9, 61.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    desc_bg = mpatches.Rectangle((101.5, 4.0), 37.9, 61.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(desc_shadow)
    ax.add_patch(desc_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 63.8), 37.9, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(103.5, 61.0, "数据来源与诊断说明 / DATA SOURCES", color='#D97706', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13.5), zorder=4)
    
    # 3 Bullet description items wrapped at 44 visual-width units, font size 15.0 (matching DR-003/007 body text exactly)
    desc_data = [
        ("1. 用地构成：现状以居住（R）和商业服务（B）用地为主，集中于亚泰大街两侧，工业与仓储用地占比较低，多属中车工业遗存及待更新厂房设施。", 55.0),
        ("2. 功能分布：商业商务功能呈轴向分布，西部及南部以老旧居住街区为主，整体用地结构较为割裂，缺乏大尺度开敞公共绿地和社区公园。", 39.0),
        ("3. 结构特征：公共管理与公共服务（A）及绿地（G）配置零散，现状建设用地开发强度高、但混合度较低，未能形成完善的15分钟社区服务圈。", 23.0)
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
    ("居住用地 (R)", "rect_euluc_0"),
    ("商业办公 (B)", "rect_euluc_1"),
    ("商业服务业 (B)", "rect_euluc_2"),
    ("工业用地 (M)", "rect_euluc_3"),
    ("交通场站 (S)", "rect_euluc_4"),
    ("机场设施 (S)", "rect_euluc_5"),
    ("行政办公 (A)", "rect_euluc_6"),
    ("教育科研 (A)", "rect_euluc_7"),
    ("医疗卫生 (A)", "rect_euluc_8"),
    ("体育文化 (A)", "rect_euluc_9"),
    ("公园与绿地 (G)", "rect_euluc_10")
]

description_lines = [
    "1. 用地构成：现状以居住（R）和商业服务（B）用地为主，集中于亚泰大街两侧，工业与仓储用地占比较低，多属中车工业遗存及待更新厂房设施。",
    "2. 功能分布：商业商务功能呈轴向分布，西部及南部以老旧居住街区为主，整体用地结构较为割裂，缺乏大尺度开敞公共绿地和社区公园。",
    "3. 结构特征：公共管理与公共服务（A）及绿地（G）配置零散，现状建设用地开发强度高、但混合度较低，未能形成完善的15分钟社区服务圈。"
]