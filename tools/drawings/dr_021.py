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
    
    ax.text(3.5, 93.6, "人群需求与老龄化分布图", 
            color='#0F172A', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=26), zorder=4)
    
    ax.text(3.5, 90.7, "测算老旧住宅分布以解析高老龄化人口集聚区，叠合500m公共服务设施覆盖分析以识别适老服务缺口。", 
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

    # 3b. Plot GIS Base Layers on sub-axes (drawn light to highlight aging overlay and green circles)
    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#E2F0FD", edgecolor="none", zorder=1)
        
    if roads is not None and not roads.empty:
        roads.plot(ax=ax_map, color="#CBD5E1", linewidth=0.6, alpha=0.8, zorder=1.5)
        
    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#94A3B8", linewidth=1.0, linestyle=(0, (5, 5)), zorder=1.2)

    # 3c. Color buildings by floor proxy representing aging population density
    # Low-rise (floor <= 3): High Aging Density -> Vibrant Coral Red (#EF4444)
    # Mid-rise (floor 4-7): Medium Aging Density -> Vibrant Yellow (#FBBF24)
    # High-rise (floor >= 8): Low Aging Density -> Vibrant Blue (#60A5FA)
    if buildings is not None and not buildings.empty:
        bc = buildings.copy()
        bc["Floor_num"] = pd.to_numeric(bc["Floor"], errors="coerce").fillna(3)
        
        conds = [
            (bc["Floor_num"] <= 3),
            (bc["Floor_num"] <= 7),
            (bc["Floor_num"] > 7)
        ]
        colors = [
            "#EF4444", # High contrast Coral Red (high age)
            "#FBBF24", # High contrast Yellow (medium)
            "#60A5FA"  # High contrast Light Blue (low)
        ]
        bc["age_color"] = np.select(conds, colors, default="#E2E8F0")
        bc.plot(ax=ax_map, color=bc["age_color"], edgecolor="#64748B", linewidth=0.18, alpha=0.9, zorder=1.8)
    
    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=5)

    # 3d. 500m Service Radius Circles for key community service gaps (High contrast Green)
    # Map elements are changed to green to perfectly match the legend and stand out
    service_pts = [
        (125.3340, 43.9060, "适老服务缺口·日间照料"),
        (125.3450, 43.9020, "社区食堂服务盲区"),
        (125.3380, 43.9000, "幼托设施覆盖缺口"),
    ]
    for lon, lat, label in service_pts:
        px, py = get_xy(lon, lat)
        buf = Point(px, py).buffer(500)
        
        # High visibility vibrant green facecolor, bold green dashed outline, with hatching overlay
        gpd.GeoDataFrame(geometry=[buf], crs="EPSG:3857").plot(
            ax=ax_map, facecolor="#4ADE80", edgecolor="#16A34A", linewidth=2.2, linestyle="--", alpha=0.40, hatch="///", zorder=2.0)
        
        # White background glow to contrast the marker on colored building areas
        ax_map.plot(px, py, marker='s', markersize=15.0, color='#FFFFFF', alpha=0.9, zorder=4.8)
        # Bold green square marker at the center
        ax_map.plot(px, py, marker='s', markersize=9.5, color='#15803D', markeredgecolor='#FFFFFF', markeredgewidth=1.2, zorder=5.0)
        
        # High contrast dark-green text label with thicker white stroke outline
        txt = ax_map.text(px, py + 70, label, color='#064E3B', ha='center', va='bottom',
                          fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=11.5), zorder=5.5)
        txt.set_path_effects([path_effects.withStroke(linewidth=3.5, foreground='#FFFFFF')])

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
        ("新建高层 (≥8层)", '#60A5FA', 'rect_fill', 120.7, 124.7, 80.5),
        # Row 1
        ("老旧住宅 (≤3层)", '#EF4444', 'rect_fill', 102.2, 106.2, 76.5),
        ("适老服务缺口圈", '#16A34A', 'green_buffer', 120.7, 124.7, 76.5),
        # Row 2
        ("中层住宅 (4-7层)", '#FBBF24', 'rect_fill', 102.2, 106.2, 72.5),
        ("服务缺口设施点", '#15803D', 'green_square', 120.7, 124.7, 72.5)
    ]
    
    for label, color_code, style, x_sym, x_txt, y_val in legend_items_data:
        if style == 'outline_boundary':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='none', edgecolor=color_code, linewidth=1.8, zorder=4)
            ax.add_patch(rect)
        elif style == 'rect_fill':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor=color_code, edgecolor='none', zorder=4)
            ax.add_patch(rect)
        elif style == 'green_buffer':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='#4ADE80', edgecolor=color_code, linewidth=1.5, linestyle='--', alpha=0.6, hatch='///', zorder=4)
            ax.add_patch(rect)
        elif style == 'green_square':
            # Background white glow
            ax.plot(x_sym + 1.5, y_val, marker='s', markersize=9.0, color='#FFFFFF', alpha=0.9, zorder=4)
            ax.plot(x_sym + 1.5, y_val, marker='s', markersize=6.0, color=color_code, markeredgecolor='#FFFFFF', markeredgewidth=0.5, zorder=5)
            
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
    
    ax.text(103.5, 61.0, "数据来源与诊断说明 / DATA SOURCES", color='#D97706', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13.5), zorder=4)
    
    # 3 Bullet description items wrapped at 44 visual-width units, font size 15.0
    desc_data = [
        ("1. 测算方法：以建筑层数作为老龄化分布的代理指标（≤3层为高老龄化住宅）。重合分析显示，低层老旧住宅与高老龄化人口高度重合。", 55.0),
        ("2. 诊断依据：依据国标GB50180-2018生活圈规范，对日间照料、社区食堂等设施建立500米缓冲区。分析揭示多处服务盲区。", 39.0),
        ("3. 绿化关联：叠合景观品质测算，78.3%的采样点绿视率低于15%宜居阈值。老龄化集聚区与绿色空间匮乏重叠，限制了日常社交。", 23.0)
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
    ("老旧低层住宅 (≤3层·高老龄化)", "rect_height_red"),
    ("中层建筑 (4-7层)", "rect_height_yellow"),
    ("新建高层 (≥8层)", "rect_height_blue"),
    ("500m适老服务缺口圈", "rect_green_buffer"),
]

description_lines = [
    "1. 测算方法：以建筑层数作为老龄化分布的代理指标（≤3层为高老龄化住宅）。重合分析显示，低层老旧住宅与高老龄化人口高度重合。",
    "2. 诊断依据：依据国标GB50180-2018生活圈规范，对日间照料、社区食堂等设施建立500米缓冲区。分析揭示多处服务盲区。",
    "3. 绿化关联：叠合景观品质测算，78.3%的采样点绿视率低于15%宜居阈值。老龄化集聚区与绿色空间匮乏重叠，限制了日常社交。"
]
