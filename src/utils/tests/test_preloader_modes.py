from src.utils import preloader


def test_cloud_light_preload_enabled_by_default(monkeypatch):
    monkeypatch.delenv("UP_ENABLE_HEAVY_PRELOAD", raising=False)
    assert preloader.is_heavy_preload_enabled() is False


def test_heavy_preload_can_be_enabled_explicitly(monkeypatch):
    monkeypatch.setenv("UP_ENABLE_HEAVY_PRELOAD", "1")
    assert preloader.is_heavy_preload_enabled() is True


def test_run_preload_skips_heavy_tiers_by_default(monkeypatch):
    calls = []
    monkeypatch.delenv("UP_ENABLE_HEAVY_PRELOAD", raising=False)
    monkeypatch.setattr(preloader, "_preload_light", lambda: calls.append("light"))
    monkeypatch.setattr(preloader, "_preload_tier1", lambda: calls.append("tier1"))
    monkeypatch.setattr(preloader, "_preload_tier2", lambda: calls.append("tier2"))
    monkeypatch.setattr(preloader, "_preload_tier3", lambda: calls.append("tier3"))

    preloader._run_preload()

    assert calls == ["light"]


def test_run_preload_runs_all_tiers_when_heavy_enabled(monkeypatch):
    calls = []
    monkeypatch.setenv("UP_ENABLE_HEAVY_PRELOAD", "true")
    monkeypatch.setattr(preloader, "_preload_light", lambda: calls.append("light"))
    monkeypatch.setattr(preloader, "_preload_tier1", lambda: calls.append("tier1"))
    monkeypatch.setattr(preloader, "_preload_tier2", lambda: calls.append("tier2"))
    monkeypatch.setattr(preloader, "_preload_tier3", lambda: calls.append("tier3"))

    preloader._run_preload()

    assert calls == ["light", "tier1", "tier2", "tier3"]
