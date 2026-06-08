# -*- coding: utf-8 -*-
# tools/drawings/dr_084.py
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

NO_FRAME = True

def wrap_text_by_pixels(text, font, max_width, draw):
    lines = []
    for block in text.split('\n'):
        current_line = ""
        for char in block:
            test_line = current_line + char
            w = draw.textlength(test_line, font=font)
            if w <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = char
        if current_line:
            lines.append(current_line)
    return lines

def draw_map_early(output_path, view_w, view_h, STATIC_DIR):
    print("Drawing DR-084 custom vector map...")
    # Create canvas 2240x1584
    img = Image.new("RGB", (2240, 1584), color=(248, 250, 252)) # slate-50
    draw = ImageDraw.Draw(img)

    # Fonts
    font_path = 'C:/Windows/Fonts/msyh.ttc'
    font_bold_path = 'C:/Windows/Fonts/msyhbd.ttc'
    try:
        font_large_title = ImageFont.truetype(font_bold_path, 36)
        font_card_title = ImageFont.truetype(font_bold_path, 20)
        font_box_header = ImageFont.truetype(font_bold_path, 18)
        font_box_sub = ImageFont.truetype(font_bold_path, 13)
        font_body = ImageFont.truetype(font_path, 14)
        font_body_bold = ImageFont.truetype(font_bold_path, 14)
        font_desc = ImageFont.truetype(font_path, 15)
    except IOError:
        font_large_title = ImageFont.load_default()
        font_card_title = ImageFont.load_default()
        font_box_header = ImageFont.load_default()
        font_box_sub = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_body_bold = ImageFont.load_default()
        font_desc = ImageFont.load_default()

    # Draw grid
    grid_spacing = 79.2
    for x in range(1, int(2240 / grid_spacing)):
        lx = int(x * grid_spacing)
        draw.line([(lx, 0), (lx, 1584)], fill=(226, 232, 240), width=1)
    for y in range(1, int(1584 / grid_spacing)):
        ly = int(y * grid_spacing)
        draw.line([(0, ly), (2240, ly)], fill=(226, 232, 240), width=1)

    # 1. Header Card (X: 32 to 2198, Y: 60 to 174)
    draw.rectangle([36, 64, 2202, 178], fill=(226, 232, 240))
    draw.rectangle([32, 60, 2198, 174], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 60, 2198, 66], fill=(217, 119, 6))
    
    draw.text((55, 117), "数据处理管线导图", fill=(15, 23, 42), font=font_large_title, anchor="lm")
    draw.text((380, 117), "规划研究范围的多源地理矢量数据、街景图像GVI语义分割及社交网络情绪文本的数据流清洗与分析管线。", 
              fill=(100, 116, 139), font=font_desc, anchor="lm")

    # 2. Left giant Map Card (X: 32 to 1584, Y: 206 to 1520)
    draw.rectangle([36, 210, 1588, 1524], fill=(226, 232, 240))
    draw.rectangle([32, 206, 1584, 1520], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 206, 1584, 212], fill=(217, 119, 6))

    draw.text((60, 250), "多源异构数据清洗与空间计算管线 / DATA PIPELINE PROCESSOR", fill=(217, 119, 6), font=font_card_title)
    draw.line([(60, 280), (1556, 280)], fill=(226, 232, 240), width=2)

    # Column 1: DATA INPUT
    # Column 2: SPATIAL COMPUTATION ENGINES
    # Column 3: TARGET DIGITAL TWIN DATABASE

    # Draw Column Labels
    draw.text((220, 310), "【数据源输入 / DATA INPUT】", fill=(100, 116, 139), font=font_body_bold, anchor="mm")
    draw.text((780, 310), "【空间计算引擎 / COMPUTATION】", fill=(100, 116, 139), font=font_body_bold, anchor="mm")
    draw.text((1340, 310), "【孪生空间库 / INTEGRATION】", fill=(100, 116, 139), font=font_body_bold, anchor="mm")

    # Y center coordinates for the 3 rows: 480, 830, 1180
    # Left Column boxes (X: 70 to 370)
    # Middle Column boxes (X: 630 to 930)
    # Right Column Box (X: 1190 to 1490, Y: 680 to 980)

    # Draw Left Boxes
    l_boxes = [
        ("地理矢量数据 (GIS)", "用地现状、路网、现状建筑层高", 480, (37, 99, 235)),
        ("社交文本情绪打卡", "微博、小红书定位文本与打卡情绪", 830, (124, 58, 237)),
        ("街角实景图像 (API)", "百度街景API自动按点位抓取图片", 1180, (5, 150, 105))
    ]
    for name, desc, y_center, color in l_boxes:
        draw.rectangle([74, y_center-96, 374, y_center+104], fill=(241, 245, 249))
        draw.rectangle([70, y_center-100, 370, y_center+100], fill=(255, 255, 255), outline=(226, 232, 240), width=2)
        draw.rectangle([70, y_center-100, 370, y_center-80], fill=color)
        draw.text((85, y_center - 50), name, fill=(15, 23, 42), font=font_box_header)
        wrapped = wrap_text_by_pixels(desc, font_body, 270, draw)
        y_text = y_center - 10
        for line in wrapped:
            draw.text((85, y_text), line, fill=(71, 85, 105), font=font_body)
            y_text += 24

    # Draw Middle Boxes
    m_boxes = [
        ("空间句法可达性计算", "使用Space Syntax度量步行可达性与车行选择度，精准计算路网物理连通性", 480, (37, 99, 235)),
        ("LLM 语义情感情感倾向分析", "使用大语言模型(NLP)分类打卡情感极性，定位噪声/环境/交通品质痛点", 830, (124, 58, 237)),
        ("PyTorch 图像语义分割", "使用DeepLabV3语义分割网络识别植物/天空比例，自动化计算街道绿视率(GVI)", 1180, (5, 150, 105))
    ]
    for name, desc, y_center, color in m_boxes:
        draw.rectangle([634, y_center-96, 934, y_center+104], fill=(241, 245, 249))
        draw.rectangle([630, y_center-100, 930, y_center+100], fill=(255, 255, 255), outline=(226, 232, 240), width=2)
        draw.rectangle([630, y_center-100, 930, y_center-80], fill=color)
        draw.text((645, y_center - 55), name, fill=(15, 23, 42), font=font_box_header)
        wrapped = wrap_text_by_pixels(desc, font_body, 270, draw)
        y_text = y_center - 20
        for line in wrapped:
            draw.text((645, y_text), line, fill=(71, 85, 105), font=font_body)
            y_text += 24

    # Draw Right Box
    draw.rectangle([1194, 734, 1494, 984], fill=(241, 245, 249))
    draw.rectangle([1190, 730, 1490, 980], fill=(255, 255, 255), outline=(217, 119, 6), width=2)
    draw.rectangle([1190, 730, 1490, 750], fill=(217, 119, 6))
    draw.text((1205, 780), "统一空间数据库 (GIS)", fill=(15, 23, 42), font=font_box_header)
    db_desc = "统一采用 EPSG:3857 投影坐标系，支持路网、现状高度、绿视率、情绪分类及用地层无缝集成叠加，用于智能指标验算。"
    wrapped_db = wrap_text_by_pixels(db_desc, font_body, 270, draw)
    y_text = 820
    for line in wrapped_db:
        draw.text((1205, y_text), line, fill=(71, 85, 105), font=font_body)
        y_text += 24

    # Draw horizontal arrows Left -> Middle
    for y_arr in [480, 830, 1180]:
        draw.line([(370 + 10, y_arr), (630 - 15, y_arr)], fill=(203, 213, 225), width=3)
        draw.polygon([(630 - 15, y_arr - 6), (630 - 15, y_arr + 6), (630 - 5, y_arr)], fill=(203, 213, 225))

    # Draw diagonal gather arrows Middle -> Right
    # From Middle Top (930, 480) to Right Center (1190, 830)
    draw.line([(930 + 10, 480), (1050, 480)], fill=(203, 213, 225), width=3)
    draw.line([(1050, 480), (1050, 800)], fill=(203, 213, 225), width=3)
    draw.line([(1050, 800), (1190 - 15, 800)], fill=(203, 213, 225), width=3)

    # From Middle Center (930, 830) to Right Center (1190, 830)
    draw.line([(930 + 10, 830), (1190 - 15, 830)], fill=(203, 213, 225), width=3)

    # From Middle Bottom (930, 1180) to Right Center (1190, 830)
    draw.line([(930 + 10, 1180), (1090, 1180)], fill=(203, 213, 225), width=3)
    draw.line([(1090, 1180), (1090, 860)], fill=(203, 213, 225), width=3)
    draw.line([(1090, 860), (1190 - 15, 860)], fill=(203, 213, 225), width=3)

    # Draw arrow heads on the right inputs
    for y_arr in [800, 830, 860]:
        draw.polygon([(1190 - 15, y_arr - 6), (1190 - 15, y_arr + 6), (1190 - 5, y_arr)], fill=(203, 213, 225))

    # 3. Right Top Card (X: 1608 to 2198, Y: 206 to 602)
    draw.rectangle([1612, 210, 2202, 606], fill=(226, 232, 240))
    draw.rectangle([1608, 206, 2198, 602], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1608, 206, 2198, 212], fill=(217, 119, 6))

    draw.text((1630, 240), "数据处理逻辑解析 / PIPELINE LOGIC", fill=(217, 119, 6), font=font_card_title)
    draw.line([(1630, 270), (2176, 270)], fill=(203, 213, 225), width=1)

    desc_lines = [
        "1. 地理矢量数据：包含路网、建筑轮廓、铁轨及公园绿地等 GIS 图层，作为空间底座并统一投影为 WGS-84 坐标系。",
        "2. 街景影像数据：通过百度街景 API 批量获取全域多视角图像，经由 PyTorch 深度语义分割网络计算街道绿视率（GVI）。",
        "3. 社交媒体文本：爬取微博和小红书的打卡文本与定位，使用自然语言处理模型分析情感倾向，识别环境与品质痛点。"
    ]
    
    y_desc = 295
    for line in desc_lines:
        wrapped = wrap_text_by_pixels(line, font_desc, 510, draw)
        for wl in wrapped:
            draw.text((1630, y_desc), wl, fill=(71, 85, 105), font=font_desc)
            y_desc += 26
        y_desc += 10

    # 4. Right Bottom Card (X: 1608 to 2198, Y: 634 to 1520)
    draw.rectangle([1612, 638, 2202, 1524], fill=(226, 232, 240))
    draw.rectangle([1608, 634, 2198, 1520], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1608, 634, 2198, 640], fill=(217, 119, 6))

    draw.text((1630, 668), "数据融合计算说明 / INTEGRATION", fill=(217, 119, 6), font=font_card_title)
    draw.line([(1630, 698), (2176, 698)], fill=(203, 213, 225), width=1)

    spec_lines = [
        "1. 原始数据获取：抓取社交媒体（微博、小红书）POI 及街景影像，以及获取高分辨率卫星遥感、建筑轮廓与路网 GIS 矢量底数据。",
        "2. 空间计算与清洗：包含空间句法（Space Syntax）全局拓扑计算、街景图像绿视率（GVI）分割，以及多源 POI 的空间落点清洗融合。",
        "3. LLM智能体分析：利用大语言模型（LLM）对收集到的居民反馈与文本数据进行情感倾向分析，生成品质痛点坐标信息并写入地理要素。"
    ]
    
    y_spec = 720
    for line in spec_lines:
        wrapped = wrap_text_by_pixels(line, font_desc, 510, draw)
        for wl in wrapped:
            draw.text((1630, y_spec), wl, fill=(71, 85, 105), font=font_desc)
            y_spec += 26
        y_spec += 10

    img.save(output_path)
    print(f"Directly generated vector data pipeline map and saved to {output_path}")
    return view_w

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    pass
