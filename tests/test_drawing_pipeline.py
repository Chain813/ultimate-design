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


# ============================================================
# DrawingPipeline tests (Task 5)
# ============================================================

from unittest.mock import patch, MagicMock
from PIL import Image


def _make_mock_sd_result():
    """Create a mock SDResult."""
    from src.engines.stable_diffusion_engine import SDResult
    return SDResult(
        images=[Image.new("RGB", (64, 64))],
        seed=12345,
        info={},
        elapsed_seconds=1.0,
    )


def test_pipeline_result_fields():
    """PipelineResult has all required fields."""
    from src.engines.drawing_pipeline import PipelineResult

    result = PipelineResult(
        template_name="区位分析图",
        success=True,
        prompt="test prompt",
        image=Image.new("RGB", (64, 64)),
    )
    assert result.template_name == "区位分析图"
    assert result.success is True
    assert result.error == ""


@patch("src.engines.drawing_pipeline.SDPipeline")
@patch("src.engines.drawing_pipeline.generate_drawing_prompt_with_llm")
@patch("src.engines.drawing_pipeline.build_drawing_prompt")
@patch("src.engines.drawing_pipeline.check_prompt_completeness")
@patch("src.engines.drawing_pipeline.get_drawing_profile")
def test_generate_single_auto_mode(mock_profile, mock_check, mock_build, mock_llm, mock_sd):
    """generate_single in auto mode runs full pipeline."""
    from src.engines.drawing_pipeline import DrawingPipeline, CompletenessReport

    mock_profile.return_value = MagicMock(
        precision="三级精度",
        drawing_type="封面类",
        name="封面",
        required_uploads=[],
    )
    mock_check.return_value = CompletenessReport(
        can_generate=True, precision="三级精度", missing=[], notices=[],
    )
    mock_build.return_value = ("test prompt", "system prompt")
    mock_llm.return_value = "final prompt"

    mock_sd_instance = MagicMock()
    mock_sd_instance.run.return_value = _make_mock_sd_result()

    pipeline = DrawingPipeline(sd_pipeline=mock_sd_instance)
    result = pipeline.generate_single("封面", mode="auto")

    assert result.success is True
    assert result.prompt == "final prompt"
    assert result.image is not None


@patch("src.engines.drawing_pipeline.get_drawing_profile")
def test_generate_single_blocks_on_missing_precision1(mock_profile):
    """generate_single blocks when 一级精度 has missing assets."""
    from src.engines.drawing_pipeline import DrawingPipeline

    mock_profile.return_value = MagicMock(
        precision="一级精度",
        drawing_type="总体规划类",
        name="总平面图",
        required_uploads=["卫星底图", "红线边界图"],
    )

    pipeline = DrawingPipeline()
    result = pipeline.generate_single("总平面图", mode="auto")

    assert result.success is False
    assert len(result.error) > 0


def test_generate_batch_multiple():
    """generate_batch processes multiple templates."""
    from src.engines.drawing_pipeline import DrawingPipeline

    pipeline = DrawingPipeline()
    pipeline.generate_single = MagicMock(side_effect=[
        MagicMock(success=True, template_name="t1"),
        MagicMock(success=False, template_name="t2", error="missing"),
    ])

    results = pipeline.generate_batch(["t1", "t2"], mode="auto")
    assert len(results) == 2
    assert results[0].success is True
    assert results[1].success is False


def test_generate_batch_progress_callback():
    """generate_batch calls on_progress for each template."""
    from src.engines.drawing_pipeline import DrawingPipeline

    pipeline = DrawingPipeline()
    pipeline.generate_single = MagicMock(return_value=MagicMock(success=True))

    progress_calls = []
    pipeline.generate_batch(
        ["t1", "t2", "t3"],
        mode="auto",
        on_progress=lambda **kw: progress_calls.append(kw),
    )
    assert len(progress_calls) == 3
