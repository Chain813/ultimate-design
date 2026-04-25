import sys
sys.modules.setdefault("streamlit", type(sys)("streamlit_mock"))

import pytest
from src.engines.rag_engine import compute_query_embedding


def test_compute_query_embedding_returns_none_when_model_unavailable():
    """Without transformers installed, should return None gracefully."""
    result = compute_query_embedding("测试查询文本")
    assert result is None


def test_retrieve_rag_context_empty_db(monkeypatch):
    from src.engines.rag_engine import retrieve_rag_context

    monkeypatch.setattr(
        "src.engines.rag_engine.load_rag_knowledge",
        lambda: {},
    )
    result = retrieve_rag_context("容积率", top_k=3)
    assert result == []


def test_retrieve_rag_context_jieba_fallback(monkeypatch):
    """When no BGE model, fall back to Jieba keyword matching."""
    from src.engines.rag_engine import retrieve_rag_context

    fake_db = {
        "1": {"content": "容积率不得低于2.0", "source": "长春市控规"},
        "2": {"content": "建筑高度不超过12米", "source": "保护条例"},
    }

    monkeypatch.setattr(
        "src.engines.rag_engine.load_rag_knowledge",
        lambda: fake_db,
    )
    monkeypatch.setattr(
        "src.engines.rag_engine.get_cached_db_embeddings",
        lambda: ({}, fake_db),
    )

    result = retrieve_rag_context("容积率红线", top_k=2)
    assert len(result) >= 1
    assert any("容积率" in chunk[1] for chunk in result)


def test_retrieve_rag_context_top_k_truncation(monkeypatch):
    from src.engines.rag_engine import retrieve_rag_context

    fake_db = {
        str(i): {"content": f"法规条款第{i}条", "source": f"文件{i}"}
        for i in range(10)
    }

    monkeypatch.setattr(
        "src.engines.rag_engine.load_rag_knowledge",
        lambda: fake_db,
    )
    monkeypatch.setattr(
        "src.engines.rag_engine.get_cached_db_embeddings",
        lambda: ({}, fake_db),
    )

    result = retrieve_rag_context("法规", top_k=3)
    assert len(result) <= 3


def test_load_bge_model_fallback(monkeypatch):
    """When transformers unavailable, returns (None, None)."""
    from src.engines.rag_engine import load_bge_micro_model

    monkeypatch.setitem(sys.modules, "transformers", None)
    tokenizer, model = load_bge_micro_model()
    # Without transformers, will fall back
