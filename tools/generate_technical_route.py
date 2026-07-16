import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

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
def draw_arrow(draw, start, end, color, width=2, scale=1.0):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = (dx**2 + dy**2)**0.5
    if length == 0:
        return
    ux = dx / length
    uy = dy / length
    
    arrow_tip = (end[0] - int(2 * scale) * ux, end[1] - int(2 * scale) * uy)
    draw.line([start, arrow_tip], fill=color, width=int(width * scale))
    
    arrow_len = int(10 * scale)
    arrow_width = int(6 * scale)
    p1 = (arrow_tip[0] - arrow_len * ux + arrow_width * uy, arrow_tip[1] - arrow_len * uy - arrow_width * ux)
    p2 = (arrow_tip[0] - arrow_len * ux - arrow_width * uy, arrow_tip[1] - arrow_len * uy + arrow_width * ux)
    draw.polygon([arrow_tip, p1, p2], fill=color)

def draw_card_node(draw, x0, y0, x1, y1, text, scheme, font, scale, is_category=False):
    # Outer Card box
    bg_color = scheme["fill"] if is_category else (255, 255, 255)
    outline_color = scheme["stroke"]
    text_color = scheme["text"] if is_category else (71, 85, 105)
    
    draw.rounded_rectangle([x0, y0, x1, y1], radius=int(6 * scale), fill=bg_color, outline=outline_color, width=int(2 * scale))
    
    # Text
    max_w = (x1 - x0) - int(20 * scale)
    wrapped_lines = wrap_text_to_lines(text, font, max_w)
    
    # Center text vertically
    line_h = int(22 * scale)
    total_h = len(wrapped_lines) * line_h
    start_y = y0 + ((y1 - y0) - total_h) // 2
    
    for i, line in enumerate(wrapped_lines):
        try:
            left, _top, right, _bottom = font.getbbox(line)
            w_line = right - left
        except AttributeError:
            w_line = font.getsize(line)[0]
        draw.text((x0 + ((x1 - x0) - w_line) // 2, start_y + i * line_h), line, fill=text_color, font=font)

def generate_technical_route_diagram():
    print("Generating technical route architecture diagram in 5K resolution (Separate Card version)...")
    base_w = 1920
    base_h = 1800
    scale = 5120.0 / base_w
    
    canvas_w = int(base_w * scale)
    canvas_h = int(base_h * scale)
    
    img = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype(FONT_BOLD_PATH, int(34 * scale))
        subtitle_font = ImageFont.truetype(FONT_PATH, int(16 * scale))
        layer_title_font = ImageFont.truetype(FONT_BOLD_PATH, int(22 * scale))
        node_title_font = ImageFont.truetype(FONT_BOLD_PATH, int(16 * scale))
        node_desc_font = ImageFont.truetype(FONT_PATH, int(14 * scale))
    except:
        title_font = subtitle_font = layer_title_font = node_title_font = node_desc_font = ImageFont.load_default()

    # Header Panel
    draw.rectangle([0, 0, canvas_w, int(80 * scale)], fill=(241, 245, 249))
    draw.line([(0, int(80 * scale)), (canvas_w, int(80 * scale))], fill=(203, 213, 225), width=int(2 * scale))
    draw.text((int(40 * scale), int(20 * scale)), "UltimateDESIGN 城市微更新智能决策支持平台 —— 技术路线全景图", fill=(15, 23, 42), font=title_font)
    draw.text((canvas_w - int(380 * scale), int(32 * scale)), "自下而上全链路技术架构", fill=(100, 116, 139), font=subtitle_font)

    # 4 Layers Configuration
    LAYERS = [
        {
            "index": 3,
            "title": "层级四：成果集成与交付层 (Output & Delivery Layer)",
            "y_center": int(220 * scale),
            "fill": (254, 243, 199), "stroke": (245, 158, 11), "text": (180, 83, 9),
            "cards": [
                {"title": "A3标准规划图册编译", "bullets": ["Pillow 后台三层图层拼装排版绘制管线", "指北针、比例尺、标准图例及图签封装", "多图框模板自适应切换与边框自动生成"]},
                {"title": "Data-to-Text规划指标绑定", "bullets": ["容积率(FAR)、建筑密度等指标后台计算", "大模型指标读取与设计说明生成策略自适应", "规划图表及条目说明在图签中实时锁定绑定"]},
                {"title": "多进程出图与一键生成", "bullets": ["Multiprocessing 多进程并行编译出图图册", "附件三 (Docx) 与附件四 (PPTX) 一键编译同步", "编译异常捕获与全数据流自动备份日志输出"]}
            ]
        },
        {
            "index": 2,
            "title": "层级三：策略决策与推演层 (Strategy & Reasoning Layer)",
            "y_center": int(600 * scale),
            "fill": (250, 245, 255), "stroke": (168, 85, 247), "text": (107, 33, 168),
            "cards": [
                {"title": "多智能体博弈决策沙盘", "bullets": ["居民、开发商、规划局三方智能体人设注入", "对话命中特定诉求词触发满意度效用演进", "多轮博弈收敛共识雷达图并输出决策策略"]},
                {"title": "国家及地方控规合规审查", "bullets": ["BGE 中文向量大模型提取政策知识库特征", "针对方案 FAR 与限高指标实时检索匹配条文", "自动越界检测与越红线一键违规红牌告警"]},
                {"title": "矢量-光栅-ControlNet AI绘图", "bullets": ["规划红线、路网中心线等GIS底板光栅化", "ControlNet 空间结构刚性约束与位置对齐", "Stable Diffusion 高质量规划意向草图生成"]}
            ]
        },
        {
            "index": 1,
            "title": "层级二：计算引擎与诊断层 (Computing & Diagnostics Layer)",
            "y_center": int(980 * scale),
            "fill": (240, 253, 244), "stroke": (13, 148, 136), "text": (15, 118, 110),
            "cards": [
                {"title": "高精度空间几何平面计算", "bullets": ["GeoPandas 空间叠加与 Shapely 缓冲平面分析", "EPSG:32652 高斯克吕格投影纠正平面偏差", "地块面积、建筑覆盖及绿地率精准空间度量"]},
                {"title": "老旧街区病理量化体检", "bullets": ["SegFormer 深度学习语义分割提取绿视率(GVI)", "411条 POI 精准搜寻半径核密度分析(KDE)", "AHP-MPI 空间潜力-需求-品质潜力分级排序"]},
                {"title": "网络拓扑与社会感知", "bullets": ["OSMnx/NetworkX 路网拓扑图论与空间句法", "全局整合度(Integration)与穿行度(Choice)评价", "微博情感大文本语义情感挖掘与痛点地图匹配"]}
            ]
        },
        {
            "index": 0,
            "title": "层级一：多源异构数据汇聚层 (Data Aggregation Layer)",
            "y_center": int(1360 * scale),
            "fill": (239, 246, 255), "stroke": (59, 130, 246), "text": (30, 58, 138),
            "cards": [
                {"title": "多源空间 GIS 矢量", "bullets": ["研究红线 Boundary_Scope.geojson", "现状建筑轮廓 Building_Footprints.geojson", "道路、铁轨及用地边界 GeoJSON 图层"]},
                {"title": "多元感知统计数据", "bullets": ["长春现状 POI 商业服务分类点数据 (CSV)", "实景街景 1,788 张 4方向现状调研照片", "GVI_Results_Analysis.csv 实测绿视率表"]},
                {"title": "政策文书与非结构化文本", "bullets": ["任务书设计约束规划说明 mission_text.txt", "城市更新地方政策法规库 rag_knowledge.json", "微博、小红书等现状居民社区诉求文本"]}
            ]
        }
    ]

    card_w = int(480 * scale)
    card_h = int(50 * scale)
    card_pitch_x = int(540 * scale)
    start_x = int(960 * scale) - card_pitch_x

    # Draw Layer Groups & Cards
    for l in LAYERS:
        yc = l["y_center"]
        # Draw Layer Header Banner background (starts at 150, ends at 1770)
        draw.rounded_rectangle([int(150 * scale), yc - int(100 * scale), int(1770 * scale), yc - int(60 * scale)], radius=int(4 * scale), fill=l["fill"], outline=l["stroke"], width=1)
        draw.text((int(170 * scale), yc - int(94 * scale)), l["title"], fill=l["text"], font=layer_title_font)
        
        # Draw the 3 Categories and their Sub-Cards
        for idx, card in enumerate(l["cards"]):
            cx = start_x + idx * card_pitch_x
            
            # Category Title Card
            cat_x0 = cx - card_w // 2
            cat_y0 = yc - int(40 * scale)
            cat_x1 = cx + card_w // 2
            cat_y1 = yc + int(10 * scale)
            draw_card_node(draw, cat_x0, cat_y0, cat_x1, cat_y1, card["title"], l, node_title_font, scale, is_category=True)
            
            # Sub-Cards
            sub_y_starts = [yc + int(30 * scale), yc + int(100 * scale), yc + int(170 * scale)]
            sub_y_ends = [yc + int(80 * scale), yc + int(150 * scale), yc + int(220 * scale)]
            
            # Connect Category to Sub-card 1
            draw_arrow(draw, (cx, cat_y1), (cx, sub_y_starts[0]), l["stroke"], 2, scale)
            
            for s_idx, bullet in enumerate(card["bullets"]):
                sub_x0 = cx - card_w // 2
                sub_y0 = sub_y_starts[s_idx]
                sub_x1 = cx + card_w // 2
                sub_y1 = sub_y_ends[s_idx]
                
                # Draw the individual sub-card
                draw_card_node(draw, sub_x0, sub_y0, sub_x1, sub_y1, bullet, l, node_desc_font, scale, is_category=False)
                
                # Connect Sub-card s_idx to Sub-card s_idx+1
                if s_idx < len(card["bullets"]) - 1:
                    draw_arrow(draw, (cx, sub_y1), (cx, sub_y_starts[s_idx + 1]), l["stroke"], 2, scale)

    # 3. Draw vertical backbone arrows representing data flow (upwards)
    draw_arrow(draw, (int(960 * scale), int(1220 * scale)), (int(960 * scale), int(1040 * scale)), color=(148, 163, 184), width=3, scale=scale)
    draw_arrow(draw, (int(960 * scale), int(840 * scale)), (int(960 * scale), int(660 * scale)), color=(148, 163, 184), width=3, scale=scale)
    draw_arrow(draw, (int(960 * scale), int(460 * scale)), (int(960 * scale), int(280 * scale)), color=(148, 163, 184), width=3, scale=scale)

    # Stylish vertical flow indicator at the left and right margins (shifted slightly to margins)
    # Left flow
    draw_arrow(draw, (int(75 * scale), int(1600 * scale)), (int(75 * scale), int(120 * scale)), color=(100, 116, 139), width=4, scale=scale)
    # Right flow
    draw_arrow(draw, (int(1845 * scale), int(1600 * scale)), (int(1845 * scale), int(120 * scale)), color=(100, 116, 139), width=4, scale=scale)
    
    # Text along the arrows (placed on the sides so they never overlap banners)
    draw.text((int(20 * scale), int(830 * scale)), "数据流向\n(Data Flow Upward)", fill=(100, 116, 139), font=node_title_font)
    draw.text((int(1785 * scale), int(830 * scale)), "数据流向\n(Data Flow Upward)", fill=(100, 116, 139), font=node_title_font)

    # Legend at the bottom
    legend_y = int(1700 * scale)
    draw.text((int(140 * scale), legend_y), "系统总体设计路线：多源数据输入 ──> 诊断计算引擎 ──> 智能博弈推演 ──> Pillow 标准图册排版交付", fill=(100, 116, 139), font=subtitle_font)

    # Save outputs
    dest_path1 = os.path.join(OUTPUT_DIR, "technical_route_mindmap.png")
    dest_path2 = os.path.join(OUTPUT_DIR, "technical_route_diagram.png")
    img.save(dest_path1, "PNG")
    img.save(dest_path2, "PNG")
    print(f"Technical route architecture diagram generated successfully at:\n  {dest_path1}\n  {dest_path2}")

if __name__ == "__main__":
    generate_technical_route_diagram()
