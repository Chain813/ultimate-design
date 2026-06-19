from pathlib import Path

from PIL import Image

from tools.generate_atlas_crops import (
    ATLAS_DIR,
    BASE_PAGE_SIZE,
    build_crop_output_path,
    crop_atlas_image,
    scaled_standard_boxes,
    should_process_atlas_image,
    should_preserve_full_image,
)


def test_standard_boxes_scale_from_atlas_layout():
    boxes = scaled_standard_boxes((4480, 3168))

    assert boxes["main"] == (108, 476, 3140, 2976)
    assert boxes["legend"] == (3230, 416, 4420, 1060)


def test_crop_output_path_keeps_original_name_with_crop_suffix():
    source = Path("static/atlas/DR-054_竖向规划与排水分析图.png")
    output_dir = Path("static/exhibition_boards/atlas_crops")

    assert build_crop_output_path(source, output_dir) == output_dir / "DR-054_竖向规划与排水分析图__crop.png"


def test_preserve_full_image_list_matches_non_crop_sheet_types():
    assert should_preserve_full_image(Path("static/atlas/DR-009_案例借鉴与对标分析图.png"))
    assert should_preserve_full_image(Path("static/atlas/DR-073_老水产市场-鸟瞰效果图.png"))
    assert should_preserve_full_image(Path("static/atlas/DR-077_老水产市场-控制性指标表.png"))
    assert should_preserve_full_image(Path("static/atlas/DR-155_图册章节结构导图.png"))
    assert not should_preserve_full_image(Path("static/atlas/DR-054_竖向规划与排水分析图.png"))


def test_key_parcel_plan_and_existing_satellite_sheets_are_preserved_from_atlas():
    preserve_keywords = (
        "现状卫星图",
        "改造总平面图",
        "场地功能策划图",
        "交通流线分析图",
        "绿化分析图",
        "场地剖面解析图",
        "鸟瞰改造",
    )
    matching_sources = [
        source
        for source in ATLAS_DIR.glob("*.png")
        if should_process_atlas_image(source) and any(keyword in source.name for keyword in preserve_keywords)
    ]

    assert len(matching_sources) == 29
    for source in matching_sources:
        assert should_preserve_full_image(source), source.name


def test_crop_atlas_image_preserves_source_and_places_legend_bottom_right(tmp_path):
    source = tmp_path / "DR-999_test.png"
    output = tmp_path / "DR-999_test__crop.png"

    img = Image.new("RGB", BASE_PAGE_SIZE, "white")
    for x in range(54, 1570):
        for y in range(238, 1488):
            img.putpixel((x, y), (20, 160, 120))
    for x in range(1615, 2210):
        for y in range(208, 530):
            img.putpixel((x, y), (220, 80, 40))
    img.save(source)
    original_bytes = source.read_bytes()

    result = crop_atlas_image(source, output, overlay_legend=True)

    assert source.read_bytes() == original_bytes
    assert output.exists()
    assert result.output_path == output
    assert result.used_legend is True

    cropped = Image.open(output).convert("RGB")
    assert cropped.size[0] < BASE_PAGE_SIZE[0]
    assert cropped.size[1] < BASE_PAGE_SIZE[1]

    # The legend from the original top-right panel should now appear in the
    # lower-right part of the cropped main drawing.
    sample = cropped.getpixel((cropped.size[0] - 80, cropped.size[1] - 80))
    assert sample[0] > 180 and sample[1] < 120 and sample[2] < 90


def test_preserved_atlas_image_is_copied_full_size_without_legend_overlay(tmp_path):
    source = tmp_path / "DR-009_案例借鉴与对标分析图.png"
    output = tmp_path / "DR-009_案例借鉴与对标分析图__crop.png"

    img = Image.new("RGB", BASE_PAGE_SIZE, "white")
    for x in range(54, 1570):
        for y in range(238, 1488):
            img.putpixel((x, y), (20, 160, 120))
    for x in range(1615, 2210):
        for y in range(208, 530):
            img.putpixel((x, y), (220, 80, 40))
    img.save(source)
    original_bytes = source.read_bytes()

    result = crop_atlas_image(source, output, overlay_legend=True)

    assert source.read_bytes() == original_bytes
    assert result.output_size == BASE_PAGE_SIZE
    assert result.used_standard_layout is False
    assert result.used_legend is False
    assert Image.open(output).size == BASE_PAGE_SIZE
