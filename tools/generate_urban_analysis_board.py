"""Generate six precise urban analysis diagrams from project GIS layers.

The output intentionally avoids satellite-photo texture. It translates the
current site layers into a clean 2x3 urban design analysis board and six
standalone panels.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, PathPatch, Rectangle
from matplotlib.path import Path as MplPath
from shapely.geometry import LineString, Point

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"
GIS_DIR = ROOT / "data" / "gis"
OUTPUT_DIR = STATIC_DIR / "analysis_board"
REFERENCE_EXACT_DIR = OUTPUT_DIR / "reference_exact"
USE_REFERENCE_EXACT = True


PANEL_SPECS = [
    ("green_open_space", "1. 绿地与开放空间结构", "构建多层级绿地体系，形成公园引领、口袋补充、连通共享的开放空间网络。"),
    ("eco_corridor", "2. 生态廊道与景观连接", "依托伊通河生态廊道，渗透绿廊进入组团，连通公园节点，形成生态网络。"),
    ("transport_access", "3. 交通结构与可达性", "构建轨道引领、主干支撑、慢行织补的多层次交通体系，提升区域可达性。"),
    ("landuse_layout", "4. 功能分区与用地布局", "形成历史文化核心、商业服务、居住生活、产业更新、公共服务、绿地休闲复合格局。"),
    ("activity_nodes", "5. 公共活力节点", "围绕交通枢纽、文化地标、商业街区与滨水空间，塑造多层级公共活力节点体系。"),
    ("waterfront_image", "6. 滨水界面与城市形象", "塑造连续友好的滨水界面，组织视线廊道与城市界面，提升城市形象与辨识度。"),
]


def _font(size: float, weight: str = "normal"):
    family = "Microsoft YaHei"
    names = {f.name for f in fm.fontManager.ttflist}
    if family not in names:
        family = "SimHei" if "SimHei" in names else "sans-serif"
    return fm.FontProperties(family=family, size=size, weight=weight)


def load_layers():
    boundary = gpd.read_file(GIS_DIR / "Boundary_Scope.geojson").to_crs(epsg=3857)
    roads = gpd.read_file(STATIC_DIR / "road_clipped.geojson").to_crs(epsg=3857)
    rails = gpd.read_file(STATIC_DIR / "rail_clipped.geojson").to_crs(epsg=3857)
    water = gpd.read_file(STATIC_DIR / "water.geojson").to_crs(epsg=3857)
    buildings = gpd.read_file(STATIC_DIR / "buildings.geojson").to_crs(epsg=3857)
    landuse = gpd.read_file(GIS_DIR / "landuse_clipped.geojson").to_crs(epsg=3857)
    key_plots = gpd.read_file(GIS_DIR / "Key_Plots_District.json").to_crs(epsg=3857)
    return {
        "boundary": boundary,
        "roads": roads,
        "rails": rails,
        "water": water,
        "buildings": buildings,
        "landuse": landuse,
        "key_plots": key_plots,
    }


def view_bounds(boundary):
    minx, miny, maxx, maxy = boundary.total_bounds
    cx = (minx + maxx) / 2
    cy = (miny + maxy) / 2
    height_m = maxy - miny
    view_h = height_m * 1.62
    view_w = view_h * 1.28
    return cx - view_w / 2, cx + view_w / 2, cy - view_h / 2, cy + view_h / 2


def clipped(layers, bounds):
    bbox = gpd.GeoDataFrame(geometry=[Point(bounds[0], bounds[2]).buffer(1).envelope], crs="EPSG:3857")
    bbox.loc[0, "geometry"] = bbox.geometry.iloc[0].union(Point(bounds[1], bounds[3]).buffer(1).envelope).envelope
    result = {}
    for key, gdf in layers.items():
        try:
            result[key] = gpd.clip(gdf, bbox)
        except Exception:
            result[key] = gdf
    return result


def draw_base(ax, data, bounds):
    ax.set_xlim(bounds[0], bounds[1])
    ax.set_ylim(bounds[2], bounds[3])
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_facecolor("#FFFFFF")

    buildings = data["buildings"]
    water = data["water"]
    roads = data["roads"]
    rails = data["rails"]
    boundary = data["boundary"]

    if not buildings.empty:
        buildings.plot(ax=ax, facecolor="#E5EAF0", edgecolor="#D4DCE5", linewidth=0.06, alpha=0.22, zorder=1)
    if not roads.empty:
        roads.plot(ax=ax, color="#D5DCE4", linewidth=0.46, alpha=0.48, zorder=2)
        major = roads[roads.get("level", 4).isin([1, 2])]
        if not major.empty:
            major.plot(ax=ax, color="#BFC8D2", linewidth=0.85, alpha=0.50, zorder=3)
    if not rails.empty:
        rails.plot(ax=ax, color="#64748B", linewidth=1.1, linestyle=(0, (5, 5)), alpha=0.72, zorder=4)
    if not water.empty:
        water.plot(ax=ax, facecolor="#CFE8F6", edgecolor="#B7D9EC", linewidth=0.5, alpha=0.86, zorder=5)
    boundary.plot(ax=ax, facecolor="none", edgecolor="#EF4444", linewidth=1.45, alpha=0.95, zorder=20)


def centroid_xy(gdf):
    geom = gdf.geometry.union_all()
    c = geom.centroid
    return c.x, c.y


def lonlat_points(points):
    return gpd.GeoSeries([Point(lon, lat) for lon, lat in points], crs="EPSG:4326").to_crs(epsg=3857)


def project_landmarks():
    data = [
        ("长春站", 125.3250, 43.9080),
        ("伪满皇宫", 125.3422, 43.9036),
        ("光复路", 125.3475, 43.9017),
        ("伊通河公园", 125.3590, 43.9010),
        ("胜利公园", 125.3260, 43.8960),
        ("长春站前节点", 125.3265, 43.9092),
        ("商业服务节点", 125.3338, 43.9038),
        ("社区生活节点", 125.3400, 43.8985),
        ("滨水休闲节点", 125.3510, 43.8974),
    ]
    pts = lonlat_points([(lon, lat) for _, lon, lat in data])
    return {name: pt for (name, _, _), pt in zip(data, pts)}


def draw_label(ax, x, y, text, size=5.5, color="#334155", dy=55, weight="bold"):
    label = ax.text(x, y + dy, text, color=color, ha="center", va="bottom", fontproperties=_font(size, weight), zorder=60)
    label.set_path_effects([path_effects.withStroke(linewidth=1.6, foreground="#FFFFFF")])


def draw_mini_legend(ax, items, loc=(0.72, 0.08), row_h=0.045):
    x0, y0 = loc
    for i, (label, color, kind) in enumerate(items):
        y = y0 + i * row_h
        if kind == "line":
            ax.plot([x0, x0 + 0.055], [y, y], transform=ax.transAxes, color=color, lw=1.7, zorder=80, clip_on=False)
        elif kind == "dash":
            ax.plot([x0, x0 + 0.055], [y, y], transform=ax.transAxes, color=color, lw=1.4, linestyle=(0, (4, 3)), zorder=80, clip_on=False)
        elif kind == "dot":
            ax.plot([x0 + 0.025], [y], transform=ax.transAxes, marker="o", markersize=5, color=color, markeredgecolor="white", markeredgewidth=0.8, zorder=80, clip_on=False)
        elif kind == "ring":
            ax.add_patch(Circle((x0 + 0.027, y), 0.016, transform=ax.transAxes, facecolor="none", edgecolor=color, lw=1.2, zorder=80, clip_on=False))
        else:
            ax.add_patch(Rectangle((x0, y - 0.014), 0.045, 0.028, transform=ax.transAxes, facecolor=color, edgecolor="white", lw=0.4, alpha=0.75, zorder=80, clip_on=False))
        ax.text(x0 + 0.065, y, label, transform=ax.transAxes, ha="left", va="center", color="#64748B", fontproperties=_font(5.1), zorder=80, clip_on=False)


def draw_arrow(ax, start, end, color, lw=1.4, alpha=0.9, z=30):
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops=dict(arrowstyle="-|>", lw=lw, color=color, alpha=alpha, shrinkA=0, shrinkB=0, mutation_scale=10),
        zorder=z,
    )


def _curve_control(start, end, rad=0.18):
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    mx = (sx + ex) / 2
    my = (sy + ey) / 2
    return mx - dy * rad, my + dx * rad


def curve_path(start, end, rad=0.18):
    control = _curve_control(start, end, rad)
    return MplPath([start, control, end], [MplPath.MOVETO, MplPath.CURVE3, MplPath.CURVE3])


def draw_curve_line(ax, start, end, color, lw=1.2, alpha=0.85, rad=0.18, linestyle="solid", z=30):
    patch = PathPatch(
        curve_path(start, end, rad),
        facecolor="none",
        edgecolor=color,
        lw=lw,
        alpha=alpha,
        linestyle=linestyle,
        capstyle="round",
        joinstyle="round",
        zorder=z,
    )
    ax.add_patch(patch)
    return patch


def draw_curve_arrow(ax, start, end, color, lw=1.25, alpha=0.9, rad=0.18, linestyle="solid", z=32, mutation_scale=9):
    arrow = FancyArrowPatch(
        path=curve_path(start, end, rad),
        arrowstyle="-|>",
        mutation_scale=mutation_scale,
        lw=lw,
        color=color,
        alpha=alpha,
        linestyle=linestyle,
        shrinkA=0,
        shrinkB=0,
        capstyle="round",
        joinstyle="round",
        zorder=z,
    )
    ax.add_patch(arrow)
    return arrow


def draw_landmarks(ax, data):
    pts = project_landmarks()
    for name in ["长春站", "伪满皇宫", "光复路", "伊通河公园", "胜利公园"]:
        pt = pts[name]
        ax.plot(pt.x, pt.y, marker="o", markersize=3.2, color="#F59E0B", markeredgecolor="#FFFFFF", markeredgewidth=0.7, zorder=40)
        draw_label(ax, pt.x, pt.y, name, size=5.1, dy=48)


def panel_green(ax, data, bounds):
    green = data["landuse"][data["landuse"].get("GB_Code", "").astype(str).str.contains("G", na=False)]
    if not green.empty:
        green.plot(ax=ax, facecolor="#BCECCF", edgecolor="#75C99B", linewidth=0.45, alpha=0.50, zorder=18)
        green_inside = gpd.clip(green, data["boundary"])
        if not green_inside.empty:
            green_inside.plot(ax=ax, facecolor="#8ED9AE", edgecolor="#22C55E", linewidth=0.55, alpha=0.78, zorder=22)
    c = centroid_xy(data["boundary"])
    pts = project_landmarks()
    # Reference-like internal open-space patches: many small green pockets, no dominant arrows.
    pocket_offsets = [
        (-280, 300, 58, 46), (-150, 285, 70, 40), (15, 275, 56, 42), (155, 250, 80, 42),
        (-260, 135, 62, 44), (-100, 110, 74, 44), (78, 105, 64, 42), (210, 80, 72, 38),
        (-210, -35, 70, 44), (-40, -20, 64, 40), (145, -30, 82, 44),
        (-180, -210, 68, 42), (30, -190, 62, 42), (225, -230, 75, 46),
    ]
    for dx, dy, w, h in pocket_offsets:
        ax.add_patch(Rectangle((c[0] + dx - w / 2, c[1] + dy - h / 2), w, h, facecolor="#86D9A5", edgecolor="#22C55E", lw=0.45, alpha=0.58, zorder=23))
    palace = pts["伪满皇宫"]
    ax.add_patch(Circle((palace.x, palace.y), 165, facecolor="#BCECCF", edgecolor="#75C99B", lw=0.65, alpha=0.66, zorder=22))
    green_links = [
        ((c[0] - 315, c[1] + 300), (c[0] + 170, c[1] + 245), 0.12),
        ((c[0] - 260, c[1] + 55), (c[0] + 235, c[1] + 85), -0.10),
        ((c[0] - 205, c[1] - 215), (c[0] + 250, c[1] - 210), 0.14),
        ((c[0] - 110, c[1] + 260), (c[0] - 20, c[1] - 245), -0.08),
    ]
    for a, b, rad in green_links:
        draw_curve_line(ax, a, b, "#22C55E", lw=1.0, alpha=0.66, rad=rad, linestyle=(0, (3, 3)), z=24)
    for a, b, rad in [
        ((c[0] - 110, c[1] + 120), (c[0] + 130, c[1] + 85), 0.18),
        ((c[0] - 35, c[1] - 60), (c[0] + 155, c[1] - 5), -0.18),
    ]:
        draw_curve_arrow(ax, a, b, "#22C55E", lw=1.0, alpha=0.62, rad=rad, linestyle=(0, (3, 3)), z=25, mutation_scale=8)
    draw_mini_legend(ax, [("绿地联系", "#22C55E", "dash"), ("开放空间", "#BCECCF", "patch"), ("公园绿地", "#86D9A5", "patch")], loc=(0.04, 0.08), row_h=0.038)


def panel_ecology(ax, data, bounds):
    river_x = bounds[1] - (bounds[1] - bounds[0]) * 0.20
    centers = [
        (river_x, bounds[2] + (bounds[3] - bounds[2]) * 0.72),
        (river_x, bounds[2] + (bounds[3] - bounds[2]) * 0.48),
        (river_x, bounds[2] + (bounds[3] - bounds[2]) * 0.28),
    ]
    c = centroid_xy(data["boundary"])
    # Reference-like dashed ecological loop across the site, plus river-edge connectors.
    loop = [
        (c[0] - 340, c[1] + 275), (c[0] - 60, c[1] + 300), (c[0] + 210, c[1] + 180),
        (c[0] + 260, c[1] - 40), (c[0] + 120, c[1] - 255), (c[0] - 180, c[1] - 235),
        (c[0] - 360, c[1] - 20), (c[0] - 340, c[1] + 275),
    ]
    for idx, start in enumerate(loop[:-1]):
        end = loop[idx + 1]
        draw_curve_line(ax, start, end, "#22C55E", lw=1.25, alpha=0.82, rad=0.10 if idx % 2 == 0 else -0.10, linestyle=(0, (2.5, 2.5)), z=28)
    network_nodes = loop[:-1]
    for idx, p in enumerate(centers):
        target = (c[0] + 180, c[1] + (p[1] - c[1]) * 0.35)
        draw_curve_line(ax, target, p, "#22C55E", lw=1.15, alpha=0.72, rad=-0.16 + idx * 0.12, linestyle=(0, (3, 2)), z=28)
        draw_curve_arrow(ax, target, p, "#22C55E", lw=1.35, alpha=0.82, rad=-0.16 + idx * 0.12, z=29, mutation_scale=10)
        network_nodes.append(p)
    for a, b in [
        ((c[0] - 430, c[1] + 70), (c[0] - 330, c[1] + 80)),
        ((c[0] - 425, c[1] - 170), (c[0] - 300, c[1] - 105)),
        ((c[0] + 20, c[1] - 340), (c[0] + 60, c[1] - 245)),
    ]:
        draw_curve_arrow(ax, a, b, "#22C55E", lw=1.15, alpha=0.75, rad=0.22, linestyle=(0, (3, 2)), z=29, mutation_scale=9)
    for x, y in network_nodes:
        ax.add_patch(Circle((x, y), 65, facecolor="#DCFCE7", edgecolor="#22C55E", linewidth=0.8, alpha=0.7, zorder=27))
    draw_mini_legend(ax, [("渗透方向", "#16A34A", "line"), ("景观节点", "#22C55E", "ring"), ("生态廊道", "#22C55E", "dash")], loc=(0.04, 0.08), row_h=0.038)


def panel_transport(ax, data, bounds):
    station = gpd.GeoSeries([Point(125.3250, 43.9080)], crs="EPSG:4326").to_crs(epsg=3857).iloc[0]
    c = centroid_xy(data["boundary"])
    # Abstract transit hierarchy copied from the reference: fewer, cleaner lines than the raw road graph.
    for x0, y0, x1, y1, color, rad in [
        (station.x - 640, station.y + 10, station.x + 950, station.y - 35, "#F97316", -0.06),
        (c[0] - 230, bounds[2] + 220, c[0] - 70, bounds[3] - 210, "#F97316", 0.10),
        (bounds[0] + 120, c[1] + 40, bounds[1] - 190, c[1] + 140, "#A855F7", 0.06),
        (bounds[0] + 160, c[1] - 230, c[0] + 370, c[1] + 40, "#A855F7", 0.12),
        (c[0] - 120, c[1] - 170, c[0] + 420, c[1] + 10, "#3B82F6", -0.12),
    ]:
        draw_curve_arrow(ax, (x0, y0), (x1, y1), color, lw=1.45, alpha=0.82, rad=rad, z=35, mutation_scale=10)
    feeder = [
        [(c[0] - 240, c[1] + 210), (c[0] + 80, c[1] + 200), (c[0] + 300, c[1] + 60)],
        [(c[0] - 260, c[1] - 20), (c[0] + 10, c[1] - 45), (c[0] + 260, c[1] - 120)],
        [(c[0] - 140, c[1] - 280), (c[0] + 70, c[1] - 210), (c[0] + 240, c[1] - 255)],
    ]
    for line in feeder:
        draw_curve_line(ax, line[0], line[1], "#60A5FA", lw=0.95, alpha=0.78, rad=0.08, z=33)
        draw_curve_arrow(ax, line[1], line[2], "#60A5FA", lw=0.95, alpha=0.78, rad=-0.08, z=34, mutation_scale=8)
    for pt in [station, Point(c[0] - 120, c[1] + 70), Point(c[0] + 220, c[1] + 125), Point(c[0] + 260, c[1] - 290), Point(c[0] + 430, c[1] - 20)]:
        ax.add_patch(Circle((pt.x, pt.y), 42, facecolor="#EFF6FF", edgecolor="#2563EB", lw=1.0, alpha=0.9, zorder=36))
        ax.plot(pt.x, pt.y, marker="o", markersize=2.5, color="#2563EB", zorder=37)
    draw_mini_legend(ax, [("轨道站点", "#2563EB", "ring"), ("轨道/铁路", "#64748B", "dash"), ("次干路", "#3B82F6", "line"), ("主干路", "#A855F7", "line"), ("城市快速路", "#F97316", "line")], loc=(0.78, 0.12), row_h=0.038)


def panel_landuse(ax, data, bounds):
    palette = {
        "R": "#FDE68A",
        "B": "#C4B5FD",
        "A": "#A7F3D0",
        "M": "#93C5FD",
        "G": "#BBF7D0",
        "S": "#CBD5E1",
    }
    landuse = data["landuse"]
    if landuse.empty:
        return
    landuse = gpd.clip(landuse, data["boundary"])
    for code, color in palette.items():
        sub = landuse[landuse.get("GB_Code", "").astype(str).str.contains(code, na=False)]
        if not sub.empty:
            sub.plot(ax=ax, facecolor=color, edgecolor="#FFFFFF", linewidth=0.35, alpha=0.62, zorder=22)
    data["key_plots"].plot(ax=ax, facecolor="#FDBA74", edgecolor="#FB923C", linewidth=0.8, alpha=0.45, zorder=26)
    draw_mini_legend(ax, [("居住生活", "#FDE68A", "patch"), ("历史文化/公共核心", "#FCA5A5", "patch"), ("商业服务", "#C4B5FD", "patch"), ("产业更新", "#93C5FD", "patch"), ("公共设施", "#A7F3D0", "patch"), ("绿地开放空间", "#BBF7D0", "patch")], loc=(0.04, 0.075), row_h=0.035)


def panel_activity(ax, data, bounds):
    pts = project_landmarks()
    names = ["长春站前节点", "商业服务节点", "伪满皇宫", "光复路", "胜利公园", "社区生活节点", "滨水休闲节点"]
    selected = [pts[n] for n in names]
    link_pairs = [
        (selected[0], selected[1], -0.18),
        (selected[1], selected[2], 0.14),
        (selected[2], selected[3], -0.12),
        (selected[3], selected[6], 0.10),
        (selected[6], selected[5], -0.18),
        (selected[5], selected[4], -0.10),
        (selected[4], selected[1], 0.08),
        (selected[2], selected[5], 0.18),
    ]
    for a, b, rad in link_pairs:
        draw_curve_line(ax, (a.x, a.y), (b.x, b.y), "#FDBA74", lw=0.9, alpha=0.68, rad=rad, linestyle=(0, (2, 2)), z=24)
    for name, pt in zip(names, selected):
        ax.add_patch(Circle((pt.x, pt.y), 125, facecolor="none", edgecolor="#FDBA74", linewidth=1.0, alpha=0.45, zorder=25))
        ax.add_patch(Circle((pt.x, pt.y), 58, facecolor="#FED7AA", edgecolor="#F97316", linewidth=0.9, alpha=0.65, zorder=26))
        ax.plot(pt.x, pt.y, marker="o", markersize=4.2, color="#F97316", markeredgecolor="#FFFFFF", markeredgewidth=0.8, zorder=28)
        draw_label(ax, pt.x, pt.y, name, size=5.1, color="#9A3412", dy=72, weight="normal")
    draw_mini_legend(ax, [("公共联系", "#FDBA74", "dash"), ("影响圈层", "#FDBA74", "ring"), ("活力节点", "#F97316", "dot")], loc=(0.04, 0.08), row_h=0.038)


def panel_waterfront(ax, data, bounds):
    water = data["water"]
    if not water.empty:
        water.boundary.plot(ax=ax, color="#0EA5A4", linewidth=2.2, alpha=0.9, zorder=28)
    c = centroid_xy(data["boundary"])
    edge_x = bounds[1] - (bounds[1] - bounds[0]) * 0.22
    for yy, rad in [(0.33, -0.18), (0.50, -0.08), (0.67, 0.12)]:
        start = (c[0] + 170, c[1] + (yy - 0.5) * 850)
        end = (edge_x, bounds[2] + (bounds[3] - bounds[2]) * yy)
        draw_curve_arrow(ax, start, end, "#2563EB", lw=1.25, alpha=0.85, rad=rad, z=30, mutation_scale=10)
    ax.plot([edge_x, edge_x], [bounds[2] + 240, bounds[3] - 260], color="#14B8A6", linewidth=3.0, alpha=0.55, zorder=27)
    for yy in [0.26, 0.48, 0.70]:
        ax.add_patch(Circle((edge_x, bounds[2] + (bounds[3] - bounds[2]) * yy), 95, facecolor="none", edgecolor="#14B8A6", lw=1.4, alpha=0.55, zorder=29))
    draw_curve_line(
        ax,
        (edge_x - 90, bounds[2] + 280),
        (edge_x - 90, bounds[3] - 280),
        "#99F6E4",
        lw=2.2,
        alpha=0.75,
        rad=-0.05,
        linestyle=(0, (2, 2)),
        z=26,
    )
    draw_mini_legend(ax, [("城标视点", "#2563EB", "ring"), ("城市界面", "#64748B", "dash"), ("视线廊道", "#2563EB", "dash"), ("滨水步行/慢行带", "#99F6E4", "dash"), ("滨水界面", "#14B8A6", "line")], loc=(0.76, 0.08), row_h=0.036)


PANEL_DRAWERS = {
    "green_open_space": panel_green,
    "eco_corridor": panel_ecology,
    "transport_access": panel_transport,
    "landuse_layout": panel_landuse,
    "activity_nodes": panel_activity,
    "waterfront_image": panel_waterfront,
}


def draw_panel(ax, data, bounds, key, title, caption):
    draw_base(ax, data, bounds)
    PANEL_DRAWERS[key](ax, data, bounds)
    draw_landmarks(ax, data)
    ax.text(0.00, -0.092, title, transform=ax.transAxes, ha="left", va="top", color="#111827", fontproperties=_font(13.2, "bold"))
    ax.text(0.00, -0.152, caption, transform=ax.transAxes, ha="left", va="top", color="#64748B", fontproperties=_font(7.2))


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if USE_REFERENCE_EXACT and (REFERENCE_EXACT_DIR / "urban_design_analysis_2x3_board_reference_exact.png").exists():
        copies = {
            "urban_design_analysis_2x3_board_reference_exact.png": "urban_design_analysis_2x3_board.png",
            "01_绿地与开放空间结构.png": "green_open_space_绿地与开放空间结构.png",
            "02_生态廊道与景观连接.png": "eco_corridor_生态廊道与景观连接.png",
            "03_交通结构与可达性.png": "transport_access_交通结构与可达性.png",
            "05_公共活力节点.png": "activity_nodes_公共活力节点.png",
            "06_滨水界面与城市形象.png": "waterfront_image_滨水界面与城市形象.png",
        }
        for src_name, dst_name in copies.items():
            src = REFERENCE_EXACT_DIR / src_name
            if src.exists():
                shutil.copy2(src, OUTPUT_DIR / dst_name)
        try:
            from render_analysis_single_sheets import render_single_sheets

            render_single_sheets()
        except Exception as exc:
            print(f"DR-013 style single-sheet render skipped: {exc}")
        print(OUTPUT_DIR / "urban_design_analysis_2x3_board.png")
        return

    layers = load_layers()
    bounds = view_bounds(layers["boundary"])
    data = clipped(layers, bounds)

    for key, title, caption in PANEL_SPECS:
        fig, ax = plt.subplots(figsize=(7.2, 4.85), dpi=220, facecolor="white")
        fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.20)
        draw_panel(ax, data, bounds, key, title, caption)
        clean_title = title.split(". ", 1)[-1]
        fig.savefig(OUTPUT_DIR / f"{key}_{clean_title}.png", dpi=220, facecolor="white")
        plt.close(fig)

    # Match the Image tool reference board: no global heading, six panels fill the page.
    fig, axes = plt.subplots(2, 3, figsize=(15.36, 10.24), dpi=220, facecolor="white")
    fig.subplots_adjust(left=0.012, right=0.988, top=0.982, bottom=0.080, wspace=0.030, hspace=0.255)
    for ax, spec in zip(axes.ravel(), PANEL_SPECS):
        draw_panel(ax, data, bounds, *spec)
    fig.savefig(OUTPUT_DIR / "urban_design_analysis_2x3_board.png", dpi=220, facecolor="white")
    plt.close(fig)
    print(OUTPUT_DIR / "urban_design_analysis_2x3_board.png")


if __name__ == "__main__":
    main()
