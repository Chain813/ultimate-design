# -*- coding: utf-8 -*-
# tools/drawings/dr_037.py
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
    print("Drawing DR-037 custom vector map...")
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
    
    draw.text((55, 117), "设计原则与理念图", fill=(15, 23, 42), font=font_large_title, anchor="lm")
    draw.text((400, 117), "本项目的四大核心设计原则与更新理念，指导从空间诊断到智能方案生成的全生命周期。", 
              fill=(100, 116, 139), font=font_desc, anchor="lm")

    # 2. Left giant Map Card (X: 32 to 1584, Y: 206 to 1520)
    draw.rectangle([36, 210, 1588, 1524], fill=(226, 232, 240))
    draw.rectangle([32, 206, 1584, 1520], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 206, 1584, 212], fill=(217, 119, 6))

    draw.text((60, 250), "四项递进式设计原则与理念流 / PROGRESSIVE DESIGN PRINCIPLES", fill=(217, 119, 6), font=font_card_title)
    draw.line([(60, 280), (1556, 280)], fill=(226, 232, 240), width=2)

    # Coordinates:
    # Box 1: X: 100 to 720, Y: 340 to 790 (Center X=410, Y=565)
    # Box 2: X: 880 to 1500, Y: 340 to 790 (Center X=1190, Y=565)
    # Box 3: X: 100 to 720, Y: 920 to 1370 (Center X=410, Y=1145)
    # Box 4: X: 880 to 1500, Y: 920 to 1370 (Center X=1190, Y=1145)

    # Box 1: 保护优先 · 精准管控
    draw.rectangle([104, 344, 724, 794], fill=(241, 245, 249))
    draw.rectangle([100, 340, 720, 790], fill=(255, 255, 255), outline=(220, 38, 38), width=2)
    draw.rectangle([100, 340, 720, 360], fill=(220, 38, 38))
    draw.text((125, 395), "① 保护优先 · 精准管控", fill=(15, 23, 42), font=font_box_header)
    b1_text = "• 划定核心保护区、建设控制区与风貌协调区三级管控，严控开发强度。\n• 伪满皇宫核心区严禁大拆大建，所有更新活动遵循微创修缮与织补原则。\n• 维护传统肌理与视廊廊道控高（9m/18m/24m）底线约束。"
    wrapped_b1 = wrap_text_by_pixels(b1_text, font_body, 570, draw)
    y_text = 440
    for line in wrapped_b1:
        draw.text((125, y_text), line, fill=(71, 85, 105), font=font_body)
        y_text += 24

    # Box 2: 诊断先行 · 有机更新
    draw.rectangle([884, 344, 1504, 794], fill=(241, 245, 249))
    draw.rectangle([880, 340, 1500, 790], fill=(255, 255, 255), outline=(217, 119, 6), width=2)
    draw.rectangle([880, 340, 1500, 360], fill=(217, 119, 6))
    draw.text((905, 395), "② 诊断先行 · 有机更新", fill=(15, 23, 42), font=font_box_header)
    b2_text = "• 引入空间句法度量可达性，评估道路网络通达度与物理阻隔影响。\n• 结合语义分割网计算街道平均绿视率(均值8.7%)，挖掘空间品质硬伤。\n• POI活力分析辅助确定邻里细胞“生活盒子”等功能触媒的最佳植入位置。"
    wrapped_b2 = wrap_text_by_pixels(b2_text, font_body, 570, draw)
    y_text = 440
    for line in wrapped_b2:
        draw.text((905, y_text), line, fill=(71, 85, 105), font=font_body)
        y_text += 24

    # Box 3: 古今共振 · 活化再生
    draw.rectangle([104, 924, 724, 1374], fill=(241, 245, 249))
    draw.rectangle([100, 920, 720, 1370], fill=(255, 255, 255), outline=(124, 58, 237), width=2)
    draw.rectangle([100, 920, 720, 940], fill=(124, 58, 237))
    draw.text((125, 975), "③ 古今共振 · 活化再生", fill=(15, 23, 42), font=font_box_header)
    b3_text = "• 借助 AIGC 模型解构传统历史建筑语汇，重构地块平面方案与天际线风貌。\n• 推动中车老厂房遗存与历史遗留旧址等空间，与新功能、新产业共振活化。\n• 精准重塑伊通河生态廊道与滨水公共节点，使新旧肌理有机交融。"
    wrapped_b3 = wrap_text_by_pixels(b3_text, font_body, 570, draw)
    y_text = 1020
    for line in wrapped_b3:
        draw.text((125, y_text), line, fill=(71, 85, 105), font=font_body)
        y_text += 24

    # Box 4: 多元共治 · 数字协同
    draw.rectangle([884, 924, 1504, 1374], fill=(241, 245, 249))
    draw.rectangle([880, 920, 1500, 1370], fill=(255, 255, 255), outline=(5, 150, 105), width=2)
    draw.rectangle([880, 920, 1500, 940], fill=(5, 150, 105))
    draw.text((905, 975), "④ 多元共治 · 数字协同", fill=(15, 23, 42), font=font_box_header)
    b4_text = "• 搭建多利益方共享数字底盘，整合多时期权属，打通信息孤岛。\n• 利用多智能体模拟评估各利益方（居民-开发商-政府）对于新方案的满意度。\n• 实现数字孪生情景下的方案自动指标验算与图集一键导出发布。"
    wrapped_b4 = wrap_text_by_pixels(b4_text, font_body, 570, draw)
    y_text = 1020
    for line in wrapped_b4:
        draw.text((905, y_text), line, fill=(71, 85, 105), font=font_body)
        y_text += 24

    # Arrows
    # 1 -> 2 (Horizontal arrow)
    draw.line([(720, 565), (880 - 15, 565)], fill=(203, 213, 225), width=3)
    draw.polygon([(880 - 15, 565 - 6), (880 - 15, 565 + 6), (880 - 5, 565)], fill=(203, 213, 225))

    # 2 -> 3 (Stepped line arrow)
    draw.line([(1190, 790), (1190, 855)], fill=(203, 213, 225), width=3)
    draw.line([(1190, 855), (410, 855)], fill=(203, 213, 225), width=3)
    draw.line([(410, 855), (410, 920 - 15)], fill=(203, 213, 225), width=3)
    draw.polygon([(410 - 6, 920 - 15), (410 + 6, 920 - 15), (410, 920 - 5)], fill=(203, 213, 225))

    # 3 -> 4 (Horizontal arrow)
    draw.line([(720, 1145), (880 - 15, 1145)], fill=(203, 213, 225), width=3)
    draw.polygon([(880 - 15, 1145 - 6), (880 - 15, 1145 + 6), (880 - 5, 1145)], fill=(203, 213, 225))

    # 3. Right Top Card (X: 1608 to 2198, Y: 206 to 602)
    draw.rectangle([1612, 210, 2202, 606], fill=(226, 232, 240))
    draw.rectangle([1608, 206, 2198, 602], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1608, 206, 2198, 212], fill=(217, 119, 6))

    draw.text((1630, 240), "更新理念基本逻辑 / PHILOSOPHY", fill=(217, 119, 6), font=font_card_title)
    draw.line([(1630, 270), (2176, 270)], fill=(203, 213, 225), width=1)

    desc_lines = [
        "1. 保护优先：明确了在伪满皇宫等极其珍贵的历史街段，更新工作必须以保护文化根基为最高原则，拒绝盲目的大拆大建。",
        "2. 有机更新：指明了不再实行漫无目的地全面改造，而是基于客观多源数据的精准诊断（绿视率、POI、句法），在关键病灶“穴位”处进行定点微创干预活化。"
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

    draw.text((1630, 668), "设计理念执行说明 / PRINCIPLES", fill=(217, 119, 6), font=font_card_title)
    draw.line([(1630, 698), (2176, 698)], fill=(203, 213, 225), width=1)

    spec_lines = [
        "【古今共振】 指的是通过人工智能技术（AIGC）对传统建筑符号与肌理进行现代解译与生成，实现现代功能与历史风貌的和谐共生，而非粗暴地复刻或仿古建造。",
        "【数字协同】 强调在多源异构数字底盘的支撑下，运用大语言模型智能体（Multi-Agent）建立起协同机制，打破“长官意志”或“开发商独大”的传统更新决策缺陷，维护多利益方共享共治。"
    ]
    y_spec = 720
    for line in spec_lines:
        wrapped = wrap_text_by_pixels(line, font_desc, 510, draw)
        for wl in wrapped:
            draw.text((1630, y_spec), wl, fill=(71, 85, 105), font=font_desc)
            y_spec += 26
        y_spec += 10

    img.save(output_path)
    print(f"Directly generated vector design principles map and saved to {output_path}")
    return view_w

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    pass
