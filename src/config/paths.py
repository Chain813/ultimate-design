"""Canonical project paths for app/pages/tools usage."""


from .runtime import project_root

ROOT_DIR = project_root()
DATA_DIR = ROOT_DIR / "data"
CSV_DIR = DATA_DIR / "csv"
GIS_DIR = DATA_DIR / "gis"
ASSETS_DIR = ROOT_DIR / "assets"
STATIC_DIR = ROOT_DIR / "static"
DOCS_DIR = ROOT_DIR / "docs"
META_DIR = DATA_DIR / "meta"
STREETVIEW_DIR = DATA_DIR / "streetview"

# Backward-compatible aliases
SHP_DIR = GIS_DIR

DATA_FILES = {
    "poi": CSV_DIR / "Changchun_POI_Real.csv",
    "traffic": CSV_DIR / "Changchun_Traffic_Real.csv",
    "nlp": CSV_DIR / "CV_NLP_RawData.csv",
    "gvi": CSV_DIR / "GVI_Results_Analysis.csv",
    "points": CSV_DIR / "Changchun_Precise_Points.xlsx",
    "rag": DATA_DIR / "rag_knowledge.json",
}

GIS_FILES = {
    "boundary": GIS_DIR / "Boundary_Scope.geojson",
    "plots": GIS_DIR / "Key_Plots_District.json",
    "buildings": GIS_DIR / "Building_Footprints.geojson",
    "roads": GIS_DIR / "road_clipped.geojson",
    "rails": GIS_DIR / "rail_clipped.geojson",
    "landuse": GIS_DIR / "landuse_clipped.geojson",
    "protected": STATIC_DIR / "protected_buildings.geojson",
}

# Backward-compatible alias
SHP_FILES = GIS_FILES

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
