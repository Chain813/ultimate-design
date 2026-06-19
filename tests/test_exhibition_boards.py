import pytest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD_DIR = ROOT / "static" / "exhibition_boards"

has_board_files = (BOARD_DIR / "index.html").exists() and (BOARD_DIR / "boards.css").exists()
pytestmark = pytest.mark.skipif(not has_board_files, reason="Exhibition board index.html or boards.css is missing.")


def _image_refs() -> list[str]:
    html = (BOARD_DIR / "index.html").read_text(encoding="utf-8")
    return [token.split('"', 1)[0] for token in html.split('src="')[1:]]


def _board_html(board_class: str) -> str:
    html = (BOARD_DIR / "index.html").read_text(encoding="utf-8")
    start = html.index(f'<section class="print-board {board_class}"')
    next_start = html.find('<section class="print-board ', start + 1)
    if next_start == -1:
        return html[start:]
    return html[start:next_start]


def test_exhibition_board_html_defines_four_a1_portrait_boards():
    html = (BOARD_DIR / "index.html").read_text(encoding="utf-8")

    assert html.count('class="print-board') == 4
    assert "技术逻辑与平台架构" in html
    assert "总体规划图册成果" in html
    assert "五个重点地块深化" in html
    assert "专项分析与实施支撑" in html


def test_exhibition_board_css_uses_a1_portrait_print_size():
    css = (BOARD_DIR / "boards.css").read_text(encoding="utf-8")

    assert "@page" in css
    assert "size: A1 portrait" in css
    assert "width: 594mm" in css
    assert "min-height: 841mm" in css


def test_exhibition_board_referenced_images_exist():
    refs = _image_refs()

    assert len(refs) >= 28
    missing = []
    for ref in refs:
        if ref.startswith("http"):
            continue
        path = (BOARD_DIR / ref).resolve()
        if not path.exists():
            missing.append(ref)

    assert missing == []


def test_exhibition_board_uses_fitted_tiles_without_referencing_crop_sources():
    html = (BOARD_DIR / "index.html").read_text(encoding="utf-8")

    assert "atlas_crops/" not in html
    assert "board_tiles/" not in html
    assert "../../output/" not in html
    assert "board_tiles_fitted/" in html


def test_exhibition_board_protected_drawings_use_full_atlas_sources():
    html = (BOARD_DIR / "index.html").read_text(encoding="utf-8")
    board_03 = _board_html("board-03")
    board_04 = _board_html("board-04")

    assert "../atlas/DR-048_总体鸟瞰白模效果图.png" in html
    assert "../atlas/DR-049_总体鸟瞰白模_彩色总图.png" in html
    assert "board_tiles_fitted/DR-049_" not in html

    board_03_refs = [token.split('"', 1)[0] for token in board_03.split('src="')[1:]]
    assert board_03_refs
    assert all(ref.startswith("../atlas/") for ref in board_03_refs)

    for prefix in ["DR-072_", "DR-093_", "DR-112_", "DR-130_", "DR-148_"]:
        assert f'img src="../atlas/{prefix}' in board_04
        assert f"board_tiles_fitted/{prefix}" not in board_04


def test_exhibition_board_competition_layout_is_dense_and_structured():
    html = (BOARD_DIR / "index.html").read_text(encoding="utf-8")

    assert html.count('class="print-board') == 4
    assert html.count('class="board-number"') == 4
    assert html.count('class="parcel-row"') == 5
    assert html.count('src="') >= 60
    assert "class=\"process-chain\"" in html
    assert "class=\"atlas-matrix\"" in html
    assert "class=\"support-mosaic\"" in html


def test_exhibition_board_does_not_reference_deleted_plan_legend_sheets():
    html = (BOARD_DIR / "index.html").read_text(encoding="utf-8")

    assert "DR-068_" not in html
    assert "DR-089_" not in html


def test_exhibition_board_media_uses_flush_no_frame_layout():
    html = (BOARD_DIR / "index.html").read_text(encoding="utf-8")
    css = (BOARD_DIR / "boards.css").read_text(encoding="utf-8")

    assert 'class="parcel-overview"' in html
    assert "object-fit: contain" in css
    assert "figure {" in css
    assert "border: 0;" in css
    assert "position: absolute;" in css


def test_exhibition_board_uses_category_based_tile_sizing():
    html = (BOARD_DIR / "index.html").read_text(encoding="utf-8")
    css = (BOARD_DIR / "boards.css").read_text(encoding="utf-8")

    assert "plan-tile" in html
    assert "effect-tile" in html
    assert "analysis-tile" in html
    assert html.count('class="analysis-grid"') == 5
    assert ".plan-tile" in css
    assert ".effect-tile" in css
    assert ".analysis-tile" in css
    assert ".analysis-grid" in css
    assert "grid-template-columns: repeat(3, 1fr);" in css


def test_exhibition_board_images_are_rendered_with_contain_to_preserve_full_drawings():
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError:
        pytest.skip("Playwright not installed, skipping browser render check.")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 2300, "height": 3300}, device_scale_factor=1)
        page.goto((BOARD_DIR / "index.html").as_uri())
        page.wait_for_load_state("networkidle")
        page.wait_for_function(
            "() => Array.from(document.images).every((img) => img.complete && img.naturalWidth > 0)"
        )
        mismatches = page.evaluate(
            """
            () => Array.from(document.querySelectorAll('figure img')).map((img, index) => {
              const objectFit = getComputedStyle(img).objectFit;
              return {
                index,
                src: img.getAttribute('src'),
                objectFit,
              };
            }).filter((item) => item.objectFit !== 'contain')
            """
        )
        browser.close()

    assert mismatches == []
