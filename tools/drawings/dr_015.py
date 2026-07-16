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
from shapely.ops import unary_union

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
    
    ax.text(3.5, 93.6, "环境品质问题地图", 
            color='#0F172A', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=26), zorder=4)
    
    ax.text(3.5, 90.7, "识别街区绿化品质瓶颈、城市边界物理割裂与多层级交通噪声声污染带，诊断环境品质提升痛点。", 
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

    # 3b. Plot GIS Base Layers on sub-axes (drawn light to highlight noise overlays)
    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#E2F0FD", edgecolor="none", zorder=1)
        
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax_map, facecolor="#F1F5F9", edgecolor="#CBD5E1", linewidth=0.2, alpha=0.7, zorder=0.8)

    # 3c. Calculate Noise Buffers and merge them into non-overlapping geometries
    # Railway (120m) & Level 1 Roads (80m)
    rail_buf = rails.geometry.buffer(120).unary_union if (rails is not None and not rails.empty) else None
    
    sub_gdf_1 = roads[roads['level'] == 1] if (roads is not None and not roads.empty) else None
    sub_gdf_2 = roads[roads['level'] == 2] if (roads is not None and not roads.empty) else None
    sub_gdf_3 = roads[roads['level'] == 3] if (roads is not None and not roads.empty) else None
    
    buf_1 = sub_gdf_1.geometry.buffer(80).unary_union if (sub_gdf_1 is not None and not sub_gdf_1.empty) else None
    buf_2 = sub_gdf_2.geometry.buffer(50).unary_union if (sub_gdf_2 is not None and not sub_gdf_2.empty) else None
    buf_3 = sub_gdf_3.geometry.buffer(30).unary_union if (sub_gdf_3 is not None and not sub_gdf_3.empty) else None
    
    strong_geoms = []
    if rail_buf is not None:
        strong_geoms.append(rail_buf)
    if buf_1 is not None:
        strong_geoms.append(buf_1)
        
    strong_noise = unary_union(strong_geoms) if strong_geoms else None
    
    med_noise = None
    if buf_2 is not None:
        med_noise = buf_2.difference(strong_noise) if strong_noise is not None and not strong_noise.is_empty else buf_2
            
    light_noise = None
    if buf_3 is not None:
        exclude = None
        if strong_noise is not None and med_noise is not None:
            exclude = strong_noise.union(med_noise)
        elif strong_noise is not None:
            exclude = strong_noise
        elif med_noise is not None:
            exclude = med_noise
            
        light_noise = buf_3.difference(exclude) if exclude is not None and not exclude.is_empty else buf_3

    # Plot Noise Buffers sequentially (Tiers 1, 2, 3)
    if strong_noise is not None and not strong_noise.is_empty:
        gpd.GeoSeries([strong_noise], crs=roads.crs).plot(
            ax=ax_map, facecolor="#FECACA", edgecolor="#EF4444", alpha=0.35, hatch="//", zorder=1.5)
            
    if med_noise is not None and not med_noise.is_empty:
        gpd.GeoSeries([med_noise], crs=roads.crs).plot(
            ax=ax_map, facecolor="#FED7AA", edgecolor="#F97316", alpha=0.25, linestyle="--", zorder=1.4)
            
    if light_noise is not None and not light_noise.is_empty:
        gpd.GeoSeries([light_noise], crs=roads.crs).plot(
            ax=ax_map, facecolor="#FEF08A", edgecolor="#CA8A04", alpha=0.20, linestyle=":", zorder=1.3)

    # 3d. Plot Road network layers on top of buffers
    if roads is not None and not roads.empty:
        for lvl, lw, color in [(1, 2.2, "#475569"), (2, 1.6, "#64748B"), (3, 1.1, "#94A3B8"), (4, 0.7, "#CBD5E1")]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax_map, color=color, linewidth=lw, capstyle="round", joinstyle="round", zorder=2.0)
                
    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#1E293B", linewidth=1.5, linestyle=(0, (5, 5)), zorder=2.5)

    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=5.0)

    # 3e. Environmental problem points (low GVI, street blockages, parking chaos)
    problem_pts = [
        ("低绿视率段 (GVI < 10%)", 125.3312, 43.9056),
        ("低绿视率段 (GVI < 10%)", 125.3482, 43.9026),
        ("街角消极空间", 125.3375, 43.9075),
        ("现状停车混乱节点", 125.3432, 43.9052),
        ("人行道破损严重段", 125.3348, 43.9042),
        ("中车厂区围墙割裂点", 125.3401, 43.9079),
    ]

    for name, lon, lat in problem_pts:
        px_p, py_p = get_xy(lon, lat)
        
        # White background circular shield for visibility on noisy backgrounds
        ax_map.plot(px_p, py_p, marker='o', markersize=14.0, color='#FFFFFF', alpha=0.9, zorder=5.7)
        # Red triangle marker
        ax_map.plot(px_p, py_p, marker='^', markersize=9.5, color='#EF4444', markeredgecolor='#FFFFFF', markeredgewidth=1.2, zorder=6.0)
        
        # High contrast red label with thick white path effects outline
        txt = ax_map.text(px_p, py_p + 60, name, color='#991B1B', ha='center', va='bottom',
                          fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=11.0), zorder=6.5)
        txt.set_path_effects([path_effects.withStroke(linewidth=3.0, foreground='#FFFFFF')])

    # Plot general landmarks for consistent location context
    labels = [
        ("伪满皇宫博物院", 125.3422, 43.9036),
        ("光复路", 125.3475, 43.9017),
        ("伊通河沿岸公园", 125.3590, 43.9010),
        ("长春站", 125.3250, 43.9080),
        ("胜利公园", 125.3260, 43.8960)
    ]
    for name, lon, lat in labels:
        x_pt, y_pt = get_xy(lon, lat)
        ax_map.text(x_pt, y_pt, name, color='#475569', ha='center', va='bottom',
                    fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=9.5),
                    path_effects=[path_effects.withStroke(linewidth=2.5, foreground='#FFFFFF')], zorder=5.8)

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
        ("中度噪声带 (50m)", '#F97316', 'orange_buffer', 120.7, 124.7, 80.5),
        # Row 1
        ("重度噪声带 (Tier 1)", '#EF4444', 'red_hatch_buffer', 102.2, 106.2, 76.5),
        ("轻度噪声带 (Tier 3)", '#CA8A04', 'yellow_buffer', 120.7, 124.7, 76.5),
        # Row 2
        ("现状交通道路", '#94A3B8', 'grey_line', 102.2, 106.2, 72.5),
        ("品质瓶颈与乱点", '#EF4444', 'red_triangle', 120.7, 124.7, 72.5)
    ]
    
    for label, color_code, style, x_sym, x_txt, y_val in legend_items_data:
        if style == 'outline_boundary':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='none', edgecolor=color_code, linewidth=1.8, zorder=4)
            ax.add_patch(rect)
        elif style == 'red_hatch_buffer':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='#FECACA', edgecolor=color_code, linewidth=1.2, hatch='//', zorder=4)
            ax.add_patch(rect)
        elif style == 'orange_buffer':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='#FED7AA', edgecolor=color_code, linewidth=1.2, linestyle='--', zorder=4)
            ax.add_patch(rect)
        elif style == 'yellow_buffer':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='#FEF08A', edgecolor=color_code, linewidth=1.2, linestyle=':', zorder=4)
            ax.add_patch(rect)
        elif style == 'grey_line':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=1.8, zorder=4)
        elif style == 'red_triangle':
            # White background circular glow
            ax.plot(x_sym + 1.5, y_val, marker='o', markersize=9.0, color='#FFFFFF', alpha=0.9, zorder=4)
            ax.plot(x_sym + 1.5, y_val, marker='^', markersize=6.0, color=color_code, markeredgecolor='#FFFFFF', markeredgewidth=0.5, zorder=5)
            
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
    
    ax.text(103.5, 61.0, "环境品质诊断说明 / DIAGNOSIS", color='#D97706', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13.5), zorder=4)
    
    # 3 Bullet description items wrapped at 44 visual-width units, font size 15.0
    desc_data = [
        ("1. 噪声影响：京哈铁路线与亚泰快速路等高负荷骨干路网对两侧产生严重声污染与物理割裂，铁路影响宽达120米，快速路及主干路分别产生80米与50米交通噪声带。", 55.0),
        ("2. 绿化品质：基于街景图像定量评估，街区平均绿视率（GVI）仅为8.7%，且78.3%的采样点低于15%的最低宜居阈值，环境呈现重度硬质化。", 39.0),
        ("3. 街面无序：老旧小区周边机动车乱停乱放严重，人行道多处破损，宽城子、中车厂区等大面积围墙导致步行系统断档、存在消极死角。", 23.0)
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
    ("铁路与快速路重度噪声带 (Tier 1)", "rect_noise_zone"),
    ("主干路中度噪声带 (Tier 2)", "rect_orange_buffer"),
    ("次干路轻度噪声带 (Tier 3)", "rect_yellow_buffer"),
    ("环境品质瓶颈/乱点", "marker_problem"),
]

description_lines = [
    "1. 噪声影响：京哈铁路线与亚泰快速路等高负荷骨干路网对两侧产生严重声污染与物理割裂，铁路影响宽达120米，快速路及主干路分别产生80米与50米交通噪声带。",
    "2. 绿化品质：基于街景图像定量评估，街区平均绿视率（GVI）仅为8.7%，且78.3%的采样点低于15%的最低宜居阈值，环境呈现重度硬质化。",
    "3. 街面无序：老旧小区周边机动车乱停乱放严重，人行道多处破损，宽城子、中车厂区等大面积围墙导致步行系统断档、存在消极死角。"
]