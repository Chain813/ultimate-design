# -*- coding: utf-8 -*-
# tools/drawings/dr_081.py
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
    print("Drawing DR-081 custom vector map...")
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
    
    draw.text((55, 117), "AIGC 技术推演过程图", fill=(15, 23, 42), font=font_large_title, anchor="lm")
    draw.text((450, 117), "基于大语言模型协同协商与Stable Diffusion+ControlNet的街区天际线风貌与平面图推演生成工作流。", 
              fill=(100, 116, 139), font=font_desc, anchor="lm")

    # 2. Left giant Map Card (X: 32 to 1584, Y: 206 to 1520)
    draw.rectangle([36, 210, 1588, 1524], fill=(226, 232, 240))
    draw.rectangle([32, 206, 1584, 1520], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 206, 1584, 212], fill=(217, 119, 6))

    draw.text((60, 250), "智能推演工作流管线 / DESIGN PIPELINE WORKFLOW", fill=(217, 119, 6), font=font_card_title)
    draw.line([(60, 280), (1556, 280)], fill=(226, 232, 240), width=2)

    # Draw Flowchart Pipeline Boxes
    boxes = [
        {
            "x0": 80, "x1": 380, "color": (37, 99, 235), # Blue
            "title": "1. 数据底座", "sub": "多源数据采集与诊断",
            "items": [
                "• GIS矢量图层数据导入",
                "  - 伪满皇宫周边路网",
                "  - 现状建筑层高与轮廓",
                "• 百度街景API自动爬取",
                "  - 图像深度语义分割(GVI)",
                "• 社交媒体打卡文本爬取",
                "  - 情感分析情绪痛点定位"
            ]
        },
        {
            "x0": 450, "x1": 750, "color": (124, 58, 237), # Purple
            "title": "2. 协同博弈", "sub": "多智能体模拟与协商",
            "items": [
                "• 居民智能体 (老王)",
                "  - 适老设施、生活便利",
                "• 开发商智能体 (赵总)",
                "  - 商业活力、投资收益",
                "• 规划师智能体 (李工)",
                "  - 天际线高度限制指标",
                "• LLM多智能体冲突协商"
            ]
        },
        {
            "x0": 820, "x1": 1120, "color": (5, 150, 105), # Emerald
            "title": "3. 智能生成", "sub": "AIGC 规划方案推演",
            "items": [
                "• ControlNet 空间语义约束",
                "  - 手绘总规草图输入",
                "• SD大模型风貌推演",
                "  - 建筑立面协调性控制",
                "  - 节点天际线风貌生成",
                "• 100+意向方案迭代生成",
                "• 多维视觉方案评选"
            ]
        },
        {
            "x0": 1190, "x1": 1490, "color": (217, 119, 6), # Amber
            "title": "4. 指标核验", "sub": "数字孪生刚性指标验算",
            "items": [
                "• 方案矢量化导回GIS库",
                "• 用地性质/绿地率核算",
                "  - 绿地率35%刚性核验",
                "• 建筑限高与天际线核算",
                "  - 伪满皇宫周边视廊审查",
                "• 自动排版图册与规划导则"
            ]
        }
    ]

    for b in boxes:
        # shadow
        draw.rectangle([b["x0"]+4, 354, b["x1"]+4, 1374], fill=(241, 245, 249))
        # main
        draw.rectangle([b["x0"], 350, b["x1"], 1370], fill=(255, 255, 255), outline=(226, 232, 240), width=2)
        # header strip
        draw.rectangle([b["x0"], 350, b["x1"], 420], fill=b["color"])
        # title inside header
        draw.text((b["x0"] + 15, 370), b["title"], fill=(255, 255, 255), font=font_box_header)
        draw.text((b["x0"] + 15, 395), b["sub"], fill=(230, 242, 255), font=font_box_sub)

        # list items
        y_item = 450
        for item in b["items"]:
            # Highlight bullet points or bold lines
            if item.startswith("•"):
                draw.text((b["x0"] + 15, y_item), item, fill=(15, 23, 42), font=font_body_bold)
            else:
                draw.text((b["x0"] + 15, y_item), item, fill=(71, 85, 105), font=font_body)
            y_item += 35

    # Draw connection arrows between boxes
    arrows = [(380, 450, 750), (750, 820, 750), (1120, 1190, 750)]
    for x_start, x_end, y_arr in arrows:
        # Line
        draw.line([(x_start + 10, y_arr), (x_end - 15, y_arr)], fill=(203, 213, 225), width=3)
        # Arrowhead
        draw.polygon([(x_end - 15, y_arr - 6), (x_end - 15, y_arr + 6), (x_end - 5, y_arr)], fill=(203, 213, 225))

    # 3. Right Top Card (X: 1608 to 2198, Y: 206 to 602)
    draw.rectangle([1612, 210, 2202, 606], fill=(226, 232, 240))
    draw.rectangle([1608, 206, 2198, 602], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1608, 206, 2198, 212], fill=(217, 119, 6))

    draw.text((1630, 240), "技术板块解析 / SYSTEM ANALYSIS", fill=(217, 119, 6), font=font_card_title)
    draw.line([(1630, 270), (2176, 270)], fill=(203, 213, 225), width=1)

    desc_lines = [
        "1. 数据底盘：整合多源城市空间矢量与非结构化社交文本，提供精准的空间病征和痛点坐标定位。",
        "2. 定量诊断：运行空间句法与街景分割算法，实现步行可达性与街道绿视率的自动化精准度量。",
        "3. 方案生成：结合Stable Diffusion与ControlNet深度学习模型，输入意向草图自动生成设计效果。"
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

    draw.text((1630, 668), "规划指标说明 / SPECIFICATIONS", fill=(217, 119, 6), font=font_card_title)
    draw.line([(1630, 698), (2176, 698)], fill=(203, 213, 225), width=1)

    spec_lines = [
        "1. 技术框架：融合GIS底盘、Space Syntax可达性分析、以及MPI综合品质诊断，对170公顷历史风貌区进行全域数字孪生本底诊断建模。",
        "2. AIGC推演：以规划手绘草图或意向图作为ControlNet约束输入，通过SD大模型自动推演建筑立面风貌、开放空间效果，生成100+意向方案。",
        "3. 协同优化：构建包含“政府-居民-开发商-规划师”的LLM多智能体（Multi-Agent）协同博弈机制，对设计方案指标进行多目标评估与优化闭环。"
    ]
    
    y_spec = 720
    for line in spec_lines:
        wrapped = wrap_text_by_pixels(line, font_desc, 510, draw)
        for wl in wrapped:
            draw.text((1630, y_spec), wl, fill=(71, 85, 105), font=font_desc)
            y_spec += 26
        y_spec += 10

    img.save(output_path)
    print(f"Directly generated vector flow image and saved to {output_path}")
    return view_w

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    pass
