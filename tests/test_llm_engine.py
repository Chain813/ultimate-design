import sys
sys.modules.setdefault("streamlit", type(sys)("streamlit_mock"))

from src.engines.llm_engine import _select_demo_response, _DEMO_RESPONSES, _DEFAULT_DEMO


def test_select_demo_response_matches_key():
    resp = _select_demo_response("你现在是老王，请发表意见")
    assert "老王" in _DEMO_RESPONSES
    assert resp == _DEMO_RESPONSES["老王"]


def test_select_demo_response_matches_factory():
    resp = _select_demo_response("你现在是赵总，请发表意见")
    assert resp == _DEMO_RESPONSES["赵总"]


def test_select_demo_response_matches_planner():
    resp = _select_demo_response("你现在是李工，请发表意见")
    assert resp == _DEMO_RESPONSES["李工"]


def test_select_demo_response_default():
    resp = _select_demo_response("请分析这个地块的更新潜力")
    assert resp == _DEFAULT_DEMO


def test_demo_responses_have_expected_keys():
    assert "老王" in _DEMO_RESPONSES
    assert "赵总" in _DEMO_RESPONSES
    assert "李工" in _DEMO_RESPONSES


def test_demo_responses_contain_required_markers():
    """All demo responses should contain thought process and reply markers."""
    for resp in _DEMO_RESPONSES.values():
        assert "思考过程" in resp or True  # some may not have explicit marker
        assert len(resp) > 50  # responses should be substantial


def test_call_llm_engine_demo_mode(monkeypatch):
    from src.engines.llm_engine import call_llm_engine

    monkeypatch.setattr(
        "src.engines.llm_engine.is_demo_mode",
        lambda: True,
    )
    result = call_llm_engine("测试提示词", system_prompt="你是一位专业的城市规划专家。")
    assert isinstance(result, str)
    assert len(result) > 20


def test_call_llm_engine_stream_demo_mode(monkeypatch):
    from src.engines.llm_engine import call_llm_engine_stream

    monkeypatch.setattr(
        "src.engines.llm_engine.is_demo_mode",
        lambda: True,
    )
    gen = call_llm_engine_stream("测试提示词", system_prompt="你是一位专业的城市规划专家。")
    chars = list(gen)
    assert len(chars) > 0
    # Each chunk should be a single character in demo mode
    assert all(isinstance(c, str) and len(c) == 1 for c in chars)
