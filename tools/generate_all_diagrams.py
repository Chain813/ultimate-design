import os
import sys
from PIL import Image, ImageDraw, ImageFont
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

# -------------------------------------------------------------
# Utility Function to Draw Arrow
# -------------------------------------------------------------
def draw_arrow(draw, start, end, color, width=2, is_dashed=False):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = (dx**2 + dy**2)**0.5
    if length == 0:
        return
    ux = dx / length
    uy = dy / length
    
    # 2.5px back-off from the box border to avoid overlaps
    arrow_tip = (end[0] - 2.5 * ux, end[1] - 2.5 * uy)
    
    # Draw line to the backed-off tip
    draw.line([start, arrow_tip], fill=color, width=width)
    
    arrow_len = 10
    arrow_width = 6
    p1 = (arrow_tip[0] - arrow_len * ux + arrow_width * uy, arrow_tip[1] - arrow_len * uy - arrow_width * ux)
    p2 = (arrow_tip[0] - arrow_len * ux - arrow_width * uy, arrow_tip[1] - arrow_len * uy + arrow_width * ux)
    draw.polygon([arrow_tip, p1, p2], fill=color)

# -------------------------------------------------------------
# Utility Function to Draw Bezier-like Smooth Branch Line
# -------------------------------------------------------------
def draw_branch_line(draw, start, end, color, width=2):
    mid_x = (start[0] + end[0]) // 2
    draw.line([start, (mid_x, start[1]), (mid_x, end[1]), end], fill=color, width=width)

def draw_centered_text(draw, text, center, fill, font):
    try:
        w, h = draw.textsize(text, font=font)
    except:
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        w = right - left
        h = bottom - top
    draw.text((center[0] - w // 2, center[1] - h // 2), text, fill=fill, font=font)

# -------------------------------------------------------------
# DIAGRAM 1: Workflow Flowchart
# -------------------------------------------------------------
def generate_workflow_flowchart():
    print("Generating workflow flowchart...")
    img = Image.new("RGB", (1920, 1080), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype(FONT_BOLD_PATH, 36)
        subtitle_font = ImageFont.truetype(FONT_PATH, 20)
        node_title_font = ImageFont.truetype(FONT_BOLD_PATH, 22)
        node_desc_font = ImageFont.truetype(FONT_PATH, 16)
        col_title_font = ImageFont.truetype(FONT_BOLD_PATH, 24)
    except:
        title_font = subtitle_font = node_title_font = node_desc_font = col_title_font = ImageFont.load_default()

    draw.rectangle([0, 0, 1920, 80], fill=(241, 245, 249))
    draw.line([(0, 80), (1920, 80)], fill=(203, 213, 225), width=2)
    draw.text((40, 20), "城市更新智能推演平台 —— 全流程16阶段工作流", fill=(15, 23, 42), font=title_font)
    draw.text((1550, 32), "v2.5.0 精细重构版", fill=(100, 116, 139), font=subtitle_font)

    COLOR_SCHEMES = {
        "data": {"fill": (239, 246, 255), "stroke": (59, 130, 246), "text": (30, 58, 138), "desc": "数据底座与分析"},
        "strategy": {"fill": (250, 245, 255), "stroke": (168, 85, 247), "text": (88, 28, 135), "desc": "智能决策与策略"},
        "design": {"fill": (240, 253, 244), "stroke": (34, 197, 94), "text": (20, 83, 45), "desc": "空间规划与深化"},
        "output": {"fill": (254, 243, 199), "stroke": (245, 158, 11), "text": (120, 53, 4), "desc": "成果表达与交付"},
        "tool": {"fill": (241, 245, 249), "stroke": (100, 116, 139), "text": (51, 65, 85), "desc": "共享辅助工具"}
    }

    NODES = {
        "S00": {"id": "S00", "name": "Stage 00 数据准备", "desc": "上传/校验10大类数据", "col": 0, "row": 0.5, "type": "data"},
        "S01": {"id": "S01", "name": "Stage 01 任务解读", "desc": "NLP提取任务书约束", "col": 0, "row": 1.7, "type": "data"},
        "S02": {"id": "S02", "name": "Stage 02 资料收集", "desc": "构建政策知识库(RAG)", "col": 0, "row": 2.9, "type": "data"},
        "S03": {"id": "S03", "name": "Stage 03 现场调研", "desc": "街景分割(GVI/SVF)", "col": 0, "row": 4.1, "type": "data"},
        "S04": {"id": "S04", "name": "Stage 04 现状分析", "desc": "3D全息数字孪生底座", "col": 1, "row": 1.5, "type": "data"},
        "S05": {"id": "S05", "name": "Stage 05 问题诊断", "desc": "AHP-MPI潜力更新评估", "col": 1, "row": 3.0, "type": "data"},
        "S06": {"id": "S06", "name": "Stage 06 目标定位", "desc": "提炼设计理念与愿景", "col": 2, "row": 1.5, "type": "strategy"},
        "S07": {"id": "S07", "name": "Stage 07 设计策略", "desc": "多主体博弈与合规预审", "col": 2, "row": 3.0, "type": "strategy"},
        "S08": {"id": "S08", "name": "Stage 08 总体城市设计", "desc": "沙盘推演与概念总规", "col": 3, "row": 0.5, "type": "design"},
        "S09": {"id": "S09", "name": "Stage 09 专项系统设计", "desc": "交通/绿地/风貌专项", "col": 3, "row": 1.7, "type": "design"},
        "S10": {"id": "S10", "name": "Stage 10 重点地段深化", "desc": "Before/After AIGC推演", "col": 3, "row": 2.9, "type": "design"},
        "S11": {"id": "S11", "name": "Stage 11 实施路径", "desc": "“留改拆”时空分期规划", "col": 3, "row": 4.1, "type": "design"},
        "S12": {"id": "S12", "name": "Stage 12 城市设计导则", "desc": "控制条文与红头Docx导出", "col": 3, "row": 5.3, "type": "design"},
        "S13": {"id": "S13", "name": "Stage 13 成果表达", "desc": "A3规划图册自动排版", "col": 4, "row": 1.7, "type": "output"},
        "S14": {"id": "S14", "name": "Stage 14 视频生成", "desc": "智能分镜与汇报视频生成", "col": 4, "row": 3.0, "type": "output"},
        "S15": {"id": "S15", "name": "Stage 15 AIGC设计推演", "desc": "Stable Diffusion生形辅助页", "col": 4, "row": 4.5, "type": "tool"}
    }

    EDGES = [
        ("S00", "S02", "direct"), ("S02", "S04", "direct"), ("S03", "S04", "direct"),
        ("S04", "S05", "direct"), ("S01", "S06", "direct"), ("S05", "S06", "direct"),
        ("S05", "S07", "direct"), ("S06", "S07", "direct"), ("S07", "S08", "direct"),
        ("S07", "S11", "direct"), ("S07", "S12", "direct"), ("S08", "S09", "direct"),
        ("S09", "S10", "direct"), ("S10", "S11", "direct"), ("S10", "S12", "direct"),
        ("S05", "S10", "direct"), ("S11", "S13", "direct"), ("S12", "S13", "direct"),
        ("S13", "S14", "direct"), ("S15", "S08", "tool"), ("S15", "S10", "tool"),
        ("S15", "S13", "tool")
    ]

    COL_X = [120, 480, 840, 1200, 1560]
    ROW_Y = [120, 260, 400, 540, 680, 820, 960]
    card_w, card_h = 280, 90

    cols_meta = [
        {"type": "data", "title": "01. 数据底座与现状诊断"},
        {"type": "data", "title": "02. 空间现状量化分析"},
        {"type": "strategy", "title": "03. 智能多主体博弈决策"},
        {"type": "design", "title": "04. 空间规划与深化设计"},
        {"type": "output", "title": "05. 成果集成与智能交付"}
    ]

    for i, col_x in enumerate(COL_X):
        draw.rectangle([col_x - 15, 100, col_x + card_w + 15, 1080 - 40], fill=(255, 255, 255), outline=(226, 232, 240), width=1)
        meta = cols_meta[i]
        scheme = COLOR_SCHEMES[meta["type"]]
        draw.rectangle([col_x - 15, 100, col_x + card_w + 15, 145], fill=scheme["fill"])
        draw.line([col_x - 15, 145, col_x + card_w + 15, 145], fill=scheme["stroke"], width=2)
        draw.text((col_x + 10, 112), meta["title"], fill=scheme["text"], font=col_title_font)

    for node_id, node in NODES.items():
        cx = COL_X[node["col"]] + card_w // 2
        row_idx = int(node["row"])
        frac = node["row"] - row_idx
        y_base = ROW_Y[row_idx]
        y_next = ROW_Y[row_idx + 1] if row_idx + 1 < len(ROW_Y) else y_base + 140
        cy = y_base + int((y_next - y_base) * frac) + 40
        node["cx"] = cx
        node["cy"] = cy

    for start_id, end_id, edge_type in EDGES:
        s_node, e_node = NODES[start_id], NODES[end_id]
        sx, sy = s_node["cx"], s_node["cy"]
        ex, ey = e_node["cx"], e_node["cy"]
        
        if s_node["col"] < e_node["col"]:
            p_start, p_end = (sx + card_w // 2, sy), (ex - card_w // 2, ey)
        elif s_node["col"] > e_node["col"]:
            p_start, p_end = (sx - card_w // 2, sy), (ex + card_w // 2, ey)
        else:
            if sy < ey:
                p_start, p_end = (sx, sy + card_h // 2), (ex, ey - card_h // 2)
            else:
                p_start, p_end = (sx, sy - card_h // 2), (ex, ey + card_h // 2)

        if edge_type == "tool":
            draw_arrow(draw, p_start, p_end, color=(148, 163, 184), width=1, is_dashed=True)
        else:
            if abs(s_node["col"] - e_node["col"]) <= 1:
                draw_arrow(draw, p_start, p_end, color=(71, 85, 105), width=2)
            else:
                mid_x = (p_start[0] + p_end[0]) // 2
                draw.line([p_start, (mid_x, p_start[1]), (mid_x, p_end[1]), p_end], fill=(100, 116, 139), width=2)
                draw_arrow(draw, (mid_x, p_end[1]), p_end, color=(71, 85, 105), width=2)

    for node_id, node in NODES.items():
        scheme = COLOR_SCHEMES[node["type"]]
        x0, y0 = node["cx"] - card_w // 2, node["cy"] - card_h // 2
        x1, y1 = node["cx"] + card_w // 2, node["cy"] + card_h // 2
        
        draw.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=scheme["fill"], outline=scheme["stroke"], width=2)
        draw.rounded_rectangle([x0 + 10, y0 + 10, x0 + 70, y0 + 38], radius=4, fill=scheme["stroke"])
        draw.text((x0 + 18, y0 + 13), node_id, fill=(255, 255, 255), font=subtitle_font)
        draw.text((x0 + 76, y0 + 12), node["name"].split(" ", 1)[1], fill=scheme["text"], font=node_title_font)
        draw.text((x0 + 15, y0 + 50), node["desc"], fill=(71, 85, 105), font=node_desc_font)

    # Legend
    legend_y = 1080 - 30
    draw.text((40, legend_y), "图例分类: ", fill=(15, 23, 42), font=node_title_font)
    offset_x = 150
    for key, val in COLOR_SCHEMES.items():
        draw.rounded_rectangle([offset_x, legend_y - 2, offset_x + 20, legend_y + 12], radius=3, fill=val["fill"], outline=val["stroke"])
        draw.text((offset_x + 28, legend_y - 2), val["desc"], fill=(15, 23, 42), font=subtitle_font)
        offset_x += 240

    img.save(os.path.join(OUTPUT_DIR, "workflow_flowchart.png"), "PNG")
    print("Workflow flowchart generated!")

# -------------------------------------------------------------
# DIAGRAM 2: System Architecture Mind Map (系统架构全景思维导图)
# -------------------------------------------------------------
def generate_system_architecture_mindmap():
    print("Generating system architecture mindmap...")
    canvas_h = 1080
    img = Image.new("RGB", (1920, canvas_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype(FONT_BOLD_PATH, 36)
        subtitle_font = ImageFont.truetype(FONT_PATH, 20)
        node_title_font = ImageFont.truetype(FONT_BOLD_PATH, 22)
        node_desc_font = ImageFont.truetype(FONT_PATH, 16)
        section_title_font = ImageFont.truetype(FONT_BOLD_PATH, 26)
    except:
        title_font = subtitle_font = node_title_font = node_desc_font = section_title_font = ImageFont.load_default()

    # Header
    draw.rectangle([0, 0, 1920, 80], fill=(241, 245, 249))
    draw.line([(0, 80), (1920, 80)], fill=(203, 213, 225), width=2)
    draw.text((40, 20), "城市更新智能推演平台 —— 系统架构全景思维导图", fill=(15, 23, 42), font=title_font)
    draw.text((1380, 32), "核心业务引擎与交互控制层 (数据层已分离)", fill=(100, 116, 139), font=subtitle_font)

    # Colors
    ROOT_SCHEME = {"fill": (239, 246, 255), "stroke": (59, 130, 246), "text": (30, 58, 138)}
    BRANCH_SCHEMES = [
        {"fill": (239, 246, 255), "stroke": (59, 130, 246), "text": (30, 58, 138), "title": "LLM 与智能体推演层"},
        {"fill": (240, 253, 244), "stroke": (34, 197, 94), "text": (20, 83, 45), "title": "空间计算与诊断引擎层"},
        {"fill": (250, 245, 255), "stroke": (168, 85, 247), "text": (88, 28, 135), "title": "Streamlit 交互与可视化层"}
    ]

    # Leaves configuration (3 columns, 3 cards each)
    LEAF_CARDS = [
        # Column 0: LLM与智能体推演层
        {"branch": 0, "title": "多主体博弈引擎 (agent_debate)", "bullets": ["• 政府、开发商、居民三方立场提示词装配", "• Ollama/DeepSeek 自动化角色博弈与对话生成", "• 多视角利益协商与规划共识策略产出"]},
        {"branch": 0, "title": "控规导则翻译器 (rule_translator)", "bullets": ["• 任务书设计约束提取与规范冲突校验", "• 自然语言到空间控制指标参数 the 翻译模型", "• 生成的城市设计控制条文文书自动排版"]},
        {"branch": 0, "title": "AIGC 生形控制 (image_generator)", "bullets": ["• ControlNet 空间刚性边界（轮廓与红线）控制", "• 总体规划平面及街区透视改造提示词装配", "• Before/After 改造前后效果渲染与方案生成"]},
        
        # Column 1: 空间计算与诊断引擎层
        {"branch": 1, "title": "空间数据诊断分析 (spatial_diagnostics)", "bullets": ["• 用地现状属性 analysis、现状层数高度诊断", "• 道路路网密度计算与空间句法可达性评价", "• 绿化景观网络结构与口袋公园服务半径诊断"]},
        {"branch": 1, "title": "社会感知与价值评估 (valuation_engine)", "bullets": ["• 积水区风险识别与暴雨洪涝安全防灾评估 (新)", "• NLP微博情感挖掘与居民痛点品质地图", "• POI活力度评价与文化遗产风貌敏感度评价"]},
        {"branch": 1, "title": "更新潜力与指标核验 (potentials_model)", "bullets": ["• AHP 层次分析法指标权重管理与潜力排序", "• 留改拆模式分区识别与用地沙盘指标测算", "• 规划总平面图面积/绿地率等规划指标表核验"]},

        # Column 2: Streamlit 交互与可视化层
        {"branch": 2, "title": "数字孪生 HUD 首页 (twin_dashboard)", "bullets": ["• 全球指标数据面板 (HUD) 实时可视化集成", "• Pydeck / Deck.GL 现状建筑与水绿三维仿真", "• 城市现状综合病理热力图叠加与灯光控制"]},
        {"branch": 2, "title": "全生命周期阶段面板 (16_stages_ui)", "bullets": ["• 严格对应 16 个功能开发阶段交互控制面板", "• 前后端 RAG 政策问答及指标分析控制闭环", "• A3 标准图纸自动化排版预览与 PDF 下载"]},
        {"branch": 2, "title": "证据链依赖与状态监控 (sniffer_bus)", "bullets": ["• require_upstream 自动上游依赖分析与阻断", "• Ollama / SD 绘图引擎本地服务在线状态监控", "• 一键填充测试 Mock 数据与全流程异常日志提示"]}
    ]

    # Positions
    root_x = 960
    root_y = 150
    root_w, root_h = 480, 80

    branch_centers = [320, 960, 1600]
    branch_w, branch_h = 420, 60
    b_y = 300

    leaf_w, leaf_h = 480, 130

    # Layout coordinate mapping for leaves:
    b0_y = [390, 570, 750]
    b1_y = [390, 570, 750]
    b2_y = [390, 570, 750]

    b0_count = 0
    b1_count = 0
    b2_count = 0

    for card in LEAF_CARDS:
        b = card["branch"]
        if b == 0:
            card["x"] = 320 - 240
            card["y"] = b0_y[b0_count]
            b0_count += 1
        elif b == 1:
            card["x"] = 960 - 240
            card["y"] = b1_y[b1_count]
            b1_count += 1
        elif b == 2:
            card["x"] = 1600 - 240
            card["y"] = b2_y[b2_count]
            b2_count += 1

    # 1. Draw connections from Root to Branches (Orthogonal top-down tree style)
    draw.line([(960, 190), (960, 230), (320, 230), (320, 270)], fill=(148, 163, 184), width=2)
    draw.line([(960, 190), (960, 270)], fill=(148, 163, 184), width=2)
    draw.line([(960, 190), (960, 230), (1600, 230), (1600, 270)], fill=(148, 163, 184), width=2)

    # 2. Draw Root Node
    draw.rounded_rectangle([root_x - root_w // 2, root_y - root_h // 2, root_x + root_w // 2, root_y + root_h // 2], radius=10, fill=ROOT_SCHEME["fill"], outline=ROOT_SCHEME["stroke"], width=3)
    draw_centered_text(draw, "城市更新智能推演平台 —— 架构", (root_x, root_y), ROOT_SCHEME["text"], section_title_font)

    # 3. Draw Branch Nodes & Leaves
    for b_idx in [0, 1, 2]:
        b_scheme = BRANCH_SCHEMES[b_idx]
        cx = branch_centers[b_idx]
        b_leaves = [card for card in LEAF_CARDS if card["branch"] == b_idx]
        
        # Draw Branch Box
        draw.rounded_rectangle([cx - branch_w // 2, b_y - branch_h // 2, cx + branch_w // 2, b_y + branch_h // 2], radius=8, fill=b_scheme["fill"], outline=b_scheme["stroke"], width=2)
        draw_centered_text(draw, b_scheme["title"], (cx, b_y), b_scheme["text"], section_title_font)

        # Backbone X position for this column
        backbone_x = cx - 240 - 15
        
        # Draw trunk line from branch left side (cx - 210, b_y) to backbone_x
        draw.line([(cx - 210, b_y), (backbone_x, b_y)], fill=b_scheme["stroke"], width=2)
        
        # Backbone vertical bottom Y
        last_leaf_y_center = b_leaves[-1]["y"] + leaf_h // 2
        
        # Draw vertical backbone line
        draw.line([(backbone_x, b_y), (backbone_x, last_leaf_y_center)], fill=b_scheme["stroke"], width=2)

        # Draw Leaves & their connections to Backbone
        for card in b_leaves:
            lx, ly = card["x"], card["y"]
            ly_center = ly + leaf_h // 2
            
            # Connection from backbone to leaf box left edge lx
            draw.line([(backbone_x, ly_center), (lx, ly_center)], fill=b_scheme["stroke"], width=1)

            # Draw Leaf Box
            draw.rounded_rectangle([lx, ly, lx + leaf_w, ly + leaf_h], radius=6, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
            # Leaf Header Bar
            draw.rectangle([lx, ly, lx + leaf_w, ly + 34], fill=b_scheme["fill"])
            draw.line([lx, ly + 34, lx + leaf_w, ly + 34], fill=b_scheme["stroke"], width=1)
            # Leaf Title
            draw.text((lx + 12, ly + 6), card["title"], fill=b_scheme["text"], font=node_title_font)

            # Leaf Bullets
            bullet_y = ly + 40
            for bullet in card["bullets"]:
                draw.text((lx + 12, bullet_y), bullet, fill=(71, 85, 105), font=node_desc_font)
                bullet_y += 20

    img.save(os.path.join(OUTPUT_DIR, "system_architecture_mindmap.png"), "PNG")
    print("System architecture mindmap generated!")

# -------------------------------------------------------------
# DIAGRAM 3: Data Pipeline Mind Map (数据管线架构思维导图)
# -------------------------------------------------------------
def generate_data_pipeline_mindmap():
    print("Generating data pipeline mindmap...")
    canvas_h = 1080
    img = Image.new("RGB", (1920, canvas_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype(FONT_BOLD_PATH, 36)
        subtitle_font = ImageFont.truetype(FONT_PATH, 20)
        node_title_font = ImageFont.truetype(FONT_BOLD_PATH, 22)
        node_desc_font = ImageFont.truetype(FONT_PATH, 16)
        section_title_font = ImageFont.truetype(FONT_BOLD_PATH, 26)
    except:
        title_font = subtitle_font = node_title_font = node_desc_font = section_title_font = ImageFont.load_default()

    # Header
    draw.rectangle([0, 0, 1920, 80], fill=(241, 245, 249))
    draw.line([(0, 80), (1920, 80)], fill=(203, 213, 225), width=2)
    draw.text((40, 20), "城市更新智能推演平台 —— 数据管线架构思维导图", fill=(15, 23, 42), font=title_font)
    draw.text((1380, 32), "贯穿全流程的数据管线", fill=(100, 116, 139), font=subtitle_font)

    # Colors
    ROOT_SCHEME = {"fill": (253, 242, 248), "stroke": (236, 72, 153), "text": (157, 23, 77)}
    BRANCH_SCHEMES = [
        {"fill": (239, 246, 255), "stroke": (59, 130, 246), "text": (30, 58, 138), "title": "原始数据入口"},
        {"fill": (240, 253, 244), "stroke": (34, 197, 94), "text": (20, 83, 45), "title": "数据处理中枢"},
        {"fill": (254, 243, 199), "stroke": (245, 158, 11), "text": (120, 53, 4), "title": "数据总线输出 (stage_bus)"}
    ]

    # Leaves configuration
    LEAF_CARDS = [
        # Children of Branch 0 (原始数据入口)
        {"branch": 0, "title": "GIS 空间矢量数据", "bullets": ["• Boundary_Scope.geojson (研究红线范围边界)", "• Building_Footprints.geojson (建筑现状轮廓几何体)", "• Key_Plots_District.json (5大重点开发地块边界)", "• road/rail/landuse_clipped.geojson (路网/铁轨/现状用地)"]},
        {"branch": 0, "title": "CSV/Excel 统计表格", "bullets": ["• Changchun_POI_Real.csv (现状POI分类兴趣点)", "• Traffic_Real.csv (交通设施) / Traffic_Flow.csv (流量)", "• GVI_Results_Analysis.csv (街景绿视率与围合度评价)", "• Building_Years.csv / House_Prices.csv / Sunshine_*.csv"]},
        {"branch": 0, "title": "街景图片与非结构文本", "bullets": ["• Point_*/heading_*.jpg (四方向现状调研实景照片)", "• rag_knowledge.json (城市更新地方政策法规库)", "• mission_text.txt / extracted_constraints.txt (任务书规划约束)"]},
        
        # Children of Branch 1 (数据处理中枢)
        {"branch": 1, "title": "全局路径与类别注册", "bullets": ["• paths.py: 集中式静态文件与资产路径注册器", "• data_categories.py: 10大数据类型描述、获取方法及检验规则"]},
        {"branch": 1, "title": "空间数据注入与文本桥梁", "bullets": ["• spatial_data_injector.py: 提供GIS几何到自然语言的转化", "• 提取相邻地块建筑面积/路网密度/设施覆盖度并注入LLM"]},
        {"branch": 1, "title": "量化统计与更新诊断引擎", "bullets": ["• spatial_engine.py: 统计及分析GVI绿视率、日照及交通指标", "• site_diagnostic_engine.py: AHP-MPI 潜力地块测度与诊断模型"]},

        # Children of Branch 2 (数据总线输出)
        {"branch": 2, "title": "阶段 05-06 产出 (现状诊断)", "bullets": ["• diagnosis_report: 用地及空间分析综合诊断报告文本", "• mpi_ranking: 现状地块更新优先级排行", "• design_concept: LLM生成的总体设计概念与发展定位"]},
        {"branch": 2, "title": "阶段 07-08 产出 (博弈与总规)", "bullets": ["• strategy_matrix: 三方博弈生成的设计策略矩阵项", "• master_plan: 总体规划总平面图ControlNet底图及提示词", "• landuse_sandbox: 用地沙盘调控与指标计算结果"]},
        {"branch": 2, "title": "阶段 09-10 产出 (专项与深化)", "bullets": ["• traffic_system / public_space: 交通与开敞空间专项方案", "• plot_design: 5个重点地块深化后的三维设计引导建议", "• before_after: 重点地段更新前后透视效果对比图资产"]},
        {"branch": 2, "title": "阶段 11-13 产出 (实施与交付)", "bullets": ["• temporal_stages: “留改拆”时空分期实施路径", "• design_guideline: 生成的城市设计控制条文文书", "• atlas_layouts: 自动化排版生成的 A3 规划图册版面"]}
    ]

    # Positions
    root_x = 960
    root_y = 150
    root_w, root_h = 360, 80

    branch_centers = [320, 960, 1600]
    branch_w, branch_h = 420, 60
    b_y = 300

    leaf_w, leaf_h = 480, 130

    # Layout coordinate mapping for leaves:
    b0_y = [390, 570, 750]
    b1_y = [390, 570, 750]
    b2_y = [390, 550, 710, 870]

    b0_count = 0
    b1_count = 0
    b2_count = 0

    for card in LEAF_CARDS:
        b = card["branch"]
        if b == 0:
            card["x"] = 320 - 240
            card["y"] = b0_y[b0_count]
            b0_count += 1
        elif b == 1:
            card["x"] = 960 - 240
            card["y"] = b1_y[b1_count]
            b1_count += 1
        elif b == 2:
            card["x"] = 1600 - 240
            card["y"] = b2_y[b2_count]
            b2_count += 1

    # 1. Draw connections from Root to Branches (Orthogonal top-down tree style)
    draw.line([(960, 190), (960, 230), (320, 230), (320, 270)], fill=(148, 163, 184), width=2)
    draw.line([(960, 190), (960, 270)], fill=(148, 163, 184), width=2)
    draw.line([(960, 190), (960, 230), (1600, 230), (1600, 270)], fill=(148, 163, 184), width=2)

    # 2. Draw Root Node
    draw.rounded_rectangle([root_x - root_w // 2, root_y - root_h // 2, root_x + root_w // 2, root_y + root_h // 2], radius=10, fill=ROOT_SCHEME["fill"], outline=ROOT_SCHEME["stroke"], width=3)
    draw_centered_text(draw, "数据管线总线架构", (root_x, root_y), ROOT_SCHEME["text"], section_title_font)

    # 3. Draw Branch Nodes & Leaves
    for b_idx, b_scheme in enumerate(BRANCH_SCHEMES):
        cx = branch_centers[b_idx]
        b_leaves = [card for card in LEAF_CARDS if card["branch"] == b_idx]
        
        # Draw Branch Box
        draw.rounded_rectangle([cx - branch_w // 2, b_y - branch_h // 2, cx + branch_w // 2, b_y + branch_h // 2], radius=8, fill=b_scheme["fill"], outline=b_scheme["stroke"], width=2)
        draw_centered_text(draw, b_scheme["title"], (cx, b_y), b_scheme["text"], section_title_font)

        # Backbone X position for this column
        backbone_x = cx - 240 - 15
        
        # Draw trunk line from branch left side (cx - 210, b_y) to backbone_x
        draw.line([(cx - 210, b_y), (backbone_x, b_y)], fill=b_scheme["stroke"], width=2)
        
        # Backbone vertical bottom Y
        last_leaf_y_center = b_leaves[-1]["y"] + leaf_h // 2
        
        # Draw vertical backbone line
        draw.line([(backbone_x, b_y), (backbone_x, last_leaf_y_center)], fill=b_scheme["stroke"], width=2)

        # Draw Leaves & their connections to Backbone
        for card in b_leaves:
            lx, ly = card["x"], card["y"]
            ly_center = ly + leaf_h // 2
            
            # Connection from backbone to leaf box left edge lx
            draw.line([(backbone_x, ly_center), (lx, ly_center)], fill=b_scheme["stroke"], width=1)

            # Draw Leaf Box
            draw.rounded_rectangle([lx, ly, lx + leaf_w, ly + leaf_h], radius=6, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
            # Leaf Header Bar
            draw.rectangle([lx, ly, lx + leaf_w, ly + 34], fill=b_scheme["fill"])
            draw.line([lx, ly + 34, lx + leaf_w, ly + 34], fill=b_scheme["stroke"], width=1)
            # Leaf Title
            draw.text((lx + 12, ly + 6), card["title"], fill=b_scheme["text"], font=node_title_font)

            # Leaf Bullets
            bullet_y = ly + 40
            for bullet in card["bullets"]:
                draw.text((lx + 12, bullet_y), bullet, fill=(71, 85, 105), font=node_desc_font)
                bullet_y += 20

    img.save(os.path.join(OUTPUT_DIR, "data_pipeline_mindmap.png"), "PNG")
    print("Data pipeline mindmap generated!")

# -------------------------------------------------------------
# DIAGRAM 4: Atlas Chapters Mind Map (图册章节与图纸清单分层树状图)
# -------------------------------------------------------------
def generate_atlas_chapters_mindmap():
    print("Generating atlas chapters mindmap...")
    # Clean top-down tree canvas (2100 width, 1400 height for 6 chapters)
    img = Image.new("RGB", (2100, 1400), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype(FONT_BOLD_PATH, 24)
        subtitle_font_small = ImageFont.truetype(FONT_PATH, 16)
        subtitle_font = ImageFont.truetype(FONT_PATH, 18)
        chapter_title_font = ImageFont.truetype(FONT_BOLD_PATH, 20)
        subgroup_title_font = ImageFont.truetype(FONT_BOLD_PATH, 16)
        bullet_font = ImageFont.truetype(FONT_PATH, 14)
        section_title_font = ImageFont.truetype(FONT_BOLD_PATH, 24)
    except:
        title_font = subtitle_font = subtitle_font_small = chapter_title_font = subgroup_title_font = bullet_font = section_title_font = ImageFont.load_default()

    # Header
    draw.rectangle([0, 0, 2100, 80], fill=(241, 245, 249))
    draw.line([(0, 80), (2100, 80)], fill=(203, 213, 225), width=2)
    draw.text((40, 16), "城市更新智能推演平台", fill=(100, 116, 139), font=subtitle_font_small)
    draw.text((40, 40), "规划图册章节与图纸清单分层树状图", fill=(15, 23, 42), font=title_font)
    draw.text((1720, 30), "6 大章节与 64 张图纸分层目录树", fill=(100, 116, 139), font=subtitle_font)

    # Helper function for vertical branch lines
    def draw_vertical_branch_line(draw_obj, start_pt, end_pt, color, line_w=2):
        mid_y = (start_pt[1] + end_pt[1]) // 2
        draw_obj.line([start_pt, (start_pt[0], mid_y), (end_pt[0], mid_y), end_pt], fill=color, width=line_w)

    # Colors
    ROOT_SCHEME = {"fill": (240, 253, 244), "stroke": (34, 197, 94), "text": (20, 83, 45)}
    
    CHAPTERS = [
        {
            "num": "01",
            "title": "01 项目认知篇",
            "fill": (239, 246, 255), "stroke": (59, 130, 246), "text": (30, 58, 138),
            "groups": [
                {"title": "1.1 基础前言 (P01-03)", "bullets": ["• P01 封面 (孪生风貌)", "• P02 目录 (图册结构)", "• P03 背景 (存量更新趋势)"]},
                {"title": "1.2 区位现状 (P04-06)", "bullets": ["• P04 区位分析 (三级区位)", "• P05 研究范围与重点地块", "• P06 周边站城联动关系"]},
                {"title": "1.3 上位指引 (P07-09)", "bullets": ["• P07 上位规划深度解读", "• P08 规划依据与技术标准", "• P09 街区历史空间沿革"]},
                {"title": "1.4 范式借鉴 (P10-11)", "bullets": ["• P10 国内案例 (微更新)", "• P11 国外案例 (站城融合)"]}
            ]
        },
        {
            "num": "03",
            "title": "03 价值评估篇",
            "fill": (254, 243, 199), "stroke": (245, 158, 11), "text": (120, 53, 4),
            "groups": [
                {"title": "3.1 遗产与防灾评估 (P32-34)", "bullets": ["• P32 遗产价值评估热力", "• P33 风貌高度敏感分区", "• P34 积水区风险分析"]},
                {"title": "3.2 更新潜力与分区 (P35-37)", "bullets": ["• P35 更新潜力评价图纸", "• P36 保护与更新冲突叠合", "• P37 综合评价单元分区"]}
            ]
        },
        {
            "num": "04",
            "title": "04 策略生成篇",
            "fill": (253, 242, 248), "stroke": (236, 72, 153), "text": (157, 23, 77),
            "groups": [
                {"title": "4.1 理念与定位 (P38-40)", "bullets": ["• P38 精准更新设计理念", "• P39 项目定位", "• P40 多维度更新目标体系"]},
                {"title": "4.2 结构与分区 (P41-45)", "bullets": ["• P41 整体概念设计和更新", "• P42 留改拆更新模式分区", "• P43 文化/生活功能策划", "• P44 空间结构规划(一核)", "• P45 5个重点地块定位"]}
            ]
        },
        {
            "num": "05",
            "title": "05 整体概念设计和更新",
            "fill": (245, 243, 255), "stroke": (139, 92, 246), "text": (76, 29, 149),
            "groups": [
                {"title": "5.1 空间与更新分区 (P46-49)", "bullets": ["• P46 整体概念规划总平面", "• P47 空间结构规划图", "• P48 城市更新模式分区图", "• P49 建筑更新控制引导图"]},
                {"title": "5.2 景观结构系统 (P50-52)", "bullets": ["• P50 景观结构与绿地系统", "• P51 连续绿色生态廊道", "• P52 口袋公园公共空间"]},
                {"title": "5.3 交通系统设计 (P53-56)", "bullets": ["• P53 道路系统规划图", "• P54 小街区密路网规划", "• P55 慢行系统规划图", "• P56 公共交通与换乘接驳"]},
                {"title": "5.4 控制引导与指标 (P57-60)", "bullets": ["• P57 建筑高度风貌控制", "• P58 开发强度指标控制", "• P59 历史游线与夜景导视", "• P60 概念规划核心指标表"]}
            ]
        },
        {
            "num": "06",
            "title": "06 重点地段更新改造设计",
            "fill": (250, 245, 255), "stroke": (168, 85, 247), "text": (88, 28, 135),
            "groups": [
                {"title": "6.1 站城门户更新 (P61-64)", "bullets": ["• P61 门户现状问题定位", "• P62 门户节点平面深化", "• P63 AIGC立面生形推演", "• P64 节点广场人视透视"]},
                {"title": "6.2 工业遗产活化 (P65-68)", "bullets": ["• P65 中车工业遗存诊断", "• P66 工业遗存功能置换", "• P67 建筑更新改造控制", "• P68 厂区活化鸟瞰效果"]},
                {"title": "6.3 老旧社区微更新 (P69-72)", "bullets": ["• P69 社区适老现状诊断", "• P70 社区口袋公园设计", "• P71 住宅立面整治图纸", "• P72 改造前后成效对比"]},
                {"title": "6.4 历史风貌协调 (P73-76)", "bullets": ["• P73 皇宫风貌界面诊断", "• P74 皇宫风貌平面深化", "• P75 沿街立面材质控制", "• P76 街道断面优化设计"]},
                {"title": "6.5 文旅活力街巷 (P77-80)", "bullets": ["• P77 街巷现状活力分析", "• P78 活力街巷铺面设计", "• P79 街巷空间人视透视", "• P80 持续运营场景策划"]}
            ]
        },
        {
            "num": "07",
            "title": "07 技术推演与实施篇",
            "fill": (241, 245, 249), "stroke": (100, 116, 139), "text": (51, 65, 85),
            "groups": [
                {"title": "7.1 技术推演 (P81-82)", "bullets": ["• P81 AIGC技术推演过程", "• P82 近中远期实施时序"]},
                {"title": "7.2 协同治理 (P83-84)", "bullets": ["• P84 协同运营机制建议", "• P85 更新成效综合评估"]}
            ]
        }
    ]

    # Coordinates for top-down root node (centered at 1050)
    root_x = 880
    root_y = 100
    root_w, root_h = 340, 90

    # Draw Root Node
    draw.rounded_rectangle([root_x, root_y - root_h // 2, root_x + root_w, root_y + root_h // 2], radius=10, fill=ROOT_SCHEME["fill"], outline=ROOT_SCHEME["stroke"], width=3)
    draw_centered_text(draw, "规划图册章节与清单", (root_x + root_w // 2, root_y - 18), ROOT_SCHEME["text"], section_title_font)
    draw_centered_text(draw, "(6 大章节 / 64 张规划与设计图纸)", (root_x + root_w // 2, root_y + 20), (100, 116, 139), subtitle_font)

    # Layout chapters horizontally
    y_chapters = 260
    col_width_pitch = 340
    col_start_x = 40

    for i, ch in enumerate(CHAPTERS):
        col_base_x = col_start_x + i * col_width_pitch
        
        # Chapter card top-left
        ch_x = col_base_x + 30
        ch_y = y_chapters
        ch_w = 260
        ch_h = 80
        
        # Connection: Root -> Chapter Card top-center
        draw_vertical_branch_line(draw, (root_x + root_w // 2, root_y + root_h // 2), (ch_x + ch_w // 2, ch_y), color=(148, 163, 184), line_w=2)

        # Draw Chapter Card
        draw.rounded_rectangle([ch_x, ch_y, ch_x + ch_w, ch_y + ch_h], radius=8, fill=(255, 255, 255), outline=ch["stroke"], width=2)
        # Header bar in Chapter Card
        draw.rectangle([ch_x, ch_y, ch_x + ch_w, ch_y + 30], fill=ch["fill"])
        draw.line([ch_x, ch_y + 30, ch_x + ch_w, ch_y + 30], fill=ch["stroke"], width=1)
        # Chapter Title text
        draw_centered_text(draw, ch["title"], (ch_x + ch_w // 2, ch_y + 55), ch["text"], chapter_title_font)
        draw_centered_text(draw, f"Chapter {ch['num']}", (ch_x + ch_w // 2, ch_y + 15), ch["text"], subgroup_title_font)

        # Draw Backbone Line & Sub-groups
        curr_y = 400
        backbone_x = col_base_x + 20
        group_centers = []
        
        for g in ch["groups"]:
            bullets_count = len(g["bullets"])
            g_h = 28 + bullets_count * 20 + 6
            g_x = col_base_x + 45
            g_w = 270
            
            # Save group center y for vertical backbone connection
            g_center_y = curr_y + g_h // 2
            group_centers.append((g_center_y, g_h))
            
            # Draw Sub-group Card
            draw.rounded_rectangle([g_x, curr_y, g_x + g_w, curr_y + g_h], radius=6, fill=(255, 255, 255), outline=ch["stroke"], width=1)
            # Header block for subgroup title
            draw.rectangle([g_x, curr_y, g_x + g_w, curr_y + 26], fill=ch["fill"])
            draw.line([g_x, curr_y + 26, g_x + g_w, curr_y + 26], fill=ch["stroke"], width=1)
            draw.text((g_x + 10, curr_y + 4), g["title"], fill=ch["text"], font=subgroup_title_font)

            # Draw Bullets
            by = curr_y + 32
            for bullet in g["bullets"]:
                draw.text((g_x + 10, by), bullet, fill=(71, 85, 105), font=bullet_font)
                by += 20
                
            # Horizontal connection from backbone to sub-group left edge
            draw.line([(backbone_x, g_center_y), (g_x, g_center_y)], fill=ch["stroke"], width=2)
            
            curr_y += g_h + 20

        # Draw Backbone and connect it to the Chapter Card bottom-center
        if group_centers:
            last_g_center_y, last_g_h = group_centers[-1]
            # Connect bottom-center of chapter card to top-center of backbone helper
            draw.line([(ch_x + ch_w // 2, ch_y + ch_h), (ch_x + ch_w // 2, 375), (backbone_x, 375), (backbone_x, 400)], fill=ch["stroke"], width=2)
            # Vertical backbone line
            draw.line([(backbone_x, 375), (backbone_x, last_g_center_y)], fill=ch["stroke"], width=2)

    img.save(os.path.join(OUTPUT_DIR, "atlas_chapters_mindmap.png"), "PNG")
    print("Atlas chapters mindmap generated!")


def generate_data_chapters_mindmap():
    print("Generating data chapters mindmap...")
    # Clean top-down tree canvas (1800 width, 1200 height for 5 subgroups)
    img = Image.new("RGB", (1800, 1200), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype(FONT_BOLD_PATH, 24)
        subtitle_font_small = ImageFont.truetype(FONT_PATH, 16)
        subtitle_font = ImageFont.truetype(FONT_PATH, 18)
        chapter_title_font = ImageFont.truetype(FONT_BOLD_PATH, 20)
        subgroup_title_font = ImageFont.truetype(FONT_BOLD_PATH, 16)
        bullet_font = ImageFont.truetype(FONT_PATH, 14)
        section_title_font = ImageFont.truetype(FONT_BOLD_PATH, 24)
    except:
        title_font = subtitle_font = subtitle_font_small = chapter_title_font = subgroup_title_font = bullet_font = section_title_font = ImageFont.load_default()

    # Header
    draw.rectangle([0, 0, 1800, 80], fill=(240, 253, 244))
    draw.line([(0, 80), (1800, 80)], fill=(187, 247, 208), width=2)
    draw.text((40, 16), "城市更新智能推演平台", fill=(22, 101, 52), font=subtitle_font_small)
    draw.text((40, 40), "规划图册数据诊断板块分析图纸清单", fill=(20, 83, 45), font=title_font)
    draw.text((1420, 30), "1 大章节与 20 张现状诊断分析图纸", fill=(22, 101, 52), font=subtitle_font)

    # Helper function for vertical branch lines
    def draw_vertical_branch_line(draw_obj, start_pt, end_pt, color, line_w=2):
        mid_y = (start_pt[1] + end_pt[1]) // 2
        draw_obj.line([start_pt, (start_pt[0], mid_y), (end_pt[0], mid_y), end_pt], fill=color, width=line_w)

    # Colors
    ROOT_SCHEME = {"fill": (239, 246, 255), "stroke": (59, 130, 246), "text": (30, 58, 138)}
    
    CH = {
        "num": "02",
        "title": "02 数据诊断篇",
        "fill": (240, 253, 244), "stroke": (34, 197, 94), "text": (20, 83, 45),
        "groups": [
            {"title": "2.1 孪生框架 (P12-13)", "bullets": ["• P12 数字孪生技术框架", "• P13 多源现状数据来源"]},
            {"title": "2.2 用地与风貌 (P14-19)", "bullets": ["• P14 用地现状分析图", "• P15 AI诊断低效用地图", "• P16 现状建筑质量评估", "• P17 现状建筑层数高度", "• P18 CV建筑风貌识别图", "• P19 复合历史遗产分布"]},
            {"title": "2.3 交通与可达 (P20-23)", "bullets": ["• P20 道路交通现状图纸", "• P21 空间句法可达性分析", "• P22 公共交通服务覆盖", "• P23 慢行系统现状断点"]},
            {"title": "2.4 空间与热力 (P24-27)", "bullets": ["• P24 口袋空间现状分布", "• P25 生态绿地网络现状", "• P26 居民游客活动热力", "• P27 POI功能活力分析"]},
            {"title": "2.5 痛点汇总 (P28-31)", "bullets": ["• P28 社交情感语义分析", "• P29 老龄社区空间分布", "• P30 环境品质问题地图", "• P31 四大问题诊断总图"]}
        ]
    }

    # Coordinates for top-down root node
    root_x = 720
    root_y = 100
    root_w, root_h = 360, 90

    # Draw Root Node
    draw.rounded_rectangle([root_x, root_y - root_h // 2, root_x + root_w, root_y + root_h // 2], radius=10, fill=ROOT_SCHEME["fill"], outline=ROOT_SCHEME["stroke"], width=3)
    draw_centered_text(draw, CH["title"], (root_x + root_w // 2, root_y - 18), ROOT_SCHEME["text"], section_title_font)
    draw_centered_text(draw, "(5 大分析板块 / 20 张现状诊断图纸)", (root_x + root_w // 2, root_y + 20), (100, 116, 139), subtitle_font)

    # Layout chapters horizontally (centered)
    y_chapters = 260
    col_width_pitch = 340
    col_start_x = 80

    for i, g in enumerate(CH["groups"]):
        col_base_x = col_start_x + i * col_width_pitch
        
        # Subgroup card dimensions (perfect alignment)
        ch_x = col_base_x
        ch_y = y_chapters
        ch_w = 280
        ch_h = 80
        
        # Connection: Root -> Chapter Card top-center
        draw_vertical_branch_line(draw, (root_x + root_w // 2, root_y + root_h // 2), (ch_x + ch_w // 2, ch_y), color=(148, 163, 184), line_w=2)

        # Draw Group Card Header
        draw.rounded_rectangle([ch_x, ch_y, ch_x + ch_w, ch_y + ch_h], radius=8, fill=(255, 255, 255), outline=CH["stroke"], width=2)
        # Header bar in Group Card
        draw.rectangle([ch_x, ch_y, ch_x + ch_w, ch_y + 30], fill=CH["fill"])
        draw.line([ch_x, ch_y + 30, ch_x + ch_w, ch_y + 30], fill=CH["stroke"], width=1)
        # Group Title text
        draw_centered_text(draw, g["title"], (ch_x + ch_w // 2, ch_y + 55), CH["text"], chapter_title_font)
        draw_centered_text(draw, f"Section 2.{i+1}", (ch_x + ch_w // 2, ch_y + 15), CH["text"], subgroup_title_font)

        # Draw Bullets Card Container
        curr_y = 390
        bullets_count = len(g["bullets"])
        g_h = bullets_count * 24 + 18
        g_x = col_base_x
        g_w = 280
        
        # Draw Bullet Container Card
        draw.rounded_rectangle([g_x, curr_y, g_x + g_w, curr_y + g_h], radius=6, fill=(255, 255, 255), outline=CH["stroke"], width=1)
        
        # Draw Bullets
        by = curr_y + 12
        for bullet in g["bullets"]:
            draw.text((g_x + 15, by), bullet, fill=(71, 85, 105), font=bullet_font)
            by += 24
            
        # Draw straight vertical connection line from Chapter Card bottom-center to Bullet Card top-center
        draw.line([(ch_x + ch_w // 2, ch_y + ch_h), (ch_x + ch_w // 2, curr_y)], fill=CH["stroke"], width=2)

    img.save(os.path.join(OUTPUT_DIR, "data_chapters_mindmap.png"), "PNG")
    print("Data chapters mindmap generated!")


# -------------------------------------------------------------
# DIAGRAM 5: A3 Layout Template Preview (A3标准图纸排版与比例标注)
# -------------------------------------------------------------
def generate_a3_layout_preview():
    print("Generating A3 layout template preview...")
    SCALE = 2
    # High resolution canvas (originally 1200 x 960 scaled to 2440 x 2000 for safety padding)
    width = 1220 * SCALE
    height = 1000 * SCALE
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype(FONT_BOLD_PATH, int(28 * SCALE))
        node_title_font = ImageFont.truetype(FONT_BOLD_PATH, int(22 * SCALE))
        node_desc_font = ImageFont.truetype(FONT_PATH, int(16 * SCALE))
        subgroup_title_font = ImageFont.truetype(FONT_BOLD_PATH, int(18 * SCALE))
        section_title_font = ImageFont.truetype(FONT_BOLD_PATH, int(24 * SCALE))
        dimension_font = ImageFont.truetype(FONT_PATH, int(14 * SCALE))
        dimension_font_small = ImageFont.truetype(FONT_PATH, int(10 * SCALE))
        stamp_detail_font = ImageFont.truetype(FONT_PATH, int(12 * SCALE))
    except:
        title_font = node_title_font = node_desc_font = subgroup_title_font = section_title_font = dimension_font = dimension_font_small = stamp_detail_font = ImageFont.load_default()

    # Header
    draw.rectangle([0, 0, width, 60 * SCALE], fill=(241, 245, 249))
    draw.line([(0, 60 * SCALE), (width, 60 * SCALE)], fill=(203, 213, 225), width=2 * SCALE)
    draw.text((30 * SCALE, 15 * SCALE), "城市更新智能推演平台 —— A3 标准图纸排版与比例设计规范", fill=(15, 23, 42), font=title_font)

    # 1. Paper Edge Frame (A3 Standard: 420mm x 297mm)
    paper_x1 = 50 * SCALE
    paper_y1 = 130 * SCALE
    paper_w = 1120 * SCALE
    paper_h = 792 * SCALE  # Exactly 1.414 (√2) aspect ratio
    paper_x2, paper_y2 = paper_x1 + paper_w, paper_y1 + paper_h
    
    # Draw Paper Outer Frame
    draw.rectangle([paper_x1, paper_y1, paper_x2, paper_y2], outline=(148, 163, 184), fill=(255, 255, 255), width=2 * SCALE)
    
    # 2. Optimized Print Margin Border (Left=15mm for binding, Top/Right/Bottom=5mm)
    # Scaling factor: 1120px = 420mm -> 1mm = 2.667px.
    # Left binding edge = 15mm * 2.667px = 40px.
    # Other edges = 5mm * 2.667px = 13px.
    frame_x1 = paper_x1 + 40 * SCALE
    frame_y1 = paper_y1 + 13 * SCALE
    frame_x2 = paper_x2 - 13 * SCALE
    frame_y2 = paper_y2 - 13 * SCALE
    
    # Draw Thick Drawing Boundary Frame (黑线粗框)
    draw.rectangle([frame_x1, frame_y1, frame_x2, frame_y2], outline=(15, 23, 42), fill=None, width=3 * SCALE)

    # 3. Layout Partition Lines
    # Right column (Legend & Title Block column): width = 80mm -> 80 * 2.667px = 213px.
    col_w_px = 213 * SCALE
    div_x = frame_x2 - col_w_px
    
    # Vertical divider line
    draw.line([(div_x, frame_y1), (div_x, frame_y2)], fill=(15, 23, 42), width=2 * SCALE)
    
    # Main drawing area height = 257mm -> 257 * 2.667px = 686px.
    main_h_px = 686 * SCALE
    div_y = frame_y1 + main_h_px
    
    # Horizontal divider line (Left side)
    draw.line([(frame_x1, div_y), (div_x, div_y)], fill=(15, 23, 42), width=2 * SCALE)
    
    # 4. Fill and Annotate Left Main Drawing Area
    main_box = [frame_x1 + 2 * SCALE, frame_y1 + 2 * SCALE, div_x - 2 * SCALE, div_y - 2 * SCALE]
    draw.rectangle(main_box, fill=(240, 246, 255))
    draw_centered_text(draw, "主绘图区 (Main Drawing Zone)", ( (frame_x1 + div_x) // 2, frame_y1 + 180 * SCALE ), (30, 58, 138), section_title_font)
    draw_centered_text(draw, "规划现状分析、GIS病理诊断热力图、AIGC方案推演对比、三维鸟瞰透视", ( (frame_x1 + div_x) // 2, frame_y1 + 240 * SCALE ), (71, 85, 105), subgroup_title_font)
    
    # Metrics
    metrics_text = [
        "• 物理图面尺寸: 285 mm × 257 mm",
        "• 打印占比: 80.3% 宽 × 89.5% 高 (在图纸边界框内)",
        "• 推荐出图比例: 1:500 或 1:1000 自适应"
    ]
    for idx, txt in enumerate(metrics_text):
        draw.text((frame_x1 + 80 * SCALE, frame_y1 + 320 * SCALE + idx * 30 * SCALE), txt, fill=(30, 58, 138), font=subgroup_title_font)

    # 5. Fill and Annotate Left Planning Notes Area
    notes_box = [frame_x1 + 2 * SCALE, div_y + 2 * SCALE, div_x - 2 * SCALE, frame_y2 - 2 * SCALE]
    draw.rectangle(notes_box, fill=(248, 250, 252))
    draw_centered_text(draw, "规划说明与指标专栏 (Notes & Key Indicators)", ( (frame_x1 + div_x) // 2, div_y + 22 * SCALE ), (51, 65, 85), subgroup_title_font)
    # Split the long note description text into two lines to avoid clipping
    note_desc_line1 = "物理尺寸: 285 mm × 30 mm  [图面占比: 80.0% 宽 × 10.1% 高]"
    note_desc_line2 = "容纳：规划设计说明、核心指标表、上位政策对标依据"
    draw_centered_text(draw, note_desc_line1, ( (frame_x1 + div_x) // 2, div_y + 44 * SCALE ), (100, 116, 139), stamp_detail_font)
    draw_centered_text(draw, note_desc_line2, ( (frame_x1 + div_x) // 2, div_y + 64 * SCALE ), (100, 116, 139), stamp_detail_font)

    # 6. Fill and Annotate Right Column
    # Divide right column horizontally
    # North Arrow / Scale height = 60mm -> 60 * 2.667px = 160px.
    arrow_y = frame_y1 + 160 * SCALE
    draw.line([(div_x, arrow_y), (frame_x2, arrow_y)], fill=(15, 23, 42), width=2 * SCALE)
    
    # Project Title Block (Stamp) height = 80mm -> 80 * 2.667px = 213px.
    stamp_y = frame_y2 - 213 * SCALE
    draw.line([(div_x, stamp_y), (frame_x2, stamp_y)], fill=(15, 23, 42), width=2 * SCALE)
    
    # 6.1 North Arrow area
    # Draw North Arrow
    cx_arrow = div_x + col_w_px // 2
    cy_arrow = frame_y1 + 80 * SCALE
    draw.ellipse([cx_arrow - 30 * SCALE, cy_arrow - 30 * SCALE, cx_arrow + 30 * SCALE, cy_arrow + 30 * SCALE], outline=(15, 23, 42), width=2 * SCALE)
    draw.line([(cx_arrow, cy_arrow - 40 * SCALE), (cx_arrow, cy_arrow + 40 * SCALE)], fill=(239, 68, 68), width=2 * SCALE)
    draw_centered_text(draw, "N", (cx_arrow, cy_arrow - 50 * SCALE), (239, 68, 68), subgroup_title_font)
    draw_centered_text(draw, "指北针与比例尺 (60 mm高)", (cx_arrow, cy_arrow + 55 * SCALE), (71, 85, 105), stamp_detail_font)
    
    # 6.2 Legend area (137mm height)
    lg_box = [div_x + 2 * SCALE, arrow_y + 2 * SCALE, frame_x2 - 2 * SCALE, stamp_y - 2 * SCALE]
    draw.rectangle(lg_box, fill=(255, 255, 255))
    draw_centered_text(draw, "图例专栏 (Legend)", (div_x + col_w_px // 2, arrow_y + 30 * SCALE), (15, 23, 42), subgroup_title_font)
    draw_centered_text(draw, "尺寸: 80 × 137 mm", (div_x + col_w_px // 2, arrow_y + 55 * SCALE), (100, 116, 139), stamp_detail_font)
    
    # Draw sample legend blocks
    draw.rectangle([div_x + 20 * SCALE, arrow_y + 90 * SCALE, div_x + 50 * SCALE, arrow_y + 110 * SCALE], fill=(59, 130, 246))
    draw.text((div_x + 60 * SCALE, arrow_y + 90 * SCALE), "历史保留保护建筑", fill=(71, 85, 105), font=stamp_detail_font)
    draw.rectangle([div_x + 20 * SCALE, arrow_y + 130 * SCALE, div_x + 50 * SCALE, arrow_y + 150 * SCALE], fill=(245, 158, 11))
    draw.text((div_x + 60 * SCALE, arrow_y + 130 * SCALE), "中车低效工业置换区", fill=(71, 85, 105), font=stamp_detail_font)
    draw.rectangle([div_x + 20 * SCALE, arrow_y + 170 * SCALE, div_x + 50 * SCALE, arrow_y + 190 * SCALE], fill=(34, 197, 94))
    draw.text((div_x + 60 * SCALE, arrow_y + 170 * SCALE), "新增适老口袋绿化", fill=(71, 85, 105), font=stamp_detail_font)

    # 6.3 Title Block (80mm height)
    stamp_box = [div_x + 2 * SCALE, stamp_y + 2 * SCALE, frame_x2 - 2 * SCALE, frame_y2 - 2 * SCALE]
    draw.rectangle(stamp_box, fill=(241, 245, 249))
    draw_centered_text(draw, "标准图签栏 (Title Block)", (div_x + col_w_px // 2, stamp_y + 25 * SCALE), (15, 23, 42), subgroup_title_font)
    draw_centered_text(draw, "尺寸: 80 × 80 mm", (div_x + col_w_px // 2, stamp_y + 50 * SCALE), (100, 116, 139), stamp_detail_font)
    
    # Lines inside Title block
    draw.line([(div_x, stamp_y + 70 * SCALE), (frame_x2, stamp_y + 70 * SCALE)], fill=(203, 213, 225), width=1 * SCALE)
    draw.text((div_x + 15 * SCALE, stamp_y + 85 * SCALE), "项目: 伪满皇宫周边更新规划", fill=(15, 23, 42), font=stamp_detail_font)
    draw.text((div_x + 15 * SCALE, stamp_y + 120 * SCALE), "图纸: 重点地块C06-03平面", fill=(15, 23, 42), font=stamp_detail_font)
    # Split the unit/organization name to prevent overflow clipping
    draw.text((div_x + 15 * SCALE, stamp_y + 155 * SCALE), "单位: ultimateDESIGN", fill=(15, 23, 42), font=stamp_detail_font)
    draw.text((div_x + 50 * SCALE, stamp_y + 182 * SCALE), "联合设计工作组", fill=(15, 23, 42), font=stamp_detail_font)

    # 7. Helper Dimension Labels & Lines (mm scale)
    # A3 width dimension line at the top
    draw.line([(paper_x1, paper_y1 - 25 * SCALE), (paper_x2, paper_y1 - 25 * SCALE)], fill=(100, 116, 139), width=1 * SCALE)
    draw.line([(paper_x1, paper_y1 - 30 * SCALE), (paper_x1, paper_y1 - 20 * SCALE)], fill=(100, 116, 139), width=1 * SCALE)
    draw.line([(paper_x2, paper_y1 - 30 * SCALE), (paper_x2, paper_y1 - 20 * SCALE)], fill=(100, 116, 139), width=1 * SCALE)
    draw_centered_text(draw, "A3 纸张标准总宽度: 420 mm (100%)", ( (paper_x1 + paper_x2) // 2, paper_y1 - 40 * SCALE ), (100, 116, 139), dimension_font)

    # Left bind margin annotation
    draw.line([(paper_x1, paper_y2 + 25 * SCALE), (frame_x1, paper_y2 + 25 * SCALE)], fill=(100, 116, 139), width=1 * SCALE)
    draw.line([(paper_x1, paper_y2 + 20 * SCALE), (paper_x1, paper_y2 + 30 * SCALE)], fill=(100, 116, 139), width=1 * SCALE)
    draw.line([(frame_x1, paper_y2 + 20 * SCALE), (frame_x1, paper_y2 + 30 * SCALE)], fill=(100, 116, 139), width=1 * SCALE)
    # Split label vertically to prevent text overlapping and clipping
    draw_centered_text(draw, "装订边", ( (paper_x1 + frame_x1) // 2, paper_y2 + 40 * SCALE ), (100, 116, 139), dimension_font_small)
    draw_centered_text(draw, "15mm", ( (paper_x1 + frame_x1) // 2, paper_y2 + 53 * SCALE ), (100, 116, 139), dimension_font_small)

    # Main Drawing Width annotation
    draw.line([(frame_x1, paper_y2 + 25 * SCALE), (div_x, paper_y2 + 25 * SCALE)], fill=(59, 130, 246), width=1 * SCALE)
    draw.line([(frame_x1, paper_y2 + 20 * SCALE), (frame_x1, paper_y2 + 30 * SCALE)], fill=(59, 130, 246), width=1 * SCALE)
    draw.line([(div_x, paper_y2 + 20 * SCALE), (div_x, paper_y2 + 30 * SCALE)], fill=(59, 130, 246), width=1 * SCALE)
    draw_centered_text(draw, "主绘图区宽度: 285 mm", ( (frame_x1 + div_x) // 2, paper_y2 + 40 * SCALE ), (59, 130, 246), dimension_font)

    # Right column Width annotation
    draw.line([(div_x, paper_y2 + 25 * SCALE), (frame_x2, paper_y2 + 25 * SCALE)], fill=(15, 23, 42), width=1 * SCALE)
    draw.line([(div_x, paper_y2 + 20 * SCALE), (div_x, paper_y2 + 30 * SCALE)], fill=(15, 23, 42), width=1 * SCALE)
    draw.line([(frame_x2, paper_y2 + 20 * SCALE), (frame_x2, paper_y2 + 30 * SCALE)], fill=(15, 23, 42), width=1 * SCALE)
    draw_centered_text(draw, "图签图例宽度: 80 mm", ( (div_x + frame_x2) // 2, paper_y2 + 40 * SCALE ), (15, 23, 42), dimension_font)

    # Right paper margin (5mm)
    draw.line([(frame_x2, paper_y2 + 25 * SCALE), (paper_x2, paper_y2 + 25 * SCALE)], fill=(100, 116, 139), width=1 * SCALE)
    draw.line([(frame_x2, paper_y2 + 20 * SCALE), (frame_x2, paper_y2 + 30 * SCALE)], fill=(100, 116, 139), width=1 * SCALE)
    draw.line([(paper_x2, paper_y2 + 20 * SCALE), (paper_x2, paper_y2 + 30 * SCALE)], fill=(100, 116, 139), width=1 * SCALE)
    draw_centered_text(draw, "5mm", ( (frame_x2 + paper_x2) // 2, paper_y2 + 40 * SCALE ), (100, 116, 139), dimension_font_small)

    # Paper height dimension line on the left
    draw.line([(15 * SCALE, paper_y1), (15 * SCALE, paper_y2)], fill=(100, 116, 139), width=1 * SCALE)
    draw.line([(10 * SCALE, paper_y1), (20 * SCALE, paper_y1)], fill=(100, 116, 139), width=1 * SCALE)
    draw.line([(10 * SCALE, paper_y2), (20 * SCALE, paper_y2)], fill=(100, 116, 139), width=1 * SCALE)
    # Draw vertical height text to cleanly fit inside the left margin
    h_text = "A3高度: 297mm"
    start_y_offset = - (len(h_text) // 2) * 15 * SCALE
    for i, char in enumerate(h_text):
        draw_centered_text(draw, char, ( (15 * SCALE + 50 * SCALE) // 2, (paper_y1 + paper_y2) // 2 + start_y_offset + i * 15 * SCALE ), (100, 116, 139), dimension_font_small)

    # Save the uncropped full template for use as a base in other scripts
    img.save(os.path.join(OUTPUT_DIR, "a3_layout_preview_full.png"), "PNG")
    
    # Save the cropped version for preview
    cropped_img = img.crop((paper_x1, paper_y1, paper_x2, paper_y2))
    cropped_img.save(os.path.join(OUTPUT_DIR, "a3_layout_preview.png"), "PNG")
    print("A3 layout template preview generated (cropped)!")

# -------------------------------------------------------------
# Run All Generators
# -------------------------------------------------------------
if __name__ == "__main__":
    generate_workflow_flowchart()
    generate_system_architecture_mindmap()
    generate_data_pipeline_mindmap()
    generate_atlas_chapters_mindmap()
    generate_data_chapters_mindmap()
    generate_a3_layout_preview()
    try:
        from tools.generate_urban_rural_planning import generate_urban_rural_planning_mindmap
        generate_urban_rural_planning_mindmap()
    except ImportError:
        try:
            from generate_urban_rural_planning import generate_urban_rural_planning_mindmap
            generate_urban_rural_planning_mindmap()
        except ImportError:
            print("Warning: Could not import and run generate_urban_rural_planning_mindmap")
    print("All diagrams generated successfully!")
