"""Background cache preloader —— 在用户浏览当前页面时，静默预热其他页面的缓存数据。

使用 daemon 线程在后台执行，不阻塞主页面渲染。通过 session state 确保每个会话只预热一次。

Usage:
    from src.utils.preloader import start_preloading
    start_preloading()  # 在 app.py 顶部调用
"""

import logging
import os
import threading
import streamlit as st

logger = logging.getLogger("ultimateDESIGN")

_preload_lock = threading.Lock()


def _warm(name: str, fn, *args, **kwargs):
    """安全调用一个缓存函数，捕获异常不影响主流程。"""
    try:
        fn(*args, **kwargs)
        logger.debug("Preloaded: %s", name)
    except Exception:
        logger.debug("Preload failed (non-fatal): %s", name, exc_info=True)


def is_heavy_preload_enabled() -> bool:
    """Return True only when local/demo runs explicitly opt into heavy warming."""
    return os.getenv("UP_ENABLE_HEAVY_PRELOAD", "").strip().lower() in {"1", "true", "yes", "on"}


def _preload_light():
    """Lightweight startup warming safe for Streamlit Cloud cold starts."""
    from src.config.loader import load_global_config
    from src.engines.spatial_engine import get_hud_statistics

    _warm("load_global_config", load_global_config)
    _warm("get_hud_statistics", get_hud_statistics)


def _preload_tier1():
    """Tier 1: 最高优先级 —— 大文件 GeoJSON 和模型加载。"""
    from src.engines.spatial_engine import get_skyline_features, get_merged_poi_data
    from src.engines.spatial_data_injector import get_landuse_summary
    from src.engines.site_diagnostic_engine import get_plot_diagnostics

    _warm("get_merged_poi_data", get_merged_poi_data)
    _warm("get_skyline_features", get_skyline_features)
    _warm("get_landuse_summary", get_landuse_summary)
    _warm("get_plot_diagnostics", get_plot_diagnostics)


def _preload_tier2():
    """Tier 2: 中优先级 —— 聚合统计和 RAG 模型。"""
    from src.engines.spatial_engine import get_hud_statistics
    from src.engines.spatial_data_injector import (
        get_key_plots_summary,
        get_building_summary,
        get_poi_summary,
        get_gvi_summary,
    )
    from src.config.loader import load_global_config, load_rag_knowledge

    _warm("load_global_config", load_global_config)
    _warm("load_rag_knowledge", load_rag_knowledge)
    _warm("get_hud_statistics", get_hud_statistics)
    _warm("get_key_plots_summary", get_key_plots_summary)
    _warm("get_building_summary", get_building_summary)
    _warm("get_poi_summary", get_poi_summary)
    _warm("get_gvi_summary", get_gvi_summary)


def _preload_tier3():
    """Tier 3: RAG 嵌入模型（最重，放最后）。"""
    from src.engines.rag_engine import load_bge_micro_model, get_cached_db_embeddings

    _warm("load_bge_micro_model", load_bge_micro_model)
    _warm("get_cached_db_embeddings", get_cached_db_embeddings)


def _run_preload():
    """Run lightweight preloading by default; heavy tiers are opt-in."""
    _preload_light()
    if not is_heavy_preload_enabled():
        logger.info("Heavy cache preloading skipped. Set UP_ENABLE_HEAVY_PRELOAD=1 to enable it.")
        return

    _preload_tier1()
    _preload_tier2()
    _preload_tier3()
    logger.info("Cache preloading complete.")


def start_preloading():
    """启动后台预热线程。每个 session 只执行一次。"""
    if st.session_state.get("_preloader_started"):
        return
    st.session_state["_preloader_started"] = True

    thread = threading.Thread(target=_run_preload, daemon=True, name="cache-preloader")
    thread.start()
    logger.info("Cache preloader started in background thread.")
