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
def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop, *args, **kwargs):
    global legend_items
    fig = ax.get_figure()
    params = kwargs.get("params", {})
    drawing_type = params.get("drawing_type", "用地规划图")
    show_buildings = (drawing_type == "用地规划图_带建筑轮廓")
    
    if show_buildings:
        if not any(item[0] == "现状建筑轮廓" for item in legend_items):
            legend_items.append(("现状建筑轮廓", "rect_style_norm"))
    else:
        legend_items = [item for item in legend_items if item[0] != "现状建筑轮廓"]
    
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
    
    ax.text(3.5, 93.6, "总体规划图", 
            color='#0F172A', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=26), zorder=4)
    
    ax.text(3.5, 90.7, "基于 MPI 48.3 诊断，实施居住减量与商业、绿地增量优化，落实建控地带容积率≤1.4、高度≤18米风貌管控。", 
            color='#334155', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=15.0), zorder=4)

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

    # Renders the beautiful masterplan landuse layout with solid colors to prevent a washed-out/whitish look
    if landuse is not None and not landuse.empty:
        for color_hex, sub_df in landuse.groupby('Color'):
            sub_df.plot(ax=ax_map, facecolor=color_hex, edgecolor="#E2E8F0", linewidth=0.1, alpha=1.0, zorder=1)
            
    # Highlight waterbody
    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#93C5FD", edgecolor="none", alpha=1.0, zorder=2)
        
    # Render building footprints if enabled
    if show_buildings and buildings is not None and not buildings.empty:
        buildings.plot(ax=ax_map, facecolor="#334155", edgecolor="#0F172A", linewidth=0.15, alpha=0.25, zorder=2.3)
        
    if key_plots is not None and not key_plots.empty:
        for idx, row in key_plots.iterrows():
            # Standard Planning Colors matching thesis v4:
            # Index 0, 1, 3 (Northwest, Northeast, East) are Commercial/文创 (#EF4444)
            # Index 2, 4 (West, Southwest) are Public Services/Admin (#C084FC)
            if idx in [0, 1, 3]:
                fc = "#EF4444"
            else:
                fc = "#C084FC"
            gpd.GeoSeries([row.geometry]).plot(ax=ax_map, facecolor=fc, edgecolor="none", linewidth=0, alpha=1.0, zorder=2.2)

    # Proposed roads: solid white lines with dark casing
    if roads is not None and not roads.empty:
        roads.plot(ax=ax_map, color="#C8D4E3", linewidth=1.5, zorder=3)
        # Add proposed minor road network lines for developed plots
        if key_plots is not None and not key_plots.empty:
            proposed_lines = []
            for idx, geom in enumerate(key_plots.geometry):
                if geom.is_valid and not geom.is_empty:
                    # Draw a loop pathway inside the key plot polygon (inward buffer)
                    for buf_dist in [-20, -12, -8]:
                        inner = geom.buffer(buf_dist)
                        if inner is not None and not inner.is_empty:
                            bnd = inner.boundary
                            if bnd is not None and not bnd.is_empty:
                                proposed_lines.append(bnd)
                                break
            if proposed_lines:
                proposed_gdf = gpd.GeoDataFrame(geometry=proposed_lines, crs=key_plots.crs)
                proposed_gdf.plot(ax=ax_map, color="#FFFFFF", linewidth=3.0, zorder=3.5)
                proposed_gdf.plot(ax=ax_map, color="#FF2D55", linewidth=1.2, linestyle="-", zorder=3.6)


    # Protected Historic Buildings (Preserved and highlighted on top of parks/plots using standard Amber color)
    prot_path = STATIC_DIR / "protected_buildings.geojson"
    if prot_path.exists():
        try:
            protected = gpd.read_file(prot_path).to_crs(epsg=3857)
            protected.plot(ax=ax_map, facecolor="#D97706", edgecolor="#B45309", linewidth=0.5, alpha=1.0, zorder=4.5)
        except Exception as e:
            print(f"Error loading protected buildings: {e}")

    # Boundary red line (Apple Red)
    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=2.0, zorder=5.0)

    # Map Labels with corrected coordinates (with white text stroke shadows)
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
                          fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=11), zorder=10)
        txt.set_path_effects([path_effects.withStroke(linewidth=3, foreground='#FFFFFF')])

    # 3c. Draw wind rose on map (HUD)
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

    # 4. Legend Card (X: 101.5 to 139.4, Y: 62.0 to 87.0)
    leg_y_min = 60.5 if show_buildings else 62.0
    leg_height = 26.5 if show_buildings else 25.0
    legend_shadow = mpatches.Rectangle((101.8, leg_y_min - 0.3), 37.9, leg_height, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    legend_bg = mpatches.Rectangle((101.5, leg_y_min), 37.9, leg_height, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(legend_shadow)
    ax.add_patch(legend_bg)
    ax.add_patch(mpatches.Rectangle((101.5, leg_y_min + leg_height - 1.2), 37.9, 1.2, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(103.5, leg_y_min + leg_height - 3.2, "图例 / LEGEND", color='#D97706', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13.5), zorder=4)
    
    # Legend Items
    if show_buildings:
        legend_items_data = [
            # Row 0
            ("规划研究范围", '#FF3B30', 'outline_boundary', 102.2, 106.2, 80.5),
            ("规划水系整治", '#93C5FD', 'rect_fill', 120.7, 124.7, 80.5),
            # Row 1
            ("居住社区规划", '#FDE047', 'rect_fill', 102.2, 106.2, 77.0),
            ("规划新增密集路网", '', 'line_double', 120.7, 124.7, 77.0),
            # Row 2
            ("商业文创策划", '#EF4444', 'rect_fill', 102.2, 106.2, 73.5),
            ("工业仓储遗存", '#64748B', 'rect_fill', 120.7, 124.7, 73.5),
            # Row 3
            ("规划新增绿地", '#22C55E', 'rect_fill', 102.2, 106.2, 70.0),
            ("重点历史保护建筑", '#D97706', 'rect_fill_border', 120.7, 124.7, 70.0),
            # Row 4
            ("现状城市道路", '#E2E8F0', 'rect_fill', 102.2, 106.2, 66.5),
            ("公共服务设施", '#C084FC', 'rect_fill', 120.7, 124.7, 66.5),
            # Row 5
            ("现状建筑轮廓", '#334155', 'rect_fill_alpha', 102.2, 106.2, 63.0)
        ]
    else:
        legend_items_data = [
            # Row 0
            ("规划研究范围", '#FF3B30', 'outline_boundary', 102.2, 106.2, 80.5),
            ("规划水系整治", '#93C5FD', 'rect_fill', 120.7, 124.7, 80.5),
            # Row 1
            ("居住社区规划", '#FDE047', 'rect_fill', 102.2, 106.2, 77.2),
            ("规划新增密集路网", '', 'line_double', 120.7, 124.7, 77.2),
            # Row 2
            ("商业文创策划", '#EF4444', 'rect_fill', 102.2, 106.2, 73.9),
            ("工业仓储遗存", '#64748B', 'rect_fill', 120.7, 124.7, 73.9),
            # Row 3
            ("规划新增绿地", '#22C55E', 'rect_fill', 102.2, 106.2, 70.6),
            ("重点历史保护建筑", '#D97706', 'rect_fill_border', 120.7, 124.7, 70.6),
            # Row 4
            ("现状城市道路", '#E2E8F0', 'rect_fill', 102.2, 106.2, 67.3),
            ("公共服务设施", '#C084FC', 'rect_fill', 120.7, 124.7, 67.3)
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
        elif style == 'rect_fill_alpha':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor=color_code, edgecolor='#0F172A', linewidth=0.3, alpha=0.35, zorder=4)
            ax.add_patch(rect)
        elif style == 'line_double':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color='#FFFFFF', linewidth=4.0, zorder=4)
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color='#FF2D55', linewidth=1.5, zorder=5)
        elif style == 'rect_fill_light':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=0.3, zorder=4)
            ax.add_patch(rect)
            
        ax.text(x_txt, y_val, label, color='#334155', ha='left', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], size=10.5), zorder=4)

    # Scale Bar (centered under Legend Card)
    y_bar = 61.4 if show_buildings else 64.6
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
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.0), zorder=4)
    ax.text(x_start + scale_len/2, y_text_val, "250m", color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.0), zorder=4)
    ax.text(x_end, y_text_val, "500m", color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.0), zorder=4)
    
    scale_ratio = view_w / 0.31968
    scale_rounded = int(round(scale_ratio / 500)) * 500
    ax.text((x_start + x_end)/2, y_ratio_val, f"比例尺 1:{scale_rounded}", color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.5, weight='bold'), zorder=4)

    # 5. Description Card (X: 101.5 to 139.4, Y: 4.0 to 60.0)
    desc_shadow = mpatches.Rectangle((101.8, 3.7), 37.9, 56.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    desc_bg = mpatches.Rectangle((101.5, 4.0), 37.9, 56.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(desc_shadow)
    ax.add_patch(desc_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 58.8), 37.9, 1.2, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(103.5, 56.2, "设计说明与规划指标 / DESCRIPTION", color='#D97706', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13.5), zorder=4)
    
    # 3 Bullet description items wrapped at 44 visual-width units, font size 15.0
    desc_data = [
        ("1. 规划格局：基于 MPI 48.3 诊断结论，确立“一核两带多节点”空间结构。以伪满皇宫为核心保护区，外围300米为风貌严控带，沿东八条与光复路历史文化轴布局文创与混合功能组团。", 50.0),
        ("2. 用地优化：针对居住比例过高、公服真空问题实施定向优化：居住用地降幅5-8%，商业服务业设施用地提升至13-15%，绿地与广场用地刚性提升至15%以上。", 34.0),
        ("3. 开发管控：严格遵循建控地带容积率≤1.4、建筑高度≤18米要求，通过低效市场功能置换与嵌入式公共空间系统植入，实现历史风貌保护、社区服务补短板与文旅动线贯通。", 18.0)
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
    ("居住社区规划", "rect_plan_yellow"),
    ("商业文创策划", "rect_plan_red"),
    ("规划新增绿地", "rect_plan_green"),
    ("规划水系整治", "rect_plan_blue"),
    ("规划新增密集路网", "line_plan_road"),
    ("工业仓储遗存", "rect_style_blue"),
    ("重点历史保护建筑", "rect_heritage"),
    ("现状城市道路", "rect_road"),
    ("公共服务设施", "rect_euluc_6")
]

description_lines = [
    "1. 规划格局：基于 MPI 48.3 诊断结论，确立“一核两带多节点”空间结构。以伪满皇宫为核心保护区，外围300米为风貌严控带，沿东八条与光复路历史文化轴布局文创与混合功能组团。",
    "2. 用地优化：针对居住比例过高、公服真空问题实施定向优化：居住用地降幅5-8%，商业服务业设施用地提升至13-15%，绿地与广场用地刚性提升至15%以上。",
    "3. 开发管控：严格遵循建控地带容积率≤1.4、建筑高度≤18米要求，通过低效市场功能置换与嵌入式公共空间系统植入，实现历史风貌保护、社区服务补短板与文旅动线贯通。"
]