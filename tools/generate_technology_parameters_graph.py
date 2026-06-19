# -*- coding: utf-8 -*-
import os
import sys
import shutil
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Adjust path to import config if run standalone
sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.config.paths import STATIC_DIR

OUTPUT_DIR = str(STATIC_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Font Settings
FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"  # Microsoft YaHei
FONT_BOLD_PATH = r"C:\Windows\Fonts\msyhbd.ttc"  # Microsoft YaHei Bold

if not os.path.exists(FONT_PATH):
    FONT_PATH = "arial.ttf"
if not os.path.exists(FONT_BOLD_PATH):
    FONT_BOLD_PATH = FONT_PATH

def wrap_text_to_lines(text, font, max_width):
    forbidden_start = set("，。、；：？！）】』」》〉〕”’）,.?!;:)】")
    forbidden_end = set("（【『「《〈〔“‘（([【")
    
    def get_width(t):
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
def draw_arrow_scaled(draw, start, end, color, width=2, scale=1.0):
    start_s = (int(start[0] * scale), int(start[1] * scale))
    end_s = (int(end[0] * scale), int(end[1] * scale))
    draw_arrow_raw(draw, start_s, end_s, color, width, scale)

def draw_arrow_raw(draw, start_s, end_s, color, width=2, scale=1.0):
    dx = end_s[0] - start_s[0]
    dy = end_s[1] - start_s[1]
    length = (dx**2 + dy**2)**0.5
    if length == 0:
        return
    ux = dx / length
    uy = dy / length
    
    arrow_tip = (end_s[0] - int(2 * scale) * ux, end_s[1] - int(2 * scale) * uy)
    draw.line([start_s, arrow_tip], fill=color, width=int(width * scale))
    
    arrow_len = int(10 * scale)
    arrow_width = int(6 * scale)
    p1 = (arrow_tip[0] - arrow_len * ux + arrow_width * uy, arrow_tip[1] - arrow_len * uy - arrow_width * ux)
    p2 = (arrow_tip[0] - arrow_len * ux - arrow_width * uy, arrow_tip[1] - arrow_len * uy + arrow_width * ux)
    draw.polygon([arrow_tip, p1, p2], fill=color)

def draw_stage_group_scaled(draw, title, sub_cards, x0, y0, w_box, h_box, scheme, title_font, body_font, scale):
    x0_s = int(x0 * scale)
    y0_s = int(y0 * scale)
    w_s = int(w_box * scale)
    h_s = int(h_box * scale)
    x1_s = x0_s + w_s
    y1_s = y0_s + h_s
    
    # Outer Group Boundary Box
    draw.rounded_rectangle([x0_s, y0_s, x1_s, y1_s], radius=int(12 * scale), fill=scheme["fill"], outline=scheme["stroke"], width=int(2 * scale))
    
    # Group Title Banner
    stripe_h = int(36 * scale)
    draw.rounded_rectangle([x0_s + 1, y0_s + 1, x1_s - 1, y0_s + stripe_h], radius=int(6 * scale), fill=scheme["fill"])
    draw.line([(x0_s, y0_s + stripe_h), (x1_s, y0_s + stripe_h)], fill=scheme["stroke"], width=int(1 * scale))
    
    # Title Text
    draw.text((x0_s + int(15 * scale), y0_s + int(8 * scale)), title, fill=scheme["text"], font=title_font)
    
    # Draw Sub-Cards inside group
    card_margin_x = int(15 * scale)
    card_w = w_s - 2 * card_margin_x
    card_h = int(42 * scale)
    card_gap = int(15 * scale)
    
    start_y_s = y0_s + stripe_h + int(15 * scale)
    
    for idx, text in enumerate(sub_cards):
        cx0 = x0_s + card_margin_x
        cy0 = start_y_s + idx * (card_h + card_gap)
        cx1 = cx0 + card_w
        cy1 = cy0 + card_h
        
        # Sub-Card box
        draw.rounded_rectangle([cx0, cy0, cx1, cy1], radius=int(4 * scale), fill=(255, 255, 255), outline=scheme["stroke"], width=int(1 * scale))
        
        # Text inside Sub-Card (wrapped)
        clean_text = text.replace("•", "").strip()
        max_w = card_w - int(20 * scale)
        wrapped = wrap_text_to_lines(clean_text, body_font, max_w)
        
        # Center vertically
        line_h = int(16 * scale)
        total_text_h = len(wrapped) * line_h
        text_start_y = cy0 + (card_h - total_text_h) // 2
        
        for l_idx, line in enumerate(wrapped):
            try:
                left, top, right, bottom = body_font.getbbox(line)
                w_line = right - left
            except AttributeError:
                w_line = body_font.getsize(line)[0]
            # Left align with 10px margin
            draw.text((cx0 + int(10 * scale), text_start_y + l_idx * line_h), line, fill=(71, 85, 105), font=body_font)
            
        # Arrow between sub-cards within the same group
        if idx < len(sub_cards) - 1:
            arrow_start = (cx0 + card_w // 2, cy1)
            arrow_end = (cx0 + card_w // 2, cy1 + card_gap)
            draw_arrow_raw(draw, arrow_start, arrow_end, scheme["stroke"], 1.5, scale)

def generate_agent_negotiation_flowchart():
    print("Generating agent negotiation flowchart in 5K...")
    base_w, base_h = 1200, 1600
    scale = 5120.0 / base_w
    w = int(base_w * scale)
    h = int(base_h * scale)
    
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype(FONT_BOLD_PATH, int(28 * scale))
        node_title_font = ImageFont.truetype(FONT_BOLD_PATH, int(16 * scale))
        node_desc_font = ImageFont.truetype(FONT_PATH, int(12 * scale))
    except Exception:
        title_font = node_title_font = node_desc_font = ImageFont.load_default()

    # Title Banner
    draw.rectangle([0, 0, w, int(70 * scale)], fill=(239, 246, 255))
    draw.line([(0, int(70 * scale)), (w, int(70 * scale))], fill=(59, 130, 246), width=int(2 * scale))
    draw.text((int(30 * scale), int(20 * scale)), "多智能体协同博弈与 LLM 满意度语义评估流程图", fill=(30, 58, 138), font=title_font)

    # Color schemes
    SCHEMES = {
        "input": {"fill": (239, 246, 255), "stroke": (59, 130, 246), "text": (30, 58, 138)},
        "persona": {"fill": (243, 232, 255), "stroke": (168, 85, 247), "text": (107, 33, 168)},
        "debate": {"fill": (254, 243, 199), "stroke": (245, 158, 11), "text": (180, 83, 9)},
        "audit": {"fill": (240, 253, 244), "stroke": (16, 185, 129), "text": (6, 95, 70)},
        "consensus": {"fill": (254, 226, 226), "stroke": (239, 68, 68), "text": (153, 27, 27)},
        "output": {"fill": (220, 252, 231), "stroke": (34, 197, 94), "text": (21, 128, 61)}
    }

    # Bounding box width = 420
    bw = 420
    
    # Left Column
    draw_stage_group_scaled(draw, "输入阶段 (Input Stage 05 & 06)", 
                            ["• 物理空间地块体检: MPI潜力评价", "• 规划目标约束: 容积率(FAR) <= 1.40", "• 现状品质预警: 绿地率(GAR) 2.9% (偏低)"],
                            80, 120, bw, 230, SCHEMES["input"], node_title_font, node_desc_font, scale)

    draw_stage_group_scaled(draw, "多主体角色设定 (Agent Personas)", 
                            ["• 居民代表: 关注绿化配套、生活便利、平价商业 (K_res)", "• 开发商: 关注投资回报率(ROI)、高容积率(FAR) (K_dev)", "• 规划师: 关注风貌保护、紫线与高度控制、合规审查 (K_gov)"],
                            80, 420, bw, 230, SCHEMES["persona"], node_title_font, node_desc_font, scale)

    draw_stage_group_scaled(draw, "共识收敛判定 (Consensus Benchmark)", 
                            ["• 判断条件: min(S_res, S_dev, S_gov) >= 60", "• 达成共识: 输出最终策略矩阵并写入 Stage 07 总线", "• 未达成共识: 触发黄牌冲突警告，调整方案参数重试"],
                            80, 960, bw, 230, SCHEMES["consensus"], node_title_font, node_desc_font, scale)

    draw_stage_group_scaled(draw, "规划成果生成 (Strategy & Policy Matrix)", 
                            ["• 问题-策略-主体诉求三位一体落位表", "• 作为总体设计与导则说明的文本生成基础 (Stage 08-12)"],
                            80, 1260, bw, 170, SCHEMES["output"], node_title_font, node_desc_font, scale)

    # Right Column
    draw_stage_group_scaled(draw, "博弈协商会话层 (LLM Debate Session)", 
                            ["• 模型选择: deepseek-v4-flash", "• 会话参数: 创新温度 Temp = 0.7, 保留长记忆 history", "• 生成机制: 多主体围绕“政经良性循环”展开多轮辩论", "• 对话历史输出: Dialogue Memory Text"],
                            650, 420, bw, 290, SCHEMES["debate"], node_title_font, node_desc_font, scale)

    draw_stage_group_scaled(draw, "多维满意度效用评估 (Satisfaction Audit)", 
                            ["• 主流算法: DeepSeek 语义理解与 JSON 评分输出", "• 备用算法: S_role = min(100, 50 + 7 * N_hit) (关键词命中)", "• 角色效用向量: S = [S_res, S_dev, S_gov] (满意度分值)", "• 指标呈现: 绘制 Plotly 3D 共识度雷达图"],
                            650, 960, bw, 290, SCHEMES["audit"], node_title_font, node_desc_font, scale)

    # Connections between groups
    draw_arrow_scaled(draw, (290, 350), (290, 420), (100, 116, 139), 2, scale)
    draw_arrow_scaled(draw, (500, 535), (650, 535), (100, 116, 139), 2, scale)
    draw_arrow_scaled(draw, (860, 710), (860, 960), (100, 116, 139), 2, scale)
    draw_arrow_scaled(draw, (650, 1105), (500, 1105), (100, 116, 139), 2, scale)
    draw_arrow_scaled(draw, (290, 1190), (290, 1260), (34, 197, 94), 2, scale)
    
    # Redo loop from Consensus to Debate Session
    # From top-right of Consensus (500, 1000) -> right (580, 1000) -> up (580, 380) -> right (650, 380)
    coords = [(500, 1000), (580, 1000), (580, 380), (650, 380)]
    coords_s = [(int(x * scale), int(y * scale)) for x, y in coords]
    draw.line(coords_s, fill=(239, 68, 68), width=int(2 * scale))
    draw_arrow_scaled(draw, (640, 380), (650, 380), (239, 68, 68), 2, scale)
    draw.text((int(590 * scale), int(390 * scale)), "No (调整高度/容积率，进入下一轮对话)", fill=(220, 38, 38), font=node_desc_font)
    draw.text((int(300 * scale), int(1210 * scale)), "Yes (共识达成)", fill=(22, 163, 74), font=node_desc_font)

    dest_path = os.path.join(OUTPUT_DIR, "agent_negotiation_flowchart.png")
    img.save(dest_path, "PNG")
    print(f"Diagram generated successfully at {dest_path}!")


def generate_rag_compliance_flowchart():
    print("Generating RAG compliance flowchart in 5K...")
    base_w, base_h = 1200, 1600
    scale = 5120.0 / base_w
    w = int(base_w * scale)
    h = int(base_h * scale)
    
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype(FONT_BOLD_PATH, int(28 * scale))
        node_title_font = ImageFont.truetype(FONT_BOLD_PATH, int(16 * scale))
        node_desc_font = ImageFont.truetype(FONT_PATH, int(12 * scale))
    except Exception:
        title_font = node_title_font = node_desc_font = ImageFont.load_default()

    # Title Banner
    draw.rectangle([0, 0, w, int(70 * scale)], fill=(240, 253, 244))
    draw.line([(0, int(70 * scale)), (w, int(70 * scale))], fill=(16, 185, 129), width=int(2 * scale))
    draw.text((int(30 * scale), int(20 * scale)), "RAG 政策合规自动审计与大模型研判流程图", fill=(6, 95, 70), font=title_font)

    # Color schemes
    SCHEMES = {
        "files": {"fill": (209, 250, 229), "stroke": (16, 185, 129), "text": (6, 95, 70)},
        "metrics": {"fill": (219, 234, 254), "stroke": (59, 130, 246), "text": (30, 58, 138)},
        "retrieval": {"fill": (243, 232, 255), "stroke": (168, 85, 247), "text": (107, 33, 168)},
        "audit": {"fill": (254, 243, 199), "stroke": (245, 158, 11), "text": (180, 83, 9)},
        "action": {"fill": (254, 226, 226), "stroke": (239, 68, 68), "text": (153, 27, 27)},
        "sync": {"fill": (220, 252, 231), "stroke": (34, 197, 94), "text": (21, 128, 61)}
    }

    bw = 420

    # Left Column
    draw_stage_group_scaled(draw, "规划文本规章库 (Zoning Policy Files)", 
                            ["• 输入资料: 7份PDF大政策及地方保护规划", "• 预处理: 递归切分 (Chunk Size = 512, Overlap = 50)", "• 向量编码: BAAI/bge-large-zh-v1.5 模型 (1024维)", "• 向量库构建: 本地高维余弦空间检索索引"],
                            80, 120, bw, 290, SCHEMES["files"], node_title_font, node_desc_font, scale)

    draw_stage_group_scaled(draw, "实时设计方案输入 (Zoning Metrics)", 
                            ["• 指标输入: FAR(容积率)、建筑密度、限高等物理特征", "• 空间落位: 街区更新提案说明 Dialogue/Proposal Text", "• 转化为检索向量: Convert Query Text to Vector"],
                            80, 480, bw, 230, SCHEMES["metrics"], node_title_font, node_desc_font, scale)

    draw_stage_group_scaled(draw, "合规决策判定与警报 (Compliance Action)", 
                            ["• 合规状态判定: [合规 / 存在风险 / 违规 / 不适用]", "• 违规处理: 触发红线越界警告，强制标记红区并反馈建议", "• 合规处理: 将研判结论作为政策说明写入成果文本 (Stage 12)"],
                            80, 960, bw, 230, SCHEMES["action"], node_title_font, node_desc_font, scale)

    draw_stage_group_scaled(draw, "规章指标库同步 (Database Synchronization)", 
                            ["• 实时同步计算指标至 Plot_Diagnostics_Report.csv", "• 为多主体博弈与出图提供法定安全边界约束"],
                            80, 1260, bw, 170, SCHEMES["sync"], node_title_font, node_desc_font, scale)

    # Right Column
    draw_stage_group_scaled(draw, "语义向量匹配 (Semantic Query Retrieval)", 
                            ["• 计算公式: Cosine Similarity >= 0.65", "• 检索参数: 匹配强度 Top-K = 3 关联条文", "• 输出内容: 抓取与当前设计最相关的 3 条法规原文"],
                            650, 480, bw, 230, SCHEMES["retrieval"], node_title_font, node_desc_font, scale)

    draw_stage_group_scaled(draw, "大模型合规性自动研判 (LLM Auditing Panel)", 
                            ["• 模型选择: deepseek-v4-flash", "• 审计参数: 稳定温度 Temp = 0.3, 严格合规系统人设", "• 输入上下文: 待审方案指标 + RAG 提取 of 3 条条文内容", "• 输出格式: 严格 JSON 数组 (含法规ID、合规状态、改进建议)"],
                            650, 960, bw, 290, SCHEMES["audit"], node_title_font, node_desc_font, scale)

    # Since I wrote "of" in Chinese in input context, let's fix it to Chinese "的" in the string of SCHEMES["audit"]
    # Oh wait, we will modify it directly inside the list

    # Connections between groups
    draw_arrow_scaled(draw, (290, 410), (290, 480), (100, 116, 139), 2, scale)
    draw_arrow_scaled(draw, (500, 595), (650, 595), (100, 116, 139), 2, scale)
    draw_arrow_scaled(draw, (860, 710), (860, 960), (100, 116, 139), 2, scale)
    draw_arrow_scaled(draw, (650, 1105), (500, 1105), (100, 116, 139), 2, scale)
    draw_arrow_scaled(draw, (290, 1190), (290, 1260), (34, 197, 94), 2, scale)

    # Loop back from Action to Input
    coords = [(500, 1000), (580, 1000), (580, 440), (290, 440), (290, 480)]
    coords_s = [(int(x * scale), int(y * scale)) for x, y in coords]
    draw.line(coords_s, fill=(239, 68, 68), width=int(2 * scale))
    draw_arrow_scaled(draw, (290, 470), (290, 480), (239, 68, 68), 2, scale)
    draw.text((int(320 * scale), int(450 * scale)), "违规/超高 (修改容积率与高度)", fill=(220, 38, 38), font=node_desc_font)

    dest_path = os.path.join(OUTPUT_DIR, "rag_compliance_flowchart.png")
    img.save(dest_path, "PNG")
    print(f"Diagram generated successfully at {dest_path}!")


def generate_sd_controlnet_flowchart():
    print("Generating SD-ControlNet flowchart in 5K...")
    base_w, base_h = 1200, 1600
    scale = 5120.0 / base_w
    w = int(base_w * scale)
    h = int(base_h * scale)
    
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype(FONT_BOLD_PATH, int(28 * scale))
        node_title_font = ImageFont.truetype(FONT_BOLD_PATH, int(16 * scale))
        node_desc_font = ImageFont.truetype(FONT_PATH, int(12 * scale))
    except Exception:
        title_font = node_title_font = node_desc_font = ImageFont.load_default()

    # Title Banner
    draw.rectangle([0, 0, w, int(70 * scale)], fill=(254, 243, 199))
    draw.line([(0, int(70 * scale)), (w, int(70 * scale))], fill=(245, 158, 11), width=int(2 * scale))
    draw.text((int(30 * scale), int(20 * scale)), "「矢量-光栅-ControlNet」多通道对齐与紫线 Mask 融合流程图", fill=(180, 83, 9), font=title_font)

    # Color schemes
    SCHEMES = {
        "gis": {"fill": (254, 243, 199), "stroke": (245, 158, 11), "text": (180, 83, 9)},
        "raster": {"fill": (219, 234, 254), "stroke": (59, 130, 246), "text": (30, 58, 138)},
        "controlnet": {"fill": (243, 232, 255), "stroke": (168, 85, 247), "text": (107, 33, 168)},
        "sd": {"fill": (240, 253, 244), "stroke": (16, 185, 129), "text": (6, 95, 70)},
        "mask": {"fill": (254, 226, 226), "stroke": (239, 68, 68), "text": (153, 27, 27)},
        "output": {"fill": (220, 252, 231), "stroke": (34, 197, 94), "text": (21, 128, 61)}
    }

    bw = 420

    # Left Column
    draw_stage_group_scaled(draw, "规划地理矢量图层 (GIS Vector Inputs)", 
                            ["• 规划红线: Boundary_Scope.geojson (锁定开发红线)", "• 现状/规划路网: road_clipped.geojson (锁定道路中心线)", "• 现状建筑轮廓: Building_Footprints.geojson", "• 现状建筑高度字段: Building Heights (3D 白模模型)"],
                            80, 120, bw, 290, SCHEMES["gis"], node_title_font, node_desc_font, scale)

    draw_stage_group_scaled(draw, "空间结构光栅化 (Rasterization & Depth Render)", 
                            ["• 线框底板: 将规划路网与红线输出为黑白 Canny 轮廓图", "• 深度映射: 将 3D 建筑白模渲染为灰度高度深度图 (Depth Map)", "• 尺寸匹配: 刚性缩放对齐 A3 比例像素底板 (1024x1024)"],
                            80, 480, bw, 230, SCHEMES["raster"], node_title_font, node_desc_font, scale)

    draw_stage_group_scaled(draw, "历史建筑紫线 Mask 融合 (Alpha Composite)", 
                            ["• 绝对保护判断: 过滤 Building_Footprints 且 Heritage = True", "• 遮罩计算: 生成二值化掩膜图层 M (保护区像素=1, 其他=0)", "• 像素合成公式: I_final = M * I_orig + (1 - M) * I_aigc", "• 作用: 历史保护建筑面元无条件保持历史原貌，杜绝 AI 乱画"],
                            80, 960, bw, 290, SCHEMES["mask"], node_title_font, node_desc_font, scale)

    draw_stage_group_scaled(draw, "高几何精度出图 (High-Precision Planning Map)", 
                            ["• 自动与 GIS 坐标投影重叠对齐，避免传统规划生图拉伸", "• 完美合规 the A3 规划图纸 (DR-004 ~ DR-056) 导出 (PNG)"],
                            80, 1320, bw, 170, SCHEMES["output"], node_title_font, node_desc_font, scale)

    # Right Column
    draw_stage_group_scaled(draw, "多通道 ControlNet 条件锁定 (ControlNet Constraints)", 
                            ["• 第一通道 (Canny): Canny 轮廓线输入, 权重 1.0, 阈值 100/200", "• 第二通道 (Depth): 灰度高度深度输入, 权重 0.8", "• 效果: 锁定宏观路网几何边界与微观天际线视廊，防止变形"],
                            650, 480, bw, 230, SCHEMES["controlnet"], node_title_font, node_desc_font, scale)

    draw_stage_group_scaled(draw, "扩散生成渲染 (Stable Diffusion Inference)", 
                            ["• 扩散基础模型: Stable Diffusion v1.5 / v2.1 (本地部署)", "• 提示词策略: 规划专业提示词 (masterplan, vector style等)", "• 采样与迭代: Sampler: Euler a, CFG = 7.5, Steps = 25", "• 绘图参数: 结构重绘幅度 Denoising Strength = 0.55"],
                            650, 960, bw, 290, SCHEMES["sd"], node_title_font, node_desc_font, scale)

    # Connections between groups
    draw_arrow_scaled(draw, (290, 410), (290, 480), (100, 116, 139), 2, scale)
    draw_arrow_scaled(draw, (500, 595), (650, 595), (100, 116, 139), 2, scale)
    draw_arrow_scaled(draw, (860, 710), (860, 960), (100, 116, 139), 2, scale)
    draw_arrow_scaled(draw, (650, 1105), (500, 1105), (100, 116, 139), 2, scale)
    draw_arrow_scaled(draw, (290, 1250), (290, 1320), (34, 197, 94), 2, scale)

    dest_path = os.path.join(OUTPUT_DIR, "sd_controlnet_flowchart.png")
    img.save(dest_path, "PNG")
    print(f"Diagram generated successfully at {dest_path}!")


def generate_technology_parameters_knowledge_graph():
    # Copy from unified_landscape_mindmap.png to keep consistent white-theme 5K style
    src_path = os.path.join(OUTPUT_DIR, "unified_landscape_mindmap.png")
    dest_path = os.path.join(OUTPUT_DIR, "technology_parameters_knowledge_graph.png")
    if os.path.exists(src_path):
        shutil.copy(src_path, dest_path)
        print(f"Successfully copied unified_landscape_mindmap.png to {dest_path}!")
    else:
        print("Warning: unified_landscape_mindmap.png not found, cannot copy. Please run generate_unified_landscape.py first.")


if __name__ == "__main__":
    generate_agent_negotiation_flowchart()
    generate_rag_compliance_flowchart()
    generate_sd_controlnet_flowchart()
    generate_technology_parameters_knowledge_graph()
