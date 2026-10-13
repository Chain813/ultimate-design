"""Unit tests for Dual-Track Site Ingestion Panel and GIS parsers.

Verifies:
1. GeoJSON boundary, centroid, UTM zone, and area calculation.
2. Zipped Shapefile parsing and DXF coordinates parsing.
3. OSMFetcher bounding box ingestion (Mode B).
4. Custom site context persistence (save and load).
5. Regulatory limits integration.
"""

import json
import os
import tempfile
import zipfile
import pytest
import geopandas as gpd
from shapely.geometry import Polygon, box

from src.ui.site_ingestion_panel import (
    parse_geojson_data,
    parse_shapefile_zip,
    parse_dxf_data,
    ingest_from_osm_bbox,
    save_custom_site,
    load_custom_site,
    render_site_ingestion_panel,
)


def test_parse_geojson_data_feature_collection():
    geojson_dict = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "工业厂区地块A", "land_use": "industrial"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [125.320, 43.850],
                            [125.325, 43.850],
                            [125.325, 43.855],
                            [125.320, 43.855],
                            [125.320, 43.850],
                        ]
                    ],
                },
            },
            {
                "type": "Feature",
                "properties": {"name": "居住配套地块B", "land_use": "residential"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [125.325, 43.850],
                            [125.330, 43.850],
                            [125.330, 43.855],
                            [125.325, 43.855],
                            [125.325, 43.850],
                        ]
                    ],
                },
            },
        ],
    }

    res = parse_geojson_data(geojson_dict)

    assert res["source_type"] == "geojson"
    assert res["features_count"] == 2
    assert "Polygon" in res["geometry_types"]
    assert res["bbox"][0] == pytest.approx(125.320, abs=1e-4)
    assert res["bbox"][2] == pytest.approx(125.330, abs=1e-4)
    assert res["bbox"][1] == pytest.approx(43.850, abs=1e-4)
    assert res["bbox"][3] == pytest.approx(43.855, abs=1e-4)
    assert res["center"][0] == pytest.approx(125.325, abs=1e-4)
    assert res["center"][1] == pytest.approx(43.8525, abs=1e-4)
    assert res["utm_epsg"] == 32651
    assert res["area_ha"] > 0
    assert len(res["plots"]) == 2
    assert res["plots"][0]["name"] == "工业厂区地块A"
    assert res["plots"][0]["land_use"] == "industrial"


def test_parse_geojson_data_bytes_and_string():
    raw_json = json.dumps({
        "type": "Feature",
        "properties": {"name": "单个测试地块"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[114.0, 22.5], [114.1, 22.5], [114.1, 22.6], [114.0, 22.6], [114.0, 22.5]]],
        },
    })
    res_str = parse_geojson_data(raw_json)
    assert res_str["features_count"] == 1
    assert res_str["utm_epsg"] == 32650
    assert res_str["area_ha"] > 0

    res_bytes = parse_geojson_data(raw_json.encode("utf-8"))
    assert res_bytes["features_count"] == 1
    assert res_bytes["utm_epsg"] == 32650


def test_parse_shapefile_zip(tmp_path):
    # Create a minimal shapefile in temporary directory
    shp_dir = tmp_path / "shp_source"
    shp_dir.mkdir()
    poly = Polygon([[125.30, 43.80], [125.35, 43.80], [125.35, 43.85], [125.30, 43.85], [125.30, 43.80]])
    gdf = gpd.GeoDataFrame([{"name": "测试SHP地块", "geometry": poly, "land_use": "commercial"}], crs="EPSG:4326")
    shp_file = shp_dir / "test.shp"
    gdf.to_file(str(shp_file))

    # Zip the shapefile parts
    zip_buf = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    zip_buf.close()
    with zipfile.ZipFile(zip_buf.name, "w") as zf:
        for f in shp_dir.iterdir():
            zf.write(f, arcname=f.name)

    with open(zip_buf.name, "rb") as f:
        zip_bytes = f.read()
    os.unlink(zip_buf.name)

    res = parse_shapefile_zip(zip_bytes)
    assert res["source_type"] == "shapefile"
    assert res["features_count"] == 1
    assert res["area_ha"] > 0
    assert res["utm_epsg"] == 32651
    assert res["plots"][0]["name"] == "测试SHP地块"


def test_parse_dxf_data():
    sample_dxf = """0
SECTION
2
ENTITIES
0
LINE
10
125.32
20
43.85
11
125.34
21
43.87
0
ENDSEC
0
EOF"""
    res = parse_dxf_data(sample_dxf.encode("utf-8"))
    assert res["source_type"] == "dxf"
    assert res["features_count"] >= 1
    assert res["area_ha"] > 0
    assert res["center"][0] > 0
    assert res["center"][1] > 0


def test_custom_site_persistence(tmp_path):
    cfg_file = tmp_path / "custom_site_test.json"

    # Non-existent file returns None
    assert load_custom_site(cfg_file) is None

    test_data = {
        "city": "成都市",
        "name": "锦江区滨水更新区",
        "center": [104.08, 30.65],
        "area_ha": 25.4,
        "regulatory_limits": {
            "far": 2.0,
            "height_limit": 24.0,
            "building_density_max": 0.30,
            "greenery_ratio_min": 0.40,
        },
    }

    saved_path = save_custom_site(test_data, config_path=cfg_file)
    assert saved_path.exists()

    loaded = load_custom_site(cfg_file)
    assert loaded is not None
    assert loaded["city"] == "成都市"
    assert loaded["regulatory_limits"]["far"] == 2.0
    assert loaded["regulatory_limits"]["height_limit"] == 24.0


def test_ingest_from_osm_bbox(tmp_path):
    # Test OSM ingestion with fallback / Overpass query
    res = ingest_from_osm_bbox(
        min_lat=43.85,
        min_lon=125.32,
        max_lat=43.90,
        max_lon=125.38,
        city_name="长春市",
        output_dir=str(tmp_path),
    )

    assert res["source_type"] == "osm_fetch"
    assert res["city"] == "长春市"
    assert res["area_ha"] > 0
    assert res["utm_epsg"] == 32651
    assert res["building_count"] >= 0
    assert res["road_count"] >= 0
    assert len(res["plots"]) >= 1
    assert 0.0 < res["building_density"] <= 1.0


def test_render_site_ingestion_panel_smoke():
    import streamlit as st

    # Initialize session state for testing
    if "custom_site_context" not in st.session_state:
        st.session_state["custom_site_context"] = {}

    # Calling render function without runtime error
    try:
        render_site_ingestion_panel()
    except Exception as e:
        pytest.fail(f"render_site_ingestion_panel raised an unexpected exception: {e}")
