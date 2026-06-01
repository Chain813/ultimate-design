"""Stable import registry for cross-domain engines.

Pages should prefer importing from the concrete engine modules when they only
need one domain. This registry is kept for page code that intentionally depends
on several domains at once.

Uses lazy imports to avoid loading heavy dependencies (pandas, numpy, PIL, jieba,
requests, torch) at module import time. Each symbol is resolved on first access.
"""

from importlib import import_module

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
    "SDPipeline",
    "SDResult",
    "QualityAssessor",
    "DrawingPipeline",
    "PipelineResult",
    "VersionStore",
    "BatchExporter",
    "ExportReport",
    "build_guideline_prompt",
    "build_outline_prompt",
    "build_expansion_prompt",
    "compute_query_embedding",
    "get_cached_db_embeddings",
    "load_bge_micro_model",
    "retrieve_rag_context",
    "call_llm_engine",
    "call_llm_engine_stream",
    "generate_policy_matrix",
    "get_plot_diagnostics",
]

# Map each symbol to its source module
_LAZY_IMPORTS = {
    "load_global_config": "src.config.loader",
    "load_rag_knowledge": "src.config.loader",
    "is_demo_mode": "src.utils.runtime_flags",
    "get_hud_statistics": "src.engines.spatial_engine",
    "get_merged_poi_data": "src.engines.spatial_engine",
    "get_skyline_features": "src.engines.spatial_engine",
    "get_spatial_data": "src.engines.spatial_engine",
    "get_nlp_data": "src.engines.nlp_engine",
    "run_realtime_sd": "src.engines.stable_diffusion_engine",
    "SDPipeline": "src.engines.stable_diffusion_engine",
    "SDResult": "src.engines.stable_diffusion_engine",
    "QualityAssessor": "src.engines.quality_assessor",
    "DrawingPipeline": "src.engines.drawing_pipeline",
    "PipelineResult": "src.engines.drawing_pipeline",
    "VersionStore": "src.engines.version_store",
    "BatchExporter": "src.engines.batch_exporter",
    "ExportReport": "src.engines.batch_exporter",
    "build_guideline_prompt": "src.engines.guideline_prompt",
    "build_outline_prompt": "src.engines.guideline_prompt",
    "build_expansion_prompt": "src.engines.guideline_prompt",
    "compute_query_embedding": "src.engines.rag_engine",
    "get_cached_db_embeddings": "src.engines.rag_engine",
    "load_bge_micro_model": "src.engines.rag_engine",
    "retrieve_rag_context": "src.engines.rag_engine",
    "call_llm_engine": "src.engines.llm_engine",
    "call_llm_engine_stream": "src.engines.llm_engine",
    "generate_policy_matrix": "src.engines.site_diagnostic_engine",
    "get_plot_diagnostics": "src.engines.site_diagnostic_engine",
}


def __getattr__(name):
    if name in _LAZY_IMPORTS:
        module = import_module(_LAZY_IMPORTS[name])
        return getattr(module, name)
    raise AttributeError(f"module 'src.engines' has no attribute {name!r}")
