"""Canonical project paths for app/pages/tools usage."""

from pathlib import Path

from .runtime import project_root

ROOT_DIR = project_root()
DATA_DIR = ROOT_DIR / "data"
SHP_DIR = DATA_DIR / "shp"
ASSETS_DIR = ROOT_DIR / "assets"
STATIC_DIR = ROOT_DIR / "static"
DOCS_DIR = ROOT_DIR / "docs"
META_DIR = DATA_DIR / "meta"

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
# IMPORTANT: Streamlit's static serving behavior varies between local, Docker, and Cloud.
# 1. Locally, it often serves at /static/.
# 2. In Docker/Cloud, it may serve at /app/static/.
# 3. We use /app/static/ as the base, but map3d_standalone.html now includes 
#    an automatic 404 fallback to /static/ for maximum resilience on Streamlit Cloud.
STATIC_URL_PREFIX = "/app/static/"

def get_static_url(filename: str) -> str:
    """
    Safely generates the internal URL routing path for a static asset.
    Example: get_static_url('buildings.geojson') -> '/app/static/buildings.geojson'
    """
    return f"{STATIC_URL_PREFIX}{filename}"
