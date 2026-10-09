import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.append(str(root))
sys.modules.setdefault("streamlit", type(sys)("streamlit_mock"))

from src.engines.guideline_prompt import (
    GUIDELINE_CHAPTERS,
    build_expansion_prompt,
    build_guideline_prompt,
    build_outline_prompt,
    build_spatial_stats_summary,
    retrieve_policy_context,
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
    # Site name/city should come from config now (not hardcoded)
    assert "长春" in prompt or "测试市" in prompt


def test_build_spatial_stats_summary():
    """build_spatial_stats_summary formats stats correctly."""
    stats = {"boundary_ha": 150, "poi_count": 1200}
    skyline = {"building_count": 110289, "avg_height": 12.5}
    result = build_spatial_stats_summary(stats, skyline)
    assert "150" in result
    assert "110289" in result


def test_retrieve_policy_context_fallback(monkeypatch):
    """retrieve_policy_context returns empty string when RAG unavailable."""
    monkeypatch.setattr(
        "src.engines.rag_engine.retrieve_rag_context",
        lambda *args, **kwargs: [],
    )
    result = retrieve_policy_context("test query")
    assert isinstance(result, str)


def test_retrieve_policy_context_with_tuples(monkeypatch):
    """retrieve_policy_context correctly unpacks (text, metadata) and (score, text, source) tuples."""
    mock_results = [
        ("保护区限高 12 米，严控建筑体量", {"source": "长春市历史文化名城保护条例"}),
        (0.85, "严禁破坏既有历史街区肌理", "国家历史名城保护规定"),
    ]
    monkeypatch.setattr(
        "src.engines.rag_engine.retrieve_rag_context",
        lambda *args, **kwargs: mock_results,
    )
    result = retrieve_policy_context("历史保护")
    assert "长春市历史文化名城保护条例" in result
    assert "保护区限高 12 米" in result
    assert "国家历史名城保护规定" in result
    assert "严禁破坏既有历史街区肌理" in result


def test_retrieve_policy_context_with_dicts(monkeypatch):
    """retrieve_policy_context correctly unpacks dict items."""
    mock_results = [
        {"content": "微更新原则：小规模、渐进式", "source": "城市更新指导意见"},
    ]
    monkeypatch.setattr(
        "src.engines.rag_engine.retrieve_rag_context",
        lambda *args, **kwargs: mock_results,
    )
    result = retrieve_policy_context("微更新")
    assert "城市更新指导意见" in result
    assert "小规模、渐进式" in result

