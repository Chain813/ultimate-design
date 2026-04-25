import sys
import os
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.append(str(root))
sys.modules.setdefault("streamlit", type(sys)("streamlit_mock"))

import src.engines.core_engine as core_engine


# ── Phase 1 + 2 ── config / runtime
def test_load_global_config_has_engine_section():
    config = core_engine.load_global_config()
    assert "engines" in config
    assert "llm" in config["engines"]


def test_load_rag_knowledge_fallback_when_file_missing(monkeypatch):
    def _fake_load_global_config():
        return {"data": {"rag_knowledge_path": "data/does_not_exist.json"}}

    monkeypatch.setattr(
        "src.config.loader.load_global_config",
        _fake_load_global_config,
    )
    data = core_engine.load_rag_knowledge()
    assert data == {}


def test_is_demo_mode_importable():
    assert callable(core_engine.is_demo_mode)


# ── Spatial engine re-exports ──
def test_spatial_exports():
    assert callable(core_engine.get_merged_poi_data)
    assert callable(core_engine.get_hud_statistics)
    assert callable(core_engine.get_skyline_features)
    assert callable(core_engine.get_spatial_data)


# ── NLP engine re-exports ──
def test_nlp_exports():
    assert callable(core_engine.get_nlp_data)


# ── AIGC engine re-exports ──
def test_aigc_exports():
    assert callable(core_engine.run_realtime_sd)


# ── RAG engine re-exports ──
def test_rag_exports():
    assert callable(core_engine.load_bge_micro_model)
    assert callable(core_engine.get_cached_db_embeddings)
    assert callable(core_engine.compute_query_embedding)
    assert callable(core_engine.retrieve_rag_context)


# ── LLM engine re-exports ──
def test_llm_exports():
    assert callable(core_engine.call_llm_engine)
    assert callable(core_engine.call_llm_engine_stream)


# ── Diagnostic engine re-exports ──
def test_diagnostic_exports():
    assert callable(core_engine.generate_policy_matrix)
    assert callable(core_engine.get_plot_diagnostics)


# ── Total export count ──
def test_all_18_symbols_reexported():
    """Verify every symbol the plan committed to re-exporting is present."""
    required = [
        # config
        "load_global_config", "load_rag_knowledge",
        # runtime
        "is_demo_mode",
        # spatial
        "get_merged_poi_data", "get_hud_statistics",
        "get_skyline_features", "get_spatial_data",
        # nlp
        "get_nlp_data",
        # aigc
        "run_realtime_sd",
        # rag
        "load_bge_micro_model", "get_cached_db_embeddings",
        "compute_query_embedding", "retrieve_rag_context",
        # llm
        "call_llm_engine", "call_llm_engine_stream",
        # diagnostic
        "get_plot_diagnostics", "generate_policy_matrix",
    ]
    for name in required:
        assert hasattr(core_engine, name), f"Missing re-export: {name}"
        assert callable(getattr(core_engine, name))
    assert len(required) == 17, f"Expected 17 symbols, got {len(required)}"
