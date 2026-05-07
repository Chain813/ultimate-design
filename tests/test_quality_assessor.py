import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.append(str(root))
sys.modules.setdefault("streamlit", type(sys)("streamlit_mock"))

from src.engines.quality_assessor import (
    QualityAssessor,
    QualityReport,
    VisualScore,
    ContentScore,
)


def test_visual_score_fields():
    score = VisualScore(score=7.5, description="清晰的图纸", issues=["文字偏小"])
    assert score.score == 7.5
    assert score.description == "清晰的图纸"
    assert "文字偏小" in score.issues


def test_content_score_fields():
    score = ContentScore(score=8.0, issues=["边界偏差"], suggestions=["修正边界"])
    assert score.score == 8.0


def test_quality_report_fields():
    report = QualityReport(
        rating="B",
        visual_score=7.0,
        content_score=8.0,
        combined_score=7.5,
        issue_types=["文字乱码"],
        suggestions=["减少文字"],
        raw_visual="原始视觉输出",
        raw_content="原始内容输出",
    )
    assert report.rating == "B"
    assert report.combined_score == 7.5


def test_rating_thresholds():
    assessor = QualityAssessor.__new__(QualityAssessor)
    assert assessor._score_to_rating(9.0) == "A"
    assert assessor._score_to_rating(7.0) == "B"
    assert assessor._score_to_rating(5.0) == "C"
    assert assessor._score_to_rating(3.0) == "D"


@patch("src.engines.quality_assessor.requests")
@patch("src.engines.quality_assessor.torch")
def test_auto_select_vision_model_8gb(mock_torch, mock_requests):
    mock_torch.cuda.is_available.return_value = True
    mock_torch.cuda.get_device_properties.return_value = MagicMock(
        total_mem=8 * 1024**3
    )
    mock_requests.get.return_value = MagicMock(
        json=lambda: {"models": [{"name": "gemma3:4b"}]}
    )
    assessor = QualityAssessor.__new__(QualityAssessor)
    assessor.ollama_url = "http://127.0.0.1:11434"
    model = assessor._auto_select_vision_model()
    assert model == "gemma3:4b"


@patch("src.engines.quality_assessor.requests")
@patch("src.engines.quality_assessor.torch")
def test_auto_select_vision_model_16gb(mock_torch, mock_requests):
    mock_torch.cuda.is_available.return_value = True
    mock_torch.cuda.get_device_properties.return_value = MagicMock(
        total_mem=16 * 1024**3
    )
    mock_requests.get.return_value = MagicMock(
        json=lambda: {"models": [{"name": "gemma3:12b"}]}
    )
    assessor = QualityAssessor.__new__(QualityAssessor)
    assessor.ollama_url = "http://127.0.0.1:11434"
    model = assessor._auto_select_vision_model()
    assert model == "gemma3:12b"


def test_detect_vram_fallback():
    assessor = QualityAssessor.__new__(QualityAssessor)
    with patch("src.engines.quality_assessor.torch", side_effect=ImportError):
        vram = assessor._detect_vram()
    assert vram == 4


from PIL import Image


@patch("src.engines.quality_assessor.requests.post")
def test_visual_assessment_calls_ollama(mock_post):
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "response": '{"score": 8, "description": "清晰的规划图", "issues": []}'
        },
    )
    assessor = QualityAssessor.__new__(QualityAssessor)
    assessor.ollama_url = "http://127.0.0.1:11434"
    assessor.vision_model = "gemma3:4b"

    img = Image.new("RGB", (64, 64))
    result = assessor._visual_assessment(img, "区位分析图")

    assert result.score == 8.0
    assert "清晰" in result.description
    mock_post.assert_called_once()


@patch("src.engines.quality_assessor.requests.post")
def test_visual_assessment_handles_failure(mock_post):
    mock_post.side_effect = Exception("connection refused")
    assessor = QualityAssessor.__new__(QualityAssessor)
    assessor.ollama_url = "http://127.0.0.1:11434"
    assessor.vision_model = "gemma3:4b"

    img = Image.new("RGB", (64, 64))
    result = assessor._visual_assessment(img, "test")

    assert result.score == 5.0
    assert "不可用" in result.issues[0]


@patch("src.engines.quality_assessor.requests.post")
def test_assess_full_pipeline(mock_post):
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "response": '{"score": 7, "description": "规划图", "issues": ["文字偏小"]}'
        },
    )

    assessor = QualityAssessor.__new__(QualityAssessor)
    assessor.ollama_url = "http://127.0.0.1:11434"
    assessor.vision_model = "gemma3:4b"
    assessor.text_model = "deepseek-v4-pro"

    with patch("src.engines.llm_engine.call_llm_engine") as mock_llm:
        mock_llm.return_value = '{"score": 8, "issues": [], "suggestions": ["保持风格"]}'
        img = Image.new("RGB", (64, 64))
        report = assessor.assess(img, "生成区位分析图", "区位分析图")

    assert report.rating in ("A", "B", "C", "D")
    assert report.visual_score > 0
    assert report.content_score > 0
    assert report.combined_score > 0


from src.engines.drawing_pipeline import DrawingPipeline, PipelineResult


@patch("src.engines.drawing_pipeline.QualityAssessor")
@patch("src.engines.drawing_pipeline.revise_prompt_by_rating")
def test_quality_loop_passes_on_a_rating(mock_revise, mock_assessor_cls):
    mock_assessor = MagicMock()
    mock_assessor.assess.return_value = MagicMock(rating="A")
    mock_assessor_cls.return_value = mock_assessor

    pipeline = DrawingPipeline()
    pipeline.generate_single = MagicMock(return_value=PipelineResult(
        template_name="t1", success=True, prompt="p", image=Image.new("RGB", (64, 64)),
    ))

    result = pipeline.generate_with_quality_loop("t1", max_retries=2)
    assert result.success is True
    assert result.quality_report is not None
    mock_revise.assert_not_called()


@patch("src.engines.drawing_pipeline.QualityAssessor")
@patch("src.engines.drawing_pipeline.revise_prompt_by_rating")
def test_quality_loop_retries_on_c_rating(mock_revise, mock_assessor_cls):
    mock_assessor = MagicMock()
    mock_assessor.assess.side_effect = [
        MagicMock(rating="C", issue_types=["文字乱码"]),
        MagicMock(rating="A"),
    ]
    mock_assessor_cls.return_value = mock_assessor
    mock_revise.return_value = "revised prompt"

    pipeline = DrawingPipeline()
    pipeline.generate_single = MagicMock(return_value=PipelineResult(
        template_name="t1", success=True, prompt="p", image=Image.new("RGB", (64, 64)),
    ))
    pipeline.render_only = MagicMock(return_value=PipelineResult(
        template_name="t1", success=True, prompt="revised", image=Image.new("RGB", (64, 64)),
    ))

    result = pipeline.generate_with_quality_loop("t1", max_retries=2)
    assert result.success is True
    assert mock_revise.call_count == 1


@patch("src.engines.drawing_pipeline.QualityAssessor")
@patch("src.engines.drawing_pipeline.revise_prompt_by_rating")
def test_quality_loop_max_retries(mock_revise, mock_assessor_cls):
    mock_assessor = MagicMock()
    mock_assessor.assess.return_value = MagicMock(rating="D", issue_types=["严重问题"])
    mock_assessor_cls.return_value = mock_assessor
    mock_revise.return_value = "revised"

    pipeline = DrawingPipeline()
    pipeline.generate_single = MagicMock(return_value=PipelineResult(
        template_name="t1", success=True, prompt="p", image=Image.new("RGB", (64, 64)),
    ))
    pipeline.render_only = MagicMock(return_value=PipelineResult(
        template_name="t1", success=True, prompt="revised", image=Image.new("RGB", (64, 64)),
    ))

    result = pipeline.generate_with_quality_loop("t1", max_retries=2)
    assert mock_assessor.assess.call_count == 3
