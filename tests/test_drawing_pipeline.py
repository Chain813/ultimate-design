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


from src.workflow.template_assets import save_template_asset
import pytest


def test_save_template_asset_rejects_invalid_type(tmp_path):
    """save_template_asset rejects files not in accepted_types."""
    manifest_path = tmp_path / "manifest.json"
    asset_dir = tmp_path / "assets"

    with pytest.raises(ValueError, match="not accepted"):
        save_template_asset(
            asset_id="fixed_base_map",
            original_name="test.txt",
            content=b"fake content",
            asset_dir=asset_dir,
            manifest_path=manifest_path,
        )


def test_save_template_asset_accepts_valid_type(tmp_path):
    """save_template_asset accepts files matching accepted_types."""
    manifest_path = tmp_path / "manifest.json"
    asset_dir = tmp_path / "assets"

    from PIL import Image
    import io
    img = Image.new("RGB", (10, 10))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    entry = save_template_asset(
        asset_id="fixed_base_map",
        original_name="test.png",
        content=png_bytes,
        asset_dir=asset_dir,
        manifest_path=manifest_path,
    )
    assert entry["asset_id"] == "fixed_base_map"


from src.engines.drawing_prompt_templates import (
    get_or_create_template,
    generate_drawing_prompt_with_llm,
    build_drawing_prompt,
)


def test_get_or_create_template_existing():
    """get_or_create_template returns existing template."""
    tmpl = get_or_create_template("区位分析图")
    assert tmpl is not None
    assert tmpl.name == "区位分析图"


def test_get_or_create_template_generic():
    """get_or_create_template generates generic template for missing drawings."""
    tmpl = get_or_create_template("封面设计图")
    assert tmpl is not None
    assert "封面设计图" in tmpl.name


def test_build_drawing_prompt_missing_template():
    """build_drawing_prompt returns empty for non-existent template."""
    prompt, sys_prompt = build_drawing_prompt("不存在的图纸XYZ")
    assert prompt == ""
    assert sys_prompt == ""
