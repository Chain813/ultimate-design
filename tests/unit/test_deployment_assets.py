import subprocess

from src.config import ROOT_DIR
from src.ui import asset_prefetch
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


def test_heavy_atlas_assets_are_not_tracked_for_deployment():
    result = subprocess.run(
        ["git", "ls-files", "static/atlas", "static/atlas_enhanced"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == ""


def test_prefetch_assets_include_default_3d_map_assets_only():
    assert "static/buildings.geojson" in PREFETCH_ASSETS
    assert "static/building_shadows.geojson" in PREFETCH_ASSETS
    assert "static/atlas/答辩PPT.pptx" not in PREFETCH_ASSETS
    assert all(not asset.startswith("static/atlas/") for asset in PREFETCH_ASSETS)


def test_prefetch_script_uses_idle_callback_and_static_urls():
    script = build_prefetch_script()
    assert "requestIdleCallback" in script
    assert 'fetch(url, { cache: "force-cache" })' in script
    assert "/app/static/buildings.geojson" in script
    assert "static/atlas" not in script


def test_render_static_asset_prefetch_uses_hidden_component(monkeypatch):
    calls = []

    def fake_html(html, height=0, scrolling=False):
        calls.append({"html": html, "height": height, "scrolling": scrolling})

    monkeypatch.setattr(asset_prefetch.st.components.v1, "html", fake_html, raising=False)

    asset_prefetch.render_static_asset_prefetch()

    assert calls
    assert calls[0]["height"] == 0
    assert calls[0]["scrolling"] is False
    assert "requestIdleCallback" in calls[0]["html"]
