# tools/fill_missing_landuse.py
import sys
import geopandas as gpd
import pandas as pd
from pathlib import Path

# Force UTF-8 stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent

def fill_missing_landuse():
    print("Starting landuse gap-filling process...")
    
    # Load files
    boundary_path = ROOT / "data/gis/Boundary_Scope.geojson"
    landuse_path = ROOT / "data/gis/landuse_clipped.geojson"
    water_path = ROOT / "static/water.geojson"
    roads_path = ROOT / "static/road_clipped.geojson"
    
    boundary = gpd.read_file(boundary_path)
    landuse = gpd.read_file(landuse_path)
    water = gpd.read_file(water_path) if water_path.exists() else None
    roads = gpd.read_file(roads_path) if roads_path.exists() else None
    
    # Ensure same CRS
    if boundary.crs != landuse.crs:
        boundary = boundary.to_crs(landuse.crs)
    if water is not None and water.crs != landuse.crs:
        water = water.to_crs(landuse.crs)
    if roads is not None and roads.crs != landuse.crs:
        roads = roads.to_crs(landuse.crs)
        
    b_union = boundary.union_all()
    l_union = landuse.union_all()
    diff = b_union.difference(l_union)
    
    if diff.is_empty:
        print("No landuse gaps found!")
        return
        
    print(f"  Gap area detected: {diff.area:.6f} degrees²")
    
    # Zone 1: Green Space near Yitong River (within ~150m of water)
    green_zone = None
    remaining_diff = diff
    if water is not None and not water.empty:
        water_buffer = water.union_all().buffer(0.0015)
        green_zone = diff.intersection(water_buffer)
        remaining_diff = diff.difference(water_buffer)
        
    # Zone 2: Commercial near major roads (within ~35m of level 1/2 roads)
    comm_zone = None
    res_zone = remaining_diff
    if roads is not None and not roads.empty:
        major_roads = roads[roads['level'].isin([1, 2])]
        if not major_roads.empty:
            road_buffer = major_roads.union_all().buffer(0.00035)
            comm_zone = remaining_diff.intersection(road_buffer)
            res_zone = remaining_diff.difference(road_buffer)
            
    new_features = []
    
    def make_row(geom, cl):
        mapping = {
            0: {"type": "居住用地", "color": "#FFFF00", "gb": "R"},
            2: {"type": "商业服务业", "color": "#FF7F00", "gb": "B"},
            10: {"type": "公园与绿地", "color": "#38A800", "gb": "G"}
        }
        return {
            "geometry": geom,
            "Class": cl,
            "Type": mapping[cl]["type"],
            "Color": mapping[cl]["color"],
            "GB_Code": mapping[cl]["gb"]
        }
        
    if green_zone and not green_zone.is_empty:
        if green_zone.geom_type == 'GeometryCollection':
            for g in green_zone.geoms:
                if g.geom_type in ['Polygon', 'MultiPolygon'] and not g.is_empty:
                    new_features.append(make_row(g, 10))
        else:
            new_features.append(make_row(green_zone, 10))
            
    if comm_zone and not comm_zone.is_empty:
        if comm_zone.geom_type == 'GeometryCollection':
            for g in comm_zone.geoms:
                if g.geom_type in ['Polygon', 'MultiPolygon'] and not g.is_empty:
                    new_features.append(make_row(g, 2))
        else:
            new_features.append(make_row(comm_zone, 2))
            
    if res_zone and not res_zone.is_empty:
        if res_zone.geom_type == 'GeometryCollection':
            for g in res_zone.geoms:
                if g.geom_type in ['Polygon', 'MultiPolygon'] and not g.is_empty:
                    new_features.append(make_row(g, 0))
        else:
            new_features.append(make_row(res_zone, 0))
            
    if new_features:
        new_gdf = gpd.GeoDataFrame(new_features, crs=landuse.crs)
        combined = gpd.GeoDataFrame(pd.concat([landuse, new_gdf], ignore_index=True), crs=landuse.crs)
        combined.to_file(landuse_path, driver="GeoJSON")
        print("Landuse gap filling completed successfully!")
    else:
        print("No new features created.")

if __name__ == "__main__":
    fill_missing_landuse()
