import os
from pathlib import Path

import geopandas as gpd
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"

# Use the DR-013/DR-004 style full-page layout instead of the standard A3 title frame.
NO_FRAME = True

def wrap_text(text, max_len=30):
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
    
    ax.text(3.5, 93.6, "研究范围图", color="#0F172A", ha="left", va="center",
            fontproperties=_font(font_prop, 26, "bold"), zorder=4)
    ax.text(3.5, 90.7, "展示项目的规划设计研究范围与五大重点更新改造地块的地理本底分布。",
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

    # 1. Satellite Base (with high-res TIFF dynamic loading)
    tif_path = None
    from src.config.runtime import resolve_path
    graduate_dir = resolve_path("output/graduate")
    if graduate_dir.exists():
        for root, _dirs, files in os.walk(graduate_dir):
            for file in files:
                if "2604161335" in file and file.lower().endswith(".tif"):
                    tif_path = Path(root) / file
                    break
    
    if not tif_path:
        album_dir = resolve_path("output/album/images")
        if album_dir.exists():
            for root, _dirs, files in os.walk(album_dir):
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
            
    # 2. Transparent Blue Water
    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#0066CC", edgecolor="none", alpha=0.35, zorder=1)

    # 3. Outer Mask
    try:
        from shapely.geometry import box
        large_box = box(cx - view_w, cy - view_h, cx + view_w, cy + view_h)
        boundary_union = boundary.geometry.union_all() if hasattr(boundary.geometry, "union_all") else boundary.geometry.unary_union
        mask_poly = large_box.difference(boundary_union)
        gpd.GeoSeries([mask_poly]).plot(ax=ax_map, facecolor="#FAFAFC", alpha=0.45, edgecolor="none", zorder=3)
    except Exception as e:
        print(f"Error drawing boundary mask: {e}")

    # 4. Rails
    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#475569", linewidth=1.8, linestyle=(0, (6, 6)), zorder=4)

    # 5. Key Plots
    if key_plots is not None and not key_plots.empty:
        key_plots.plot(ax=ax_map, facecolor="#3B82F6", alpha=0.25, edgecolor="none", zorder=4.8)
        key_plots.plot(ax=ax_map, facecolor="none", edgecolor="#2563EB", linewidth=2.2, zorder=5)
        for idx, row in key_plots.iterrows():
            geom = row.geometry
            cx_kp = geom.centroid.x
            cy_kp = geom.centroid.y
            name_kp = row.get("name", f"地块 {idx+1}")
            txt = ax_map.text(cx_kp, cy_kp, name_kp, color='#1D4ED8', ha='center', va='center', 
                           fontproperties=_font(font_prop, 12, "bold"), zorder=6)
            txt.set_path_effects([path_effects.withStroke(linewidth=3, foreground='#FFFFFF')])

    # 6. Red Boundary Line
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
        ("重点更新地块", "outline_blue"),
        ("伊通河水系", "water"),
        ("现状铁路线", "rail"),
        ("卫星遥感底图", "sat_base"),
    ]
    for i, (label, style) in enumerate(legend_rows):
        x = 103.5 + (i % 2) * 18.0
        y = 80.0 - (i // 2) * 3.3
        if style == "outline_red":
            ax.add_patch(mpatches.Rectangle((x, y - 0.8), 2.7, 1.7, facecolor="none", edgecolor="#FF3B30", linewidth=1.8, zorder=4))
        elif style == "outline_blue":
            ax.add_patch(mpatches.Rectangle((x, y - 0.8), 2.7, 1.7, facecolor="none", edgecolor="#2563EB", linewidth=1.8, zorder=4))
        elif style == "water":
            ax.add_patch(mpatches.Rectangle((x, y - 0.8), 2.7, 1.7, facecolor="#0066CC", alpha=0.5, edgecolor="none", zorder=4))
        elif style == "rail":
            ax.plot([x, x + 2.7], [y, y], color="#475569", linewidth=1.8, linestyle=(0, (5, 4)), zorder=4)
        elif style == "sat_base":
            ax.add_patch(mpatches.Rectangle((x, y - 0.8), 2.7, 1.7, facecolor="#64748B", alpha=0.6, edgecolor="none", zorder=4))
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
    ax.text(103.5, 61.0, "范围说明 / SCOPE ANALYSIS", color="#D97706", ha="left", va="center",
            fontproperties=_font(font_prop, 13.5, "bold"), zorder=4)

    rows = [
        ("1. 核心范围", "规划确定的更新改造研究边界西起亚泰快速路，东至东九条，南至长春大街，北至长白路，总用地面积约为 150 公顷。"),
        ("2. 重点地块", "规划重点针对片区内 5 个低效国有或集体资产地块进行城市设计与活力针灸，包括老水产批发市场和中车旧厂区等。"),
        ("3. 现状本底", "周边路网成熟，紧邻长春站交通门户，是缝合老宽城铁北地区与长春历史文化中轴线的空间关键锁扣。"),
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
    ("五大重点更新地块", "rect_blue_fill"),
    ("伊通河水系", "rect_water"),
    ("卫星遥感影像", "rect_sat_base"),
]

description_lines = [
    "1. 核心范围：规划确定的更新改造研究边界西起亚泰快速路，东至东九条，南至长春大街，北至长白路，总用地面积约为 150 公顷。",
    "2. 重点地块：规划重点针对片区内 5 个低效国有或集体资产地块进行城市设计与活力针灸，包括老水产批发市场和中车旧厂区等。",
    "3. 现状本底：周边路网成熟，紧邻长春站交通门户，是缝合老宽城铁北地区与长春历史文化中轴线的空间关键锁扣。"
]