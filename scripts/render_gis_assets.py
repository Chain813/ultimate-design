import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from pathlib import Path
import os
import sys

# 强制 UTF-8 编码输出
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 配置路径
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data/gis"
OUTPUT_DIR = ROOT / "static/assets/generated_base"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def render_assets():
    print("Starting GIS Rasterization Engine...")
    
    # 1. 加载数据
    boundary = gpd.read_file(DATA_DIR / "Boundary_Scope.geojson")
    roads = gpd.read_file(DATA_DIR / "road_network_clipped.geojson")
    landuse = gpd.read_file(DATA_DIR / "landuse_clipped.geojson")
    
    # 统一投影为 Web Mercator
    boundary_3857 = boundary.to_crs(epsg=3857)
    roads_3857 = roads.to_crs(epsg=3857)
    landuse_3857 = landuse.to_crs(epsg=3857)
    
    # 获取范围
    bbox = boundary_3857.total_bounds
    
    # --- 任务 A: 渲染卫星底图 ---
    print("Step A: Downloading high-res satellite imagery...")
    fig, ax = plt.subplots(figsize=(20, 20))
    boundary_3857.plot(ax=ax, facecolor='none', edgecolor='none')
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, zoom=16)
    ax.set_axis_off()
    plt.savefig(OUTPUT_DIR / "satellite_basemap.png", bbox_inches='tight', pad_inches=0, dpi=150)
    plt.close()

    # --- 任务 B: 渲染路网引导图 ---
    print("Step B: Rendering road guidance map...")
    fig, ax = plt.subplots(figsize=(20, 20), facecolor='black')
    ax.set_facecolor('black')
    roads_3857[roads_3857['level'] == 1].plot(ax=ax, color='white', linewidth=4)
    roads_3857[roads_3857['level'] == 2].plot(ax=ax, color='white', linewidth=2)
    roads_3857[roads_3857['level'] >= 3].plot(ax=ax, color='white', linewidth=1)
    ax.set_axis_off()
    ax.set_xlim(bbox[0], bbox[2])
    ax.set_ylim(bbox[1], bbox[3])
    plt.savefig(OUTPUT_DIR / "road_guidance.png", bbox_inches='tight', pad_inches=0, dpi=150)
    plt.close()

    # --- 任务 C: 渲染用地语义图 ---
    print("Step C: Rendering landuse segmentation map...")
    fig, ax = plt.subplots(figsize=(20, 20), facecolor='black')
    ax.set_facecolor('black')
    for _, row in landuse_3857.iterrows():
        color = row.get('Color', '#999999')
        gpd.GeoSeries([row.geometry]).plot(ax=ax, color=color, edgecolor='none')
    ax.set_axis_off()
    ax.set_xlim(bbox[0], bbox[2])
    ax.set_ylim(bbox[1], bbox[3])
    plt.savefig(OUTPUT_DIR / "landuse_segmentation.png", bbox_inches='tight', pad_inches=0, dpi=150)
    plt.close()

    print(f"Success! Assets generated in: {OUTPUT_DIR}")

if __name__ == "__main__":
    try:
        render_assets()
    except Exception as e:
        print(f"Error: {e}")
