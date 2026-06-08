# -*- coding: utf-8 -*-
"""Enhance reference-exact analysis graphics without generative redrawing.

This keeps the Image-tool reference board visually unchanged, then improves
sharpness/resolution and adds missing vector legends to selected panels.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
REF_DIR = ROOT / "static" / "analysis_board" / "reference_exact"
SCALE = 2


def font(size: int, bold: bool = False):
    paths = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
    ]
    for path in paths:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def enhance_base(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    img = img.resize((img.width * SCALE, img.height * SCALE), Image.Resampling.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.15, percent=135, threshold=3))
    img = ImageEnhance.Sharpness(img).enhance(1.10)
    img = ImageEnhance.Contrast(img).enhance(1.035)
    return img


def s(value: int | float) -> int:
    return int(round(value * SCALE))


def dashed_line(draw: ImageDraw.ImageDraw, xy, fill, width=2, dash=10, gap=7):
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


def legend_panel_01(draw: ImageDraw.ImageDraw, x: int, y: int):
    f = font(s(10))
    green = (117, 180, 116)
    light = (190, 220, 188)
    draw.rectangle((x, y, x + s(22), y + s(12)), fill=green, outline=(255, 255, 255), width=s(1))
    draw.text((x + s(32), y - s(1)), "公园绿地", fill=(82, 101, 112), font=f)
    draw.rectangle((x, y + s(23), x + s(22), y + s(35)), fill=light, outline=(255, 255, 255), width=s(1))
    draw.text((x + s(32), y + s(22)), "开放空间", fill=(82, 101, 112), font=f)
    dashed_line(draw, (x, y + s(52), x + s(24), y + s(52)), fill=(47, 160, 78), width=s(2), dash=s(7), gap=s(5))
    draw.text((x + s(32), y + s(43)), "绿地联系", fill=(82, 101, 112), font=f)


def legend_panel_02(draw: ImageDraw.ImageDraw, x: int, y: int):
    f = font(s(10))
    green = (47, 155, 72)
    dashed_line(draw, (x, y, x + s(30), y), fill=green, width=s(2), dash=s(7), gap=s(5))
    draw.text((x + s(38), y - s(9)), "生态廊道", fill=(82, 101, 112), font=f)
    draw.ellipse((x + s(4), y + s(19), x + s(28), y + s(43)), outline=green, width=s(2))
    draw.text((x + s(38), y + s(21)), "景观节点", fill=(82, 101, 112), font=f)
    draw.line((x, y + s(61), x + s(32), y + s(61)), fill=green, width=s(3))
    draw.polygon([(x + s(32), y + s(61)), (x + s(23), y + s(56)), (x + s(23), y + s(66))], fill=green)
    draw.text((x + s(38), y + s(52)), "渗透方向", fill=(82, 101, 112), font=f)


def legend_panel_05(draw: ImageDraw.ImageDraw, x: int, y: int):
    f = font(s(10))
    orange = (239, 123, 30)
    pale = (247, 177, 102)
    dashed_line(draw, (x, y, x + s(30), y), fill=pale, width=s(2), dash=s(7), gap=s(5))
    draw.text((x + s(38), y - s(9)), "公共联系", fill=(82, 101, 112), font=f)
    draw.ellipse((x + s(4), y + s(18), x + s(30), y + s(44)), outline=pale, width=s(2))
    draw.text((x + s(38), y + s(21)), "影响圈层", fill=(82, 101, 112), font=f)
    draw.ellipse((x + s(11), y + s(55), x + s(23), y + s(67)), fill=orange, outline=(255, 255, 255), width=s(1))
    draw.text((x + s(38), y + s(52)), "活力节点", fill=(82, 101, 112), font=f)


def add_missing_legends(img: Image.Image, name: str) -> Image.Image:
    draw = ImageDraw.Draw(img)
    if name.startswith("01_"):
        legend_panel_01(draw, s(32), s(332))
    elif name.startswith("02_"):
        legend_panel_02(draw, s(32), s(330))
    elif name.startswith("05_"):
        legend_panel_05(draw, s(315), s(22))
    elif name.startswith("urban_design_analysis"):
        # Panel-local coordinates on the full reference board.
        legend_panel_01(draw, s(38), s(340))
        legend_panel_02(draw, s(538), s(340))
        legend_panel_05(draw, s(821), s(511))
    return img


def main():
    files = [
        "urban_design_analysis_2x3_board_reference_exact.png",
        "01_绿地与开放空间结构.png",
        "02_生态廊道与景观连接.png",
        "03_交通结构与可达性.png",
        "04_功能分区与用地布局.png",
        "05_公共活力节点.png",
        "06_滨水界面与城市形象.png",
    ]
    for filename in files:
        src = REF_DIR / filename
        if not src.exists():
            continue
        img = enhance_base(Image.open(src))
        img = add_missing_legends(img, filename)
        out = src.with_name(f"{src.stem}_enhanced{src.suffix}")
        img.save(out, quality=96)
        print(out)


if __name__ == "__main__":
    main()
