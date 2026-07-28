"""
Unit tests for OSMDataFetcher engine.
"""

import os
import tempfile
import pytest
import geopandas as gpd
from src.engines.osm_fetcher import OSMDataFetcher, estimate_utm_crs

def test_estimate_utm_crs():
    # Changchun coordinates ~ (125.32 E, 43.85 N) -> Zone 51 -> EPSG:32651
    crs_str = estimate_utm_crs(125.32, 43.85)
    assert crs_str == "EPSG:32651"
    
    # Southern hemisphere check
    crs_south = estimate_utm_crs(151.20, -33.86)
    assert crs_south == "EPSG:32756"

def test_osm_fetcher_fallback_with_utm():
    fetcher = OSMDataFetcher(timeout=2)
    with tempfile.TemporaryDirectory() as tmp_dir:
        gdfs = fetcher._generate_fallback_gdfs(
            min_lat=43.85,
            min_lon=125.32,
            max_lat=43.90,
            max_lon=125.38,
            utm_crs="EPSG:32651",
            output_dir=tmp_dir
        )
        assert "buildings" in gdfs
        assert "roads" in gdfs
        assert "landuse" in gdfs
        assert not gdfs["buildings"].empty
        assert "area_m2" in gdfs["buildings"].columns
        assert "perimeter_m" in gdfs["buildings"].columns
        assert gdfs["buildings"].iloc[0]["area_m2"] > 0
        
        assert os.path.exists(os.path.join(tmp_dir, "Building_Footprints.geojson"))

def test_osm_fetcher_parse_elements():
    fetcher = OSMDataFetcher()
    elements = [
        {"type": "node", "id": 1, "lat": 43.85, "lon": 125.32},
        {"type": "node", "id": 2, "lat": 43.86, "lon": 125.32},
        {"type": "node", "id": 3, "lat": 43.86, "lon": 125.33},
        {"type": "node", "id": 4, "lat": 43.85, "lon": 125.33},
        {
            "type": "way",
            "id": 10,
            "nodes": [1, 2, 3, 4, 1],
            "tags": {"building": "residential", "building:levels": "6", "name": "Block 1"}
        }
    ]
    
    gdfs = fetcher._parse_overpass_elements(elements, 43.84, 125.31, 43.87, 125.34, "EPSG:32651")
    assert len(gdfs["buildings"]) == 1
    assert gdfs["buildings"].iloc[0]["Floor"] == 6
    assert gdfs["buildings"].iloc[0]["area_m2"] > 0
