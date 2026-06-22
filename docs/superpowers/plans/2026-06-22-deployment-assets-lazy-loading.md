# Deployment Assets Lazy Loading Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy only homepage and 3D-map runtime assets while keeping first-page entry smooth through browser idle prefetching and lightweight server preloading.

**Architecture:** Add a small asset manifest module responsible for required deployment assets and browser prefetch rendering. Keep the existing Deck.GL map async layer loading, but prefetch default map resources after the homepage is visible. Add a cloud-light mode to the existing server preloader so Streamlit Cloud does not start heavy model or GeoPandas warming during cold start.

**Tech Stack:** Python, Streamlit `st.markdown`, browser `requestIdleCallback`, pytest, existing Streamlit test mock in `tests/conftest.py`.

---

### Task 1: Deployment Asset Manifest And Browser Prefetch

**Files:**
- Create: `src/ui/asset_prefetch.py`
- Create: `tests/test_deployment_assets.py`
- Modify: `app.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_deployment_assets.py` with tests that import the desired asset manifest and helper:

```python
from pathlib import Path

from src.config import ROOT_DIR
from src.ui.asset_prefetch import (
    DEPLOYMENT_ASSETS,
    PREFETCH_ASSETS,
    build_prefetch_script,
    iter_required_asset_paths,
)


def test_required_deployment_assets_exist():
    missing = [str(path.relative_to(ROOT_DIR)) for path in iter_required_asset_paths() if not path.exists()]
    assert missing == []


def test_deployment_assets_exclude_static_atlas():
    all_assets = [asset for assets in DEPLOYMENT_ASSETS.values() for asset in assets]
    assert all(not asset.startswith("static/atlas/") for asset in all_assets)
    assert all(not asset.startswith("static/atlas_enhanced/") for asset in all_assets)


def test_prefetch_assets_include_default_3d_map_assets_only():
    assert "static/buildings.geojson" in PREFETCH_ASSETS
    assert "static/building_shadows.geojson" in PREFETCH_ASSETS
    assert "static/atlas/答辩PPT.pptx" not in PREFETCH_ASSETS
    assert all(not asset.startswith("static/atlas/") for asset in PREFETCH_ASSETS)


def test_prefetch_script_uses_idle_callback_and_static_urls():
    script = build_prefetch_script()
    assert "requestIdleCallback" in script
    assert "fetch(url, { cache: \"force-cache\" })" in script
    assert "/app/static/buildings.geojson" in script
    assert "static/atlas" not in script
```

- [ ] **Step 2: Run the tests and verify they fail because the module is missing**

Run: `python -m pytest tests/test_deployment_assets.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'src.ui.asset_prefetch'`.

- [ ] **Step 3: Implement the asset manifest and prefetch helper**

Create `src/ui/asset_prefetch.py`:

```python
"""Static asset manifest and browser prefetch helpers for deployed Streamlit pages."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.config import ROOT_DIR, get_static_url


DEPLOYMENT_ASSETS: dict[str, tuple[str, ...]] = {
    "critical": (
        "static/research_scope_2d_cropped.png",
        "static/03_digital_twin.png",
        "static/04_urban_diagnosis.png",
        "static/05_design_inference.png",
        "static/06_llm_consultation_v2.png",
        "static/boundary.geojson",
        "data/gis/Boundary_Scope.geojson",
        "data/gis/Key_Plots_District.json",
    ),
    "default_map": (
        "static/buildings.geojson",
        "static/building_shadows.geojson",
        "data/gis/Building_Footprints.geojson",
    ),
    "optional_layers": (
        "static/landuse.geojson",
        "static/rail_clipped.geojson",
        "static/road_clipped.geojson",
        "static/road_syntax.geojson",
        "static/water.geojson",
        "data/gis/landuse_clipped.geojson",
        "data/gis/rail_clipped.geojson",
        "data/gis/road_clipped.geojson",
    ),
}

PREFETCH_ASSETS: tuple[str, ...] = (
    "static/buildings.geojson",
    "static/building_shadows.geojson",
    "static/landuse.geojson",
    "static/rail_clipped.geojson",
    "static/road_clipped.geojson",
    "static/road_syntax.geojson",
)


def iter_required_asset_paths() -> list[Path]:
    """Return absolute paths for assets that must exist in a deployed build."""
    return [ROOT_DIR / asset for assets in DEPLOYMENT_ASSETS.values() for asset in assets]


def _static_asset_url(asset: str) -> str:
    if not asset.startswith("static/"):
        raise ValueError(f"Only static assets can be browser-prefetched: {asset}")
    return get_static_url(asset.removeprefix("static/"))


def build_prefetch_script(prefetch_assets: tuple[str, ...] = PREFETCH_ASSETS) -> str:
    """Build a browser-side idle prefetch script for static 3D map assets."""
    urls = [_static_asset_url(asset) for asset in prefetch_assets]
    urls_json = json.dumps(urls)
    return f"""
<script>
(function() {{
  const urls = {urls_json};
  const run = function() {{
    urls.forEach(function(url) {{
      fetch(url, {{ cache: "force-cache" }}).catch(function(error) {{
        console.debug("[asset-prefetch] skipped", url, error);
      }});
    }});
  }};
  if ("requestIdleCallback" in window) {{
    window.requestIdleCallback(run, {{ timeout: 2500 }});
  }} else {{
    window.setTimeout(run, 1200);
  }}
}})();
</script>
"""


def render_static_asset_prefetch() -> None:
    """Inject the idle prefetch script after the homepage has rendered."""
    st.markdown(build_prefetch_script(), unsafe_allow_html=True)
```

- [ ] **Step 4: Run the deployment asset tests and verify they pass**

Run: `python -m pytest tests/test_deployment_assets.py -v`

Expected: PASS.

- [ ] **Step 5: Wire the prefetch helper into the homepage**

Modify `app.py` near the existing imports:

```python
from src.ui.asset_prefetch import render_static_asset_prefetch
```

Call it after the main banner has rendered, before the heavier map section:

```python
render_static_asset_prefetch()
```

- [ ] **Step 6: Run the focused tests again**

Run: `python -m pytest tests/test_deployment_assets.py -v`

Expected: PASS.

### Task 2: Cloud-Light Server Preloader

**Files:**
- Modify: `src/utils/preloader.py`
- Create: `tests/test_preloader_modes.py`

- [ ] **Step 1: Write failing tests for cloud-light mode**

Create `tests/test_preloader_modes.py`:

```python
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
```

- [ ] **Step 2: Run the tests and verify they fail because cloud-light functions do not exist**

Run: `python -m pytest tests/test_preloader_modes.py -v`

Expected: FAIL with `AttributeError` for `is_heavy_preload_enabled`.

- [ ] **Step 3: Implement cloud-light mode**

Modify `src/utils/preloader.py`:

```python
import os
```

Add:

```python
def is_heavy_preload_enabled() -> bool:
    """Return True only when local/demo runs explicitly opt into heavy warming."""
    return os.getenv("UP_ENABLE_HEAVY_PRELOAD", "").strip().lower() in {"1", "true", "yes", "on"}


def _preload_light():
    """Lightweight startup warming safe for Streamlit Cloud cold starts."""
    from src.config.loader import load_global_config
    from src.engines.spatial_engine import get_hud_statistics

    _warm("load_global_config", load_global_config)
    _warm("get_hud_statistics", get_hud_statistics)
```

Replace `_run_preload()` with:

```python
def _run_preload():
    """Run lightweight preloading by default; heavy tiers are opt-in."""
    _preload_light()
    if not is_heavy_preload_enabled():
        logger.info("Heavy cache preloading skipped. Set UP_ENABLE_HEAVY_PRELOAD=1 to enable it.")
        return

    _preload_tier1()
    _preload_tier2()
    _preload_tier3()
    logger.info("Cache preloading complete.")
```

- [ ] **Step 4: Run preloader tests**

Run: `python -m pytest tests/test_preloader_modes.py -v`

Expected: PASS.

### Task 3: Verification

**Files:**
- Verify: `src/ui/asset_prefetch.py`
- Verify: `src/utils/preloader.py`
- Verify: `app.py`
- Verify: tests

- [ ] **Step 1: Run focused tests**

Run: `python -m pytest tests/test_deployment_assets.py tests/test_preloader_modes.py -v`

Expected: PASS.

- [ ] **Step 2: Run existing related tests**

Run: `python -m pytest tests/test_startup_smoke.py tests/test_streamlit_compat.py tests/test_service_check.py -v`

Expected: PASS.

- [ ] **Step 3: Run syntax/lint check for changed files**

Run: `python -m ruff check app.py src/ui/asset_prefetch.py src/utils/preloader.py tests/test_deployment_assets.py tests/test_preloader_modes.py`

Expected: exit code 0.

- [ ] **Step 4: Review git diff**

Run: `git diff -- app.py src/ui/asset_prefetch.py src/utils/preloader.py tests/test_deployment_assets.py tests/test_preloader_modes.py`

Expected: diff only contains asset manifest, idle prefetch injection, cloud-light preloader logic, and tests.
