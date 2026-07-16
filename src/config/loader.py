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


import urllib.parse

@st.cache_resource
def load_global_config() -> dict:
    """Load config.yaml as a cached resource."""
    config = {}
    try:
        config_path = resolve_path("config/config.yaml")
        with config_path.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except Exception:
        logger.warning("config.yaml not found or invalid, returning empty config", exc_info=True)
        return {}

    # Validation and sanitization
    if "engines" in config and isinstance(config["engines"], dict):
        # Validate LLM settings
        llm = config["engines"].get("llm", {})
        if "api_url" in llm:
            parsed = urllib.parse.urlparse(llm["api_url"])
            if not all([parsed.scheme, parsed.netloc]):
                logger.warning(f"Invalid LLM API URL: {llm['api_url']}, falling back to DeepSeek.")
                llm["api_url"] = "https://api.deepseek.com/chat/completions"
        if "timeout" in llm:
            try:
                t = int(llm["timeout"])
                llm["timeout"] = max(10, min(t, 600))  # Clamp timeout between 10s and 10min
            except ValueError:
                llm["timeout"] = 120
    
    return config


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
