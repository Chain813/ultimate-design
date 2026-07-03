import subprocess
import sys
from pathlib import Path

import pytest

from src.engines.drawing_prompt_engine import (
    BOOK_CHAPTERS,
    ImagePromptRequest,
    build_image_prompt,
    flatten_chapter_drawings,
    get_book_chapters,
    get_drawing_profile,
    revise_prompt_by_rating,
)
from src.engines.key_plot_engine import KeyPlot


def _base_request(**overrides):
    data = {
        "chapter": "04 策略生成篇",
        "drawing_name": "总体策略图",
        "drawing_type": "策略生成类",
        "aspect_ratio": "A3横版",
        "output_scene": "A3横版图册",
        "uploaded_channels": [],
        "main_expression": "表达问题-策略-空间响应关系",
        "legend_content": "问题类型、策略类型、空间响应类型",
        "evidence_blocks": {"阶段四博弈共识": "保护历史风貌，同时补足公共空间。"},
    }
    data.update(overrides)
    return ImagePromptRequest(**data)


def _plot(index: int) -> KeyPlot:
    return KeyPlot(index=index, plot_id=str(index), name=f"测试地块{index}")


def test_book_chapters_expand_dynamic_key_plots():
    plots = [_plot(1), _plot(2), _plot(3)]

    chapters = get_book_chapters(key_plots=plots)
    detail = chapters.get("06 重点地段更新改造设计", [])

    assert len(detail) == 27
    assert detail[0] == "地块1现状问题图"
    assert detail[-1] == "地块3运营场景图"
    assert "地块4现状问题图" not in detail


def test_flatten_chapter_drawings_accepts_dynamic_key_plots():
    names = flatten_chapter_drawings(key_plots=[_plot(1)])

    assert "地块1街道断面图" in names
    assert "地块2街道断面图" not in names


def test_legacy_book_chapters_snapshot_stays_static_while_flatten_is_dynamic():
    static_detail = BOOK_CHAPTERS["06 重点地段更新改造设计"]
    dynamic_names = flatten_chapter_drawings(key_plots=[_plot(1)])

    assert len(static_detail) == 45
    assert "地块5街道断面图" in static_detail
    assert "地块2街道断面图" not in dynamic_names


def test_arbitrary_plot_index_profile_is_level_one():
    profile = get_drawing_profile("地块12平面深化图")

    assert profile.precision == "一级精度"
    assert "红线边界图" in profile.required_uploads


def test_static_strategy_chapter_uses_dynamic_key_plot_label():
    assert "重点地块定位图" in BOOK_CHAPTERS["04 策略生成篇"]
    assert "5个重点地块定位图" not in BOOK_CHAPTERS["04 策略生成篇"]


def test_legacy_key_plot_locator_name_matches_current_profile():
    legacy = get_drawing_profile("5个重点地块定位图")
    current = get_drawing_profile("重点地块定位图")

    assert legacy.precision == current.precision
    assert legacy.drawing_type == current.drawing_type
    assert legacy.required_uploads == current.required_uploads


def test_module_import_does_not_load_key_plot_engine_at_top_level():
    code = (
        "import sys; "
        "import src.engines.drawing_prompt_engine; "
        "print('src.engines.key_plot_engine' in sys.modules)"
    )

    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )

    assert completed.stdout.strip() == "False"


def test_level_one_research_scope_requires_redline():
    request = _base_request(
        chapter="01 项目认知篇",
        drawing_name="研究范围图",
        uploaded_channels=["卫星底图"],
        main_expression="表达研究范围和四至边界",
        legend_content="研究范围边界、主要道路、核心地标",
    )

    result = build_image_prompt(request)

    assert result.can_generate
    assert "红线边界图" in result.missing_items


def test_level_two_without_data_generates_template_only_prompt():
    request = _base_request(
        chapter="03 价值评估篇",
        drawing_name="遗产价值评估热力图",
        uploaded_channels=[],
        main_expression="表达遗产价值评价等级和保护优先级",
        legend_content="高价值、中价值、低价值、保护冲突点",
    )

    result = build_image_prompt(request)

    assert result.can_generate
    assert result.template_only
    assert "视觉表达模板提示词" in result.prompt
    assert "不要虚构热力数据" in result.negative_prompt


def test_level_one_complete_prompt_includes_reference_constraints():
    request = _base_request(
        chapter="05 整体概念设计和更新",
        drawing_name="道路交通系统规划图",
        uploaded_channels=["卫星底图", "红线边界图", "道路矢量图", "图例参考图", "固定图框模板"],
        main_expression="表达道路等级、交通组织和慢行衔接",
        legend_content="主干路、次干路、支路、慢行路径、换乘节点",
    )

    result = build_image_prompt(request)

    assert result.can_generate
    assert "不得改变研究范围边界" in result.prompt
    assert "请严格保持上传道路矢量图" in result.prompt
    assert "请严格套用上传的固定图框" in result.prompt
    assert "不要改变道路结构" in result.negative_prompt


def test_plot_detail_drawing_is_level_one():
    profile = get_drawing_profile("地块3平面深化图")

    assert profile.precision == "一级精度"
    assert "红线边界图" in profile.required_uploads


def test_rating_revision_strengthens_boundary_and_text_rules():
    prompt = "生成一张总体策略图。"

    revised = revise_prompt_by_rating(prompt, "B级：需要轻微后期修改", ["边界不准", "文字乱码"])

    assert "必须严格保持上传红线图边界" in revised
    assert "只生成一级标题和少量关键词" in revised


def test_prompt_includes_recommended_layout_clause():
    request = _base_request(
        drawing_name="地块2改造前后对比图",
        drawing_type="重点地块深化类",
        main_expression="对比更新前后的街区空间品质和功能提升",
        layout_structure="保留改造前后对比的补充说明",
    )

    result = build_image_prompt(request)

    assert result.can_generate
    assert "Layout profile: dual_compare" in result.prompt
    assert "保留改造前后对比的补充说明" in result.prompt
    assert "Times New Roman" in result.prompt


def test_explicit_layout_profile_id_overrides_recommendation():
    request = _base_request(
        drawing_name="地块2改造前后对比图",
        drawing_type="重点地块深化类",
        layout_profile_id="analysis_dashboard",
    )

    result = build_image_prompt(request)

    assert "Layout profile: analysis_dashboard" in result.prompt
    assert "Layout profile: dual_compare" not in result.prompt


def test_unknown_layout_profile_id_raises():
    request = _base_request(layout_profile_id="unknown_layout_profile")

    with pytest.raises(ValueError, match="unknown_layout_profile"):
        build_image_prompt(request)
