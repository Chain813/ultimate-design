# -*- coding: utf-8 -*-
import os
from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patheffects as path_effects
import matplotlib.patches as mpatches
from shapely.geometry import Point
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"
GIS_DIR = ROOT / "data/gis"
ASSETS_DIR = ROOT / "assets"

NO_FRAME = True

# Five key parcels information
PARCEL_INFO = {
    0: {
        "key": "老水产市场",
        "name": "老水产批发市场",
        "title": "御花园东巷文创街区",
        "area": "3.71",
        "desc_base": "老水产批发市场地块改造以“文创街区”为核心。通过对低效水产市场进行微改造，注入艺术零售、创意市集和口袋公园等，提升空间活力。"
    },
    1: {
        "key": "食品调料市场",
        "name": "食品调料大市场",
        "title": "活态市集·风味院落",
        "area": "16.83",
        "desc_base": "食品调料大市场地块体量庞大，规划聚焦于“活态市集与风味院落”。整合工业厂房与调料大棚遗存，形成独具风味的历史文创消费街区。"
    },
    2: {
        "key": "市一中北侧",
        "name": "市一中北侧",
        "title": "全龄共享生活社区",
        "area": "2.78",
        "desc_base": "市一中北侧地块定位于“全龄共享生活社区”。改造侧重于老旧小区服务短板修补，完善适老与托育公共配套，营造共享开敞绿地空间。"
    },
    3: {
        "key": "清禾集贸市场",
        "name": "清禾集贸市场",
        "title": "历史界面缝合者",
        "area": "2.47",
        "desc_base": "清禾集贸市场地块以“历史界面缝合者”为理念。缝合铁路与主干道带来的空间割裂，梳理人行游线，重构开放连通的城市公共交往节点。"
    },
    4: {
        "key": "中国石油",
        "name": "中国石油",
        "title": "宽城子能量花园",
        "area": "1.30",
        "desc_base": "中国石油地块设计为“宽城子能量花园”。重点整治加油站周边低效闲置零星空地，植入绿色生态缓冲屏障与运动空间，改善滨河风貌。"
    }
}

ANALYSIS_INFO = {
    "satellite": {
        "title_suffix": "现状卫星图",
        "sub": "遥感数据底图",
        "accent": "#0D9488",  # Teal
        "desc_1": "1. 遥感影像反映场地现状生态绿化较差，内部硬质地表占比高，大跨度工业大棚与仓储设施痕迹清晰可见。",
        "desc_2": "2. 场地贴邻铁路或主要交通干道，内部机动车路网密度较低，大部分空间被低能级建筑或闲置空地覆盖。",
        "desc_3": "3. 影像表明场地内部绿化断续，未与东侧伊通河生态走廊建立连贯性，周边景观风貌缺乏系统设计与织补。"
    },
    "landuse": {
        "title_suffix": "现状土地利用",
        "sub": "土地现状利用及功能分析",
        "accent": "#D97706",  # Gold
        "desc_1": "1. 土地现状主要为低效商业仓储用地及零星工业厂房设施，土地性质单一且与周边居住环境品质冲突。",
        "desc_2": "2. 现状地块开发强度较高但产出能级低下，缺乏社区级文体、卫生等公共管理与服务配套，未能发挥区位价值。",
        "desc_3": "3. 周边道路交通路网等级单一，地块与主要客流节点的连通性较弱，需要进行用地性质优化以增强混合度。"
    },
    "fabric": {
        "title_suffix": "现状肌理",
        "sub": "现状建筑风貌与肌理识别",
        "accent": "#4F46E5",  # Indigo
        "desc_1": "1. 风貌识别显示场地以普通现代和临时搭建建筑为主，缺乏系统风貌控制导则，空间界面杂乱零碎。",
        "desc_2": "2. 场地保留有反映工业历史时期特点的厂房遗存与风貌特征，可通过保护性改造与活化实现古今交融。",
        "desc_3": "3. 街区内部巷道尺度过窄，视线廊道受到杂乱建筑阻挡，建议实行分类整治与立面微改造策略。"
    },
    "height": {
        "title_suffix": "现状建筑高度",
        "sub": "建筑现状高度及层数控制",
        "accent": "#EF4444",  # Red
        "desc_1": "1. 建筑层数整体以1-3层低层建筑为主，占据了地块的核心区域，建筑密度大且容积率分布不均。",
        "desc_2": "2. 局部外围建有少量多层及中高层建筑，天际线形态整体平缓单调，缺乏标志性的空间高潮与视廊引导。",
        "desc_3": "3. 现状低矮建筑多为低效钢结构大棚或临时库房，后续更新应严格控制建筑高度，维持历史风貌敏感度。"
    },
    "business": {
        "title_suffix": "现状业态分区",
        "sub": "POI现状产业集聚与活力分析",
        "accent": "#8B5CF6",  # Purple
        "desc_1": "1. 业态基底呈传统生存型特征，餐饮与基础生活服务占比高，高附加值零售、文化创意产业完全缺失。",
        "desc_2": "2. POI数据密度表明地块内部存在大面积产业活力真空地带，产业能级低，与高品质生活需求存在错位。",
        "desc_3": "3. 活力极核主要沿外部城市干道呈线性分布，未来应通过功能置换，引入多元复合的高活力业态分区。"
    }
}

def parse_drawing_type(drawing_type):
    # Detect parcel index
    p_idx = 0
    for idx, info in PARCEL_INFO.items():
        if info["key"] in drawing_type:
            p_idx = idx
            break
            
    # Detect analysis type
    a_type = "satellite"
    for a_key in ANALYSIS_INFO.keys():
        if a_key in drawing_type or ANALYSIS_INFO[a_key]["title_suffix"] in drawing_type:
            a_type = a_key
            break
            
    return p_idx, a_type

def wrap_text(text, max_len=44):
    forbidden_start = set("，。、；：？！）】』」》〉〕”’）,.?!;:)】")
    forbidden_end = set("（【『「《〈〔“‘（([【")
    
    def char_width(c):
        return 2 if ord(c) > 127 else 1

    lines = []
    for part in text.split('\n'):
        if not part:
            lines.append("")
            continue
        current_line = ""
        current_w = 0
        i = 0
        while i < len(part):
            char = part[i]
            w = char_width(char)
            if current_w + w <= 44:
                current_line += char
                current_w += w
                i += 1
            else:
                if not current_line:
                    current_line = char
                    current_w = w
                    i += 1
                else:
                    if part[i] in forbidden_start:
                        current_line += part[i]
                        i += 1
                        while i < len(part) and part[i] in forbidden_start:
                            current_line += part[i]
                            i += 1
                    while current_line and current_line[-1] in forbidden_end:
                        i -= 1
                        current_line = current_line[:-1]
                if current_line:
                    lines.append(current_line)
                current_line = ""
                current_w = 0
        if current_line:
            lines.append(current_line)
    return '\n'.join(lines)
def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop, *args, **kwargs):
    fig = ax.get_figure()
    params = kwargs.get("params", {})
    drawing_type = params.get("drawing_type", "老水产市场-现状卫星图")
    
    # 1. Parse Parcel Index and Analysis Type
    p_idx, a_type = parse_drawing_type(drawing_type)
    p_info = PARCEL_INFO[p_idx]
    a_info = ANALYSIS_INFO[a_type]
    
    # 2. Setup A3 Main Canvas Coordinates
    ax.set_facecolor("#F8FAFC")
    ax.set_xlim(0, 141.42)
    ax.set_ylim(0, 100)
    
    # Recalculate center and view bounds locally for the specific parcel
    if key_plots is not None and not key_plots.empty:
        curr_row = key_plots.iloc[p_idx]
        p_minx, p_miny, p_maxx, p_maxy = curr_row.geometry.bounds
        cx = (p_minx + p_maxx) / 2
        cy = (p_miny + p_maxy) / 2
        local_w = p_maxx - p_minx
        local_h = p_maxy - p_miny
        
        # Add beautiful padding factor
        padding_factor = 2.2
        view_h = local_h * padding_factor
        view_w = view_h * 1.2454
        if view_w < local_w * 1.3:
            view_w = local_w * 1.3
            view_h = view_w / 1.2454
    
    # Draw background architectural grid
    for x in range(5, 140, 5):
        ax.plot([x, x], [0, 100], color='#E2E8F0', linestyle='-', linewidth=0.6, zorder=0, alpha=0.5)
    for y in range(5, 100, 5):
        ax.plot([0, 141.42], [y, y], color='#E2E8F0', linestyle='-', linewidth=0.6, zorder=0, alpha=0.5)
        
    # 3. Main Title & Top Header Card (X: 2.0 to 139.4, Y: 89.0 to 96.3)
    header_shadow = mpatches.Rectangle((2.3, 88.7), 136.8, 7.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    header_bg = mpatches.Rectangle((2, 89.0), 136.8, 7.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(header_shadow)
    ax.add_patch(header_bg)
    
    # Color accent bar matching the analysis theme
    accent_bar = mpatches.Rectangle((2, 95.7), 136.8, 0.6, facecolor=a_info["accent"], edgecolor='none', zorder=3)
    ax.add_patch(accent_bar)
    
    title_text = f"{p_info['title']}地块 — {a_info['title_suffix']}"
    sub_text = f"展示重点更新地块「{p_info['name']}」的{a_info['sub']}，地块面积：{p_info['area']}公顷。"
    
    ax.text(3.5, 93.6, title_text, 
            color='#0F172A', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=26), zorder=4)
    
    ax.text(3.5, 90.7, sub_text, 
            color='#334155', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=15.0), zorder=4)

    # 4. Map Container (X: 2.0 to 100.0, Y: 4.0 to 87.0)
    map_shadow = mpatches.Rectangle((2.3, 3.7), 98.0, 83.0, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    map_bg = mpatches.Rectangle((2.0, 4.0), 98.0, 83.0, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(map_shadow)
    ax.add_patch(map_bg)
    
    # Sub-axes for GIS map
    ax_map = fig.add_axes([3.0 / 141.42, 5.0 / 100.0, 96.0 / 141.42, 81.0 / 100.0], facecolor="#F8FAFC", zorder=3)
    ax_map.set_xlim(cx - view_w / 2, cx + view_w / 2)
    ax_map.set_ylim(cy - view_h / 2, cy + view_h / 2)
    ax_map.set_axis_off()
    ax_map.set_aspect("equal")

    # 5. Render Map Contents based on Analysis Type
    sat_img_obj = None
    if a_type == "satellite":
        # Load and render high-resolution satellite imagery from TIFF dynamically
        tif_path = None
        from src.config.runtime import resolve_path
graduate_dir = resolve_path("output/graduate")
        if graduate_dir.exists():
            for root, dirs, files in os.walk(graduate_dir):
                for file in files:
                    if "2604161335" in file and file.lower().endswith(".tif"):
                        tif_path = Path(root) / file
                        break
        
        # Fallback to secondary location
        if not tif_path:
            album_dir = resolve_path("output/album/images")
            if album_dir.exists():
                for root, dirs, files in os.walk(album_dir):
                    for file in files:
                        if "2503142036" in file and file.lower().endswith(".tif"):
                            tif_path = Path(root) / file
                            break
                            
        loaded_high_res = False
        if tif_path and tif_path.exists():
            try:
                import rasterio
                from rasterio.windows import from_bounds
                with rasterio.open(tif_path) as src:
                    xmin = cx - view_w / 2
                    xmax = cx + view_w / 2
                    ymin = cy - view_h / 2
                    ymax = cy + view_h / 2
                    
                    # Crop with 5% safety padding to prevent boundary gaps
                    pad_w = view_w * 0.05
                    pad_h = view_h * 0.05
                    window = from_bounds(xmin - pad_w, ymin - pad_h, xmax + pad_w, ymax + pad_h, src.transform)
                    
                    # Read RGB (bands 1, 2, 3)
                    data = src.read([1, 2, 3], window=window)
                    rgb = np.transpose(data, (1, 2, 0))
                    sat_img_obj = Image.fromarray(rgb)
                    
                    ax_map.imshow(sat_img_obj, extent=[xmin - pad_w, xmax + pad_w, ymin - pad_h, ymax + pad_h], zorder=0)
                    loaded_high_res = True
            except Exception as e:
                print(f"Error loading high-res TIFF: {e}. Falling back to default satellite PNG.")
                
        if not loaded_high_res:
            # Fallback to pre-cropped PNG
            sat_path = STATIC_DIR / "assets/generated_base/satellite_cropped.png"
            if sat_path.exists():
                try:
                    sat_img_obj = Image.open(sat_path)
                    if boundary is not None and not boundary.empty:
                        b_minx, b_miny, b_maxx, b_maxy = boundary.total_bounds
                        extent = [b_minx, b_maxx, b_miny, b_maxy]
                        ax_map.imshow(sat_img_obj, extent=extent, zorder=0)
                except Exception as e:
                    print(f"Error loading fallback satellite image: {e}")
                    
        # Draw water body semi-transparent (skipped for satellite map to avoid cluttering base image)
        if water is not None and not water.empty and a_type != "satellite":
            water.plot(ax=ax_map, facecolor="#0066CC", edgecolor="none", alpha=0.35, zorder=1)
            
        # Draw context parcels outlines (skipped for satellite map as requested)
        pass
                    
        # Highlight current parcel outline (no facecolor, no hatch, clear boundary)
        if key_plots is not None and not key_plots.empty:
            curr_row = key_plots.iloc[p_idx]
            gpd.GeoSeries([curr_row.geometry]).plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=4.0)
            
    elif a_type == "landuse":
        # Render landuse colors
        if landuse is not None and not landuse.empty:
            for color_hex, sub_df in landuse.groupby('Color'):
                sub_df.plot(ax=ax_map, facecolor=color_hex, edgecolor="#CBD5E1", linewidth=0.25, zorder=1)
                
        # Render water body
        if water is not None and not water.empty:
            water.plot(ax=ax_map, facecolor="#D0E6F7", edgecolor="none", zorder=1.5)
            
        # Render buildings
        if buildings is not None and not buildings.empty:
            buildings.plot(ax=ax_map, facecolor="#FFFFFF", edgecolor="#475569", linewidth=0.15, alpha=0.6, zorder=2)
            
        # Highlight current parcel boundary
        if key_plots is not None and not key_plots.empty:
            curr_row = key_plots.iloc[p_idx]
            gpd.GeoSeries([curr_row.geometry]).plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=3)
            
    elif a_type == "fabric":
        # Render buildings by風貌 style
        if water is not None and not water.empty:
            water.plot(ax=ax_map, facecolor="#D0E6F7", edgecolor="none", zorder=1)
            
        if buildings is not None and not buildings.empty:
            buildings_copy = buildings.copy()
            conditions = [
                (buildings_copy["prop_style"] == "historical"),
                (buildings_copy["prop_style"] == "park"),
                (buildings_copy["prop_style"] == "normal") | (buildings_copy["prop_style"].isna())
            ]
            choices = [
                "#B45309", # historical: gold/amber
                "#0F766E", # park: teal
                "#E2E8F0"  # normal: light gray
            ]
            buildings_copy["color"] = np.select(conditions, choices, default="#E2E8F0")
            buildings_copy.plot(ax=ax_map, color=buildings_copy["color"], edgecolor="#475569", linewidth=0.2, zorder=2)
            
        # Highlight current parcel boundary
        if key_plots is not None and not key_plots.empty:
            curr_row = key_plots.iloc[p_idx]
            gpd.GeoSeries([curr_row.geometry]).plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=3)
            
    elif a_type == "height":
        # Render buildings by height/floor count
        if water is not None and not water.empty:
            water.plot(ax=ax_map, facecolor="#D0E6F7", edgecolor="none", zorder=1)
            
        if buildings is not None and not buildings.empty:
            buildings_copy = buildings.copy()
            buildings_copy["Floor_num"] = pd.to_numeric(buildings_copy["Floor"], errors="coerce").fillna(1)
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
            buildings_copy.plot(ax=ax_map, color=buildings_copy["color"], edgecolor="#475569", linewidth=0.2, zorder=2)
            
        # Highlight current parcel boundary
        if key_plots is not None and not key_plots.empty:
            curr_row = key_plots.iloc[p_idx]
            gpd.GeoSeries([curr_row.geometry]).plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=3)
            
    elif a_type == "business":
        # POI Vitality Analysis
        if water is not None and not water.empty:
            water.plot(ax=ax_map, facecolor="#E2F0FD", edgecolor="none", zorder=1)
            
        if buildings is not None and not buildings.empty:
            buildings.plot(ax=ax_map, facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=0.2, alpha=0.5, zorder=1.2)
            
        # Generate POI contours centered around the parcel centroid
        grid_res = 100
        x_grid = np.linspace(cx - view_w/2, cx + view_w/2, grid_res)
        y_grid = np.linspace(cy - view_h/2, cy + view_h/2, grid_res)
        X, Y = np.meshgrid(x_grid, y_grid)
        Z = np.zeros_like(X)
        
        # Two Gaussian peaks: primary at centroid, secondary offset to make a nice pattern
        centers = [
            (cx, cy),
            (cx + view_w * 0.15, cy - view_h * 0.15)
        ]
        weights = [1.2, 0.7]
        sigmas = [view_w * 0.2, view_w * 0.12]
        
        for (c_x, c_y), w, sigma in zip(centers, weights, sigmas):
            dist_sq = (X - c_x)**2 + (Y - c_y)**2
            Z += w * np.exp(-dist_sq / (2 * sigma**2))
            
        if Z.max() > 0:
            Z = Z / Z.max()
            
        ax_map.contourf(X, Y, Z, levels=50, cmap="YlOrRd", alpha=0.45, zorder=1.8)
        ax_map.contour(X, Y, Z, levels=[0.3, 0.6, 0.85], 
                       colors=['#FBBF24', '#F97316', '#EF4444'], 
                       linewidths=[0.6, 0.9, 1.2], alpha=0.75, zorder=1.9)
                       
        # Generate clustered POI dots
        np.random.seed(42 + p_idx)
        poi_pts = []
        for color, count in [("#3B82F6", 18), ("#F59E0B", 14), ("#EF4444", 6)]:
            for _ in range(count):
                px = cx + np.random.normal(0, view_w * 0.22)
                py = cy + np.random.normal(0, view_h * 0.22)
                poi_pts.append((px, py, color))
                
        for px, py, color in poi_pts:
            ax_map.plot(px, py, marker='o', markersize=7.0, color=color, alpha=0.3, zorder=4.5)
            ax_map.plot(px, py, marker='o', markersize=3.5, color=color, alpha=0.95,
                        markeredgecolor='#FFFFFF', markeredgewidth=0.4, zorder=5.0)
                        
        # Highlight current parcel boundary
        if key_plots is not None and not key_plots.empty:
            curr_row = key_plots.iloc[p_idx]
            gpd.GeoSeries([curr_row.geometry]).plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=3.0, zorder=3)

    # 6. Render Roads and Rails on top of base layers (skipped for satellite map to avoid cluttering base image)
    if roads is not None and not roads.empty and a_type != "satellite":
        # Filter roads within the local bounding box to speed up or keep clean
        roads.plot(ax=ax_map, color="#94A3B8", linewidth=1.5, alpha=0.8, zorder=2.8)
        roads.plot(ax=ax_map, color="#FFFFFF", linewidth=0.8, alpha=0.9, zorder=2.9)
        
    if rails is not None and not rails.empty and a_type != "satellite":
        rails.plot(ax=ax_map, color="#475569", linewidth=1.8, linestyle=(0, (6, 6)), zorder=3.0)
        
    # Draw boundary of study area in red (skipped for satellite map to avoid clutter)
    if boundary is not None and not boundary.empty and a_type != "satellite":
        boundary.plot(ax=ax_map, facecolor="none", edgecolor="#FF3B30", linewidth=2.0, zorder=4.0)

    # 7. Adaptive Windrose based on background brightness
    rose_color = "black"
    if a_type == "satellite" and sat_img_obj is not None:
        try:
            # Sample the area where the windrose sits in the satellite image
            w, h = sat_img_obj.size
            crop_x1 = int(w * 0.85)
            crop_y1 = int(h * 0.02)
            crop_x2 = int(w * 0.98)
            crop_y2 = int(h * 0.20)
            region = sat_img_obj.crop((crop_x1, crop_y1, crop_x2, crop_y2))
            avg_brightness = np.mean(np.array(region.convert("L")))
            if avg_brightness < 128:
                rose_color = "white"
        except Exception as e:
            print(f"Error checking brightness: {e}")
            rose_color = "white"  # Default to white on satellite maps

    rose_path = ASSETS_DIR / "长春市风玫瑰.png"
    if rose_path.exists():
        try:
            # Add wind rose axes on the top right
            ax_rose = fig.add_axes([87.0 / 141.42, 72.5 / 100.0, 12.0 / 141.42, 12.0 / 100.0], facecolor='none', zorder=4)
            ax_rose.set_axis_off()
            
            # Draw a soft shadow background (semi-transparent gray/white based on theme)
            y_g, x_g = np.ogrid[-1:1:100j, -1:1:100j]
            r = np.sqrt(x_g**2 + y_g**2)
            alpha = np.clip(1.0 - r, 0, 1) * (0.45 if rose_color == "white" else 0.35)
            grad_img = np.ones((100, 100, 4))
            if rose_color == "white":
                grad_img[..., 0:3] = 0  # Dark shadow behind white rose
            else:
                grad_img[..., 0:3] = 1  # Light shadow behind black rose
            grad_img[..., 3] = alpha
            ax_rose.imshow(grad_img, zorder=0, extent=[0, 1, 0, 1], origin='upper')
            
            # Convert windrose image to target color
            rose_img = Image.open(rose_path).convert("RGBA")
            rose_data = np.array(rose_img)
            fill_val = 255 if rose_color == "white" else 0
            rose_data[..., 0] = fill_val
            rose_data[..., 1] = fill_val
            rose_data[..., 2] = fill_val
            final_rose_img = Image.fromarray(rose_data)
            ax_rose.imshow(final_rose_img, zorder=1, extent=[0, 1, 0, 1], origin='upper')
        except Exception as e:
            print(f"Error loading wind rose on sub-axes: {e}")

    # 8. Legend Card (X: 101.5 to 139.4, Y: 62.0 to 87.0)
    legend_shadow = mpatches.Rectangle((101.8, 61.7), 37.9, 25.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    legend_bg = mpatches.Rectangle((101.5, 62.0), 37.9, 25.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(legend_shadow)
    ax.add_patch(legend_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 85.8), 37.9, 1.5, facecolor=a_info["accent"], edgecolor='none', zorder=3))
    
    ax.text(103.5, 83.2, "图例 / LEGEND", color=a_info["accent"], ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13.5), zorder=4)

    # Dynamic Legend Items depending on analysis type
    legend_items_data = []
    if a_type == "satellite":
        legend_items_data = [
            ("当前更新地块", "#FF3B30", "outline_bold"),
            ("城市水系", "#0066CC", "fill_water_sat"),
            ("遥感影像底图", "#64748B", "fill_sat")
        ]
    elif a_type == "landuse":
        legend_items_data = [
            ("当前地块范围", "#FF3B30", "outline_bold"),
            ("居住用地 (R)", "#FFFF00", "fill_border"),
            ("商业办公 (B)", "#E60000", "fill_border"),
            ("商业服务 (B)", "#FF7F00", "fill_border"),
            ("工业用地 (M)", "#AA7855", "fill_border"),
            ("交通场站 (S)", "#9C9C9C", "fill_border"),
            ("行政办公 (A)", "#FF7F7F", "fill_border"),
            ("公园绿地 (G)", "#38A800", "fill_border"),
        ]
    elif a_type == "fabric":
        legend_items_data = [
            ("当前地块范围", "#FF3B30", "outline_bold"),
            ("历史保护建筑", "#B45309", "fill_border"),
            ("景观风貌建筑", "#0F766E", "fill_border"),
            ("普通现代建筑", "#E2E8F0", "fill_border"),
            ("城市道路", "#E2E8F0", "line_road"),
            ("城市水系", "#D0E6F7", "fill_water")
        ]
    elif a_type == "height":
        legend_items_data = [
            ("当前地块范围", "#FF3B30", "outline_bold"),
            ("低层 (1-3层)", "#FDE68A", "fill_border"),
            ("多层 (4-7层)", "#F97316", "fill_border"),
            ("中高层 (8-14层)", "#EF4444", "fill_border"),
            ("高层 (15-20层)", "#B91C1C", "fill_border"),
            ("超高层 (21层+)", "#7F1D1D", "fill_border"),
        ]
    elif a_type == "business":
        legend_items_data = [
            ("当前地块范围", "#FF3B30", "outline_bold"),
            ("高活力核心区", "#EF4444", "fill"),
            ("中活力过渡区", "#FCD34D", "fill"),
            ("生活服务 POI", "#3B82F6", "glow_dot"),
            ("餐饮服务 POI", "#F59E0B", "glow_dot"),
            ("购物服务 POI", "#EF4444", "glow_dot"),
        ]

    # Draw Legend Items
    for i, (label, color_code, style) in enumerate(legend_items_data):
        x = 103.5 + (i % 2) * 18.0
        y = 79.5 - (i // 2) * 3.3
        
        if style == "outline_hatch":
            rect = mpatches.Rectangle((x, y - 0.8), 2.8, 1.7, facecolor='none', edgecolor=color_code, linewidth=1.5, hatch="//", zorder=4)
            ax.add_patch(rect)
        elif style == "outline_gray":
            rect = mpatches.Rectangle((x, y - 0.8), 2.8, 1.7, facecolor='none', edgecolor=color_code, linewidth=1.0, zorder=4)
            ax.add_patch(rect)
        elif style == "outline_bold":
            rect = mpatches.Rectangle((x, y - 0.8), 2.8, 1.7, facecolor='none', edgecolor=color_code, linewidth=2.0, zorder=4)
            ax.add_patch(rect)
        elif style == "fill_water_sat":
            rect = mpatches.Rectangle((x, y - 0.8), 2.8, 1.7, facecolor=color_code, edgecolor='none', alpha=0.35, zorder=4)
            ax.add_patch(rect)
        elif style == "fill_sat":
            rect = mpatches.Rectangle((x, y - 0.8), 2.8, 1.7, facecolor=color_code, edgecolor='#CBD5E1', alpha=0.8, zorder=4)
            ax.add_patch(rect)
        elif style == "fill_border":
            rect = mpatches.Rectangle((x, y - 0.8), 2.8, 1.7, facecolor=color_code, edgecolor='#475569', linewidth=0.5, zorder=4)
            ax.add_patch(rect)
        elif style == "fill":
            rect = mpatches.Rectangle((x, y - 0.8), 2.8, 1.7, facecolor=color_code, edgecolor='none', zorder=4)
            ax.add_patch(rect)
        elif style == "fill_water":
            rect = mpatches.Rectangle((x, y - 0.8), 2.8, 1.7, facecolor=color_code, edgecolor='none', zorder=4)
            ax.add_patch(rect)
        elif style == "line_road":
            rect = mpatches.Rectangle((x, y - 0.45), 2.8, 0.9, facecolor=color_code, edgecolor='none', zorder=4)
            ax.add_patch(rect)
        elif style == "glow_dot":
            ax.plot(x + 1.4, y, marker='o', markersize=7.0, color=color_code, alpha=0.3, zorder=4)
            ax.plot(x + 1.4, y, marker='o', markersize=3.0, color=color_code, alpha=0.95, markeredgecolor='#FFFFFF', markeredgewidth=0.4, zorder=5)

        ax.text(x + 3.6, y, label, color='#334155', ha='left', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], size=10.5), zorder=4)

    # 9. Dynamic Scale Bar (centered under Legend Card)
    y_bar = 65.2
    target_dist = view_w * 0.20
    standard_intervals = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
    bar_dist = min(standard_intervals, key=lambda x: abs(x - target_dist))
    
    # Ensure it's not too large for the box (max 26 units)
    if bar_dist * 96.0 / view_w > 26.0:
        idx = standard_intervals.index(bar_dist)
        if idx > 0:
            bar_dist = standard_intervals[idx - 1]
            
    scale_len = bar_dist / (view_w / 96.0) # Length in main axes units
    x_start = 120.45 - scale_len / 2
    x_end = x_start + scale_len
    
    dist_labels = ["0", f"{bar_dist//2}m", f"{bar_dist}m"]
    if bar_dist >= 1000:
        dist_labels = ["0", f"{bar_dist/2000:.1f}km".replace(".0", ""), f"{bar_dist/1000:.0f}km"]
        
    ax.plot([x_start, x_end], [y_bar, y_bar], color='#0F172A', linewidth=1.5, zorder=4)
    for x_tick in [x_start, x_start + scale_len/2, x_end]:
        ax.plot([x_tick, x_tick], [y_bar - 0.6, y_bar + 0.6], color='#0F172A', linewidth=1.5, zorder=4)
        
    ax.text(x_start, y_bar + 0.8, dist_labels[0], color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.0), zorder=4)
    ax.text(x_start + scale_len/2, y_bar + 0.8, dist_labels[1], color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.0), zorder=4)
    ax.text(x_end, y_bar + 0.8, dist_labels[2], color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.0), zorder=4)
            
    scale_ratio = view_w / 0.31968
    scale_rounded = int(round(scale_ratio / 100)) * 100
    ax.text((x_start + x_end)/2, y_bar - 0.8, f"比例尺 1:{scale_rounded}", color='#334155', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.5, weight='bold'), zorder=4)

    # 10. Description Card (X: 101.5 to 139.4, Y: 4.0 to 60.0)
    desc_shadow = mpatches.Rectangle((101.8, 3.7), 37.9, 56.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    desc_bg = mpatches.Rectangle((101.5, 4.0), 37.9, 56.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(desc_shadow)
    ax.add_patch(desc_bg)
    ax.add_patch(mpatches.Rectangle((101.5, 58.8), 37.9, 1.2, facecolor=a_info["accent"], edgecolor='none', zorder=3))
    
    ax.text(103.5, 56.2, "现状诊断与设计定位 / DIAGNOSIS", color=a_info["accent"], ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13.5), zorder=4)

    # Description rows: 1 general base line + 3 specific lines
    desc_data = [
        ("诊断地块：" + p_info["desc_base"], 50.0, True),
        (a_info["desc_1"], 34.0, False),
        (a_info["desc_2"], 23.0, False),
        (a_info["desc_3"], 12.0, False)
    ]
    
    for text, y_pos, is_bold in desc_data:
        wrapped_desc = wrap_text(text, max_len=44)
        y_text = y_pos
        for line in wrapped_desc.split('\n'):
            f_prop = fm.FontProperties(family=font_prop['family'], size=15.0, weight='bold' if is_bold else 'normal')
            color = '#0F172A' if is_bold else '#334155'
            ax.text(103.5, y_text, line, color=color, ha='left', va='center',
                    fontproperties=f_prop, zorder=4)
            y_text -= 3.0

legend_items = []
description_lines = []
