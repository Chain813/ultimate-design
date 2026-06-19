# -*- coding: utf-8 -*-
# tools/drawings/dr_083.py
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

NO_FRAME = True

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
    print("Drawing DR-083 custom vector map...")
    # Create canvas 2240x1584
    img = Image.new("RGB", (2240, 1584), color=(248, 250, 252)) # slate-50
    draw = ImageDraw.Draw(img)

    # Fonts
    font_path = 'C:/Windows/Fonts/msyh.ttc'
    font_bold_path = 'C:/Windows/Fonts/msyhbd.ttc'
    try:
        font_large_title = ImageFont.truetype(font_bold_path, 36)
        font_card_title = ImageFont.truetype(font_bold_path, 20)
        font_box_header = ImageFont.truetype(font_bold_path, 16)
        font_box_sub = ImageFont.truetype(font_bold_path, 12)
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
    
    draw.text((55, 117), "图册章节结构导图", fill=(15, 23, 42), font=font_large_title, anchor="lm")
    draw.text((400, 117), "基于“多源数据诊断—AI协同博弈—AIGC方案推演—数字孪生刚性核验”的规划设计图册章节结构体系。", 
              fill=(100, 116, 139), font=font_desc, anchor="lm")

    # 2. Left giant Map Card (X: 32 to 1584, Y: 206 to 1520)
    draw.rectangle([36, 210, 1588, 1524], fill=(226, 232, 240))
    draw.rectangle([32, 206, 1584, 1520], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 206, 1584, 212], fill=(217, 119, 6))

    draw.text((60, 250), "图册编制结构树 / ATLAS COMPILATION STRUCTURE", fill=(217, 119, 6), font=font_card_title)
    draw.line([(60, 280), (1556, 280)], fill=(226, 232, 240), width=2)

    # Root Node
    rx0, rx1, ry0, ry1 = 60, 310, 800, 920
    draw.rectangle([rx0+4, ry0+4, rx1+4, ry1+4], fill=(241, 245, 249))
    draw.rectangle([rx0, ry0, rx1, ry1], fill=(255, 255, 255), outline=(217, 119, 6), width=2)
    draw.rectangle([rx0, ry0, rx1, ry0+8], fill=(217, 119, 6))
    draw.text((rx0 + 15, ry0 + 35), "长春伪满皇宫周边", fill=(15, 23, 42), font=font_box_header)
    draw.text((rx0 + 15, ry0 + 65), "更新图册章节结构", fill=(15, 23, 42), font=font_box_header)
    draw.text((rx0 + 15, ry0 + 92), "ATLAS STRUCTURE", fill=(148, 163, 184), font=font_box_sub)

    # Chapters
    chapters = [
        {
            "id": 1, "y0": 320, "y1": 420, "color": (37, 99, 235), # Blue
            "title": "第1章 项目背景与概况", "sub": "PROJECT BACKGROUND",
            "sheets": "DR-003_项目背景与政策解读图、DR-004_现状区位图、DR-005_研究范围图"
        },
        {
            "id": 2, "y0": 550, "y1": 650, "color": (220, 38, 38), # Red
            "title": "第2章 现状调查与分析", "sub": "SITE INVESTIGATION",
            "sheets": "DR-013_遥感底图、DR-014_用地现状、DR-017_建筑高度、DR-018_风貌识别、DR-020_道路现状、DR-028_街区品质、DR-029_人群需求、DR-032_遗产价值评估"
        },
        {
            "id": 3, "y0": 780, "y1": 880, "color": (124, 58, 237), # Purple
            "title": "第3章 设计理念与构思", "sub": "CONCEPT & STRATEGY",
            "sheets": "DR-007_上位规划解读、DR-037_设计原则理念、DR-038_设计目标体系、DR-039_总体策略图"
        },
        {
            "id": 4, "y0": 1010, "y1": 1110, "color": (5, 150, 105), # Emerald
            "title": "第4章 总体方案设计", "sub": "MASTER PLAN DESIGN",
            "sheets": "DR-044_用地规划、DR-049_高度控制、DR-051_道路系统规划、DR-053_慢行系统规划、DR-055_公共空间系统、DR-046_产业业态规划、DR-056_绿地景观、DR-057_历史文化展示"
        },
        {
            "id": 5, "y0": 1240, "y1": 1340, "color": (217, 119, 6), # Amber
            "title": "第5章 重点地块设计", "sub": "KEY PLOT DESIGN",
            "sheets": "DR-081_AIGC技术推演、DR-082_近期实施分期、DR-076_五地块深化设计总图"
        }
    ]

    cx0, cx1 = 400, 720
    sx0, sx1 = 810, 1540

    for ch in chapters:
        # Draw connection from root to chapter
        mid_cy = (ch["y0"] + ch["y1"]) // 2
        draw.line([(rx1, 860), (rx1 + 30, 860)], fill=(203, 213, 225), width=2)
        draw.line([(rx1 + 30, 860), (rx1 + 30, mid_cy)], fill=(203, 213, 225), width=2)
        draw.line([(rx1 + 30, mid_cy), (cx0, mid_cy)], fill=(203, 213, 225), width=2)

        # Draw chapter box
        draw.rectangle([cx0+3, ch["y0"]+3, cx1+3, ch["y1"]+3], fill=(241, 245, 249))
        draw.rectangle([cx0, ch["y0"], cx1, ch["y1"]], fill=(255, 255, 255), outline=ch["color"], width=2)
        draw.rectangle([cx0, ch["y0"], cx1, ch["y0"]+8], fill=ch["color"])
        draw.text((cx0 + 15, ch["y0"] + 30), ch["title"], fill=(15, 23, 42), font=font_box_header)
        draw.text((cx0 + 15, ch["y0"] + 65), ch["sub"], fill=(148, 163, 184), font=font_box_sub)

        # Draw connection from chapter to sub-sheets box
        draw.line([(cx1, mid_cy), (sx0, mid_cy)], fill=(203, 213, 225), width=2)

        # Draw sub-sheets container card
        draw.rectangle([sx0+3, ch["y0"]+3, sx1+3, ch["y1"]+3], fill=(241, 245, 249))
        draw.rectangle([sx0, ch["y0"], sx1, ch["y1"]], fill=(255, 255, 255), outline=(226, 232, 240), width=2)
        draw.rectangle([sx0, ch["y0"], sx0+6, ch["y1"]], fill=ch["color"])

        # Wrap text for sub-sheets list
        draw.text((sx0 + 20, ch["y0"] + 15), "包含核心图纸：", fill=(100, 116, 139), font=font_body_bold)
        wrapped_sheets = wrap_text_by_pixels(ch["sheets"], font_body, sx1 - sx0 - 40, draw)
        y_text = ch["y0"] + 40
        for ws in wrapped_sheets[:2]: # Show max 2 lines
            draw.text((sx0 + 20, y_text), ws, fill=(71, 85, 105), font=font_body)
            y_text += 24

    # 3. Right Top Card (X: 1608 to 2198, Y: 206 to 602)
    draw.rectangle([1612, 210, 2202, 606], fill=(226, 232, 240))
    draw.rectangle([1608, 206, 2198, 602], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1608, 206, 2198, 212], fill=(217, 119, 6))

    draw.text((1630, 240), "章节逻辑解析 / CHAPTER LOGIC", fill=(217, 119, 6), font=font_card_title)
    draw.line([(1630, 270), (2176, 270)], fill=(203, 213, 225), width=1)

    desc_lines = [
        "1. 现状认知与诊断：由DR-003至DR-032构成，建立高分辨率遥感基底，精准算得用地、交通、高度现状及街道环境与文化资源病征。",
        "2. 刚性策略与控制：由DR-040至DR-049构成，承接上位规划限制，制定街区更新分区、控制性高度视廊指标。",
        "3. 系统方案与深化：由DR-051至DR-082构成，系统排布道路交通、慢行系统、蓝绿景观与近期实施地块分期。"
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

    draw.text((1630, 668), "图纸篇章对应说明 / SPECIFICATIONS", fill=(217, 119, 6), font=font_card_title)
    draw.line([(1630, 698), (2176, 698)], fill=(203, 213, 225), width=1)

    spec_lines = [
        "【认知篇】 图纸 DR-001 至 DR-013，侧重于规划研究范围划定、区位关系解析及遥感数据基底建立。",
        "【诊断篇】 图纸 DR-014 至 DR-030，对用地现状、建筑层高、历史风貌、可达性及环境品质进行定量测算。",
        "【策略篇】 图纸 DR-040 至 DR-049，提出更新分区模式，控制建筑改造强度与伪满皇宫周边的视廊限高。",
        "【方案篇】 图纸 DR-051 至 DR-082，详细规划路网交通、蓝绿景观系统、文化展示游线及近期实施时序。",
        "【技术支撑】 图纸 DR-083 至 DR-086，展示全周期的数字化计算、数据管线、工作流以及空间规划体系。"
    ]
    
    y_spec = 720
    for line in spec_lines:
        wrapped = wrap_text_by_pixels(line, font_desc, 510, draw)
        for wl in wrapped:
            draw.text((1630, y_spec), wl, fill=(71, 85, 105), font=font_desc)
            y_spec += 26
        y_spec += 8

    img.save(output_path)
    print(f"Directly generated vector structure mindmap and saved to {output_path}")
    return view_w

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    pass
