"""NLP sentiment engine: lexicon-based classification and word-cloud extraction.

Usage:
    from src.engines.nlp_engine import get_nlp_data, classify_sentiment
"""

import logging
from collections import Counter

import jieba
import pandas as pd
import streamlit as st

from src.config import resolve_path, DATA_FILES

logger = logging.getLogger("ultimateDESIGN")


@st.cache_resource
def _load_sentiment_lexicon() -> tuple[frozenset, frozenset]:
    """Fast sentiment dictionary tuned for urban-planning corpora."""
    pos_words = frozenset({
        "不错", "满意", "提升", "美观", "便利", "好", "完善", "特色",
        "活化", "保护", "改善", "新颖", "舒适", "生机", "活力", "期待",
    })
    neg_words = frozenset({
        "差", "破", "旧", "拥堵", "杂乱", "漏水", "噪音", "脏", "不便",
        "闲置", "空置", "杂乱无章", "衰败", "凋敝", "不安全",
    })
    return pos_words, neg_words


def _llm_classify_batch(batch: list[str]) -> list[dict]:
    from src.engines.llm_engine import call_llm_engine
    from src.utils.llm_json_parser import parse_llm_json
    
    formatted_texts = "\n".join(f"[{i}] {t}" for i, t in enumerate(batch))
    prompt = f"""
    分析以下城市更新相关的社交媒体评论情感。
    评论列表：
    {formatted_texts}
    
    请严格对每条评论进行情感分类 (positive/neutral/negative) 并给出一个 -1.0 到 1.0 的情感评分（正分代表积极正面，负分代表消极负面，接近 0 代表中立）。
    请仅返回 JSON 数组格式结果，不要包含任何 markdown 块或多余文字：
    [
        {{"id": 0, "sentiment": "positive", "score": 0.8}},
        ...
    ]
    """
    resp = call_llm_engine(prompt=prompt, system_prompt="你是一位专业的城市规划舆情分析师。", model="deepseek-v4-flash")
    parsed = parse_llm_json(resp, fallback=None)
    if parsed and isinstance(parsed, list) and len(parsed) == len(batch):
        return parsed
    raise ValueError("LLM parsing failed or length mismatch")


def classify_sentiment(texts: list[str]) -> tuple[list[str], list[float]]:
    """Tries LLM-based sentiment analysis, falls back to lightweight dictionary-based classification.

    Returns (labels, scores) where label ∈ {positive, neutral, negative}.
    """
    try:
        labels: list[str] = []
        scores: list[float] = []
        
        batch_size = 20
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            results = _llm_classify_batch(batch)
            for res in results:
                labels.append(res.get("sentiment", "neutral"))
                scores.append(float(res.get("score", 0.0)))
                
        if len(labels) == len(texts):
            return labels, scores
    except Exception as e:
        logger.warning(f"LLM sentiment analysis failed, falling back to lexicon: {e}")

    pos_set, neg_set = _load_sentiment_lexicon()
    labels: list[str] = []
    scores: list[float] = []

    for text in texts:
        text = str(text)
        words = set(jieba.cut(text))
        pos_hits = len(words & pos_set)
        neg_hits = len(words & neg_set)
        raw = (pos_hits - neg_hits) / (pos_hits + neg_hits + 1)

        if raw > 0.05:
            labels.append("positive")
            scores.append(round(min(raw + 0.4, 0.98), 3))
        elif raw < -0.05:
            labels.append("negative")
            scores.append(round(max(raw - 0.4, -0.98), 3))
        else:
            labels.append("neutral")
            scores.append(0.0)

    return labels, scores


@st.cache_data(ttl=600)
def get_nlp_data() -> tuple[pd.DataFrame, list[tuple[str, int]]]:
    """Load NLP raw data and compute sentiment + word cloud."""
    nlp_path = resolve_path(str(DATA_FILES["nlp"]))

    try:
        df = pd.read_csv(str(nlp_path), encoding="utf-8-sig")
        if "Text" not in df.columns:
            df = _normalize_text_column(df)
    except Exception:
        logger.warning("NLP data file missing, using demo data", exc_info=True)
        df = _generate_demo_nlp_data()

    if "Sentiment" not in df.columns or "Score" not in df.columns:
        valid = df["Text"].dropna().astype(str).tolist()
        labels, scores = classify_sentiment(valid)
        df["Sentiment"] = labels[:len(df)]
        df["Score"] = scores[:len(df)]

    stop_words = {"的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "很", "什么", "我们"}
    all_text = " ".join(df["Text"].dropna().astype(str))
    words = [w for w in jieba.cut(all_text) if len(w) > 1 and w not in stop_words]
    word_counts = Counter(words).most_common(15)

    return df, word_counts


def _normalize_text_column(df: pd.DataFrame) -> pd.DataFrame:
    col_lower = {c.lower(): c for c in df.columns}
    if "text" in col_lower:
        return df.rename(columns={col_lower["text"]: "Text"})
    for guess in ("评论", "内容"):
        if guess in df.columns:
            return df.rename(columns={guess: "Text"})
    df["Text"] = df.iloc[:, 0].astype(str)
    return df


def _generate_demo_nlp_data() -> pd.DataFrame:
    return pd.DataFrame({
        "Text": ["环境很差", "历史遗迹不错", "老厂房太破了", "交通拥堵", "伪满建筑很有特色"],
        "Score": [-0.8, 0.9, -0.6, -0.7, 0.8],
    })
