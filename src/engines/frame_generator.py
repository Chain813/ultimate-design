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

def _get_project_name(site_name: str = "", city_name: str = "") -> str:
    try:
        from src.config.site import get_project_info, get_site_city, get_site_name
        city = city_name or get_site_city() or ""
        name = site_name or get_site_name() or ""
        p_info = get_project_info() or {}
        p_name = p_info.get("name", "")
        is_changchun = ("伪满" in name) or ("长春" in city)
        if p_name and (is_changchun or ("长春" not in p_name and "伪满" not in p_name)):
            return p_name
        if city or name:
            return f"数字孪生·空间计算 — {city}{name}城市更新规划设计"
    except Exception:
        if city_name or site_name:
            return f"数字孪生·空间计算 — {city_name}{site_name}城市更新规划设计"
    return "数字孪生·空间计算 — 城市更新规划设计"


def _get_project_location() -> str:
    try:
        from src.config.site import get_site_city, get_site_district, get_site_name
        city = get_site_city()
        district = get_site_district()
        name = get_site_name()
        loc = f"{city}{district}" if (city or district) else (name or "规划研究范围")
        return loc
    except Exception:
        return "规划研究范围"

PROJECT_NAME = "数字孪生·空间计算 — 城市更新规划设计"
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
    legend_items: list[tuple[str, str]] | None = None,
    drawing_number: str = "",
    scale_text: str = "1:5000",
    author: str = "",
    author_id: str = "",
    organization: str = "",
    site_name: str = "",
    city_name: str = "",
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
        author: 制作人姓名。
        author_id: 制作人编号/学号。
        organization: 单位/部门。
        site_name: 场地名称。
        city_name: 城市名称。

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
    proj_title = _get_project_name(site_name=site_name, city_name=city_name)
    proj_bbox = draw.textbbox((0, 0), proj_title, font=font_body)
    proj_w = proj_bbox[2] - proj_bbox[0]
    draw.text(
        (SHEET_W - MARGIN - proj_w - 30, MARGIN + 30),
        proj_title, fill=DIM_COLOR, font=font_body,
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

    # 右侧：团队信息与作者图签
    org_flat = organization.replace("\n", " · ").strip() if organization else TEAM_INFO
    author_tag = f"{author} ({author_id})" if (author and author_id) else (author or author_id)
    right_line_1 = f"{org_flat} | {author_tag}" if author_tag else org_flat
    team_bbox = draw.textbbox((0, 0), right_line_1, font=font_body)
    team_w = team_bbox[2] - team_bbox[0]
    draw.text(
        (SHEET_W - MARGIN - team_w - 30, bar_top + 15),
        right_line_1, fill=DIM_COLOR, font=font_body,
    )
    loc_text = f"{city_name}{site_name}".strip() or _get_project_location()
    draw.text(
        (SHEET_W - MARGIN - team_w - 30, bar_top + 60),
        f"{loc_text} · EPSG:4326 · AI-Generated Data Visualization",
        fill=DIM_COLOR, font=font_small,
    )

    # ── 最外层边框 ──
    draw.rectangle(
        [MARGIN - 5, MARGIN - 5, SHEET_W - MARGIN + 5, SHEET_H - MARGIN + 5],
        fill=None, outline=BORDER_COLOR, width=3,
    )

    return sheet


def apply_custom_a3_overlay(
    image_path: str | Path,
    output_path: str | Path,
    title: str,
    subtitle: str = "",
    desc_list: list[str] | None = None,
    author: str = "",
    author_id: str = "",
    organization: str = "",
    site_name: str = "",
    city_name: str = "",
    drawing_number: str = "",
) -> Path:
    """在 NO_FRAME A3 图纸上覆盖重绘自定义标题栏、设计说明卡与工程图签栏。

    解决 dr_*.py 中 NO_FRAME=True 硬编码长春标题、说明文字与图签被跳过的问题，
    确保学生在 Stage 13 中编辑的标题、说明（1-3条）、姓名、学号、单位与自定义场地名称
    清晰完整地渲染到最终导出的 A3 图纸 PNG 上。
    """
    from src.config.site import get_author_info, get_institution_info, get_site_city, get_site_config, get_site_name

    s_cfg = get_site_config() or {}
    city = city_name if city_name else (get_site_city() or s_cfg.get("city", ""))
    site = site_name if site_name else (get_site_name() or s_cfg.get("name", "城市更新示范区"))

    if not author or not author_id:
        a_info = get_author_info() or {}
        author = author or a_info.get("name", "规划设计组")
        author_id = author_id or a_info.get("id", "URBAN-2026")

    if not organization:
        inst_info = get_institution_info() or {}
        organization = f"{inst_info.get('name', '建筑与规划学院')}\n{inst_info.get('department', '城乡规划专业')}".strip()

    img = Image.open(image_path).convert("RGB")
    target_w, target_h = 2240, 1584
    if img.size != (target_w, target_h):
        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(img)

    def px(x_val: float) -> int:
        return int(round(x_val / 141.42 * target_w))

    def py(y_val: float) -> int:
        return int(round((100.0 - y_val) / 100.0 * target_h))

    font_h1 = _try_load_font(34)
    font_sub = _try_load_font(19)
    font_card_hdr = _try_load_font(20)
    font_desc_bold = _try_load_font(18)
    font_desc = _try_load_font(17)
    font_stamp_lbl = _try_load_font(14)
    font_stamp_val = _try_load_font(17)
    font_stamp_title = _try_load_font(22)

    # ── 1. 顶部标题横幅覆盖 (X: 2.0..139.4, Y: 88.7..96.3) ──
    hdr_x1, hdr_y1 = px(2.0), py(96.3)
    hdr_x2, hdr_y2 = px(139.4), py(88.7)
    draw.rectangle([hdr_x1 + 3, hdr_y1 + 3, hdr_x2 + 3, hdr_y2 + 3], fill=(226, 232, 240))
    draw.rectangle([hdr_x1, hdr_y1, hdr_x2, hdr_y2], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([hdr_x1, hdr_y1, hdr_x2, py(95.7)], fill=(217, 119, 6))

    draw.text((px(3.5), py(94.8)), title, fill=(15, 23, 42), font=font_h1)

    loc_prefix = f"{city}{site}".strip()
    sub_text = subtitle or f"展示{loc_prefix}范围内「{title}」的空间现状、规划布局与法定管控要素。"
    draw.text((px(3.5), py(91.5)), sub_text, fill=(51, 65, 85), font=font_sub)

    proj_title = _get_project_name(site_name=site, city_name=city)
    p_bbox = draw.textbbox((0, 0), proj_title, font=font_desc_bold)
    p_w = p_bbox[2] - p_bbox[0]
    draw.text((hdr_x2 - p_w - 24, py(94.4)), proj_title, fill=(100, 116, 139), font=font_desc_bold)

    if drawing_number:
        n_str = f"图号 / NO: {drawing_number}"
        n_bbox = draw.textbbox((0, 0), n_str, font=font_desc_bold)
        n_w = n_bbox[2] - n_bbox[0]
        draw.text((hdr_x2 - n_w - 24, py(91.3)), n_str, fill=(217, 119, 6), font=font_desc_bold)

    # ── 2. 右侧说明卡片与工程图签栏覆盖 (X: 101.5..139.4, Y: 4.0..65.3) ──
    card_x1, card_y1 = px(101.5), py(65.3)
    card_x2, card_y2 = px(139.4), py(4.0)
    draw.rectangle([card_x1 + 3, card_y1 + 3, card_x2 + 3, card_y2 + 3], fill=(226, 232, 240))
    draw.rectangle([card_x1, card_y1, card_x2, card_y2], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([card_x1, card_y1, card_x2, py(63.8)], fill=(217, 119, 6))

    draw.text((card_x1 + 24, py(62.8)), "规划说明与指标 / DESIGN NOTES", fill=(217, 119, 6), font=font_card_hdr)
    draw.line([(card_x1 + 20, py(59.6)), (card_x2 - 20, py(59.6))], fill=(226, 232, 240), width=1)

    valid_descs = [d.strip() for d in (desc_list or []) if d and str(d).strip()]
    if not valid_descs:
        area_ha = s_cfg.get("area_ha", 150)
        valid_descs = [
            f"1. 空间范围：研究范围覆盖{loc_prefix}，总面积约 {area_ha} 公顷。",
            f"2. 规划导向：围绕「{title}」落实存量空间织补、慢行网络贯通与公服设施提升。",
            "3. 指标管控：严格执行法定容积率、建筑密度、绿地率与天际线高度分区控制要求。",
        ]

    cur_y = py(58.4)
    max_txt_w = (card_x2 - card_x1) - 48
    stamp_top_y = py(24.5)

    for idx, desc_line in enumerate(valid_descs[:3]):
        if cur_y > stamp_top_y - 35:
            break
        _draw_wrapped_text(
            draw,
            desc_line,
            x=card_x1 + 24,
            y=cur_y,
            max_width=max_txt_w,
            font=font_desc,
            fill=(30, 41, 59),
            line_spacing=6,
        )
        # Estimate height advanced by wrapped text
        char_per_line = max(1, max_txt_w // 18)
        n_lines = max(1, (len(desc_line) + char_per_line - 1) // char_per_line + desc_line.count("\n"))
        cur_y += n_lines * 25 + 16

    # 法定红线指标摘要条（若上方空间充裕）
    reg = s_cfg.get("regulatory_limits") or {}
    far_val = reg.get("far", s_cfg.get("far", 2.0))
    h_val = reg.get("height_limit", s_cfg.get("height_limit", 24))
    bd_val = reg.get("building_density_max", 0.35)
    bd_pct = int(bd_val * 100) if isinstance(bd_val, (int, float)) and bd_val <= 1.0 else bd_val
    gr_val = reg.get("greenery_ratio_min", 0.30)
    gr_pct = int(gr_val * 100) if isinstance(gr_val, (int, float)) and gr_val <= 1.0 else gr_val
    if cur_y + 52 < stamp_top_y - 8:
        draw.rectangle(
            [card_x1 + 20, cur_y, card_x2 - 20, cur_y + 46],
            fill=(248, 250, 252),
            outline=(203, 213, 225),
            width=1,
        )
        reg_line = f"法定管控：FAR≤{far_val} | 限高≤{h_val}m | 密度≤{bd_pct}% | 绿地≥{gr_pct}%"
        draw.text((card_x1 + 30, cur_y + 12), reg_line, fill=(29, 78, 216), font=font_desc_bold)

    # ── 3. 标准工程图签栏 (Y: 4.0..24.5) ──
    draw.rectangle(
        [card_x1, stamp_top_y, card_x2, card_y2],
        fill=(241, 245, 249),
        outline=(15, 23, 42),
        width=2,
    )
    row1_y = stamp_top_y + 72
    row2_y = row1_y + 78
    row3_y = row2_y + 82
    mid_x = (card_x1 + card_x2) // 2

    draw.line([(card_x1, row1_y), (card_x2, row1_y)], fill=(15, 23, 42), width=1)
    draw.line([(card_x1, row2_y), (card_x2, row2_y)], fill=(15, 23, 42), width=1)
    draw.line([(card_x1, row3_y), (card_x2, row3_y)], fill=(15, 23, 42), width=1)
    draw.line([(mid_x, row3_y), (mid_x, card_y2)], fill=(15, 23, 42), width=1)

    # Row 0: 图纸名称 + 图号
    draw.text((card_x1 + 18, stamp_top_y + 8), "图纸名称 / DRAWING TITLE", fill=(100, 116, 139), font=font_stamp_lbl)
    draw.text((card_x1 + 18, stamp_top_y + 30), title, fill=(15, 23, 42), font=font_stamp_title)
    if drawing_number:
        dn_bbox = draw.textbbox((0, 0), drawing_number, font=font_desc_bold)
        draw.text((card_x2 - (dn_bbox[2] - dn_bbox[0]) - 18, stamp_top_y + 34), drawing_number, fill=(217, 119, 6), font=font_desc_bold)

    # Row 1: 项目名称
    draw.text((card_x1 + 18, row1_y + 8), "项目名称 / PROJECT", fill=(100, 116, 139), font=font_stamp_lbl)
    draw.text((card_x1 + 18, row1_y + 30), f"AI赋能下的{loc_prefix}更新规划设计", fill=(15, 23, 42), font=font_stamp_val)

    # Row 2: 单位/部门
    draw.text((card_x1 + 18, row2_y + 8), "单位与部门 / ORGANIZATION", fill=(100, 116, 139), font=font_stamp_lbl)
    org_lines = [line.strip() for line in organization.split("\n") if line.strip()]
    for i, ol in enumerate(org_lines[:2]):
        draw.text((card_x1 + 18, row2_y + 28 + i * 24), ol, fill=(15, 23, 42), font=font_stamp_val)

    # Row 3: 制作人 & 学号/编号
    draw.text((card_x1 + 18, row3_y + 8), "制作人 / AUTHOR", fill=(100, 116, 139), font=font_stamp_lbl)
    draw.text((card_x1 + 18, row3_y + 32), author, fill=(15, 23, 42), font=font_stamp_val)

    draw.text((mid_x + 18, row3_y + 8), "编号 / ID", fill=(100, 116, 139), font=font_stamp_lbl)
    draw.text((mid_x + 18, row3_y + 32), author_id, fill=(15, 23, 42), font=font_stamp_val)

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out_p), format="PNG")
    return out_p


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
