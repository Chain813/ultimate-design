# tools/drawings/dr_155.py
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

NO_FRAME = True

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
    print("Drawing DR-083 custom vector map...")
    # Create canvas 2240x1584
    img = Image.new("RGB", (2240, 1584), color=(248, 250, 252)) # slate-50
    draw = ImageDraw.Draw(img)

    # Fonts
    font_path = 'C:/Windows/Fonts/msyh.ttc'
    font_bold_path = 'C:/Windows/Fonts/msyhbd.ttc'
    try:
        font_large_title = ImageFont.truetype(font_bold_path, 40)
        font_card_title = ImageFont.truetype(font_bold_path, 28)
        font_box_header = ImageFont.truetype(font_bold_path, 22)
        font_box_sub = ImageFont.truetype(font_bold_path, 16)
        font_body = ImageFont.truetype(font_path, 18)
        font_body_bold = ImageFont.truetype(font_bold_path, 18)
        font_desc = ImageFont.truetype(font_path, 18)
    except OSError:
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
    rx0, rx1, ry0, ry1 = 60, 310, 800, 930
    draw.rectangle([rx0+4, ry0+4, rx1+4, ry1+4], fill=(241, 245, 249))
    draw.rectangle([rx0, ry0, rx1, ry1], fill=(255, 255, 255), outline=(217, 119, 6), width=2)
    draw.rectangle([rx0, ry0, rx1, ry0+8], fill=(217, 119, 6))
    draw.text((rx0 + 15, ry0 + 35), "长春伪满皇宫周边", fill=(15, 23, 42), font=font_box_header)
    draw.text((rx0 + 15, ry0 + 65), "更新图册章节结构", fill=(15, 23, 42), font=font_box_header)
    draw.text((rx0 + 15, ry0 + 92), "ATLAS STRUCTURE", fill=(148, 163, 184), font=font_box_sub)

    # Chapters
    chapters = [
        {
            "id": 1, "y0": 280, "y1": 430, "color": (37, 99, 235), # Blue
            "title": "第1章 项目认知篇", "sub": "PROJECT COGNITION",
            "sheets": "DR-003_项目背景与政策解读图、DR-004_现状区位图、DR-005_研究范围图、DR-006_原始数据清单、DR-007_上位规划解读图、DR-008_上位专项规划解读图、DR-009_案例借鉴与对标分析图",
            "max_lines": 3
        },
        {
            "id": 2, "y0": 460, "y1": 645, "color": (220, 38, 38), # Red
            "title": "第2章 数据诊断篇", "sub": "DATA DIAGNOSIS",
            "sheets": "DR-010_数据来源与遥感现状图、DR-011_用地现状分析图、DR-012_道路交通现状图、DR-013_建筑高度现状图、DR-014_建筑风貌识别图, DR-015_环境品质问题地图、DR-016_街区景观品质分析图、DR-017_历史建筑与工业遗产分布图、DR-018_文化资源分析图、DR-019_遗产价值评估热力图、DR-020_POI产业活力分析图、DR-021_人群需求与老龄化分布图、DR-022_空间句法可达性分析图、DR-023_综合现状问题诊断图、DR-024_MPI更新潜力评估图",
            "max_lines": 4
        },
        {
            "id": 3, "y0": 675, "y1": 860, "color": (124, 58, 237), # Purple
            "title": "第3章 设计理念与构思篇", "sub": "CONCEPT & VISION",
            "sheets": "DR-025_核心算法与数学公式、DR-026_平台核心代码清单、DR-027_规划设计依据、DR-028_规划设计原则、DR-029_规划设计目标、DR-030_规划设计定位、DR-031_规划设计策略、DR-032_设计原则与理念图、DR-033_设计目标体系图、DR-034_总体策略图",
            "max_lines": 4
        },
        {
            "id": 4, "y0": 890, "y1": 1105, "color": (5, 150, 105), # Emerald
            "title": "第4章 总体规划篇", "sub": "MASTER PLANNING",
            "sheets": "DR-035_更新模式分区图、DR-036_空间结构规划图、DR-037_用地规划图、DR-038_用地规划图_带建筑轮廓、DR-039_用地规划指标表、DR-040_产业业态规划图、DR-041_建筑更新控制图、DR-042_建筑高度控制图、DR-043_道路交通系统规划图、DR-044_慢行系统规划图、DR-045_公共空间系统图、DR-046_绿地景观系统图、DR-047_历史文化展示系统图、DR-048_总体鸟瞰白模效果图、DR-049_总体鸟瞰白模_彩色总图、DR-050_日照与风环境分析图、DR-051_功能分区与策划定位图、DR-052_开发强度与容积率分区策略图、DR-053_天际线与视觉通廊控制图、DR-054_竖向规划与排水分析图、DR-055_智慧城市与数字基础设施规划图、DR-056_投资估算与经济测算图、DR-057_公众参与与博弈协商成果图",
            "max_lines": 5
        },
        {
            "id": 5, "y0": 1135, "y1": 1450, "color": (217, 119, 6), # Amber
            "title": "第5章 重点地块设计", "sub": "KEY PLOT DESIGN",
            "sheets": "DR-058_五地块深化设计总图、DR-059_AIGC技术推演过程图、DR-060_实施分期图、DR-061~081_老水产市场更新方案图集、DR-082~101_食品调料市场更新方案图集、DR-102~120_市一中北侧地块更新方案图集、DR-121~138_清禾集贸市场更新方案图集、DR-139~154_中国石油地块更新方案图集",
            "max_lines": 8
        }
    ]

    cx0, cx1 = 400, 720
    sx0, sx1 = 810, 1540

    for ch in chapters:
        # Draw connection from root to chapter
        mid_cy = (ch["y0"] + ch["y1"]) // 2
        draw.line([(rx1, 865), (rx1 + 30, 865)], fill=(203, 213, 225), width=2)
        draw.line([(rx1 + 30, 865), (rx1 + 30, mid_cy)], fill=(203, 213, 225), width=2)
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
        max_l = ch.get("max_lines", 2)
        if len(wrapped_sheets) > max_l:
            wrapped_sheets = [*wrapped_sheets[:max_l - 1], wrapped_sheets[max_l - 1] + "...等"]
        for ws in wrapped_sheets:
            draw.text((sx0 + 20, y_text), ws, fill=(71, 85, 105), font=font_body)
            y_text += 32

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
            y_desc += 32
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
            y_spec += 32
        y_spec += 8

    img.save(output_path)
    print(f"Directly generated vector structure mindmap and saved to {output_path}")
    return view_w

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    pass
