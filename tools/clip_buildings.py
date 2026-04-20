import geopandas as gpd
import shutil

print("Loading datasets...", flush=True)
try:
    buildings = gpd.read_file('data/shp/Building_Footprints.geojson')
    print("Total buildings loaded:", len(buildings), flush=True)
    
    boundary = gpd.read_file('data/shp/Boundary_Scope.geojson')
    
    boundary_geom = boundary.geometry.unary_union
    minx, miny, maxx, maxy = boundary_geom.bounds
    
    # 扩大边界约1公里 (0.01度) 留出视野缓冲
    minx, miny = minx - 0.01, miny - 0.01
    maxx, maxy = maxx + 0.01, maxy + 0.01
    
    print("Filtering buildings by bounding box...", flush=True)
    buildings_clipped = buildings.cx[minx:maxx, miny:maxy]
    print("Buildings remaining after clip:", len(buildings_clipped), flush=True)
    
    if len(buildings_clipped) > 0 and len(buildings_clipped) < len(buildings):
        # 备份原文件
        print("Backing up Original...", flush=True)
        shutil.copyfile('data/shp/Building_Footprints.geojson', 'data/shp/Building_Footprints_Original.geojson.bak')
        
        # 写入裁剪后的数据
        print("Saving optimized GeoJSON...", flush=True)
        buildings_clipped.to_file('data/shp/Building_Footprints.geojson', driver='GeoJSON')
        print("Optimization complete!", flush=True)
    else:
        print("No clipping needed or clipping failed (0 results).", flush=True)
except Exception as e:
    print("Fatal Error:", e)

