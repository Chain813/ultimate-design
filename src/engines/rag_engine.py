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
        from src.config.loader import load_global_config
        hf_mirror = load_global_config().get("engines", {}).get("hf_mirror", "")
        if hf_mirror:
            os.environ["HF_ENDPOINT"] = hf_mirror
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

    # 1. 尝试从本地持久化缓存读取
    import hashlib
    import pickle
    from src.config.loader import load_global_config
    from src.config.runtime import resolve_path

    config = load_global_config()
    rag_path_key = config.get("data", {}).get("rag_knowledge_path", "data/rag_knowledge.json")
    rag_path = resolve_path(rag_path_key)

    rag_hash = ""
    if rag_path.exists():
        try:
            with open(rag_path, "rb") as f:
                rag_hash = hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.warning("Failed to compute md5 of RAG knowledge file: %s", e)

    cache_path = resolve_path("data/rag_embeddings_cache.pkl")

    if cache_path.exists() and rag_hash:
        try:
            with open(cache_path, "rb") as f:
                cache_data = pickle.load(f)
            if cache_data.get("hash") == rag_hash:
                logger.info("Loaded RAG embeddings from persistent cache: %s", cache_path)
                return cache_data["embeddings"], rag_db
        except Exception as e:
            logger.warning("Failed to load RAG embeddings cache, will re-compute: %s", e)

    # 2. 缓存未命中时进行重计算
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

    # 3. 将计算结果持久化写入本地缓存文件
    if rag_hash:
        try:
            cache_data = {
                "hash": rag_hash,
                "embeddings": db_embeddings
            }
            with open(cache_path, "wb") as f:
                pickle.dump(cache_data, f)
            logger.info("Saved RAG embeddings to persistent cache: %s", cache_path)
        except Exception as e:
            logger.warning("Failed to save RAG embeddings cache: %s", e)

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


@st.cache_data(ttl=600)
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
        for _cid, p_info in rag_db.items():
            content = p_info["content"]
            score = sum(1 for w in words if w in content)
            if score > 0:
                best_chunks.append((score, content, p_info["source"]))

    best_chunks.sort(key=lambda x: x[0], reverse=True)
    return best_chunks[:top_k]
