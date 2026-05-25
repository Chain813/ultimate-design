# tools/draw_scope_map.py
import sys
import os
from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from shapely.geometry import Point, box
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"
GIS_DIR = ROOT / "data/gis"
ASSETS_DIR = ROOT / "assets"

def draw_spatial_map(output_path, drawing_type="现状区位图"):
    print(f"Loading spatial data layers for {drawing_type}...")
    
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
    landuse_path = GIS_DIR / "landuse_clipped.geojson"
    
    # Load and project to EPSG:3857 (Web Mercator)
    boundary = gpd.read_file(boundary_path).to_crs(epsg=3857)
    water = gpd.read_file(water_path).to_crs(epsg=3857) if water_path.exists() else None
    roads = gpd.read_file(roads_path).to_crs(epsg=3857) if roads_path.exists() else None
    rails = gpd.read_file(rails_path).to_crs(epsg=3857) if rails_path.exists() else None
    buildings = gpd.read_file(buildings_path).to_crs(epsg=3857) if buildings_path.exists() else None
    key_plots = gpd.read_file(key_plots_path).to_crs(epsg=3857) if key_plots_path.exists() else None
    landuse = gpd.read_file(landuse_path).to_crs(epsg=3857) if landuse_path.exists() else None

    # Calculate center and bounds
    minx, miny, maxx, maxy = boundary.total_bounds
    cx = (minx + maxx) / 2
    cy = (miny + maxy) / 2
    height_m = maxy - miny
    
    # Target aspect ratio is 1705/1369 = ~1.2454
    view_h = height_m * 1.55
    view_w = view_h * 1.2454

    # 2. Setup figure and axes
    fig = plt.figure(figsize=(17.05, 13.69), dpi=200, facecolor="#FAFAFC")
    ax = fig.add_axes([0, 0, 1, 1], facecolor="#FAFAFC")
    
    # Set display bounds
    ax.set_xlim(cx - view_w / 2, cx + view_w / 2)
    ax.set_ylim(cy - view_h / 2, cy + view_h / 2)
    ax.set_axis_off()
    ax.set_aspect("equal")

    # 3. Plot layers based on drawing_type
    if drawing_type == "土地利用现状图":
        # Draw landuse polygons with their native Colors
        if landuse is not None and not landuse.empty:
            for color_hex, sub_df in landuse.groupby('Color'):
                sub_df.plot(ax=ax, facecolor=color_hex, edgecolor="#CBD5E1", linewidth=0.25, zorder=1)
        # Add thin buildings outline for overlay
        if buildings is not None and not buildings.empty:
            buildings.plot(ax=ax, facecolor="none", edgecolor="#475569", linewidth=0.15, alpha=0.3, zorder=2)
        # Water
        if water is not None and not water.empty:
            water.plot(ax=ax, facecolor="#D0E6F7", edgecolor="none", zorder=2.5)
        # Roads (thin lines)
        if roads is not None and not roads.empty:
            roads.plot(ax=ax, color="#E2E8F0", linewidth=0.8, alpha=0.8, zorder=3)
        # Rails
        if rails is not None and not rails.empty:
            rails.plot(ax=ax, color="#64748B", linewidth=1.0, linestyle=(0, (5, 5)), zorder=4)

    elif drawing_type == "道路系统规划图":
        # Draw water and buildings very lightly
        if water is not None and not water.empty:
            water.plot(ax=ax, facecolor="#E8F4FC", edgecolor="none", zorder=1)
        if buildings is not None and not buildings.empty:
            buildings.plot(ax=ax, facecolor="#F1F5F9", edgecolor="#E2E8F0", linewidth=0.2, zorder=2)
        
        # Roads: highlight by level
        if roads is not None and not roads.empty:
            # Casing
            for lvl, lw, color in [(1, 4.5, "#E11D48"), (2, 3.5, "#D97706"), (3, 2.0, "#94A3B8"), (4, 1.2, "#CBD5E1")]:
                sub_gdf = roads[roads['level'] == lvl]
                if not sub_gdf.empty:
                    sub_gdf.plot(ax=ax, color=color, linewidth=lw, zorder=3)
            # Inner fill
            for lvl, lw, color in [(1, 3.0, "#FDA4AF"), (2, 2.2, "#FDE68A"), (3, 1.0, "#F1F5F9"), (4, 0.6, "#FFFFFF")]:
                sub_gdf = roads[roads['level'] == lvl]
                if not sub_gdf.empty:
                    sub_gdf.plot(ax=ax, color=color, linewidth=lw, zorder=4)
        
        # Proposed minor roads / pedestrian streets inside low-efficiency key plots to represent "小街区、密路网"
        if key_plots is not None and not key_plots.empty:
            proposed_lines = []
            from shapely.geometry import LineString
            for geom in key_plots.geometry:
                if geom.is_valid and not geom.is_empty:
                    minx_p, miny_p, maxx_p, maxy_p = geom.bounds
                    cx_p = geom.centroid.x
                    cy_p = geom.centroid.y
                    v_line = LineString([(cx_p, miny_p), (cx_p, maxy_p)])
                    h_line = LineString([(minx_p, cy_p), (maxx_p, cy_p)])
                    for line in [v_line, h_line]:
                        inter = line.intersection(geom)
                        if not inter.is_empty:
                            proposed_lines.append(inter)
            if proposed_lines:
                proposed_gdf = gpd.GeoDataFrame(geometry=proposed_lines, crs=key_plots.crs)
                proposed_gdf.plot(ax=ax, color="#FF2D55", linewidth=2.2, linestyle=(0, (4, 3)), zorder=4.5)
        
        if rails is not None and not rails.empty:
            rails.plot(ax=ax, color="#334155", linewidth=1.5, linestyle=(0, (5, 5)), zorder=5)

    elif drawing_type == "绿地系统规划图":
        # Draw water
        if water is not None and not water.empty:
            water.plot(ax=ax, facecolor="#D0E6F7", edgecolor="none", zorder=1.5)
        # Buildings (light)
        if buildings is not None and not buildings.empty:
            buildings.plot(ax=ax, facecolor="#F8FAFC", edgecolor="#E2E8F0", linewidth=0.2, zorder=1)
        
        # Highlight green spaces from landuse
        if landuse is not None and not landuse.empty:
            green_gdf = landuse[landuse['GB_Code'] == 'G']
            other_gdf = landuse[landuse['GB_Code'] != 'G']
            if not other_gdf.empty:
                other_gdf.plot(ax=ax, facecolor="#F1F5F9", edgecolor="#E2E8F0", linewidth=0.2, zorder=0.8)
            if not green_gdf.empty:
                green_gdf.plot(ax=ax, facecolor="#A7F3D0", edgecolor="#047857", linewidth=0.5, zorder=2)
        
        # Draw proposed new green spaces/parks at the low-efficiency key plots to represent master planning conversion
        if key_plots is not None and not key_plots.empty:
            key_plots.plot(ax=ax, facecolor="#10B981", edgecolor="#047857", linewidth=1.5, alpha=0.9, zorder=2.5)
            
        # Roads (thin lines)
        if roads is not None and not roads.empty:
            roads.plot(ax=ax, color="#E2E8F0", linewidth=0.8, zorder=3)
        # Rails
        if rails is not None and not rails.empty:
            rails.plot(ax=ax, color="#64748B", linewidth=1.0, linestyle=(0, (5, 5)), zorder=4)

    elif drawing_type == "卫星图":
        # Draw satellite base image from static/assets/generated_base/satellite_cropped.png
        sat_path = STATIC_DIR / "assets/generated_base/satellite_cropped.png"
        if sat_path.exists():
            try:
                sat_img = Image.open(sat_path)
                extent = [cx - view_w / 2, cx + view_w / 2, cy - view_h / 2, cy + view_h / 2]
                ax.imshow(sat_img, extent=extent, zorder=0)
            except Exception as e:
                print(f"Error loading satellite image: {e}")
                ax.text(cx, cy, "卫星遥感底图加载失败", ha='center', va='center', fontsize=24, color='#FF3B30')
        else:
            ax.text(cx, cy, "卫星遥感底图未找到", ha='center', va='center', fontsize=24, color='#8E8E93')
        
        # Draw water layer with slight transparency for a blue tint on top of satellite
        if water is not None and not water.empty:
            water.plot(ax=ax, facecolor="#0066CC", edgecolor="none", alpha=0.35, zorder=1.5)

    elif drawing_type == "交通分析图":
        # Draw water and buildings outline lightly
        if water is not None and not water.empty:
            water.plot(ax=ax, facecolor="#D0E6F7", edgecolor="none", zorder=1.5)
        if buildings is not None and not buildings.empty:
            buildings.plot(ax=ax, facecolor="none", edgecolor="#475569", linewidth=0.15, alpha=0.3, zorder=1)
        
        # Roads: high-contrast blue thematic colors for transport networks
        if roads is not None and not roads.empty:
            # Casing
            for lvl, lw, color in [(1, 4.5, "#1E3A8A"), (2, 3.5, "#2563EB"), (3, 2.0, "#60A5FA"), (4, 1.2, "#93C5FD")]:
                sub_gdf = roads[roads['level'] == lvl]
                if not sub_gdf.empty:
                    sub_gdf.plot(ax=ax, color=color, linewidth=lw, zorder=3)
            # Inner fill
            for lvl, lw, color in [(1, 3.0, "#3B82F6"), (2, 2.2, "#60A5FA"), (3, 1.0, "#EFF6FF"), (4, 0.6, "#FFFFFF")]:
                sub_gdf = roads[roads['level'] == lvl]
                if not sub_gdf.empty:
                    sub_gdf.plot(ax=ax, color=color, linewidth=lw, zorder=4)
        
        # Rails
        if rails is not None and not rails.empty:
            rails.plot(ax=ax, color="#1E293B", linewidth=1.8, linestyle=(0, (5, 5)), zorder=5)

    elif drawing_type == "历史建筑与工业遗产分布图":
        # Draw water and roads
        if water is not None and not water.empty:
            water.plot(ax=ax, facecolor="#D0E6F7", edgecolor="none", zorder=1.5)
        # Normal buildings: very light grey
        if buildings is not None and not buildings.empty:
            buildings.plot(ax=ax, facecolor="#F1F5F9", edgecolor="#E2E8F0", linewidth=0.2, zorder=1)
        
        # Protected buildings (heritage)
        prot_path = STATIC_DIR / "protected_buildings.geojson"
        if prot_path.exists():
            try:
                protected = gpd.read_file(prot_path).to_crs(epsg=3857)
                protected.plot(ax=ax, facecolor="#D97706", edgecolor="#B45309", linewidth=0.5, alpha=0.9, zorder=2.2)
            except Exception as e:
                print(f"Error loading protected buildings: {e}")
        
        # Roads (thin lines)
        if roads is not None and not roads.empty:
            roads.plot(ax=ax, color="#CBD5E1", linewidth=0.8, zorder=3)
        # Rails
        if rails is not None and not rails.empty:
            rails.plot(ax=ax, color="#64748B", linewidth=1.0, linestyle=(0, (5, 5)), zorder=4)

    elif drawing_type == "建筑高度现状图":
        # Draw water
        if water is not None and not water.empty:
            water.plot(ax=ax, facecolor="#D0E6F7", edgecolor="none", zorder=1.5)
        
        # Color building footprints by Floor
        if buildings is not None and not buildings.empty:
            buildings_copy = buildings.copy()
            # Ensure Floor is numeric
            buildings_copy["Floor_num"] = pd.to_numeric(buildings_copy["Floor"], errors="coerce").fillna(1)
            
            # Create a color column
            conditions = [
                (buildings_copy["Floor_num"] <= 3),
                (buildings_copy["Floor_num"] >= 4) & (buildings_copy["Floor_num"] <= 7),
                (buildings_copy["Floor_num"] >= 8) & (buildings_copy["Floor_num"] <= 14),
                (buildings_copy["Floor_num"] >= 15) & (buildings_copy["Floor_num"] <= 20),
                (buildings_copy["Floor_num"] >= 21)
            ]
            choices = [
                "#FDE68A", # 1-3层: 黄
                "#F97316", # 4-7层: 橙
                "#EF4444", # 8-14层: 红
                "#B91C1C", # 15-20层: 深红
                "#7F1D1D"  # 21+层: 褐红
            ]
            buildings_copy["color"] = np.select(conditions, choices, default="#FDE68A")
            
            # Plot the buildings with their color
            buildings_copy.plot(ax=ax, color=buildings_copy["color"], edgecolor="#475569", linewidth=0.15, zorder=2)
            
        # Roads (thin lines)
        if roads is not None and not roads.empty:
            roads.plot(ax=ax, color="#CBD5E1", linewidth=0.8, zorder=3)
        # Rails
        if rails is not None and not rails.empty:
            rails.plot(ax=ax, color="#64748B", linewidth=1.0, linestyle=(0, (5, 5)), zorder=4)

    elif drawing_type == "建筑风貌现状图":
        # Draw water
        if water is not None and not water.empty:
            water.plot(ax=ax, facecolor="#D0E6F7", edgecolor="none", zorder=1.5)
        
        # Color building footprints by prop_style
        if buildings is not None and not buildings.empty:
            buildings_copy = buildings.copy()
            conditions = [
                (buildings_copy["prop_style"] == "historical"),
                (buildings_copy["prop_style"] == "park"),
                (buildings_copy["prop_style"] == "normal") | (buildings_copy["prop_style"].isna())
            ]
            choices = [
                "#B45309", # historical: 历史保护风貌 (古铜/褐金)
                "#0F766E", # park: 附属景观风貌 (青绿)
                "#E2E8F0"  # normal: 现代普通风貌 (浅灰)
            ]
            buildings_copy["color"] = np.select(conditions, choices, default="#E2E8F0")
            
            # Plot
            buildings_copy.plot(ax=ax, color=buildings_copy["color"], edgecolor="#475569", linewidth=0.15, zorder=2)
            
        # Roads (thin lines)
        if roads is not None and not roads.empty:
            roads.plot(ax=ax, color="#CBD5E1", linewidth=0.8, zorder=3)
        # Rails
        if rails is not None and not rails.empty:
            rails.plot(ax=ax, color="#64748B", linewidth=1.0, linestyle=(0, (5, 5)), zorder=4)

    else:
        # Default: 现状区位图 (Location Map)
        if water is not None and not water.empty:
            water.plot(ax=ax, facecolor="#D0E6F7", edgecolor="none", zorder=1)
        if buildings is not None and not buildings.empty:
            buildings.plot(ax=ax, facecolor="#FFFFFF", edgecolor="#E5E5E7", linewidth=0.35, zorder=2)
        if roads is not None and not roads.empty:
            for lvl, lw in [(1, 3.8), (2, 3.0), (3, 2.2), (4, 1.6)]:
                sub_gdf = roads[roads['level'] == lvl]
                if not sub_gdf.empty:
                    sub_gdf.plot(ax=ax, color="#C7C7CC", linewidth=lw, zorder=3)
            for lvl, lw in [(1, 2.6), (2, 2.0), (3, 1.2), (4, 0.8)]:
                sub_gdf = roads[roads['level'] == lvl]
                if not sub_gdf.empty:
                    sub_gdf.plot(ax=ax, color="#E5E5EA", linewidth=lw, zorder=4)
        if rails is not None and not rails.empty:
            rails.plot(ax=ax, color="#48484A", linewidth=1.5, linestyle=(0, (5, 5)), zorder=5)

    # Boundary red line (Apple Red)
    boundary.plot(ax=ax, facecolor="none", edgecolor="#FF3B30", linewidth=2.0, zorder=7.0)

    # 4. Add text annotations for key landmarks
    if drawing_type in ["现状区位图", "土地利用现状图", "卫星图", "交通分析图", "历史建筑与工业遗产分布图", "建筑高度现状图", "建筑风貌现状图"]:
        labels = [
            ("伪满皇宫博物院", 125.3422, 43.9036),
            ("光复路", 125.3475, 43.9017),
            ("伊通河沿岸公园", 125.3590, 43.9010),
            ("长春站", 125.3250, 43.9080),
            ("胜利公园", 125.3260, 43.8960)
        ]
        
        font_prop = {'family': 'sans-serif', 'weight': 'bold', 'size': 16}
        import matplotlib.font_manager as fm
        sys_fonts = [f.name for f in fm.fontManager.ttflist]
        if "Microsoft YaHei" in sys_fonts:
            font_prop['family'] = "Microsoft YaHei"
        elif "SimHei" in sys_fonts:
            font_prop['family'] = "SimHei"

        for name, lon, lat in labels:
            p = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(epsg=3857)
            px, py = p.iloc[0].x, p.iloc[0].y
            ax.plot(px, py, marker='o', markersize=10, color='#FF9500', markeredgecolor='#FFFFFF', markeredgewidth=2.0, zorder=9)
            py_text = py + 70
            txt = ax.text(px, py_text, name, color='#1d1d1f', ha='center', va='bottom', 
                          fontdict=font_prop, zorder=10)
            txt.set_path_effects([path_effects.withStroke(linewidth=3, foreground='#FFFFFF')])

    # Save temporary map image
    plt.savefig(output_path, dpi=200)
    plt.close(fig)
    print(f"Temporary spatial map saved to {output_path}")
    return view_w

def draw_centered_text(draw, text, cx, cy, fill, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text((cx - w // 2, cy - h // 2), text, fill=fill, font=font)

def process_a3_layout(map_path, output_path, view_w, drawing_type="现状区位图", title="现状区位图", description_lines=None, drawing_number="DR-001", author="陈礼冲", author_id="202111003", organization="吉林建筑大学建筑与规划学院\n城乡规划211班"):
    print("Processing A3 layout template...")
    template = Image.open(STATIC_DIR / 'a3_layout_preview_full.png').convert('RGB')
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
    
    # 3. Fonts loading
    font_path = 'C:/Windows/Fonts/msyh.ttc'
    try:
        font_small = ImageFont.truetype(font_path, 18)
        font_title = ImageFont.truetype(font_path, 28)
        font_body = ImageFont.truetype(font_path, 18)
        font_tb = ImageFont.truetype(font_path, 24)
    except IOError:
        font_small = ImageFont.load_default()
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_tb = ImageFont.load_default()
        
    # 4. Draw dynamic scale bar
    m_per_px = view_w / 1705
    scale_bar_px = int(round(500 / m_per_px))
    x_start = 2101 - scale_bar_px // 2
    x_end = 2101 + scale_bar_px // 2
    
    draw.line([(x_start, 545), (x_end, 545)], fill=(0, 0, 0), width=2)
    draw.line([(x_start, 540), (x_start, 545)], fill=(0, 0, 0), width=2)
    draw.line([(x_end, 540), (x_end, 545)], fill=(0, 0, 0), width=2)
    draw.text((x_start - 5, 555), "0", fill=(72, 72, 74), font=font_small)
    draw.text((x_end - 20, 555), "500m", fill=(72, 72, 74), font=font_small)
    
    scale_ratio = view_w / 0.31968
    scale_rounded = int(round(scale_ratio / 500)) * 500
    scale_text = f"比例尺 1:{scale_rounded}"
    bbox_scale = draw.textbbox((0, 0), scale_text, font=font_small)
    w_scale = bbox_scale[2] - bbox_scale[0]
    draw.text((2101 - w_scale // 2, 515), scale_text, fill=(72, 72, 74), font=font_small)
    
    # 5. Clear and Redraw Legend section [1890, 608, 2312, 1390]
    draw.rectangle([1891, 608, 2309, 1390], fill=(255, 255, 255))
    
    # Title "图例"
    draw_centered_text(draw, "图    例", 2101, 640, (15, 23, 42), font_title)
    draw.line([(1910, 665), (2290, 665)], fill=(203, 213, 225), width=1)
    
    # Legend Items based on drawing_type
    if drawing_type == "土地利用现状图":
        legend_items = [
            ("规划研究范围", "rect_red_border"),
            ("居住用地 (R)", "rect_euluc_0"),
            ("商业办公 (B)", "rect_euluc_1"),
            ("商业服务业 (B)", "rect_euluc_2"),
            ("工业用地 (M)", "rect_euluc_3"),
            ("交通场站 (S)", "rect_euluc_4"),
            ("机场设施 (S)", "rect_euluc_5"),
            ("行政办公 (A)", "rect_euluc_6"),
            ("教育科研 (A)", "rect_euluc_7"),
            ("医疗卫生 (A)", "rect_euluc_8"),
            ("体育文化 (A)", "rect_euluc_9"),
            ("公园与绿地 (G)", "rect_euluc_10")
        ]
    elif drawing_type == "道路系统规划图":
        legend_items = [
            ("规划研究范围", "rect_red_border"),
            ("规划建议道路/步行街", "line_proposed_road"),
            ("现状城市主干路", "line_primary_road"),
            ("现状城市次干路", "line_secondary_road"),
            ("现状城市支路", "line_tertiary_road"),
            ("现状铁路", "line_rail"),
        ]
    elif drawing_type == "绿地系统规划图":
        legend_items = [
            ("规划研究范围", "rect_red_border"),
            ("规划新增绿地/广场", "rect_green_planned"),
            ("现状公园绿地", "rect_green"),
            ("城市水系", "rect_water"),
            ("城市道路", "rect_road"),
            ("现状建筑", "rect_building")
        ]
    elif drawing_type == "卫星图":
        legend_items = [
            ("规划研究范围", "rect_red_border"),
            ("重点更新地块", "rect_orange_border"),
            ("伊通河水系", "rect_water"),
            ("卫星遥感影像", "rect_sat_base")
        ]
    elif drawing_type == "交通分析图":
        legend_items = [
            ("规划研究范围", "rect_red_border"),
            ("城市主干路", "line_primary_road_blue"),
            ("城市次干路", "line_secondary_road_blue"),
            ("城市支路", "line_tertiary_road_blue"),
            ("现状铁路线", "line_rail"),
            ("现状建筑轮廓", "rect_building_outline"),
        ]
    elif drawing_type == "历史建筑与工业遗产分布图":
        legend_items = [
            ("规划研究范围", "rect_red_border"),
            ("重点历史/工业遗产建筑", "rect_heritage"),
            ("现状普通建筑", "rect_building_light"),
            ("城市水系", "rect_water"),
            ("城市道路", "rect_road"),
            ("现状铁路线", "line_rail")
        ]
    elif drawing_type == "建筑高度现状图":
        legend_items = [
            ("规划研究范围", "rect_red_border"),
            ("低层建筑 (1-3 层)", "rect_h1"),
            ("多层建筑 (4-7 层)", "rect_h2"),
            ("中高层建筑 (8-14 层)", "rect_h3"),
            ("高层建筑 (15-20 层)", "rect_h4"),
            ("超高层建筑 (21层以上)", "rect_h5"),
            ("城市水系", "rect_water"),
            ("城市道路", "rect_road"),
        ]
    elif drawing_type == "建筑风貌现状图":
        legend_items = [
            ("规划研究范围", "rect_red_border"),
            ("历史保护风貌建筑", "rect_style_hist"),
            ("公建及附属景观风貌", "rect_style_park"),
            ("普通住宅与现代风貌", "rect_style_norm"),
            ("城市水系", "rect_water"),
            ("城市道路", "rect_road"),
        ]
    else:
        # Default: 现状区位图 (Location Map)
        legend_items = [
            ("规划研究范围", "rect_red_border"),
            ("重点更新地块", "rect_orange_border"),
            ("现状建筑", "rect_building"),
            ("城市水系 (伊通河等)", "rect_water"),
            ("现状铁路 (京哈线等)", "line_rail"),
            ("城市道路", "rect_road")
        ]
    
    y = 690
    spacing = 38 if len(legend_items) > 8 else 45
    for label, style in legend_items:
        if style == "rect_red_border":
            draw.rectangle([1915, y, 1950, y+18], fill=(255, 255, 255), outline=(255, 59, 48), width=3)
        elif style == "rect_orange_border":
            draw.rectangle([1915, y, 1950, y+18], fill=(255, 245, 230), outline=(255, 149, 0), width=2)
        elif style == "rect_building":
            draw.rectangle([1915, y, 1950, y+18], fill=(255, 255, 255), outline=(229, 229, 231), width=1)
        elif style == "rect_water":
            draw.rectangle([1915, y, 1950, y+18], fill=(208, 230, 247), outline=(180, 200, 220), width=1)
        elif style == "line_rail":
            draw.line([(1915, y+9), (1927, y+9)], fill=(72, 72, 74), width=2)
            draw.line([(1932, y+9), (1943, y+9)], fill=(72, 72, 74), width=2)
            draw.line([(1948, y+9), (1950, y+9)], fill=(72, 72, 74), width=2)
        elif style == "rect_road":
            draw.rectangle([1915, y, 1950, y+18], fill=(229, 229, 234), outline=(199, 199, 204), width=1)
        elif style == "rect_euluc_0":
            draw.rectangle([1915, y, 1950, y+18], fill=(255, 255, 0), outline=(203, 213, 225), width=1)
        elif style == "rect_euluc_1":
            draw.rectangle([1915, y, 1950, y+18], fill=(230, 0, 0), outline=(203, 213, 225), width=1)
        elif style == "rect_euluc_2":
            draw.rectangle([1915, y, 1950, y+18], fill=(255, 127, 0), outline=(203, 213, 225), width=1)
        elif style == "rect_euluc_3":
            draw.rectangle([1915, y, 1950, y+18], fill=(170, 120, 85), outline=(203, 213, 225), width=1)
        elif style == "rect_euluc_4":
            draw.rectangle([1915, y, 1950, y+18], fill=(156, 156, 156), outline=(203, 213, 225), width=1)
        elif style == "rect_euluc_5":
            draw.rectangle([1915, y, 1950, y+18], fill=(104, 104, 104), outline=(203, 213, 225), width=1)
        elif style == "rect_euluc_6":
            draw.rectangle([1915, y, 1950, y+18], fill=(255, 127, 127), outline=(203, 213, 225), width=1)
        elif style == "rect_euluc_7":
            draw.rectangle([1915, y, 1950, y+18], fill=(255, 127, 255), outline=(203, 213, 225), width=1)
        elif style == "rect_euluc_8":
            draw.rectangle([1915, y, 1950, y+18], fill=(255, 127, 191), outline=(203, 213, 225), width=1)
        elif style == "rect_euluc_9":
            draw.rectangle([1915, y, 1950, y+18], fill=(127, 255, 255), outline=(203, 213, 225), width=1)
        elif style == "rect_euluc_10":
            draw.rectangle([1915, y, 1950, y+18], fill=(56, 168, 0), outline=(203, 213, 225), width=1)
        elif style == "line_proposed_road":
            draw.rectangle([1915, y, 1950, y+18], fill=(255, 230, 230), outline=(255, 45, 85), width=2)
            draw.line([(1915, y+9), (1950, y+9)], fill=(255, 45, 85), width=1)
        elif style == "rect_green_planned":
            draw.rectangle([1915, y, 1950, y+18], fill=(16, 185, 129), outline=(4, 120, 87), width=1)
        elif style == "line_primary_road":
            draw.rectangle([1915, y, 1950, y+18], fill=(253, 164, 189), outline=(225, 29, 72), width=2)
        elif style == "line_secondary_road":
            draw.rectangle([1915, y, 1950, y+18], fill=(253, 230, 138), outline=(217, 119, 6), width=2)
        elif style == "line_tertiary_road":
            draw.rectangle([1915, y, 1950, y+18], fill=(241, 245, 249), outline=(148, 163, 184), width=1)
        elif style == "rect_sat_base":
            draw.rectangle([1915, y, 1950, y+18], fill=(34, 76, 56), outline=(203, 213, 225), width=1)
        elif style == "rect_building_outline":
            draw.rectangle([1915, y, 1950, y+18], fill=(255, 255, 255), outline=(71, 85, 105), width=1)
        elif style == "line_primary_road_blue":
            draw.rectangle([1915, y, 1950, y+18], fill=(96, 165, 250), outline=(30, 58, 138), width=2)
        elif style == "line_secondary_road_blue":
            draw.rectangle([1915, y, 1950, y+18], fill=(147, 197, 253), outline=(37, 99, 235), width=2)
        elif style == "line_tertiary_road_blue":
            draw.rectangle([1915, y, 1950, y+18], fill=(239, 246, 255), outline=(96, 165, 250), width=1)
        elif style == "rect_heritage":
            draw.rectangle([1915, y, 1950, y+18], fill=(217, 119, 6), outline=(180, 83, 9), width=1)
        elif style == "rect_building_light":
            draw.rectangle([1915, y, 1950, y+18], fill=(241, 245, 249), outline=(226, 232, 240), width=1)
        elif style == "rect_h1":
            draw.rectangle([1915, y, 1950, y+18], fill=(253, 230, 138), outline=(217, 119, 6), width=1)
        elif style == "rect_h2":
            draw.rectangle([1915, y, 1950, y+18], fill=(249, 115, 22), outline=(194, 65, 12), width=1)
        elif style == "rect_h3":
            draw.rectangle([1915, y, 1950, y+18], fill=(239, 68, 68), outline=(185, 28, 28), width=1)
        elif style == "rect_h4":
            draw.rectangle([1915, y, 1950, y+18], fill=(185, 28, 28), outline=(153, 27, 27), width=1)
        elif style == "rect_h5":
            draw.rectangle([1915, y, 1950, y+18], fill=(127, 29, 29), outline=(127, 29, 29), width=1)
        elif style == "rect_style_hist":
            draw.rectangle([1915, y, 1950, y+18], fill=(180, 83, 9), outline=(146, 64, 14), width=1)
        elif style == "rect_style_park":
            draw.rectangle([1915, y, 1950, y+18], fill=(15, 118, 110), outline=(13, 148, 136), width=1)
        elif style == "rect_style_norm":
            draw.rectangle([1915, y, 1950, y+18], fill=(226, 232, 240), outline=(203, 213, 225), width=1)
        
        draw.text((1965, y), label, fill=(29, 29, 31), font=font_body)
        y += spacing
    # 6. Fill planning description card
    draw.rectangle([184, 1661, 1887, 1815], fill=(248, 250, 252))
    draw.text((210, 1670), "设计说明与规划指标 (Design Notes & Planning Indicators)", fill=(29, 29, 31), font=font_title)
    
    if not description_lines:
        if drawing_type == "土地利用现状图":
            description_lines = [
                "1. 用地构成：项目区内以居住用地（R）和商业服务业设施用地（B）为主，主要分布在亚泰大街及长通路两侧。工业与仓储用地占比较低且多属需更新工业遗存。",
                "2. 混合利用：规划提倡在轨道站点及重点更新地段发展商住混合、文创混合等多功能混合用地（M），以提升地块经济与社会活力。",
                "3. 用地优化：通过盘活现状低效建设用地，增加公共服务设施用地（A）和绿地与广场用地（G），改善居民 15 分钟生活圈的公共服务供给与空间品质。"
            ]
        elif drawing_type == "道路系统规划图":
            description_lines = [
                "1. 路网骨架：规划形成“三横三纵”的城市主次干路网骨架，提升地块对外的交通联系和连通度，实现内外交通的顺畅转换。",
                "2. 慢行慢游：加密内部支路网，优化慢行步道，提升街区可达性，建立对行人与自行车慢行友好的漫游系统，打通微循环瓶颈。",
                "3. TOD 开发：紧邻长春火车站与轨道交通站点，规划强化 TOD 交通枢纽的辐射带动作用，引导高密度、功能混合的公共交通导向型开发。"
            ]
        elif drawing_type == "绿地系统规划图":
            description_lines = [
                "1. 生态骨架：以东侧伊通河滨水生态廊道为生态基底，向街区内部延伸多条绿色触角，构建“一廊多点”的生态空间格局。",
                "2. 公园绿地：规划多处社区公园、口袋公园与街头绿地，确保街区内居民实现“300米见绿、500米见园”的生态生活目标。",
                "3. 蓝绿交织：整合水系边缘与道路绿化带，增加透水铺装与雨水花园，构建海绵城市雨洪管理系统，兼具景观美学与生态韧性。"
            ]
        elif drawing_type == "卫星图":
            description_lines = [
                "1. 遥感影像：本图底图采用高分辨率 Google Earth 卫星遥感影像（2024年最新数据），直观反映项目所在长春市宽城区伪满皇宫周边区域的真实地表覆盖与建筑空间密度。",
                "2. 蓝绿肌理：东侧伊通河生态廊道水体形态完整，但街区内部绿色开敞空间较少，植被覆盖主要呈线性分布在铁路线及道路两侧，亟需引入更多社区口袋公园。",
                "3. 建设状况：街区内现状以中低层高密度建筑群为主，东北侧存在大面积中车低效工业遗存与厂房，南侧及西侧以商旧住宅为主，空间肌理较为拥挤。"
            ]
        elif drawing_type == "历史建筑与工业遗产分布图":
            description_lines = [
                "1. 遗产识别：片区内包含以伪满皇宫为核心的近代历史建筑群，以及东北侧中车长客厂区的大跨度工业厂房和铁轨遗存，是复合型城市遗产的关键载体。",
                "2. 价值评估：历史风貌核心保护区与中车厂区具有极高的建筑质量和空间识别度，是本次更新设计中严格执行“保留与修缮”的刚性管控区域。",
                "3. 活化思路：保护传统街区肌理与风貌界面的连续性，打通历史文化展示游线，将工业遗存置换为文创、博览和青年双创等活力复合功能。"
            ]
        elif drawing_type == "交通分析图":
            description_lines = [
                "1. 骨架路网：规划区内以亚泰大街快速路和长通路、凯旋路为主干路网，南北向贯穿良好，但高架道路对两侧街区存在一定的物理与视线割裂作用。",
                "2. 铁路线路：北部京哈铁路横穿，对地块形成严重的南北向交通阻隔。规划建议在更新改造中，增设跨铁人行天桥或地下通道以缝合城市南北片区。",
                "3. 慢行慢游：现状支路网密度偏低且不成系统，慢行体验较差。规划提出通过微循环道路改造和TOD联动，构建高品质、步行友好的慢游交通环线。"
            ]
        elif drawing_type == "建筑高度现状图":
            description_lines = [
                "1. 高度特征：区内建筑以低层（1-3层）和多层（4-7层）为主，集中分布在历史街区内部和老旧社区，空间肌理紧凑，尺度宜人。",
                "2. 高层分布：中高层与高层住宅主要零散分布在区位外围，对历史街区核心区及伪满皇宫周边产生了一定的视线廊道压力。",
                "3. 管控思路：规划提出结合视线敏感度分析，严格控制核心区新建建筑高度，禁止插建高层，保留历史空间原有的舒缓天际线。"
            ]
        elif drawing_type == "建筑风貌现状图":
            description_lines = [
                "1. 风貌构成：区内历史保护风貌占比约3.2%，集中在伪满皇宫周边；普通居住风貌占主导，整体风貌协调度有待提升。",
                "2. 界面杂乱：局部街区存在杂乱搭接及立面风貌破损，严重削弱了历史文化街区的空间质量与文化氛围，缺乏统一的导则引导。",
                "3. 整治策略：实行分类整治，对历史建筑修缮复原，对普通住宅立面进行微改造协调，消除风貌冲突，营造和谐的历史共振街区。"
            ]
        else:
            # 现状区位图 (Location Map)
            description_lines = [
                "1. 地理区位：本项目位于吉林省长春市宽城区历史文化核心街区，紧邻长春火车站与伪满皇宫博物院，是连接历史风貌区与现代城市中心的关键枢纽地带。",
                "2. 规划范围：规划研究范围东至伊通河、西至亚泰大街、南至长通路、北至京哈铁路，总规划研究面积约150公顷。包含5大重点更新地块。",
                "3. 指标现状：核心区现状路网密度6.2km/km²，建筑密度42%，水绿覆盖率约12.4%。规划定位为“数字孪生·古今共振”的历史风貌与双创活力街区。"
            ]
            
    y_desc = 1712
    for line in description_lines[:3]:
        draw.text((210, y_desc), line, fill=(72, 72, 74), font=font_body)
        y_desc += 36
        
    # 7. Redraw the entire Title Block [1890, 1394, 2312, 1816]
    draw.rectangle([1890, 1394, 2312, 1816], fill=(241, 245, 249), outline=(15, 23, 42), width=2)
    
    # Grid lines inside the stamp
    draw.line([(1890, 1464), (2312, 1464)], fill=(15, 23, 42), width=1)
    draw.line([(1890, 1564), (2312, 1564)], fill=(15, 23, 42), width=1)
    draw.line([(1890, 1664), (2312, 1664)], fill=(15, 23, 42), width=1)
    draw.line([(2090, 1664), (2090, 1816)], fill=(15, 23, 42), width=1) # vertical split
    
    # Fonts for the stamp
    try:
        font_stamp_large = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 26) # Bold YaHei
    except IOError:
        try:
            font_stamp_large = ImageFont.truetype(font_path, 26)
        except IOError:
            font_stamp_large = ImageFont.load_default()
            
    try:
        font_stamp_title = ImageFont.truetype(font_path, 20)
        font_stamp_body = ImageFont.truetype(font_path, 15)
        font_stamp_label = ImageFont.truetype(font_path, 12)
    except IOError:
        font_stamp_title = ImageFont.load_default()
        font_stamp_body = ImageFont.load_default()
        font_stamp_label = ImageFont.load_default()
        
    # Title
    bbox_title = draw.textbbox((0, 0), title, font=font_stamp_large)
    title_h = bbox_title[3] - bbox_title[1]
    title_y = 1429 - title_h // 2
    draw.text((1905, title_y), title, fill=(15, 23, 42), font=font_stamp_large)
    
    # Project Name (Fixed as requested)
    draw.text((1905, 1472), "项目名称 / PROJECT", fill=(120, 120, 125), font=font_stamp_label)
    draw.text((1905, 1494), "数字孪生·古今共振——", fill=(15, 23, 42), font=font_stamp_body)
    draw.text((1905, 1524), "AI赋能下的伪满皇宫周边街区更新规划设计", fill=(15, 23, 42), font=font_stamp_body)
    
    # Unit/Class
    draw.text((1905, 1572), "学校班级 / ORGANIZATION", fill=(120, 120, 125), font=font_stamp_label)
    org_lines = organization.split('\n')
    org_y = 1594
    for ol in org_lines[:2]:
        draw.text((1905, org_y), ol, fill=(15, 23, 42), font=font_stamp_body)
        org_y += 30
    
    # Author & ID
    draw.text((1905, 1674), "制作人 / AUTHOR", fill=(120, 120, 125), font=font_stamp_label)
    draw.text((1905, 1710), author, fill=(15, 23, 42), font=font_stamp_title)
    
    draw.text((2105, 1674), "学号 / ID", fill=(120, 120, 125), font=font_stamp_label)
    draw.text((2105, 1710), author_id, fill=(15, 23, 42), font=font_stamp_body)
    
    # 8. Save cropped homepage banner image from primary map area (if default Location Map)
    if drawing_type == "现状区位图" and title == "现状区位图":
        homepage_banner_img = template.crop((183, 289, 1888, 1658))
        cropped_banner_path = STATIC_DIR / "research_scope_2d_cropped.png"
        homepage_banner_img.save(cropped_banner_path)
        print(f"Homepage banner cropped image saved to {cropped_banner_path}")
    
    # 9. Crop the paper frame of the drawing template: [100, 260, 2340, 1844]
    # This crops out the outer white edges and the top specification description title
    paper_frame = template.crop((100, 260, 2340, 1844))
    
    # Save output A3 sheet
    paper_frame.save(output_path)
    print(f"Final A3 scope layout saved to {output_path} (Dimensions: {paper_frame.size}, cropped to paper boundary)")

def main():
    temp_map_path = STATIC_DIR / "temp_drawn_map.png"
    final_output_path = STATIC_DIR / "research_scope_2d.png"
    
    try:
        # Draw spatial map from GIS geojson files
        view_w = draw_spatial_map(temp_map_path, drawing_type="现状区位图")
        
        # Merging layout
        process_a3_layout(temp_map_path, final_output_path, view_w, drawing_type="现状区位图", title="现状区位图")
        
    finally:
        # Clean up temporary file
        if temp_map_path.exists():
            os.remove(temp_map_path)
            print("Temporary files cleaned up.")

if __name__ == "__main__":
    main()
