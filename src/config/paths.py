"""Canonical project paths for app/pages/tools usage."""


from .runtime import project_root

from .loader import load_global_config
from pathlib import Path

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

config = load_global_config()

def _get_conf_path(key: str, default: Path) -> Path:
    val = config.get("data", {}).get(key)
    if val:
        p = Path(val)
        return p if p.is_absolute() else ROOT_DIR / p
    return default

DATA_FILES = {
    "poi": _get_conf_path("poi_data", CSV_DIR / "Changchun_POI_Real.csv"),
    "poi_secondary": _get_conf_path("poi_secondary_data", CSV_DIR / "Changchun_POI_Baidu_New.csv"),
    "traffic": _get_conf_path("traffic_data", CSV_DIR / "Changchun_Traffic_Real.csv"),
    "nlp": _get_conf_path("nlp_raw_data", CSV_DIR / "CV_NLP_RawData.csv"),
    "gvi": _get_conf_path("gvi_results", CSV_DIR / "GVI_Results_Analysis.csv"),
    "points": _get_conf_path("precise_points", CSV_DIR / "Changchun_Precise_Points.xlsx"),
    "rag": _get_conf_path("rag_knowledge_path", DATA_DIR / "rag_knowledge.json"),
}

GIS_FILES = {
    "boundary": _get_conf_path("boundary_scope", GIS_DIR / "Boundary_Scope.geojson"),
    "plots": _get_conf_path("key_plots", GIS_DIR / "Key_Plots_District.json"),
    "buildings": _get_conf_path("building_footprints", GIS_DIR / "Building_Footprints.geojson"),
    "roads": _get_conf_path("roads", GIS_DIR / "road_clipped.geojson"),
    "rails": _get_conf_path("rails", GIS_DIR / "rail_clipped.geojson"),
    "landuse": _get_conf_path("landuse", GIS_DIR / "landuse_clipped.geojson"),
    "protected": _get_conf_path("protected_buildings", STATIC_DIR / "protected_buildings.geojson"),
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
