# -*- coding: utf-8 -*-
import os
import sys
import shutil
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Adjust path to import config if run standalone
sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.config.paths import STATIC_DIR

# Output Directory
OUTPUT_DIR = str(STATIC_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Font Settings
FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"  # Microsoft YaHei
FONT_BOLD_PATH = r"C:\Windows\Fonts\msyhbd.ttc"  # Microsoft YaHei Bold

if not os.path.exists(FONT_PATH):
    FONT_PATH = "arial.ttf"
if not os.path.exists(FONT_BOLD_PATH):
    FONT_BOLD_PATH = FONT_PATH

# Canvas Dimensions (5K Resolution)
canvas_w = 5120
canvas_h = 3000

def wrap_text_to_lines(text, font, max_width):
    lines = []
    try:
        left, top, right, bottom = font.getbbox(text)
        w = right - left
    except AttributeError:
        w = font.getsize(text)[0]
    if w <= max_width:
        return [text]
        
    current_line = ""
    for char in text:
        test_line = current_line + char
        try:
            left, top, right, bottom = font.getbbox(test_line)
            w_test = right - left
        except AttributeError:
            w_test = font.getsize(test_line)[0]
            
        if w_test <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char
    if current_line:
        lines.append(current_line)
    return lines

# Drawing Helpers
# -------------------------------------------------------------
def draw_glow_arrow(draw, start, end, color, width=2):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = (dx**2 + dy**2)**0.5
    if length == 0:
        return
    ux = dx / length
    uy = dy / length
    
    # 2.5px back-off from the box border to avoid overlaps
    arrow_tip = (end[0] - 2.5 * ux, end[1] - 2.5 * uy)
    
    # Draw core line to the backed-off tip
    draw.line([start, arrow_tip], fill=color, width=width)
    
    # Draw arrow head
    arrow_len = 14
    arrow_width = 10
    p1 = (arrow_tip[0] - arrow_len * ux + arrow_width * uy, arrow_tip[1] - arrow_len * uy - arrow_width * ux)
    p2 = (arrow_tip[0] - arrow_len * ux - arrow_width * uy, arrow_tip[1] - arrow_len * uy + arrow_width * ux)
    draw.polygon([arrow_tip, p1, p2], fill=color)

def draw_curved_connection_line(draw, start, end, color, width=2):
    dx = abs(end[0] - start[0])
    cp1_x = start[0] + min(180, dx * 0.3)
    cp2_x = end[0] - min(180, dx * 0.3)
    
    points = []
    steps = 100
    for i in range(steps + 1):
        t = i / steps
        x = (1-t)**3 * start[0] + 3*(1-t)**2 * t * cp1_x + 3*(1-t) * t**2 * cp2_x + t**3 * end[0]
        y = (1-t)**3 * start[1] + 3*(1-t)**2 * t * start[1] + 3*(1-t) * t**2 * end[1] + t**3 * end[1]
        points.append((x, y))
        
    # Calculate tangent at the end point based on last segment
    last_dx = end[0] - points[-2][0]
    last_dy = end[1] - points[-2][1]
    last_len = (last_dx**2 + last_dy**2)**0.5
    if last_len > 0:
        ux = last_dx / last_len
        uy = last_dy / last_len
    else:
        ux, uy = 1.0, 0.0
        
    # 2.5px back-off from the box border to avoid overlaps
    arrow_tip = (end[0] - 2.5 * ux, end[1] - 2.5 * uy)
    points[-1] = arrow_tip
    
    # Draw Bezier curve
    draw.line(points, fill=color, width=width)
    
    # Arrow head oriented along the tangent
    arrow_len = 12
    arrow_width = 8
    p1 = (arrow_tip[0] - arrow_len * ux + arrow_width * uy, arrow_tip[1] - arrow_len * uy - arrow_width * ux)
    p2 = (arrow_tip[0] - arrow_len * ux - arrow_width * uy, arrow_tip[1] - arrow_len * uy + arrow_width * ux)
    draw.polygon([arrow_tip, p1, p2], fill=color)

def draw_curved_connection_label(draw, start, end, label, color, font, drawn_boxes):
    if not label:
        return
    dx = abs(end[0] - start[0])
    cp1_x = start[0] + min(180, dx * 0.3)
    cp2_x = end[0] - min(180, dx * 0.3)
    
    lines = label.split("\n")
    max_w = 0
    total_h = 0
    for l in lines:
        try:
            l_box = font.getbbox(l)
            w_l = l_box[2] - l_box[0]
            h_l = l_box[3] - l_box[1]
        except AttributeError:
            w_l, h_l = font.getsize(l)
        max_w = max(max_w, w_l)
        total_h += h_l + 4
    bw, bh = max_w + 14, total_h + 8

    found_pos = False
    best_x, best_y = 0, 0
    
    # Check t-candidates along the bezier curve
    t_candidates = [0.65, 0.50, 0.75, 0.40, 0.80, 0.30, 0.85]
    for t_lbl in t_candidates:
        lbl_x = (1-t_lbl)**3 * start[0] + 3*(1-t_lbl)**2 * t_lbl * cp1_x + 3*(1-t_lbl) * t_lbl**2 * cp2_x + t_lbl**3 * end[0]
        lbl_y = (1-t_lbl)**3 * start[1] + 3*(1-t_lbl)**2 * t_lbl * start[1] + 3*(1-t_lbl) * t_lbl**2 * end[1] + t_lbl**3 * end[1]
        
        bx0, by0 = lbl_x - bw // 2, lbl_y - bh // 2
        bx1, by1 = lbl_x + bw // 2, lbl_y + bh // 2
        
        overlap = False
        for box in drawn_boxes:
            if not (bx1 < box[0] or bx0 > box[2] or by1 < box[1] or by0 > box[3]):
                overlap = True
                break
        
        if not overlap:
            best_x, best_y = lbl_x, lbl_y
            found_pos = True
            break
            
    # Shift vertical if no free space along curve
    if not found_pos:
        t_lbl = 0.65
        lbl_x = (1-t_lbl)**3 * start[0] + 3*(1-t_lbl)**2 * t_lbl * cp1_x + 3*(1-t_lbl) * t_lbl**2 * cp2_x + t_lbl**3 * end[0]
        lbl_y = (1-t_lbl)**3 * start[1] + 3*(1-t_lbl)**2 * t_lbl * start[1] + 3*(1-t_lbl) * t_lbl**2 * end[1] + t_lbl**3 * end[1]
        
        for y_offset in [35, -35, 70, -70, 105, -105]:
            bx0, by0 = lbl_x - bw // 2, lbl_y + y_offset - bh // 2
            bx1, by1 = lbl_x + bw // 2, lbl_y + y_offset + bh // 2
            overlap = False
            for box in drawn_boxes:
                if not (bx1 < box[0] or bx0 > box[2] or by1 < box[1] or by0 > box[3]):
                    overlap = True
                    break
            if not overlap:
                best_x, best_y = lbl_x, lbl_y + y_offset
                found_pos = True
                break
                
    if not found_pos:
        best_x, best_y = lbl_x, lbl_y
        
    bx0, by0 = best_x - bw // 2, best_y - bh // 2
    bx1, by1 = best_x + bw // 2, best_y + bh // 2
    drawn_boxes.append((bx0 - 2, by0 - 2, bx1 + 2, by1 + 2))
    
    # Solid border matching the line color
    label_border_color = (color[0], color[1], color[2], 255)
    
    # Match text color to the line type for better recognition and readability in Light Mode
    text_fill = (71, 85, 105, 255)  # Default dark slate grey
    r, g, b = color[0], color[1], color[2]
    if r == 148 and g == 163 and b == 184:    # c_raw_stage (Slate Grey-blue)
        text_fill = (71, 85, 105, 255)
    elif r == 168 and g == 85 and b == 247:   # c_cross (Violet)
        text_fill = (126, 34, 206, 255)       # High-contrast purple
    elif r == 251 and g == 191 and b == 36:   # c_deliver (Amber)
        text_fill = (180, 83, 9, 255)         # High-contrast brown/amber
        
    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=4, fill=(255, 255, 255, 255), outline=label_border_color, width=1)
    
    ty = by0 + 4
    for l in lines:
        try:
            w_l = font.getbbox(l)[2] - font.getbbox(l)[0]
            h_l = font.getbbox(l)[3] - font.getbbox(l)[1]
        except AttributeError:
            w_l, h_l = font.getsize(l)
        draw.text((best_x - w_l // 2, ty), l, fill=text_fill, font=font)
        ty += h_l + 4

def draw_card(draw, x, y, w, h, title, bullets, scheme, font_title, font_body):
    # Outer box
    draw.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=scheme["fill"], outline=scheme["stroke"], width=2)
    # Header banner (Taller header for larger title font)
    draw.rectangle([x + 2, y + 2, x + w - 2, y + 42], fill=scheme["fill"])
    draw.line([x, y + 42, x + w, y + 42], fill=scheme["stroke"], width=1)
    
    # Title Text
    draw.text((x + 12, y + 8), title, fill=scheme["text"], font=font_title)
    
    # Bullets Text
    by = y + 52
    max_text_w = w - 24
    for bullet in bullets:
        wrapped_lines = wrap_text_to_lines(bullet, font_body, max_text_w)
        for line in wrapped_lines:
            draw.text((x + 12, by), line, fill=(71, 85, 105), font=font_body)
            by += 24

# -------------------------------------------------------------
# MAIN DRAWING ROUTINE
# -------------------------------------------------------------
def draw_unified_landscape():
    img = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Load Fonts
    try:
        title_font = ImageFont.truetype(FONT_BOLD_PATH, 72)
        subtitle_font = ImageFont.truetype(FONT_PATH, 32)
        group_font = ImageFont.truetype(FONT_BOLD_PATH, 24)
        node_title_font = ImageFont.truetype(FONT_BOLD_PATH, 18)
        node_desc_font = ImageFont.truetype(FONT_PATH, 16)
        label_font = ImageFont.truetype(FONT_PATH, 16)
    except:
        title_font = subtitle_font = group_font = node_title_font = node_desc_font = label_font = ImageFont.load_default()

    # Draw Subtle grid background for high-tech HUD feel (Light Slate Grey grid)
    grid_spacing = 100
    for x in range(0, canvas_w, grid_spacing):
        draw.line([(x, 0), (x, canvas_h)], fill=(226, 232, 240, 150), width=1)
    for y in range(0, canvas_h, grid_spacing):
        draw.line([(0, y), (canvas_w, y)], fill=(226, 232, 240, 150), width=1)

    # Top Header Panel (Light Mode Theme)
    draw.rectangle([0, 0, canvas_w, 160], fill=(241, 245, 249, 255))
    draw.line([(0, 160), (canvas_w, 160)], fill=(203, 213, 225, 255), width=2) # Light border
    draw.text((80, 40), "城市更新微更新决策支持平台 —— 核心技术与全生命周期数据算法知识图谱", fill=(15, 23, 42, 255), font=title_font)
    draw.text((4200, 60), "5K MULTI-LEVEL COGNITIVE MAP", fill=(100, 116, 139, 255), font=subtitle_font)

    # Color Schemes (Beautiful High-Contrast Light Mode)
    SCHEMES = {
        "raw": {"fill": (241, 245, 249), "stroke": (148, 163, 184), "text": (15, 23, 42)},
        "stage": {"fill": (239, 246, 255), "stroke": (59, 130, 246), "text": (30, 58, 138)},
        "result": {"fill": (250, 245, 255), "stroke": (168, 85, 247), "text": (88, 28, 135)},
        "deliverable": {"fill": (254, 243, 199), "stroke": (245, 158, 11), "text": (120, 53, 4)}
    }

    # -------------------------------------------------------------
    # Coordinates Mapping & Config
    # -------------------------------------------------------------
    x_raw = 40
    w_raw = 480
    h_raw = 110

    x_s1 = 620
    x_r1 = 1000
    w_s = 350
    h_s = 100
    w_r = 480
    h_r = 140

    x_s2 = 1550
    x_r2 = 1930

    x_s3 = 2480
    x_r3 = 2860

    x_s4 = 3410
    x_r4 = 3790

    x_atlas = 4480
    w_atlas = 530
    h_atlas = 210

    # 1. RAW DATA (19 items)
    raw_nodes = [
        {"id": "R0", "file": "Boundary_Scope.geojson", "title": "Boundary_Scope.geojson", "desc": "研究红线边界 (规划范围)"},
        {"id": "R1", "file": "Building_Footprints.geojson", "title": "Building_Footprints.geojson", "desc": "现状建筑轮廓 (高度/层数)"},
        {"id": "R2", "file": "Key_Plots_District.json", "title": "Key_Plots_District.json", "desc": "5个重点地块边界 (设计单元)"},
        {"id": "R3", "file": "road_clipped.geojson", "title": "road_clipped.geojson", "desc": "路网中心线 (交通网络)"},
        {"id": "R4", "file": "rail_clipped.geojson", "title": "rail_clipped.geojson", "desc": "轨道交通线 (TOD底盘)"},
        {"id": "R5", "file": "landuse_clipped.geojson", "title": "landuse_clipped.geojson", "desc": "现状用地分类 (国标类别)"},
        {"id": "R6", "file": "Changchun_POI_Real.csv", "title": "Changchun_POI_Real.csv", "desc": "POI兴趣点 (业态分类)"},
        {"id": "R7", "file": "Changchun_Traffic_Real.csv", "title": "Changchun_Traffic_Real.csv", "desc": "现状交通设施分布点"},
        {"id": "R8", "file": "CV_NLP_RawData.csv", "title": "CV_NLP_RawData.csv", "desc": "社交媒体评论 (情感诊断)"},
        {"id": "R9", "file": "GVI_Results_Analysis.csv", "title": "GVI_Results_Analysis.csv", "desc": "街景指标表 (绿视率/SVF)"},
        {"id": "R10", "file": "Changchun_Precise_Points.xlsx", "title": "Changchun_Precise_Points.xlsx", "desc": "458个采样点精确三维坐标"},
        {"id": "R11", "file": "Traffic_Flow.csv", "title": "Traffic_Flow.csv", "desc": "路网拥堵/流量分布表"},
        {"id": "R12", "file": "Building_Years.csv", "title": "Building_Years.csv", "desc": "建筑建成年代 (更新迫切度)"},
        {"id": "R13", "file": "House_Prices.csv", "title": "House_Prices.csv", "desc": "地块房价/地价数据"},
        {"id": "R14", "file": "Sunshine_*.csv", "title": "Sunshine_*.csv", "desc": "冬至/夏至日照时长诊断表"},
        {"id": "R15", "file": "data/streetview/*.jpg", "title": "data/streetview/*.jpg", "desc": "采样点实景相片 (AIGC底盘)"},
        {"id": "R16", "file": "mission_text.txt", "title": "mission_text.txt", "desc": "规划任务书/约束建议"},
        {"id": "R17", "file": "rag_knowledge.json", "title": "rag_knowledge.json", "desc": "城市更新政策条例库"},
        {"id": "R18", "file": "protected_buildings.geojson", "title": "protected_buildings.geojson", "desc": "历史保护建筑边界 (紫线)"}
    ]

    for i, rn in enumerate(raw_nodes):
        rn["x"] = x_raw
        rn["y"] = 220 + i * 135
        rn["w"] = w_raw
        rn["h"] = h_raw

    # 2. COLUMN 1 Stages & Results
    s_col1 = [
        {"id": "S00", "title": "S00. 数据准备", "desc": "数据接入与质量自检", "y": 200},
        {"id": "S01", "title": "S01. 任务解读", "desc": "语义分析与指标提取", "y": 740},
        {"id": "S02", "title": "S02. 资料收集", "desc": "政策合规底册语料收集", "y": 1280},
        {"id": "S03", "title": "S03. 现场调研", "desc": "视觉环境采样与建模", "y": 1820},
        {"id": "S04", "title": "S04. 现状分析", "desc": "数字孪生指标量化", "y": 2360}
    ]
    for s in s_col1:
        s["x"] = x_s1
        s["w"] = w_s
        s["h"] = h_s
        s["y"] += 120

    r_col1 = [
        {"id": "S00_res", "stage": "S00", "title": "标准化物理数据资产", "bullets": ["• gis/csv/streetview标准化", "• data_categories自检清单", "• 缺失数据Mock垫底机制"], "y": 200},
        {"id": "S01_res", "stage": "S01", "title": "任务约束指标 (extracted_constraints)", "bullets": ["• 任务书刚性控制红线提取", "• LLM语义解读指标表预定义", "• 大模型动态指标约束规则库"], "y": 740},
        {"id": "S02_res", "stage": "S02", "title": "政策合规向量库 (rag_vector_db)", "bullets": ["• 248处更新法规语义索引库", "• 建筑退界/红线退让/高度限制", "• Zoning RAG 高维向量检索比对"], "y": 1280},
        {"id": "S03_res", "stage": "S03", "title": "视觉品质指标 (GVI_SVF_index)", "bullets": ["• 绿视率分值 / 天空可视率", "• 街区围合度 / 视觉混乱度", "• 分类语义分割特征表"], "y": 1820},
        {"id": "S04_res1", "stage": "S04", "title": "三维孪生底座 (twin_3d_model)", "bullets": ["• Pydeck 三维建筑模型白模", "• 冬至日照时长时空可视化", "• 道路拓扑连通度及机动分析"], "y": 2240},
        {"id": "S04_res2", "stage": "S04", "title": "现状地块现状图 (landuse_diagnostics)", "bullets": ["• 现状建筑层数及结构材质", "• 现状用地面积国标分类表", "• 建筑建成年代空间热力图"], "y": 2370},
        {"id": "S04_res3", "stage": "S04", "title": "天际线高度特征 (skyline_profile)", "bullets": ["• 最高高度/均高/高层占比", "• 天际线凹凸度分析分析图"], "y": 2500}
    ]
    for r in r_col1:
        r["x"] = x_r1
        r["w"] = w_r
        r["h"] = h_r
        r["y"] += 120

    # 3. COLUMN 2 Stages & Results
    s_col2 = [
        {"id": "S05", "title": "S05. 问题诊断", "desc": "地块更新迫切潜力分析", "y": 480},
        {"id": "S06", "title": "S06. 目标定位", "desc": "发展目标及理念策划", "y": 1300},
        {"id": "S07", "title": "S07. 设计策略", "desc": "多主体协商与合规研判", "y": 2120}
    ]
    for s in s_col2:
        s["x"] = x_s2
        s["w"] = w_s
        s["h"] = h_s
        s["y"] += 120

    r_col2 = [
        {"id": "S05_res1", "stage": "S05", "title": "地块潜力排行 (mpi_ranking)", "bullets": ["• AHP-MPI 潜力等级排行", "• 更新迫切度地块排序"], "y": 360},
        {"id": "S05_res2", "stage": "S05", "title": "潜力雷达图 (radar_data)", "bullets": ["• POI密度/GVI品质/面积因子", "• 多指标维度地块分析图表"], "y": 480},
        {"id": "S05_res3", "stage": "S05", "title": "现状诊断报告 (diagnosis_report)", "bullets": ["• 区域三大问题短板报告", "• 微博舆情正负向情感热词"], "y": 600},
        
        {"id": "S06_res", "stage": "S06", "title": "规划愿景与定位 (design_concept)", "bullets": ["• 总体更新目标定位建议", "• 核心空间策划理念词条", "• AIGC设计引导词框架"], "y": 1300},
        
        {"id": "S07_res1", "stage": "S07", "title": "改造策略矩阵 (strategy_matrix)", "bullets": ["• 三方谈判协同改造选项", "• 保留/微更新/拆建分区表"], "y": 2040},
        {"id": "S07_res2", "stage": "S07", "title": "合规审计与协商 (Compliance & Debate)", "bullets": ["• 居民/开发商/政府三智能体协商", "• LLM 自动满意度效用评分 grading", "• 控规指标一键合规红牌告警"], "y": 2170}
    ]
    for r in r_col2:
        r["x"] = x_r2
        r["w"] = w_r
        r["h"] = h_r
        r["y"] += 120

    # 4. COLUMN 3 Stages & Results
    s_col3 = [
        {"id": "S08", "title": "S08. 总体城市设计", "desc": "平面布局及用地调配", "y": 250},
        {"id": "S09", "title": "S09. 专项系统设计", "desc": "子系统深化设计规划", "y": 780},
        {"id": "S10", "title": "S10. 重点地段深化", "desc": "AIGC渲染效果图深化", "y": 1310},
        {"id": "S11", "title": "S11. 实施路径", "desc": "时序分期留改拆安排", "y": 1840},
        {"id": "S12", "title": "S12. 城市设计导则", "desc": "开发强度控制条例", "y": 2370}
    ]
    for s in s_col3:
        s["x"] = x_s3
        s["w"] = w_s
        s["h"] = h_s
        s["y"] += 120

    r_col3 = [
        {"id": "S08_res1", "stage": "S08", "title": "指标沙盘平衡表 (landuse_sandbox)", "bullets": ["• 用地调整前后面积对比", "• 商业/绿地/公共设施指标平衡"], "y": 190},
        {"id": "S08_res2", "stage": "S08", "title": "概念总规线稿 (master_plan_sketch)", "bullets": ["• 概念规划总平面草图", "• ControlNet 生形线稿底图"], "y": 320},
        
        {"id": "S09_res1", "stage": "S09", "title": "道路交通规划图 (traffic_system)", "bullets": ["• TOD轨道覆盖与慢行网络", "• 道路等级红线及断面"], "y": 660},
        {"id": "S09_res2", "stage": "S09", "title": "公共空间规划图 (public_space)", "bullets": ["• 绿道覆盖与口袋公园布局", "• 慢行景观绿化控制网"], "y": 780},
        {"id": "S09_res3", "stage": "S09", "title": "风貌景观引导图 (landscape_style)", "bullets": ["• 天际线风貌轴线控制", "• 街道立面材质色彩导引"], "y": 900},
        
        {"id": "S10_res1", "stage": "S10", "title": "深化地块画像 (plot_personas)", "bullets": ["• 重点深化地块产业定位策划", "• 核心客群画像与功能落位建议"], "y": 1220},
        {"id": "S10_res2", "stage": "S10", "title": "更新前后对比图 (before_after_rendering)", "bullets": ["• 现状透视底图街景提取", "• SD ControlNet AIGC高精渲染"], "y": 1350},
        
        {"id": "S11_res", "stage": "S11", "title": "时空实施分期图 (phasing_plan)", "bullets": ["• 时序分期实施划定 (近/中/远)", "• 各阶段“留改拆”改造实施进度"], "y": 1840},
        {"id": "S12_res", "stage": "S12", "title": "控制导则文本 (design_guideline_docx)", "bullets": ["• LLM 自动控制条文编译导出", "• 容积率/绿地率刚性限额说明", "• 红头规划图则标准 Word 输出"], "y": 2370}
    ]
    for r in r_col3:
        r["x"] = x_r3
        r["w"] = w_r
        r["h"] = h_r
        r["y"] += 120

    # 5. COLUMN 4 Stages & Results
    s_col4 = [
        {"id": "S13", "title": "S13. 成果表达", "desc": "图册自动排版与封存", "y": 600},
        {"id": "S14", "title": "S14. 视频生成", "desc": "数据驱动视频汇报生成", "y": 1400},
        {"id": "S15", "title": "S15. 辅助设计工具", "desc": "AIGC提示词生形辅助页", "y": 2150}
    ]
    for s in s_col4:
        s["x"] = x_s4
        s["w"] = w_s
        s["h"] = h_s
        s["y"] += 120

    r_col4 = [
        {"id": "S13_res", "stage": "S13", "title": "A3规划图册版面集 (atlas_layouts)", "bullets": ["• PIL图层拼装/图例图签自动绘制", "• 大模型指标读取与动态设计说明生成", "• 多进程图册批量编译及PDF归档"], "y": 600},
        {"id": "S14_res", "stage": "S14", "title": "视频分镜与多媒体 (script_scenes)", "bullets": ["• 智能解说词文本生成 (LLM)", "• 数据可视化图表视频嵌入", "• 最终多媒体视频汇报成果"], "y": 1400},
        {"id": "S15_res", "stage": "S15", "title": "智能辅助设计 (AI Planning Copilot)", "bullets": ["• 全局 Sidebar 智能规划助手", "• 阶段跳转 Agent 指引决策路径", "• AIGC 控制提示词动态管理库"], "y": 2150}
    ]
    for r in r_col4:
        r["x"] = x_r4
        r["w"] = w_r
        r["h"] = h_r
        r["y"] += 120

    # 6. ATLAS CHAPTERS
    chapters = [
        {
            "id": "C1", "title": "Chapter 01 项目认知篇", "y": 200,
            "bullets": [
                "【必备】: 封面、目录、背景图、区位图、范围图、",
                "          上位规划解读图",
                "【可选】: 历史沿革图、周边关系分析图、案例借鉴图"
            ]
        },
        {
            "id": "C2", "title": "Chapter 02 数据诊断篇", "y": 580,
            "bullets": [
                "【必备】: 用地现状分析图、交通现状图、",
                "          POI活力分析图、问题诊断总图",
                "【可选】: 数字孪生框架图、建筑现状高度图、",
                "          风貌现状图、句法可达性图、情感舆情热力图"
            ]
        },
        {
            "id": "C3", "title": "Chapter 03 价值评估篇", "y": 960,
            "bullets": [
                "【必备】: 遗产价值评估热力图、更新潜力图、",
                "          积水区与防灾安全风险分析 (新)",
                "【可选】: 风貌敏感度评价图、更新冲突图、",
                "          综合评价分区图"
            ]
        },
        {
            "id": "C4", "title": "Chapter 04 策略生成篇", "y": 1340,
            "bullets": [
                "【必备】: 项目发展定位与愿景图 (新)、更新模式",
                "          分区图、总体更新规划策略图",
                "【可选】: 设计理念图、目标体系图、功能策划图、",
                "          空间结构规划图"
            ]
        },
        {
            "id": "C5", "title": "Chapter 05 整体概念设计和更新", "y": 1720,
            "bullets": [
                "【必备】: 概念总平面、更新分区、空间结构、",
                "          景观结构与绿地系统、道路交通网络",
                "【可选】: 鸟瞰效果图、建筑高度控制、开发强度控制、",
                "          指标表 (无土地利用图)"
            ]
        },
        {
            "id": "C6", "title": "Chapter 06 重点地段更新改造设计", "y": 2100,
            "bullets": [
                "【必备】: 站城门户更新、工业遗产活化、",
                "          老旧社区微更新、历史风貌协调、",
                "          文旅活力街巷等重点地段改造设计",
                "【可选】: 立面生形图、人视透视图、街道断面设计"
            ]
        },
        {
            "id": "C7", "title": "Chapter 07 技术推演与实施篇", "y": 2480,
            "bullets": [
                "【必备】: AIGC设计推演过程图、实施分期图、",
                "          更新成效评估图",
                "【可选】: 协同治理与运营机制建议图"
            ]
        }
    ]
    for ch in chapters:
        ch["x"] = x_atlas
        ch["w"] = w_atlas
        ch["h"] = h_atlas
        ch["y"] += 120

    # Helper maps for coordinate lookups
    all_stages = {s["id"]: s for s in s_col1 + s_col2 + s_col3 + s_col4}
    all_results = {r["id"]: r for r in r_col1 + r_col2 + r_col3 + r_col4}
    all_raws = {rn["id"]: rn for rn in raw_nodes}
    all_chapters = {ch["id"]: ch for ch in chapters}

    # -------------------------------------------------------------
    # 3-PASS RENDERING PIPELINE FOR CLEAN LAYOUT
    # -------------------------------------------------------------
    connections = []
    def add_conn(start, end, label, color):
        connections.append((start, end, label, color))

    # Colors for connecting lines (RGBA to support transparency)
    c_raw_stage = (148, 163, 184, 45)  # Faint grey-blue background web
    c_stage_res = (129, 140, 248, 255)  # Solid indigo for direct stage-to-result
    c_cross = (168, 85, 247, 120)      # Translucent violet for intermediate cross-inputs
    c_deliver = (251, 191, 36, 180)    # Amber with 70% opacity for final chapters

    # Helper functions for edges
    def r_edge(rn):
        return (rn["x"] + rn["w"], rn["y"] + rn["h"] // 2)
    def s_l_edge(sn):
        return (sn["x"], sn["y"])
    def s_r_edge(sn):
        return (sn["x"] + sn["w"], sn["y"])
    def res_l_edge(rn):
        return (rn["x"], rn["y"])
    def res_r_edge(rn):
        return (rn["x"] + rn["w"], rn["y"])
    def ch_l_edge(ch):
        return (ch["x"], ch["y"])

    # 1. Raw Data -> Stages
    add_conn(r_edge(all_raws["R0"]), s_l_edge(all_stages["S00"]), "范围导入", c_raw_stage)
    add_conn(r_edge(all_raws["R1"]), s_l_edge(all_stages["S00"]), "现状轮廓导入", c_raw_stage)
    add_conn(r_edge(all_raws["R3"]), s_l_edge(all_stages["S00"]), "路网几何导入", c_raw_stage)
    add_conn(r_edge(all_raws["R16"]), s_l_edge(all_stages["S01"]), "任务书NLP分析\n分词与关键词过滤", c_raw_stage)
    add_conn(r_edge(all_raws["R17"]), s_l_edge(all_stages["S02"]), "法规文献段落提取\nChroma向量索引库", c_raw_stage)
    add_conn(r_edge(all_raws["R15"]), s_l_edge(all_stages["S03"]), "DeepLabV3\n街景图像语义分割", c_raw_stage)
    add_conn(r_edge(all_raws["R1"]), s_l_edge(all_stages["S04"]), "Deck.GL 三维渲染\n与形态均高分析", c_raw_stage)
    add_conn(r_edge(all_raws["R5"]), s_l_edge(all_stages["S04"]), "空间叠加\n与现状面积统计", c_raw_stage)
    add_conn(r_edge(all_raws["R6"]), s_l_edge(all_stages["S05"]), "AHP-MPI 因子\n(POI业态密度匹配)", c_raw_stage)
    add_conn(r_edge(all_raws["R9"]), s_l_edge(all_stages["S05"]), "AHP-MPI 因子\n(街景品质指标提取)", c_raw_stage)
    add_conn(r_edge(all_raws["R2"]), s_l_edge(all_stages["S05"]), "AHP-MPI 因子\n(重点地块空间匹配)", c_raw_stage)

    # 2. Stage to Stage / Cross connections
    add_conn(res_r_edge(all_results["S01_res"]), s_l_edge(all_stages["S06"]), "LLM语义策划\n定位目标生成", c_cross)
    add_conn(res_r_edge(all_results["S05_res3"]), s_l_edge(all_stages["S06"]), "问题短板\n输入对标", c_cross)
    add_conn(res_r_edge(all_results["S06_res"]), s_l_edge(all_stages["S07"]), "定位愿景注入", c_cross)
    add_conn(res_r_edge(all_results["S02_res"]), s_l_edge(all_stages["S07"]), "RAG 政策检索比对\n& 合规性审查分析", c_cross)
    add_conn(res_r_edge(all_results["S07_res1"]), s_l_edge(all_stages["S08"]), "留改拆分区控制", c_cross)
    add_conn(res_r_edge(all_results["S04_res1"]), s_l_edge(all_stages["S08"]), "现状建筑高度限制", c_cross)
    add_conn(res_r_edge(all_results["S04_res2"]), s_l_edge(all_stages["S08"]), "用地现状面积输入", c_cross)
    add_conn(res_r_edge(all_results["S08_res1"]), s_l_edge(all_stages["S09"]), "沙盘边界同步", c_cross)
    add_conn(res_r_edge(all_results["S04_res1"]), s_l_edge(all_stages["S09"]), "交通路网/TOD分析", c_cross)
    add_conn(res_r_edge(all_results["S08_res2"]), s_l_edge(all_stages["S10"]), "ControlNet 线稿控制层", c_cross)
    add_conn(res_r_edge(all_results["S03_res"]), s_l_edge(all_stages["S10"]), "现状实景相片底盘", c_cross)
    add_conn(res_r_edge(all_results["S05_res1"]), s_l_edge(all_stages["S10"]), "重点更新项目落位", c_cross)
    add_conn(res_r_edge(all_results["S10_res2"]), s_l_edge(all_stages["S11"]), "更新项目落位", c_cross)
    add_conn(res_r_edge(all_results["S07_res1"]), s_l_edge(all_stages["S11"]), "开发强度/投资测算\n留改拆时序划分", c_cross)
    add_conn(res_r_edge(all_results["S07_res1"]), s_l_edge(all_stages["S12"]), "刚性改造机制约束", c_cross)
    add_conn(res_r_edge(all_results["S10_res1"]), s_l_edge(all_stages["S12"]), "LLM控制条文编译\n写入容积率限制", c_cross)

    # Drawings to S13
    add_conn(res_r_edge(all_results["S08_res2"]), s_l_edge(all_stages["S13"]), "概念总规图纸", c_cross)
    add_conn(res_r_edge(all_results["S09_res1"]), s_l_edge(all_stages["S13"]), "交通规划图纸", c_cross)
    add_conn(res_r_edge(all_results["S09_res2"]), s_l_edge(all_stages["S13"]), "绿道开敞图纸", c_cross)
    add_conn(res_r_edge(all_results["S10_res2"]), s_l_edge(all_stages["S13"]), "Before/After对比图", c_cross)
    add_conn(res_r_edge(all_results["S11_res"]), s_l_edge(all_stages["S13"]), "时序分期图纸", c_cross)
    add_conn(res_r_edge(all_results["S13_res"]), s_l_edge(all_stages["S14"]), "A3图册版面合集\n用于汇报巡游片段", c_cross)
    add_conn(res_r_edge(all_results["S05_res1"]), s_l_edge(all_stages["S14"]), "诊断数据注入脚本\n自动生成朗读配音", c_cross)

    # Results to Chapters
    add_conn(res_r_edge(all_results["S01_res"]), ch_l_edge(all_chapters["C1"]), "任务背景", c_deliver)
    add_conn(res_r_edge(all_results["S03_res"]), ch_l_edge(all_chapters["C2"]), "街区品质", c_deliver)
    add_conn(res_r_edge(all_results["S04_res1"]), ch_l_edge(all_chapters["C2"]), "现状图纸", c_deliver)
    add_conn(res_r_edge(all_results["S04_res2"]), ch_l_edge(all_chapters["C2"]), "用地现状", c_deliver)
    add_conn(res_r_edge(all_results["S05_res1"]), ch_l_edge(all_chapters["C3"]), "潜力等级", c_deliver)
    add_conn(res_r_edge(all_results["S05_res3"]), ch_l_edge(all_chapters["C3"]), "诊断综合", c_deliver)
    add_conn(res_r_edge(all_results["S06_res"]), ch_l_edge(all_chapters["C4"]), "总体理念", c_deliver)
    add_conn(res_r_edge(all_results["S07_res1"]), ch_l_edge(all_chapters["C4"]), "改造模式", c_deliver)
    add_conn(res_r_edge(all_results["S08_res1"]), ch_l_edge(all_chapters["C5"]), "用地沙盘", c_deliver)
    add_conn(res_r_edge(all_results["S08_res2"]), ch_l_edge(all_chapters["C5"]), "概念总规", c_deliver)
    add_conn(res_r_edge(all_results["S09_res1"]), ch_l_edge(all_chapters["C5"]), "交通系统", c_deliver)
    add_conn(res_r_edge(all_results["S09_res2"]), ch_l_edge(all_chapters["C5"]), "开敞空间", c_deliver)
    add_conn(res_r_edge(all_results["S09_res3"]), ch_l_edge(all_chapters["C5"]), "风貌控制", c_deliver)
    add_conn(res_r_edge(all_results["S10_res1"]), ch_l_edge(all_chapters["C6"]), "地块功能", c_deliver)
    add_conn(res_r_edge(all_results["S10_res2"]), ch_l_edge(all_chapters["C6"]), "AIGC人视", c_deliver)
    add_conn(res_r_edge(all_results["S11_res"]), ch_l_edge(all_chapters["C7"]), "开发时序", c_deliver)
    add_conn(res_r_edge(all_results["S12_res"]), ch_l_edge(all_chapters["C7"]), "设计导则", c_deliver)
    add_conn(res_r_edge(all_results["S14_res"]), ch_l_edge(all_chapters["C7"]), "技术推演", c_deliver)

    # =============================================================
    # PASS 1: DRAW CONNECTION LINES & GLOWS (No labels or cards yet)
    # =============================================================
    for start, end, label, color in connections:
        draw_curved_connection_line(draw, start, end, color)

    # Draw Stage -> Result direct horizontal links
    for sn in s_col1 + s_col2 + s_col3 + s_col4:
        linked_res = [r for r in r_col1 + r_col2 + r_col3 + r_col4 if r["stage"] == sn["id"]]
        for rn in linked_res:
            draw_glow_arrow(draw, s_r_edge(sn), res_l_edge(rn), c_stage_res, width=2)

    # =============================================================
    # PASS 2: DRAW CARDS (Saves bounding boxes to avoid overlaps)
    # =============================================================
    drawn_boxes = []

    # Column 0: RAW DATA CARDS
    for rn in raw_nodes:
        draw.rounded_rectangle([rn["x"], rn["y"], rn["x"] + rn["w"], rn["y"] + rn["h"]], radius=6, fill=SCHEMES["raw"]["fill"], outline=SCHEMES["raw"]["stroke"], width=1)
        draw.rectangle([rn["x"], rn["y"], rn["x"] + 12, rn["y"] + rn["h"]], fill=SCHEMES["raw"]["stroke"])
        draw.text((rn["x"] + 24, rn["y"] + 15), rn["title"], fill=(15, 23, 42), font=node_title_font)
        draw.text((rn["x"] + 24, rn["y"] + 58), rn["desc"], fill=(71, 85, 105), font=node_desc_font)
        drawn_boxes.append((rn["x"] - 5, rn["y"] - 5, rn["x"] + rn["w"] + 5, rn["y"] + rn["h"] + 5))

    # Stage Columns
    for sn in s_col1:
        draw_card(draw, sn["x"], sn["y"] - sn["h"]//2, sn["w"], sn["h"], sn["title"], [sn["desc"]], SCHEMES["stage"], node_title_font, node_desc_font)
        drawn_boxes.append((sn["x"] - 5, sn["y"] - sn["h"]//2 - 5, sn["x"] + sn["w"] + 5, sn["y"] + sn["h"]//2 + 5))
    for sn in s_col2:
        draw_card(draw, sn["x"], sn["y"] - sn["h"]//2, sn["w"], sn["h"], sn["title"], [sn["desc"]], SCHEMES["stage"], node_title_font, node_desc_font)
        drawn_boxes.append((sn["x"] - 5, sn["y"] - sn["h"]//2 - 5, sn["x"] + sn["w"] + 5, sn["y"] + sn["h"]//2 + 5))
    for sn in s_col3:
        draw_card(draw, sn["x"], sn["y"] - sn["h"]//2, sn["w"], sn["h"], sn["title"], [sn["desc"]], SCHEMES["stage"], node_title_font, node_desc_font)
        drawn_boxes.append((sn["x"] - 5, sn["y"] - sn["h"]//2 - 5, sn["x"] + sn["w"] + 5, sn["y"] + sn["h"]//2 + 5))
    for sn in s_col4:
        draw_card(draw, sn["x"], sn["y"] - sn["h"]//2, sn["w"], sn["h"], sn["title"], [sn["desc"]], SCHEMES["stage"], node_title_font, node_desc_font)
        drawn_boxes.append((sn["x"] - 5, sn["y"] - sn["h"]//2 - 5, sn["x"] + sn["w"] + 5, sn["y"] + sn["h"]//2 + 5))

    # Result Cards
    for rn in r_col1 + r_col2 + r_col3 + r_col4:
        draw_card(draw, rn["x"], rn["y"] - rn["h"]//2, rn["w"], rn["h"], rn["title"], rn["bullets"], SCHEMES["result"], node_title_font, node_desc_font)
        drawn_boxes.append((rn["x"] - 5, rn["y"] - rn["h"]//2 - 5, rn["x"] + rn["w"] + 5, rn["y"] + rn["h"]//2 + 5))

    # Chapter Cards
    for ch in chapters:
        draw.rounded_rectangle([ch["x"], ch["y"] - ch["h"]//2, ch["x"] + ch["w"], ch["y"] + ch["h"]//2], radius=10, fill=SCHEMES["deliverable"]["fill"], outline=SCHEMES["deliverable"]["stroke"], width=2)
        draw.rectangle([ch["x"] + 2, ch["y"] - ch["h"]//2 + 2, ch["x"] + ch["w"] - 2, ch["y"] - ch["h"]//2 + 50], fill=SCHEMES["deliverable"]["fill"])
        draw.line([ch["x"], ch["y"] - ch["h"]//2 + 50, ch["x"] + ch["w"], ch["y"] - ch["h"]//2 + 50], fill=SCHEMES["deliverable"]["stroke"], width=1)
        draw.text((ch["x"] + 16, ch["y"] - ch["h"]//2 + 10), ch["title"], fill=SCHEMES["deliverable"]["text"], font=group_font)
        by = ch["y"] - ch["h"]//2 + 62
        max_text_w = ch["w"] - 32
        for bullet in ch["bullets"]:
            wrapped_lines = wrap_text_to_lines(bullet, node_desc_font, max_text_w)
            for line in wrapped_lines:
                draw.text((ch["x"] + 16, by), line, fill=(71, 85, 105), font=node_desc_font)
                by += 26
        drawn_boxes.append((ch["x"] - 5, ch["y"] - ch["h"]//2 - 5, ch["x"] + ch["w"] + 5, ch["y"] + ch["h"]//2 + 5))

    # =============================================================
    # PASS 3: DRAW CONNECTION LABELS ON TOP (With Collision Avoidance)
    # =============================================================
    for start, end, label, color in connections:
        draw_curved_connection_label(draw, start, end, label, color, label_font, drawn_boxes)

    # -------------------------------------------------------------
    # Drawing Legends and Info stamp
    # -------------------------------------------------------------
    draw.rectangle([0, canvas_h - 120, canvas_w, canvas_h], fill=(241, 245, 249, 255))
    draw.line([(0, canvas_h - 120), (canvas_w, canvas_h - 120)], fill=(203, 213, 225, 255), width=2)

    legend_items = [
        ("原始数据层", SCHEMES["raw"]["stroke"]),
        ("规划阶段 (S00-S15)", SCHEMES["stage"]["stroke"]),
        ("规划成果结果层", SCHEMES["result"]["stroke"]),
        ("图册章节交付层", SCHEMES["deliverable"]["stroke"]),
        ("阶段直连流 (靛蓝)", (129, 140, 248)),
        ("原始加工流 (灰蓝)", (148, 163, 184)),
        ("算法分析流 (紫罗兰)", (168, 85, 247)),
        ("成果交付流 (琥珀黄)", (251, 191, 36))
    ]

    lx = 60
    ly = canvas_h - 75
    for title, color in legend_items:
        draw.rounded_rectangle([lx, ly, lx + 30, ly + 30], radius=4, fill=(255, 255, 255, 255), outline=color, width=2)
        draw.text((lx + 45, ly - 2), title, fill=(15, 23, 42), font=subtitle_font)
        lx += 620

    # Save to disk
    dest_path = os.path.join(OUTPUT_DIR, "unified_landscape_mindmap.png")
    img.save(dest_path, "PNG")
    
    # Also save as the knowledge graph to replace the dark theme version
    dest_path_kg = os.path.join(OUTPUT_DIR, "technology_parameters_knowledge_graph.png")
    img.save(dest_path_kg, "PNG")
    print(f"Unified 5K landscape flowchart generated successfully at:\n  {dest_path}\n  {dest_path_kg}")

if __name__ == "__main__":
    draw_unified_landscape()
