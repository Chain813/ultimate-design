import os
import sys

from PIL import Image, ImageDraw, ImageFont

from src.config.paths import STATIC_DIR

# Define Output File
OUTPUT_DIR = str(STATIC_DIR)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "workflow_flowchart.png")

# Set up Font
FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"  # Microsoft YaHei
FONT_BOLD_PATH = r"C:\Windows\Fonts\msyhbd.ttc"  # Microsoft YaHei Bold

if not os.path.exists(FONT_PATH):
    FONT_PATH = "arial.ttf"
if not os.path.exists(FONT_BOLD_PATH):
    FONT_BOLD_PATH = FONT_PATH

# Sizes and Constants
IMG_WIDTH = 1920
IMG_HEIGHT = 1080
BG_COLOR = (248, 250, 252)  # Slate 50
TEXT_COLOR_DARK = (15, 23, 42)  # Slate 900
TEXT_COLOR_MUTED = (100, 116, 139)  # Slate 500
LINE_COLOR = (148, 163, 184)  # Slate 400

# Color Schemes for different columns
COLOR_SCHEMES = {
    "data": {"fill": (239, 246, 255), "stroke": (59, 130, 246), "text": (30, 58, 138), "desc": "数据底座与分析"},  # Blue
    "strategy": {"fill": (250, 245, 255), "stroke": (168, 85, 247), "text": (88, 28, 135), "desc": "智能决策与策略"},  # Purple
    "design": {"fill": (240, 253, 244), "stroke": (34, 197, 94), "text": (20, 83, 45), "desc": "空间规划与深化"},  # Green
    "output": {"fill": (254, 243, 199), "stroke": (245, 158, 11), "text": (120, 53, 4), "desc": "成果表达与交付"},  # Amber/Orange
    "tool": {"fill": (241, 245, 249), "stroke": (100, 116, 139), "text": (51, 65, 85), "desc": "共享辅助工具"}  # Gray
}

# Define Nodes
# Each node has: id, label, col (0-4), row (0-5), type
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

# Define Connections (Edges)
EDGES = [
    # Data gathering -> analysis
    ("S00", "S02", "direct"),
    ("S02", "S04", "direct"),
    ("S03", "S04", "direct"),
    
    # Analysis -> diagnosis
    ("S04", "S05", "direct"),
    
    # Task interpretation & Diagnosis -> strategy
    ("S01", "S06", "direct"),
    ("S05", "S06", "direct"),
    ("S05", "S07", "direct"),
    ("S06", "S07", "direct"),
    
    # Strategy -> overall design & implementation
    ("S07", "S08", "direct"),
    ("S07", "S11", "direct"),
    ("S07", "S12", "direct"),
    
    # Overall design -> special -> plot
    ("S08", "S09", "direct"),
    ("S09", "S10", "direct"),
    
    # Plot -> implementation & guideline
    ("S10", "S11", "direct"),
    ("S10", "S12", "direct"),
    ("S05", "S10", "direct"),  # Diagnosis selects key plots
    
    # Outputs
    ("S11", "S13", "direct"),
    ("S12", "S13", "direct"),
    ("S13", "S14", "direct"),
    
    # S15 tools serve S08, S10, S13
    ("S15", "S08", "tool"),
    ("S15", "S10", "tool"),
    ("S15", "S13", "tool")
]

# Grid Layout Calculation
COL_X = [120, 480, 840, 1200, 1560]
ROW_Y = [120, 260, 400, 540, 680, 820, 960]

def draw_arrow(draw, start, end, color, width=2, is_dashed=False):
    # Draw line
    draw.line([start, end], fill=color, width=width)
    
    # Draw arrow head
    # Calculate direction vector
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = (dx**2 + dy**2)**0.5
    if length == 0:
        return
    ux = dx / length
    uy = dy / length
    
    arrow_len = 10
    arrow_width = 6
    
    # Points for arrowhead triangle
    p1 = (end[0] - arrow_len * ux + arrow_width * uy, end[1] - arrow_len * uy - arrow_width * ux)
    p2 = (end[0] - arrow_len * ux - arrow_width * uy, end[1] - arrow_len * uy + arrow_width * ux)
    
    draw.polygon([end, p1, p2], fill=color)

def main():
    print("Creating canvas...")
    # Create Image
    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Fonts
    try:
        title_font = ImageFont.truetype(FONT_BOLD_PATH, 32)
        subtitle_font = ImageFont.truetype(FONT_PATH, 16)
        node_title_font = ImageFont.truetype(FONT_BOLD_PATH, 18)
        node_desc_font = ImageFont.truetype(FONT_PATH, 13)
        col_title_font = ImageFont.truetype(FONT_BOLD_PATH, 20)
    except Exception as e:
        print(f"Error loading fonts: {e}. Using default.")
        title_font = subtitle_font = node_title_font = node_desc_font = col_title_font = ImageFont.load_default()

    # Draw Background Headers & Grid Panels
    draw.rectangle([0, 0, IMG_WIDTH, 80], fill=(15, 23, 42))  # Dark header bar
    draw.text((40, 20), "城市更新智能推演平台 —— 全流程16阶段工作流", fill=(255, 255, 255), font=title_font)
    draw.text((1550, 32), "v2.5.0 精细重构版", fill=(148, 163, 184), font=subtitle_font)

    # Column Width & Height parameters
    card_w = 260
    card_h = 75
    
    # Draw Swimlane Backgrounds & Column Titles
    cols_meta = [
        {"type": "data", "title": "01. 数据底座与现状诊断"},
        {"type": "data", "title": "02. 空间现状量化分析"},
        {"type": "strategy", "title": "03. 智能多主体博弈决策"},
        {"type": "design", "title": "04. 总体与专项深化设计"},
        {"type": "output", "title": "05. 成果集成与智能交付"}
    ]
    
    for i, col_x in enumerate(COL_X):
        # Draw swimlane background
        draw.rectangle([col_x - 15, 100, col_x + card_w + 15, IMG_HEIGHT - 40], 
                       fill=(255, 255, 255), outline=(226, 232, 240), width=1)
        # Draw header bar for swimlane
        meta = cols_meta[i]
        scheme = COLOR_SCHEMES[meta["type"]]
        draw.rectangle([col_x - 15, 100, col_x + card_w + 15, 145], fill=scheme["fill"])
        draw.line([col_x - 15, 145, col_x + card_w + 15, 145], fill=scheme["stroke"], width=2)
        
        # Center the text in the column header
        title_text = meta["title"]
        draw.text((col_x + 10, 112), title_text, fill=scheme["text"], font=col_title_font)

    # Calculate Node Coordinates
    node_centers = {}
    for node_id, node in NODES.items():
        cx = COL_X[node["col"]] + card_w // 2
        
        # Row calculation
        row_idx = int(node["row"])
        frac = node["row"] - row_idx
        y_base = ROW_Y[row_idx]
        y_next = ROW_Y[row_idx + 1] if row_idx + 1 < len(ROW_Y) else y_base + 140
        cy = y_base + int((y_next - y_base) * frac) + 40
        
        node_centers[node_id] = (cx, cy)
        node["cx"] = cx
        node["cy"] = cy

    # Draw Connections
    for start_id, end_id, edge_type in EDGES:
        start_node = NODES[start_id]
        end_node = NODES[end_id]
        
        # Calculate ports
        # We draw clean routes
        # If start is left of end, start port is right, end port is left
        # If start is right of end, start port is left, end port is right
        # If same column, start port is bottom, end port is top
        start_x, start_y = start_node["cx"], start_node["cy"]
        end_x, end_y = end_node["cx"], end_node["cy"]
        
        if start_node["col"] < end_node["col"]:
            p_start = (start_x + card_w // 2, start_y)
            p_end = (end_x - card_w // 2, end_y)
        elif start_node["col"] > end_node["col"]:
            p_start = (start_x - card_w // 2, start_y)
            p_end = (end_x + card_w // 2, end_y)
        else:
            if start_y < end_y:
                p_start = (start_x, start_y + card_h // 2)
                p_end = (end_x, end_y - card_h // 2)
            else:
                p_start = (start_x, start_y - card_h // 2)
                p_end = (end_x, end_y + card_h // 2)
                
        # Draw connections
        color = LINE_COLOR
        width = 2
        if edge_type == "tool":
            color = (148, 163, 184)  # Slate 400
            width = 1
            # Draw curved or orthagonal dashed helper lines
            draw_arrow(draw, p_start, p_end, color=color, width=width, is_dashed=True)
        else:
            # Orthogonal or direct arrows
            # If columns are adjacent or same, draw direct arrow
            if abs(start_node["col"] - end_node["col"]) <= 1:
                draw_arrow(draw, p_start, p_end, color=(71, 85, 105), width=width)
            else:
                # Orthogonal routing for clarity
                mid_x = (p_start[0] + p_end[0]) // 2
                draw.line([p_start, (mid_x, p_start[1]), (mid_x, p_end[1]), p_end], fill=(100, 116, 139), width=width)
                draw_arrow(draw, (mid_x, p_end[1]), p_end, color=(71, 85, 105), width=width)

    # Draw Nodes
    for node_id, node in NODES.items():
        scheme = COLOR_SCHEMES[node["type"]]
        cx, cy = node["cx"], node["cy"]
        
        # Box coords
        x0 = cx - card_w // 2
        y0 = cy - card_h // 2
        x1 = cx + card_w // 2
        y1 = cy + card_h // 2
        
        # Draw node box (rounded rectangle)
        draw.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=scheme["fill"], outline=scheme["stroke"], width=2)
        
        # Draw status dot / stage code
        code_w = 42
        draw.rounded_rectangle([x0 + 10, y0 + 10, x0 + 10 + code_w, y0 + 30], radius=4, fill=scheme["stroke"])
        # Stage code text (S00, etc)
        draw.text((x0 + 15, y0 + 13), node_id, fill=(255, 255, 255), font=subtitle_font)
        
        # Node Title
        draw.text((x0 + 15 + code_w + 5, y0 + 12), node["name"].split(" ", 1)[1], fill=scheme["text"], font=node_title_font)
        
        # Node Description
        draw.text((x0 + 15, y0 + 44), node["desc"], fill=(71, 85, 105), font=node_desc_font)

    # Legend in the footer
    legend_y = IMG_HEIGHT - 30
    draw.text((40, legend_y), "图例分类: ", fill=TEXT_COLOR_DARK, font=node_title_font)
    
    offset_x = 150
    for _key, val in COLOR_SCHEMES.items():
        draw.rounded_rectangle([offset_x, legend_y - 2, offset_x + 20, legend_y + 12], radius=3, fill=val["fill"], outline=val["stroke"])
        draw.text((offset_x + 28, legend_y - 2), val["desc"], fill=TEXT_COLOR_DARK, font=subtitle_font)
        offset_x += 240

    # Save image
    print(f"Saving to {OUTPUT_FILE}...")
    img.save(OUTPUT_FILE, "PNG")
    print("Done!")

if __name__ == "__main__":
    main()
