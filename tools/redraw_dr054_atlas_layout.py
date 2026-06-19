# -*- coding: utf-8 -*-
"""Redraw DR-054 with the standard atlas sheet layout and custom map code."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
ATLAS_DIR = ROOT / "static" / "atlas"
OUTPUT_NAME = "DR-054_竖向规划与排水分析图.png"
OUTPUT_PATH = ATLAS_DIR / OUTPUT_NAME
BACKUP_DIR = ROOT / "static" / "atlas_backup" / "dr054_before_atlas_redraw_20260619"

CANVAS_SIZE = (4480, 3168)
SCALE = 2

DRAINAGE_ARROW_STYLE = {
    "color": "#1D4ED8",
    "stroke_width": 12,
    "outline_width": 11,
    "mutation_scale": 48,
}


def layout_boxes(scale: int = SCALE) -> dict[str, tuple[int, int, int, int]]:
    base = {
        "header": (32, 60, 2208, 178),
        "map": (32, 208, 1592, 1518),
        "legend": (1615, 208, 2210, 530),
        "description": (1615, 560, 2210, 1518),
    }
    return {key: tuple(v * scale for v in box) for key, box in base.items()}


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for block in text.split("\n"):
        current = ""
        for char in block:
            test = current + char
            if draw.textlength(test, font=fnt) <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = char
        if current:
            lines.append(current)
    return lines


def draw_grid(draw: ImageDraw.ImageDraw) -> None:
    for x in range(0, CANVAS_SIZE[0], 80):
        draw.line((x, 0, x, CANVAS_SIZE[1]), fill="#E2E8F0", width=1)
    for y in range(0, CANVAS_SIZE[1], 80):
        draw.line((0, y, CANVAS_SIZE[0], y), fill="#E2E8F0", width=1)


def draw_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], accent: str | None = None) -> None:
    x1, y1, x2, y2 = box
    draw.rectangle((x1 + 8, y1 + 8, x2 + 8, y2 + 8), fill="#E2E8F0")
    draw.rectangle(box, fill="#FFFFFF", outline="#CBD5E1", width=3)
    if accent:
        draw.rectangle((x1, y1, x2, y1 + 14), fill=accent)


def backup_existing() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if OUTPUT_PATH.exists():
        target = BACKUP_DIR / OUTPUT_PATH.name
        if not target.exists():
            shutil.copy2(OUTPUT_PATH, target)


def _render_map(size: tuple[int, int]) -> Image.Image:
    import geopandas as gpd
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.font_manager as fm
    import matplotlib.patheffects as path_effects
    import matplotlib.pyplot as plt
    from shapely.geometry import Point, box

    dpi = 220

    def mpl_font(size_pt: int, weight: str = "normal") -> fm.FontProperties:
        for candidate in [
            Path("C:/Windows/Fonts/msyh.ttc"),
            Path("C:/Windows/Fonts/msyhbd.ttc"),
            Path("C:/Windows/Fonts/simhei.ttf"),
        ]:
            if candidate.exists():
                return fm.FontProperties(fname=str(candidate), size=size_pt, weight=weight)
        return fm.FontProperties(size=size_pt, weight=weight)

    def mercator_point(lon: float, lat: float) -> tuple[float, float]:
        point = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(epsg=3857).iloc[0]
        return point.x, point.y

    def mercator_box(bounds: tuple[float, float, float, float]):
        xmin, ymin = mercator_point(bounds[0], bounds[1])
        xmax, ymax = mercator_point(bounds[2], bounds[3])
        return box(xmin, ymin, xmax, ymax)

    def load(path: Path) -> gpd.GeoDataFrame:
        return gpd.read_file(path).to_crs(epsg=3857)

    def clipped(layer: gpd.GeoDataFrame, clip_geom) -> gpd.GeoDataFrame:
        if layer.empty:
            return layer
        return layer[layer.intersects(clip_geom)].copy()

    view_bounds = (125.3217, 43.8898, 125.3632, 43.9120)
    view = mercator_box(view_bounds)

    boundary = clipped(load(ROOT / "data/gis/Boundary_Scope.geojson"), view)
    roads = clipped(load(ROOT / "data/gis/road_clipped.geojson"), view)
    rail = clipped(load(ROOT / "data/gis/rail_clipped.geojson"), view)
    water = clipped(load(ROOT / "static/water.geojson"), view)
    buildings_path = ROOT / "static/buildings.geojson"
    if not buildings_path.exists():
        buildings_path = ROOT / "data/gis/Building_Footprints.geojson"
    buildings = clipped(load(buildings_path), view)
    key_plots = clipped(load(ROOT / "data/gis/Key_Plots_District.json"), view)

    fig = plt.figure(figsize=(size[0] / dpi, size[1] / dpi), dpi=dpi, facecolor="#FFFFFF")
    ax = fig.add_axes([0, 0, 1, 1], facecolor="#FFFFFF")
    ax.set_axis_off()
    ax.set_aspect("equal")
    ax.set_xlim(view.bounds[0], view.bounds[2])
    ax.set_ylim(view.bounds[1], view.bounds[3])

    if not water.empty:
        water.plot(ax=ax, facecolor="#CFE8F8", edgecolor="#B7D8ED", linewidth=1.0, alpha=0.92, zorder=1)

    if not buildings.empty:
        buildings.plot(ax=ax, facecolor="#F1F5F9", edgecolor="#E2E8F0", linewidth=0.2, alpha=0.68, zorder=2)

    if not roads.empty:
        roads.plot(ax=ax, color="#D7E0EA", linewidth=0.65, alpha=0.82, zorder=4)
        if "fclass" in roads.columns:
            major = roads[roads["fclass"].isin(["primary", "secondary", "trunk", "motorway"])]
            if not major.empty:
                major.plot(ax=ax, color="#AEBCCC", linewidth=1.8, alpha=0.88, zorder=5)

    if not rail.empty:
        rail.plot(ax=ax, color="#334155", linewidth=1.9, linestyle=(0, (8, 8)), alpha=0.72, zorder=7)

    if not key_plots.empty:
        key_plots.plot(
            ax=ax,
            facecolor="#F59E0B",
            edgecolor="#EA580C",
            linewidth=2.7,
            alpha=0.58,
            zorder=10,
        )

    if not boundary.empty:
        boundary.plot(ax=ax, facecolor="none", edgecolor="#FFFFFF", linewidth=7.5, alpha=0.9, zorder=15)
        boundary.plot(ax=ax, facecolor="none", edgecolor="#DC2626", linewidth=4.8, alpha=0.98, zorder=16)

    def draw_arrow(start_ll: tuple[float, float], end_ll: tuple[float, float]) -> None:
        sx, sy = mercator_point(*start_ll)
        ex, ey = mercator_point(*end_ll)
        common = dict(
            arrowstyle="-|>",
            shrinkA=0,
            shrinkB=0,
            connectionstyle="arc3,rad=0.04",
        )
        ax.annotate(
            "",
            xy=(ex, ey),
            xytext=(sx, sy),
            arrowprops=dict(
                **common,
                color="#FFFFFF",
                lw=DRAINAGE_ARROW_STYLE["stroke_width"] + DRAINAGE_ARROW_STYLE["outline_width"],
                alpha=0.9,
                mutation_scale=DRAINAGE_ARROW_STYLE["mutation_scale"] + 7,
            ),
            zorder=17,
        )
        ax.annotate(
            "",
            xy=(ex, ey),
            xytext=(sx, sy),
            arrowprops=dict(
                **common,
                color=DRAINAGE_ARROW_STYLE["color"],
                lw=DRAINAGE_ARROW_STYLE["stroke_width"],
                alpha=0.98,
                mutation_scale=DRAINAGE_ARROW_STYLE["mutation_scale"],
            ),
            zorder=18,
        )

    arrows = [
        ((125.3315, 43.9021), (125.3396, 43.9004)),
        ((125.3378, 43.9003), (125.3453, 43.8987)),
        ((125.3430, 43.8981), (125.3523, 43.8960)),
        ((125.3428, 43.9031), (125.3502, 43.9018)),
        ((125.3476, 43.8999), (125.3563, 43.8977)),
        ((125.3416, 43.8954), (125.3494, 43.8941)),
        ((125.3490, 43.8929), (125.3560, 43.8928)),
        ((125.3348, 43.9046), (125.3416, 43.9026)),
    ]
    for start, end in arrows:
        draw_arrow(start, end)

    for lon, lat in [
        (125.3387, 43.9003),
        (125.3449, 43.8987),
        (125.3503, 43.8958),
        (125.3548, 43.8975),
        (125.3418, 43.9026),
    ]:
        x, y = mercator_point(lon, lat)
        ax.scatter([x], [y], s=76, color=DRAINAGE_ARROW_STYLE["color"], edgecolor="white", linewidth=2.2, zorder=19)

    for lon, lat in [(125.3492, 43.8930), (125.3468, 43.8992)]:
        x, y = mercator_point(lon, lat)
        ax.scatter([x], [y], s=115, color="#EF4444", marker="x", linewidth=3.4, zorder=20)

    def label(text: str, lon: float, lat: float, color="#1E3A8A", size_pt=18, weight="bold", ha="center") -> None:
        x, y = mercator_point(lon, lat)
        txt = ax.text(
            x,
            y,
            text,
            color=color,
            ha=ha,
            va="center",
            fontproperties=mpl_font(size_pt, weight),
            zorder=30,
        )
        txt.set_path_effects([path_effects.withStroke(linewidth=4, foreground="#FFFFFF")])

    for text, lon, lat in [
        ("长春站\n+156.2m", 125.3250, 43.9080),
        ("伪满皇宫博物院\n+149.8m", 125.3422, 43.9036),
        ("胜利公园", 125.3260, 43.8960),
        ("光复路", 125.3488, 43.8997),
        ("伊通河岸\n+144.5m", 125.3583, 43.8972),
    ]:
        x, y = mercator_point(lon, lat)
        ax.scatter([x], [y], s=70, color="#F59E0B", edgecolor="white", linewidth=2.0, zorder=20)
        label(text, lon + 0.00045, lat + 0.0002, size_pt=18, ha="left")

    label("西高东低，雨水径流向伊通河汇集", 125.3493, 43.9061, color=DRAINAGE_ARROW_STYLE["color"], size_pt=21)

    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=dpi, facecolor="#FFFFFF", bbox_inches=None, pad_inches=0)
    plt.close(fig)
    buffer.seek(0)
    return Image.open(buffer).convert("RGB")


def paste_map(canvas: Image.Image, draw: ImageDraw.ImageDraw, map_box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = map_box
    inset = 28
    inner = (x1 + inset, y1 + inset, x2 - inset, y2 - inset)
    map_img = _render_map((inner[2] - inner[0], inner[3] - inner[1]))
    canvas.paste(map_img, (inner[0], inner[1]))

    # North arrow in the map panel, matching the atlas drawing convention.
    nx, ny = x2 - 260, y1 + 120
    draw.text((nx + 55, ny - 92), "N", fill="#0F172A", font=font(46, True), stroke_width=4, stroke_fill="#FFFFFF")
    draw.polygon([(nx + 80, ny - 38), (nx + 46, ny + 76), (nx + 114, ny + 76)], fill="#0F172A")
    draw.polygon([(nx + 80, ny + 166), (nx + 46, ny + 76), (nx + 114, ny + 76)], fill="#FFFFFF", outline="#0F172A")
    draw.line((nx + 80, ny - 48, nx + 80, ny + 174), fill="#0F172A", width=4)
    draw.line((nx - 10, ny + 76, nx + 170, ny + 76), fill="#0F172A", width=4)


def draw_header(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    draw_card(draw, box, "#D97706")
    x1, y1, _, _ = box
    draw.text((x1 + 42, y1 + 38), "竖向规划与排水分析图", fill="#0F172A", font=font(54, True))
    draw.text(
        (x1 + 42, y1 + 112),
        "结合现状海绵城市高程排水体系，优化地表径流路径，确保降雨汇水高效排入伊通河。",
        fill="#334155",
        font=font(30),
    )


def draw_legend(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    draw_card(draw, box, "#D97706")
    x1, y1, _, _ = box
    draw.text((x1 + 64, y1 + 96), "图例 / LEGEND", fill="#D97706", font=font(32, True))

    rows = [
        ("排水流向（向东）", DRAINAGE_ARROW_STYLE["color"], "arrow"),
        ("海绵储水节点", DRAINAGE_ARROW_STYLE["color"], "dot"),
        ("重点更新地块", "#F59E0B", "parcel"),
        ("积水易涝风险点", "#EF4444", "x"),
        ("规划研究范围", "#DC2626", "boundary"),
        ("现状铁路", "#334155", "rail"),
    ]
    col_x = [x1 + 70, x1 + 590]
    start_y = y1 + 190
    for idx, (text, color, kind) in enumerate(rows):
        x = col_x[idx % 2]
        y = start_y + (idx // 2) * 86
        if kind == "arrow":
            draw.line((x, y + 18, x + 78, y + 18), fill=color, width=8)
            draw.polygon([(x + 78, y + 18), (x + 56, y + 4), (x + 56, y + 32)], fill=color)
        elif kind == "dot":
            draw.ellipse((x + 27, y + 5, x + 53, y + 31), fill=color, outline="#FFFFFF", width=3)
        elif kind == "parcel":
            draw.rectangle((x + 8, y + 2, x + 72, y + 34), fill="#FCD48A", outline=color, width=4)
        elif kind == "x":
            draw.line((x + 28, y + 5, x + 56, y + 33), fill=color, width=6)
            draw.line((x + 56, y + 5, x + 28, y + 33), fill=color, width=6)
        elif kind == "boundary":
            draw.rectangle((x + 10, y + 2, x + 70, y + 34), outline=color, width=5)
        elif kind == "rail":
            for sx in range(x + 8, x + 82, 24):
                draw.line((sx, y + 18, min(sx + 14, x + 82), y + 18), fill=color, width=5)
        draw.text((x + 110, y - 3), text, fill="#334155", font=font(27))

    sx, sy = x1 + 360, y1 + 488
    draw.text((sx - 10, sy - 54), "0        250m        500m", fill="#334155", font=font(24))
    draw.line((sx, sy, sx + 320, sy), fill="#0F172A", width=5)
    for tick in [0, 160, 320]:
        draw.line((sx + tick, sy - 24, sx + tick, sy + 24), fill="#0F172A", width=4)
    draw.text((sx + 70, sy + 32), "比例尺 1:15000", fill="#0F172A", font=font(24, True))


def draw_description(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    draw_card(draw, box, "#D97706")
    x1, y1, x2, _ = box
    draw.text((x1 + 64, y1 + 96), "竖向与排水 / ELEVATION & DRAINAGE", fill="#D97706", font=font(32, True))

    sections = [
        (
            "1. 高程地势分析",
            "整体地势呈西高东低、北高南低态势，最大高差约12米；东侧靠近伊通河区域属于低洼易涝边缘。",
        ),
        (
            "2. 雨水径流控制",
            "通过场地道路横坡与绿地微地形改造，组织地表径流方向；规划多条主排水路径，向东汇入伊通河。",
        ),
        (
            "3. 海绵城市设施",
            "在重点更新地块、铁路防护绿带和口袋公园布置下凹式绿地、雨水花园与植草沟，实现原位蓄滞并降低峰值流量。",
        ),
    ]

    title_font = font(32, True)
    body_font = font(31)
    cy = y1 + 220
    max_width = x2 - x1 - 128
    for title, body in sections:
        draw.text((x1 + 64, cy), title, fill="#0F172A", font=title_font)
        cy += 68
        for line in wrap_text(draw, body, body_font, max_width):
            draw.text((x1 + 64, cy), line, fill="#334155", font=body_font)
            cy += 54
        cy += 58


def render() -> Path:
    backup_existing()
    boxes = layout_boxes()
    canvas = Image.new("RGB", CANVAS_SIZE, "#F8FAFC")
    draw = ImageDraw.Draw(canvas)
    draw_grid(draw)

    draw_header(draw, boxes["header"])
    draw_card(draw, boxes["map"])
    paste_map(canvas, draw, boxes["map"])
    draw_legend(draw, boxes["legend"])
    draw_description(draw, boxes["description"])

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT_PATH, quality=96)
    return OUTPUT_PATH


def main() -> None:
    path = render()
    with Image.open(path) as img:
        print(f"wrote={path}")
        print(f"size={img.size[0]}x{img.size[1]}")
        print(f"backup_dir={BACKUP_DIR}")


if __name__ == "__main__":
    main()
