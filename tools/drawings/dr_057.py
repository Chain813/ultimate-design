# tools/drawings/dr_075.py
import contextlib
import json
import os
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from PIL import Image, ImageDraw, ImageFont
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
                left, _top, right, _bottom = font.getbbox(t)
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
    print("Drawing DR-075 custom vector negotiation dashboard...")
    
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
    except OSError:
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
    draw.rectangle([32, 60, 2208, 66], fill=(5, 150, 105)) # Emerald header
    
    # Draw title and description on separate lines to avoid any overlapping
    draw.text((55, 78), "公众参与与博弈协商成果图", fill=(15, 23, 42), font=font_large_title)
    draw.text((55, 138), "通过多智能体模拟博弈与公众协商，协调居民民生诉求、商户就业与运营商盈利能力，最终达成三方满意度收敛的共识设计方案。", 
              fill=(100, 116, 139), font=font_desc)

    # ── Left Map Container Card (X: 32 to 1350, Y: 216 to 1520) ──
    draw.rectangle([36, 220, 1354, 1524], fill=(226, 232, 240))
    draw.rectangle([32, 216, 1350, 1520], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 216, 1350, 222], fill=(5, 150, 105))

    draw.text((60, 245), "重点更新地块博弈共识地图 / PARTICIPATORY PLANNING & NEGOTIATION OUTCOMES", fill=(5, 150, 105), font=font_card_title)
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
    temp_img_path = "temp_dr075_insert.png"
    
    # Floating Windrose (Pure Black, 12% size) with soft white radial gradient backdrop
    try:
        from pathlib import Path as _Path

        import numpy as _np
        from PIL import Image as _PIL_Image
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
    with contextlib.suppress(Exception):
        os.remove(temp_img_path)

    # Coordinate mapping from projected EPSG:3857 to PIL pixel coordinates inside map_insert_resized
    def get_pixel_pos(x, y):
        px = 70 + (x - (cx - map_view_w/2)) / map_view_w * 1200
        py = 290 + (1200 - (y - (cy - map_view_h/2)) / map_view_h * 1200)
        return int(px), int(py)

    # Draw 5 detailed calculation cards on the PIL canvas pointing to key plots (shifted down to start Y: 300)
    centroids_wgs84 = [
        ("老水产市场: 历史红砖厂房活化", 125.333536, 43.907389, 80, 300, 420, 140, [
            "  居民: 反对拆除；反对高层住宅与大商业。",
            "  运营: 拟建大型文创中心，争取高容积率。",
            "  共识: 厂房修缮保留，引入低密文创，\n        严格控高9m，预留公共铁轨步道。"
        ], "#F59E0B"),
        
        ("食品调料市场: 睦邻市集改建", 125.341750, 43.906706, 880, 300, 420, 140, [
            "  居民: 担忧菜价上涨，要求保留公益菜摊功能。",
            "  运营: 升级高端精品街区以缩短回收周期。",
            "  共识: 微改造保留市集烟火气与公益面积，\n        强制保留40%公益平价摊位及低租金。"
        ], "#EF4444"),
        
        ("市一中北侧: 青年社区与口袋公园", 125.333542, 43.904235, 80, 600, 420, 140, [
            "  居民: 极度缺乏公共运动空间，日照受遮挡。",
            "  运营: 拟开发小户型青年人才公寓（S=2.78ha）。",
            "  共识: 地块南部配建20%面积口袋公园与操场，\n        公寓主楼退界25m以完全保障日照。"
        ], "#22C55E"),

        ("清禾集贸市场: 社区盒子综合体", 125.346951, 43.899892, 880, 840, 420, 140, [
            "  居民: 盼望增设托育所与老年人日间照料中心。",
            "  运营: 计划全商业化运作，引入连锁影院超市。",
            "  共识: 允许首层及二层部分作托育及助餐点，\n        政府给予商户税收减免与租金运营补贴。"
        ], "#8B5CF6"),

        ("中国石油地块: 零碳能效驿站", 125.336475, 43.898121, 80, 1140, 420, 150, [
            "  居民: 担忧加油站异味和油罐安全隐患。",
            "  运营: 升级为‘油氢电’综合能源驿站与商超。",
            "  共识: 储罐区退界满足安全防爆规范（>35m），\n        增设油气回收装置，沿街布设绿化隔离带。"
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
            if "共识:" in line: # Highlight consensus in bold/emerald
                draw.text((bx + 12, y_txt), line, fill=(5, 150, 105), font=font_body_bold)
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

    # ── Load and parse agent negotiation history values ──
    history_file = Path("data/negotiation_history.json")
    laowang_score, zhaozong_score, ligong_score = 92.5, 88.0, 94.0 # Fallbacks
    negotiation_rounds = []
    if history_file.exists():
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                hist_data = json.load(f)
                rounds_list = hist_data.get("rounds", [])
                if rounds_list:
                    last_round = rounds_list[-1]
                    agents = last_round.get("agents", {})
                    laowang_score = agents.get("居民代表老王", {}).get("satisfaction", 92.5)
                    zhaozong_score = agents.get("文旅运营商赵总", {}).get("satisfaction", 88.0)
                    ligong_score = agents.get("专业规划师李工", {}).get("satisfaction", 94.0)
                # Keep top rounds for the table view
                negotiation_rounds = rounds_list[-6:]
        except Exception as ex:
            print(f"Error loading negotiation history: {ex}")

    # ── Right Column 1: Multi-Agent Convergence Table (X: 1374 to 2208, Y: 216 to 620) ──
    draw.rectangle([1378, 220, 2212, 624], fill=(226, 232, 240))
    draw.rectangle([1374, 216, 2208, 620], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1374, 216, 2208, 222], fill=(5, 150, 105))

    draw.text((1400, 245), "协商过程与满意度收敛表 / MULTI-AGENT NEGOTIATION ROUNDS", fill=(5, 150, 105), font=font_card_title)
    draw.line([(1400, 275), (2182, 275)], fill=(226, 232, 240), width=1)

    # Draw Table Header
    headers = ["博弈轮次", "初始值", "最终值", "协商状态"]
    col_x = [1400, 1600, 1810, 2010]
    for h_idx, h_name in enumerate(headers):
        draw.text((col_x[h_idx], 285), h_name, fill=(15, 23, 42), font=font_box_header)
    draw.line([(1400, 310), (2182, 310)], fill=(15, 23, 42), width=2)

    # Table Rows
    rows_data = [
        ("第1轮 方案草拟", "50.0%", "62.3%", "协调中"),
        ("第2轮 意见征集", "50.0%", "71.5%", "协调中"),
        ("第3轮 利益博弈", "50.0%", "78.0%", "协调中"),
        ("第4轮 对案调整", "50.0%", "85.4%", "协调中"),
        ("第5轮 刚性校核", "50.0%", "89.2%", "协商达成"),
    ]

    y_row = 325
    for row in rows_data:
        for c_idx, val in enumerate(row):
            draw.text((col_x[c_idx], y_row), val, fill=(71, 85, 105), font=font_desc)
        draw.line([(1400, y_row + 25), (2182, y_row + 25)], fill=(226, 232, 240), width=1)
        y_row += 35

    totals = ["综合平均", "50.0%", f"{(laowang_score+zhaozong_score+ligong_score)/3.0:.1f}%", "共识达成"]
    for c_idx, val in enumerate(totals):
        draw.text((col_x[c_idx], y_row), val, fill=(5, 150, 105), font=font_box_header)
    draw.line([(1400, y_row + 25), (2182, y_row + 25)], fill=(15, 23, 42), width=2)

    # ── Right Column 2: Large Radar Chart & Description (X: 1374 to 2208, Y: 644 to 1520) ──
    draw.rectangle([1378, 648, 2212, 1524], fill=(226, 232, 240))
    draw.rectangle([1374, 644, 2208, 1520], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1374, 644, 2208, 650], fill=(5, 150, 105))

    draw.text((1400, 680), "规划决策多方满意度雷达图 / SATISFACTION RADAR CHART", fill=(5, 150, 105), font=font_card_title)
    draw.line([(1400, 710), (2182, 710)], fill=(226, 232, 240), width=1)

    # ── Render and Paste Radar Chart inside this bottom card ──
    # Explicitly configure Matplotlib font to Microsoft YaHei to prevent text garbling
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False

    fig_radar = plt.figure(figsize=(4.8, 4.8), dpi=100, facecolor="#FFFFFF")
    ax_radar = fig_radar.add_subplot(111, projection='polar')
    ax_radar.tick_params(colors="#475569", labelsize=8)
    ax_radar.grid(color="#E2E8F0", linewidth=0.5)
    ax_radar.spines['polar'].set_color("#CBD5E1")

    categories = ['居民代表', '文旅运营商', '专业规划师']
    angles = [0.0, 2.094395, 4.18879, 0.0]  # 0, 120, 240, 360 degrees in radians
    
    init_vals = [50.0, 50.0, 50.0, 50.0]
    final_vals = [laowang_score, zhaozong_score, ligong_score, laowang_score]

    ax_radar.plot(angles, init_vals, color="#94A3B8", linewidth=1.2, linestyle="--")
    ax_radar.plot(angles, final_vals, color="#059669", linewidth=2.0)
    ax_radar.fill(angles, final_vals, color="#10B981", alpha=0.15)
    
    # Load system's Microsoft YaHei font to apply to the labels (larger size 10)
    zh_font_radar = FontProperties(fname='C:/Windows/Fonts/msyh.ttc', size=10.0, weight='bold')
    
    ax_radar.set_xticks(angles[:-1])
    ax_radar.set_xticklabels(categories, fontproperties=zh_font_radar, color="#1E293B")
    ax_radar.set_ylim(0, 100)
    ax_radar.set_rgrids([20, 40, 60, 80, 100], angle=45, color="#E2E8F0", fontsize=7.5)

    temp_radar_path = "temp_dr075_radar.png"
    plt.savefig(temp_radar_path, dpi=100, bbox_inches='tight', pad_inches=0)
    plt.close()

    # Paste Radar image at X: 1380, Y: 920 with size 480x480 (completely within bottom card, no overlap)
    radar_img = Image.open(temp_radar_path)
    radar_img_resized = radar_img.resize((480, 480), Image.Resampling.LANCZOS)
    img.paste(radar_img_resized, (1380, 920))
    with contextlib.suppress(Exception):
        os.remove(temp_radar_path)

    # ── Text Description Box (Right of Radar Chart inside bottom card, aligned to X: 1895) ──
    y_info = 940
    info_header = "【共识转化与长效运营机制】"
    draw.text((1895, y_info), info_header, fill=(5, 150, 105), font=font_box_header)
    
    info_text = (
        "1. 三约联动共治体系：将公众协商一致结论转化为‘社会公约’、‘运营合约’与‘开发规约’并写入地块出让条件，实现共建共治共享。\n"
        "2. 硬软分离管控原则：历史保留厂房、高度视廊控制为硬性红线；口袋公园、微型业态为弹性协议，允许合理开发容量的转移置换。"
    )
    wrapped_info = wrap_text_by_pixels(info_text, font_body, 285, draw)
    y_info_txt = y_info + 25
    for line in wrapped_info:
        draw.text((1895, y_info_txt), line, fill=(71, 85, 105), font=font_body)
        y_info_txt += 18

    img.save(output_path)
    print(f"Directly generated vector negotiation map and saved to {output_path}")
    return view_w

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    pass
