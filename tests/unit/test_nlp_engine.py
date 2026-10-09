import sys

sys.modules.setdefault("streamlit", type(sys)("streamlit_mock"))

from src.engines.nlp_engine import _load_sentiment_lexicon, classify_sentiment


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
    labels, _scores = classify_sentiment(texts)
    assert labels[0] == "neutral"


def test_classify_sentiment_returns_all_three_labels():
    texts = ["这个公园不错很漂亮", "道路太破了很不安全", "天气不错"]
    labels, scores = classify_sentiment(texts)
    assert len(labels) == 3
    assert len(scores) == 3


def test_classify_sentiment_scores_in_range():
    texts = ["环境特别差，非常破旧", "非常满意，很舒适漂亮"]
    _labels, scores = classify_sentiment(texts)
    for s in scores:
        assert -1.0 <= s <= 1.0


def test_get_nlp_data_handles_nan_text(monkeypatch):
    import pandas as pd
    from src.engines.nlp_engine import get_nlp_data

    mock_df = pd.DataFrame({
        "Text": ["这个街区太破旧了，拥堵杂乱，很不安全", None, "历史文化很丰富，很漂亮", float("nan"), "普通街道"]
    })
    monkeypatch.setattr("pandas.read_csv", lambda *args, **kwargs: mock_df.copy())
    if hasattr(get_nlp_data, "clear"):
        get_nlp_data.clear()
    df, word_counts = get_nlp_data()
    assert len(df) == 5
    assert "Sentiment" in df.columns
    assert "Score" in df.columns
    assert df.loc[1, "Sentiment"] == "neutral"
    assert df.loc[1, "Score"] == 0.0
    assert df.loc[3, "Sentiment"] == "neutral"
    assert df.loc[3, "Score"] == 0.0
    assert df.loc[0, "Sentiment"] == "negative"
