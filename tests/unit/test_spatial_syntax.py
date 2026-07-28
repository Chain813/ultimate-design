"""
Unit tests for SpatialSyntaxEngine.
"""

import pytest
import geopandas as gpd
from shapely.geometry import LineString, Polygon, box
from src.engines.spatial_syntax_engine import SpatialSyntaxEngine

def test_spatial_syntax_depthmapx_metrics():
    engine = SpatialSyntaxEngine()
    
    # 3 intersecting lines forming a Y-junction
    l1 = LineString([(0, 0), (10, 0)])
    l2 = LineString([(5, -5), (5, 5)])
    l3 = LineString([(2, -2), (2, 2)])
    
    roads = gpd.GeoDataFrame([
        {"id": 1, "geometry": l1},
        {"id": 2, "geometry": l2},
        {"id": 3, "geometry": l3}
    ], crs="EPSG:4326")
    
    res = engine.analyze_network_syntax(roads)
    assert "MeanDepth" in res.columns
    assert "RA" in res.columns
    assert "Integration" in res.columns
    assert "Choice" in res.columns
    assert res["Integration"].min() > 0
    assert len(res) == 3

def test_spatial_syntax_momepy_morphometrics():
    engine = SpatialSyntaxEngine()
    
    b1 = box(0, 0, 10, 10)  # 100 m2
    b2 = box(15, 15, 25, 25) # 100 m2
    
    buildings = gpd.GeoDataFrame([
        {"geometry": b1, "Floor": 5, "height": 16.0, "area_m2": 100.0},
        {"geometry": b2, "Floor": 20, "height": 64.0, "area_m2": 100.0}
    ], crs="EPSG:4326")
    
    morpho = engine.compute_momepy_morphometrics(buildings, site_area_m2=1000.0)
    assert "BCR" in morpho
    assert "FAR" in morpho
    assert "SVF" in morpho
    assert morpho["BCR"] == 0.2  # 200 / 1000 = 0.2
    assert morpho["FAR"] == 2.5  # (100*5 + 100*20) / 1000 = 2.5

def test_spatial_syntax_microclimate():
    engine = SpatialSyntaxEngine()
    b1 = box(0, 0, 10, 10)
    buildings = gpd.GeoDataFrame([{"geometry": b1, "Floor": 5, "height": 16.0, "area_m2": 100.0}], crs="EPSG:4326")
    
    mc = engine.evaluate_microclimate(buildings)
    assert "wind_comfort_index" in mc
    assert "solar_shadow_index" in mc
    assert "morphometrics" in mc
    assert "SVF" in mc["morphometrics"]
