# -*- coding: utf-8 -*-
from shapely.geometry import Point
from shapely.ops import unary_union
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
    
    ax.text(3.5, 93.6, "遗产价值评估热力图", 
            color='#0F172A', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=26), zorder=4)
    
    ax.text(3.5, 90.7, "基于MCDA框架加权估算（V = 0.40 * I_hist + 0.30 * I_ind + 0.15 * I_synt + 0.15 * I_riv），科学度量遗产价值空间分布特征。", 
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

    # 3b. Plot GIS Base Layers on sub-axes (drawn light to highlight overlay)
    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#E2F0FD", edgecolor="none", zorder=1.1)
        
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax_map, facecolor="#FFFFFF", edgecolor="#E2E8F0", linewidth=0.2, zorder=0.8)

    # 3c. MCDA Model calculations for grid heritage value
    # Grid coordinates
    grid_x, grid_y = np.mgrid[cx-view_w/2:cx+view_w/2:120j, cy-view_h/2:cy+view_h/2:120j]
    
    # Factor 1: Historical & Cultural Heritage Factor (I_history)
    I_history = np.zeros_like(grid_x)
    px_palace, py_palace = get_xy(125.3422, 43.9036)
    dist_sq_palace = (grid_x - px_palace)**2 + (grid_y - py_palace)**2
    I_history += 1.5 * np.exp(-dist_sq_palace / (2 * 450**2))
    
    prot_path = STATIC_DIR / "protected_buildings.geojson"
    if prot_path.exists():
        try:
            prot_gdfs = gpd.read_file(prot_path).to_crs(epsg=3857)
            for _, row in prot_gdfs.iterrows():
                bx, by = row.geometry.centroid.x, row.geometry.centroid.y
                dist_sq_b = (grid_x - bx)**2 + (grid_y - by)**2
                I_history += 0.8 * np.exp(-dist_sq_b / (2 * 200**2))
        except Exception:
            pass

    # Factor 2: Industrial & Rail Heritage Factor (I_industrial)
    I_industrial = np.zeros_like(grid_x)
    if rails is not None and not rails.empty:
        try:
            simplified_rails = rails.geometry.simplify(50)
            coords = []
            for geom in simplified_rails:
                if geom.geom_type == 'LineString':
                    coords.extend(geom.coords)
                elif geom.geom_type == 'MultiLineString':
                    for part in geom.geoms:
                        coords.extend(part.coords)
            for rx, ry in coords[::5]:
                dist_sq_r = (grid_x - rx)**2 + (grid_y - ry)**2
                I_industrial += 0.6 * np.exp(-dist_sq_r / (2 * 180**2))
        except Exception:
            pass

    # Factor 3: Spatial Access & Perceptual Integration Factor (I_syntax)
    I_syntax = np.zeros_like(grid_x)
    if roads is not None and not roads.empty:
        try:
            high_int_roads = roads[roads['level'].isin([1, 2])].geometry.simplify(100)
            road_coords = []
            for geom in high_int_roads:
                if geom.geom_type == 'LineString':
                    road_coords.extend(geom.coords)
                elif geom.geom_type == 'MultiLineString':
                    for part in geom.geoms:
                        road_coords.extend(part.coords)
            for rx, ry in road_coords[::10]:
                dist_sq_rd = (grid_x - rx)**2 + (grid_y - ry)**2
                I_syntax += 0.4 * np.exp(-dist_sq_rd / (2 * 120**2))
        except Exception:
            pass

    # Factor 4: River Scenic Corridor Factor (I_river)
    I_river = np.zeros_like(grid_x)
    if water is not None and not water.empty:
        try:
            simplified_water = water.geometry.simplify(100)
            water_coords = []
            for geom in simplified_water:
                if geom.geom_type == 'Polygon':
                    water_coords.extend(geom.exterior.coords)
                elif geom.geom_type == 'MultiPolygon':
                    for poly in geom.geoms:
                        water_coords.extend(poly.exterior.coords)
            for wx, wy in water_coords[::20]:
                dist_sq_w = (grid_x - wx)**2 + (grid_y - wy)**2
                I_river += 0.4 * np.exp(-dist_sq_w / (2 * 150**2))
        except Exception:
            pass

    # Normalize factors
    def normalize(grid):
        mx = grid.max()
        return grid / mx if mx > 0.0 else grid
        
    I_history = normalize(I_history)
    I_industrial = normalize(I_industrial)
    I_syntax = normalize(I_syntax)
    I_river = normalize(I_river)
    
    # Combined Multi-Criteria Heritage Value Index:
    # 40% History + 30% Industrial + 15% Connectivity + 15% Scenic Corridor
    grid_z = 0.40 * I_history + 0.30 * I_industrial + 0.15 * I_syntax + 0.15 * I_river
    grid_z = grid_z * 100.0

    # Draw 14-level MCDA Heatmap Contour
    levels = np.linspace(8, 95, 14)
    ax_map.contourf(grid_x, grid_y, grid_z, levels=levels, cmap='YlOrRd', alpha=0.55, zorder=1.5)

    # 3d. Plot Key Protected Heritage Buildings on top of the Heatmap
    if prot_path.exists():
        try:
            prot_gdfs = gpd.read_file(prot_path).to_crs(epsg=3857)
            # Rose-pink high contrast heritage polygon with white border outline
            prot_gdfs.plot(ax=ax_map, facecolor="#F43F5E", edgecolor="#FFFFFF", linewidth=0.6, alpha=0.9, zorder=3.5)
        except Exception:
            pass

    # 3e. Plot Road network layers on top of buffers
    if roads is not None and not roads.empty:
        for lvl, lw, color in [(1, 1.8, "#94A3B8"), (2, 1.2, "#CBD5E1"), (3, 0.7, "#E2E8F0"), (4, 0.5, "#F1F5F9")]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax_map, color=color, linewidth=lw, capstyle="round", joinstyle="round", zorder=2.0)
                
    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#475569", linewidth=1.2, linestyle=(0, (5, 5)), zorder=2.2)

    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=5.0)

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
        ax_map.text(x_pt, y_pt, name, color='#1E293B', ha='center', va='bottom',
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
        ("外围本底价值区", '#FEF08A', 'rect_fill', 120.7, 124.7, 80.5),
        # Row 1
        ("极高遗产价值区", '#B91C1C', 'rect_fill', 102.2, 106.2, 76.5),
        ("重点历史保护建筑", '#F43F5E', 'rect_fill_border', 120.7, 124.7, 76.5),
        # Row 2
        ("中等风貌过渡区", '#F97316', 'rect_fill', 102.2, 106.2, 72.5),
        ("现状普通建筑", '#E2E8F0', 'rect_fill_light', 120.7, 124.7, 72.5)
    ]
    
    for label, color_code, style, x_sym, x_txt, y_val in legend_items_data:
        if style == 'outline_boundary':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='none', edgecolor=color_code, linewidth=1.8, zorder=4)
            ax.add_patch(rect)
        elif style == 'rect_fill':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor=color_code, edgecolor='none', zorder=4)
            ax.add_patch(rect)
        elif style == 'rect_fill_border':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor=color_code, edgecolor='#FFFFFF', linewidth=0.6, zorder=4)
            ax.add_patch(rect)
        elif style == 'rect_fill_light':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=0.3, zorder=4)
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
    
    # Scale text labels (size 10.0)
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

    # 5. Description Card (X: 101.5 to 139.4, Y: 4.0 to 65.0)
    desc_shadow = mpatches.Rectangle((101.8, 3.7), 37.9, 61.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    desc_bg = mpatches.Rectangle((101.5, 4.0), 37.9, 61.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(desc_shadow)
    ax.add_patch(desc_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 63.8), 37.9, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(103.5, 61.0, "遗产价值评估诊断 / DIAGNOSIS", color='#D97706', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13.5), zorder=4)
    
    # 3 Bullet description items wrapped at 44 visual-width units, font size 15.0
    desc_data = [
        ("1. 评估体系：引入多准则决策分析（MCDA）框架，综合耦合历史文化（40%）、工业遗存（30%）、空间句法整合度（15%）及水系风貌廊道（15%）四个维度，科学建构遗产价值空间评价模型。", 55.0),
        ("2. 价值双核：评估呈现以伪满皇宫博物院近代旧址群为一级高值极核、中车长客厂区大跨度车间工业遗产为二级核心的特征，其高价值影响域半径分别达450米与180米。", 39.0),
        ("3. 风貌管控：基于价值衰减曲线，划定核心保护范围、建设控制地带（300米内）与风貌协调区，作为AIGC建筑风貌识别管控与历史天际线体量约束的硬性空间边界。", 23.0)
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
    ("核心遗产价值最高点", "rect_heatmap_high"),
    ("风貌过渡控制价值中", "rect_heatmap_med"),
    ("外围本底遗产价值低", "rect_heatmap_low"),
    ("现状普通建筑", "rect_building_light")
]

description_lines = [
    "1. 评估体系：引入多准则决策分析（MCDA）框架，综合耦合历史文化（40%）、工业遗存（30%）、空间句法整合度（15%）及水系风貌廊道（15%）四个维度，科学建构遗产价值空间评价模型。",
    "2. 价值双核：评估呈现以伪满皇宫博物院近代旧址群为一级高值极核、中车长客厂区大跨度车间工业遗产为二级核心的特征，其高价值影响域半径分别达450米与180米。",
    "3. 风貌管控：基于价值衰减曲线，划定核心保护范围、建设控制地带（300米内）与风貌协调区，作为AIGC建筑风貌识别管控与历史天际线体量约束的硬性空间边界。"
]