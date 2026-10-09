"""
Unit tests for VectorExporter and DXF export functions.
Verifies AutoCAD 2000 AC1015 compliance, GB standard layer conventions,
MultiPolygon/MultiLineString geometry decomposition, and TEXT newline sanitization.
"""

import os
import tempfile
import zipfile
import pytest
import geopandas as gpd
from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPolygon,
    Point,
    Polygon,
)
from src.utils.vector_exporter import (
    STANDARD_GB_LAYERS,
    VectorExporter,
    clean_dxf_string,
    export_dxf_from_gdf,
    export_multi_layer_dxf,
    flatten_geometries,
    normalize_layer_name,
    rgb_to_truecolor,
)
from src.utils.document_generator import export_statutory_dxf_bundle


def test_rgb_to_truecolor():
    tc = rgb_to_truecolor(255, 69, 0)
    assert tc == (255 << 16) | (69 << 8) | 0


def test_clean_dxf_string():
    raw = "第一行文本\n第二行包含细节\r\n第三行\t制表符"
    cleaned = clean_dxf_string(raw)
    assert "\n" not in cleaned
    assert "\r" not in cleaned
    assert "\t" not in cleaned
    assert "第一行文本 第二行包含细节 第三行 制表符" == cleaned


def test_normalize_layer_name():
    assert normalize_layer_name("boundary") == "01_BOUNDARY"
    assert normalize_layer_name("规划红线") == "01_BOUNDARY"
    assert normalize_layer_name("buildings") == "02_EXISTING_BLDG"
    assert normalize_layer_name("retained_bldg") == "02_EXISTING_BLDG"
    assert normalize_layer_name("proposed_renewal") == "03_PROPOSED_BLDG"
    assert normalize_layer_name("roads") == "04_ROAD_CENTER"
    assert normalize_layer_name("road_network") == "04_ROAD_CENTER"
    assert normalize_layer_name("green_space") == "05_GREEN_SPACE"
    assert normalize_layer_name("park") == "05_GREEN_SPACE"


def test_flatten_geometries_multipolygon_and_multilinestring():
    p1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    p2 = Polygon([(2, 2), (3, 2), (3, 3), (2, 3)])
    mp = MultiPolygon([p1, p2])

    l1 = LineString([(0, 0), (5, 5)])
    l2 = LineString([(5, 5), (10, 10)])
    mls = MultiLineString([l1, l2])

    flat_mp = flatten_geometries(mp)
    assert len(flat_mp) == 2
    assert all(t == "polygon" for t, _ in flat_mp)

    flat_mls = flatten_geometries(mls)
    assert len(flat_mls) == 2
    assert all(t == "line" for t, _ in flat_mls)


def test_vector_exporter_ac1015_header_and_tables():
    exporter = VectorExporter()
    p = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    l = LineString([(0, 0), (20, 20)])
    pt = Point(5, 5)

    gdfs = {
        "boundary": gpd.GeoDataFrame([{"geometry": p, "name": "规划研究红线"}], crs="EPSG:4326"),
        "roads": gpd.GeoDataFrame([{"geometry": l, "name": "人民大街\n主干道\r\n4车道"}], crs="EPSG:4326"),
        "poi": gpd.GeoDataFrame([{"geometry": pt, "name": "地铁站节点"}], crs="EPSG:4326")
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        dxf_path = os.path.join(tmp_dir, "test_ac1015.dxf")
        res = exporter.export_to_dxf(gdfs, dxf_path)
        assert os.path.exists(res)

        with open(res, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. 验证 AC1015 (AutoCAD 2000) 声明与中文字符集 ANSI_936
        assert "AC1015" in content
        assert "$DWGCODEPAGE" in content
        assert "ANSI_936" in content

        # 2. 验证国标 5 大图层声明与颜色
        for layer_name in STANDARD_GB_LAYERS.keys():
            assert f"2\n{layer_name}\n" in content

        # 3. 验证换行符被严格清除，防止 DXF 组码错位
        lines = content.split("\n")
        # 遍历所有 TEXT 实体的内容组码 '1'
        for i in range(len(lines) - 1):
            if lines[i] == "1" and "人民大街" in lines[i+1]:
                # 该行不应含有实际未转义换行（在单行中）
                assert "\r" not in lines[i+1]
                assert "人民大街 主干道 4车道" in lines[i+1]

        # 4. 验证 MultiPolygon 和 MultiLineString 递归展开
        assert "01_BOUNDARY" in content
        assert "04_ROAD_CENTER" in content
        assert "TABLES" in content
        assert "ENTITIES" in content
        assert "EOF" in content


def test_vector_exporter_multilinestring_export():
    exporter = VectorExporter()
    l1 = LineString([(100, 100), (200, 200)])
    l2 = LineString([(200, 200), (300, 300)])
    mls = MultiLineString([l1, l2])

    p1 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    p2 = Polygon([(20, 20), (30, 20), (30, 30), (20, 30)])
    mp = MultiPolygon([p1, p2])

    gdfs = {
        "roads": gpd.GeoDataFrame([{"geometry": mls, "name": "复杂路网"}], crs="EPSG:4326"),
        "buildings": gpd.GeoDataFrame([{"geometry": mp, "name": "双塔复合建筑", "Floor": 18}], crs="EPSG:4326"),
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        dxf_path = os.path.join(tmp_dir, "test_multi.dxf")
        exporter.export_to_dxf(gdfs, dxf_path)
        with open(dxf_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 两个折线都应该存在
        assert "100.0" in content
        assert "200.0" in content
        assert "300.0" in content
        # 双塔楼两个多边形都导出
        assert "18F" in content


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


def test_export_dxf_from_gdf_and_multi_layer():
    p = Polygon([(125.33, 43.89), (125.35, 43.89), (125.35, 43.91), (125.33, 43.91)])
    l = LineString([(125.33, 43.89), (125.35, 43.91)])
    gdf_b = gpd.GeoDataFrame([{"geometry": p, "name": "测试红线"}], crs="EPSG:4326")
    gdf_r = gpd.GeoDataFrame([{"geometry": l, "name": "测试道路"}], crs="EPSG:4326")

    with tempfile.TemporaryDirectory() as tmp_dir:
        # 1. Single layer export
        out_single = os.path.join(tmp_dir, "single.dxf")
        res1 = export_dxf_from_gdf(gdf_b, out_single, layer_name="01_BOUNDARY", to_metric=True)
        assert os.path.exists(res1)
        with open(res1, "r", encoding="utf-8") as f:
            content1 = f.read()
        assert "LWPOLYLINE" in content1
        assert "01_BOUNDARY" in content1

        # 2. Multi layer export
        out_multi = os.path.join(tmp_dir, "multi.dxf")
        res2 = export_multi_layer_dxf({
            "01_BOUNDARY": gdf_b,
            "04_ROAD_CENTER": gdf_r,
        }, out_multi, to_metric=True)
        assert os.path.exists(res2)
        with open(res2, "r", encoding="utf-8") as f:
            content2 = f.read()
        assert "LWPOLYLINE" in content2
        assert "01_BOUNDARY" in content2
        assert "04_ROAD_CENTER" in content2
