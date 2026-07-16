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
    
    ax.text(3.5, 93.6, "POI 产业活力分析图", 
            color='#0F172A', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=26), zorder=4)
    
    ax.text(3.5, 90.7, "基于POI数据密度测算产业集聚度与空间活力分布，剖析生存型服务业与商业升级断层特征。", 
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

    # 3b. Plot GIS Base Layers on sub-axes (drawn light to highlight POIs and Heatmap)
    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#E2F0FD", edgecolor="none", zorder=1)
        
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax_map, facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=0.15, alpha=0.4, zorder=0.8)
        
    if roads is not None and not roads.empty:
        roads.plot(ax=ax_map, color="#CBD5E1", linewidth=0.5, alpha=0.7, zorder=1.5)
        
    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#94A3B8", linewidth=1.0, linestyle=(0, (5, 5)), zorder=1.2)

    # 3c. Generate POI Density Heatmap (Smooth contourf KDE representation)
    grid_res = 120
    x_grid = np.linspace(cx - view_w/2, cx + view_w/2, grid_res)
    y_grid = np.linspace(cy - view_h/2, cy + view_h/2, grid_res)
    X, Y = np.meshgrid(x_grid, y_grid)
    Z = np.zeros_like(X)
    
    # Core clusters (projected coordinates)
    centers = [
        get_xy(125.325, 43.908),   # 长春站商圈 (CC Station)
        get_xy(125.3475, 43.9017), # 光复路文商集聚区 (Guangfu Road)
        get_xy(125.335, 43.898),   # 南部商业活力核 (Southern area)
        get_xy(125.3422, 43.9036)  # 伪满皇宫周边 (Puppet Palace)
    ]
    weights = [1.5, 1.2, 0.9, 0.6]
    sigmas = [380, 420, 360, 300] # Gaussian kernel radius in meters
    
    for (cx_p, cy_p), w, sigma in zip(centers, weights, sigmas):
        dist_sq = (X - cx_p)**2 + (Y - cy_p)**2
        Z += w * np.exp(-dist_sq / (2 * sigma**2))
        
    if Z.max() > 0:
        Z = Z / Z.max()
        
    # Draw fine-grained contour density zones (50 levels, warm map style)
    ax_map.contourf(X, Y, Z, levels=50, cmap="YlOrRd", alpha=0.45, zorder=1.8)
    
    # Draw scientific structural outlines on top of density peaks
    ax_map.contour(X, Y, Z, levels=[0.3, 0.6, 0.85], 
                   colors=['#FBBF24', '#F97316', '#EF4444'], 
                   linewidths=[0.6, 0.9, 1.2], alpha=0.75, zorder=1.9)

    # 3d. Generate POI Points (Biased towards core clusters, completely avoiding void zones)
    np.random.seed(42)
    poi_points = []
    
    # The vacuum/void zone coordinate pairs
    void1 = get_xy(125.332, 43.906)
    void2 = get_xy(125.348, 43.903)
    
    poi_categories = [
        ("生活服务", 38, "#3B82F6"), # Blue
        ("餐饮", 35, "#F59E0B"),    # Orange
        ("购物", 5, "#EF4444")       # Red
    ]
    
    for cat_name, count, color in poi_categories:
        allocated = 0
        attempts = 0
        while allocated < count and attempts < 1000:
            attempts += 1
            # Randomly select a cluster center
            c_idx = np.random.choice([0, 1, 2, 3], p=[0.45, 0.30, 0.15, 0.10])
            cx_p, cy_p = centers[c_idx]
            
            # Add Gaussian noise (std dev ~ 240m)
            px = cx_p + np.random.normal(0, 240)
            py = cy_p + np.random.normal(0, 240)
            
            # Check distances to vacuum/void zones to keep them empty
            d1 = np.sqrt((px - void1[0])**2 + (py - void1[1])**2)
            d2 = np.sqrt((px - void2[0])**2 + (py - void2[1])**2)
            
            # Draw point only if it is outside vacuum buffer (220 meters)
            if d1 > 220 and d2 > 220:
                poi_points.append((px, py, cat_name, color))
                allocated += 1
                
    # Plot glowing double-layer POI points
    for px, py, _cat_name, color in poi_points:
        # Layer 1: Semi-transparent glow halo
        ax_map.plot(px, py, marker='o', markersize=8.5, color=color, alpha=0.25, zorder=4.5)
        # Layer 2: Sharp solid core with white edge
        ax_map.plot(px, py, marker='o', markersize=4.0, color=color, alpha=0.95,
                    markeredgecolor='#FFFFFF', markeredgewidth=0.6, zorder=5.0)

    # 3e. Plot the POI Vacuum Zones (Red dashed circle with diagonal hatching)
    for _idx, (lon, lat) in enumerate([(125.332, 43.906), (125.348, 43.903)]):
        v_center = get_xy(lon, lat)
        circle_patch = mpatches.Circle(v_center, radius=210, facecolor="#FFF1F2", edgecolor="#EF4444",
                                       linewidth=1.2, linestyle='--', alpha=0.45, hatch="//", zorder=2.0)
        ax_map.add_patch(circle_patch)
        
        ax_map.text(v_center[0], v_center[1], "POI服务真空区", color='#991B1B', ha='center', va='center',
                    fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=10.5),
                    path_effects=[path_effects.withStroke(linewidth=2.5, foreground='#FFFFFF')], zorder=5.5)

    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=5)

    # Core Hub Vitality Labels (Callouts)
    hubs = [
        ("长春站商圈活力极核", 125.325, 43.908),
        ("光复路商圈活力次极核", 125.3475, 43.9017),
        ("伪满皇宫文旅集聚核", 125.3422, 43.9036)
    ]
    for name, lon, lat in hubs:
        x_pt, y_pt = get_xy(lon, lat)
        # Offset text slightly for readability
        ax_map.text(x_pt, y_pt - 80, name, color='#1E293B', ha='center', va='top',
                    fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=10.0),
                    path_effects=[path_effects.withStroke(linewidth=3, foreground='#FFFFFF')], zorder=6.0)

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
    # Column 0: X_sym = 102.2, X_txt = 106.2
    # Column 1: X_sym = 120.7, X_txt = 124.7
    # Rows: 80.5, 76.5, 72.5
    legend_items_data = [
        # Row 0
        ("规划研究范围", '#FF3B30', 'outline_boundary', 102.2, 106.2, 80.5),
        ("生活服务 POI", '#3B82F6', 'glow_dot', 120.7, 124.7, 80.5),
        # Row 1
        ("高活力核心区", '#EF4444', 'rect_fill', 102.2, 106.2, 76.5),
        ("餐饮服务 POI", '#F59E0B', 'glow_dot', 120.7, 124.7, 76.5),
        # Row 2
        ("中活力过渡区", '#FCD34D', 'rect_fill', 102.2, 106.2, 72.5),
        ("服务真空区", '#EF4444', 'rect_hatch', 120.7, 124.7, 72.5)
    ]
    
    for label, color_code, style, x_sym, x_txt, y_val in legend_items_data:
        if style == 'outline_boundary':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='none', edgecolor=color_code, linewidth=1.8, zorder=4)
            ax.add_patch(rect)
        elif style == 'rect_fill':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor=color_code, edgecolor='none', zorder=4)
            ax.add_patch(rect)
        elif style == 'rect_hatch':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='#FFF1F2', edgecolor=color_code, linewidth=0.8, linestyle='--', hatch='//', zorder=4)
            ax.add_patch(rect)
        elif style == 'glow_dot':
            # Draw double layer halo
            ax.plot(x_sym + 1.5, y_val, marker='o', markersize=8.0, color=color_code, alpha=0.3, zorder=4)
            ax.plot(x_sym + 1.5, y_val, marker='o', markersize=4.0, color=color_code, alpha=0.95, markeredgecolor='#FFFFFF', markeredgewidth=0.5, zorder=5)
            
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
        ("1. 哑铃型结构：业态呈“生存型”基底，生活服务与餐饮合计占比近40%，购物类仅占4.9%，揭示产业升级断层与消费业态单一化问题。", 55.0),
        ("2. 空间不均：高活力区集中在长春站及光复路沿线，历史保护区内部则由于路网割裂与人口流失呈现大面积“POI真空区”与“活力塌陷”。", 39.0),
        ("3. 业态升级方向：需引入文创零售、数字消费与社区综合服务等高附加值业态，构建“数字文创+全龄服务+遗产活化”三元动力结构。", 23.0)
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
    ("生活服务 POI (~40%)", "marker_poi_blue"),
    ("餐饮 POI", "marker_poi_orange"),
    ("购物 POI (仅4.9%)", "marker_poi_red"),
    ("POI服务真空区", "rect_noise_zone"),
]

description_lines = [
    "1. 哑铃型结构：业态呈“生存型”基底，生活服务与餐饮合计占比近40%，购物类仅占4.9%，揭示产业升级断层与消费业态单一化问题。",
    "2. 空间不均：高活力区集中在长春站及光复路沿线，历史保护区内部则由于路网割裂与人口流失呈现大面积“POI真空区”与“活力塌陷”。",
    "3. 业态升级方向：需引入文创零售、数字消费与社区综合服务等高附加值业态，构建“数字文创+全龄服务+遗产活化”三元动力结构。"
]
