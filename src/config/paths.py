"""Canonical project paths for app/pages/tools usage."""

from pathlib import Path

from .runtime import project_root

ROOT_DIR = project_root()
DATA_DIR = ROOT_DIR / "data"
SHP_DIR = DATA_DIR / "shp"
ASSETS_DIR = ROOT_DIR / "assets"
STATIC_DIR = ROOT_DIR / "static"

DATA_FILES = {
    "poi": DATA_DIR / "Changchun_POI_Real.csv",
    "traffic": DATA_DIR / "Changchun_Traffic_Real.csv",
    "nlp": DATA_DIR / "CV_NLP_RawData.csv",
    "gvi": DATA_DIR / "GVI_Results_Analysis.csv",
    "points": DATA_DIR / "Changchun_Precise_Points.xlsx",
    "rag": DATA_DIR / "rag_knowledge.json",
}

SHP_FILES = {
    "boundary": SHP_DIR / "Boundary_Scope.geojson",
    "plots": SHP_DIR / "Key_Plots_District.json",
    "buildings": SHP_DIR / "Building_Footprints.geojson",
}

# ==========================================
# 🌐 Web Static Routing Configuration
# ==========================================
# WARNING: When Streamlit is run with --server.enableStaticServing=true,
# it HARDCODES the internal web endpoint for the local 'static/' folder to '/app/static/'.
# Please DO NOT interpret '/app/' as a Docker-specific path and attempt to remove it.
# Deleting '/app/' will cause all frontend 3D rendering to fail with 404 errors!
STATIC_URL_PREFIX = "/app/static/"

def get_static_url(filename: str) -> str:
    """
    Safely generates the internal URL routing path for a static asset.
    Example: get_static_url('buildings.geojson') -> '/app/static/buildings.geojson'
    """
    return f"{STATIC_URL_PREFIX}{filename}"
