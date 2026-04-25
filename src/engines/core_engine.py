"""Backward-compatible re-export hub.

Prefer importing from the dedicated domain modules directly in new code.
All symbols below remain available for existing page imports.
"""

# Config / runtime
from src.config.loader import load_global_config, load_rag_knowledge
from src.utils.runtime_flags import is_demo_mode

# Spatial & HUD
from src.engines.spatial_engine import (
    get_hud_statistics,
    get_merged_poi_data,
    get_skyline_features,
    get_spatial_data,
)

# NLP
from src.engines.nlp_engine import get_nlp_data

# AIGC
from src.engines.aigc_engine import run_realtime_sd

# RAG
from src.engines.rag_engine import (
    compute_query_embedding,
    get_cached_db_embeddings,
    load_bge_micro_model,
    retrieve_rag_context,
)

# LLM
from src.engines.llm_engine import call_llm_engine, call_llm_engine_stream

# Diagnostics & policy
from src.engines.diagnostic_engine import generate_policy_matrix, get_plot_diagnostics

__all__ = [
    "load_global_config",
    "load_rag_knowledge",
    "is_demo_mode",
    "get_hud_statistics",
    "get_merged_poi_data",
    "get_skyline_features",
    "get_spatial_data",
    "get_nlp_data",
    "run_realtime_sd",
    "compute_query_embedding",
    "get_cached_db_embeddings",
    "load_bge_micro_model",
    "retrieve_rag_context",
    "call_llm_engine",
    "call_llm_engine_stream",
    "generate_policy_matrix",
    "get_plot_diagnostics",
]
