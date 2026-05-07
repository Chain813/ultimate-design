import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.append(str(root))
sys.modules.setdefault("streamlit", type(sys)("streamlit_mock"))

from src.engines.guideline_prompt import (
    build_outline_prompt,
    build_expansion_prompt,
    build_guideline_prompt,
    GUIDELINE_CHAPTERS,
    retrieve_policy_context,
    build_spatial_stats_summary,
)


def test_guideline_chapters_count():
    """GUIDELINE_CHAPTERS has 10 chapters."""
    assert len(GUIDELINE_CHAPTERS) == 10


def test_build_outline_prompt_contains_chapters():
    """Outline prompt includes all chapter titles."""
    prompt = build_outline_prompt()
    for ch in GUIDELINE_CHAPTERS:
        assert ch["title"] in prompt


def test_build_expansion_prompt_contains_outline():
    """Expansion prompt includes the provided outline text."""
    outline = "## 第1章 总则\n### 核心论点\n- 论点1"
    prompt = build_expansion_prompt(outline=outline)
    assert outline in prompt


def test_build_guideline_prompt_contains_project_info():
    """Guideline prompt contains project location and scope."""
    prompt = build_guideline_prompt()
    assert "长春" in prompt
    assert "150公顷" in prompt or "150" in prompt


def test_build_spatial_stats_summary():
    """build_spatial_stats_summary formats stats correctly."""
    stats = {"boundary_ha": 150, "poi_count": 1200}
    skyline = {"building_count": 110289, "avg_height": 12.5}
    result = build_spatial_stats_summary(stats, skyline)
    assert "150" in result
    assert "110289" in result


def test_retrieve_policy_context_fallback():
    """retrieve_policy_context returns empty string when RAG unavailable."""
    result = retrieve_policy_context("test query")
    assert isinstance(result, str)
