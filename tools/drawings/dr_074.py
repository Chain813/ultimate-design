# -*- coding: utf-8 -*-
# tools/drawings/dr_074.py
import os
import json
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import geopandas as gpd
from pathlib import Path
from shapely.geometry import Point

# Disable Matplotlib GUI warnings
plt.switch_backend('Agg')

NO_FRAME = True  # Bypasses the standard A3 layout template and draws the entire sheet!

def wrap_text_by_pixels(text, font, max_width, draw):
    forbidden_start = set("，。、；：？！）】』」》〉〕”’）,.?!;:)】")
    forbidden_end = set("（【『「《〈〔“‘（([【")
    
    def get_width(t):
        try:
            return draw.textlength(t, font=font)
        except AttributeError:
            try:
                left, top, right, bottom = font.getbbox(t)
                return right - left
            except AttributeError:
                return font.getsize(t)[0]

    lines = []
    for block in text.split('\n'):
        if not block:
            lines.append("")
            continue
        current_line = ""
        i = 0
        while i < len(block):
            char = block[i]
            test_line = current_line + char
            if get_width(test_line) <= max_width:
                current_line = test_line
                i += 1
            else:
                if not current_line:
                    current_line = char
                    i += 1
                else:
                    if block[i] in forbidden_start:
                        current_line += block[i]
                        i += 1
                        while i < len(block) and block[i] in forbidden_start:
                            current_line += block[i]
                            i += 1
                    while current_line and current_line[-1] in forbidden_end:
                        i -= 1
                        current_line = current_line[:-1]
                if current_line:
                    lines.append(current_line)
                current_line = ""
        if current_line:
            lines.append(current_line)
    return lines
def draw_map_early(output_path, view_w, view_h, STATIC_DIR):
    print("Drawing DR-074 custom vector economic dashboard...")
    
    # 1. Create main A3 canvas 2240x1584 (slate-50 background)
    img = Image.new("RGB", (2240, 1584), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)

    # Fonts
    font_path = 'C:/Windows/Fonts/msyh.ttc'
    font_bold_path = 'C:/Windows/Fonts/msyhbd.ttc'
    try:
        font_large_title = ImageFont.truetype(font_bold_path, 36)
        font_card_title = ImageFont.truetype(font_bold_path, 20)
        font_box_header = ImageFont.truetype(font_bold_path, 16)
        font_body = ImageFont.truetype(font_path, 13)
        font_body_bold = ImageFont.truetype(font_bold_path, 13)
        font_desc = ImageFont.truetype(font_path, 14)
        font_stamp = ImageFont.truetype(font_path, 12)
    except IOError:
        font_large_title = ImageFont.load_default()
        font_card_title = ImageFont.load_default()
        font_box_header = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_body_bold = ImageFont.load_default()
        font_desc = ImageFont.load_default()
        font_stamp = ImageFont.load_default()

    # Draw grid background
    grid_spacing = 79.2
    for x in range(1, int(2240 / grid_spacing)):
        lx = int(x * grid_spacing)
        draw.line([(lx, 0), (lx, 1584)], fill=(226, 232, 240), width=1)
    for y in range(1, int(1584 / grid_spacing)):
        ly = int(y * grid_spacing)
        draw.line([(0, ly), (2240, ly)], fill=(226, 232, 240), width=1)

    # ── Header Card (X: 32 to 2208, Y: 60 to 184) ──
    draw.rectangle([36, 64, 2212, 188], fill=(226, 232, 240))
    draw.rectangle([32, 60, 2208, 184], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 60, 2208, 66], fill=(37, 99, 235)) # Blue header
    
    # Title and subtitle on two separate lines
    draw.text((55, 78), "投资估算与经济测算图", fill=(15, 23, 42), font=font_large_title)
    draw.text((55, 138), "根据5个重点更新地块的改造总平面设计，细化“建、绿、路、管”分项指标与投资，测算回收期与资金平衡。", 
              fill=(100, 116, 139), font=font_desc)

    # ── Left Map Container Card (X: 32 to 1350, Y: 216 to 1520) ──
    draw.rectangle([36, 220, 1354, 1524], fill=(226, 232, 240))
    draw.rectangle([32, 216, 1350, 1520], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 216, 1350, 222], fill=(37, 99, 235))

    draw.text((60, 245), "重点更新片区投资地图 / INVESTMENT & COST SPATIAL ALLOCATION", fill=(37, 99, 235), font=font_card_title)
    draw.line([(60, 275), (1322, 275)], fill=(226, 232, 240), width=1)

    # ── Load and Plot GIS Map inside the Container ──
    GIS_DIR = Path("data/gis")
    boundary_path = GIS_DIR / "Boundary_Scope.geojson"
    water_path = STATIC_DIR / "water.geojson"
    roads_path = STATIC_DIR / "road_clipped.geojson"
    rails_path = STATIC_DIR / "rail_clipped.geojson"
    buildings_path = STATIC_DIR / "buildings.geojson"
    key_plots_path = GIS_DIR / "Key_Plots_District.json"

    # Set up matplotlib figure for map insert (larger size to fill container)
    fig_map = plt.figure(figsize=(10.5, 10.5), dpi=120, facecolor="#FFFFFF")
    ax_map = fig_map.add_axes([0, 0, 1, 1], facecolor="#FFFFFF")
    ax_map.set_axis_off()

    try:
        boundary = gpd.read_file(boundary_path).to_crs(epsg=3857)
        water = gpd.read_file(water_path).to_crs(epsg=3857) if water_path.exists() else None
        roads = gpd.read_file(roads_path).to_crs(epsg=3857) if roads_path.exists() else None
        rails = gpd.read_file(rails_path).to_crs(epsg=3857) if rails_path.exists() else None
        buildings = gpd.read_file(buildings_path).to_crs(epsg=3857) if buildings_path.exists() else None
        key_plots = gpd.read_file(key_plots_path).to_crs(epsg=3857) if key_plots_path.exists() else None

        minx, miny, maxx, maxy = boundary.total_bounds
        cx = (minx + maxx) / 2
        cy = (miny + maxy) / 2
        height_m = maxy - miny
        map_view_h = height_m * 1.50
        map_view_w = map_view_h

        ax_map.set_xlim(cx - map_view_w/2, cx + map_view_w/2)
        ax_map.set_ylim(cy - map_view_h/2, cy + map_view_h/2)
        ax_map.set_aspect('equal')

        # Plot GIS Layers
        if water is not None:
            water.plot(ax=ax_map, facecolor="#D0E6F7", edgecolor="none", zorder=3)
        if buildings is not None:
            buildings.plot(ax=ax_map, facecolor="#F1F5F9", edgecolor="#CBD5E1", linewidth=0.4, zorder=2)
        if roads is not None:
            for lvl, lw, color in [(1, 1.8, "#94A3B8"), (2, 1.2, "#CBD5E1"), (3, 0.7, "#E2E8F0"), (4, 0.5, "#F1F5F9")]:
                sub_gdf = roads[roads['level'] == lvl]
                if not sub_gdf.empty:
                    sub_gdf.plot(ax=ax_map, color=color, linewidth=lw, capstyle="round", zorder=4)
        if rails is not None:
            rails.plot(ax=ax_map, color="#64748B", linewidth=1.2, linestyle=(0, (5, 5)), zorder=5)
        if boundary is not None:
            boundary.plot(ax=ax_map, facecolor="none", edgecolor="#EF4444", linewidth=2.0, zorder=6)

        # Plot 5 Key Plots with distinct colors
        plot_colors = ["#F59E0B", "#EF4444", "#22C55E", "#8B5CF6", "#3B82F6"]
        if key_plots is not None:
            for idx, row in key_plots.iterrows():
                if idx < len(plot_colors):
                    gpd.GeoSeries([row.geometry]).plot(ax=ax_map, facecolor=plot_colors[idx], edgecolor="#1E293B", linewidth=1.5, alpha=0.75, zorder=7)
    except Exception as ex:
        print(f"Error drawing Matplotlib GIS insert: {ex}")

    # Save temp insert
    temp_img_path = "temp_dr074_insert.png"
    
    # Floating Windrose (Pure Black, 12% size) with soft white radial gradient backdrop
    try:
        from PIL import Image as _PIL_Image
        import numpy as _np
        from pathlib import Path as _Path
        _rose_path = _Path("assets/长春市风玫瑰.png")
        if _rose_path.exists():
            _ax_rose = fig_map.add_axes([0.85, 0.85, 0.12, 0.12], facecolor='none', zorder=10)
            _ax_rose.set_axis_off()
            
            _y_g, _x_g = _np.ogrid[-1:1:100j, -1:1:100j]
            _r = _np.sqrt(_x_g**2 + _y_g**2)
            _alpha = _np.clip(1.0 - _r, 0, 1) * 0.50
            _grad_img = _np.ones((100, 100, 4))
            _grad_img[..., 3] = _alpha
            _ax_rose.imshow(_grad_img, zorder=0, extent=[0, 1, 0, 1], origin='lower')
            
            _rose_img = _PIL_Image.open(_rose_path).convert("RGBA")
            _rose_data = _np.array(_rose_img)
            _rose_data[..., 0] = 0
            _rose_data[..., 1] = 0
            _rose_data[..., 2] = 0
            _black_rose_img = _PIL_Image.fromarray(_rose_data)
            _ax_rose.imshow(_black_rose_img, zorder=1)
    except Exception as e:
        print(f"Error drawing insert wind rose: {e}")

    plt.savefig(temp_img_path, dpi=120, bbox_inches='tight', pad_inches=0)
    plt.close()

    # Open and paste into A3 canvas (placed centrally inside the map container, starting at Y: 290 to prevent overlap)
    map_insert = Image.open(temp_img_path)
    map_insert_resized = map_insert.resize((1200, 1200), Image.Resampling.LANCZOS)
    img.paste(map_insert_resized, (70, 290))
    try:
        os.remove(temp_img_path)
    except Exception:
        pass

    # Coordinate mapping from projected EPSG:3857 to PIL pixel coordinates inside map_insert_resized
    def get_pixel_pos(x, y):
        px = 70 + (x - (cx - map_view_w/2)) / map_view_w * 1200
        py = 290 + (1200 - (y - (cy - map_view_h/2)) / map_view_h * 1200)
        return int(px), int(py)

    # Draw 5 detailed calculation cards on the PIL canvas pointing to key plots (shifted down to start Y: 300)
    centroids_wgs84 = [
        ("老水产市场 (S=3.71ha)", 125.333536, 43.907389, 80, 300, 420, 140, [
            "建: 48,230㎡ × 2800元 = 13,504万元",
            "绿: 14,098㎡ × 700元 = 987万元",
            "路: 3,200㎡ × 250元 = 80万元",
            "管: 500m × 1500 + 10根 × 4.5万 = 120万元",
            "总投资: 1.47 亿元 | 回收期: 8.9 年"
        ], "#F59E0B"),
        
        ("食品调料市场 (S=16.83ha)", 125.341750, 43.906706, 880, 300, 420, 140, [
            "建: 235,620㎡ × 2800 × 55% = 36,285万元",
            "绿: 58,905㎡ × 700元 = 4,123万元",
            "路: 12,000㎡ × 250元 = 300万元",
            "管: 1800m × 1500 + 35根 × 4.5万 = 427万元",
            "总投资: 4.11 亿元 | 回收期: 8.9 年"
        ], "#EF4444"),
        
        ("市一中北侧 (S=2.78ha)", 125.333542, 43.904235, 80, 600, 420, 140, [
            "建: 36,140㎡ × 2800 × 40% = 4,047万元",
            "绿: 9,730㎡ × 700元 = 681万元",
            "路: 2,500㎡ × 250元 = 62万元",
            "管: 400m × 1500 + 8根 × 4.5万 = 96万元",
            "总投资: 4,886 万元 | 回收期: 9.8 年"
        ], "#22C55E"),

        ("清禾集贸市场 (S=2.47ha)", 125.346951, 43.899892, 880, 840, 420, 140, [
            "建: 32,110㎡ × 2800 × 50% = 4,495万元",
            "绿: 8,645㎡ × 700元 = 605万元",
            "路: 3,000㎡ × 250元 = 75万元",
            "管: 450m × 1500 + 8根 × 4.5万 = 103万元",
            "总投资: 5,278 万元 | 回收期: 9.6 年"
        ], "#8B5CF6"),

        ("中国石油地块 (S=1.30ha)", 125.336475, 43.898121, 80, 1140, 420, 150, [
            "建: 2,600㎡ × 2800元 = 728万元",
            "绿: 10,400㎡ × 700元 = 728万元",
            "路: 1,200㎡ × 250元 = 30万元",
            "管: 200m × 1500 + 4根 × 4.5万 = 48万元",
            "安全防护与设施改线费 = 1000万元",
            "总投资: 2,534 万元 | 回收期: 8.4 年"
        ], "#3B82F6")
    ]

    import pyproj
    transformer = pyproj.Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)

    for name, lon, lat, bx, by, bw, bh, lines, color in centroids_wgs84:
        mx, my = transformer.transform(lon, lat)
        px, py = get_pixel_pos(mx, my)
        
        # Adjust px, py boundary clipping to prevent running off map
        px = max(90, min(1290, px))
        py = max(310, min(1470, py))

        # Draw card border shadow
        draw.rectangle([bx+4, by+4, bx+bw+4, by+bh+4], fill=(226, 232, 240))
        # Draw card background
        draw.rectangle([bx, by, bx+bw, by+bh], fill=(255, 255, 255), outline=(203, 213, 225), width=1)
        # Draw header color block
        draw.rectangle([bx, by, bx+bw, by+26], fill=color)
        draw.text((bx + 12, by + 5), name, fill=(255, 255, 255), font=font_box_header)

        # Draw details text lines
        y_txt = by + 32
        for line in lines:
            if "|" in line: # Highlights totals
                parts = line.split("|")
                draw.text((bx + 12, y_txt), parts[0].strip(), fill=(30, 41, 59), font=font_body_bold)
                draw.text((bx + bw/2 + 10, y_txt), parts[1].strip(), fill=(220, 38, 38), font=font_body_bold)
            else:
                draw.text((bx + 12, y_txt), line, fill=(71, 85, 105), font=font_body)
            y_txt += 18

        # Draw leader lines pointing from box edge to plot centroid
        if bx + bw < px:
            start_x = bx + bw
            start_y = by + bh/2
        elif bx > px:
            start_x = bx
            start_y = by + bh/2
        else:
            start_x = bx + bw/2
            start_y = by + bh if by < py else by
            
        draw.line([(start_x, start_y), (px, py)], fill=color, width=2)
        draw.ellipse([(px-4, py-4), (px+4, py+4)], fill=color)

    # ── Right Column 1: Unit Cost Reference Table (X: 1374 to 2208, Y: 216 to 620) ──
    draw.rectangle([1378, 220, 2212, 624], fill=(226, 232, 240))
    draw.rectangle([1374, 216, 2208, 620], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1374, 216, 2208, 222], fill=(37, 99, 235))

    draw.text((1400, 245), "工程概算指标及测算标准 / COSTING STANDARDS", fill=(37, 99, 235), font=font_card_title)
    draw.line([(1400, 275), (2182, 275)], fill=(226, 232, 240), width=1)

    standards = [
        ("🏗️ 建筑更新改造 (A)", "计算公式: S_总建 × 2800元/㎡\n包含原有砖混厂房与建筑改造主体结构加固、沿街立面整治与内部管线改造综合单价。", "#3B82F6"),
        ("🌳 绿化景观与海绵 (B)", "计算公式: S_地块 × 绿地率 × 700元/㎡\n包含屋顶绿化、口袋公园种植设计、透水铺装及生态草沟海绵城市设施综合单价。", "#10B981"),
        ("🛣️ 道路铺装与慢行 (C)", "计算公式: S_路网 × 250元/㎡\n包含彩色透水铺装慢行系统、非机动车道划分与微循环交通安防设施。", "#F59E0B"),
        ("⚡ 市政综合管线 (D)", "计算公式: L_管线 × 1500元/延米 + N_智能杆 × 4.5万元/根\n包含老旧区架空线缆入地整治、雨污分流管道敷设以及5G智慧路灯综合杆布设。", "#8B5CF6")
    ]

    y_std = 285
    for title, desc, color_tag in standards:
        draw.text((1400, y_std), title, fill=(15, 23, 42), font=font_box_header)
        draw.rectangle([1390, y_std + 3, 1395, y_std + 15], fill=color_tag)
        wrapped_desc = wrap_text_by_pixels(desc, font_body, 770, draw)
        y_txt = y_std + 20
        for line in wrapped_desc:
            if "计算公式:" in line:
                draw.text((1400, y_txt), line, fill=(220, 38, 38), font=font_body_bold)
            else:
                draw.text((1400, y_txt), line, fill=(100, 116, 139), font=font_body)
            y_txt += 18
        y_std += 80

    # ── Right Column 2: Financial Summary Matrix Table (X: 1374 to 2208, Y: 644 to 1520) ──
    draw.rectangle([1378, 648, 2212, 1524], fill=(226, 232, 240))
    draw.rectangle([1374, 644, 2208, 1520], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1374, 644, 2208, 650], fill=(37, 99, 235))

    draw.text((1400, 680), "地块经济估算及资金平衡预测表 / FINANCIAL SUMMARY", fill=(37, 99, 235), font=font_card_title)
    draw.line([(1400, 710), (2182, 710)], fill=(226, 232, 240), width=1)

    # Draw Table Header
    headers = ["更新地块", "估算总投资", "预计年回报", "静态回收期"]
    col_x = [1400, 1600, 1810, 2010]
    for h_idx, h_name in enumerate(headers):
        draw.text((col_x[h_idx], 730), h_name, fill=(15, 23, 42), font=font_box_header)
    draw.line([(1400, 755), (2182, 755)], fill=(15, 23, 42), width=2)

    # Table Rows
    rows_data = [
        ("老水产市场", "1.47 亿元", "1,650 万元", "8.9 年"),
        ("食品调料市场", "4.11 亿元", "4,600 万元", "8.9 年"),
        ("市一中北侧", "4,886 万元", "500 万元", "9.8 年"),
        ("清禾集贸市场", "5,278 万元", "550 万元", "9.6 年"),
        ("中国石油地块", "2,534 万元", "300 万元", "8.4 年"),
    ]

    y_row = 770
    for row in rows_data:
        for c_idx, val in enumerate(row):
            draw.text((col_x[c_idx], y_row), val, fill=(71, 85, 105), font=font_desc)
        draw.line([(1400, y_row + 25), (2182, y_row + 25)], fill=(226, 232, 240), width=1)
        y_row += 35

    # Table Footer Total Row
    totals = ["合计 / Total", "6.85 亿元", "7,600 万元", "9.0 年"]
    for c_idx, val in enumerate(totals):
        draw.text((col_x[c_idx], y_row), val, fill=(220, 38, 38), font=font_box_header)
    draw.line([(1400, y_row + 25), (2182, y_row + 25)], fill=(15, 23, 42), width=2)

    # ── Text Description Box (Under Table) ──
    y_info = y_row + 45
    info_header = "【财务与效益可行性研判】"
    draw.text((1400, y_info), info_header, fill=(37, 99, 235), font=font_box_header)
    
    info_text = (
        "1. 资金平衡路径：片区更新总投资约 6.85 亿元。其中老旧住宅微更新与基础设施提升具有高度公益性，通过老水产文创街区与食品调料大市场的特许经营、商业租金、市集摊位费收益进行‘肥瘦搭配’，实现资金长期闭环与自我输血。\n"
        "2. 经济与社会溢价：更新释放运营空间 35 万平方米，预计带动就业岗位 2500 余个，周边居住物业平均增值 15%-20%，有效拉动铁北老工业片区内需和文旅活力。\n"
        "3. 生态经济学估算：10万平方米绿地与能量花园可实现年雨水滞蓄约 8.5 万立方米，减少市政雨水管网负荷；年吸收二氧化碳约 340 吨，具有显著的社会和生态服务价值。"
    )
    wrapped_info = wrap_text_by_pixels(info_text, font_body, 770, draw)
    y_info_txt = y_info + 25
    for line in wrapped_info:
        draw.text((1400, y_info_txt), line, fill=(71, 85, 105), font=font_body)
        y_info_txt += 20

    # ── Standard A3 Drawing Sheet Stamp Block (Bottom Right aligned to X: 2208) ──
    stamp_x = 1901
    stamp_y = 1390
    draw.rectangle([stamp_x, stamp_y, 2208, 1520], fill=(255, 255, 255), outline=(148, 163, 184), width=1)
    draw.line([(stamp_x, stamp_y + 32), (2208, stamp_y + 32)], fill=(148, 163, 184), width=1)
    draw.line([(stamp_x + 90, stamp_y), (stamp_x + 90, stamp_y + 130)], fill=(148, 163, 184), width=1)
    
    draw.text((stamp_x + 10, stamp_y + 10), "图名 / Title", fill=(100, 116, 139), font=font_stamp)
    draw.text((stamp_x + 100, stamp_y + 10), "投资估算与经济测算图", fill=(15, 23, 42), font=font_stamp)
    
    draw.text((stamp_x + 10, stamp_y + 42), "图号 / No.", fill=(100, 116, 139), font=font_stamp)
    draw.text((stamp_x + 100, stamp_y + 42), "DR-074", fill=(15, 23, 42), font=font_stamp)
    
    draw.text((stamp_x + 10, stamp_y + 74), "作者 / Designer", fill=(100, 116, 139), font=font_stamp)
    draw.text((stamp_x + 100, stamp_y + 74), "你的铁北老伙计", fill=(15, 23, 42), font=font_stamp)
    
    draw.text((stamp_x + 10, stamp_y + 106), "单位 / Agency", fill=(100, 116, 139), font=font_stamp)
    draw.text((stamp_x + 100, stamp_y + 106), "吉林建筑大学建筑与规划学院", fill=(15, 23, 42), font=font_stamp)

    img.save(output_path)
    print(f"Directly generated vector economic map and saved to {output_path}")
    return view_w

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    pass
