from pathlib import Path

import geopandas as gpd
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"

# Use the DR-013/DR-004 style full-page layout instead of the standard A3 title frame.
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
            if current_w + w <= max_len:
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

    ax.set_facecolor("#F8FAFC")
    ax.set_xlim(0, 141.42)
    ax.set_ylim(0, 100)
    ax.set_axis_off()

    # Draw grid
    for x in range(5, 140, 5):
        ax.plot([x, x], [0, 100], color="#E2E8F0", linewidth=0.6, alpha=0.5, zorder=0)
    for y in range(5, 100, 5):
        ax.plot([0, 141.42], [y, y], color="#E2E8F0", linewidth=0.6, alpha=0.5, zorder=0)

    # Header Panel
    ax.add_patch(mpatches.Rectangle((2.3, 88.7), 136.8, 7.3, facecolor="#E2E8F0", edgecolor="none", zorder=1))
    ax.add_patch(mpatches.Rectangle((2.0, 89.0), 136.8, 7.3, facecolor="#FFFFFF", edgecolor="#CBD5E1", linewidth=1.2, zorder=2))
    ax.add_patch(mpatches.Rectangle((2.0, 95.7), 136.8, 0.6, facecolor="#D97706", edgecolor="none", zorder=3))
    
    ax.text(3.5, 93.6, "建筑风貌识别图", color="#0F172A", ha="left", va="center",
            fontproperties=_font(font_prop, 26, "bold"), zorder=4)
    ax.text(3.5, 90.7, "展示项目在长春市宽城区伪满皇宫周边现状建筑风貌类型识别，为风貌分类整治和引导控制提供依据。",
            color="#334155", ha="left", va="center", fontproperties=_font(font_prop, 15.0), zorder=4)

    # Main map on the left
    ax.add_patch(mpatches.Rectangle((2.3, 3.7), 98.0, 83.0, facecolor="#E2E8F0", edgecolor="none", zorder=1))
    ax.add_patch(mpatches.Rectangle((2.0, 4.0), 98.0, 83.0, facecolor="#FFFFFF", edgecolor="#CBD5E1", linewidth=1.2, zorder=2))
    
    # Exact sub-axes of DR-004
    ax_map = fig.add_axes([3.0 / 141.42, 5.0 / 100.0, 96.0 / 141.42, 81.0 / 100.0], facecolor="#F8FAFC", zorder=3)
    ax_map.set_xlim(cx - view_w / 2, cx + view_w / 2)
    ax_map.set_ylim(cy - view_h / 2, cy + view_h / 2)
    ax_map.set_axis_off()
    ax_map.set_aspect("equal")

    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#D0E6F7", edgecolor="none", zorder=1)
        
    if buildings is not None and not buildings.empty:
        buildings_copy = buildings.copy()
        conditions = [
            (buildings_copy["prop_style"] == "historical"),
            (buildings_copy["prop_style"] == "park"),
            (buildings_copy["prop_style"] == "normal") | (buildings_copy["prop_style"].isna())
        ]
        choices = [
            "#B45309", # historical: 历史保护风貌 (古铜/褐金)
            "#0F766E", # park: 附属景观风貌 (青绿)
            "#E2E8F0"  # normal: 现代普通风貌 (浅灰)
        ]
        buildings_copy["color"] = np.select(conditions, choices, default="#E2E8F0")
        buildings_copy.plot(ax=ax_map, color=buildings_copy["color"], edgecolor="#475569", linewidth=0.15, zorder=2)
        
    if roads is not None and not roads.empty:
        for lvl, lw in [(1, 3.8), (2, 3.0), (3, 2.2), (4, 1.6)]:
            sub_gdf = roads[roads["level"] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax_map, color="#94A3B8", linewidth=lw, capstyle="round", joinstyle="round", zorder=3)
        for lvl, lw in [(1, 2.6), (2, 2.0), (3, 1.2), (4, 0.8)]:
            sub_gdf = roads[roads["level"] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax_map, color="#E2E8F0", linewidth=lw, capstyle="round", joinstyle="round", zorder=4)
                
    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#475569", linewidth=1.8, linestyle=(0, (6, 6)), zorder=5)
        
    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=7)

    # Right legend card
    ax.add_patch(mpatches.Rectangle((101.8, 66.7), 37.9, 20.3, facecolor="#E2E8F0", edgecolor="none", zorder=1))
    ax.add_patch(mpatches.Rectangle((101.5, 67.0), 37.9, 20.3, facecolor="#FFFFFF", edgecolor="#CBD5E1", linewidth=1.2, zorder=2))
    ax.add_patch(mpatches.Rectangle((101.5, 85.8), 37.9, 1.5, facecolor="#D97706", edgecolor="none", zorder=3))
    ax.text(103.5, 82.8, "图例 / LEGEND", color="#D97706", ha="left", va="center",
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)

    legend_rows = [
        ("规划研究范围", "outline_red"),
        ("城市道路", "road"),
        ("历史保护风貌建筑", "rect_style_hist"),
        ("公建及附属景观风貌", "rect_style_park"),
        ("普通住宅与现代风貌", "rect_style_norm"),
        ("城市水系", "water"),
    ]
    for i, (label, style) in enumerate(legend_rows):
        x = 103.5 + (i % 2) * 18.0
        y = 80.0 - (i // 2) * 3.3
        if style == "outline_red":
            ax.add_patch(mpatches.Rectangle((x, y - 0.8), 2.7, 1.7, facecolor="none", edgecolor="#FF3B30", linewidth=1.8, zorder=4))
        elif style == "rect_style_hist":
            ax.add_patch(mpatches.Rectangle((x, y - 0.8), 2.7, 1.7, facecolor="#B45309", edgecolor="#475569", linewidth=0.5, zorder=4))
        elif style == "rect_style_park":
            ax.add_patch(mpatches.Rectangle((x, y - 0.8), 2.7, 1.7, facecolor="#0F766E", edgecolor="#475569", linewidth=0.5, zorder=4))
        elif style == "rect_style_norm":
            ax.add_patch(mpatches.Rectangle((x, y - 0.8), 2.7, 1.7, facecolor="#E2E8F0", edgecolor="#475569", linewidth=0.5, zorder=4))
        elif style == "water":
            ax.add_patch(mpatches.Rectangle((x, y - 0.8), 2.7, 1.7, facecolor="#D0E6F7", edgecolor="none", zorder=4))
        elif style == "road":
            ax.add_patch(mpatches.Rectangle((x, y - 0.55), 2.7, 1.1, facecolor="#E2E8F0", edgecolor="none", zorder=4))
        ax.text(x + 3.6, y, label, color="#334155", ha="left", va="center",
                fontproperties=_font(font_prop, 13.5), zorder=4)

    # Scale Bar
    scale_len = 500 / (view_w / 96.0)
    x_start = 120.45 - scale_len / 2
    x_end = x_start + scale_len
    y_bar = 68.7
    ax.plot([x_start, x_end], [y_bar, y_bar], color="#0F172A", linewidth=1.5, zorder=4)
    for x_tick in [x_start, x_start + scale_len / 2, x_end]:
        ax.plot([x_tick, x_tick], [y_bar - 0.8, y_bar + 0.8], color="#0F172A", linewidth=1.5, zorder=4)
    ax.text(x_start, 70.5, "0", color="#334155", ha="center", va="center", fontproperties=_font(font_prop, 11), zorder=4)
    ax.text(x_start + scale_len / 2, 70.5, "250m", color="#334155", ha="center", va="center", fontproperties=_font(font_prop, 11), zorder=4)
    ax.text(x_end, 70.5, "500m", color="#334155", ha="center", va="center", fontproperties=_font(font_prop, 11), zorder=4)
    scale_ratio = view_w / 0.31968
    scale_rounded = round(scale_ratio / 500) * 500
    ax.text((x_start + x_end) / 2, 67.4, f"比例尺 1:{scale_rounded}", color="#334155", ha="center", va="center",
            fontproperties=_font(font_prop, 11, "bold"), zorder=4)

    # Right explanation card
    ax.add_patch(mpatches.Rectangle((101.8, 3.7), 37.9, 61.3, facecolor="#E2E8F0", edgecolor="none", zorder=1))
    ax.add_patch(mpatches.Rectangle((101.5, 4.0), 37.9, 61.3, facecolor="#FFFFFF", edgecolor="#CBD5E1", linewidth=1.2, zorder=2))
    ax.add_patch(mpatches.Rectangle((101.5, 63.8), 37.9, 1.5, facecolor="#D97706", edgecolor="none", zorder=3))
    ax.text(103.5, 61.0, "风貌说明 / STYLE ANALYSIS", color="#D97706", ha="left", va="center",
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)

    rows = [
        ("1. 风貌构成", "区内历史保护风貌占比约3.2%，集中在伪满皇宫周边；普通居住风貌占主导，整体风貌协调度有待提升。"),
        ("2. 界面杂乱", "局部街区存在杂乱搭接及立面风貌破损，严重削弱了历史文化街区的空间质量与文化氛围，缺乏统一的导则引导。"),
        ("3. 整治策略", "实行分类整治，对历史建筑修缮复原，对普通住宅立面进行微改造协调，消除风貌冲突，营造和谐的历史共振街区。"),
    ]
    y = 56.0
    for title, body in rows:
        ax.text(103.5, y, title, color="#0F172A", ha="left", va="top",
                fontproperties=_font(font_prop, 15.0, "bold"), zorder=4)
        y -= 2.5
        for line in wrap_text(body, 44).split("\n"):
            ax.text(103.5, y, line, color="#334155", ha="left", va="top",
                    fontproperties=_font(font_prop, 15.0), zorder=4)
            y -= 2.85
        y -= 2.2

        # Floating Windrose (Pure Black, 12.0 x 12.0) with soft white radial gradient backdrop
    try:
        from pathlib import Path as _Path

        import numpy as _np
        from PIL import Image as _PIL_Image
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
    ("历史保护风貌建筑", "rect_style_hist"),
    ("公建及附属景观风貌", "rect_style_park"),
    ("普通住宅与现代风貌", "rect_style_norm"),
    ("城市水系", "rect_water"),
    ("城市道路", "rect_road"),
]

description_lines = [
    "1. 风貌构成：区内历史保护风貌占比约3.2%，集中在伪满皇宫周边；普通居住风貌占主导，整体风貌协调度有待提升。",
    "2. 界面杂乱：局部街区存在杂乱搭接及立面风貌破损，严重削弱了历史文化街区的空间质量与文化氛围，缺乏统一的导则引导。",
    "3. 整治策略：实行分类整治，对历史建筑修缮复原，对普通住宅立面进行微改造协调，消除风貌冲突，营造和谐的历史共振街区。"
]