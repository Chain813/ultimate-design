# -*- coding: utf-8 -*-
"""Create tightly cropped and A1-fitted board image tiles from atlas derivatives."""
from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from tools.generate_atlas_crops import is_standard_atlas_ratio, scaled_standard_boxes


ROOT = Path(__file__).resolve().parent.parent
BOARD_DIR = ROOT / "static" / "exhibition_boards"
BOARD_HTML_PATH = BOARD_DIR / "index.html"
ATLAS_CROP_DIR = ROOT / "static" / "exhibition_boards" / "atlas_crops"
BOARD_TILE_DIR = ROOT / "static" / "exhibition_boards" / "board_tiles"
BOARD_TILE_FITTED_DIR = ROOT / "static" / "exhibition_boards" / "board_tiles_fitted"
HOMEPAGE_IMAGE_PATH = ROOT / "output" / "homepage_for_picsart.png"
DEFAULT_FITTED_LONG_SIDE = 1800

MAIN_DRAWING_TILE_KEYWORDS = (
    "现状卫星图",
    "改造总平面图",
    "场地功能策划图",
    "交通流线分析图",
    "绿化分析图",
    "场地剖面解析图",
    "鸟瞰效果图",
    "鸟瞰改造",
    "控制性指标表",
    "五地块深化设计总图",
    "总体鸟瞰白模",
)


@dataclass(frozen=True)
class BoardTileResult:
    source_path: Path
    output_path: Path
    source_size: tuple[int, int]
    output_size: tuple[int, int]


@dataclass(frozen=True)
class FittedTileRequest:
    source_ref: str
    source_path: Path
    output_path: Path
    target_ratio: float
    slot_size: tuple[float, float]


@dataclass(frozen=True)
class FittedTileResult:
    source_path: Path
    output_path: Path
    source_size: tuple[int, int]
    output_size: tuple[int, int]
    target_ratio: float


def build_board_tile_output_path(source_path: Path, output_dir: Path) -> Path:
    name = source_path.name
    if name.endswith("__crop.png"):
        tile_name = name.replace("__crop.png", "__tile.png")
    else:
        tile_name = f"{source_path.stem}__tile{source_path.suffix}"
    return output_dir / tile_name


def build_fitted_tile_output_path(source_path: Path, output_dir: Path, *, slot_key: str | None = None) -> Path:
    name = source_path.name
    suffix = source_path.suffix or ".png"
    if name.endswith("__tile.png"):
        stem = name.removesuffix("__tile.png")
    elif name.endswith("__crop.png"):
        stem = name.removesuffix("__crop.png")
    elif name.endswith("__fit.png"):
        stem = name.removesuffix("__fit.png")
    elif "__fit_" in name and name.endswith(".png"):
        stem = name.rsplit("__fit_", 1)[0]
    else:
        stem = source_path.stem

    if slot_key:
        return output_dir / f"{stem}__fit_{slot_key}{suffix}"
    return output_dir / f"{stem}__fit{suffix}"


def _content_bbox(image: Image.Image, threshold: int = 250) -> tuple[int, int, int, int] | None:
    gray = ImageOps.grayscale(image.convert("RGB"))
    mask = gray.point(lambda pixel: 255 if pixel < threshold else 0)
    return mask.getbbox()


def _scaled_content_bbox(
    image: Image.Image,
    *,
    threshold: int = 250,
    max_detection_side: int | None = None,
) -> tuple[int, int, int, int] | None:
    if max_detection_side is None or max(image.size) <= max_detection_side:
        return _content_bbox(image, threshold=threshold)

    width, height = image.size
    scale = max_detection_side / max(width, height)
    small_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    small = image.resize(small_size, Image.Resampling.BOX)
    small_bbox = _content_bbox(small, threshold=threshold)
    if small_bbox is None:
        return None

    x1, y1, x2, y2 = small_bbox
    return (
        max(0, math.floor(x1 / scale)),
        max(0, math.floor(y1 / scale)),
        min(width, math.ceil(x2 / scale)),
        min(height, math.ceil(y2 / scale)),
    )


def trim_white_margins(
    image: Image.Image,
    *,
    threshold: int = 250,
    padding_ratio: float = 0.012,
    max_detection_side: int | None = None,
) -> Image.Image:
    rgb = image.convert("RGB")
    bbox = _scaled_content_bbox(rgb, threshold=threshold, max_detection_side=max_detection_side)
    if bbox is None:
        return rgb.copy()

    width, height = rgb.size
    x1, y1, x2, y2 = bbox
    padding = round(min(width, height) * padding_ratio)
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(width, x2 + padding)
    y2 = min(height, y2 + padding)
    if x2 <= x1 or y2 <= y1:
        return rgb.copy()
    return rgb.crop((x1, y1, x2, y2))


def _as_opaque_rgb(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    if image.mode in {"RGBA", "LA"} or ("transparency" in image.info):
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        background.alpha_composite(rgba)
        return background.convert("RGB")
    return image.convert("RGB")


def _fitted_canvas_size(target_ratio: float, *, long_side: int = DEFAULT_FITTED_LONG_SIDE) -> tuple[int, int]:
    if target_ratio <= 0 or not math.isfinite(target_ratio):
        raise ValueError(f"target_ratio must be a positive finite number, got {target_ratio!r}")
    if long_side <= 0:
        raise ValueError(f"long_side must be positive, got {long_side!r}")

    if target_ratio >= 1:
        width = long_side
        height = max(1, round(width / target_ratio))
    else:
        height = long_side
        width = max(1, round(height * target_ratio))
    return width, height


def _resize_to_cover(image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    source_width, source_height = image.size
    target_width, target_height = target_size
    scale = max(target_width / source_width, target_height / source_height)
    resized_size = (max(target_width, math.ceil(source_width * scale)), max(target_height, math.ceil(source_height * scale)))
    resized = image.resize(resized_size, Image.Resampling.LANCZOS)
    left = max(0, (resized.width - target_width) // 2)
    top = max(0, (resized.height - target_height) // 2)
    return resized.crop((left, top, left + target_width, top + target_height))


def _resize_to_contain(image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    source_width, source_height = image.size
    target_width, target_height = target_size
    scale = min(target_width / source_width, target_height / source_height)
    resized_size = (max(1, round(source_width * scale)), max(1, round(source_height * scale)))
    return image.resize(resized_size, Image.Resampling.LANCZOS)


def compose_fitted_tile_image(
    source_image: Image.Image,
    *,
    target_ratio: float,
    long_side: int = DEFAULT_FITTED_LONG_SIDE,
) -> Image.Image:
    image = _as_opaque_rgb(source_image)
    canvas_size = _fitted_canvas_size(target_ratio, long_side=long_side)

    blur_radius = max(8, round(max(canvas_size) / 62))
    background = _resize_to_cover(image, canvas_size).filter(ImageFilter.GaussianBlur(radius=blur_radius))
    background = ImageEnhance.Contrast(background).enhance(0.72)
    background = ImageEnhance.Brightness(background).enhance(1.06)
    background = Image.blend(background, Image.new("RGB", canvas_size, (246, 248, 248)), 0.18)

    foreground = _resize_to_contain(image, canvas_size)
    left = (canvas_size[0] - foreground.width) // 2
    top = (canvas_size[1] - foreground.height) // 2
    background.paste(foreground, (left, top))
    return background


def _should_crop_to_main_drawing(source_name: str, size: tuple[int, int]) -> bool:
    return is_standard_atlas_ratio(size) and any(keyword in source_name for keyword in MAIN_DRAWING_TILE_KEYWORDS)


def prepare_board_tile_image(source_image: Image.Image, source_name: str) -> Image.Image:
    image = source_image.convert("RGB")
    if _should_crop_to_main_drawing(source_name, image.size):
        image = image.crop(scaled_standard_boxes(image.size)["main"])
    return trim_white_margins(image, max_detection_side=900)


def generate_board_tile(source_path: Path, output_path: Path, *, overwrite: bool = False) -> BoardTileResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if (
        not overwrite
        and output_path.exists()
        and output_path.stat().st_size > 0
        and output_path.stat().st_mtime >= source_path.stat().st_mtime
    ):
        with Image.open(source_path) as source_image, Image.open(output_path) as output_image:
            return BoardTileResult(source_path, output_path, source_image.size, output_image.size)

    with Image.open(source_path) as source_image:
        source_size = source_image.size
        tile = prepare_board_tile_image(source_image, source_path.name)
        output_size = tile.size

    tmp_output = output_path.with_suffix(output_path.suffix + ".tmp")
    tile.save(tmp_output, format="PNG", compress_level=2, optimize=False)
    tmp_output.replace(output_path)
    return BoardTileResult(source_path, output_path, source_size, output_size)


def generate_fitted_tile(
    source_path: Path,
    output_path: Path,
    *,
    target_ratio: float,
    overwrite: bool = False,
    long_side: int = DEFAULT_FITTED_LONG_SIDE,
) -> FittedTileResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if (
        not overwrite
        and output_path.exists()
        and output_path.stat().st_size > 0
        and output_path.stat().st_mtime >= source_path.stat().st_mtime
    ):
        with Image.open(source_path) as source_image, Image.open(output_path) as output_image:
            output_ratio = output_image.width / output_image.height
            if abs(output_ratio - target_ratio) <= 0.01:
                return FittedTileResult(source_path, output_path, source_image.size, output_image.size, target_ratio)

    with Image.open(source_path) as source_image:
        source_size = source_image.size
        fitted = compose_fitted_tile_image(source_image, target_ratio=target_ratio, long_side=long_side)
        output_size = fitted.size

    tmp_output = output_path.with_suffix(output_path.suffix + ".tmp")
    fitted.save(tmp_output, format="PNG", compress_level=2, optimize=False)
    tmp_output.replace(output_path)
    return FittedTileResult(source_path, output_path, source_size, output_size, target_ratio)


def _resolve_board_image_source(ref: str) -> Path:
    if ref.startswith("board_tiles_fitted/"):
        fitted_name = Path(ref).name
        if fitted_name.startswith("homepage_for_picsart__fit"):
            return HOMEPAGE_IMAGE_PATH
        source_name = re.sub(r"__fit(?:_[^.]*)?\.png$", "__tile.png", fitted_name)
        return BOARD_TILE_DIR / source_name
    if ref.startswith("board_tiles/"):
        return (BOARD_DIR / ref).resolve()
    if ref == "../../output/homepage_for_picsart.png":
        return HOMEPAGE_IMAGE_PATH
    return (BOARD_DIR / ref).resolve()


def collect_board_fitted_tile_requests(
    html_path: Path = BOARD_HTML_PATH,
    output_dir: Path = BOARD_TILE_FITTED_DIR,
) -> list[FittedTileRequest]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 2300, "height": 3300}, device_scale_factor=1)
        page.goto(html_path.as_uri())
        page.wait_for_load_state("networkidle")
        slots = page.evaluate(
            """
            () => Array.from(document.querySelectorAll('figure img')).map((img) => {
              const rect = img.getBoundingClientRect();
              return {
                src: img.getAttribute('src'),
                width: rect.width,
                height: rect.height
              };
            })
            """
        )
        browser.close()

    requests: list[FittedTileRequest] = []
    for index, slot in enumerate(slots, start=1):
        source_ref = slot["src"]
        width = float(slot["width"])
        height = float(slot["height"])
        if width <= 0 or height <= 0:
            raise ValueError(f"Image slot has invalid size: {source_ref!r} -> {width}x{height}")
        source_path = _resolve_board_image_source(source_ref)
        output_path = build_fitted_tile_output_path(source_path, output_dir, slot_key=f"{index:03d}")
        requests.append(
            FittedTileRequest(
                source_ref=source_ref,
                source_path=source_path,
                output_path=output_path,
                target_ratio=width / height,
                slot_size=(width, height),
            )
        )
    return requests


def rewrite_board_html_with_fitted_refs(
    requests: list[FittedTileRequest],
    *,
    html_path: Path = BOARD_HTML_PATH,
) -> None:
    html = html_path.read_text(encoding="utf-8")
    replacements = [request.output_path.relative_to(BOARD_DIR).as_posix() for request in requests]
    replacement_iter = iter(replacements)

    def replace_src(match: re.Match[str]) -> str:
        try:
            replacement = next(replacement_iter)
        except StopIteration as exc:
            raise ValueError("HTML contains more image src attributes than fitted requests") from exc
        return f'src="{replacement}"'

    updated = re.sub(r'src="[^"]+"', replace_src, html)
    try:
        next(replacement_iter)
    except StopIteration:
        pass
    else:
        raise ValueError("Fitted request count exceeds HTML image src attribute count")

    html_path.write_text(updated, encoding="utf-8")


def generate_fitted_tiles_for_board(
    *,
    html_path: Path = BOARD_HTML_PATH,
    output_dir: Path = BOARD_TILE_FITTED_DIR,
    overwrite: bool = False,
    rewrite_html: bool = False,
    long_side: int = DEFAULT_FITTED_LONG_SIDE,
) -> list[FittedTileResult]:
    requests = collect_board_fitted_tile_requests(html_path=html_path, output_dir=output_dir)
    results: list[FittedTileResult] = []
    missing_sources = [request.source_path for request in requests if not request.source_path.exists()]
    if missing_sources:
        missing = "\n".join(str(path) for path in missing_sources)
        raise FileNotFoundError(f"Missing fitted tile source images:\n{missing}")

    for request in requests:
        results.append(
            generate_fitted_tile(
                request.source_path,
                request.output_path,
                target_ratio=request.target_ratio,
                overwrite=overwrite,
                long_side=long_side,
            )
        )

    if rewrite_html:
        rewrite_board_html_with_fitted_refs(requests, html_path=html_path)
    return results


def generate_all_board_tiles(
    source_dir: Path = ATLAS_CROP_DIR,
    output_dir: Path = BOARD_TILE_DIR,
    *,
    overwrite: bool = False,
) -> list[BoardTileResult]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[BoardTileResult] = []
    for source in sorted(source_dir.glob("*__crop.png")):
        output = build_board_tile_output_path(source, output_dir)
        results.append(generate_board_tile(source, output, overwrite=overwrite))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board-tiles", action="store_true", help="Generate tightly cropped board_tiles from atlas_crops.")
    parser.add_argument("--fit-board", action="store_true", help="Generate board_tiles_fitted from the current A1 board layout.")
    parser.add_argument("--rewrite-html", action="store_true", help="Rewrite A1 board image refs to board_tiles_fitted outputs.")
    parser.add_argument("--overwrite", action="store_true", help="Regenerate outputs even if they appear current.")
    parser.add_argument("--long-side", type=int, default=DEFAULT_FITTED_LONG_SIDE, help="Long side in pixels for fitted output.")
    args = parser.parse_args()

    if not args.board_tiles and not args.fit_board:
        args.board_tiles = True

    if args.board_tiles:
        results = generate_all_board_tiles(overwrite=args.overwrite)
        trimmed = sum(1 for result in results if result.output_size != result.source_size)
        print(f"board_tile_output_dir={BOARD_TILE_DIR}")
        print(f"board_tiles_generated={len(results)}")
        print(f"board_tiles_trimmed={trimmed}")

    if args.fit_board:
        fitted_results = generate_fitted_tiles_for_board(
            overwrite=args.overwrite,
            rewrite_html=args.rewrite_html,
            long_side=args.long_side,
        )
        print(f"fitted_tile_output_dir={BOARD_TILE_FITTED_DIR}")
        print(f"fitted_tiles_generated={len(fitted_results)}")
        print(f"html_rewritten={args.rewrite_html}")


if __name__ == "__main__":
    main()
