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
