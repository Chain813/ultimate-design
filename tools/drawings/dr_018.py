# -*- coding: utf-8 -*-
from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"

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

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop, *args, **kwargs):
    fig = ax.get_figure()
    
    # 1. Setup A3 Canvas Coordinates
    ax.set_facecolor("#F8FAFC")
    ax.set_xlim(0, 141.42)
    ax.set_ylim(0, 100)
    ax.set_axis_off()
    
    # Draw background grid
    for x in range(5, 140, 5):
        ax.plot([x, x], [0, 100], color='#E2E8F0', linestyle='-', linewidth=0.6, zorder=0, alpha=0.5)
    for y in range(5, 100, 5):
        ax.plot([0, 141.42], [y, y], color='#E2E8F0', linestyle='-', linewidth=0.6, zorder=0, alpha=0.5)

    # 2. Header Panel
    ax.add_patch(mpatches.Rectangle((2.3, 88.7), 136.8, 7.3, facecolor='#E2E8F0', edgecolor='none', zorder=1))
    ax.add_patch(mpatches.Rectangle((2.0, 89.0), 136.8, 7.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2))
    ax.add_patch(mpatches.Rectangle((2.0, 95.7), 136.8, 0.6, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(3.5, 93.6, "文化资源分析图", 
            color='#0F172A', ha='left', va='center', fontproperties=_font(font_prop, 26, "bold"), zorder=4)
    ax.text(3.5, 90.7, "分析伪满皇宫与旧工业遗产的“双核集聚、轴线割裂”空间格局，识别文化空间叙事断裂痛点。", 
            color='#334155', ha='left', va='center', fontproperties=_font(font_prop, 15.0), zorder=4)

    # 3. Main Map Card Container (X: 2.0 to 100.0, Y: 4.0 to 87.0)
    ax.add_patch(mpatches.Rectangle((2.3, 3.7), 98.0, 83.0, facecolor='#E2E8F0', edgecolor='none', zorder=1))
    ax.add_patch(mpatches.Rectangle((2.0, 4.0), 98.0, 83.0, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2))

    # Sub-axes for GIS map
    ax_map = fig.add_axes([3.0 / 141.42, 5.0 / 100.0, 96.0 / 141.42, 81.0 / 100.0], facecolor="#F8FAFC", zorder=3)
    ax_map.set_xlim(cx - view_w / 2, cx + view_w / 2)
    ax_map.set_ylim(cy - view_h / 2, cy + view_h / 2)
    ax_map.set_axis_off()
    ax_map.set_aspect("equal")

    # Plot GIS Base Layers
    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#D0E6F7", edgecolor="none", zorder=1)
        
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax_map, facecolor="#F1F5F9", edgecolor="#E2E8F0", linewidth=0.2, zorder=0.8)

    # Highlight Existing Heritage (protected buildings)
    prot_path = STATIC_DIR / "protected_buildings.geojson"
    if prot_path.exists():
        try:
            protected = gpd.read_file(prot_path).to_crs(epsg=3857)
            protected.plot(ax=ax_map, facecolor="#D97706", edgecolor="#B45309", linewidth=0.5, alpha=1.0, zorder=2.5)
        except Exception as e:
            print(f"Error loading protected buildings: {e}")

    if roads is not None and not roads.empty:
        for lvl, lw, color in [(1, 1.8, "#94A3B8"), (2, 1.2, "#CBD5E1"), (3, 0.7, "#E2E8F0"), (4, 0.5, "#F1F5F9")]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax_map, color=color, linewidth=lw, capstyle="round", joinstyle="round", zorder=1.2)

    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#64748B", linewidth=1.2, linestyle=(0, (5, 5)), zorder=1.3)

    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=5)

    # Draw Cultural Elements: "双核集聚、轴线割裂"
    # Core 1: 伪满皇宫历史核 (125.3422, 43.9036)
    pt1_x, pt1_y = get_xy(125.3422, 43.9036)
    
    # Outer glowing buffer (400m radius in EPSG:3857 ≈ 400 projection units)
    core1_outer = mpatches.Circle((pt1_x, pt1_y), 450, facecolor='#F59E0B', edgecolor='#D97706', linewidth=1.0, linestyle='--', alpha=0.15, zorder=2.1)
    core1_inner = mpatches.Circle((pt1_x, pt1_y), 250, facecolor='#F59E0B', edgecolor='#D97706', linewidth=1.5, alpha=0.3, zorder=2.2)
    ax_map.add_patch(core1_outer)
    ax_map.add_patch(core1_inner)
    
    # Core 2: 中车工业遗产核 (125.3401, 43.9079)
    pt2_x, pt2_y = get_xy(125.3401, 43.9079)
    core2_outer = mpatches.Circle((pt2_x, pt2_y), 450, facecolor='#8B5CF6', edgecolor='#7C3AED', linewidth=1.0, linestyle='--', alpha=0.15, zorder=2.1)
    core2_inner = mpatches.Circle((pt2_x, pt2_y), 250, facecolor='#8B5CF6', edgecolor='#7C3AED', linewidth=1.5, alpha=0.3, zorder=2.2)
    ax_map.add_patch(core2_outer)
    ax_map.add_patch(core2_inner)

    # Draw Railway axis barrier (轴线割裂)
    barrier_pts = [get_xy(125.325, 43.909), get_xy(125.335, 43.907), get_xy(125.347, 43.904), get_xy(125.359, 43.899)]
    bx, by = zip(*barrier_pts)
    ax_map.plot(bx, by, color='#EF4444', linewidth=7.0, alpha=0.25, zorder=1.4)
    ax_map.plot(bx, by, color='#EF4444', linewidth=1.8, linestyle='--', zorder=1.5)

    # Core 1 to Core 2 connection gap (叙事断裂)
    ax_map.plot([pt1_x, pt2_x], [pt1_y, pt2_y], color='#EF4444', linewidth=1.8, linestyle=':', zorder=4)
    mid_x, mid_y = (pt1_x + pt2_x) / 2, (pt1_y + pt2_y) / 2
    ax_map.plot(mid_x, mid_y, marker='X', color='#EF4444', markersize=10, markeredgecolor='#FFFFFF', markeredgewidth=1.0, zorder=4.5)

    # Text Annotations in Map
    ax_map.text(pt1_x, pt1_y - 260, "伪满皇宫历史核\n占地 13.55公顷\n周边绿视率仅 8.7%", color='#B45309', ha='center', va='top',
                fontproperties=_font(font_prop, 8.5, 'bold'),
                path_effects=[path_effects.withStroke(linewidth=2.0, foreground='#FFFFFF')], zorder=5)

    ax_map.text(pt2_x, pt2_y + 160, "中车工业遗产核\n仓储区空置率达 40%", color='#6D28D9', ha='center', va='bottom',
                fontproperties=_font(font_prop, 8.5, 'bold'),
                path_effects=[path_effects.withStroke(linewidth=2.0, foreground='#FFFFFF')], zorder=5)

    ax_map.text(mid_x + 60, mid_y + 60, "文化叙事轴断裂", color='#DC2626', ha='left', va='bottom',
                fontproperties=_font(font_prop, 8.5, 'bold'),
                path_effects=[path_effects.withStroke(linewidth=2.0, foreground='#FFFFFF')], zorder=5)

    # Label the railway barrier
    ax_map.text(get_xy(125.334, 43.907)[0], get_xy(125.334, 43.907)[1] - 80, "铁路割裂轴线", color='#DC2626', ha='right', va='top',
                fontproperties=_font(font_prop, 9.0, 'bold'),
                path_effects=[path_effects.withStroke(linewidth=2.0, foreground='#FFFFFF')], zorder=5)

    # Plot landmark labels
    labels = [
        ("伪满皇宫博物院", 125.3422, 43.9036),
        ("光复路", 125.3395, 43.9016),
        ("伊通河沿岸公园", 125.3590, 43.9010),
        ("长春站", 125.3250, 43.9080),
        ("胜利公园", 125.3260, 43.8960)
    ]
    for name, lon, lat in labels:
        x_pt, y_pt = get_xy(lon, lat)
        # Avoid overriding our cultural labels
        if name != "伪满皇宫博物院":
            ax_map.text(x_pt, y_pt, name, color='#475569', ha='center', va='bottom',
                        fontproperties=_font(font_prop, 9.0, 'bold'),
                        path_effects=[path_effects.withStroke(linewidth=2.0, foreground='#FFFFFF')], zorder=4.8)

    # 4. Legend Card (X: 101.5 to 139.4, Y: 67.0 to 87.0)
    legend_shadow = mpatches.Rectangle((101.8, 66.7), 37.9, 20.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    legend_bg = mpatches.Rectangle((101.5, 67.0), 37.9, 20.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(legend_shadow)
    ax.add_patch(legend_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 85.8), 37.9, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(103.5, 82.8, "图例 / LEGEND", color='#D97706', ha='left', va='center',
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)
    
    legend_items_data = [
        ("规划研究范围", '#FF3B30', 'outline_boundary', 102.2, 106.2, 79.5),
        ("历史/工业遗产建筑", '#D97706', 'rect_heritage_solid', 120.7, 124.7, 79.5),
        ("伪满皇宫历史核", '#F59E0B', 'circle_orange', 102.2, 106.2, 75.0),
        ("中车工业遗产核", '#8B5CF6', 'circle_purple', 120.7, 124.7, 75.0),
        ("铁路割裂轴线", '#EF4444', 'line_dashed_red', 102.2, 106.2, 70.5),
        ("文化叙事断裂", '#EF4444', 'marker_x', 120.7, 124.7, 70.5)
    ]
    
    for label, color_code, style, x_sym, x_txt, y_val in legend_items_data:
        if style == 'outline_boundary':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='none', edgecolor=color_code, linewidth=1.8, zorder=4)
            ax.add_patch(rect)
        elif style == 'rect_heritage_solid':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor=color_code, edgecolor='#B45309', linewidth=0.5, zorder=4)
            ax.add_patch(rect)
        elif style == 'circle_orange':
            # Draw semi-transparent circle symbolic legend
            circle = mpatches.Circle((x_sym + 1.5, y_val), 1.0, facecolor=color_code, edgecolor='#D97706', linewidth=0.5, alpha=0.5, zorder=4)
            ax.add_patch(circle)
        elif style == 'circle_purple':
            circle = mpatches.Circle((x_sym + 1.5, y_val), 1.0, facecolor=color_code, edgecolor='#7C3AED', linewidth=0.5, alpha=0.5, zorder=4)
            ax.add_patch(circle)
        elif style == 'line_dashed_red':
            ax.plot([x_sym, x_sym + 3.0], [y_val, y_val], color=color_code, linewidth=2.0, linestyle='--', zorder=4)
        elif style == 'marker_x':
            ax.plot(x_sym + 1.5, y_val, marker='X', color=color_code, markersize=6.0, markeredgecolor='#FFFFFF', markeredgewidth=0.3, zorder=4)
            
        ax.text(x_txt, y_val, label, color='#334155', ha='left', va='center',
                fontproperties=_font(font_prop, 10.5), zorder=4)

    # Scale Bar
    scale_len = 500 / (view_w / 96.0)
    x_start = 120.45 - scale_len / 2
    x_end = x_start + scale_len
    y_bar = 67.4
    ax.plot([x_start, x_end], [y_bar, y_bar], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_start, x_start], [y_bar - 0.8, y_bar + 0.8], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_start + scale_len/2, x_start + scale_len/2], [y_bar - 0.8, y_bar + 0.8], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_end, x_end], [y_bar - 0.8, y_bar + 0.8], color='#0F172A', linewidth=1.5, zorder=4)
    ax.text(x_start, y_bar + 1.5, "0", color='#334155', ha='center', va='center', fontproperties=_font(font_prop, 10.0), zorder=4)
    ax.text(x_start + scale_len/2, y_bar + 1.5, "250m", color='#334155', ha='center', va='center', fontproperties=_font(font_prop, 10.0), zorder=4)
    ax.text(x_end, y_bar + 1.5, "500m", color='#334155', ha='center', va='center', fontproperties=_font(font_prop, 10.0), zorder=4)
    scale_ratio = view_w / 0.31968
    scale_rounded = int(round(scale_ratio / 500)) * 500
    ax.text((x_start + x_end)/2, y_bar - 1.6, f"比例尺 1:{scale_rounded}", color='#334155', ha='center', va='center',
            fontproperties=_font(font_prop, 10.5, 'bold'), zorder=4)

    # 5. Description Card (X: 101.5 to 139.4, Y: 4.0 to 65.0)
    ax.add_patch(mpatches.Rectangle((101.8, 3.7), 37.9, 61.3, facecolor='#E2E8F0', edgecolor='none', zorder=1))
    ax.add_patch(mpatches.Rectangle((101.5, 4.0), 37.9, 61.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2))
    ax.add_patch(mpatches.Rectangle((101.5, 63.8), 37.9, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(103.5, 61.0, "文化空间诊断说明 / DIAGNOSIS", color='#D97706', ha='left', va='center',
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)
    
    desc_data = [
        ("1. 双核集聚：研究范围内文化资源主要富集于两大核心——伪满皇宫近代历史风貌保护区（占地 13.55 公顷）与西北侧中车旧厂区与工业遗产核。两者是宽城近代变迁的关键缩影。", 55.0),
        ("2. 轴线割裂：伪满皇宫与中车旧厂区之间受到现状繁忙的铁路线（长图铁路等）以及高宽交通干道等物理轴线的严厉割裂，造成了片区交通盲区与空间不可达。", 39.0),
        ("3. 叙事缺失：两大核心内部及周边品质消极（如皇宫周边绿视率仅 8.7%，旧厂区仓储空置率高达 40%）。两大文化核与南部城市生活板块之间严重缺乏连续的文化空间叙事与游线连接。", 23.0)
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
    ("重点历史/工业遗产建筑", "rect_heritage"),
    ("伪满皇宫历史核", "rect_orange_alpha"),
    ("中车工业遗产核", "rect_purple_alpha"),
    ("铁路割裂轴线", "line_dashed_red"),
    ("文化叙事断裂", "marker_x")
]

description_lines = [
    "1. 双核集聚：研究范围内文化资源主要富集于两大核心——伪满皇宫近代历史风貌保护区（占地 13.55 公顷）与西北侧中车旧厂区与工业遗产核。两者是宽城近代变迁的关键缩影。",
    "2. 轴线割裂：伪满皇宫与中车旧厂区之间受到现状繁忙的铁路线（长图铁路等）以及高宽交通干道等物理轴线的严厉割裂，造成了片区交通盲区与空间不可达。",
    "3. 叙事缺失：两大核心内部及周边品质消极（如皇宫周边绿视率仅 8.7%，旧厂区仓储空置率高达 40%）。两大文化核与南部城市生活板块之间严重缺乏连续的文化空间叙事与游线连接。"
]
