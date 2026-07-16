import math
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Set up paths
ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"
ATLAS_DIR = STATIC_DIR / "atlas"

def init_fonts():
    font_path = 'C:/Windows/Fonts/msyh.ttc'
    font_bold_path = 'C:/Windows/Fonts/msyhbd.ttc'
    try:
        f_large_title = ImageFont.truetype(font_bold_path, 40)
        f_card_title = ImageFont.truetype(font_bold_path, 28)
        f_box_header = ImageFont.truetype(font_bold_path, 22)
        f_box_sub = ImageFont.truetype(font_bold_path, 16)
        f_body = ImageFont.truetype(font_path, 18)
        f_body_bold = ImageFont.truetype(font_bold_path, 18)
        f_desc = ImageFont.truetype(font_path, 18)
        f_field = ImageFont.truetype(font_path, 14)
        f_field_bold = ImageFont.truetype(font_bold_path, 14)
    except OSError:
        f_large_title = f_card_title = f_box_header = f_box_sub = f_body = f_body_bold = f_desc = f_field = f_field_bold = ImageFont.load_default()
    return f_large_title, f_card_title, f_box_header, f_box_sub, f_body, f_body_bold, f_desc, f_field, f_field_bold

def draw_grid_background(draw, width, height, cell_size=79.2):
    for x in range(0, width, int(cell_size)):
        draw.line([(x, 0), (x, height)], fill=(240, 243, 246), width=1)
    for y in range(0, height, int(cell_size)):
        draw.line([(0, y), (width, y)], fill=(240, 243, 246), width=1)

def draw_arrow(draw, start, end, fill=(100, 116, 139), width=2, arrow_size=12):
    # Draw line
    draw.line([start, end], fill=fill, width=width)
    # Draw arrowhead
    x1, y1 = start
    x2, y2 = end
    angle = math.atan2(y2 - y1, x2 - x1)
    # Backpoints of arrow
    x3 = x2 - arrow_size * math.cos(angle - math.pi / 6)
    y3 = y2 - arrow_size * math.sin(angle - math.pi / 6)
    x4 = x2 - arrow_size * math.cos(angle + math.pi / 6)
    y4 = y2 - arrow_size * math.sin(angle + math.pi / 6)
    draw.polygon([(x2, y2), (x3, y3), (x4, y4)], fill=fill)

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

def draw_base_layout(draw, sheet_title, sheet_subtitle, rt_title, rb_title, f_large_title, f_desc, f_card_title):
    # 1. Header Card (X: 32 to 2198, Y: 60 to 174)
    draw.rectangle([36, 64, 2202, 178], fill=(226, 232, 240))
    draw.rectangle([32, 60, 2198, 174], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 60, 2198, 66], fill=(217, 119, 6))
    
    draw.text((55, 117), sheet_title, fill=(15, 23, 42), font=f_large_title, anchor="lm")
    draw.text((550, 117), sheet_subtitle, fill=(100, 116, 139), font=f_desc, anchor="lm")

    # 2. Left giant Map Card (X: 32 to 1584, Y: 206 to 1520)
    draw.rectangle([36, 210, 1588, 1524], fill=(226, 232, 240))
    draw.rectangle([32, 206, 1584, 1520], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 206, 1584, 212], fill=(217, 119, 6))

    # 3. Right Top Card (X: 1608 to 2198, Y: 206 to 602)
    draw.rectangle([1612, 210, 2202, 606], fill=(226, 232, 240))
    draw.rectangle([1608, 206, 2198, 602], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1608, 206, 2198, 212], fill=(217, 119, 6))
    draw.text((1630, 240), rt_title, fill=(217, 119, 6), font=f_card_title)
    draw.line([(1630, 270), (2176, 270)], fill=(203, 213, 225), width=1)

    # 4. Right Bottom Card (X: 1608 to 2198, Y: 634 to 1520)
    draw.rectangle([1612, 638, 2202, 1524], fill=(226, 232, 240))
    draw.rectangle([1608, 634, 2198, 1520], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1608, 634, 2198, 640], fill=(217, 119, 6))
    draw.text((1630, 668), rb_title, fill=(217, 119, 6), font=f_card_title)
    draw.line([(1630, 698), (2176, 698)], fill=(203, 213, 225), width=1)

def draw_bullet_points(draw, x_start, y_start, width, lines_list, font, spacing=32, gap=12):
    y_pos = y_start
    for line in lines_list:
        wrapped = wrap_text_by_pixels(line, font, width, draw)
        for wl in wrapped:
            draw.text((x_start, y_pos), wl, fill=(71, 85, 105), font=font)
            y_pos += spacing
        y_pos += gap

def generate_dr159():
    print("Generating DR-159: Platform Functional Architecture...")
    W, H = 2240, 1584
    img = Image.new("RGB", (W, H), color=(248, 250, 252)) # slate-50 background
    draw = ImageDraw.Draw(img)
    
    draw_grid_background(draw, W, H, cell_size=79.2)
    
    f_large_title, f_card_title, f_box_header, _f_box_sub, f_body, f_body_bold, f_desc, _, _ = init_fonts()
    
    draw_base_layout(
        draw,
        sheet_title="智能体协同规划平台功能架构图",
        sheet_subtitle="融合多源空间数据、智能体技术决策与空间刚性控规校验的规划协同平台架构。",
        rt_title="平台架构设计逻辑 / SYSTEM LOGIC",
        rb_title="系统主要模块功能说明 / MODULES",
        f_large_title=f_large_title,
        f_desc=f_desc,
        f_card_title=f_card_title
    )
    
    # Draw title inside left card
    draw.text((60, 250), "平台系统架构设计 / PLATFORM FUNCTIONAL ARCHITECTURE", fill=(217, 119, 6), font=f_card_title)
    draw.line([(60, 280), (1556, 280)], fill=(226, 232, 240), width=2)
    
    # Define layers
    layers = [
        {
            "title": "表现层 | UI & Visualization Layer",
            "color": (239, 246, 255),
            "border": (59, 130, 246),
            "y": 310,
            "items": [
                ("Streamlit 规划协同主页", "提供全流程交互控制与步骤索引"),
                ("三维数据大屏可视化", "展示现状诊断与规划指标大盘统计"),
                ("AIGC 规划设计工作台", "集成提示词推演与改造方案对比生成"),
                ("规划智能体 Skill 控制台", "进行智能体底层技能链调试与脚本运行")
            ]
        },
        {
            "title": "业务逻辑层 | Core Logic & Analysis Layer",
            "color": (245, 243, 255),
            "border": (139, 92, 246),
            "y": 610,
            "items": [
                ("规划用地指标刚性核验", "地块性质、容积率与建筑退让刚性校验"),
                ("空间句法可达性计算", "集成度、选择度拓扑网络空间分析"),
                ("更新单元潜力评估 (AHP-MPI)", "多物理空间准则加权综合更新潜力排序"),
                ("CFD 场地微气候风环境模拟", "日照时数与CFD局部流场风环境模拟")
            ]
        },
        {
            "title": "智能体与协同计算层 | Agent & Consensus Layer",
            "color": (236, 253, 245),
            "border": (16, 185, 129),
            "y": 910,
            "items": [
                ("规划设计智能体 (Planner Agent)", "基于提示词工程引导的指标演算与分析"),
                ("多主体利益博弈协商引擎", "模拟政府、居民、开发商等角色动态协商"),
                ("LLM 博弈算法收敛机制", "基于纳什均衡解推荐最优权衡规划方案"),
                ("AIGC 控规特征提取模型", "基于 ControlNet 的意向图片风格精确控制")
            ]
        },
        {
            "title": "数据底座层 | Multi-Source Spatial Database Layer",
            "color": (254, 242, 242),
            "border": (239, 68, 68),
            "y": 1210,
            "items": [
                ("多源遥感影像 (GeoTIFF)", "2024年超高分辨率遥感底图与DEM"),
                ("街景绿视率 (GVI Data)", "街角采样绿化率与绿视率空间分布"),
                ("兴趣点分类 (POI Data)", "商业、餐饮、办公业态活力网点分类"),
                ("现状空间矢量 (Shapefile)", "建筑轮廓、路网线划、行政区划范围")
            ]
        }
    ]
    
    # Draw layers inside left card
    for layer in layers:
        ly = layer["y"]
        # Layer outer boundary
        draw.rectangle([80, ly, 1536, ly + 220], fill=layer["color"], outline=layer["border"], width=3)
        # Layer title
        draw.text((100, ly + 15), layer["title"], fill=layer["border"], font=f_box_header)
        
        # Draw cards inside
        card_w = 320
        for idx, (name, desc) in enumerate(layer["items"]):
            x_start = 120 + idx * 360
            box_y = ly + 55
            # Card rectangle
            draw.rectangle([x_start, box_y, x_start + card_w, box_y + 140], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
            draw.rectangle([x_start, box_y, x_start + card_w, box_y + 8], fill=layer["border"])
            # Text
            draw.text((x_start + 12, box_y + 22), name, fill=(15, 23, 42), font=f_body_bold)
            
            # Text wrapping for desc
            desc_lines = wrap_text_by_pixels(desc, f_body, card_w - 24, draw)
            for line_idx, dl in enumerate(desc_lines[:3]):
                draw.text((x_start + 12, box_y + 55 + line_idx * 24), dl, fill=(100, 116, 139), font=f_body)
                
    # Draw connection arrows between layers
    for i in range(len(layers) - 1):
        y_top = layers[i]["y"] + 220
        y_bottom = layers[i+1]["y"]
        center_x = 808
        # Arrow down
        draw_arrow(draw, (center_x - 120, y_bottom), (center_x - 120, y_top), fill=(100, 116, 139), width=3)
        draw_arrow(draw, (center_x + 120, y_top), (center_x + 120, y_bottom), fill=(100, 116, 139), width=3)
        
    # Draw right top content
    rt_lines = [
        "1. 多层级协同解耦：采用表现层、业务逻辑层、智能博弈层与数据底座层的四层架构，各层之间通过标准数据流进行解耦，保障平台高效稳定。",
        "2. 智能决策与计算集成：通过 Skill 工具链将大语言模型的推理内核与专业的空间计算算法（如句法、CFD等）深度融合，构建智慧推演闭环。"
    ]
    draw_bullet_points(draw, 1630, 295, 510, rt_lines, f_desc)
    
    # Draw right bottom content
    rb_lines = [
        "【表现层】 提供 Streamlit 协同主页、三维大屏可视化与 AIGC 规划设计工作台，为多方提供便捷的协同交互入口。",
        "【逻辑层】 集成用地规划指标核验、空间句法可达性计算、更新潜力评估与 CFD 微气候模拟等刚性与弹性计算引擎。",
        "【智能层】 运行 Planner Agent，模拟政府、居民、开发商的博弈协商，并通过 LLM 推演寻优，推荐纳什均衡解。",
        "【数据层】 存储多源高分辨率遥感影像（GeoTIFF）、路网与建筑现状矢量（Shapefile）、POI 与街景绿视率底数。"
    ]
    draw_bullet_points(draw, 1630, 720, 510, rb_lines, f_desc)

    output_path = ATLAS_DIR / "DR-159_智能体协同规划平台功能架构图.png"
    img.save(str(output_path))
    print("DR-159 saved successfully without template frames.")

def generate_dr160():
    print("Generating DR-160: Planner Agent Decision Loop...")
    W, H = 2240, 1584
    img = Image.new("RGB", (W, H), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    
    draw_grid_background(draw, W, H, cell_size=79.2)
    
    f_large_title, f_card_title, f_box_header, _f_box_sub, f_body, f_body_bold, f_desc, _, _ = init_fonts()
    
    draw_base_layout(
        draw,
        sheet_title="规划智能体核心决策与工具调用图",
        sheet_subtitle="基于 ReAct 决策机制的大模型推理内核与专属规划分析技能库的交互逻辑。",
        rt_title="智能决策核心逻辑 / AGENT LOGIC",
        rb_title="制图与设计专属技能说明 / SKILL DETAIL",
        f_large_title=f_large_title,
        f_desc=f_desc,
        f_card_title=f_card_title
    )
    
    # Title inside left card
    draw.text((60, 250), "智能推演核心决策流程 / LLM REASONING CORE & DECISION LOOP", fill=(217, 119, 6), font=f_card_title)
    draw.line([(60, 280), (1556, 280)], fill=(226, 232, 240), width=2)
    
    # 1. PERCEPTION BLOCK (Left)
    draw.rectangle([80, 320, 430, 920], fill=(239, 246, 255), outline=(59, 130, 246), width=3)
    draw.rectangle([80, 320, 430, 375], fill=(59, 130, 246))
    draw.text((100, 335), "感知输入层 | PERCEPTION", fill=(255, 255, 255), font=f_box_header)
    
    p_items = [
        ("上位规划法理刚性要求", "包含国土空间、控规指标边界约束"),
        ("多源数据大盘现状问题", "空间可达性低、老龄化与业态不均"),
        ("多主体更新改造核心意愿", "开发商利润、政府指标与居民改善诉求")
    ]
    for idx, (name, desc) in enumerate(p_items):
        y_pos = 395 + idx * 175
        draw.rectangle([100, y_pos, 410, y_pos + 150], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
        draw.text((115, y_pos + 15), name, fill=(15, 23, 42), font=f_body_bold)
        desc_lines = wrap_text_by_pixels(desc, f_body, 280, draw)
        for li, dl in enumerate(desc_lines[:3]):
            draw.text((115, y_pos + 45 + li * 24), dl, fill=(100, 116, 139), font=f_body)

    # 2. BRAIN BLOCK (Center)
    draw.rectangle([510, 320, 1110, 920], fill=(245, 243, 255), outline=(139, 92, 246), width=3)
    draw.rectangle([510, 320, 1110, 375], fill=(139, 92, 246))
    draw.text((530, 335), "规划智能体大模型大脑 | LLM REASONING CORE", fill=(255, 255, 255), font=f_box_header)
    
    react_y = 395
    draw.rectangle([540, react_y, 1080, react_y + 495], fill=(255, 255, 255), outline=(226, 232, 240), width=2)
    draw.text((560, react_y + 20), "规划问题求解逻辑 ReAct 思考循环", fill=(139, 92, 246), font=f_body_bold)
    
    stages = [
        ("1. Thought (思考推理)", "解析地块目标与约束\n判定首要待解决瓶颈"),
        ("2. Action (行为选择)", "根据场景决定调用技能\n(如路网分析/AIGC渲染)"),
        ("3. Observation (观察校验)", "反馈计算数值及图像质量\n进行容积率/刚性约束核算")
    ]
    for idx, (name, desc) in enumerate(stages):
        bx = 565 + idx * 170
        by = react_y + 70
        draw.rectangle([bx, by, bx + 155, by + 390], fill=(250, 250, 250), outline=(203, 213, 225), width=2)
        
        # Wrap title
        title_lines = wrap_text_by_pixels(name, f_body_bold, 140, draw)
        for li, tl in enumerate(title_lines):
            draw.text((bx + 10, by + 15 + li * 24), tl, fill=(15, 23, 42), font=f_body_bold)
            
        dy = by + 80
        for line in desc.split("\n"):
            dl_lines = wrap_text_by_pixels(line, f_body, 135, draw)
            for dl in dl_lines:
                draw.text((bx + 10, dy), dl, fill=(100, 116, 139), font=f_body)
                dy += 24
            dy += 6
            
    # Connect stages inside brain
    draw_arrow(draw, (723, react_y + 260), (733, react_y + 260), fill=(139, 92, 246), width=2)
    draw_arrow(draw, (893, react_y + 260), (903, react_y + 260), fill=(139, 92, 246), width=2)

    # 3. ACTION BLOCK (Right)
    draw.rectangle([1190, 320, 1540, 920], fill=(236, 253, 245), outline=(16, 185, 129), width=3)
    draw.rectangle([1190, 320, 1540, 375], fill=(16, 185, 129))
    draw.text((1210, 335), "行动输出层 | ACTION", fill=(255, 255, 255), font=f_box_header)
    
    a_items = [
        ("矢量图纸与分析图导出", "自动输出道路、公共空间规划矢量"),
        ("规划控制指标表更新", "更新总开发强度与各地块平衡控制表"),
        ("AIGC 改造效果意向图", "地块立面改造、节点景观风格效果图")
    ]
    for idx, (name, desc) in enumerate(a_items):
        y_pos = 395 + idx * 175
        draw.rectangle([1210, y_pos, 1520, y_pos + 150], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
        draw.text((1225, y_pos + 15), name, fill=(15, 23, 42), font=f_body_bold)
        desc_lines = wrap_text_by_pixels(desc, f_body, 280, draw)
        for li, dl in enumerate(desc_lines[:3]):
            draw.text((1225, y_pos + 45 + li * 24), dl, fill=(100, 116, 139), font=f_body)

    # 4. SKILLS BLOCK (Bottom)
    draw.rectangle([80, 980, 1540, 1470], fill=(254, 250, 242), outline=(217, 119, 6), width=3)
    draw.rectangle([80, 980, 1540, 1035], fill=(217, 119, 6))
    draw.text((100, 995), "制图与设计智能体专属技能库 (Skill Library)", fill=(255, 255, 255), font=f_box_header)
    
    skills = [
        ("SpaceSyntaxSkill", "计算道路网络可达性与步行整合度矢量"),
        ("CFDSimulationSkill", "调用微气候分析引擎模拟日照时数与局部风速"),
        ("AIGCRendererSkill", "精准执行地块设计草图至彩图的意向迁移渲染"),
        ("AHPMPIScorerSkill", "智能解译多源空间数据，计算 MPI 潜力得分"),
        ("GeoDataExporterSkill", "绑定 A3 标准图框，一键编译生成多格式图册")
    ]
    card_w = 260
    for idx, (name, desc) in enumerate(skills):
        x_pos = 110 + idx * 286
        y_pos = 1055
        draw.rectangle([x_pos, y_pos, x_pos + card_w, y_pos + 390], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
        draw.rectangle([x_pos, y_pos, x_pos + card_w, y_pos + 8], fill=(217, 119, 6))
        
        name_lines = wrap_text_by_pixels(name, f_body_bold, card_w - 20, draw)
        for li, nl in enumerate(name_lines):
            draw.text((x_pos + 12, y_pos + 20 + li * 24), nl, fill=(15, 23, 42), font=f_body_bold)
            
        desc_lines = wrap_text_by_pixels(desc, f_body, card_w - 24, draw)
        for li, dl in enumerate(desc_lines[:11]):
            draw.text((x_pos + 12, y_pos + 75 + li * 24), dl, fill=(100, 116, 139), font=f_body)

    # Connections between Perception -> Brain -> Action
    draw_arrow(draw, (430, 620), (510, 620), fill=(59, 130, 246), width=3)
    draw_arrow(draw, (1110, 620), (1190, 620), fill=(16, 185, 129), width=3)
    # Double-headed connections between Brain <-> Skills
    draw_arrow(draw, (808 - 150, 920), (808 - 150, 980), fill=(139, 92, 246), width=3)
    draw_arrow(draw, (808 + 150, 980), (808 + 150, 920), fill=(217, 119, 6), width=3)
    
    # Right top content
    rt_lines = [
        "1. 闭环推理控制：智能体通过 “感知-思考-行动” 的 ReAct 推理机制，实时读取空间参数与改造边界约束，实现方案动态优化。",
        "2. 刚性合规约束：在 Observation 阶段，智能体调用用地核验工具，若发现指标超限，则发出反馈重新进行规划决策。"
    ]
    draw_bullet_points(draw, 1630, 295, 510, rt_lines, f_desc)
    
    # Right bottom content
    rb_lines = [
        "【SpaceSyntaxSkill】 计算道路可达性与步行整合度矢量，评估道路的交通组织潜力。",
        "【CFDSimulationSkill】 调用微气候分析引擎，在方案生形后模拟日照时数与局部风场。",
        "【AIGCRendererSkill】 精准执行地块总图与立面草图的意向迁移，自动生成彩总图与鸟瞰效果。",
        "【AHPMPIScorerSkill】 智能解译地块的多源属性，计算 MPI 更新潜力得分并进行分期排序。",
        "【GeoDataExporterSkill】 实现图纸与 A3 级标准图框的结合，一键生成 A1 展板与多格式图册。"
    ]
    draw_bullet_points(draw, 1630, 720, 510, rb_lines, f_desc)

    output_path = ATLAS_DIR / "DR-160_规划智能体核心决策与工具调用图.png"
    img.save(str(output_path))
    print("DR-160 saved successfully without template frames.")

def generate_dr161():
    print("Generating DR-161: Spatial Database Schema...")
    W, H = 2240, 1584
    img = Image.new("RGB", (W, H), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    
    draw_grid_background(draw, W, H, cell_size=79.2)
    
    f_large_title, f_card_title, _f_box_header, _f_box_sub, _f_body, _f_body_bold, f_desc, f_field, f_field_bold = init_fonts()
    
    draw_base_layout(
        draw,
        sheet_title="空间数据库实体关系设计图",
        sheet_subtitle="协同规划平台底层多源空间矢量、用地指标与智能体博弈日志的关系模型（E-R 图）。",
        rt_title="数据库设计原则 / DATABASE SCHEMA",
        rb_title="主要数据表结构说明 / TABLE SCHEMA",
        f_large_title=f_large_title,
        f_desc=f_desc,
        f_card_title=f_card_title
    )
    
    # Title inside left card
    draw.text((60, 250), "空间数据库实体关系设计 / SPATIAL DATABASE SCHEMA DESIGN", fill=(217, 119, 6), font=f_card_title)
    draw.line([(60, 280), (1556, 280)], fill=(226, 232, 240), width=2)
    
    # Drawing ER tables
    tables = [
        {
            "title": "tb_parcel_status (地块现状表)",
            "x": 100, "y": 340, "w": 400,
            "border": (59, 130, 246),
            "fields": [
                ("parcel_id (PK)", "VARCHAR(32) | 地块主键"),
                ("area", "DECIMAL(10,2) | 地块面积"),
                ("landuse_type", "VARCHAR(16) | 现状用地性质"),
                ("current_far", "DECIMAL(4,2) | 现状容积率"),
                ("current_height", "DECIMAL(6,2) | 现状平均高度"),
                ("building_density", "DECIMAL(4,2) | 现状建筑密度")
            ]
        },
        {
            "title": "tb_parcel_control (规划指标控制表)",
            "x": 100, "y": 910, "w": 400,
            "border": (59, 130, 246),
            "fields": [
                ("control_id (PK)", "VARCHAR(32) | 控制主键"),
                ("parcel_id (FK)", "VARCHAR(32) | 关联地块主键"),
                ("target_far", "DECIMAL(4,2) | 目标规划容积率"),
                ("max_height", "DECIMAL(6,2) | 规划限制高度"),
                ("green_ratio", "DECIMAL(4,2) | 规划绿地率控制"),
                ("update_strategy", "VARCHAR(32) | 更新更新模式")
            ]
        },
        {
            "title": "tb_building_geometry (建筑轮廓表)",
            "x": 650, "y": 340, "w": 400,
            "border": (139, 92, 246),
            "fields": [
                ("building_id (PK)", "VARCHAR(32) | 建筑唯一主键"),
                ("parcel_id (FK)", "VARCHAR(32) | 所属地块主键"),
                ("height", "DECIMAL(6,2) | 现状高度"),
                ("floors", "INTEGER | 现状层数"),
                ("structure_type", "VARCHAR(16) | 建筑结构风貌"),
                ("geom", "GEOMETRY(POLYGON) | 建筑平面几何")
            ]
        },
        {
            "title": "tb_space_syntax (空间句法指标表)",
            "x": 650, "y": 910, "w": 400,
            "border": (16, 185, 129),
            "fields": [
                ("road_id (PK)", "VARCHAR(32) | 路段主键"),
                ("integration", "DECIMAL(8,4) | 拓扑整合度"),
                ("choice", "DECIMAL(8,4) | 选择度指标"),
                ("connectivity", "DECIMAL(6,2) | 连接值大小"),
                ("mean_depth", "DECIMAL(6,2) | 平均深度值"),
                ("geom", "GEOMETRY(LINESTRING) | 路网几何")
            ]
        },
        {
            "title": "tb_negotiation_log (智能体谈判日志表)",
            "x": 1200, "y": 340, "w": 340,
            "border": (239, 68, 68),
            "fields": [
                ("log_id (PK)", "VARCHAR(32) | 协商主键"),
                ("epoch", "INTEGER | 谈判轮次"),
                ("agent_role", "VARCHAR(16) | 博弈角色"),
                ("proposal_far", "DECIMAL(4,2) | 提案容积率"),
                ("utility_score", "DECIMAL(4,2) | 角色得分"),
                ("consensus_reached", "BOOLEAN | 达成最优")
            ]
        },
        {
            "title": "tb_poi_vitality (POI产业活力点表)",
            "x": 1200, "y": 910, "w": 340,
            "border": (217, 119, 6),
            "fields": [
                ("poi_id (PK)", "VARCHAR(32) | POI主键"),
                ("poi_type", "VARCHAR(32) | 业态大类"),
                ("poi_name", "VARCHAR(64) | 网点名称"),
                ("vitality_weight", "DECIMAL(4,2) | 活力权重"),
                ("geom", "GEOMETRY(POINT) | POI坐标")
            ]
        }
    ]
    
    # Draw ER tables
    for table in tables:
        tx, ty, tw = table["x"], table["y"], table["w"]
        # Outer header box
        draw.rectangle([tx, ty, tx + tw, ty + 38], fill=table["border"])
        draw.text((tx + 12, ty + 10), table["title"], fill=(255, 255, 255), font=f_field_bold)
        
        # Draw columns body
        num_fields = len(table["fields"])
        th = 38 + num_fields * 30
        draw.rectangle([tx, ty + 38, tx + tw, ty + th], fill=(255, 255, 255), outline=table["border"], width=2)
        
        for idx, (f_name, f_type) in enumerate(table["fields"]):
            fy = ty + 38 + idx * 30
            # Separator line
            if idx > 0:
                draw.line([(tx, fy), (tx + tw, fy)], fill=(226, 232, 240), width=1)
            # Field texts
            draw.text((tx + 12, fy + 6), f_name, fill=(15, 23, 42), font=f_field_bold)
            draw.text((tx + 175, fy + 6), f_type, fill=(100, 116, 139), font=f_field)
            
    # Draw database relationships lines
    # Relationship 1: tb_parcel_status.parcel_id (1) <--> tb_parcel_control.parcel_id (N)
    # Start: x = 300, y = 558. End: x = 300, y = 910
    draw.line([(300, 558), (300, 910)], fill=(100, 116, 139), width=2)
    draw.ellipse([295, 558, 305, 568], fill=(59, 130, 246)) # '1' dot
    draw.polygon([(295, 900), (305, 900), (300, 910)], fill=(59, 130, 246)) # crow's foot 'N'
    
    # Relationship 2: tb_parcel_status.parcel_id (1) <--> tb_building_geometry.parcel_id (N)
    # Start: x = 500, y = 449. End: x = 650, y = 449
    draw.line([(500, 449), (650, 449)], fill=(100, 116, 139), width=2)
    draw.ellipse([500, 444, 510, 454], fill=(59, 130, 246))
    draw.polygon([(640, 444), (640, 454), (650, 449)], fill=(59, 130, 246))
    
    # Relationship 3: tb_parcel_control.parcel_id (1) <--> tb_poi_vitality.geom (Spatial Join)
    # Start: x = 500, y = 1019. End: x = 1200, y = 1019
    draw.line([(500, 1019), (1200, 1019)], fill=(120, 120, 120), width=2)
    draw.ellipse([500, 1014, 510, 1024], fill=(217, 119, 6))
    draw.polygon([(1190, 1014), (1190, 1024), (1200, 1019)], fill=(217, 119, 6))
    
    # Relationship 4: tb_parcel_control.parcel_id (1) <--> tb_negotiation_log.proposal_far (N)
    # Start: x = 500, y = 969. End: x = 1200, y = 449
    draw.line([(500, 969), (590, 969), (590, 750), (1180, 750), (1180, 449), (1200, 449)], fill=(100, 116, 139), width=2)
    draw.ellipse([495, 964, 505, 974], fill=(239, 68, 68))
    draw.polygon([(1190, 444), (1190, 454), (1200, 449)], fill=(239, 68, 68))
    
    # Right top content
    rt_lines = [
        "1. 空间与属性一体化：使用 PostGIS 空间扩展，将地理要素几何字段（geom）与常规规划指标属性字段统一存储在关系型数据库中，提高检索效率。",
        "2. 拓扑与博弈联动：通过 parcel_id 键，实现了地块现状属性、规划限制控制、多主体博弈决策日志与现状建筑轮廓的完整级联更新。"
    ]
    draw_bullet_points(draw, 1630, 295, 510, rt_lines, f_desc)
    
    # Right bottom content
    rb_lines = [
        "【tb_parcel_status】 存储现状地块物理指标，包括面积、容积率、高度、现状密度与用地性质等。",
        "【tb_parcel_control】 存储智能博弈推演后的控规刚性指标，用于与 AIGC 设计成果进行合规性核验。",
        "【tb_building_geometry】 存储 LOD3 级高精度现状建筑几何实体，包含高度、层数与风貌属性。",
        "【tb_space_syntax】 存储句法路网拓扑模型计算结果，涵盖整合度、选择度与连接值空间数据。",
        "【tb_negotiation_log】 存储多轮大模型博弈谈判日志，包含各角色提案、期望与最优纳什均衡解。",
        "【tb_poi_vitality】 存储 POI 网点分类与地理坐标，计算并提供地块的业态活力指数支撑。"
    ]
    draw_bullet_points(draw, 1630, 720, 510, rb_lines, f_desc)

    output_path = ATLAS_DIR / "DR-161_空间数据库实体关系设计图.png"
    img.save(str(output_path))
    print("DR-161 saved successfully without template frames.")

def generate_all():
    ATLAS_DIR.mkdir(parents=True, exist_ok=True)
    generate_dr159()
    generate_dr160()
    generate_dr161()
    print("All 3 technical support drawings have been generated successfully!")

if __name__ == "__main__":
    generate_all()
