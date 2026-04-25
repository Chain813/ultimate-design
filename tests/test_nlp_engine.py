import sys
sys.modules.setdefault("streamlit", type(sys)("streamlit_mock"))

from src.engines.nlp_engine import classify_sentiment, _load_sentiment_lexicon


def test_load_sentiment_lexicon_returns_frozensets():
    pos, neg = _load_sentiment_lexicon()
    assert isinstance(pos, frozenset)
    assert isinstance(neg, frozenset)
    assert len(pos) > 0
    assert len(neg) > 0


def test_classify_sentiment_positive():
    texts = ["这里环境非常美观便利，生活很舒适"]
    labels, scores = classify_sentiment(texts)
    assert labels[0] == "positive"
    assert scores[0] > 0


def test_classify_sentiment_negative():
    texts = ["这个街区太破旧了，拥堵杂乱，很不安全"]
    labels, scores = classify_sentiment(texts)
    assert labels[0] == "negative"
    assert scores[0] < 0


def test_classify_sentiment_neutral():
    texts = ["今天天气还可以"]
    labels, scores = classify_sentiment(texts)
    assert labels[0] == "neutral"


def test_classify_sentiment_returns_all_three_labels():
    texts = ["这个公园不错很漂亮", "道路太破了很不安全", "天气不错"]
    labels, scores = classify_sentiment(texts)
    assert len(labels) == 3
    assert len(scores) == 3


def test_classify_sentiment_scores_in_range():
    texts = ["环境特别差，非常破旧", "非常满意，很舒适漂亮"]
    labels, scores = classify_sentiment(texts)
    for s in scores:
        assert -1.0 <= s <= 1.0
