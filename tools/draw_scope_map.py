# tools/draw_scope_map.py
import sys
import os
from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from shapely.geometry import Point
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"
GIS_DIR = ROOT / "data/gis"
ASSETS_DIR = ROOT / "assets"

def draw_spatial_map(output_path):
    print("Loading spatial data layers...")
    
    # 1. Load layers
    boundary_path = GIS_DIR / "Boundary_Scope.geojson"
    water_path = STATIC_DIR / "water.geojson"
    roads_path = STATIC_DIR / "road_clipped.geojson"
    rails_path = STATIC_DIR / "rail_clipped.geojson"
    
    # Try to load buildings from static or data/gis
    buildings_path = STATIC_DIR / "buildings.geojson"
    if not buildings_path.exists():
        buildings_path = GIS_DIR / "Building_Footprints.geojson"
        
    key_plots_path = GIS_DIR / "Key_Plots_District.json"
    
    # Load and project to EPSG:3857 (Web Mercator)
    boundary = gpd.read_file(boundary_path).to_crs(epsg=3857)
    water = gpd.read_file(water_path).to_crs(epsg=3857) if water_path.exists() else None
    roads = gpd.read_file(roads_path).to_crs(epsg=3857) if roads_path.exists() else None
    rails = gpd.read_file(rails_path).to_crs(epsg=3857) if rails_path.exists() else None
    buildings = gpd.read_file(buildings_path).to_crs(epsg=3857) if buildings_path.exists() else None
    key_plots = gpd.read_file(key_plots_path).to_crs(epsg=3857) if key_plots_path.exists() else None

    # Calculate center and bounds
    minx, miny, maxx, maxy = boundary.total_bounds
    cx = (minx + maxx) / 2
    cy = (miny + maxy) / 2
    height_m = maxy - miny
    
    # Target aspect ratio is 1705/1369 = ~1.2454
    view_h = height_m * 1.55
    view_w = view_h * 1.2454

    # 2. Setup figure and axes
    fig, ax = plt.subplots(figsize=(17.05, 13.69), dpi=200, facecolor="#F5F5F7")
    ax.set_facecolor("#F5F5F7")
    
    # Set display bounds
    ax.set_xlim(cx - view_w / 2, cx + view_w / 2)
    ax.set_ylim(cy - view_h / 2, cy + view_h / 2)
    ax.set_axis_off()
    ax.set_aspect("equal")

    # 3. Plot layers with Apple Maps Light style
    # Water layer
    if water is not None and not water.empty:
        water.plot(ax=ax, facecolor="#D0E6F7", edgecolor="none", zorder=1)

    # Buildings layer
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax, facecolor="#FFFFFF", edgecolor="#E5E5E7", linewidth=0.35, zorder=2)

    # Roads layer
    if roads is not None and not roads.empty:
        # Casing for roads to stand out slightly
        for lvl, lw in [(1, 3.5), (2, 2.8), (3, 2.0), (4, 1.4)]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax, color="#EBEBEF", linewidth=lw, zorder=3)
        # Main fill for roads
        for lvl, lw in [(1, 2.5), (2, 1.8), (3, 1.0), (4, 0.6)]:
            sub_gdf = roads[roads['level'] == lvl]
            if not sub_gdf.empty:
                sub_gdf.plot(ax=ax, color="#FFFFFF", linewidth=lw, zorder=4)

    # Rails layer
    if rails is not None and not rails.empty:
        rails.plot(ax=ax, color="#D2D2D7", linewidth=1.0, linestyle=(0, (5, 5)), zorder=5)

    # Key plots
    if key_plots is not None and not key_plots.empty:
        key_plots.plot(ax=ax, facecolor="none", edgecolor="#FF9500", linewidth=1.8, zorder=6)

    # Boundary red line (Apple Red)
    boundary.plot(ax=ax, facecolor="none", edgecolor="#FF3B30", linewidth=2.5, zorder=7)

    # 4. Add text annotations for key landmarks (projecting coordinates from WGS84)
    labels = [
        ("伪满皇宫博物院", 125.3407, 43.9015),
        ("光复路", 125.3475, 43.9017),
        ("伊通河沿岸公园", 125.3530, 43.9010),
        ("长春站", 125.3250, 43.9080),
        ("胜利公园", 125.3260, 43.8960)
    ]
    
    font_prop = {'family': 'sans-serif', 'weight': 'bold', 'size': 12}
    
    # Find system fonts (MS YaHei if available on Windows)
    import matplotlib.font_manager as fm
    sys_fonts = [f.name for f in fm.fontManager.ttflist]
    if "Microsoft YaHei" in sys_fonts:
        font_prop['family'] = "Microsoft YaHei"
    elif "SimHei" in sys_fonts:
        font_prop['family'] = "SimHei"

    for name, lon, lat in labels:
        p = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(epsg=3857)
        px, py = p.iloc[0].x, p.iloc[0].y
        
        # Draw text with white halo/glow effect
        txt = ax.text(px, py, name, color='#1d1d1f', ha='center', va='center', 
                      fontdict=font_prop, zorder=10)
        txt.set_path_effects([path_effects.withStroke(linewidth=3, foreground='#FFFFFF')])

    # Save temporary map image
    plt.savefig(output_path, bbox_inches='tight', pad_inches=0, dpi=200)
    plt.close(fig)
    print(f"Temporary spatial map saved to {output_path}")

def process_a3_layout(map_path, output_path):
    print("Processing A3 layout template...")
    template = Image.open(STATIC_DIR / 'a3_layout_preview.png').convert('RGB')
    map_img = Image.open(map_path).convert('RGB')
    windrose = Image.open(ASSETS_DIR / '长春市风玫瑰.png')
    
    # 1. Resize and paste spatial map
    # Primary drawing area in A3 template: x=183, y=289, w=1705, h=1369
    map_resized = map_img.resize((1705, 1369), Image.Resampling.LANCZOS)
    template.paste(map_resized, (183, 289))
    
    # 2. Clear right side compass box and paste wind rose
    draw = ImageDraw.Draw(template)
    draw.rectangle([1891, 292, 2309, 605], fill=(255, 255, 255))
    
    wr_w, wr_h = windrose.size
    new_h = 200
    new_w = int(new_h * wr_w / wr_h)
    windrose_resized = windrose.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    wx = 1890 + (420 - new_w) // 2
    wy = 291 + 15
    template.paste(windrose_resized, (wx, wy), windrose_resized)
    
    # 3. Draw standard scale bar and text
    font_path = 'C:/Windows/Fonts/msyh.ttc'
    try:
        font_small = ImageFont.truetype(font_path, 14)
        font_title = ImageFont.truetype(font_path, 20)
        font_body = ImageFont.truetype(font_path, 15)
        font_tb = ImageFont.truetype(font_path, 18)
    except IOError:
        font_small = ImageFont.load_default()
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_tb = ImageFont.load_default()
        
    draw.line([(2010, 545), (2190, 545)], fill=(0, 0, 0), width=2)
    draw.line([(2010, 540), (2010, 545)], fill=(0, 0, 0), width=2)
    draw.line([(2190, 540), (2190, 545)], fill=(0, 0, 0), width=2)
    draw.text((2005, 552), "0", fill=(72, 72, 74), font=font_small)
    draw.text((2175, 552), "500m", fill=(72, 72, 74), font=font_small)
    draw.text((2065, 523), "比例尺 1:1000", fill=(72, 72, 74), font=font_small)
    
    # 4. Fill planning description card
    draw.rectangle([184, 1661, 1887, 1815], fill=(248, 250, 252))
    draw.text((210, 1675), "规划说明与设计指标 (Notes & Key Indicators)", fill=(29, 29, 31), font=font_title)
    draw.text((210, 1710), "1. 本图为长春伪满皇宫周边历史街区微更新设计范围图，研究范围约150公顷。本图按照A3标准图纸排版与比例设计规范绘制。", fill=(72, 72, 74), font=font_body)
    draw.text((210, 1738), "2. 规划策略：重点保护历史文化街区完整性，合理置换中车低效工业用地，提升历史风貌街区空间活力。", fill=(72, 72, 74), font=font_body)
    draw.text((210, 1766), "3. 设计指标：规划范围 150 公顷 | 历史风貌保护建筑 28 处 | 新增绿地与口袋公园 12.4 公顷", fill=(72, 72, 74), font=font_body)
    
    # 5. Update title box at bottom right
    draw.rectangle([1900, 1632, 2300, 1664], fill=(241, 245, 249))
    draw.text((1905, 1638), "图纸: 规划研究范围图", fill=(29, 29, 31), font=font_tb)
    
    template.save(output_path)
    print(f"Final A3 scope layout saved to {output_path}")

def main():
    temp_map_path = STATIC_DIR / "temp_drawn_map.png"
    final_output_path = STATIC_DIR / "research_scope_2d.png"
    
    try:
        # Draw spatial map from GIS geojson files
        draw_spatial_map(temp_map_path)
        
        # Merging layout
        process_a3_layout(temp_map_path, final_output_path)
        
    finally:
        # Clean up temporary file
        if temp_map_path.exists():
            os.remove(temp_map_path)
            print("Temporary files cleaned up.")

if __name__ == "__main__":
    main()
