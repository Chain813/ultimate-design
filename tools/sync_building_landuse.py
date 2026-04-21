"""
Building-Landuse Spatial Join
Tags buildings based on their landuse zone:
  - Class 9 (Green Space) -> prop_style = "park" (green)
  - Class 2 (Admin/Historical) -> prop_style = "historical" (purple)
"""
import geopandas as gpd
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def sync_building_landuse():
    print("🚀 Starting building-landuse spatial join (FULL JILIN SCOPE)...")

    # 1. Load data
    print("  Loading full Jilin landuse (97MB)...")
    landuse = gpd.read_file("data/shp/landuse_jilin.geojson")
    print(f"  Landuse polygons: {len(landuse)}")

    print("  Loading buildings...")
    buildings = gpd.read_file("data/shp/Building_Footprints.geojson")
    print(f"  Buildings: {len(buildings)}")

    # Ensure CRS match
    if buildings.crs != landuse.crs:
        landuse = landuse.to_crs(buildings.crs)

    # 2. Prepare building centroids for faster sjoin
    print("  Computing building centroids...")
    bld_centroids = buildings.copy()
    bld_centroids['geometry'] = bld_centroids.geometry.centroid

    # 3. Spatial join: which landuse zone does each building centroid fall in?
    print("  Performing spatial join...")
    joined = gpd.sjoin(bld_centroids, landuse[['Class', 'geometry']], how='left', predicate='within')

    # 4. Apply rules
    # Initialize columns (preserve any existing historical labels)
    existing_hist = buildings['prop_style'] == 'historical'
    
    buildings['landuse_class'] = joined['Class'].values
    
    park_mask = buildings['landuse_class'] == 10
    hist_mask = buildings['landuse_class'] == 9
    
    # Tag park buildings
    buildings.loc[park_mask, 'is_historical'] = False
    buildings.loc[park_mask, 'prop_style'] = 'park'
    buildings.loc[park_mask, 'hist_name'] = '公园绿地区域'
    buildings.loc[park_mask, 'hist_batch'] = 'G-绿地'
    
    # Tag admin/historical zone buildings (only if not already tagged)
    new_hist = hist_mask & ~existing_hist
    buildings.loc[new_hist, 'is_historical'] = True
    buildings.loc[new_hist, 'prop_style'] = 'historical'
    buildings.loc[new_hist, 'hist_name'] = '行政办公/历史保护区域'
    buildings.loc[new_hist, 'hist_batch'] = 'A-保护'
    
    # Drop temp column
    buildings.drop(columns=['landuse_class'], inplace=True)

    # 5. Stats
    n_park = (buildings['prop_style'] == 'park').sum()
    n_hist = (buildings['prop_style'] == 'historical').sum()
    n_normal = (buildings['prop_style'] == 'normal').sum()
    print(f"\n📊 Results:")
    print(f"  🟢 Park/Green buildings: {n_park}")
    print(f"  🟣 Historical/Protected buildings: {n_hist}")
    print(f"  ⬜ Normal buildings: {n_normal}")

    # 6. Save to both locations
    print("\n💾 Saving updated GeoJSON...")
    buildings.to_file("data/shp/Building_Footprints.geojson", driver='GeoJSON')
    buildings.to_file("static/buildings.geojson", driver='GeoJSON')
    print("✅ Done! Both data and static files synchronized.")

if __name__ == "__main__":
    sync_building_landuse()
