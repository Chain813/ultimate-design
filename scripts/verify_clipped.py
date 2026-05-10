import sys
import geopandas as gpd
sys.stdout.reconfigure(encoding="utf-8")

files = [
    ("data/shp/road_network_clipped.geojson", "道路网"),
    ("data/shp/rail_network_clipped.geojson", "铁路网"),
    ("data/shp/landuse_clipped.geojson", "用地现状"),
]

for f, label in files:
    gdf = gpd.read_file(f)
    print(f"{label}: {len(gdf)} 个要素, 字段={list(gdf.columns)}")
    if "Type" in gdf.columns:
        vc = dict(gdf["Type"].value_counts())
        print(f"  分类统计: {vc}")
    elif "Class" in gdf.columns:
        vc = dict(gdf["Class"].value_counts())
        print(f"  分类统计: {vc}")
    print()
