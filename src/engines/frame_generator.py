"""规划图纸图框生成引擎 — 使用 PIL 绘制标准 A3 工程制图边框。

功能：
1. 在数据底图外围添加统一的标题栏、图例区、文字说明和团队信息。
2. 接收重绘后的图像并自动居中放置于主图区域。
3. 支持自定义章节号、图纸名称、图面总结（由 LLM 生成）和图例条目。

Usage:
    from src.engines.frame_generator import compose_framed_sheet
    output_img = compose_framed_sheet(
        main_image=PIL.Image,
        title="用地现状分析图",
        chapter="02 数据诊断篇",
        summary="研究范围内居住用地占比最高...",
        legend_items=[("居住用地", "#FFFF00"), ("商业用地", "#FF0000")],
    )
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

# ── 常量 ──────────────────────────────────────────

# A3 横版 300dpi: 4961 x 3508
SHEET_W, SHEET_H = 4961, 3508

# 边距与分区
MARGIN = 60
TITLE_BAR_H = 200       # 顶部标题栏
BOTTOM_BAR_H = 120       # 底部信息栏
LEGEND_W = 600           # 右侧图例区宽度
SUMMARY_H = 300          # 底部右侧文字总结高度

# 颜色
BG_COLOR = (15, 23, 42)           # 深蓝黑底
TITLE_BG = (30, 41, 59)           # 标题栏底色
BORDER_COLOR = (100, 160, 220)    # 青蓝边框
TEXT_COLOR = (220, 230, 240)      # 白色文字
ACCENT_COLOR = (129, 140, 248)    # 强调紫蓝
GOLD_COLOR = (245, 185, 60)       # 暖金色
DIM_COLOR = (148, 163, 184)       # 次要文字
MAIN_AREA_BG = (20, 30, 48)      # 主图区底色

PROJECT_NAME = "数字孪生·古今共振 — 伪满皇宫周边街区更新规划设计"
TEAM_INFO = "UltimateDESIGN · AI-Powered Urban Renewal Platform"


def _try_load_font(size: int) -> ImageFont.FreeTypeFont:
    """尝试加载中文字体，失败则回退到默认字体。"""
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
        "C:/Windows/Fonts/simhei.ttf",     # 黑体
        "C:/Windows/Fonts/simsun.ttc",     # 宋体
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
    for font_path in candidates:
        if Path(font_path).exists():
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def compose_framed_sheet(
    main_image: Image.Image,
    title: str,
    chapter: str = "",
    summary: str = "",
    legend_items: Optional[List[Tuple[str, str]]] = None,
    drawing_number: str = "",
    scale_text: str = "1:5000",
) -> Image.Image:
    """将主图嵌入标准规划图框，返回合成后的 PIL Image。

    Args:
        main_image: 数据底图或重绘后的图纸。
        title: 图纸标题（如"用地现状分析图"）。
        chapter: 章节名（如"02 数据诊断篇"）。
        summary: 由 LLM 生成的图面总结文字（50-150 字）。
        legend_items: 图例条目列表，格式为 [(名称, 十六进制颜色), ...]。
        drawing_number: 图纸编号。
        scale_text: 比例尺文字。

    Returns:
        合成后的 A3 尺寸 PIL Image。
    """
    legend_items = legend_items or []

    # ── 创建画布 ──
    sheet = Image.new("RGB", (SHEET_W, SHEET_H), BG_COLOR)
    draw = ImageDraw.Draw(sheet)

    # ── 加载字体 ──
    font_title = _try_load_font(56)
    font_chapter = _try_load_font(36)
    font_body = _try_load_font(28)
    font_small = _try_load_font(22)
    font_legend = _try_load_font(24)

    # ══════════════════════════════════════════
    # 1. 顶部标题栏
    # ══════════════════════════════════════════
    draw.rectangle(
        [MARGIN, MARGIN, SHEET_W - MARGIN, MARGIN + TITLE_BAR_H],
        fill=TITLE_BG, outline=BORDER_COLOR, width=2,
    )
    # 章节标签
    if chapter:
        draw.text(
            (MARGIN + 30, MARGIN + 20),
            chapter, fill=ACCENT_COLOR, font=font_chapter,
        )
    # 图纸标题
    draw.text(
        (MARGIN + 30, MARGIN + 70),
        title, fill=TEXT_COLOR, font=font_title,
    )
    # 右侧项目名
    proj_bbox = draw.textbbox((0, 0), PROJECT_NAME, font=font_body)
    proj_w = proj_bbox[2] - proj_bbox[0]
    draw.text(
        (SHEET_W - MARGIN - proj_w - 30, MARGIN + 30),
        PROJECT_NAME, fill=DIM_COLOR, font=font_body,
    )
    # 编号
    if drawing_number:
        num_bbox = draw.textbbox((0, 0), drawing_number, font=font_small)
        num_w = num_bbox[2] - num_bbox[0]
        draw.text(
            (SHEET_W - MARGIN - num_w - 30, MARGIN + 80),
            drawing_number, fill=GOLD_COLOR, font=font_small,
        )

    # ══════════════════════════════════════════
    # 2. 主图区域
    # ══════════════════════════════════════════
    main_top = MARGIN + TITLE_BAR_H + 20
    main_bottom = SHEET_H - MARGIN - BOTTOM_BAR_H - 20
    main_left = MARGIN + 10
    main_right = SHEET_W - MARGIN - LEGEND_W - 30

    main_area_w = main_right - main_left
    main_area_h = main_bottom - main_top

    # 主图区底色
    draw.rectangle(
        [main_left, main_top, main_right, main_bottom],
        fill=MAIN_AREA_BG, outline=BORDER_COLOR, width=1,
    )

    # 缩放主图以适应主图区（保持比例）
    img_w, img_h = main_image.size
    ratio = min(main_area_w / img_w, main_area_h / img_h)
    new_w = int(img_w * ratio)
    new_h = int(img_h * ratio)
    resized = main_image.resize((new_w, new_h), Image.LANCZOS)

    # 居中粘贴
    paste_x = main_left + (main_area_w - new_w) // 2
    paste_y = main_top + (main_area_h - new_h) // 2

    # 处理透明通道
    if resized.mode == "RGBA":
        sheet.paste(resized, (paste_x, paste_y), resized)
    else:
        sheet.paste(resized, (paste_x, paste_y))

    # ══════════════════════════════════════════
    # 3. 右侧图例区
    # ══════════════════════════════════════════
    legend_left = SHEET_W - MARGIN - LEGEND_W - 10
    legend_top = main_top
    legend_bottom = main_bottom

    draw.rectangle(
        [legend_left, legend_top, SHEET_W - MARGIN, legend_bottom],
        fill=TITLE_BG, outline=BORDER_COLOR, width=1,
    )
    draw.text(
        (legend_left + 20, legend_top + 15),
        "图  例 / LEGEND", fill=ACCENT_COLOR, font=font_chapter,
    )
    draw.line(
        [(legend_left + 20, legend_top + 60), (SHEET_W - MARGIN - 20, legend_top + 60)],
        fill=BORDER_COLOR, width=1,
    )

    # 绘制图例条目
    y_cursor = legend_top + 80
    swatch_size = 28
    for name, color_hex in legend_items:
        if y_cursor + 40 > legend_bottom - SUMMARY_H - 20:
            break  # 防止溢出到总结区
        try:
            rgb = tuple(int(color_hex.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
        except (ValueError, IndexError):
            rgb = (180, 180, 180)
        draw.rectangle(
            [legend_left + 20, y_cursor, legend_left + 20 + swatch_size, y_cursor + swatch_size],
            fill=rgb, outline=(200, 200, 200), width=1,
        )
        draw.text(
            (legend_left + 60, y_cursor + 2),
            name, fill=TEXT_COLOR, font=font_legend,
        )
        y_cursor += 42

    # ── 图面总结区（右侧底部） ──
    if summary:
        summary_top = legend_bottom - SUMMARY_H
        draw.line(
            [(legend_left + 20, summary_top), (SHEET_W - MARGIN - 20, summary_top)],
            fill=BORDER_COLOR, width=1,
        )
        draw.text(
            (legend_left + 20, summary_top + 10),
            "图面说明 / DESCRIPTION", fill=ACCENT_COLOR, font=font_small,
        )
        # 自动换行绘制摘要文字
        _draw_wrapped_text(
            draw, summary,
            x=legend_left + 20,
            y=summary_top + 45,
            max_width=LEGEND_W - 40,
            font=font_small,
            fill=DIM_COLOR,
            line_spacing=8,
        )

    # ══════════════════════════════════════════
    # 4. 底部信息栏
    # ══════════════════════════════════════════
    bar_top = SHEET_H - MARGIN - BOTTOM_BAR_H
    draw.rectangle(
        [MARGIN, bar_top, SHEET_W - MARGIN, SHEET_H - MARGIN],
        fill=TITLE_BG, outline=BORDER_COLOR, width=2,
    )
    # 左侧：比例尺
    draw.text(
        (MARGIN + 30, bar_top + 15),
        f"比例尺 / Scale: {scale_text}", fill=DIM_COLOR, font=font_body,
    )
    # 绘制比例尺图形
    bar_y = bar_top + 65
    bar_seg_w = 100
    for i in range(5):
        c = TEXT_COLOR if i % 2 == 0 else BG_COLOR
        draw.rectangle(
            [MARGIN + 30 + i * bar_seg_w, bar_y, MARGIN + 30 + (i + 1) * bar_seg_w, bar_y + 12],
            fill=c, outline=BORDER_COLOR, width=1,
        )

    # 中间：指北针占位
    north_x = SHEET_W // 2
    draw.text((north_x - 10, bar_top + 15), "N", fill=GOLD_COLOR, font=font_chapter)
    draw.line([(north_x, bar_top + 55), (north_x, bar_top + 100)], fill=GOLD_COLOR, width=3)
    draw.polygon(
        [(north_x - 8, bar_top + 55), (north_x + 8, bar_top + 55), (north_x, bar_top + 35)],
        fill=GOLD_COLOR,
    )

    # 右侧：团队信息
    team_bbox = draw.textbbox((0, 0), TEAM_INFO, font=font_body)
    team_w = team_bbox[2] - team_bbox[0]
    draw.text(
        (SHEET_W - MARGIN - team_w - 30, bar_top + 15),
        TEAM_INFO, fill=DIM_COLOR, font=font_body,
    )
    draw.text(
        (SHEET_W - MARGIN - team_w - 30, bar_top + 60),
        "长春市宽城区 · EPSG:4326 · AI-Generated Data Visualization",
        fill=DIM_COLOR, font=font_small,
    )

    # ── 最外层边框 ──
    draw.rectangle(
        [MARGIN - 5, MARGIN - 5, SHEET_W - MARGIN + 5, SHEET_H - MARGIN + 5],
        fill=None, outline=BORDER_COLOR, width=3,
    )

    return sheet


def _draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int, y: int,
    max_width: int,
    font: ImageFont.FreeTypeFont,
    fill: tuple,
    line_spacing: int = 6,
):
    """在给定区域内自动换行绘制文本。"""
    chars = list(text)
    line = ""
    cy = y
    for ch in chars:
        test_line = line + ch
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] > max_width:
            draw.text((x, cy), line, fill=fill, font=font)
            bbox_h = bbox[3] - bbox[1]
            cy += bbox_h + line_spacing
            line = ch
        else:
            line = test_line
    if line:
        draw.text((x, cy), line, fill=fill, font=font)


def sheet_to_bytes(sheet: Image.Image, fmt: str = "PNG") -> bytes:
    """将合成图纸转为可下载的字节流。"""
    buf = io.BytesIO()
    sheet.save(buf, format=fmt, quality=95)
    buf.seek(0)
    return buf.getvalue()
