# -*- coding: utf-8 -*-
"""Render A1 exhibition board PNG previews with Playwright."""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent.parent
BOARD_DIR = ROOT / "static" / "exhibition_boards"
HTML_PATH = BOARD_DIR / "index.html"
SINGLE_OUTPUTS = [
    BOARD_DIR / "a1_board_01_preview.png",
    BOARD_DIR / "a1_board_02_preview.png",
    BOARD_DIR / "a1_board_03_preview.png",
    BOARD_DIR / "a1_board_04_preview.png",
]
COMBINED_OUTPUT = BOARD_DIR / "a1_boards_competition_preview.png"


def render_previews() -> list[Path]:
    outputs = [*SINGLE_OUTPUTS, COMBINED_OUTPUT]
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
        if count != len(SINGLE_OUTPUTS):
            raise RuntimeError(f"Expected {len(SINGLE_OUTPUTS)} boards, found {count}")
        for index, output in enumerate(SINGLE_OUTPUTS):
            boards.nth(index).screenshot(path=output)

        page.screenshot(path=COMBINED_OUTPUT, full_page=True)
        browser.close()
    return outputs


def main() -> None:
    for output in render_previews():
        print(output)


if __name__ == "__main__":
    main()
