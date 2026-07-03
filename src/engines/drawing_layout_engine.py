"""Deterministic layout profiles and PIL renderer for A3 atlas sheets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageOps


A3_LANDSCAPE_SIZE = (4961, 3508)


@dataclass(frozen=True)
class LayoutSlot:
    slot_id: str
    label: str
    box: tuple[int, int, int, int]
    purpose: str


@dataclass(frozen=True)
class LayoutProfile:
    layout_id: str
    name: str
    description: str
    slots: tuple[LayoutSlot, ...]
    prompt_rules: tuple[str, ...]


_PROFILES: tuple[LayoutProfile, ...] = (
    LayoutProfile(
        layout_id="map_legend_right",
        name="主图+右侧图例",
        description="适合标准规划图、系统图和以地图为主体的图纸。",
        slots=(
            LayoutSlot("main_map", "主图", (220, 390, 3620, 2940), "承载地图、总平面或空间系统主表达"),
            LayoutSlot("legend_panel", "图例", (3740, 520, 4740, 1820), "放置图例、比例、符号和分类说明"),
            LayoutSlot("notes_panel", "说明", (3740, 1920, 4740, 2920), "放置关键指标、数据来源和简短结论"),
            LayoutSlot("title_block", "图名信息栏", (220, 3040, 4740, 3360), "放置标题、章节、编号和项目信息"),
        ),
        prompt_rules=(
            "主图占据最大面积，右侧信息栏只服务于主图阅读。",
            "图例符号必须与主图颜色和线型一致。",
            "标题和说明文字保持短句，不覆盖主图边界。",
        ),
    ),
    LayoutProfile(
        layout_id="dual_compare",
        name="改造前后对比",
        description="适合改造前后、方案 A/B、现状与规划的并列比较。",
        slots=(
            LayoutSlot("before_view", "改造前", (220, 520, 2350, 2590), "展示现状、改造前或方案 A"),
            LayoutSlot("after_view", "改造后", (2610, 520, 4740, 2590), "展示规划、改造后或方案 B"),
            LayoutSlot("comparison_notes", "对比说明", (220, 2740, 4740, 3260), "列出差异、提升点、指标和结论"),
        ),
        prompt_rules=(
            "左右两个画面尺度和视角保持一致，便于直接对比。",
            "差异标注集中在下方说明区，不压住两张主图。",
            "使用统一色彩体系表达保留、更新、拆除和新增内容。",
        ),
    ),
    LayoutProfile(
        layout_id="analysis_dashboard",
        name="分析仪表盘",
        description="适合诊断、评价、热力、活力、现状和指标类图纸。",
        slots=(
            LayoutSlot("analysis_map", "分析主图", (220, 480, 2920, 2550), "承载热力、评价、现状或诊断地图"),
            LayoutSlot("metric_a", "指标 A", (3060, 480, 4740, 1120), "展示关键指标、图表或统计占位"),
            LayoutSlot("metric_b", "指标 B", (3060, 1230, 4740, 1870), "展示辅助指标、剖面或对比图表"),
            LayoutSlot("legend_panel", "图例与分级", (3060, 1980, 4740, 2920), "说明分级、色带、阈值和数据口径"),
            LayoutSlot("analysis_notes", "诊断结论", (220, 2680, 2920, 3260), "承载问题清单、机会点和结论摘要"),
        ),
        prompt_rules=(
            "先读主图，再读右侧指标，最后读底部结论。",
            "所有指标必须标注口径或使用占位符，不能虚构具体数据。",
            "热力色带、评价等级和图例分级必须对应。",
        ),
    ),
    LayoutProfile(
        layout_id="matrix_storyboard",
        name="矩阵推演故事板",
        description="适合策略、目标、体系、流程、技术推演和阶段演化表达。",
        slots=(
            LayoutSlot("step_1", "步骤 1", (220, 500, 1690, 1450), "展示第一阶段、目标或输入条件"),
            LayoutSlot("step_2", "步骤 2", (1840, 500, 3310, 1450), "展示第二阶段、策略或中间过程"),
            LayoutSlot("step_3", "步骤 3", (3460, 500, 4740, 1450), "展示第三阶段、结果或输出"),
            LayoutSlot("step_4", "步骤 4", (220, 1640, 1690, 2590), "展示辅助系统、行动包或技术路径"),
            LayoutSlot("step_5", "步骤 5", (1840, 1640, 3310, 2590), "展示协同关系、流程节点或矩阵分类"),
            LayoutSlot("step_6", "步骤 6", (3460, 1640, 4740, 2590), "展示落地场景、实施阶段或总结"),
            LayoutSlot("story_notes", "推演说明", (220, 2760, 4740, 3260), "放置流程箭头说明、关键策略和技术备注"),
        ),
        prompt_rules=(
            "按从左到右、从上到下的阅读顺序组织信息。",
            "每个格子只表达一个策略或流程节点。",
            "连接线和箭头保持克制，避免干扰各格主图。",
        ),
    ),
    LayoutProfile(
        layout_id="full_bleed_effect",
        name="满版效果表达",
        description="适合鸟瞰、人视、运营场景、AIGC 和效果图类图纸。",
        slots=(
            LayoutSlot("hero_visual", "满版主图", (0, 0, 4961, 3508), "承载鸟瞰、人视、运营场景或 AIGC 效果主画面"),
            LayoutSlot("title_overlay", "标题叠层", (240, 220, 2940, 660), "放置短标题和章节信息"),
            LayoutSlot("caption_strip", "场景说明", (240, 2920, 4720, 3300), "放置场景标签、设计亮点和必要说明"),
        ),
        prompt_rules=(
            "主视觉可以满版，但标题与说明必须放在清晰留白或半透明叠层内。",
            "人物、树木和装饰不能遮挡关键空间关系。",
            "控制文字数量，以短标题、标签和少量关键词为主。",
        ),
    ),
    LayoutProfile(
        layout_id="chapter_cover",
        name="章节封面",
        description="适合封面、目录、篇章背景和章节过渡页。",
        slots=(
            LayoutSlot("cover_visual", "封面背景", (0, 0, 4961, 3508), "承载章节氛围、项目背景或抽象视觉"),
            LayoutSlot("title_focus", "主标题", (420, 560, 3640, 1340), "放置章节标题、项目名和核心主题"),
            LayoutSlot("chapter_index", "章节信息", (420, 1510, 2260, 2100), "放置章节编号、目录摘要或说明"),
        ),
        prompt_rules=(
            "封面以识别度和章节气质为先，不堆叠复杂数据。",
            "标题区必须保留高对比度留白。",
            "背景可以氛围化，但不能影响标题可读性。",
        ),
    ),
)

_PROFILE_BY_ID = {profile.layout_id: profile for profile in _PROFILES}

_PRIMARY_VISUAL_SLOT_BY_LAYOUT = {
    "map_legend_right": "main_map",
    "analysis_dashboard": "analysis_map",
    "matrix_storyboard": "step_1",
    "full_bleed_effect": "hero_visual",
    "chapter_cover": "cover_visual",
}

_COVER_VISUAL_SLOT_IDS = {"hero_visual", "cover_visual"}

_FONT_CANDIDATES: tuple[Path | str, ...] = (
    Path("C:/Windows/Fonts/msyh.ttc"),
    Path("C:/Windows/Fonts/msyhbd.ttc"),
    Path("C:/Windows/Fonts/simhei.ttf"),
    Path("C:/Windows/Fonts/simsun.ttc"),
    Path("C:/Windows/Fonts/arialuni.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/System/Library/Fonts/STHeiti Light.ttc"),
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    Path("/Library/Fonts/Arial Unicode.ttf"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/noto/NotoSansSC-Regular.otf"),
    Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"),
    Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    "DejaVuSans.ttf",
)


def list_layout_profiles() -> list[LayoutProfile]:
    """Return all registered layout profiles in stable order."""
    return list(_PROFILES)


def get_layout_profile(layout_id: str) -> LayoutProfile:
    """Return a layout profile by id."""
    try:
        return _PROFILE_BY_ID[layout_id]
    except KeyError as exc:
        raise ValueError(f"Unknown layout profile: {layout_id}") from exc


def recommend_layout_profile(drawing_name: str) -> LayoutProfile:
    """Pick a layout profile from drawing-name semantics."""
    name = str(drawing_name or "")
    lowered = name.lower()

    if any(keyword in name for keyword in ("改造前后", "前后", "对比")) or "compare" in lowered:
        return get_layout_profile("dual_compare")
    if any(keyword in name for keyword in ("鸟瞰", "人视", "运营场景", "AIGC", "效果图")):
        return get_layout_profile("full_bleed_effect")
    if any(keyword in name for keyword in ("诊断", "评价", "热力", "活力", "现状", "指标")):
        return get_layout_profile("analysis_dashboard")
    if any(keyword in name for keyword in ("策略", "目标", "体系", "流程", "技术推演")):
        return get_layout_profile("matrix_storyboard")
    if any(keyword in name for keyword in ("封面", "目录", "背景")):
        return get_layout_profile("chapter_cover")
    return get_layout_profile("map_legend_right")


def layout_prompt_clause(profile: LayoutProfile) -> str:
    """Build a prompt clause that describes the selected layout contract."""
    lines = [
        f"Layout profile: {profile.layout_id}",
        f"Name: {profile.name}",
        f"Description: {profile.description}",
        "Slots:",
    ]
    for slot in profile.slots:
        lines.append(
            f"- {slot.slot_id}: label={slot.label}; purpose={slot.purpose}; box={slot.box}"
        )
    lines.append("Prompt rules:")
    lines.extend(f"- {rule}" for rule in profile.prompt_rules)
    lines.append("- 不得让文字压住主图，标题、图例、notes 必须与主图保持安全间距。")
    return "\n".join(lines)


def compose_layout_sheet(
    layout_id: str,
    images: dict[str, Image.Image],
    title: str,
    chapter: str = "",
    legend_items: list[tuple[str, str]] | None = None,
    notes: list[str] | None = None,
) -> Image.Image:
    """Compose an RGB A3 landscape sheet from slot images and annotations."""
    profile = get_layout_profile(layout_id)
    sheet = Image.new("RGB", A3_LANDSCAPE_SIZE, "#f3f0e8")
    draw = ImageDraw.Draw(sheet)

    _draw_page_background(draw)
    for slot in profile.slots:
        _render_slot(sheet, draw, slot, _image_for_slot(profile, slot, images))

    _draw_title(sheet, title=title, chapter=chapter, profile=profile)
    _draw_legend(sheet, profile, legend_items or [])
    _draw_notes(sheet, profile, notes or [])
    _draw_footer(sheet, profile)
    return sheet


def _image_for_slot(
    profile: LayoutProfile,
    slot: LayoutSlot,
    images: dict[str, Image.Image],
) -> Image.Image | None:
    if slot.slot_id in images:
        return images[slot.slot_id]

    primary_slot_id = _PRIMARY_VISUAL_SLOT_BY_LAYOUT.get(profile.layout_id)
    if slot.slot_id == primary_slot_id:
        return images.get("main")

    return None


def _draw_page_background(draw: ImageDraw.ImageDraw) -> None:
    width, height = A3_LANDSCAPE_SIZE
    draw.rectangle((0, 0, width - 1, height - 1), fill="#f3f0e8")
    draw.rectangle((110, 110, width - 110, height - 110), outline="#1d3557", width=4)
    draw.line((110, 300, width - 110, 300), fill="#8aa0b5", width=2)


def _render_slot(
    sheet: Image.Image,
    draw: ImageDraw.ImageDraw,
    slot: LayoutSlot,
    image: Image.Image | None,
) -> None:
    left, top, right, bottom = slot.box
    is_full_bleed = slot.box == (0, 0, *A3_LANDSCAPE_SIZE)
    if not is_full_bleed:
        draw.rectangle(slot.box, fill="#fbfaf6", outline="#67809a", width=3)

    inner = _inset_box(slot.box, 18 if not is_full_bleed else 0)
    if image is None:
        if not is_full_bleed:
            draw.rectangle(inner, fill="#ece7dd")
            draw.line((inner[0], inner[1], inner[2], inner[3]), fill="#c5bfb3", width=2)
            draw.line((inner[0], inner[3], inner[2], inner[1]), fill="#c5bfb3", width=2)
            _draw_text(draw, (inner[0] + 24, inner[1] + 24), slot.label, 34, fill="#455a6f")
    else:
        _paste_image_fit(sheet, image, inner, fill="#f7f4ee", cover=_slot_uses_cover(slot))

    if not is_full_bleed:
        label_box = (left + 22, top + 18, min(right - 22, left + 460), top + 76)
        draw.rectangle(label_box, fill="#1d3557")
        _draw_text(draw, (label_box[0] + 18, label_box[1] + 9), slot.label, 28, fill="#ffffff")


def _slot_uses_cover(slot: LayoutSlot) -> bool:
    return slot.box == (0, 0, *A3_LANDSCAPE_SIZE) or slot.slot_id in _COVER_VISUAL_SLOT_IDS


def _paste_image_fit(
    sheet: Image.Image,
    image: Image.Image,
    box: tuple[int, int, int, int],
    fill: str,
    cover: bool = False,
) -> None:
    left, top, right, bottom = box
    width = max(1, right - left)
    height = max(1, bottom - top)
    source = _normalize_slot_image(image)
    target_size = (width, height)
    if cover:
        fitted = ImageOps.fit(source, target_size, method=Image.Resampling.LANCZOS)
    else:
        fitted = ImageOps.contain(source, target_size, method=Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(sheet)
    draw.rectangle(box, fill=fill)
    paste_left = left + (width - fitted.width) // 2
    paste_top = top + (height - fitted.height) // 2
    if fitted.mode == "RGBA":
        sheet.paste(fitted.convert("RGB"), (paste_left, paste_top), fitted.getchannel("A"))
    else:
        sheet.paste(fitted, (paste_left, paste_top))


def _normalize_slot_image(image: Image.Image) -> Image.Image:
    if image.mode in {"RGBA", "LA"} or (image.mode == "P" and "transparency" in image.info):
        return image.convert("RGBA")
    return image.convert("RGB")


def _draw_title(sheet: Image.Image, title: str, chapter: str, profile: LayoutProfile) -> None:
    draw = ImageDraw.Draw(sheet)
    if profile.layout_id in {"full_bleed_effect", "chapter_cover"}:
        title_slot = _find_slot(profile, "title_overlay") or _find_slot(profile, "title_focus")
        if title_slot:
            _draw_overlay(sheet, title_slot.box, "#0d1b2a", alpha=190)
            x, y = title_slot.box[0] + 36, title_slot.box[1] + 34
            _draw_text(draw, (x, y), title or profile.name, 64, fill="#ffffff")
            if chapter:
                _draw_text(draw, (x, y + 96), chapter, 34, fill="#d6e4f0")
        return

    _draw_text(draw, (220, 175), title or profile.name, 58, fill="#14213d")
    if chapter:
        _draw_text(draw, (220, 250), chapter, 30, fill="#516579")


def _draw_legend(
    sheet: Image.Image,
    profile: LayoutProfile,
    legend_items: list[tuple[str, str]],
) -> None:
    slot = _find_slot(profile, "legend")
    if slot is None or not legend_items:
        return

    draw = ImageDraw.Draw(sheet)
    left, top, right, bottom = _inset_box(slot.box, 42)
    _draw_panel_header(draw, left, top, right, "图例 / Legend")
    y = top + 78
    for label, color in legend_items[:10]:
        if y + 52 > bottom:
            break
        swatch = (left, y + 4, left + 42, y + 46)
        draw.rectangle(swatch, fill=_safe_color(color), outline="#334155", width=2)
        _draw_text(draw, (left + 62, y + 2), str(label), 26, fill="#243447")
        y += 58


def _draw_notes(sheet: Image.Image, profile: LayoutProfile, notes: list[str]) -> None:
    slot = _find_notes_slot(profile)
    if slot is None:
        return

    draw = ImageDraw.Draw(sheet)
    left, top, right, bottom = _inset_box(slot.box, 42)
    _draw_panel_header(draw, left, top, right, "Notes")
    y = top + 76
    note_lines = notes or ["结论占位", "指标占位", "数据来源占位"]
    for note in note_lines[:6]:
        wrapped = _wrap_text(str(note), right - left - 28, 24)
        for line in wrapped:
            if y + 36 > bottom:
                return
            _draw_text(draw, (left + 18, y), f"- {line}", 24, fill="#243447")
            y += 34
        y += 8


def _draw_footer(sheet: Image.Image, profile: LayoutProfile) -> None:
    draw = ImageDraw.Draw(sheet)
    width, height = A3_LANDSCAPE_SIZE
    text = f"{profile.layout_id} | A3 landscape | {width} x {height}"
    _draw_text(draw, (220, height - 88), text, 22, fill="#607085")


def _draw_panel_header(
    draw: ImageDraw.ImageDraw,
    left: int,
    top: int,
    right: int,
    text: str,
) -> None:
    draw.rectangle((left, top, right, top + 48), fill="#dfe8ef")
    _draw_text(draw, (left + 16, top + 9), text, 24, fill="#1d3557")


def _draw_overlay(sheet: Image.Image, box: tuple[int, int, int, int], color: str, alpha: int) -> None:
    overlay = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    rgba = ImageColor.getrgb(color) + (alpha,)
    overlay_draw.rectangle(box, fill=rgba)
    sheet.paste(Image.alpha_composite(sheet.convert("RGBA"), overlay).convert("RGB"))


def _find_slot(profile: LayoutProfile, key: str) -> LayoutSlot | None:
    for slot in profile.slots:
        haystack = f"{slot.slot_id} {slot.label} {slot.purpose}".lower()
        if key.lower() in haystack:
            return slot
    return None


def _find_notes_slot(profile: LayoutProfile) -> LayoutSlot | None:
    for key in ("notes", "说明", "结论", "caption", "story", "comparison"):
        slot = _find_slot(profile, key)
        if slot is not None:
            return slot
    return profile.slots[-1] if profile.slots else None


def _inset_box(box: tuple[int, int, int, int], inset: int) -> tuple[int, int, int, int]:
    left, top, right, bottom = box
    return (left + inset, top + inset, right - inset, bottom - inset)


def _safe_color(color: str) -> tuple[int, int, int]:
    try:
        return ImageColor.getrgb(color)
    except ValueError:
        return (96, 125, 139)


def _wrap_text(text: str, max_width: int, font_size: int) -> list[str]:
    if not text:
        return []
    font = _load_font(font_size)
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if current and _text_width(candidate, font) > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    size: int,
    fill: str,
) -> None:
    for font in _load_font_options(size):
        try:
            draw.text(xy, text, font=font, fill=fill)
            return
        except UnicodeEncodeError:
            continue

    fallback_text = text.encode("ascii", "replace").decode("ascii") or "?"
    for font in _load_font_options(size):
        try:
            draw.text(xy, fallback_text, font=font, fill=fill)
            return
        except UnicodeEncodeError:
            continue


def _text_width(text: str, font: ImageFont.ImageFont) -> int:
    try:
        return int(font.getlength(text))
    except (AttributeError, UnicodeEncodeError):
        return len(text) * 14


def _load_font(size: int) -> ImageFont.ImageFont:
    return next(_load_font_options(size))


def _load_font_options(size: int):
    seen: set[str] = set()
    for candidate in _FONT_CANDIDATES:
        key = str(candidate).lower()
        if key in seen:
            continue
        seen.add(key)
        if isinstance(candidate, Path):
            if not candidate.exists():
                continue
            location = str(candidate)
        else:
            location = candidate
        try:
            yield ImageFont.truetype(location, size)
        except OSError:
            continue
    yield ImageFont.load_default()


def _validate_profiles() -> None:
    width, height = A3_LANDSCAPE_SIZE
    seen: set[str] = set()
    for profile in _PROFILES:
        if profile.layout_id in seen:
            raise ValueError(f"Duplicate layout profile: {profile.layout_id}")
        seen.add(profile.layout_id)
        for slot in profile.slots:
            left, top, right, bottom = slot.box
            if not (0 <= left < right <= width and 0 <= top < bottom <= height):
                raise ValueError(f"Invalid slot box for {profile.layout_id}.{slot.slot_id}: {slot.box}")


_validate_profiles()


__all__ = [
    "A3_LANDSCAPE_SIZE",
    "LayoutSlot",
    "LayoutProfile",
    "list_layout_profiles",
    "get_layout_profile",
    "recommend_layout_profile",
    "layout_prompt_clause",
    "compose_layout_sheet",
]
