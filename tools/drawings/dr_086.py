# -*- coding: utf-8 -*-
# tools/drawings/dr_086.py
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
    print("Drawing DR-086 custom vector map...")
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
    
    draw.text((55, 117), "城乡规划知识体系导图", fill=(15, 23, 42), font=font_large_title, anchor="lm")
    draw.text((420, 117), "定位本规划设计在国家法定城乡规划与技术标准框架下的法理层级与用途管制逻辑。", 
              fill=(100, 116, 139), font=font_desc, anchor="lm")

    # 2. Left giant Map Card (X: 32 to 1584, Y: 206 to 1520)
    draw.rectangle([36, 210, 1588, 1524], fill=(226, 232, 240))
    draw.rectangle([32, 206, 1584, 1520], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 206, 1584, 212], fill=(217, 119, 6))

    draw.text((60, 250), "法定城乡规划与治理知识体系层级 / URBAN PLANNING FRAMEWORK", fill=(217, 119, 6), font=font_card_title)
    draw.line([(60, 280), (1556, 280)], fill=(226, 232, 240), width=2)

    # Level 1 Box
    draw.rectangle([84, 324, 1534, 484], fill=(241, 245, 249))
    draw.rectangle([80, 320, 1530, 480], fill=(255, 255, 255), outline=(37, 99, 235), width=2)
    draw.rectangle([80, 320, 1530, 340], fill=(37, 99, 235))
    draw.text((95, 365), "层级 1：规划法律法规与技术标准体系 (REGULATORY SYSTEM)", fill=(15, 23, 42), font=font_box_header)
    l1_text = "• 法律底盘：《中华人民共和国城乡规划法》《中华人民共和国土地管理法》规范规划编制的法定地位与审批流程。\n• 技术标准：《国土空间规划编制规程》《城市设计指南》《城市更新规划编制标准》指引本次毕业设计成果的科学性与规范度。"
    wrapped_l1 = wrap_text_by_pixels(l1_text, font_body, 1400, draw)
    y_text = 400
    for line in wrapped_l1:
        draw.text((95, y_text), line, fill=(71, 85, 105), font=font_body)
        y_text += 26

    # Level 2 Box (Planning Hierarchies)
    draw.rectangle([84, 554, 1534, 914], fill=(241, 245, 249))
    draw.rectangle([80, 550, 1530, 910], fill=(255, 255, 255), outline=(124, 58, 237), width=2)
    draw.rectangle([80, 550, 1530, 570], fill=(124, 58, 237))
    draw.text((95, 595), "层级 2：规划编制与深化层级 (PLANNING HIERARCHIES)", fill=(15, 23, 42), font=font_box_header)
    
    # 4 columns inside Level 2
    l2_cols = [
        ("总体规划 (Master Plan)", "规划“一核、一廊、多点”的总体空间结构，宏观层面划定用地骨架与红线。", (37, 99, 235), 100, 430),
        ("控制性详细规划 (控规)", "严格控制各街坊用地性质与伪满皇宫周边的视廊限高（9m/18m/24m）。", (220, 38, 38), 460, 790),
        ("修建性详细规划 (修规)", "深化五大地块总平面设计。核算容积率、绿地率（35%底线）与公服配套位置。", (5, 150, 105), 820, 1150),
        ("城市设计与实施指引", "制定建筑立面、历史遗存分类修缮指引。排布近期实施时序与地块分期节奏。", (217, 119, 6), 1180, 1510)
    ]
    for name, desc, col, x0, x1 in l2_cols:
        draw.rectangle([x0, 640, x1, 890], fill=(255, 255, 255), outline=(226, 232, 240), width=2)
        draw.rectangle([x0, 640, x1, 655], fill=col)
        draw.text((x0 + 12, 670), name, fill=(15, 23, 42), font=font_body_bold)
        wrapped_sub = wrap_text_by_pixels(desc, font_body, x1 - x0 - 24, draw)
        y_sub = 705
        for line in wrapped_sub:
            draw.text((x0 + 12, y_sub), line, fill=(71, 85, 105), font=font_body)
            y_sub += 24

    # Level 3 Box (Land Governance)
    draw.rectangle([84, 984, 1534, 1184], fill=(241, 245, 249))
    draw.rectangle([80, 980, 1530, 1180], fill=(255, 255, 255), outline=(5, 150, 105), width=2)
    draw.rectangle([80, 980, 1530, 1000], fill=(5, 150, 105))
    draw.text((95, 1025), "层级 3：空间开发用途管制与治理要素 (LAND GOVERNANCE)", fill=(15, 23, 42), font=font_box_header)
    l3_text = "• 三区三线管控：划定生态、城镇开发边界，实施空间准入与开发刚性管制，保护伊通河滨水生态走廊完整性。\n• 城市更新分类分区：划分保护修缮区（如中车老厂房遗存）、整治提升区、拆改更新区，分类引导建筑改造手段与强度。"
    wrapped_l3 = wrap_text_by_pixels(l3_text, font_body, 1400, draw)
    y_text = 1060
    for line in wrapped_l3:
        draw.text((95, y_text), line, fill=(71, 85, 105), font=font_body)
        y_text += 26

    # Level 4 Box (Delivery)
    draw.rectangle([84, 1254, 1534, 1454], fill=(241, 245, 249))
    draw.rectangle([80, 1250, 1530, 1450], fill=(255, 255, 255), outline=(217, 119, 6), width=2)
    draw.rectangle([80, 1250, 1530, 1270], fill=(217, 119, 6))
    draw.text((95, 1295), "层级 4：成果表达与落地交付 (DELIVERY & OUTPUTS)", fill=(15, 23, 42), font=font_box_header)
    l4_text = "• A3规划图集：统一卡片式无边框排版，输出包含区位现状、Space Syntax诊断、AIGC意向、修规总图在内的35张高精度图纸。\n• 规划设计导则：包含建筑分类更新控制表、地块分期实施计划、文字说明书，作为毕业设计核心文本汇报依据。"
    wrapped_l4 = wrap_text_by_pixels(l4_text, font_body, 1400, draw)
    y_text = 1330
    for line in wrapped_l4:
        draw.text((95, y_text), line, fill=(71, 85, 105), font=font_body)
        y_text += 26

    # Arrows connecting levels
    for y_arr in [515, 945, 1215]:
        draw.line([(805, y_arr), (805, y_arr + 30)], fill=(203, 213, 225), width=3)
        draw.polygon([(805 - 6, y_arr + 30), (805 + 6, y_arr + 30), (805, y_arr + 35)], fill=(203, 213, 225))

    # 3. Right Top Card (X: 1608 to 2198, Y: 206 to 602)
    draw.rectangle([1612, 210, 2202, 606], fill=(226, 232, 240))
    draw.rectangle([1608, 206, 2198, 602], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1608, 206, 2198, 212], fill=(217, 119, 6))

    draw.text((1630, 240), "规划体系逻辑解析 / PLANNING LOGIC", fill=(217, 119, 6), font=font_card_title)
    draw.line([(1630, 270), (2176, 270)], fill=(203, 213, 225), width=1)

    desc_lines = [
        "1. 法规依据：城乡规划法律法规为规划成果提供核心合法性与权威支撑，并由国土空间规程界定数据标准与图纸表达规范。",
        "2. 刚性与弹性：总体规划侧重宏观结构控制与用途准入，而控制性/修建性详细规划与城市设计则为微观地块开发提供指导与高度控高约束。"
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

    draw.text((1630, 668), "规划编制与管制说明 /编制导则", fill=(217, 119, 6), font=font_card_title)
    draw.line([(1630, 698), (2176, 698)], fill=(203, 213, 225), width=1)

    spec_lines = [
        "【五级编制体系】 国土空间规划分为国家级、省级、市级、县级、乡镇级，实现自上而下的规划指标分解与刚性管控约束。",
        "【三类规划类型】 包含总体规划（空间开发保护总纲）、详细规划（开发建设和整治依据）以及专项规划（特定领域专项）。",
        "【三区三线】 划定生态、农业、城镇三类空间，对应生态保护红线、永久基本农田、城镇开发边界三条红线，实行刚性管制。",
        "【工作流提示】 本工作流涵盖了总体规划、控制性与修建性详细规划、城市设计及其实施阶段的核心内容体系。"
    ]
    
    y_spec = 720
    for line in spec_lines:
        wrapped = wrap_text_by_pixels(line, font_desc, 510, draw)
        for wl in wrapped:
            draw.text((1630, y_spec), wl, fill=(71, 85, 105), font=font_desc)
            y_spec += 26
        y_spec += 8

    img.save(output_path)
    print(f"Directly generated vector planning knowledge map and saved to {output_path}")
    return view_w

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    pass
