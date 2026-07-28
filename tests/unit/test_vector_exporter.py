"""
Unit tests for VectorExporter and DXF export functions.
"""

import os
import zipfile
import tempfile
import pytest
import geopandas as gpd
from shapely.geometry import Polygon, LineString, Point
from src.utils.vector_exporter import VectorExporter, rgb_to_truecolor
from src.utils.document_generator import export_statutory_dxf_bundle

def test_rgb_to_truecolor():
    tc = rgb_to_truecolor(255, 69, 0)
    assert tc == (255 << 16) | (69 << 8) | 0

def test_vector_exporter_dxf_with_tables_and_text():
    exporter = VectorExporter()
    p = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    l = LineString([(0, 0), (20, 20)])
    pt = Point(5, 5)

    gdfs = {
        "landuse": gpd.GeoDataFrame([{"geometry": p, "type": "residential", "name": "Plot A", "Floor": 12}], crs="EPSG:4326"),
        "roads": gpd.GeoDataFrame([{"geometry": l, "name": "Main Rd"}], crs="EPSG:4326"),
        "poi": gpd.GeoDataFrame([{"geometry": pt, "name": "Node B"}], crs="EPSG:4326")
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        dxf_path = os.path.join(tmp_dir, "test_plan.dxf")
        res = exporter.export_to_dxf(gdfs, dxf_path)
        assert os.path.exists(res)
        
        with open(res, "r", encoding="utf-8") as f:
            content = f.read()
            assert "TABLES" in content
            assert "LAYER" in content
            assert "420" in content  # TrueColor Group Code
            assert "TEXT" in content # Text annotation
            assert "Plot A" in content

def test_vector_exporter_bundle():
    p = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    gdfs = {
        "buildings": gpd.GeoDataFrame([{"geometry": p, "Floor": 5}], crs="EPSG:4326")
    }
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, "statutory_bundle.zip")
        res = export_statutory_dxf_bundle(gdfs, zip_path)
        assert os.path.exists(res)
        
        with zipfile.ZipFile(res, "r") as zf:
            names = zf.namelist()
            assert "statutory_plan.dxf" in names
            assert "buildings.geojson" in names
