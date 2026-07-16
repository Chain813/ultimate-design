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
def approx_closeness(graph, k=300, weight='weight', seed=42):
    import random

    import networkx as nx
    random.seed(seed)
    nodes = list(graph.nodes())
    if len(nodes) <= k:
        return nx.closeness_centrality(graph, distance=weight)
    sampled_sources = random.sample(nodes, k)
    path_lengths = {}
    for s in sampled_sources:
        lengths = nx.single_source_dijkstra_path_length(graph, s, weight=weight)
        path_lengths[s] = lengths
    cl_dict = {}
    for u in nodes:
        sum_d = 0
        count = 0
        for s in sampled_sources:
            d = path_lengths[s].get(u, None)
            if d is not None and d > 0:
                sum_d += d
                count += 1
        cl_dict[u] = count / sum_d if sum_d > 0 else 0
    return cl_dict

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop, *args, **kwargs):
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
    
    ax.text(3.5, 93.6, "空间句法可达性分析图", 
            color='#0F172A', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=26), zorder=4)
    
    ax.text(3.5, 90.7, "基于空间句法轴线理论测算全局整合度（Integration），剖析街区人流可达性及步行微循环瓶颈。", 
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

    # 3b. Plot GIS Base Layers on sub-axes
    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#E2F0FD", edgecolor="none", zorder=1)
        
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax_map, facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=0.2, zorder=0.8)
        
    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#64748B", linewidth=1.2, linestyle=(0, (5, 5)), zorder=3)

    # Load pre-calculated space syntax road network directly from road_syntax.geojson
    # to match the high-quality 3D digital twin presentation logic
    roads_copy = None
    syntax_path = STATIC_DIR / "road_syntax.geojson"
    if syntax_path.exists():
        try:
            roads_copy = gpd.read_file(syntax_path)
            if roads_copy.crs != boundary.crs:
                roads_copy = roads_copy.to_crs(boundary.crs)
            
            # Plot the roads colored by integration (Spectral colormap: red=high, blue=low)
            roads_copy.plot(ax=ax_map, column='integration_norm', cmap='Spectral_r', linewidth=2.8, zorder=4)
        except Exception as e:
            print(f"Error loading road_syntax.geojson: {e}")

    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=5)

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

    # Inset Synergy scatter plot directly onto the layout! (X: 4.5 to 29.5, Y: 6.5 to 25.5 on ax)
    if roads_copy is not None:
        try:
            inset_bg = mpatches.Rectangle((4.5, 6.5), 25.0, 19.0, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.0, alpha=0.9, zorder=5)
            ax.add_patch(inset_bg)
            
            ax_synergy = fig.add_axes([5.5 / 141.42, 7.5 / 100.0, 23.0 / 141.42, 17.0 / 100.0], facecolor="#FFFFFF", zorder=6)
            x_v = roads_copy['integration_norm'].values
            y_v = roads_copy['choice_norm'].values
            valid = (x_v > 0) & (y_v > 0)
            if np.any(valid):
                  x_vals = x_v[valid]
                  y_vals = y_v[valid]
                  ax_synergy.scatter(x_vals, y_vals, color='#3B82F6', alpha=0.5, s=6, zorder=2)
                  m, b_val = np.polyfit(x_vals, y_vals, 1)
                  r_matrix = np.corrcoef(x_vals, y_vals)
                  r_sq = r_matrix[0, 1]**2 if r_matrix.shape == (2, 2) else 0
                  x_fit = np.linspace(min(x_vals), max(x_vals), 100)
                  ax_synergy.plot(x_fit, m*x_fit + b_val, color='#EF4444', linewidth=1.5, label=f'R²={r_sq:.2f}', zorder=3)
                  ax_synergy.legend(loc='upper left', fontsize=7, framealpha=0.6)
            ax_synergy.set_title("协同度分析 (Synergy)", fontsize=8, fontweight='bold', family=font_prop['family'], color='#0F172A')
            ax_synergy.set_xlabel("全局整合度 (Rn)", fontsize=6.5, family=font_prop['family'], color='#475569')
            ax_synergy.set_ylabel("全局选择度 (Choice)", fontsize=6.5, family=font_prop['family'], color='#475569')
            ax_synergy.tick_params(axis='both', which='both', labelsize=6)
            ax_synergy.grid(True, linestyle='--', alpha=0.2)
        except Exception as e:
            print(f"Error drawing synergy inset plot: {e}")

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
        ("高整合度 (Rn)", '#EF4444', 'line_high', 120.7, 124.7, 80.5),
        # Row 1
        ("中等整合度", '#FDAE61', 'line_med', 102.2, 106.2, 76.5),
        ("低整合度", '#3288BD', 'line_low', 120.7, 124.7, 76.5),
        # Row 2
        ("现状铁路线", '#64748B', 'line_rail', 102.2, 106.2, 72.5),
        ("现状建筑轮廓", '#CBD5E1', 'rect_outline', 120.7, 124.7, 72.5)
    ]
    
    for label, color_code, style, x_sym, x_txt, y_val in legend_items_data:
        if style == 'outline_boundary':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='none', edgecolor=color_code, linewidth=1.8, zorder=4)
            ax.add_patch(rect)
        elif style == 'rect_outline':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='#F8FAFC', edgecolor=color_code, linewidth=0.6, zorder=4)
            ax.add_patch(rect)
        elif style == 'line_high':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=2.8, solid_capstyle='round', zorder=4)
        elif style == 'line_med':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=2.4, solid_capstyle='round', zorder=4)
        elif style == 'line_low':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=2.0, solid_capstyle='round', zorder=4)
        elif style == 'line_rail':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=1.2, linestyle='--', zorder=4)
            
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
        ("1. 全局整合：基于空间句法轴线分析，全局整合度呈“外高内低”凹陷特征，外围亚泰大街及长通路车行整合度最高，而内部历史风貌区核心严重塌陷。", 55.0),
        ("2. 步行可达：内部支路网缺失与铁轨物理割裂导致步行整合度极低，文旅人流难以从交通节点（长春站、伪满皇宫）渗透进老旧住宅社区内部。", 39.0),
        ("3. 协同度分析：协同度散点图 R² 拟合值较低，说明全局交通与局部慢行网络严重脱节，存在明显的“交通孤岛效应”，亟需打通内部支路以提升协同度。", 23.0)
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
    ("高整合度 (核心区/Red)", "line_syntax_high"),
    ("中等整合度 (Orange/Yellow)", "line_syntax_med"),
    ("低整合度 (外围/Blue)", "line_syntax_low"),
    ("现状铁路线", "line_rail"),
    ("现状建筑轮廓", "rect_building_light")
]

description_lines = [
    "1. 全局整合：基于空间句法轴线分析，全局整合度呈“外高内低”凹陷特征，外围亚泰大街及长通路车行整合度最高，而内部历史风貌区核心严重塌陷。",
    "2. 步行可达：内部支路网缺失与铁轨物理割裂导致步行整合度极低，文旅人流难以从交通节点（长春站、伪满皇宫）渗透进老旧住宅社区内部。",
    "3. 协同度分析：协同度散点图 $R^2$ 拟合值较低，说明全局交通与局部慢行网络严重脱节，存在明显的“交通孤岛效应”，亟需打通内部支路以提升协同度。"
]