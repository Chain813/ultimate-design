# -*- coding: utf-8 -*-
"""Render DR-013 style single sheets for selected analysis panels."""
from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "static" / "analysis_board"
REFERENCE_DIR = OUTPUT_DIR / "reference_exact"
RUNTIME_PACKAGES = ROOT / ".runtime-packages"
if RUNTIME_PACKAGES.exists():
    sys.path.insert(0, str(RUNTIME_PACKAGES))

CANVAS_W = 2240
CANVAS_H = 1584


def font(size: int, bold: bool = False):
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def text_width(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont) -> int:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if current and text_width(draw, candidate, fnt) > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def draw_grid(draw: ImageDraw.ImageDraw):
    for x in range(0, CANVAS_W, 40):
        draw.line((x, 0, x, CANVAS_H), fill="#E2E8F0", width=1)
    for y in range(0, CANVAS_H, 40):
        draw.line((0, y, CANVAS_W, y), fill="#E2E8F0", width=1)


def draw_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], accent: str | None = None):
    x1, y1, x2, y2 = box
    draw.rectangle((x1 + 5, y1 + 5, x2 + 5, y2 + 5), fill="#E2E8F0")
    draw.rectangle(box, fill="#FFFFFF", outline="#CBD5E1", width=2)
    if accent:
        draw.rectangle((x1, y1, x2, y1 + 10), fill=accent)


def paste_panel_map(canvas: Image.Image, src_path: Path, box: tuple[int, int, int, int]):
    enhanced_path = src_path.with_name(f"{src_path.stem}_enhanced{src_path.suffix}")
    if enhanced_path.exists():
        src_path = enhanced_path
    src = Image.open(src_path).convert("RGB")
    # Remove the original small-panel title/caption so the A3 header carries the title.
    crop_h = int(src.height * 0.86)
    src = src.crop((0, 0, src.width, crop_h))
    src = src.filter(ImageFilter.UnsharpMask(radius=0.9, percent=150, threshold=2))
    src = ImageEnhance.Sharpness(src).enhance(1.18)
    src = ImageEnhance.Contrast(src).enhance(1.04)

    x1, y1, x2, y2 = box
    max_w = x2 - x1
    max_h = y2 - y1
    scale = min(max_w / src.width, max_h / src.height)
    new_size = (int(src.width * scale), int(src.height * scale))
    src = src.resize(new_size, Image.Resampling.LANCZOS)
    src = src.filter(ImageFilter.UnsharpMask(radius=0.65, percent=140, threshold=2))
    px = x1 + (max_w - new_size[0]) // 2
    py = y1 + (max_h - new_size[1]) // 2
    canvas.paste(src, (px, py))


def paste_vector_panel(canvas: Image.Image, panel_key: str, box: tuple[int, int, int, int]):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import generate_urban_analysis_board as board

    x1, y1, x2, y2 = box
    max_w = x2 - x1
    max_h = y2 - y1
    dpi = 260
    fig_w = max_w / dpi
    fig_h = max_h / dpi

    layers = board.load_layers()
    bounds = board.view_bounds(layers["boundary"])
    data = board.clipped(layers, bounds)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi, facecolor="white")
    fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0)
    original_legend = board.draw_mini_legend
    board.draw_mini_legend = lambda *args, **kwargs: None
    try:
        board.draw_base(ax, data, bounds)
        board.PANEL_DRAWERS[panel_key](ax, data, bounds)
        board.draw_landmarks(ax, data)
    finally:
        board.draw_mini_legend = original_legend

    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=dpi, facecolor="white", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    buffer.seek(0)

    img = Image.open(buffer).convert("RGB")
    scale = min(max_w / img.width, max_h / img.height)
    new_size = (int(img.width * scale), int(img.height * scale))
    img = img.resize(new_size, Image.Resampling.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=0.6, percent=125, threshold=2))
    px = x1 + (max_w - new_size[0]) // 2
    py = y1 + (max_h - new_size[1]) // 2
    canvas.paste(img, (px, py))


def dashed_line(draw: ImageDraw.ImageDraw, xy, fill: str, width: int = 4, dash: int = 18, gap: int = 12):
    x1, y1, x2, y2 = xy
    dx = x2 - x1
    dy = y2 - y1
    length = (dx * dx + dy * dy) ** 0.5
    if length == 0:
        return
    ux = dx / length
    uy = dy / length
    pos = 0
    while pos < length:
        end = min(pos + dash, length)
        draw.line((x1 + ux * pos, y1 + uy * pos, x1 + ux * end, y1 + uy * end), fill=fill, width=width)
        pos += dash + gap


def draw_legend(draw: ImageDraw.ImageDraw, items: list[tuple[str, str, str]], x: int, y: int):
    label_font = font(24)
    row_gap = 40
    for idx, (label, color, kind) in enumerate(items):
        cy = y + idx * row_gap
        if kind == "dash":
            dashed_line(draw, (x, cy, x + 58, cy), color, width=4, dash=14, gap=9)
        elif kind == "line":
            draw.line((x, cy, x + 58, cy), fill=color, width=7)
        elif kind == "ring":
            draw.ellipse((x + 10, cy - 18, x + 46, cy + 18), outline=color, width=4)
        elif kind == "dot":
            draw.ellipse((x + 18, cy - 10, x + 38, cy + 10), fill=color, outline="#FFFFFF", width=2)
        elif kind == "blue-ring":
            draw.ellipse((x + 8, cy - 17, x + 48, cy + 17), outline=color, width=5)
        draw.text((x + 78, cy - 17), label, fill="#334155", font=label_font)


def draw_description(draw: ImageDraw.ImageDraw, lines: list[str], x: int, y: int, max_width: int):
    body_font = font(26)
    line_h = 42
    block_gap = 36
    cy = y
    for idx, item in enumerate(lines, 1):
        wrapped = wrap_text(draw, f"{idx}. {item}", body_font, max_width)
        for line in wrapped:
            draw.text((x, cy), line, fill="#334155", font=body_font)
            cy += line_h
        cy += block_gap


def render_sheet(config: dict[str, object]):
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), "#F8FAFC")
    draw = ImageDraw.Draw(canvas)
    draw_grid(draw)

    header = (32, 60, 2208, 178)
    map_card = (32, 208, 1592, 1518)
    legend_card = (1615, 208, 2210, 530)
    desc_card = (1615, 560, 2210, 1518)

    draw_card(draw, header, "#0D9488")
    draw_card(draw, map_card)
    draw_card(draw, legend_card, "#D97706")
    draw_card(draw, desc_card, "#D97706")

    draw.text((58, 86), str(config["title"]), fill="#0F172A", font=font(38, True))
    draw.text((58, 136), str(config["subtitle"]), fill="#334155", font=font(22))

    panel_key = config.get("panel_key")
    if panel_key:
        paste_vector_panel(canvas, str(panel_key), (54, 238, 1570, 1488))
    else:
        paste_panel_map(canvas, REFERENCE_DIR / str(config["source"]), (54, 238, 1570, 1488))

    draw.text((1645, 274), "图例 / LEGEND", fill="#D97706", font=font(24, True))
    draw_legend(draw, config["legend"], 1648, 342)  # type: ignore[arg-type]

    draw.text((1645, 628), str(config["desc_title"]), fill="#D97706", font=font(24, True))
    draw_description(draw, config["description"], 1645, 720, 500)  # type: ignore[arg-type]

    output = OUTPUT_DIR / str(config["output"])
    canvas.save(output, quality=96)
    return output


def render_single_sheets():
    configs = [
        {
            "panel_key": "activity_nodes",
            "source": "05_公共活力节点.png",
            "output": "activity_nodes_公共活力节点.png",
            "title": "公共活力节点",
            "subtitle": "识别交通枢纽、文化地标、商业街区与滨水空间，组织多层级公共活动网络。",
            "desc_title": "活力结构与更新响应 / ACTIVITY",
            "legend": [
                ("公共联系", "#FDBA74", "dash"),
                ("影响圈层", "#FDBA74", "ring"),
                ("活力节点", "#F97316", "dot"),
            ],
            "description": [
                "以长春站前、胜利公园、伪满皇宫、光复路门户和滨水休闲空间构建多点联动网络。",
                "橙色圈层表达公共活动辐射范围，虚线联系反映步行与慢行可达关系。",
                "更新重点为补齐社区生活服务、强化文化游线，并把滨水空间纳入公共活力体系。",
            ],
        },
        {
            "panel_key": "waterfront_image",
            "source": "06_滨水界面与城市形象.png",
            "output": "waterfront_image_滨水界面与城市形象.png",
            "title": "滨水界面与城市形象",
            "subtitle": "梳理伊通河滨水界面、视线廊道与城市展示面，提升片区识别度与开放性。",
            "desc_title": "界面控制与形象塑造 / WATERFRONT",
            "legend": [
                ("滨水界面", "#14B8A6", "line"),
                ("滨水步行/慢行带", "#99F6E4", "dash"),
                ("视线廊道", "#2563EB", "dash"),
                ("城市界面", "#64748B", "dash"),
                ("城标视点", "#2563EB", "blue-ring"),
            ],
            "description": [
                "依托伊通河连续水体与沿岸公园，强化东侧滨水公共界面和慢行体验。",
                "蓝色视线廊道组织组团内部向滨水空间的视觉开敞，提升城市识别性。",
                "通过界面整治、节点植入与步行连续化，形成面向城市展示的开放滨水形象。",
            ],
        },
    ]
    return [render_sheet(config) for config in configs]


if __name__ == "__main__":
    for path in render_single_sheets():
        print(path)
