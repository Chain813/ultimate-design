import sys

sys.modules.setdefault("streamlit", type(sys)("streamlit_mock"))

from src.config.site import (
    get_landmarks,
    get_local_crs,
    get_map_viewport,
    get_site_center,
    get_site_city,
    get_site_config,
    get_site_name,
)


def test_site_config_helpers():
    config = get_site_config()
    assert isinstance(config, dict)
    
    assert isinstance(get_site_name(), str)
    assert isinstance(get_site_city(), str)
    
    center = get_site_center()
    assert isinstance(center, list)
    assert len(center) == 2
    assert isinstance(center[0], float)
    assert isinstance(center[1], float)
    
    viewport = get_map_viewport()
    assert isinstance(viewport, dict)
    assert "center" in viewport
    assert "zoom" in viewport
    
    crs = get_local_crs()
    assert isinstance(crs, str)
    assert crs.startswith("EPSG:")
    
    landmarks = get_landmarks()
    assert isinstance(landmarks, list)
    if len(landmarks) > 0:
        assert "name" in landmarks[0]
        assert "coords" in landmarks[0]
