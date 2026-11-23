"""Unit tests for src.core.runtime_adapter dual-mode cache and state layer."""

from __future__ import annotations

import sys
import time

import pytest

from src.core.runtime_adapter import (
    cache_data,
    cache_resource,
    clear_all_caches,
    delete_state,
    get_active_project_id,
    get_state,
    is_streamlit_runtime,
    runtime_state,
    set_active_project_id,
    set_state,
)


@pytest.fixture(autouse=True)
def _clean_runtime_adapter(monkeypatch):
    """Ensure clean project ID, caches, and isolated desktop state for each test."""
    st_mod = sys.modules.get("streamlit")
    if st_mod is not None and hasattr(st_mod, "session_state"):
        monkeypatch.setattr(st_mod, "session_state", None, raising=False)
    set_active_project_id("changchun_default", clear_cache=True)
    runtime_state.clear()
    yield
    set_active_project_id("changchun_default", clear_cache=True)
    runtime_state.clear()


def test_is_streamlit_runtime_false_in_pytest():
    assert is_streamlit_runtime() is False


def test_cache_data_memoization_and_clear():
    calls = {"count": 0}

    @cache_data(ttl=60, max_entries=32)
    def compute_square(x: int, factor: int = 1) -> int:
        calls["count"] += 1
        return (x * x) * factor

    assert compute_square(4, factor=2) == 32
    assert compute_square(4, factor=2) == 32
    assert calls["count"] == 1

    assert compute_square(5, factor=2) == 50
    assert calls["count"] == 2

    compute_square.clear()
    assert compute_square(4, factor=2) == 32
    assert calls["count"] == 3


def test_cache_data_ttl_expiration():
    calls = {"count": 0}

    @cache_data(ttl=0.05)
    def short_lived(val: str) -> str:
        calls["count"] += 1
        return f"res:{val}:{calls['count']}"

    r1 = short_lived("a")
    r2 = short_lived("a")
    assert r1 == r2
    assert calls["count"] == 1

    time.sleep(0.08)
    r3 = short_lived("a")
    assert r3 != r1
    assert calls["count"] == 2


def test_cache_resource_singleton_and_clear_all():
    created = {"data": 0, "res": 0}

    @cache_data
    def load_table() -> dict[str, int]:
        created["data"] += 1
        return {"rows": 100}

    @cache_resource
    def get_heavy_client() -> object:
        created["res"] += 1
        return object()

    c1 = get_heavy_client()
    c2 = get_heavy_client()
    assert c1 is c2
    assert created["res"] == 1

    t1 = load_table()
    t2 = load_table()
    assert t1 == t2
    assert created["data"] == 1

    clear_all_caches()

    c3 = get_heavy_client()
    t3 = load_table()
    assert c3 is not c1
    assert t3 == t1
    assert created["res"] == 2
    assert created["data"] == 2


def test_get_set_delete_and_runtime_state_proxy():
    assert get_state("missing_key", "fallback") == "fallback"

    set_state("alpha", 123)
    assert get_state("alpha") == 123
    assert "alpha" in runtime_state
    assert runtime_state["alpha"] == 123
    assert runtime_state.alpha == 123

    runtime_state["beta"] = "hello"
    runtime_state.gamma = [1, 2, 3]
    assert runtime_state.get("beta") == "hello"
    assert runtime_state["gamma"] == [1, 2, 3]

    assert runtime_state.setdefault("beta", "other") == "hello"
    assert runtime_state.setdefault("delta", 99) == 99
    assert get_state("delta") == 99

    runtime_state.update({"epsilon": True}, zeta="ok")
    snapshot = runtime_state.to_dict()
    assert snapshot["epsilon"] is True
    assert snapshot["zeta"] == "ok"
    assert "alpha" in list(runtime_state.keys())
    assert 123 in list(runtime_state.values())
    assert ("beta", "hello") in list(runtime_state.items())

    popped = runtime_state.pop("delta")
    assert popped == 99
    assert "delta" not in runtime_state
    assert runtime_state.pop("delta", "gone") == "gone"

    deleted = delete_state("alpha")
    assert deleted == 123
    assert "alpha" not in runtime_state


def test_project_switching_isolates_state_and_caches():
    calls = {"count": 0}

    @cache_data
    def get_project_label() -> str:
        calls["count"] += 1
        return f"label_for_{get_active_project_id()}"

    set_active_project_id("project_alpha")
    set_state("target_plot", "地块A")
    runtime_state["stage_bus"] = {"04_target_plot": "地块A"}
    lbl_alpha = get_project_label()
    assert lbl_alpha == "label_for_project_alpha"
    assert get_state("target_plot") == "地块A"

    set_active_project_id("project_beta")
    assert get_active_project_id() == "project_beta"
    assert get_state("target_plot") is None
    assert "stage_bus" not in runtime_state

    set_state("target_plot", "地块B")
    lbl_beta = get_project_label()
    assert lbl_beta == "label_for_project_beta"
    assert get_state("target_plot") == "地块B"

    # Switch back to project_alpha and verify its state was preserved
    set_active_project_id("project_alpha")
    assert get_state("target_plot") == "地块A"
    assert runtime_state["stage_bus"]["04_target_plot"] == "地块A"
