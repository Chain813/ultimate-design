from pathlib import Path

from PIL import Image

from tools.generate_exhibition_board_tiles import (
    BOARD_TILE_FITTED_DIR,
    build_board_tile_output_path,
    build_fitted_tile_output_path,
    compose_fitted_tile_image,
    generate_board_tile,
    generate_fitted_tile,
    prepare_board_tile_image,
    trim_white_margins,
)
from tools.generate_atlas_crops import BASE_BOXES, BASE_PAGE_SIZE


def test_build_board_tile_output_path_replaces_crop_suffix():
    source = Path("static/exhibition_boards/atlas_crops/DR-108_市一中北侧-改造总平面图__crop.png")
    output_dir = Path("static/exhibition_boards/board_tiles")

    assert build_board_tile_output_path(source, output_dir) == output_dir / "DR-108_市一中北侧-改造总平面图__tile.png"


def test_build_fitted_tile_output_path_can_be_slot_specific():
    source = Path("static/exhibition_boards/board_tiles/DR-108_市一中北侧-改造总平面图__tile.png")

    assert (
        build_fitted_tile_output_path(source, BOARD_TILE_FITTED_DIR, slot_key="003")
        == BOARD_TILE_FITTED_DIR / "DR-108_市一中北侧-改造总平面图__fit_003.png"
    )


def test_trim_white_margins_removes_large_blank_edges():
    image = Image.new("RGB", (400, 300), "white")
    for x in range(70, 330):
        for y in range(60, 240):
            image.putpixel((x, y), (80, 140, 90))

    trimmed = trim_white_margins(image, padding_ratio=0)

    assert trimmed.size == (260, 180)


def test_generate_board_tile_preserves_source_and_writes_trimmed_copy(tmp_path):
    source = tmp_path / "DR-999_example__crop.png"
    output = tmp_path / "DR-999_example__tile.png"
    image = Image.new("RGB", (500, 360), "white")
    for x in range(100, 420):
        for y in range(90, 250):
            image.putpixel((x, y), (50, 110, 160))
    image.save(source)
    original_bytes = source.read_bytes()

    result = generate_board_tile(source, output)

    assert source.read_bytes() == original_bytes
    assert output.exists()
    assert result.source_size == (500, 360)
    assert result.output_size[0] < result.source_size[0]
    assert result.output_size[1] < result.source_size[1]


def test_compose_fitted_tile_matches_target_ratio_without_cropping_canvas():
    image = Image.new("RGB", (420, 180), (245, 247, 248))
    for x in range(70, 350):
        for y in range(35, 145):
            image.putpixel((x, y), (30, 120, 190))

    fitted = compose_fitted_tile_image(image, target_ratio=1.0, long_side=600)

    assert fitted.size == (600, 600)
    assert fitted.getbbox() is not None


def test_generate_fitted_tile_preserves_source_and_writes_ratio_matched_copy(tmp_path):
    source = tmp_path / "DR-999_example__tile.png"
    output = tmp_path / "DR-999_example__fit_001.png"
    image = Image.new("RGB", (500, 260), "white")
    for x in range(60, 440):
        for y in range(50, 210):
            image.putpixel((x, y), (80, 130, 70))
    image.save(source)
    original_bytes = source.read_bytes()

    result = generate_fitted_tile(source, output, target_ratio=1.25, long_side=500)

    assert source.read_bytes() == original_bytes
    assert output.exists()
    assert result.source_size == (500, 260)
    assert abs((result.output_size[0] / result.output_size[1]) - 1.25) <= 0.01


def test_prepare_board_tile_crops_standard_atlas_sheet_to_main_drawing_area():
    image = Image.new("RGB", BASE_PAGE_SIZE, "white")
    # Simulate title/header and right-side note content that should not drive A1 tile bounds.
    for x in range(60, 700):
        for y in range(70, 120):
            image.putpixel((x, y), (20, 20, 20))
    for x in range(1700, 2100):
        for y in range(260, 520):
            image.putpixel((x, y), (40, 40, 40))

    main_x1, main_y1, main_x2, main_y2 = BASE_BOXES["main"]
    for x in range(main_x1 + 220, main_x2 - 180):
        for y in range(main_y1 + 160, main_y2 - 140):
            image.putpixel((x, y), (60, 150, 110))

    tile = prepare_board_tile_image(image, "DR-108_市一中北侧-改造总平面图__crop.png")

    assert tile.size[0] < main_x2 - main_x1
    assert tile.size[1] < main_y2 - main_y1
    assert tile.size[0] > 900
    assert tile.size[1] > 800
