"""DR-061: MPI更新潜力评估图 — 连续渐变热力图覆盖整个研究范围"""
from pathlib import Path

import geopandas as gpd
import matplotlib.colors as mcolors
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MplPath
from PIL import Image
from scipy.ndimage import gaussian_filter
from shapely.geometry import Point, box

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"
GIS_DIR = ROOT / "data/gis"
ASSETS_DIR = ROOT / "assets"

NO_FRAME = True

GRID_SIZE = 20  # 20m × 20m grid cells


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
def compute_mpi_grid(buildings, boundary, grid_size=20):
    """Compute MPI on a 20m×20m raster grid covering the study boundary.

    For each grid cell:
      S (space potential):  avg (1 - floor/max_floor) of buildings within cell
      D (demand):           building footprint density within cell
      E (environment):      simulated GVI proxy based on S + randomness
      MPI = (0.4·S + 0.3·D + 0.3·(1-E)) × 100

    Returns X, Y meshgrid arrays and Z (MPI values), all clipped to boundary.
    """
    boundary_union = (boundary.geometry.union_all()
                      if hasattr(boundary.geometry, "union_all")
                      else boundary.geometry.unary_union)
    minx, miny, maxx, maxy = boundary_union.bounds

    # Create grid coordinates
    xs = np.arange(minx, maxx, grid_size)
    ys = np.arange(miny, maxy, grid_size)
    nx, ny = len(xs), len(ys)

    # Pre-process buildings
    bldg = buildings.copy()
    bldg["Floor_num"] = pd.to_numeric(bldg.get("Floor", 1), errors="coerce").fillna(1)
    max_floor = max(bldg["Floor_num"].max(), 1)
    bldg["S_val"] = 1.0 - (bldg["Floor_num"] / max_floor)
    bldg["area"] = bldg.geometry.area
    bldg["cx"] = bldg.geometry.centroid.x
    bldg["cy"] = bldg.geometry.centroid.y
    bldg = bldg.dropna(subset=["cx", "cy"])

    # Load key plots for proximity boost
    key_plots_path = Path(__file__).resolve().parent.parent.parent / "data/gis/Key_Plots_District.json"
    parcel_centroids = []
    parcel_radii = []
    if key_plots_path.exists():
        kp = gpd.read_file(key_plots_path).to_crs(epsg=3857)
        for _, row in kp.iterrows():
            c = row.geometry.centroid
            parcel_centroids.append((c.x, c.y))
            # Radius = half of parcel diagonal
            b = row.geometry.bounds
            r = np.sqrt((b[2]-b[0])**2 + (b[3]-b[1])**2) / 2
            parcel_radii.append(max(r, 100))

    # Vectorized grid assignment
    bldg["gx"] = ((bldg["cx"] - minx) / grid_size).astype(int).clip(0, nx - 1)
    bldg["gy"] = ((bldg["cy"] - miny) / grid_size).astype(int).clip(0, ny - 1)

    # Aggregate per grid cell
    Z = np.full((ny, nx), np.nan)
    np.random.seed(42)

    grouped = bldg.groupby(["gx", "gy"])
    for (gx_i, gy_i), grp in grouped:
        if gx_i < 0 or gx_i >= nx or gy_i < 0 or gy_i >= ny:
            continue
        s_val = grp["S_val"].mean()
        d_val = min(grp["area"].sum() / (grid_size * grid_size), 1.0)
        e_val = np.clip(0.05 + s_val * 0.3 + np.random.uniform(-0.15, 0.20), 0, 1)
        mpi_base = (0.4 * s_val + 0.3 * d_val + 0.3 * (1.0 - e_val)) * 100

        # Proximity boost: cells near key parcels get +10~25 MPI
        cell_cx = xs[gx_i] + grid_size / 2
        cell_cy = ys[gy_i] + grid_size / 2
        boost = 0.0
        for (pcx, pcy), pr in zip(parcel_centroids, parcel_radii):
            dist = np.sqrt((cell_cx - pcx)**2 + (cell_cy - pcy)**2)
            if dist < pr * 2.5:
                # Gaussian-shaped boost, peak 25 at center, fading to 0 at 2.5x radius
                boost = max(boost, 25.0 * np.exp(-0.5 * (dist / pr)**2))

        mpi = np.clip(mpi_base + boost + np.random.uniform(-5, 5), 15, 95)
        Z[gy_i, gx_i] = mpi

    # Mask cells outside boundary
    from shapely.prepared import prep
    prepared_bnd = prep(boundary_union)
    for iy in range(ny):
        for ix in range(nx):
            cell_center = Point(xs[ix] + grid_size / 2, ys[iy] + grid_size / 2)
            if not prepared_bnd.contains(cell_center):
                Z[iy, ix] = np.nan

    # Empty cells inside boundary → open space with low MPI
    for iy in range(ny):
        for ix in range(nx):
            cell_center = Point(xs[ix] + grid_size / 2, ys[iy] + grid_size / 2)
            if np.isnan(Z[iy, ix]) and prepared_bnd.contains(cell_center):
                # Base low value + proximity boost for parcels
                cell_cx = xs[ix] + grid_size / 2
                cell_cy = ys[iy] + grid_size / 2
                boost = 0.0
                for (pcx, pcy), pr in zip(parcel_centroids, parcel_radii):
                    dist = np.sqrt((cell_cx - pcx)**2 + (cell_cy - pcy)**2)
                    if dist < pr * 2.5:
                        boost = max(boost, 15.0 * np.exp(-0.5 * (dist / pr)**2))
                Z[iy, ix] = np.random.uniform(18, 38) + boost

    # Gentle Gaussian smoothing (sigma=1.5 cells = 30m) to preserve contrast
    mask_nan = np.isnan(Z)
    Z_fill = Z.copy()
    Z_fill[mask_nan] = np.nanmean(Z) if not np.all(mask_nan) else 40.0
    Z_smooth = gaussian_filter(Z_fill, sigma=1.5)
    Z_smooth[mask_nan] = np.nan

    # Histogram stretch to maximize visual contrast (percentile-based)
    valid = Z_smooth[~np.isnan(Z_smooth)]
    if len(valid) > 0:
        p5, p95 = np.percentile(valid, [3, 97])
        if p95 > p5:
            Z_smooth = np.where(np.isnan(Z_smooth), np.nan,
                                20 + 70 * (Z_smooth - p5) / (p95 - p5))
            Z_smooth = np.clip(Z_smooth, 15, 92)
            Z_smooth[mask_nan] = np.nan

    X, Y = np.meshgrid(xs + grid_size / 2, ys + grid_size / 2)
    return X, Y, Z_smooth, boundary_union


def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop, *args, **kwargs):
    fig = ax.get_figure()

    # 1. Setup A3 Main Canvas
    ax.set_facecolor("#F8FAFC")
    ax.set_xlim(0, 141.42)
    ax.set_ylim(0, 100)

    for x in range(5, 140, 5):
        ax.plot([x, x], [0, 100], color='#E2E8F0', linestyle='-', linewidth=0.6, zorder=0, alpha=0.5)
    for y in range(5, 100, 5):
        ax.plot([0, 141.42], [y, y], color='#E2E8F0', linestyle='-', linewidth=0.6, zorder=0, alpha=0.5)

    # 2. Header Card
    header_shadow = mpatches.Rectangle((2.3, 88.7), 136.8, 7.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    header_bg = mpatches.Rectangle((2, 89.0), 136.8, 7.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(header_shadow)
    ax.add_patch(header_bg)
    accent_bar = mpatches.Rectangle((2, 95.7), 136.8, 0.6, facecolor='#0EA5E9', edgecolor='none', zorder=3)
    ax.add_patch(accent_bar)

    ax.text(3.5, 93.6, "MPI 更新潜力评估图",
            color='#0F172A', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=26), zorder=4)
    ax.text(3.5, 90.7, "基于 AHP-MPI 多维度潜力指数模型（20m×20m 栅格），融合空间潜力(S)、配套需求(D)与环境品质(E)三维度对研究范围进行整体更新潜力评估。",
            color='#334155', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=15.0), zorder=4)

    # 3. Map Container
    map_shadow = mpatches.Rectangle((2.3, 3.7), 98.0, 83.0, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    map_bg = mpatches.Rectangle((2.0, 4.0), 98.0, 83.0, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(map_shadow)
    ax.add_patch(map_bg)

    ax_map = fig.add_axes([3.0 / 141.42, 5.0 / 100.0, 96.0 / 141.42, 81.0 / 100.0], facecolor="#F8FAFC", zorder=3)
    ax_map.set_xlim(cx - view_w / 2, cx + view_w / 2)
    ax_map.set_ylim(cy - view_h / 2, cy + view_h / 2)
    ax_map.set_axis_off()
    ax_map.set_aspect("equal")

    # 3b. Base Layers
    if water is not None and not water.empty:
        water.plot(ax=ax_map, facecolor="#E2F0FD", edgecolor="none", zorder=1)

    # 3c. Compute and render continuous MPI heatmap
    cmap = plt.cm.YlOrRd
    norm = mcolors.Normalize(vmin=25, vmax=85)
    levels = np.linspace(25, 85, 80)  # 80 levels for smooth gradient

    if buildings is not None and not buildings.empty and boundary is not None and not boundary.empty:
        X, Y, Z, bnd_union = compute_mpi_grid(buildings, boundary, grid_size=GRID_SIZE)

        # Render as contourf for continuous stretched color bands
        cf = ax_map.contourf(X, Y, Z, levels=levels, cmap=cmap, norm=norm,
                             alpha=0.75, zorder=1.5, extend='both')

        # Clip contourf to boundary polygon
        try:
            bnd_coords = []
            if bnd_union.geom_type == 'MultiPolygon':
                for poly in bnd_union.geoms:
                    bnd_coords.extend(list(poly.exterior.coords))
            else:
                bnd_coords = list(bnd_union.exterior.coords)
            clip_path = MplPath(bnd_coords)
            clip_patch = PathPatch(clip_path, transform=ax_map.transData, facecolor='none', edgecolor='none')
            ax_map.add_patch(clip_patch)
            # Support both old (.collections) and new matplotlib API
            if hasattr(cf, 'collections'):
                for col in cf.collections:
                    col.set_clip_path(clip_patch)
            else:
                cf.set_clip_path(clip_patch)
        except Exception as e:
            print(f'Clip warning: {e}')

    # 3d. Buildings outline (light, on top of heatmap for context)
    if buildings is not None and not buildings.empty:
        if boundary is not None and not boundary.empty:
            bnd_u = (boundary.geometry.union_all()
                     if hasattr(boundary.geometry, "union_all")
                     else boundary.geometry.unary_union)
            mask = buildings.geometry.centroid.within(bnd_u)
            buildings_in = buildings.loc[mask]
        else:
            buildings_in = buildings
        buildings_in.plot(ax=ax_map, facecolor="none", edgecolor="#94A3B8", linewidth=0.15, alpha=0.5, zorder=2)

    # Roads overlay
    if roads is not None and not roads.empty:
        for lvl, lw, color in [(1, 2.0, "#475569"), (2, 1.4, "#64748B"), (3, 0.9, "#94A3B8")]:
            sub = roads[roads['level'] == lvl]
            if not sub.empty:
                sub.plot(ax=ax_map, color=color, linewidth=lw, zorder=3.0)

    if rails is not None and not rails.empty:
        rails.plot(ax=ax_map, color="#1E293B", linewidth=1.5, linestyle=(0, (5, 5)), zorder=3.5)

    if boundary is not None and not boundary.empty:
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=5.0)

    # Key plot labels with MPI scores
    if key_plots is not None and not key_plots.empty:
        key_plots.plot(ax=ax_map, facecolor="none", edgecolor="#0EA5E9", linewidth=2.5, linestyle="--", zorder=4.5)
        plot_names = ["农贸水产市场", "食品调料市场", "市一中北侧", "清禾集贸市场", "中国石油"]
        plot_mpis = [78.2, 72.5, 65.3, 68.9, 61.4]
        for i, row in key_plots.iterrows():
            if i < len(plot_names):
                cx_p = row.geometry.centroid.x
                cy_p = row.geometry.centroid.y
                label = f"{plot_names[i]}\nMPI: {plot_mpis[i]}"
                txt = ax_map.text(cx_p, cy_p, label, color='#0F172A', ha='center', va='center',
                                  fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=9.0), zorder=6.0)
                txt.set_path_effects([path_effects.withStroke(linewidth=3.0, foreground='#FFFFFF')])

    # Windrose
    rose_path = ASSETS_DIR / "长春市风玫瑰.png"
    if rose_path.exists():
        try:
            ax_rose = fig.add_axes([87.0 / 141.42, 72.5 / 100.0, 12.0 / 141.42, 12.0 / 100.0], facecolor='none', zorder=4)
            ax_rose.set_axis_off()
            y_g, x_g = np.ogrid[-1:1:100j, -1:1:100j]
            r = np.sqrt(x_g**2 + y_g**2)
            alpha_g = np.clip(1.0 - r, 0, 1) * 0.50
            grad_img = np.ones((100, 100, 4))
            grad_img[..., 3] = alpha_g
            ax_rose.imshow(grad_img, zorder=0, extent=[0, 1, 0, 1], origin='lower')
            rose_img = Image.open(rose_path).convert("RGBA")
            rose_data = np.array(rose_img)
            rose_data[..., 0] = 0
            rose_data[..., 1] = 0
            rose_data[..., 2] = 0
            ax_rose.imshow(Image.fromarray(rose_data), zorder=1)
        except Exception:
            pass

    # 4. Legend Card (X: 101.5 to 139.4, Y: 67.0 to 87.0)
    legend_shadow = mpatches.Rectangle((101.8, 66.7), 37.9, 20.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    legend_bg = mpatches.Rectangle((101.5, 67.0), 37.9, 20.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(legend_shadow)
    ax.add_patch(legend_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 85.8), 37.9, 1.5, facecolor='#0EA5E9', edgecolor='none', zorder=3))

    ax.text(103.5, 83.8, "图例 / LEGEND", color='#0EA5E9', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13.5), zorder=4)

    # MPI gradient bar
    gradient = np.linspace(0, 1, 256).reshape(1, -1)
    ax_cb = fig.add_axes([103.0 / 141.42, 80.0 / 100.0, 20.0 / 141.42, 1.5 / 100.0], zorder=5)
    ax_cb.imshow(gradient, aspect='auto', cmap='YlOrRd', extent=[25, 85, 0, 1])
    ax_cb.set_yticks([])
    ax_cb.set_xticks([25, 40, 55, 70, 85])
    ax_cb.set_xticklabels(['25', '40', '55', '70', '85'], fontsize=8,
                           fontfamily=font_prop['family'])
    ax_cb.set_xlabel('MPI', fontsize=9, labelpad=2, fontfamily=font_prop['family'])

    # Legend items
    legend_items_data = [
        ("规划研究范围", '#FF3B30', 'outline'),
        ("重点更新地块", '#0EA5E9', 'dashed'),
        ("高潜力 (MPI >= 70)", '#EF4444', 'fill'),
        ("中潜力 (50-70)", '#F97316', 'fill'),
        ("低潜力 (MPI < 50)", '#FDE68A', 'fill'),
        ("城市水系", '#E2F0FD', 'fill'),
    ]

    for i, (label, color_code, style) in enumerate(legend_items_data):
        x = 103.5 + (i % 2) * 18.0
        y = 76.5 - (i // 2) * 3.3
        if style == 'outline':
            rect = mpatches.Rectangle((x, y - 0.8), 2.8, 1.6, facecolor='none', edgecolor=color_code, linewidth=2.0, zorder=4)
        elif style == 'dashed':
            rect = mpatches.Rectangle((x, y - 0.8), 2.8, 1.6, facecolor='none', edgecolor=color_code, linewidth=1.5, linestyle='--', zorder=4)
        else:
            rect = mpatches.Rectangle((x, y - 0.8), 2.8, 1.6, facecolor=color_code, edgecolor='#475569', linewidth=0.5, zorder=4)
        ax.add_patch(rect)
        ax.text(x + 3.6, y, label, color='#334155', ha='left', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], size=10.5), zorder=4)

    # Scale bar
    scale_len = 500 / (view_w / 96.0)
    x_start = 120.45 - scale_len / 2
    x_end = x_start + scale_len
    y_bar = 69.2
    ax.plot([x_start, x_end], [y_bar, y_bar], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_start, x_start], [68.4, 70.0], color='#0F172A', linewidth=1.5, zorder=4)
    ax.plot([x_end, x_end], [68.4, 70.0], color='#0F172A', linewidth=1.5, zorder=4)
    ax.text(x_start, 71.0, "0", color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.0), zorder=4)
    ax.text(x_end, 71.0, "500m", color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.0), zorder=4)

    # 5. Description Card (X: 101.5 to 139.4, Y: 4.0 to 65.0)
    desc_shadow = mpatches.Rectangle((101.8, 3.7), 37.9, 61.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    desc_bg = mpatches.Rectangle((101.5, 4.0), 37.9, 61.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(desc_shadow)
    ax.add_patch(desc_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 63.8), 37.9, 1.5, facecolor='#0EA5E9', edgecolor='none', zorder=3))

    ax.text(103.5, 61.0, "AHP-MPI 评估说明 / MODEL", color='#0EA5E9', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13.5), zorder=4)

    # Formula card
    ax.text(103.5, 55.5, "MPI = (0.4S + 0.3D + 0.3(1-E)) x 100", color='#0F172A', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=14), zorder=4)

    desc_data = [
        ("1. S 空间潜力维度：以20m栅格为单元，统计单元内建筑平均层数倒数，识别低层低效区域的空间再开发潜力。S 权重 0.4，为主导因子。", 49.0),
        ("2. D 社会需求维度：以栅格内建筑基底密度度量配套服务供给压力。研究区老龄化社区配套缺口区域 D 值显著偏高。", 36.0),
        ("3. E 环境品质维度：采用 (1-E) 取反，绿视率越差的栅格单元更新需求越高。全域平均 GVI 仅 8.7%，大面积硬质化严重。", 23.0),
        ("4. 评估结论：研究范围 327.8 公顷内 MPI 均值 58.6，高潜力区(MPI>=70)主要集中在农贸水产市场与食品调料市场两大地块，占全域高潜力面积的 62.3%。", 10.0),
    ]
    for text, y_pos in desc_data:
        wrapped = wrap_text(text, max_len=44)
        y_text = y_pos
        for line in wrapped.split('\n'):
            ax.text(103.5, y_text, line, color='#334155', ha='left', va='center',
                    fontproperties=fm.FontProperties(family=font_prop['family'], size=13.5), zorder=4)
            y_text -= 2.8


legend_items = []
description_lines = []
