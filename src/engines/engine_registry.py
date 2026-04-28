"""Stable import registry for cross-domain engines.

Pages should prefer importing from the concrete engine modules when they only
need one domain. This registry is kept for page code that intentionally depends
on several domains at once.
"""

from src.config.loader import load_global_config, load_rag_knowledge
from src.engines.llm_engine import call_llm_engine, call_llm_engine_stream
from src.engines.nlp_engine import get_nlp_data
from src.engines.rag_engine import (
    compute_query_embedding,
    get_cached_db_embeddings,
    load_bge_micro_model,
    retrieve_rag_context,
)
from src.engines.site_diagnostic_engine import generate_policy_matrix, get_plot_diagnostics
from src.engines.spatial_engine import (
    get_hud_statistics,
    get_merged_poi_data,
    get_skyline_features,
    get_spatial_data,
)
from src.engines.stable_diffusion_engine import run_realtime_sd
from src.utils.runtime_flags import is_demo_mode

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
