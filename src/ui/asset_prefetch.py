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
    st.components.v1.html(build_prefetch_script(), height=0, scrolling=False)
