"""RAG hybrid retrieval engine: BGE dense embedding + FastDense fallback + Precomputed BM25 + Scope-Aware RRF.

Upgraded with industrial hybrid retrieval strategies from 408-helper/backend/rag_service.py:
  1. Urban planning synonym query expansion (URBAN_QUERY_EXPANSION_RULES)
  2. Jieba + Chinese stopword filtering + intra-clause Chinese bi-grams (tokenize_text)
  3. Precomputed O(1) inverted index (cid, tf) + dynamic avgdl + IDF-weighted BM25 (_bm25_search)
  4. Metadata scope classification (national, city_statute, case_thesis, project_custom)
  5. Cross-city pollution prevention (excludes Changchun thesis in non-Changchun mode, labels cross-city statutes)
  6. Cross-scoring semantic reranker (_semantic_rerank) + U-shaped attention packing (_u_shaped_packing)
  7. Custom project document ingestion (add_custom_document)

Usage:
    from src.engines.rag_engine import (
        load_bge_micro_model, get_cached_db_embeddings,
        compute_query_embedding, retrieve_rag_context,
        classify_chunk_scope, add_custom_document,
    )
"""

from collections import Counter, defaultdict
import hashlib
import json
import logging
import math
import os
import pickle
import re
import tempfile
import threading
from typing import Any, Dict, List, Optional, Tuple

import jieba
import numpy as np
import streamlit as st

from src.config.loader import load_global_config, load_rag_knowledge
from src.config.runtime import resolve_path
from src.engines.contextual_chunker import (
    AcademicContextualChunker,
    clean_pdf_noise,
    recursive_character_chunking,
)

logger = logging.getLogger("ultimateDESIGN")

CUSTOM_RAG_REL_PATH = "data/custom_site/custom_rag_knowledge.json"

# ─────────────────────────────────────────────────────────────
# 0. 中文通用停用词表与城乡规划专业同义词扩展表
# ─────────────────────────────────────────────────────────────
CHINESE_STOPWORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
    "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
    "自己", "这", "那", "对于", "关于", "以及", "通过", "进行", "可以", "能够", "由",
    "因此", "所以", "如果", "但是", "然而", "或者", "因为", "由于", "从而", "虽然",
    "，", "。", "、", "【", "】", "（", "）", "：", "；", "！", "？", "\n", "\r", "\t", " ",
}

URBAN_QUERY_EXPANSION_RULES: Dict[str, List[str]] = {
    "far": ["容积率", "开发强度", "计容建筑面积"],
    "容积率": ["开发强度", "建筑密度", "控制性详细规划"],
    "tod": ["公共交通导向开发", "站点周边开发", "轨道交通站点"],
    "gvi": ["绿视率", "街道绿化", "沿街绿化"],
    "绿视率": ["街道绿化", "口袋公园", "绿地率"],
    "svf": ["天空开敞度", "天空可视率", "空间压迫感"],
    "mpi": ["综合更新潜力", "多源感知指数", "更新优先级"],
    "poi": ["兴趣点", "商业业态", "公共服务设施"],
    "留改拆": ["保护保留", "修缮改造", "拆除新建", "微更新"],
    "控规": ["控制性详细规划", "容积率", "建筑密度", "绿地率", "建筑限高"],
    "限高": ["建筑高度", "核心保护区", "建设控制地带", "风貌协调区", "视线通廊", "天际线"],
    "历史街区": ["历史文化街区", "核心保护范围", "建设控制地带", "风貌协调区", "历史建筑"],
    "视廊": ["视线通廊", "天际线", "高度控制", "风貌管控"],
    "微更新": ["渐进式更新", "社区针灸", "存量提质", "口袋公园"],
    "海绵城市": ["雨水花园", "透水铺装", "下凹式绿地", "径流控制"],
}

# 向后兼容别名
QUERY_EXPANSION_RULES = URBAN_QUERY_EXPANSION_RULES


def expand_query_terms(query: str) -> str:
    """对规划检索查询进行专业同义词与规范术语扩展。"""
    if not query:
        return ""
    expanded_parts = [query]
    q_lower = query.lower()
    for term, expansions in URBAN_QUERY_EXPANSION_RULES.items():
        if term in q_lower or term.upper() in query:
            expanded_parts.extend(expansions)
    return " ".join(expanded_parts)


# ─────────────────────────────────────────────────────────────
# 1. 工业级中文分词与停用词过滤 (Jieba + Stopwords + Intra-clause Bi-grams)
# ─────────────────────────────────────────────────────────────
def tokenize_text(text: str, filter_stopwords: bool = True) -> List[str]:
    """高质量中英文分词 (Jieba 精确模式 + 停用词过滤 + 句内汉字 Bi-gram 专名增强)。"""
    if not text:
        return []
    raw_tokens = [w.lower().strip() for w in jieba.cut(text) if len(w.strip()) > 0]
    if filter_stopwords:
        tokens = [t for t in raw_tokens if t not in CHINESE_STOPWORDS and len(t) > 0]
    else:
        tokens = raw_tokens

    # 汉字 bi-gram 补充增强（提高复合词与专有名词召回率，仅在句内断句生成）
    clean_text = text.lower()
    clauses = re.split(r"[，。！？；：\n\r\t、\(\)（）\[\]【】《》“”\"'/\\—\-_]", clean_text)
    for clause in clauses:
        chars = re.findall(r"[\u4e00-\u9fa5]", clause)
        for i in range(len(chars) - 1):
            bg = chars[i] + chars[i + 1]
            if not filter_stopwords or bg not in CHINESE_STOPWORDS:
                tokens.append(bg)
    return tokens


# ─────────────────────────────────────────────────────────────
# 2. 本地高维稠密特征投影向量引擎 (BGE 离线时的无损兜底)
# ─────────────────────────────────────────────────────────────
class FastDenseEmbeddingFunction:
    """
    本地高维稠密特征投影向量引擎 (默认 Dimension: 384，与 bge-micro-zh-v4 同维)
    采用中英文多粒度子空间正交投影 + 局部语义位置权重衰减 + L2 范数归一化。
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def __call__(self, texts: List[str]) -> List[np.ndarray]:
        embeddings: List[np.ndarray] = []
        dim = self.dimension
        for doc in texts:
            vec = [0.0] * dim
            tokens = tokenize_text(doc, filter_stopwords=True)
            if tokens:
                for pos, token in enumerate(tokens):
                    pos_weight = 1.0 + 0.5 * math.exp(-pos / 30.0)
                    h1 = int(hashlib.sha256((token + "_w1").encode("utf-8")).hexdigest()[:8], 16)
                    h2 = int(hashlib.sha256((token + "_w2").encode("utf-8")).hexdigest()[:8], 16)
                    h3 = int(hashlib.sha256((token + "_w3").encode("utf-8")).hexdigest()[:8], 16)
                    h4 = int(hashlib.sha256((token + "_w4").encode("utf-8")).hexdigest()[:8], 16)

                    idx1, idx2, idx3, idx4 = h1 % dim, h2 % dim, h3 % dim, h4 % dim
                    sign1 = 1.0 if (h1 & 0x1) else -1.0
                    sign2 = 1.0 if (h2 & 0x1) else -1.0
                    sign3 = 1.0 if (h3 & 0x1) else -1.0
                    sign4 = 1.0 if (h4 & 0x1) else -1.0

                    vec[idx1] += sign1 * 1.0 * pos_weight
                    vec[idx2] += sign2 * 0.75 * pos_weight
                    vec[idx3] += sign3 * 0.5 * pos_weight
                    vec[idx4] += sign4 * 0.25 * pos_weight

                norm = math.sqrt(sum(v * v for v in vec))
                if norm > 0:
                    vec = [v / norm for v in vec]
                else:
                    vec = [1.0 / math.sqrt(dim)] * dim
            else:
                vec = [1.0 / math.sqrt(dim)] * dim
            embeddings.append(np.array(vec, dtype=np.float32))
        return embeddings


# ─────────────────────────────────────────────────────────────
# 3. 知识切片元数据作用域自动分类 (Metadata Scope Classification)
# ─────────────────────────────────────────────────────────────
_KNOWN_CITIES = [
    "长春", "北京", "上海", "广州", "深圳", "成都", "重庆", "杭州", "南京", "武汉",
    "西安", "苏州", "天津", "长沙", "郑州", "青岛", "沈阳", "大连", "哈尔滨", "济南",
    "福州", "厦门", "昆明", "合肥", "佛山", "无锡", "宁波",
]


def classify_chunk_scope(source: str, content: str = "", explicit_scope: str = "") -> Dict[str, str]:
    """
    自动识别 RAG 知识切片的适用空间层级：
      - "project_custom": 当前项目用户自定义上传的专属任务书/上位规划
      - "case_thesis": 示范案例毕业设计开题报告/任务书 (在非长春场地自动屏蔽)
      - "national": 国家级通用技术规范、用地分类标准、中央城市更新指导意见
      - "city_statute": 特定城市地方性法规、保护规划、总规 (异地场地降权并标注为参考先例)
    """
    src = str(source or "").strip()
    txt = str(content or "")[:300].strip()

    if explicit_scope == "project_custom" or src.startswith("自定义:") or src.startswith("项目专属:"):
        from src.config.site import get_site_city
        return {"scope": "project_custom", "city": get_site_city() or "属地"}

    # 1. 毕业设计任务书 / 开题报告示范案例
    if any(k in src for k in ("毕业设计", "开题报告", "任务书")):
        return {"scope": "case_thesis", "city": "长春"}

    # 2. 国家级标准规范与中央文件
    if any(
        k in src
        for k in (
            "中共中央",
            "国务院",
            "用地用海规范",
            "控规用地颜色分类",
            "国家",
            "住建部",
            "自然资源部",
            "GB",
            "持续推进城市更新行动的意见",
        )
    ):
        return {"scope": "national", "city": "全国"}

    # 3. 城市地方性条例与专项保护规划
    if any(k in src or k in txt for k in ("伪满皇宫", "长春", "宽城区")):
        return {"scope": "city_statute", "city": "长春"}

    for c_name in _KNOWN_CITIES:
        if c_name in src:
            return {"scope": "city_statute", "city": c_name}

    # 默认通用规范
    return {"scope": "national", "city": "全国"}


# ─────────────────────────────────────────────────────────────
# 4. 原生 BGE 向量嵌入接口 (100% 保持向后兼容)
# ─────────────────────────────────────────────────────────────
@st.cache_resource
def load_bge_micro_model():
    """Lazily load BAAI/bge-micro-zh-v4 for vector retrieval."""
    try:
        from transformers import AutoModel, AutoTokenizer

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
        content = p_info.get("content")
        if not content:
            continue
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
                "embeddings": db_embeddings,
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


# ─────────────────────────────────────────────────────────────
# 5. 自定义项目文档持久化管理 (Custom Document Ingestion)
# ─────────────────────────────────────────────────────────────
def load_custom_rag_knowledge() -> Dict[str, Dict[str, Any]]:
    """加载当前项目自定义上传的 RAG 切片库 (data/custom_site/custom_rag_knowledge.json)。"""
    try:
        custom_path = resolve_path(CUSTOM_RAG_REL_PATH)
        if custom_path.exists():
            with open(custom_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception as e:
        logger.warning("Failed to load custom RAG knowledge: %s", e)
    return {}


def add_custom_document(filename: str, text: str, scope: str = "project_custom") -> int:
    """
    将用户上传的规划文本/任务书/上位规划切分并持久化写入 `data/custom_site/custom_rag_knowledge.json`。
    使用 AcademicContextualChunker 与 recursive_character_chunking 进行双层高锐度切片。
    返回新增切片数量。
    """
    cleaned_text = clean_pdf_noise(text)
    if not cleaned_text or len(cleaned_text.strip()) < 10:
        return 0

    from src.config.site import get_site_city

    active_city = (get_site_city() or "属地").strip()
    source_name = os.path.basename(filename or "项目自定义规范.txt")

    chunker = AcademicContextualChunker(parent_size=900, child_size=320, parent_overlap=80)
    _, child_records = chunker.build_parent_child_index_from_section(
        book_meta={"major_code": scope, "subject": f"{active_city}城市更新规划", "book_name": source_name},
        chapter_title=source_name,
        sec_text=cleaned_text,
        page_start=1,
        page_end=1,
    )

    new_chunks: Dict[str, Dict[str, Any]] = {}
    if child_records:
        for rec in child_records:
            content_body = rec.get("content", "").strip()
            if not content_body:
                continue
            cid = hashlib.md5(f"{source_name}_{content_body[:100]}".encode("utf-8")).hexdigest()[:12]
            new_chunks[cid] = {
                "source": source_name,
                "content": content_body,
                "index_text": rec.get("index_text", content_body),
                "scope": scope,
                "city": active_city,
            }
    else:
        raw_slices = recursive_character_chunking(cleaned_text, chunk_size=400, chunk_overlap=60, min_chunk_len=10)
        for sl in raw_slices:
            cid = hashlib.md5(f"{source_name}_{sl[:100]}".encode("utf-8")).hexdigest()[:12]
            new_chunks[cid] = {
                "source": source_name,
                "content": sl,
                "scope": scope,
                "city": active_city,
            }

    if not new_chunks:
        return 0

    existing = load_custom_rag_knowledge()
    existing.update(new_chunks)

    custom_path = resolve_path(CUSTOM_RAG_REL_PATH)
    custom_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=str(custom_path.parent), suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, str(custom_path))
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise

    # 清除检索缓存以立即生效
    try:
        retrieve_rag_context.clear()
    except Exception:
        pass
    _BM25_INDEX_CACHE.clear()

    return len(new_chunks)


def clear_custom_documents() -> None:
    """清空自定义项目 RAG 知识切片并重置检索缓存。"""
    try:
        custom_path = resolve_path(CUSTOM_RAG_REL_PATH)
        if custom_path.exists():
            custom_path.unlink()
    except Exception as e:
        logger.warning("Failed to remove custom RAG file: %s", e)
    try:
        retrieve_rag_context.clear()
    except Exception:
        pass
    _BM25_INDEX_CACHE.clear()


# ─────────────────────────────────────────────────────────────
# 6. 预计算倒排索引 BM25 + 交叉重排 + U 型防迷失组装
# ─────────────────────────────────────────────────────────────
_BM25_INDEX_CACHE: Dict[str, Tuple[Dict[str, List[Tuple[str, int]]], Dict[str, int], float]] = {}
_INDEX_LOCK = threading.RLock()


def _get_or_build_bm25_index(
    rag_db: Dict[str, Dict[str, Any]]
) -> Tuple[Dict[str, List[Tuple[str, int]]], Dict[str, int], float]:
    """为给定的 rag_db 构建并缓存 O(1) 词频倒排索引 `(cid, tf)` 与动态 `avgdl`。"""
    if not rag_db:
        return {}, {}, 400.0

    keys_sorted = sorted(rag_db.keys())
    sample_sig = f"{len(keys_sorted)}_{keys_sorted[0]}_{keys_sorted[-1]}"
    sample_content = str(rag_db[keys_sorted[0]].get("content", ""))[:32]
    cache_key = hashlib.md5(f"{sample_sig}_{sample_content}".encode("utf-8")).hexdigest()

    with _INDEX_LOCK:
        if cache_key in _BM25_INDEX_CACHE:
            return _BM25_INDEX_CACHE[cache_key]

        inverted_index: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
        doc_lengths: Dict[str, int] = {}

        for cid, p_info in rag_db.items():
            text = p_info.get("index_text") or p_info.get("content") or ""
            source = p_info.get("source") or ""
            full_str = f"{source}\n{text}"
            tokens = tokenize_text(full_str, filter_stopwords=True)
            token_counts = Counter(tokens)
            doc_lengths[cid] = max(len(tokens), 1)
            for tok, tf in token_counts.items():
                inverted_index[tok].append((cid, tf))

        total_len = sum(doc_lengths.values())
        avgdl = (total_len / max(len(doc_lengths), 1)) or 300.0

        result = (dict(inverted_index), doc_lengths, avgdl)
        _BM25_INDEX_CACHE[cache_key] = result
        return result


def _bm25_search(
    query: str,
    rag_db: Dict[str, Dict[str, Any]],
    top_k: int = 20,
) -> List[Tuple[str, float]]:
    """基于预计算倒排索引 (O(1) 词频命中) 与动态全局 avgdl 的标准 BM25 检索。"""
    if not rag_db or not query:
        return []

    inverted_index, lengths_dict, avgdl = _get_or_build_bm25_index(rag_db)
    expanded_query = expand_query_terms(query)
    query_tokens = tokenize_text(expanded_query, filter_stopwords=True)
    if not query_tokens:
        query_tokens = tokenize_text(query, filter_stopwords=False)

    scores: Dict[str, float] = defaultdict(float)
    total_docs = len(rag_db)
    k1 = 2.0
    b = 0.75

    for token in query_tokens:
        postings = inverted_index.get(token)
        if not postings:
            continue
        doc_freq = len(postings)
        idf = math.log((total_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)
        for cid, tf in postings:
            doc_len = lengths_dict.get(cid, avgdl)
            score = idf * (tf * (k1 + 1.0)) / (tf + k1 * (1.0 - b + b * (doc_len / avgdl)))
            scores[cid] += score

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]


def _semantic_rerank(
    query: str,
    candidates: List[str],
    rrf_map: Dict[str, float],
    rag_db: Dict[str, Dict[str, Any]],
) -> List[Tuple[str, float]]:
    """轻量级语义交叉打分精排 (Cross-Scoring Reranker: 融合 RRF 基础分 + 词重叠率 + 来源标题命中加权)。"""
    q_tokens = set(tokenize_text(query, filter_stopwords=True))
    scored: List[Tuple[str, float]] = []

    for cid in candidates:
        p_info = rag_db.get(cid)
        if not p_info:
            continue
        base_rrf = rrf_map.get(cid, 0.0)
        content = p_info.get("content", "") or ""
        source = p_info.get("source", "") or ""
        d_tokens = set(tokenize_text(f"{source} {content}", filter_stopwords=True))

        overlap = len(q_tokens & d_tokens) / max(len(q_tokens), 1)
        source_lower = source.lower()
        title_boost = 1.25 if any(qt in source_lower for qt in q_tokens if len(qt) > 1) else 1.0

        # 以 RRF 为主干，叠加上下文词重叠精排因子
        final_score = base_rrf * (1.0 + 0.35 * overlap) * title_boost
        scored.append((cid, final_score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def _u_shaped_packing(chunks: List[Tuple[float, str, str]]) -> List[Tuple[float, str, str]]:
    """
    U 型注意力防迷失组装 (Lost-in-the-Middle 对抗策略):
    排布顺序: [Rank 1 在最前, Rank 3 在中间, Rank 2 在最后]
    让大模型注意力最高的头部与尾部承载最核心规范上下文。
    """
    if len(chunks) <= 2:
        return chunks
    reordered: List[Optional[Tuple[float, str, str]]] = [None] * len(chunks)
    left, right = 0, len(chunks) - 1
    for i, item in enumerate(chunks):
        if i % 2 == 0:
            reordered[left] = item
            left += 1
        else:
            reordered[right] = item
            right -= 1
    return [c for c in reordered if c is not None]


# ─────────────────────────────────────────────────────────────
# 7. 主检索入口 (Scope-Aware Hybrid RRF Retrieval)
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def retrieve_rag_context(query: str, top_k: int = 3) -> list:
    """Retrieve top-k most relevant regulation chunks using Scope-Aware Hybrid RRF (k=60).

    Combines dense BGE vector semantic ranking with precomputed inverted-index BM25 ranking,
    automatic scope metadata filtering/boosting, cross-scoring reranker, and U-shaped packing.
    Returns list of (score, content, source) tuples.
    """
    if not query or not str(query).strip():
        return []

    base_db = load_rag_knowledge() or {}
    custom_db = load_custom_rag_knowledge() if base_db else {}
    if not base_db and not custom_db:
        return []

    # 合并基础库与用户自定义库（浅拷贝避免污染缓存对象）
    rag_db: Dict[str, Dict[str, Any]] = {}
    for cid, info in base_db.items():
        if isinstance(info, dict):
            rag_db[cid] = dict(info)
    for cid, info in custom_db.items():
        if isinstance(info, dict):
            item_copy = dict(info)
            item_copy.setdefault("scope", "project_custom")
            rag_db[cid] = item_copy

    if not rag_db:
        return []

    # 检测当前激活场地是否为默认长春伪满皇宫场地
    try:
        from src.config.site import get_site_city, get_site_name

        active_city = (get_site_city() or "").strip()
        active_name = (get_site_name() or "").strip()
    except Exception:
        active_city, active_name = "长春", "伪满皇宫"

    is_changchun = ("长春" in active_city) or ("伪满" in active_name) or (not active_city and not active_name)

    # 0. 作用域分类与跨城防污染预过滤
    filtered_db: Dict[str, Dict[str, Any]] = {}
    scope_meta_map: Dict[str, Dict[str, str]] = {}

    for cid, p_info in rag_db.items():
        src = p_info.get("source", "") or ""
        cnt = p_info.get("content", "") or ""
        explicit_sc = p_info.get("scope", "") or ""
        sc_meta = classify_chunk_scope(src, cnt, explicit_scope=explicit_sc)

        # 非长春场地：严禁注入作者个人的长春毕业设计任务书与开题报告
        if not is_changchun and sc_meta["scope"] == "case_thesis":
            continue

        scope_meta_map[cid] = sc_meta
        filtered_db[cid] = p_info

    if not filtered_db:
        return []

    db_embeddings, _ = get_cached_db_embeddings()

    # 1. Rank by Dense Vector Similarity (BGE 优先)
    dense_ranks: Dict[str, int] = {}
    if db_embeddings:
        query_emb = compute_query_embedding(query)
        if query_emb is not None:
            v_scores = []
            for cid in filtered_db:
                if cid in db_embeddings:
                    score = float(np.dot(query_emb, db_embeddings[cid]))
                    v_scores.append((cid, score))
            v_scores.sort(key=lambda x: x[1], reverse=True)
            dense_ranks = {cid: rank + 1 for rank, (cid, _) in enumerate(v_scores)}

    # 2. Rank by Precomputed Inverted-Index BM25 with Urban Synonym Expansion
    bm25_hits = _bm25_search(query, filtered_db, top_k=max(top_k * 6, 24))
    kw_ranks = {cid: rank + 1 for rank, (cid, _) in enumerate(bm25_hits)}

    # 兜底：若分词后未命中任何词项，使用基础子串匹配保证召回
    if not kw_ranks:
        query_words = [w for w in jieba.cut(query) if len(w.strip()) > 0]
        kw_scores = []
        for cid, p_info in filtered_db.items():
            content = p_info.get("content", "") or ""
            score = sum(1 for w in query_words if w in content)
            if score > 0:
                kw_scores.append((cid, score))
        kw_scores.sort(key=lambda x: x[1], reverse=True)
        kw_ranks = {cid: rank + 1 for rank, (cid, _) in enumerate(kw_scores)}

    # 3. Scope-Aware Reciprocal Rank Fusion (RRF with k=60)
    K = 60.0
    rrf_map: Dict[str, float] = {}
    all_cids = set(dense_ranks.keys()).union(set(kw_ranks.keys()))

    for cid in all_cids:
        rrf_score = 0.0
        if cid in dense_ranks:
            rrf_score += 1.0 / (K + dense_ranks[cid])
        if cid in kw_ranks:
            rrf_score += 1.0 / (K + kw_ranks[cid])

        sc_info = scope_meta_map.get(cid, {"scope": "national", "city": "全国"})
        sc_type = sc_info["scope"]
        sc_city = sc_info["city"]

        if not is_changchun:
            if sc_type == "project_custom":
                rrf_score *= 2.0
            elif sc_type == "national":
                rrf_score *= 1.5
            elif sc_type == "city_statute":
                if active_city and (sc_city in active_city or active_city in sc_city):
                    rrf_score *= 1.8
                else:
                    rrf_score *= 0.45
        else:
            if sc_type == "project_custom":
                rrf_score *= 1.5
            elif sc_type == "city_statute":
                rrf_score *= 1.15
            elif sc_type == "national":
                rrf_score *= 1.1
            elif sc_type == "case_thesis":
                rrf_score *= 0.9

        rrf_map[cid] = rrf_score

    if not rrf_map:
        return []

    # 4. Cross-Scoring Semantic Reranker
    top_candidates = sorted(rrf_map.keys(), key=lambda x: rrf_map[x], reverse=True)[: max(top_k * 3, 10)]
    reranked_pairs = _semantic_rerank(query, top_candidates, rrf_map, filtered_db)[:top_k]

    best_chunks: List[Tuple[float, str, str]] = []
    for cid, final_score in reranked_pairs:
        p_info = filtered_db.get(cid, {})
        raw_content = p_info.get("content", "") or ""
        content = clean_pdf_noise(raw_content)
        source = p_info.get("source", "") or ""

        sc_info = scope_meta_map.get(cid, {"scope": "national", "city": "全国"})
        if (
            not is_changchun
            and sc_info["scope"] == "city_statute"
            and not (active_city and (sc_info["city"] in active_city or active_city in sc_info["city"]))
        ):
            if not source.startswith("异地参考先例:"):
                source = f"异地参考先例:{source}"

        best_chunks.append((round(final_score, 6), content, source))

    # 5. U-Shaped Attention Packing (when top_k >= 3)
    if top_k >= 3 and len(best_chunks) >= 3:
        best_chunks = _u_shaped_packing(best_chunks)

    return best_chunks[:top_k]
