from PIL import Image, ImageChops
import pytest

import src.engines.drawing_layout_engine as layout_engine
from src.engines.drawing_layout_engine import (
    A3_LANDSCAPE_SIZE,
    LayoutProfile,
    compose_layout_sheet,
    get_layout_profile,
    layout_prompt_clause,
    list_layout_profiles,
    recommend_layout_profile,
)


EXPECTED_LAYOUT_IDS = {
    "map_legend_right",
    "dual_compare",
    "analysis_dashboard",
    "matrix_storyboard",
    "full_bleed_effect",
    "chapter_cover",
}


def _sample_image(seed: int) -> Image.Image:
    width = 640 + seed * 31
    height = 420 + seed * 17
    color = (
        (70 + seed * 37) % 255,
        (120 + seed * 53) % 255,
        (180 + seed * 29) % 255,
    )
    return Image.new("RGB", (width, height), color)


def _assert_not_blank(image: Image.Image) -> None:
    baseline = Image.new("RGB", image.size, image.getpixel((0, 0)))
    diff = ImageChops.difference(image, baseline)
    assert diff.getbbox() is not None


def _assert_color_close(pixel, expected, tolerance: int = 4) -> None:
    assert all(abs(pixel[index] - expected[index]) <= tolerance for index in range(3))


def _spy_drawn_text(monkeypatch):
    drawn_texts: list[str] = []
    original_draw_text = layout_engine._draw_text

    def spy(draw, xy, text, size, fill):
        drawn_texts.append(str(text))
        return original_draw_text(draw, xy, text, size, fill)

    monkeypatch.setattr(layout_engine, "_draw_text", spy)
    return drawn_texts


def test_a3_landscape_size_matches_print_target():
    assert A3_LANDSCAPE_SIZE == (4961, 3508)


def test_registry_contains_expected_unique_layout_profiles():
    profiles = list_layout_profiles()
    layout_ids = [profile.layout_id for profile in profiles]

    assert EXPECTED_LAYOUT_IDS.issubset(layout_ids)
    assert len(layout_ids) == len(set(layout_ids))
    assert len(layout_ids) >= 6
    assert all(isinstance(profile, LayoutProfile) for profile in profiles)
    assert all(isinstance(profile.slots, tuple) for profile in profiles)
    assert all(isinstance(profile.prompt_rules, tuple) for profile in profiles)


def test_layout_slot_boxes_are_valid_and_inside_a3_canvas():
    canvas_width, canvas_height = A3_LANDSCAPE_SIZE

    for profile in list_layout_profiles():
        assert profile.slots
        for slot in profile.slots:
            left, top, right, bottom = slot.box

            assert 0 <= left < right <= canvas_width
            assert 0 <= top < bottom <= canvas_height
            assert slot.slot_id
            assert slot.label
            assert slot.purpose


def test_get_layout_profile_rejects_unknown_id():
    with pytest.raises(ValueError, match="unknown_layout"):
        get_layout_profile("unknown_layout")


@pytest.mark.parametrize(
    ("drawing_name", "expected_layout_id"),
    [
        ("地块改造前后对比图", "dual_compare"),
        ("AIGC鸟瞰效果图", "full_bleed_effect"),
        ("人视运营场景效果图", "full_bleed_effect"),
        ("用地现状活力热力评价图", "analysis_dashboard"),
        ("更新策略目标体系流程技术推演图", "matrix_storyboard"),
        ("项目封面与目录背景图", "chapter_cover"),
        ("道路交通系统规划图", "map_legend_right"),
    ],
)
def test_recommend_layout_profile_matches_drawing_semantics(drawing_name, expected_layout_id):
    profile = recommend_layout_profile(drawing_name)

    assert profile.layout_id == expected_layout_id


def test_layout_prompt_clause_includes_slots_rules_and_text_safety_rule():
    profile = get_layout_profile("analysis_dashboard")

    clause = layout_prompt_clause(profile)

    assert profile.layout_id in clause
    assert "不得让文字压住主图" in clause
    for slot in profile.slots:
        assert slot.label in clause
        assert slot.purpose in clause
    for rule in profile.prompt_rules:
        assert rule in clause


@pytest.mark.parametrize("layout_id", sorted(EXPECTED_LAYOUT_IDS))
def test_compose_layout_sheet_outputs_non_blank_rgb_a3_sheet_for_every_profile(layout_id):
    profile = get_layout_profile(layout_id)
    images = {
        slot.slot_id: _sample_image(index + 1)
        for index, slot in enumerate(profile.slots)
    }

    sheet = compose_layout_sheet(
        layout_id,
        images,
        title="重点地段更新图纸",
        chapter="06 重点地段更新改造设计",
        legend_items=[("历史建筑", "#f2c94c"), ("慢行系统", "#2d9cdb")],
        notes=["指标占位：建筑高度、开发强度", "结论占位：公共空间连续性提升"],
    )

    assert sheet.size == A3_LANDSCAPE_SIZE
    assert sheet.mode == "RGB"
    _assert_not_blank(sheet)


def test_slot_image_is_composited_into_its_declared_slot():
    red = (225, 32, 32)
    sheet = compose_layout_sheet(
        "map_legend_right",
        {"main_map": Image.new("RGB", (1200, 900), red)},
        title="主图落槽测试",
    )

    main_map = next(slot for slot in get_layout_profile("map_legend_right").slots if slot.slot_id == "main_map")
    center = ((main_map.box[0] + main_map.box[2]) // 2, (main_map.box[1] + main_map.box[3]) // 2)
    _assert_color_close(sheet.getpixel(center), red)


def test_legend_items_use_label_color_order(monkeypatch):
    drawn_texts = _spy_drawn_text(monkeypatch)
    legend_color = (242, 201, 76)

    sheet = compose_layout_sheet(
        "map_legend_right",
        {"main_map": Image.new("RGB", (1200, 900), (230, 230, 230))},
        title="图例顺序测试",
        legend_items=[("历史建筑", "#f2c94c")],
    )

    legend_slot = next(
        slot for slot in get_layout_profile("map_legend_right").slots if slot.slot_id == "legend_panel"
    )
    left, top, _, _ = legend_slot.box
    swatch_center = (left + 42 + 21, top + 42 + 78 + 25)

    _assert_color_close(sheet.getpixel(swatch_center), legend_color)
    assert "历史建筑" in drawn_texts
    assert "#f2c94c" not in drawn_texts


def test_empty_notes_render_placeholder_text(monkeypatch):
    drawn_texts = _spy_drawn_text(monkeypatch)

    sheet = compose_layout_sheet(
        "map_legend_right",
        {"main_map": _sample_image(3)},
        title="空 notes 占位测试",
        notes=[],
    )

    assert sheet.size == A3_LANDSCAPE_SIZE
    assert any("占位" in text for text in drawn_texts)
