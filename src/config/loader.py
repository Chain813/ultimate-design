"""Global configuration and RAG-knowledge loaders.

Usage:
    from src.config.loader import load_global_config, load_rag_knowledge
"""

import json
import logging

import streamlit as st
import yaml

from src.config.runtime import resolve_path

logger = logging.getLogger("ultimateDESIGN")


@st.cache_resource
def load_global_config() -> dict:
    """Load config.yaml as a cached resource."""
    try:
        config_path = resolve_path("config.yaml")
        with config_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        logger.warning("config.yaml not found, returning empty config", exc_info=True)
        return {}


@st.cache_resource
def load_rag_knowledge() -> dict:
    """Load the RAG knowledge base JSON as a cached resource."""
    config = load_global_config()
    rag_path_key = config.get("data", {}).get("rag_knowledge_path", "data/rag_knowledge.json")
    try:
        rag_path = resolve_path(rag_path_key)
        with rag_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.warning("RAG knowledge file not found: %s", rag_path_key, exc_info=True)
        return {}
