from src.engines.image_prompt_engine import (
    ImagePromptRequest,
    build_image_prompt,
    get_drawing_profile,
    revise_prompt_by_rating,
)


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


def test_level_one_research_scope_requires_redline():
    request = _base_request(
        chapter="01 项目认知篇",
        drawing_name="研究范围图",
        uploaded_channels=["卫星底图"],
        main_expression="表达研究范围和四至边界",
        legend_content="研究范围边界、主要道路、核心地标",
    )

    result = build_image_prompt(request)

    assert not result.can_generate
    assert "红线边界图" in result.missing_items
    assert "一级精度图纸" in "".join(result.notices)


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
        chapter="05 总体规划篇",
        drawing_name="道路交通系统规划图",
        uploaded_channels=["卫星底图", "红线边界图", "道路矢量图", "图例参考图"],
        main_expression="表达道路等级、交通组织和慢行衔接",
        legend_content="主干路、次干路、支路、慢行路径、换乘节点",
    )

    result = build_image_prompt(request)

    assert result.can_generate
    assert "不得改变研究范围边界" in result.prompt
    assert "请严格保持上传道路矢量图" in result.prompt
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
