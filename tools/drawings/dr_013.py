import os
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
    
    # Draw background architectural grid
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
    
    ax.text(3.5, 93.6, "数据来源与遥感现状图", 
            color='#0F172A', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=26), zorder=4)
    
    ax.text(3.5, 90.7, "展示研究区域的多源遥感底图数据，以获取真实的地表覆盖、建筑现状密度及周边生态廊道肌理。", 
            color='#334155', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=15.0), zorder=4)

    # 3. Giant Satellite Map Card Container (X: 2.0 to 100.0, Y: 4.0 to 87.0)
    map_shadow = mpatches.Rectangle((2.3, 3.7), 98.0, 83.0, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    map_bg = mpatches.Rectangle((2.0, 4.0), 98.0, 83.0, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(map_shadow)
    ax.add_patch(map_bg)
    
    # Sub-axes for spatial GIS map (Centered inside the container)
    ax_map = fig.add_axes([3.0 / 141.42, 5.0 / 100.0, 96.0 / 141.42, 81.0 / 100.0], facecolor="#F8FAFC", zorder=3)
    ax_map.set_xlim(cx - view_w / 2, cx + view_w / 2)
    ax_map.set_ylim(cy - view_h / 2, cy + view_h / 2)
    ax_map.set_axis_off()
    ax_map.set_aspect("equal")

    # Load and display satellite image on sub-axes (with high-res TIFF dynamic loading)
    tif_path = None
    graduate_dir = Path("E:/graduate")
    if graduate_dir.exists():
        for root, dirs, files in os.walk(graduate_dir):
            for file in files:
                if "2604161335" in file and file.lower().endswith(".tif"):
                    tif_path = Path(root) / file
                    break
    
    if not tif_path:
        album_dir = Path("E:/画册/影像")
        if album_dir.exists():
            for root, dirs, files in os.walk(album_dir):
                for file in files:
                    if "2503142036" in file and file.lower().endswith(".tif"):
                        tif_path = Path(root) / file
                        break

    loaded_high_res = False
    if tif_path and tif_path.exists():
        try:
            import rasterio
            from rasterio.windows import from_bounds
            with rasterio.open(tif_path) as src:
                xmin = cx - view_w / 2
                xmax = cx + view_w / 2
                ymin = cy - view_h / 2
                ymax = cy + view_h / 2
                
                # Crop with 5% safety padding to prevent boundary gaps
                pad_w = view_w * 0.05
                pad_h = view_h * 0.05
                window = from_bounds(xmin - pad_w, ymin - pad_h, xmax + pad_w, ymax + pad_h, src.transform)
                
                # Read RGB (bands 1, 2, 3)
                data = src.read([1, 2, 3], window=window)
                rgb = np.transpose(data, (1, 2, 0))
                sat_img = Image.fromarray(rgb)
                
                extent = [xmin - pad_w, xmax + pad_w, ymin - pad_h, ymax + pad_h]
                ax_map.imshow(sat_img, extent=extent, zorder=0)
                loaded_high_res = True
        except Exception as e:
            print(f"Error loading high-res TIFF: {e}. Falling back to default satellite PNG.")

    if not loaded_high_res:
        sat_path = STATIC_DIR / "assets/generated_base/satellite_cropped.png"
        if sat_path.exists():
            try:
                sat_img = Image.open(sat_path)
                extent = [cx - view_w / 2, cx + view_w / 2, cy - view_h / 2, cy + view_h / 2]
                ax_map.imshow(sat_img, extent=extent, zorder=0)
            except Exception as e:
                print(f"Error loading satellite image: {e}")
                ax_map.text(cx, cy, "卫星遥感底图加载失败", ha='center', va='center', fontsize=20, color='#FF3B30', fontproperties=fm.FontProperties(family=font_prop['family']))
        else:
            ax_map.text(cx, cy, "卫星遥感底图未找到", ha='center', va='center', fontsize=20, color='#8E8E93', fontproperties=fm.FontProperties(family=font_prop['family']))

    # Plot water body
    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#0066CC", edgecolor="none", alpha=0.35, zorder=1)
        
    # Plot study boundary (Red line)
    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=2)

    # Plot key landmarks on satellite map
    labels = [
        ("伪满皇宫博物院", 125.3422, 43.9036),
        ("光复路", 125.3475, 43.9017),
        ("伊通河沿岸公园", 125.3590, 43.9010),
        ("长春站", 125.3250, 43.9080),
        ("胜利公园", 125.3260, 43.8960)
    ]
    for name, lon, lat in labels:
        x_pt, y_pt = get_xy(lon, lat)
        ax_map.text(x_pt, y_pt, name, color='#FFFFFF', ha='center', va='center',
                    fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=11),
                    path_effects=[path_effects.withStroke(linewidth=3, foreground='#000000')], zorder=5)

    # Floating Windrose (Pure White, Enlarged to 12.0 x 12.0, Shifted slightly down)
    rose_path = ASSETS_DIR / "长春市风玫瑰.png"
    if rose_path.exists():
        try:
            # Create ax_rose at the top right of the satellite map (zorder=4, overlapping ax_map)
            # Aligned with the right boundary (X: 99.0) but shifted down slightly (Y: 72.5 to 84.5) to avoid touching the top border
            ax_rose = fig.add_axes([87.0 / 141.42, 72.5 / 100.0, 12.0 / 141.42, 12.0 / 100.0], facecolor='none', zorder=4)
            ax_rose.set_axis_off()
            
            # Generate a beautiful soft dark radial gradient background (from black center to transparent edge)
            y, x = np.ogrid[-1:1:100j, -1:1:100j]
            r = np.sqrt(x**2 + y**2)
            # Alpha goes from 0.45 at center to 0.0 at the edges
            alpha = np.clip(1.0 - r, 0, 1) * 0.45
            grad_img = np.zeros((100, 100, 4)) # Black base
            grad_img[..., 3] = alpha
            
            # Display dark radial gradient shadow (zorder=0)
            ax_rose.imshow(grad_img, zorder=0, extent=[0, 1, 0, 1], origin='lower')
            
            # Load wind rose image and convert RGB channels to pure white (255)
            rose_img = Image.open(rose_path).convert("RGBA")
            rose_data = np.array(rose_img)
            rose_data[..., 0] = 255
            rose_data[..., 1] = 255
            rose_data[..., 2] = 255
            white_rose_img = Image.fromarray(rose_data)
            
            # Display pure white wind rose image (zorder=1)
            ax_rose.imshow(white_rose_img, zorder=1)
        except Exception as e:
            print(f"Error loading wind rose: {e}")

    # 4. Legend Card (X: 101.5 to 139.4, Y: 67.0 to 87.0) — Compressed vertically!
    legend_shadow = mpatches.Rectangle((101.8, 66.7), 37.9, 20.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    legend_bg = mpatches.Rectangle((101.5, 67.0), 37.9, 20.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(legend_shadow)
    ax.add_patch(legend_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 85.8), 37.9, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(103.5, 82.5, "图例 / LEGEND", color='#D97706', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13.5), zorder=4)
    
    # Legend Items — Arranged horizontally, spacing compressed, text size 13.5 (matching DR-003/007 body text exactly)
    y_leg = 78.5
    legend_items_data = [
        ("研究范围", '#FF3B30', 'outline', 102.2, 105.7),
        ("更新地块", '#F59E0B', 'outline', 111.2, 114.7),
        ("伊通河", '#0066CC', 'fill', 120.2, 123.7),
        ("影像底图", '#64748B', 'sat', 128.0, 131.5)
    ]
    for label, color_code, style, x_sym, x_txt in legend_items_data:
        if style == 'outline':
            rect = mpatches.Rectangle((x_sym, y_leg - 0.8), 3.0, 1.8, facecolor='none', edgecolor=color_code, linewidth=1.8, zorder=4)
        elif style == 'fill':
            rect = mpatches.Rectangle((x_sym, y_leg - 0.8), 3.0, 1.8, facecolor=color_code, edgecolor='none', alpha=0.6, zorder=4)
        else:
            rect = mpatches.Rectangle((x_sym, y_leg - 0.8), 3.0, 1.8, facecolor=color_code, edgecolor='#CBD5E1', alpha=0.8, zorder=4)
        ax.add_patch(rect)
        ax.text(x_txt, y_leg, label, color='#334155', ha='left', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], size=13.5), zorder=4)

    # 4b. Draw line-shaped scale bar centered inside the bottom row of the Legend Card
    scale_len = 500 / (view_w / 96.0) # Length in main axes units
    x_start = 120.45 - scale_len / 2
    x_end = x_start + scale_len
    y_bar = 70.0
    ax.plot([x_start, x_end], [y_bar, y_bar], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_start, x_start], [69.2, 70.8], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_start + scale_len/2, x_start + scale_len/2], [69.2, 70.8], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_end, x_end], [69.2, 70.8], color='#0F172A', linewidth=1.5, zorder=4)
    
    # Scale text labels (size 11.0)
    ax.text(x_start, 72.0, "0", color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=11.0), zorder=4)
    ax.text(x_start + scale_len/2, 72.0, "250m", color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=11.0), zorder=4)
    ax.text(x_end, 72.0, "500m", color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=11.0), zorder=4)
    
    scale_ratio = view_w / 0.31968
    scale_rounded = int(round(scale_ratio / 500)) * 500
    ax.text((x_start + x_end)/2, 68.0, f"比例尺 1:{scale_rounded}", color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=11.0, weight='bold'), zorder=4)

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
        ("1. 遥感影像：本图底图采用高分辨率 Google Earth 卫星遥感影像（2024年最新数据），直观反映项目所在长春市宽城区伪满皇宫周边区域的真实地表覆盖与建筑空间密度。", 55.0),
        ("2. 蓝绿肌理：东侧伊通河生态廊道水体形态完整，但街区内部绿色开敞空间较少，植被覆盖主要呈线性分布在铁路线及道路两侧，亟需引入更多社区口袋公园。", 39.0),
        ("3. 建设状况：街区内现状以中低层高密度建筑群为主，东北侧存在大面积中车低效工业遗存与厂房，南侧及西侧以商旧住宅为主，空间肌理较为拥挤。", 23.0)
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
    ("重点更新地块", "rect_orange_border"),
    ("伊通河水系", "rect_water"),
    ("卫星遥感影像", "rect_sat_base")
]

description_lines = [
    "1. 遥感影像：本图底图采用高分辨率 Google Earth 卫星遥感影像（2024年最新数据），直观反映项目所在长春市宽城区伪满皇宫周边区域的真实地表覆盖与建筑空间密度。",
    "2. 蓝绿肌理：东侧伊通河生态廊道水体形态完整，但街区内部绿色开敞空间较少，植被覆盖主要呈线性分布在铁路线及道路两侧，亟需引入更多社区口袋公园。",
    "3. 建设状况：街区内现状以中低层高密度建筑群为主，东北侧存在大面积中车低效工业遗存与厂房，南侧及西侧以商旧住宅为主，空间肌理较为拥挤。"
]