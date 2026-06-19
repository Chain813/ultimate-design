# -*- coding: utf-8 -*-
# tools/drawings/dr_085.py
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
    print("Drawing DR-085 custom vector map...")
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
    
    draw.text((55, 117), "规划协同工作流程图", fill=(15, 23, 42), font=font_large_title, anchor="lm")
    draw.text((400, 117), "模拟“政府-居民-开发商-规划师”的多利益主体博弈协同，依托大语言模型化解更新指标冲突的闭环流程。", 
              fill=(100, 116, 139), font=font_desc, anchor="lm")

    # 2. Left giant Map Card (X: 32 to 1584, Y: 206 to 1520)
    draw.rectangle([36, 210, 1588, 1524], fill=(226, 232, 240))
    draw.rectangle([32, 206, 1584, 1520], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 206, 1584, 212], fill=(217, 119, 6))

    draw.text((60, 250), "多利益主体 Multi-Agent 协同规划博弈逻辑 / COLLABORATION WORKFLOW", fill=(217, 119, 6), font=font_card_title)
    draw.line([(60, 280), (1556, 280)], fill=(226, 232, 240), width=2)

    # Coordinates:
    # Resident Node: X: 80 to 420, Y: 330 to 580 (Center: 250, 455)
    # Developer Node: X: 80 to 420, Y: 750 to 1000 (Center: 250, 875)
    # Planner Node: X: 80 to 420, Y: 1170 to 1420 (Center: 250, 1295)
    # Debate Center Node: X: 640 to 980, Y: 700 to 1050 (Center: 810, 875)
    # Outcome Node: X: 1200 to 1500, Y: 750 to 1000 (Center: 1350, 875)

    # 1. Resident Node
    draw.rectangle([84, 334, 424, 584], fill=(241, 245, 249))
    draw.rectangle([80, 330, 420, 580], fill=(255, 255, 255), outline=(37, 99, 235), width=2)
    draw.rectangle([80, 330, 420, 350], fill=(37, 99, 235))
    draw.text((95, 380), "居民代表智能体 (老王)", fill=(15, 23, 42), font=font_box_header)
    res_text = "核心诉求：增设养老院、托儿所与口袋绿地，保留历史老树与街区旧记忆，保障步行生活便利性。"
    wrapped_res = wrap_text_by_pixels(res_text, font_body, 310, draw)
    y_text = 420
    for line in wrapped_res:
        draw.text((95, y_text), line, fill=(71, 85, 105), font=font_body)
        y_text += 24

    # 2. Developer Node
    draw.rectangle([84, 754, 424, 1004], fill=(241, 245, 249))
    draw.rectangle([80, 750, 420, 1000], fill=(255, 255, 255), outline=(220, 38, 38), width=2)
    draw.rectangle([80, 750, 420, 770], fill=(220, 38, 38))
    draw.text((95, 800), "开发商代表智能体 (赵总)", fill=(15, 23, 42), font=font_box_header)
    dev_text = "核心诉求：合理开发文创街区与科创办公，适当提高容积率，打造特色商业IP，保障商业投资回报率。"
    wrapped_dev = wrap_text_by_pixels(dev_text, font_body, 310, draw)
    y_text = 840
    for line in wrapped_dev:
        draw.text((95, y_text), line, fill=(71, 85, 105), font=font_body)
        y_text += 24

    # 3. Planner Node
    draw.rectangle([84, 1174, 424, 1424], fill=(241, 245, 249))
    draw.rectangle([80, 1170, 420, 1420], fill=(255, 255, 255), outline=(5, 150, 105), width=2)
    draw.rectangle([80, 1170, 420, 1190], fill=(5, 150, 105))
    draw.text((95, 1220), "规划师代表智能体 (李工)", fill=(15, 23, 42), font=font_box_header)
    plan_text = "核心诉求：遵守伪满皇宫视廊控高（9m/18m/24m），确保红线与绿地率不突破35%红线，保障生态廊道完整性。"
    wrapped_plan = wrap_text_by_pixels(plan_text, font_body, 310, draw)
    y_text = 1260
    for line in wrapped_plan:
        draw.text((95, y_text), line, fill=(71, 85, 105), font=font_body)
        y_text += 24

    # 4. LLM Debate Center
    draw.rectangle([644, 704, 984, 1054], fill=(241, 245, 249))
    draw.rectangle([640, 700, 980, 1050], fill=(255, 255, 255), outline=(124, 58, 237), width=3)
    draw.rectangle([640, 700, 980, 725], fill=(124, 58, 237))
    draw.text((660, 750), "LLM 协同博弈核心", fill=(124, 58, 237), font=font_box_header)
    draw.text((660, 780), "MULTI-AGENT DEBATE ENGINE", fill=(148, 163, 184), font=font_box_sub)
    
    debate_text = "• 多智能体角色扮演冲突陈述\n• 基于大模型的多轮协商化解\n• GIS空间规则校验与惩罚反馈\n• 用地性质与建筑限高强约束\n• 自动评估生成折中满意方案"
    wrapped_deb = wrap_text_by_pixels(debate_text, font_body_bold, 310, draw)
    y_text = 820
    for line in wrapped_deb:
        draw.text((660, y_text), line, fill=(15, 23, 42) if line.startswith("•") else (71, 85, 105), font=font_body)
        y_text += 32

    # 5. Outcome Node
    draw.rectangle([1204, 754, 1504, 1004], fill=(241, 245, 249))
    draw.rectangle([1200, 750, 1500, 1000], fill=(255, 255, 255), outline=(217, 119, 6), width=2)
    draw.rectangle([1200, 750, 1500, 770], fill=(217, 119, 6))
    draw.text((1215, 800), "满意规划方案输出", fill=(15, 23, 42), font=font_box_header)
    out_text = "最终深化生成：\n[DR-076] 五地块深化设计总图、[DR-082] 实施分期图。符合居民、政府、开发商多方利益共识。"
    wrapped_out = wrap_text_by_pixels(out_text, font_body, 270, draw)
    y_text = 840
    for line in wrapped_out:
        draw.text((1215, y_text), line, fill=(71, 85, 105), font=font_body)
        y_text += 24

    # Connectors
    # From Resident (420, 455) to Debate (640, 875)
    draw.line([(420, 455), (530, 455)], fill=(203, 213, 225), width=3)
    draw.line([(530, 455), (530, 840)], fill=(203, 213, 225), width=3)
    draw.line([(530, 840), (640 - 15, 840)], fill=(203, 213, 225), width=3)
    draw.polygon([(640 - 15, 840 - 6), (640 - 15, 840 + 6), (640 - 5, 840)], fill=(203, 213, 225))

    # From Developer (420, 875) to Debate (640, 875)
    draw.line([(420, 875), (640 - 15, 875)], fill=(203, 213, 225), width=3)
    draw.polygon([(640 - 15, 875 - 6), (640 - 15, 875 + 6), (640 - 5, 875)], fill=(203, 213, 225))

    # From Planner (420, 1295) to Debate (640, 875)
    draw.line([(420, 1295), (530, 1295)], fill=(203, 213, 225), width=3)
    draw.line([(530, 1295), (530, 910)], fill=(203, 213, 225), width=3)
    draw.line([(530, 910), (640 - 15, 910)], fill=(203, 213, 225), width=3)
    draw.polygon([(640 - 15, 910 - 6), (640 - 15, 910 + 6), (640 - 5, 910)], fill=(203, 213, 225))

    # From Debate (980, 875) to Outcome (1200, 875)
    draw.line([(980, 875), (1200 - 15, 875)], fill=(203, 213, 225), width=3)
    draw.polygon([(1200 - 15, 875 - 6), (1200 - 15, 875 + 6), (1200 - 5, 875)], fill=(203, 213, 225))

    # 3. Right Top Card (X: 1608 to 2198, Y: 206 to 602)
    draw.rectangle([1612, 210, 2202, 606], fill=(226, 232, 240))
    draw.rectangle([1608, 206, 2198, 602], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1608, 206, 2198, 212], fill=(217, 119, 6))

    draw.text((1630, 240), "多源诊断与决策 / DECISION PROCESS", fill=(217, 119, 6), font=font_card_title)
    draw.line([(1630, 270), (2176, 270)], fill=(203, 213, 225), width=1)

    desc_lines = [
        "1. 多源诊断：获取街区遥感、路网、建筑层数等空间现状，诊断步行连通度、绿视率、铁路割裂等环境病征。",
        "2. AI推演：基于手绘总规图，输入 ControlNet 并配合天际线效果提示词，由 Diffusion 批量推演多样化更新方案。",
        "3. 指标核验：将 AI 生成的候选平面方案矢量化，导回 GIS 数据库，自动核算各地块用地性质、高度、密度等指标。"
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

    draw.text((1630, 668), "协同决策过程说明 / COLLABORATION", fill=(217, 119, 6), font=font_card_title)
    draw.line([(1630, 698), (2176, 698)], fill=(203, 213, 225), width=1)

    spec_lines = [
        "1. 智能诊断阶段：通过多源异构数据清洗与整合，利用大语言模型（LLM）智能体进行品质病征定位，确定更新的先导方向与改造级别。",
        "2. 协同生成阶段：通过交互式草图/提示词控制网（ControlNet），实现建筑天际线重塑与总体规划总平面图的多方案AIGC生成与方案评选。",
        "3. 方案闭环阶段：将选定方案以矢量要素导回 GIS 系统中，进行用地/高度/容积率等核心指标验算，自动输出规范的图册和导则。"
    ]
    
    y_spec = 720
    for line in spec_lines:
        wrapped = wrap_text_by_pixels(line, font_desc, 510, draw)
        for wl in wrapped:
            draw.text((1630, y_spec), wl, fill=(71, 85, 105), font=font_desc)
            y_spec += 26
        y_spec += 10

    img.save(output_path)
    print(f"Directly generated vector workflow flowchart map and saved to {output_path}")
    return view_w

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    pass
