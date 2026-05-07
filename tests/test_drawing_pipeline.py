import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.append(str(root))
sys.modules.setdefault("streamlit", type(sys)("streamlit_mock"))

from src.engines.drawing_prompt_engine import (
    CompletenessReport,
    PromptEngineError,
    TemplateNotFoundError,
    LLMCallError,
    check_prompt_completeness,
    build_image_prompt,
    ImagePromptRequest,
    get_drawing_profile,
)


def test_completeness_report_fields():
    """CompletenessReport has all required fields."""
    report = CompletenessReport(
        can_generate=True,
        precision="一级精度",
        missing=["底图"],
        notices=["notice"],
        template_only=False,
        degraded=False,
    )
    assert report.can_generate is True
    assert report.precision == "一级精度"
    assert report.missing == ["底图"]
    assert report.template_only is False
    assert report.degraded is False


def test_prompt_engine_exceptions_hierarchy():
    """All prompt engine exceptions inherit from PromptEngineError."""
    assert issubclass(TemplateNotFoundError, PromptEngineError)
    assert issubclass(LLMCallError, PromptEngineError)
    assert issubclass(PromptEngineError, Exception)


def test_check_prompt_completeness_returns_report():
    """check_prompt_completeness returns a CompletenessReport."""
    request = ImagePromptRequest(
        chapter="01 项目认知篇",
        drawing_name="区位分析图",
        drawing_type="研究范围类",
        aspect_ratio="A3横版",
        output_scene="毕业设计图册",
        uploaded_channels=[],
        main_expression="区位分析",
    )
    report = check_prompt_completeness(request)
    assert isinstance(report, CompletenessReport)
    assert isinstance(report.missing, list)
    assert isinstance(report.notices, list)
    assert isinstance(report.template_only, bool)
    assert isinstance(report.degraded, bool)


def test_check_prompt_completeness_precision_levels():
    """Different precision levels produce different validation behavior."""
    request_1 = ImagePromptRequest(
        chapter="05 总体规划篇",
        drawing_name="总平面图",
        drawing_type="总体规划类",
        aspect_ratio="A3横版",
        output_scene="毕业设计图册",
        uploaded_channels=[],
        main_expression="总平面",
    )
    report_1 = check_prompt_completeness(request_1)
    assert report_1.precision == "一级精度"
    assert len(report_1.missing) > 0

    request_3 = ImagePromptRequest(
        chapter="07 技术推演与实施篇",
        drawing_name="封面",
        drawing_type="封面类",
        aspect_ratio="A3横版",
        output_scene="毕业设计图册",
        uploaded_channels=[],
        main_expression="封面设计",
    )
    report_3 = check_prompt_completeness(request_3)
    assert report_3.precision == "三级精度"
