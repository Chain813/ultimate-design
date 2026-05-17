import os
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path

# 强制 UTF-8
import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
GIS_DIR = ROOT / "data/gis"
STATIC_DIR = ROOT / "static"
OUTPUT_DIR = ROOT / "output/high_precision"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 图层路径配置
LAYERS = {
    "boundary": GIS_DIR / "Boundary_Scope.geojson",
    "water": STATIC_DIR / "water.geojson",
    "roads": STATIC_DIR / "road_clipped.geojson",
    "rails": STATIC_DIR / "rail_clipped.geojson",
    "buildings": STATIC_DIR / "buildings.geojson",
    "landuse": GIS_DIR / "landuse_clipped.geojson",
    "key_plots": GIS_DIR / "Key_Plots_District.json",
    "protected": STATIC_DIR / "protected_buildings.geojson",
}

def load_layer(path):
    if path.exists():
        try:
            return gpd.read_file(path).to_crs(epsg=3857)
        except Exception as e:
            print(f"Error loading {path.name}: {e}")
    return None

def plot_layer(ax, gdf, layer_name, style_override=None):
    if gdf is None or gdf.empty:
        return

    # 默认样式字典
    styles = {
        "boundary": {"facecolor": "none", "edgecolor": "#FF0000", "linewidth": 4, "linestyle": "--", "zorder": 10},
        "water": {"facecolor": "#A0D8EF", "edgecolor": "none", "zorder": 2},
        "buildings_fill": {"facecolor": "#E5E5E5", "edgecolor": "#B3B3B3", "linewidth": 0.5, "zorder": 4},
        "buildings_outline": {"facecolor": "none", "edgecolor": "#333333", "linewidth": 0.5, "zorder": 4},
        "protected": {"facecolor": "#FFC0CB", "edgecolor": "#FF1493", "linewidth": 1.5, "zorder": 5},
        "rails": {"facecolor": "none", "edgecolor": "#000080", "linewidth": 2, "linestyle": "-.", "zorder": 6},
        "key_plots": {"facecolor": "none", "edgecolor": "#FFA500", "linewidth": 3, "zorder": 9},
    }

    style = style_override if style_override else styles.get(layer_name, {})

    if layer_name == "roads":
        # 道路按等级分别渲染
        for lvl, lw, color in [(1, 3, "#333333"), (2, 2, "#666666"), (3, 1, "#999999"), (4, 0.5, "#CCCCCC")]:
            sub_gdf = gdf[gdf.get("level", 4) == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax, color=color, linewidth=lw, zorder=5)
    elif layer_name == "landuse":
        # 用地按自带颜色渲染
        for _, row in gdf.iterrows():
            c = row.get("Color", "#CCCCCC")
            gpd.GeoSeries([row.geometry]).plot(ax=ax, facecolor=c, edgecolor="none", alpha=0.8, zorder=1)
    else:
        gdf.plot(ax=ax, **style)

def generate_map(map_name, layers_to_plot, bounds_gdf):
    print(f"Generating {map_name}...")
    fig, ax = plt.subplots(figsize=(24, 24), dpi=300)
    
    # 范围为研究范围及周边1km (EPSG:3857 单位为米)
    minx, miny, maxx, maxy = bounds_gdf.total_bounds
    pad = 1000  # 1km
    ax.set_xlim(minx - pad, maxx + pad)
    ax.set_ylim(miny - pad, maxy + pad)
    
    # 渲染每一层
    for layer_name, gdf in layers_to_plot:
        plot_layer(ax, gdf, layer_name)
        
    ax.set_axis_off()
    ax.set_aspect("equal")
    
    # 保存为透明背景的 PNG
    out_path = OUTPUT_DIR / f"{map_name}.png"
    plt.savefig(out_path, transparent=True, bbox_inches='tight', pad_inches=0, dpi=300)
    plt.close(fig)
    print(f"  -> Saved to {out_path.name}")

def main():
    print("Loading GIS Layers...")
    gdfs = {name: load_layer(path) for name, path in LAYERS.items()}
    boundary = gdfs["boundary"]
    if boundary is None:
        print("Boundary missing, cannot render.")
        return

    # 1. 交通分析图 (路网 + 铁路 + 水系 + 建筑轮廓 + 边界)
    traffic_layers = [
        ("water", gdfs["water"]),
        ("buildings_outline", gdfs["buildings"]),
        ("roads", gdfs["roads"]),
        ("rails", gdfs["rails"]),
        ("boundary", boundary)
    ]
    generate_map("交通分析图_Traffic_Analysis", traffic_layers, boundary)

    # 2. 重点地段与历史保护图 (水系 + 建筑填充 + 保护建筑 + 重点地块 + 路网浅色底 + 边界)
    focus_layers = [
        ("water", gdfs["water"]),
        ("buildings_fill", gdfs["buildings"]),
        ("protected", gdfs["protected"]),
        ("roads", gdfs["roads"]),  # 也可以写个逻辑把它调浅，这里用默认
        ("key_plots", gdfs["key_plots"]),
        ("boundary", boundary)
    ]
    generate_map("重点地段解析图_Focus_Analysis", focus_layers, boundary)

    # 3. 总体语义图底稿 (用地色块 + 建筑轮廓 + 路网 + 水系 + 边界)
    master_layers = [
        ("landuse", gdfs["landuse"]),
        ("water", gdfs["water"]),
        ("buildings_outline", gdfs["buildings"]),
        ("roads", gdfs["roads"]),
        ("boundary", boundary)
    ]
    generate_map("总体语义底稿图_Masterplan_Semantic", master_layers, boundary)
    
    print("\nAll high precision maps generated successfully!")

if __name__ == "__main__":
    main()
