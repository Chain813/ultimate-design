"""Geographic site configurations loader.

Usage:
    from src.config.site import (
        get_site_config, get_site_name, get_site_city,
        get_site_center, get_map_viewport, get_local_crs,
        get_landmarks,
    )
"""

import logging
from src.config.loader import load_global_config

logger = logging.getLogger("ultimateDESIGN")

def get_site_config() -> dict:
    """Return the site configuration dict."""
    config = load_global_config()
    return config.get("site", {})

def get_site_name() -> str:
    return get_site_config().get("site_name", "长春伪满皇宫周边街区")

def get_site_city() -> str:
    return get_site_config().get("city_name", "长春")

def get_site_center() -> list[float]:
    """Return the [longitude, latitude] center of the site."""
    return get_site_config().get("map", {}).get("center", [125.34064, 43.90095])

def get_map_viewport() -> dict:
    """Return the map viewport settings (center, zoom, pitch, bearing)."""
    site_conf = get_site_config()
    map_conf = site_conf.get("map", {})
    return {
        "center": map_conf.get("center", [125.34064, 43.90095]),
        "zoom": map_conf.get("zoom", 14.4),
        "pitch": map_conf.get("pitch", 65.0),
        "bearing": map_conf.get("bearing", 30.0),
        "min_zoom": map_conf.get("min_zoom", 10.0),
        "max_zoom": map_conf.get("max_zoom", 18.0),
    }

def get_local_crs() -> str:
    """Return the local UTM or projected Coordinate Reference System EPSG string."""
    return get_site_config().get("local_crs", "EPSG:32650")

def get_landmarks() -> list[dict]:
    """Return the list of landmarks with names and WGS84 coordinates."""
    default_landmarks = [
        {"name": "长春站", "coords": [125.3250, 43.9080]},
        {"name": "伪满皇宫", "coords": [125.3422, 43.9036]},
        {"name": "伊通河公园", "coords": [125.3590, 43.9010]},
        {"name": "胜利公园", "coords": [125.3260, 43.8960]},
        {"name": "光复路", "coords": [125.3395, 43.9016]},
    ]
    return get_site_config().get("landmarks", default_landmarks)

def get_site_district() -> str:
    return get_site_config().get("district_name", "宽城区")

def get_site_desc() -> str:
    return get_site_config().get("description", "由长春大街、长白路、东九条、亚泰快速路围合而成，研究范围约160公顷。")

def get_site_adjacent() -> str:
    return get_site_config().get("adjacent_features", "长春站（北侧枢纽）、伊通河（东侧生态廊道）")

def get_site_policies() -> list[str]:
    default_policies = [
        "《长春市历史文化名城保护规划》",
        "《长春市国土空间总体规划》"
    ]
    return get_site_config().get("policies", default_policies)
