# -*- coding: utf-8 -*-
# tools/drawings/dr_038.py
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
    print("Drawing DR-038 custom vector map...")
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
    
    draw.text((55, 117), "设计目标体系图", fill=(15, 23, 42), font=font_large_title, anchor="lm")
    draw.text((400, 117), "规划总体定位、三大定量控制目标（生态/服务/风貌）以及两项细化实施定位构成的高层指标大纲。", 
              fill=(100, 116, 139), font=font_desc, anchor="lm")

    # 2. Left giant Map Card (X: 32 to 1584, Y: 206 to 1520)
    draw.rectangle([36, 210, 1588, 1524], fill=(226, 232, 240))
    draw.rectangle([32, 206, 1584, 1520], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 206, 1584, 212], fill=(217, 119, 6))

    draw.text((60, 250), "设计目标与定位体系 / DESIGN OBJECTIVES & POSITIONING", fill=(217, 119, 6), font=font_card_title)
    draw.line([(60, 280), (1556, 280)], fill=(226, 232, 240), width=2)

    # Top Center: 总体定位
    # X: 350 to 1250, Y: 320 to 470 (Center X=800, Y=395)
    draw.rectangle([354, 324, 1254, 474], fill=(241, 245, 249))
    draw.rectangle([350, 320, 1250, 470], fill=(255, 255, 255), outline=(217, 119, 6), width=2)
    draw.rectangle([350, 320, 1250, 335], fill=(217, 119, 6))
    draw.text((800, 370), "总体定位：数字孪生 · 古今共振", fill=(15, 23, 42), font=font_box_header, anchor="mm")
    draw.text((800, 415), "站城文旅首站 × 全龄友好社区 × 数字历史文化展示展廊", fill=(71, 85, 105), font=font_desc, anchor="mm")

    # Three Quantitative Target Cards:
    # Target 1: X: 80 to 480, Y: 600 to 920 (Center X=280)
    # Target 2: X: 590 to 990, Y: 600 to 920 (Center X=790)
    # Target 3: X: 1100 to 1500, Y: 600 to 920 (Center X=1300)

    # Target 1: 生态韧性目标
    draw.rectangle([84, 604, 484, 924], fill=(241, 245, 249))
    draw.rectangle([80, 600, 480, 920], fill=(255, 255, 255), outline=(5, 150, 105), width=2)
    draw.rectangle([80, 600, 480, 615], fill=(5, 150, 105))
    draw.text((105, 650), "生态韧性目标", fill=(15, 23, 42), font=font_box_header)
    draw.text((105, 680), "ECOLOGICAL RESILIENCE", fill=(148, 163, 184), font=font_box_sub)
    t1_text = "• 绿视率由现状 8.7% 提升至不低于 28%，修补生态赤字。\n• 绿地率达到 35% 刚性红线，提升海绵渗透能力。\n• 年雨水径流控制率不低于 70%，构建韧性防涝地盘。"
    wrapped_t1 = wrap_text_by_pixels(t1_text, font_body, 350, draw)
    y_text = 715
    for line in wrapped_t1:
        draw.text((105, y_text), line, fill=(71, 85, 105), font=font_body)
        y_text += 24

    # Target 2: 全龄服务目标
    draw.rectangle([594, 604, 994, 924], fill=(241, 245, 249))
    draw.rectangle([590, 600, 990, 920], fill=(255, 255, 255), outline=(37, 99, 235), width=2)
    draw.rectangle([590, 600, 990, 615], fill=(37, 99, 235))
    draw.text((615, 650), "全龄服务目标", fill=(15, 23, 42), font=font_box_header)
    draw.text((615, 680), "ALL-AGE SOCIAL SERVICE", fill=(148, 163, 184), font=font_box_sub)
    t2_text = "• 强制植入建筑面积 ≥2000㎡ 的“社区盒子”邻里细胞。\n• 500m 适老化与无障碍慢行网络全区覆盖。\n• 精准补齐老年日间照料中心、社区食堂及儿童托管空间。"
    wrapped_t2 = wrap_text_by_pixels(t2_text, font_body, 350, draw)
    y_text = 715
    for line in wrapped_t2:
        draw.text((615, y_text), line, fill=(71, 85, 105), font=font_body)
        y_text += 24

    # Target 3: 风貌管控目标
    draw.rectangle([1104, 604, 1504, 924], fill=(241, 245, 249))
    draw.rectangle([1100, 600, 1500, 920], fill=(255, 255, 255), outline=(220, 38, 38), width=2)
    draw.rectangle([1100, 600, 1500, 615], fill=(220, 38, 38))
    draw.text((1125, 650), "风貌管控目标", fill=(15, 23, 42), font=font_box_header)
    draw.text((1125, 680), "HISTORICAL WIND CONTROL", fill=(148, 163, 184), font=font_box_sub)
    t3_text = "• 伪满皇宫周边 300m 控高 9m/18m/24m，维护视廊完整。\n• 改建建筑通过本地 AIGC 生成模型的和谐度测评分数 ≥0.85。\n• 中车老厂房工业遗产全寿命分类保护，织补工业文明特征。"
    wrapped_t3 = wrap_text_by_pixels(t3_text, font_body, 350, draw)
    y_text = 715
    for line in wrapped_t3:
        draw.text((1125, y_text), line, fill=(71, 85, 105), font=font_body)
        y_text += 24

    # Connectors from Top Center to Targets
    draw.line([(800, 470), (800, 535)], fill=(203, 213, 225), width=3)
    draw.line([(280, 535), (1300, 535)], fill=(203, 213, 225), width=3)
    
    # 280, 535 down to 600
    draw.line([(280, 535), (280, 600 - 15)], fill=(203, 213, 225), width=3)
    draw.polygon([(280 - 6, 600 - 15), (280 + 6, 600 - 15), (280, 600 - 5)], fill=(203, 213, 225))
    
    # 790, 535 down to 600 (Target 2 Center)
    draw.line([(790, 535), (790, 600 - 15)], fill=(203, 213, 225), width=3)
    draw.polygon([(790 - 6, 600 - 15), (790 + 6, 600 - 15), (790, 600 - 5)], fill=(203, 213, 225))
    
    # 1300, 535 down to 600
    draw.line([(1300, 535), (1300, 600 - 15)], fill=(203, 213, 225), width=3)
    draw.polygon([(1300 - 6, 600 - 15), (1300 + 6, 600 - 15), (1300, 600 - 5)], fill=(203, 213, 225))


    # Two Function & Image Cards at the bottom:
    # Card 1: X: 150 to 750, Y: 1080 to 1380
    # Card 2: X: 850 to 1450, Y: 1080 to 1380

    # Bottom 1: 功能定位
    draw.rectangle([154, 1084, 754, 1384], fill=(241, 245, 249))
    draw.rectangle([150, 1080, 750, 1380], fill=(255, 255, 255), outline=(124, 58, 237), width=2)
    draw.rectangle([150, 1080, 750, 1095], fill=(124, 58, 237))
    draw.text((175, 1125), "功能定位：站城文旅首站与全龄友好", fill=(15, 23, 42), font=font_box_header)
    b1_text = "• 推动宽城站交通枢纽向城市文商旅会客厅转型，盘活周边老街区。\n• 精准布设并织补民生急需的公共口袋公园，填补老龄化社区服务网硬缺口。\n• 引入小尺度、低负荷的弹性更新项目，保留场地原本居民生活印记。"
    wrapped_b1 = wrap_text_by_pixels(b1_text, font_body, 550, draw)
    y_text = 1170
    for line in wrapped_b1:
        draw.text((175, y_text), line, fill=(71, 85, 105), font=font_body)
        y_text += 24

    # Bottom 2: 空间形象
    draw.rectangle([854, 1084, 1454, 1384], fill=(241, 245, 249))
    draw.rectangle([850, 1080, 1450, 1380], fill=(255, 255, 255), outline=(234, 88, 12), width=2)
    draw.rectangle([850, 1080, 1450, 1095], fill=(234, 88, 12))
    draw.text((875, 1125), "空间形象：数字展廊与活态文明窗口", fill=(15, 23, 42), font=font_box_header)
    b2_text = "• 摒弃生硬粗暴的仿古复建工程，注重多历史时期风貌在空间中的层级叠加。\n• 打造以绿色廊道渗透为主线的“活态历史文明展示展廊”。\n• 采用微创修缮，将工业遗产烟囱与红砖老厂房融入现代化风貌体系。"
    wrapped_b2 = wrap_text_by_pixels(b2_text, font_body, 550, draw)
    y_text = 1170
    for line in wrapped_b2:
        draw.text((875, y_text), line, fill=(71, 85, 105), font=font_body)
        y_text += 24

    # Connectors from Target Cards to Bottom Cards:
    # Target 1 (280, 920) -> (280, 1000) -> (450, 1000) -> (450, 1080 - 15) with arrow
    draw.line([(280, 920), (280, 1000)], fill=(203, 213, 225), width=3)
    draw.line([(280, 1000), (450, 1000)], fill=(203, 213, 225), width=3)
    draw.line([(450, 1000), (450, 1080 - 15)], fill=(203, 213, 225), width=3)
    draw.polygon([(450 - 6, 1080 - 15), (450 + 6, 1080 - 15), (450, 1080 - 5)], fill=(203, 213, 225))

    # Target 2 (790, 920) -> (790, 1000) -> (450, 1000) & (1150, 1000)
    draw.line([(790, 920), (790, 1000)], fill=(203, 213, 225), width=3)
    draw.line([(450, 1000), (1150, 1000)], fill=(203, 213, 225), width=3)

    # Target 3 (1300, 920) -> (1300, 1000) -> (1150, 1000) -> (1150, 1080 - 15) with arrow
    draw.line([(1300, 920), (1300, 1000)], fill=(203, 213, 225), width=3)
    draw.line([(1300, 1000), (1150, 1000)], fill=(203, 213, 225), width=3)
    draw.line([(1150, 1000), (1150, 1080 - 15)], fill=(203, 213, 225), width=3)
    draw.polygon([(1150 - 6, 1080 - 15), (1150 + 6, 1080 - 15), (1150, 1080 - 5)], fill=(203, 213, 225))


    # 3. Right Top Card (X: 1608 to 2198, Y: 206 to 602)
    draw.rectangle([1612, 210, 2202, 606], fill=(226, 232, 240))
    draw.rectangle([1608, 206, 2198, 602], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1608, 206, 2198, 212], fill=(217, 119, 6))

    draw.text((1630, 240), "定量目标导读 / KPI READINGS", fill=(217, 119, 6), font=font_card_title)
    draw.line([(1630, 270), (2176, 270)], fill=(203, 213, 225), width=1)

    desc_lines = [
        "1. 生态赤字应对：针对调研中 78.3% 绿视率不达标区域，制定绿视率不低于 28% 的刚性指标，同时严控地块绿地率在 35% 以上，用生态织补治愈街区绿荒。",
        "2. 老龄服务补强：响应 30% 街区老龄化人口诉求，定量建设不小于 2000㎡ 的综合社区生活服务盒子，解决生活便利性危机。"
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

    draw.text((1630, 668), "风貌和谐管控指南 / HISTORIC", fill=(217, 119, 6), font=font_card_title)
    draw.line([(1630, 698), (2176, 698)], fill=(203, 213, 225), width=1)

    spec_lines = [
        "【控高边界】 针对伪满皇宫文保边界，执行 9m、18m、24m 三级圈层控高底线，严禁遮挡历史标志物的地平视线廊道。",
        "【和谐校验】 规定所有在风貌协调区内的新建或扩建方案立面，在进入法定审批前，须接受本地化 AIGC 评估网络校验，其和谐度测算得分需达到 0.85 分以上，方为合规风貌设计。"
    ]
    y_spec = 720
    for line in spec_lines:
        wrapped = wrap_text_by_pixels(line, font_desc, 510, draw)
        for wl in wrapped:
            draw.text((1630, y_spec), wl, fill=(71, 85, 105), font=font_desc)
            y_spec += 26
        y_spec += 10

    img.save(output_path)
    print(f"Directly generated vector design objectives map and saved to {output_path}")
    return view_w

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    pass
