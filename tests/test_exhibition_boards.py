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


def _board_image_refs(board_class: str) -> list[str]:
    board = _board_html(board_class)
    return [token.split('"', 1)[0] for token in board.split('src="')[1:]]


def test_exhibition_board_html_defines_five_a1_portrait_boards():
    html = (BOARD_DIR / "index.html").read_text(encoding="utf-8")

    assert html.count('class="print-board') == 5
    for board_class in ["board-01", "board-02", "board-03", "board-04", "board-05"]:
        assert f'class="print-board {board_class}"' in html
    assert "政经良性循环与实施政策策划" in html


def test_exhibition_board_css_uses_a1_portrait_print_size():
    css = (BOARD_DIR / "boards.css").read_text(encoding="utf-8")

    assert "@page" in css
    assert "size: A1 portrait" in css
    assert "width: 594mm" in css
    assert "min-height: 841mm" in css


def test_exhibition_board_uses_white_main_paper_tone():
    css = (BOARD_DIR / "boards.css").read_text(encoding="utf-8")

    assert "--paper: #ffffff;" in css
    assert "var(--paper)" in css
    assert "radial-gradient(circle" not in css


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


def test_exhibition_board_does_not_reference_crop_or_fitted_sources():
    html = (BOARD_DIR / "index.html").read_text(encoding="utf-8")

    assert "atlas_crops/" not in html
    assert "board_tiles/" not in html
    assert "board_tiles_fitted/" not in html
    assert "../../output/" not in html


def test_exhibition_board_protected_drawings_use_full_atlas_sources():
    html = (BOARD_DIR / "index.html").read_text(encoding="utf-8")
    board_02 = _board_html("board-02")
    board_03 = _board_html("board-03")
    board_04 = _board_html("board-04")
    board_05 = _board_html("board-05")

    assert "../atlas/DR-048_总体鸟瞰白模效果图.png" in html
    assert "../atlas/DR-049_总体鸟瞰白模_彩色总图.png" in html
    assert "board_tiles_fitted/DR-049_" not in html
    for code in ["DR-035_", "DR-036_", "DR-037_", "DR-038_", "DR-040_", "DR-041_", "DR-042_", "DR-043_", "DR-044_", "DR-045_", "DR-046_", "DR-047_"]:
        assert f'img src="../atlas/{code}' in board_02

    board_02_refs = [token.split('"', 1)[0] for token in board_02.split('src="')[1:]]
    assert board_02_refs
    assert all(ref.startswith("../atlas/") for ref in board_02_refs)

    board_03_refs = [token.split('"', 1)[0] for token in board_03.split('src="')[1:]]
    assert board_03_refs
    assert all(ref.startswith("../atlas/") for ref in board_03_refs)

    board_04_refs = [token.split('"', 1)[0] for token in board_04.split('src="')[1:]]
    assert board_04_refs
    assert all(ref.startswith("../atlas/") for ref in board_04_refs)

    for prefix in ["DR-072_", "DR-093_", "DR-112_", "DR-130_", "DR-148_"]:
        assert f'img src="../atlas/{prefix}' in board_05
        assert f"board_tiles_fitted/{prefix}" not in board_05


def test_exhibition_board_uses_dr56_dr57_policy_reference_sources():
    from PIL import Image

    board_05 = _board_html("board-05")
    for filename in ["DR-056_投资估算与经济测算图.png", "DR-057_公众参与与博弈协商成果图.png"]:
        source = ROOT / "static" / "atlas" / filename

        assert source.exists()
        with Image.open(source) as image:
            assert image.width >= 1400
            assert image.height >= 900
    for phrase in ["投资估算", "经济测算", "公众参与", "博弈协商", "7,600 万元", "91.5%"]:
        assert phrase in board_05


def test_exhibition_board_02_uses_x4plus_enhanced_traffic_system_sheet():
    from PIL import Image

    traffic_sheet = ROOT / "static" / "atlas" / "DR-043_道路交通系统规划图.png"

    assert '../atlas/DR-043_道路交通系统规划图.png' in _board_html("board-02")
    with Image.open(traffic_sheet) as image:
        assert image.width == 5964
        assert image.height == 4220


def test_exhibition_board_04_groups_effects_by_parcel_with_plan_reference():
    html_04 = _board_html("board-04")
    html_05 = _board_html("board-05")

    assert html_05.count('<section class="support-mosaic"') == 1
    assert html_05.split('<section class="support-mosaic"', 1)[1].split("</section>", 1)[0].count("<figure") == 9

    assert html_04.count('<section class="effect-rows-container"') == 1
    effect_board = html_04.split('<section class="effect-rows-container"', 1)[1].split("</section>", 1)[0]
    assert effect_board.count('<article class="effect-parcel-row') == 5
    for plan_code in ["DR-067_", "DR-088_", "DR-108_", "DR-127_", "DR-145_"]:
        assert f'src="../atlas/{plan_code}' in effect_board
    for code in ["DR-073_", "DR-074_", "DR-078_", "DR-079_", "DR-080_", "DR-081_"]:
        assert f'src="../atlas/{code}' in effect_board
    for code in ["DR-094_", "DR-098_", "DR-099_", "DR-100_", "DR-101_"]:
        assert f'src="../atlas/{code}' in effect_board
    for code in ["DR-113_", "DR-117_", "DR-118_", "DR-119_", "DR-120_"]:
        assert f'src="../atlas/{code}' in effect_board
    for code in ["DR-131_", "DR-135_", "DR-136_", "DR-137_", "DR-138_"]:
        assert f'src="../atlas/{code}' in effect_board
    for code in ["DR-149_", "DR-153_", "DR-154_"]:
        assert f'src="../atlas/{code}' in effect_board


def test_exhibition_board_04_makes_analysis_tiles_smaller_than_effect_gallery():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 2300, "height": 3300}, device_scale_factor=1)
        page.goto((BOARD_DIR / "index.html").as_uri())
        page.wait_for_load_state("networkidle")
        sizes = page.evaluate(
            """
            () => {
              const board_04 = document.querySelector('.board-04').getBoundingClientRect();
              const board_05 = document.querySelector('.board-05').getBoundingClientRect();
              const analysis = document.querySelector('.board-05 .support-mosaic').getBoundingClientRect();
              const effects = document.querySelector('.board-04 .effect-rows-container').getBoundingClientRect();
              return {board_04, board_05, analysis, effects};
            }
            """
        )
        browser.close()

    assert sizes["analysis"]["height"] < sizes["effects"]["height"] * 0.70
    assert sizes["effects"]["height"] > sizes["board_04"]["height"] * 0.50


def test_exhibition_board_04_analysis_frames_fit_drawings_and_sections_are_prominent():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 2300, "height": 3300}, device_scale_factor=1)
        page.goto((BOARD_DIR / "index.html").as_uri())
        page.wait_for_load_state("networkidle")
        sizes = page.evaluate(
            """
            () => {
              const board = document.querySelector('.board-05').getBoundingClientRect();
              const analysisItems = Array.from(document.querySelectorAll('.board-05 .support-mosaic figure')).map((figure) => {
                const figureRect = figure.getBoundingClientRect();
                const imgRect = figure.querySelector('img').getBoundingClientRect();
                return {
                  fillX: imgRect.width / figureRect.width,
                  fillY: imgRect.height / figureRect.height,
                };
              });
              const sectionStack = document.querySelector('.board-05 .section-stack').getBoundingClientRect();
              const sectionItems = Array.from(document.querySelectorAll('.board-05 .section-stack figure')).map((figure) => {
                const figureRect = figure.getBoundingClientRect();
                const imgRect = figure.querySelector('img').getBoundingClientRect();
                return {
                  fillX: imgRect.width / figureRect.width,
                  fillY: imgRect.height / figureRect.height,
                };
              });
              return {board, analysisItems, sectionStack, sectionItems};
            }
            """
        )
        browser.close()

    assert all(item["fillX"] > 0.92 for item in sizes["analysisItems"])
    assert all(item["fillY"] > 0.76 for item in sizes["analysisItems"])
    assert sizes["sectionStack"]["width"] > sizes["board"]["width"] * 0.32
    assert sizes["sectionStack"]["height"] > sizes["board"]["height"] * 0.26
    assert all(item["fillX"] > 0.95 for item in sizes["sectionItems"])
    assert all(item["fillY"] > 0.95 for item in sizes["sectionItems"])


def test_exhibition_board_01_uses_dense_real_project_screenshot_wall():
    html = _board_html("board-01")

    assert '<section class="project-screenshot-grid"' in html
    assert html.count('class="project-shot') >= 7
    for ref in [
        "project_shots/app_home.png",
        "project_shots/diagnosis_page.png",
        "project_shots/data_dashboard_page.png",
        "project_shots/overall_design_page.png",
        "project_shots/key_parcels_page.png",
        "project_shots/aigc_page.png",
        "project_shots/results_page.png",
    ]:
        assert f'src="{ref}"' in html


def test_exhibition_board_competition_layout_is_dense_and_structured():
    html = (BOARD_DIR / "index.html").read_text(encoding="utf-8")

    assert html.count('class="print-board') == 5
    assert html.count('class="board-number"') == 5
    assert html.count('class="parcel-row"') == 5 or html.count('class="effect-parcel-row"') == 5
    assert html.count('src="') >= 60
    assert 'class="tech-ribbon"' in html
    assert 'class="atlas-matrix"' in html
    assert 'class="support-mosaic"' in html
    assert 'class="policy-board-layout"' in html or 'class="policy-section-container"' in html


def test_exhibition_board_02_and_05_split_strategy_sheets_without_repetition():
    board_02_refs = _board_image_refs("board-02")
    board_05_refs = _board_image_refs("board-05")
    uploaded_strategy_codes = {f"DR-{index:03d}_" for index in range(27, 34)}

    board_02_strategy = {code for code in uploaded_strategy_codes if any(code in ref for ref in board_02_refs)}
    board_05_strategy = {code for code in uploaded_strategy_codes if any(code in ref for ref in board_05_refs)}

    assert board_02_strategy == {"DR-027_", "DR-028_", "DR-029_", "DR-030_", "DR-031_"}
    assert board_05_strategy == {"DR-032_", "DR-033_"}
    assert board_02_strategy.isdisjoint(board_05_strategy)


def test_exhibition_board_02_keeps_strategy_mainline_without_dropping_atlas_matrix():
    board_02 = _board_html("board-02")

    assert 'class="strategy-mainline"' in board_02
    for code in ["DR-027_", "DR-028_", "DR-029_", "DR-030_", "DR-031_"]:
        assert f'img src="../atlas/{code}' in board_02
    for code in ["DR-035_", "DR-036_", "DR-037_", "DR-038_", "DR-040_", "DR-041_", "DR-042_", "DR-043_", "DR-044_", "DR-045_", "DR-046_", "DR-047_"]:
        assert f'img src="../atlas/{code}' in board_02


def test_exhibition_board_05_uses_strategy_policy_sheets_instead_of_generated_a3_strip():
    board_05 = _board_html("board-05")

    assert "三方政经闭环循环" in board_05 or "政经良性循环与实施政策策划" in board_05
    assert "../atlas/DR-032_设计原则与理念图.png" in board_05
    assert "../atlas/DR-033_设计目标体系图.png" in board_05
    assert "../atlas/policy_a3/" not in board_05
    assert "真实地图" not in board_05
    assert "卫星图" not in board_05


def test_exhibition_board_05_has_policy_basis_and_visual_policy_diagrams():
    board_05 = _board_html("board-05")

    for phrase in ["政策依据", "投资估算与经济测算", "公众参与与博弈协商", "7,600 万元", "91.5%", "共识达成"]:
        assert phrase in board_05
    for visual_class in [
        "policy-basis-panel",
        "policy-mindmap",
        "policy-fund-flow",
        "policy-kpi-loop",
        "policy-roadmap",
        "policy-program-matrix",
        "policy-agent-map",
        "policy-risk-grid",
    ]:
        assert visual_class in board_05
    assert board_05.count('class="mind-node') >= 12
    assert board_05.count('class="policy-chip') >= 18
    assert board_05.count('class="policy-lane') >= 5
    assert board_05.count('class="policy-risk') >= 4


def test_exhibition_board_05_keeps_policy_reference_and_risk_bands_compact():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 2300, "height": 3300}, device_scale_factor=1)
        page.goto((BOARD_DIR / "index.html").as_uri())
        page.wait_for_load_state("networkidle")
        sizes = page.evaluate(
            """
            () => {
              const board = document.querySelector('.board-05').getBoundingClientRect();
              const basis = document.querySelector('.board-05 .policy-basis-panel').getBoundingClientRect();
              const risk = document.querySelector('.board-05 .policy-risk-grid').getBoundingClientRect();
              return {board, basis, risk};
            }
            """
        )
        browser.close()

    assert sizes["basis"]["height"] < sizes["board"]["height"] * 0.12
    assert sizes["risk"]["height"] < sizes["board"]["height"] * 0.085


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


def test_exhibition_board_02_master_images_are_prominent():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 2300, "height": 3300}, device_scale_factor=1)
        page.goto((BOARD_DIR / "index.html").as_uri())
        page.wait_for_load_state("networkidle")
        sizes = page.evaluate(
            """
            () => {
              const board = document.querySelector('.board-02').getBoundingClientRect();
              const hero = document.querySelector('.board-02 .master-hero').getBoundingClientRect();
              const secondary = document.querySelector('.board-02 .master-secondary').getBoundingClientRect();
              return {board, hero, secondary};
            }
            """
        )
        browser.close()

    assert sizes["hero"]["width"] > sizes["board"]["width"] * 0.42
    assert sizes["secondary"]["width"] > sizes["board"]["width"] * 0.42
    assert sizes["hero"]["height"] > sizes["board"]["height"] * 0.20
    assert sizes["secondary"]["height"] > sizes["board"]["height"] * 0.20


def test_exhibition_board_01_uses_light_main_tone_outside_title():
    css = (BOARD_DIR / "boards.css").read_text(encoding="utf-8")

    assert ".board-01 .tech-ribbon span" in css
    assert ".board-01 .tech-proof-panel" in css
    assert ".board-01 .tech-ribbon span {\n  background: #f7f9fa;" in css
    assert ".board-01 .tech-proof-panel {\n  background: #ffffff;" in css
    assert ".board-01 .proof-card {\n  background: #f7f9fa;" in css
    assert ".board-01 figcaption {\n  background: #f7f9fa;" in css


def test_board01_tech_diagram_assets_are_light_and_dense():
    from PIL import Image

    diagram_dir = BOARD_DIR / "tech_diagrams"
    paths = sorted(diagram_dir.glob("board01_*.png"))
    assert len(paths) >= 15

    for path in paths:
        with Image.open(path).convert("RGB") as image:
            pixels = image.resize((120, 72)).getdata()
            total = len(pixels)
            dark_ratio = sum(1 for r, g, b in pixels if (r + g + b) / 3 < 65) / total
            nonwhite_ratio = sum(1 for r, g, b in pixels if (r + g + b) / 3 < 238) / total

        assert dark_ratio < 0.05, path.name
        assert nonwhite_ratio > 0.10, path.name
