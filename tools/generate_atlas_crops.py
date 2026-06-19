# -*- coding: utf-8 -*-
"""Generate exhibition-board crops from atlas sheets without modifying atlas files."""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parent.parent
ATLAS_DIR = ROOT / "static" / "atlas"
DEFAULT_OUTPUT_DIR = ROOT / "static" / "exhibition_boards" / "atlas_crops"

BASE_PAGE_SIZE = (2240, 1584)
BASE_BOXES = {
    # Inner drawing area used by the atlas sheet generator.
    "main": (54, 238, 1570, 1488),
    # Top-right legend card in the standard atlas layout.
    "legend": (1615, 208, 2210, 530),
}

PRESERVE_FULL_IMAGE_NAMES = {
    "DR-001_规划设计图册封面.png",
    "DR-002_图册目录.png",
    "DR-003_项目背景与政策解读图.png",
    "DR-006_原始数据清单.png",
    "DR-007_上位规划解读图.png",
    "DR-008_上位专项规划解读图.png",
    "DR-009_案例借鉴与对标分析图.png",
    "DR-025_核心算法与数学公式.png",
    "DR-026_平台核心代码清单.png",
    "DR-027_规划设计依据.png",
    "DR-028_规划设计原则.png",
    "DR-029_规划设计目标.png",
    "DR-030_规划设计定位.png",
    "DR-031_规划设计策略.png",
    "DR-048_总体鸟瞰白模效果图.png",
    "DR-049_总体鸟瞰白模_彩色总图.png",
    "DR-059_AIGC技术推演过程图.png",
    "DR-073_老水产市场-鸟瞰效果图.png",
    "DR-075_老水产市场-改造前后对比图.png",
    "DR-077_老水产市场-控制性指标表.png",
    "DR-078_老水产市场-AIGC效果图1.png",
    "DR-079_老水产市场-AIGC效果图2.png",
    "DR-080_老水产市场-AIGC效果图3.png",
    "DR-081_老水产市场-AIGC效果图4.png",
    "DR-094_食品调料市场-鸟瞰效果图.png",
    "DR-095_食品调料市场-改造前后对比图.png",
    "DR-097_食品调料市场-控制性指标表.png",
    "DR-098_食品调料市场-AIGC效果图1.png",
    "DR-099_食品调料市场-AIGC效果图2.png",
    "DR-100_食品调料市场-AIGC效果图3.png",
    "DR-101_食品调料市场-AIGC效果图4.png",
    "DR-113_市一中北侧-鸟瞰效果图.png",
    "DR-114_市一中北侧-改造前后对比图.png",
    "DR-116_市一中北侧-控制性指标表.png",
    "DR-117_市一中北侧-AIGC效果图1.png",
    "DR-118_市一中北侧-AIGC效果图2.png",
    "DR-119_市一中北侧-AIGC效果图3.png",
    "DR-120_市一中北侧-AIGC效果图4.png",
    "DR-131_清禾集贸市场-鸟瞰效果图.png",
    "DR-132_清禾集贸市场-改造前后对比图.png",
    "DR-134_清禾集贸市场-控制性指标表.png",
    "DR-135_清禾集贸市场-AIGC效果图1.png",
    "DR-136_清禾集贸市场-AIGC效果图2.png",
    "DR-137_清禾集贸市场-AIGC效果图3.png",
    "DR-138_清禾集贸市场-AIGC效果图4.png",
    "DR-149_中国石油-鸟瞰效果图.png",
    "DR-150_中国石油-改造前后对比图.png",
    "DR-152_中国石油-控制性指标表.png",
    "DR-153_中国石油-AIGC效果图1.png",
    "DR-154_中国石油-AIGC效果图2.png",
    "DR-155_图册章节结构导图.png",
    "DR-156_数据处理管线导图.png",
    "DR-157_规划协同工作流程图.png",
    "DR-158_城乡规划知识体系导图.png",
}

PRESERVE_FULL_IMAGE_KEYWORDS = (
    "现状卫星图",
    "改造总平面图",
    "场地功能策划图",
    "交通流线分析图",
    "绿化分析图",
    "剖面解析",
    "效果图",
    "鸟瞰改造",
)


@dataclass(frozen=True)
class CropResult:
    source_path: Path
    output_path: Path
    source_size: tuple[int, int]
    output_size: tuple[int, int]
    used_standard_layout: bool
    used_legend: bool
    preserved_full_image: bool = False


def scaled_standard_boxes(size: tuple[int, int]) -> dict[str, tuple[int, int, int, int]]:
    width, height = size
    sx = width / BASE_PAGE_SIZE[0]
    sy = height / BASE_PAGE_SIZE[1]

    def scale_box(box: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        x1, y1, x2, y2 = box
        return (
            round(x1 * sx),
            round(y1 * sy),
            round(x2 * sx),
            round(y2 * sy),
        )

    return {name: scale_box(box) for name, box in BASE_BOXES.items()}


def build_crop_output_path(source_path: Path, output_dir: Path) -> Path:
    return output_dir / f"{source_path.stem}__crop{source_path.suffix}"


def is_standard_atlas_ratio(size: tuple[int, int]) -> bool:
    width, height = size
    ratio = width / height
    # The earlier 4K enhancement created both exact A3-ratio sheets and a
    # wider 4:3-like batch. Both still preserve the atlas sheet layout.
    return 1.30 <= ratio <= 1.43 and width >= 2000 and height >= 1400


def should_process_atlas_image(path: Path) -> bool:
    name = path.name
    if not name.lower().endswith(".png"):
        return False
    if "_backup" in name or name.startswith("test_"):
        return False
    return True


def should_preserve_full_image(path: Path) -> bool:
    name = path.name
    return name in PRESERVE_FULL_IMAGE_NAMES or any(keyword in name for keyword in PRESERVE_FULL_IMAGE_KEYWORDS)


def _safe_crop_box(size: tuple[int, int]) -> tuple[int, int, int, int]:
    width, height = size
    margin_x = round(width * 0.035)
    margin_top = round(height * 0.065)
    margin_bottom = round(height * 0.045)
    return (margin_x, margin_top, width - margin_x, height - margin_bottom)


def _legend_has_content(legend: Image.Image) -> bool:
    gray = legend.convert("L")
    # A nearly blank white card should not be pasted onto the crop.
    hist = gray.histogram()
    total = legend.width * legend.height
    whiteish = sum(hist[242:])
    return whiteish / total < 0.96


def _paste_legend(crop: Image.Image, legend: Image.Image) -> bool:
    if not _legend_has_content(legend):
        return False

    canvas = crop.convert("RGBA")
    legend_rgba = legend.convert("RGBA")

    max_w = round(canvas.width * 0.34)
    max_h = round(canvas.height * 0.30)
    scale = min(max_w / legend_rgba.width, max_h / legend_rgba.height, 1.0)
    legend_size = (max(1, round(legend_rgba.width * scale)), max(1, round(legend_rgba.height * scale)))
    legend_rgba = legend_rgba.resize(legend_size, Image.Resampling.LANCZOS)

    margin = max(24, round(min(canvas.size) * 0.022))
    x = canvas.width - legend_rgba.width - margin
    y = canvas.height - legend_rgba.height - margin

    shadow = Image.new("RGBA", (legend_rgba.width + 18, legend_rgba.height + 18), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle((9, 9, legend_rgba.width + 9, legend_rgba.height + 9), radius=8, fill=(15, 23, 42, 36))
    shadow = shadow.filter(ImageFilter.GaussianBlur(5))
    canvas.alpha_composite(shadow, (x - 9, y - 9))

    # Slight white backing keeps the transplanted legend readable on complex maps.
    backing = Image.new("RGBA", legend_rgba.size, (255, 255, 255, 235))
    canvas.alpha_composite(backing, (x, y))
    canvas.alpha_composite(legend_rgba, (x, y))

    crop.paste(canvas.convert(crop.mode))
    return True


def crop_atlas_image(source_path: Path, output_path: Path, overlay_legend: bool = True) -> CropResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if should_preserve_full_image(source_path):
        with Image.open(source_path) as original:
            size = original.size

        tmp_output = output_path.with_suffix(output_path.suffix + ".tmp")
        shutil.copy2(source_path, tmp_output)
        tmp_output.replace(output_path)
        return CropResult(
            source_path=source_path,
            output_path=output_path,
            source_size=size,
            output_size=size,
            used_standard_layout=False,
            used_legend=False,
            preserved_full_image=True,
        )

    with Image.open(source_path) as original:
        image = original.convert("RGB")
        size = image.size

        if is_standard_atlas_ratio(size):
            boxes = scaled_standard_boxes(size)
            main_box = boxes["main"]
            legend_box = boxes["legend"]
            used_standard_layout = True
        else:
            main_box = _safe_crop_box(size)
            legend_box = None
            used_standard_layout = False

        crop = image.crop(main_box)
        used_legend = False
        if overlay_legend and legend_box is not None:
            legend = image.crop(legend_box)
            used_legend = _paste_legend(crop, legend)

        tmp_output = output_path.with_suffix(output_path.suffix + ".tmp")
        crop.save(tmp_output, format="PNG", compress_level=1, optimize=False)
        tmp_output.replace(output_path)
        return CropResult(
            source_path=source_path,
            output_path=output_path,
            source_size=size,
            output_size=crop.size,
            used_standard_layout=used_standard_layout,
            used_legend=used_legend,
            preserved_full_image=False,
        )


def generate_all_crops(
    atlas_dir: Path = ATLAS_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    overwrite: bool = False,
) -> list[CropResult]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[CropResult] = []
    for source in sorted(atlas_dir.glob("*.png")):
        if not should_process_atlas_image(source):
            continue
        output = build_crop_output_path(source, output_dir)
        preserve_full_image = should_preserve_full_image(source)
        if not overwrite and output.exists() and output.stat().st_size > 0 and not preserve_full_image:
            continue
        results.append(crop_atlas_image(source, output, overlay_legend=True))
    return results


def main() -> None:
    results = generate_all_crops()
    standard_count = sum(1 for result in results if result.used_standard_layout)
    legend_count = sum(1 for result in results if result.used_legend)
    preserved_count = sum(1 for result in results if result.preserved_full_image)
    print(f"output_dir={DEFAULT_OUTPUT_DIR}")
    print(f"generated={len(results)}")
    print(f"standard_layout={standard_count}")
    print(f"legend_overlay={legend_count}")
    print(f"preserved_full_image={preserved_count}")


if __name__ == "__main__":
    main()
