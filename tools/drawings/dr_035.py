# -*- coding: utf-8 -*-
from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
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
def _font(font_prop, size, weight="normal"):
    return fm.FontProperties(family=font_prop["family"], size=size, weight=weight)

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop, params=None, *args, **kwargs):
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
    
    ax.text(3.5, 93.6, "更新模式分区图", 
            color='#0F172A', ha='left', va='center', fontproperties=_font(font_prop, 26, "bold"), zorder=4)
    ax.text(3.5, 90.7, "划分保护修缮、整治提升、功能置换与拆改更新四大引导分区，实施“微创织补、精准干预”的分级更新控制。", 
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
        buildings_copy = buildings.copy()
        # Distances to Palace
        px_palace, py_palace = get_xy(125.3422, 43.9036)
        palace_pt = Point(px_palace, py_palace)
        dists = buildings_copy.geometry.distance(palace_pt)

        # Fallback check for prop_style column to prevent KeyError
        prop_style_col = buildings_copy["prop_style"] if "prop_style" in buildings_copy.columns else pd.Series([""] * len(buildings_copy))
        conditions = [
            (prop_style_col == "historical") | (dists <= 150),
            (dists > 150) & (dists <= 450),
            (buildings_copy["geometry"].centroid.x < 125.335) | (buildings_copy["geometry"].centroid.x > 125.346),
            (dists > 450)
        ]
        # LLM-guided color overrides
        c = params.get("color_overrides", {}) if params else {}
        choices = [
            c.get("heritage_core", "#B45309"),   # 保护修缮: 历史核心 (古铜)
            c.get("transition_zone", "#F59E0B"),  # 整治提升: 过渡风貌 (橙黄)
            c.get("micro_update", "#10B981"),     # 微更新: 老社区修补 (绿)
            c.get("functional_replace", "#3B82F6") # 功能置换: 工业转型 (蓝)
        ]
        buildings_copy["color"] = np.select(conditions, choices, default="#F59E0B")
        buildings_copy.plot(ax=ax_map, color=buildings_copy["color"], edgecolor="#475569", linewidth=0.15, zorder=2.2)

    if key_plots is not None and not key_plots.empty:
        key_plots.plot(ax=ax_map, facecolor="#A855F7", edgecolor="#7E22CE", linewidth=1.5, alpha=0.8, zorder=2.5)

    if roads is not None and not roads.empty:
        for lvl, lw, color in [(1, 1.8, "#94A3B8"), (2, 1.2, "#CBD5E1"), (3, 0.7, "#E2E8F0"), (4, 0.5, "#F1F5F9")]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax_map, color=color, linewidth=lw, capstyle="round", joinstyle="round", zorder=1.2)

    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#64748B", linewidth=1.2, linestyle=(0, (5, 5)), zorder=1.3)

    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=5)

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
        ("重点更新地块", '#A855F7', 'rect_purple_solid', 120.7, 124.7, 79.5),
        ("保护修缮区", '#B45309', 'rect_solid', 102.2, 106.2, 75.0),
        ("整治提升区", '#F59E0B', 'rect_solid', 120.7, 124.7, 75.0),
        ("微更新区", '#10B981', 'rect_solid', 102.2, 106.2, 70.5),
        ("功能置换区", '#3B82F6', 'rect_solid', 120.7, 124.7, 70.5)
    ]
    
    for label, color_code, style, x_sym, x_txt, y_val in legend_items_data:
        if style == 'outline_boundary':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor='none', edgecolor=color_code, linewidth=1.8, zorder=4)
            ax.add_patch(rect)
        elif style == 'rect_purple_solid':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor=color_code, edgecolor='#7E22CE', linewidth=0.8, alpha=0.8, zorder=4)
            ax.add_patch(rect)
        elif style == 'rect_solid':
            rect = mpatches.Rectangle((x_sym, y_val - 0.8), 3.0, 1.6, facecolor=color_code, edgecolor='none', zorder=4)
            ax.add_patch(rect)
            
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
    
    ax.text(103.5, 61.0, "更新模式引导说明 / DIAGNOSIS", color='#D97706', ha='left', va='center',
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)
    
    desc_data = [
        ("1. 筛选评估：基于MPI综合评估指标（MPI值≤48.3的严重失能建筑），共筛选评估街区内719栋现状建筑，实施“微创织补、精准干预”分类更新模式分区。", 55.0),
        ("2. 四区分类：划分保护修缮区（伪满皇宫等历史建筑群）、整治提升区（过渡风貌建筑）、功能置换区（中车老旧工业厂房遗存）与拆改更新区（严重破损住宅与低效市场）。", 39.0),
        ("3. 导则控制：核心修缮区严禁新建建筑；整治提升区推行中式现代风貌立面改造；功能置换区引入青年公寓与众创空间；拆改区用于补足全龄配套设施。", 23.0)
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
    ("重点更新地块 (拆改建)", "rect_purple_fill"),
    ("历史保护核心 (保护修缮)", "rect_style_hist"),
    ("风貌敏感地带 (整治提升)", "rect_style_orange"),
    ("老旧住宅社区 (微更新)", "rect_style_green"),
    ("工业仓储遗存 (功能置换)", "rect_style_blue")
]

description_lines = [
    "1. 筛选评估：基于MPI综合评估指标（MPI值≤48.3的严重失能建筑），共筛选评估街区内719栋现状建筑，实施“微创织补、精准干预”分类更新模式分区。",
    "2. 四区分类：划分保护修缮区（伪满皇宫等历史建筑群）、整治提升区（过渡风貌建筑）、功能置换区（中车老旧工业厂房遗存）与拆改更新区（严重破损住宅与低效市场）。",
    "3. 导则控制：核心修缮区严禁新建建筑；整治提升区推行中式现代风貌立面改造；功能置换区引入青年公寓与众创空间；拆改区用于补足全龄配套设施。"
]