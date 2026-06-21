# -*- coding: utf-8 -*-
"""Render A1 exhibition board PNG previews with Playwright."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BOARD_DIR = ROOT / "static" / "exhibition_boards"
HTML_PATH = BOARD_DIR / "index.html"
COMBINED_OUTPUT = BOARD_DIR / "a1_boards_competition_preview.png"


def build_single_outputs(count: int) -> list[Path]:
    return [BOARD_DIR / f"a1_board_{index:02d}_preview.png" for index in range(1, count + 1)]


def render_previews() -> list[Path]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 2400, "height": 3350}, device_scale_factor=1)
        page.goto(HTML_PATH.as_uri())
        page.wait_for_load_state("networkidle")
        page.wait_for_function(
            "() => Array.from(document.images).every((img) => img.complete && img.naturalWidth > 0)"
        )

        boards = page.locator(".print-board")
        count = boards.count()
        single_outputs = build_single_outputs(count)
        outputs = [*single_outputs, COMBINED_OUTPUT]
        for index, output in enumerate(single_outputs):
            boards.nth(index).screenshot(path=output)

        page.screenshot(path=COMBINED_OUTPUT, full_page=True)
        browser.close()
    return outputs


def main() -> None:
    for output in render_previews():
        print(output)


if __name__ == "__main__":
    main()
