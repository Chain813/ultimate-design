"""RAG vector-search engine: BGE embedding + Jieba fallback.

Usage:
    from src.engines.rag_engine import (
        load_bge_micro_model, get_cached_db_embeddings,
        compute_query_embedding, retrieve_rag_context,
    )
"""

import logging
import os

import jieba
import numpy as np
import streamlit as st

from src.config.loader import load_rag_knowledge

logger = logging.getLogger("ultimateDESIGN")


@st.cache_resource
def load_bge_micro_model():
    """Lazily load BAAI/bge-micro-zh-v4 for vector retrieval."""
    try:
        from transformers import AutoTokenizer, AutoModel
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-micro-zh-v4")
        model = AutoModel.from_pretrained("BAAI/bge-micro-zh-v4")
        model.eval()
        return tokenizer, model
    except Exception:
        logger.warning("BGE-Micro model load failed, will use Jieba fallback", exc_info=True)
        return None, None


@st.cache_resource
def get_cached_db_embeddings():
    """Pre-compute and cache vector embeddings for all RAG chunks."""
    rag_db = load_rag_knowledge()
    if not rag_db:
        return {}, rag_db

    tokenizer, model = load_bge_micro_model()
    if not tokenizer or not model:
        return {}, rag_db

    import torch
    db_embeddings = {}
    for cid, p_info in rag_db.items():
        content = p_info["content"]
        inputs = tokenizer(content, padding=True, truncation=True, return_tensors="pt", max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
            emb = outputs[0][:, 0]
        emb = torch.nn.functional.normalize(emb, p=2, dim=1).numpy()[0]
        db_embeddings[cid] = emb
    return db_embeddings, rag_db


def compute_query_embedding(prompt: str):
    """Embed a query string with the BGE model."""
    tokenizer, model = load_bge_micro_model()
    if not tokenizer or not model:
        return None
    import torch
    inputs = tokenizer(prompt, padding=True, truncation=True, return_tensors="pt", max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        emb = outputs[0][:, 0]
    emb = torch.nn.functional.normalize(emb, p=2, dim=1).numpy()[0]
    return emb


def retrieve_rag_context(query: str, top_k: int = 3) -> list:
    """Retrieve top-k most relevant regulation chunks for a query.

    Returns list of (score, content, source) tuples.
    """
    rag_db = load_rag_knowledge()
    if not rag_db:
        return []

    db_embeddings, _ = get_cached_db_embeddings()
    best_chunks: list = []

    if db_embeddings:
        query_emb = compute_query_embedding(query)
        if query_emb is not None:
            for cid, p_info in rag_db.items():
                if cid in db_embeddings:
                    score = float(np.dot(query_emb, db_embeddings[cid]))
                    best_chunks.append((score, p_info["content"], p_info["source"]))

    if not best_chunks:
        words = [w for w in jieba.cut(query) if len(w) > 1]
        for cid, p_info in rag_db.items():
            content = p_info["content"]
            score = sum(1 for w in words if w in content)
            if score > 0:
                best_chunks.append((score, content, p_info["source"]))

    best_chunks.sort(key=lambda x: x[0], reverse=True)
    return best_chunks[:top_k]
