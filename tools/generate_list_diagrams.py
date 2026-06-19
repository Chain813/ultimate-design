# -*- coding: utf-8 -*-
# tools/generate_list_diagrams.py
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ATLAS_DIR = ROOT / "static" / "atlas"
ATLAS_DIR.mkdir(parents=True, exist_ok=True)

# A3 print canvas (1.5x base for readability)
CANVAS_W, CANVAS_H = 3360, 2376

# Font Paths
FONT_PATH = 'C:/Windows/Fonts/msyh.ttc'
FONT_BOLD_PATH = 'C:/Windows/Fonts/msyhbd.ttc'
FONT_CODE_PATH = 'C:/Windows/Fonts/consola.ttf'

def load_fonts():
    try:
        fonts = {
            "large_title": ImageFont.truetype(FONT_BOLD_PATH, 48),
            "card_title": ImageFont.truetype(FONT_BOLD_PATH, 34),
            "box_header": ImageFont.truetype(FONT_BOLD_PATH, 34),
            "body": ImageFont.truetype(FONT_PATH, 24),
            "body_bold": ImageFont.truetype(FONT_BOLD_PATH, 28),
            "desc": ImageFont.truetype(FONT_PATH, 24),
            "code": ImageFont.truetype(FONT_CODE_PATH, 24) if os.path.exists(FONT_CODE_PATH) else ImageFont.truetype(FONT_PATH, 24),
            "code_bold": ImageFont.truetype(FONT_BOLD_PATH, 25),
            "badge": ImageFont.truetype(FONT_BOLD_PATH, 22),
            "formula": ImageFont.truetype(FONT_BOLD_PATH, 48),
            "formula_sub": ImageFont.truetype(FONT_PATH, 36),
        }
    except IOError:
        default = ImageFont.load_default()
        fonts = {k: default for k in ["large_title","card_title","box_header","body","body_bold","desc","code","code_bold","badge","formula","formula_sub"]}
    return fonts

def wrap_text_by_pixels(text, font, max_width, draw):
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

def draw_grid_and_base(draw):
    grid_spacing = 118.8
    for x in range(1, int(CANVAS_W / grid_spacing)):
        lx = int(x * grid_spacing)
        draw.line([(lx, 0), (lx, CANVAS_H)], fill=(238, 242, 246), width=1)
    for y in range(1, int(CANVAS_H / grid_spacing)):
        ly = int(y * grid_spacing)
        draw.line([(0, ly), (CANVAS_W, ly)], fill=(238, 242, 246), width=1)

def draw_header_card(draw, title, subtitle, fonts, color=(37, 99, 235)):
    # Draw double line inner border
    draw.rectangle([24, 24, 3336, 2352], outline=(203, 213, 225), width=3)
    draw.rectangle([30, 30, 3330, 2346], outline=(226, 232, 240), width=1)
    
    # Header box — two-line layout (title + subtitle)
    draw.rectangle([54, 72, 3303, 285], fill=(241, 245, 249))
    draw.rectangle([48, 66, 3297, 279], fill=(255, 255, 255), outline=(203, 213, 225), width=3)
    draw.rectangle([48, 66, 3297, 75], fill=color)
    draw.text((82, 152), title, fill=(15, 23, 42), font=fonts["large_title"], anchor="lm")
    draw.text((82, 248), subtitle, fill=(100, 116, 139), font=fonts["desc"], anchor="lm")

    # Footer/Title block (图签)
    # (Removed as per user request to not display title block at the bottom right)


def draw_card_with_shadow(draw, rect, fill, outline, width=2, radius=12, shadow_color=(226, 232, 240), shadow_offset=6):
    x1, y1, x2, y2 = rect
    draw.rounded_rectangle([x1 + shadow_offset, y1 + shadow_offset, x2 + shadow_offset, y2 + shadow_offset], radius=radius, fill=shadow_color)
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)

# -------------------------------------------------------------
# 1. DR-006_原始数据清单
# -------------------------------------------------------------
def generate_data_list_sheet():
    print("Generating DR-006_原始数据清单.png...")
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), color=(250, 252, 254))
    draw = ImageDraw.Draw(img)
    fonts = load_fonts()
    
    draw_grid_and_base(draw)
    draw_header_card(draw, "规划设计原始数据清单", "系统推演与现状诊断所依赖的多源城市感知及法理规则等 12 大类原始数据库。", fonts, color=(59, 130, 246))
    
    # 3 rows, 4 columns grid — scaled 1.5x (aligned with DR-025/DR-026)
    cols, rows_n = 4, 3
    card_w = 768
    card_h = 615
    gap_x = 45
    gap_y = 33
    start_x = 63
    start_y = 315
    
    data_sources = [
        ("1. 规划研究红线 (GeoJSON)", "自绘成果", "170.4 公顷", 
         "确立规划设计空间边界约束", 
         "通过人工收集周边社区法理界线，对齐高分影像，校正并确定古城周边街区核心更新范围闭合曲线。"),
        ("2. 现状建筑基底 (GeoJSON)", "OSM 数据", "11,289 栋建筑", 
         "计算容积率及建筑密度", 
         "包含古城区内所有建筑 of 规划及高度，用以自动化重构三维数字孪生底座。"),
        ("3. 城市道路网络 (GeoJSON)", "OSM 数据", "1,062 段核心路段", 
         "空间句法与慢行分析", 
         "高精度拓扑道路中心线网，包含机动车道、人行道、支路和历史胡同，作为行人可达性与网络穿行度基底。"),
        ("4. 现状土地利用 (GeoJSON)", "自绘成果", "1,026 宗地块", 
         "核查现状控规用地占比", 
         "包含三级用地分类代码(GB-Code)及权属边界，用于校验现状绿地率及开发强度等硬性指标合规审查。"),
        ("5. POI 产业活力数据 (CSV)", "百度地图 API", "411 条服务节点", 
         "计算服务核密度与配套覆盖", 
         "抓取古城区内餐饮、文娱、教育、医疗等生活服务要素节点，用以衡量街区社会设施配套短板。"),
        ("6. 实拍街景影像 (JPG)", "百度街景", "1,788 张街区照片", 
         "计算绿视率(GVI)与天空开阔", 
         "基于全景相机定点采样街景，通过语义分割模型(SegFormer)自动分析行人视角的绿化比例与微气候品质。"),
        ("7. 微博舆情文本 (CSV)", "新浪微博", "207 条社会舆情", 
         "NLP 情感分析获取公众诉求", 
         "抓取街区更新相关的社交媒体文本，提取高频热词与负面情感节点，捕捉居民对平价商业和绿化空间的需求。"),
        ("8. 政策保护规章 (PDF)", "自然资源部", "248 个向量分块", 
         "大模型 RAG 知识库合规审查", 
         "包含《长春历史文化名城保护规划》及建筑限高规定，切分向量化后输入 LLM，实现方案自动法理合规审计。"),
        ("9. 建筑层高分布数据 (GeoJSON)", "自绘成果", "11,289 栋建筑", 
         "三维空间管控与日照模拟", 
         "包含各现状建筑的真实物理层数及绝对高度属性，用于测算片区容积率分布及三维白模日照模拟。"),
        ("10. 空间句法整合度数据 (GeoJSON)", "平台深度计算", "1,062 段道路", 
         "计算路网全局整合度与穿行", 
         "基于拓扑中心线进行空间句法分析，计算全局和局部整合度(Integration)与选择度(Choice)，辅助慢行织补。"),
        ("11. 控规地块日照参数 (CSV)", "自绘成果", "5 个重点片区", 
         "计算重点更新地块的日照遮挡", 
         "包含长春纬度(43.9°)、冬至日太阳高度角等参数，用以进行矢量日照阴影几何解算及退界合规审查。"),
        ("12. 街区微气候栅格数据 (TIFF)", "遥感反演", "20m × 20m 栅格", 
         "热岛效应诊断与风道优化", 
         "高分辨率地表温度(LST)及风速流场栅格底图，用以评估古城周边的热舒适度及口袋公园微气候布局。")
    ]
    
    card_colors = [
        ((239, 246, 255), (59, 130, 246), (30, 58, 138)),
        ((240, 253, 244), (16, 185, 129), (6, 95, 70)),
        ((254, 243, 199), (245, 158, 11), (180, 83, 9)),
        ((250, 245, 255), (168, 85, 247), (107, 33, 168)),
        ((255, 241, 242), (244, 63, 94), (159, 18, 57)),
        ((236, 254, 255), (6, 182, 212), (8, 114, 133)),
        ((254, 242, 242), (239, 68, 68), (153, 27, 27)),
        ((248, 250, 252), (100, 116, 139), (51, 65, 85)),
        ((238, 242, 255), (79, 70, 229), (49, 46, 129)),
        ((240, 253, 250), (13, 148, 136), (17, 94, 89)),
        ((236, 253, 245), (16, 185, 129), (6, 95, 70)),
        ((255, 247, 237), (249, 115, 22), (124, 45, 18))
    ]
    
    for idx, (title, source, scale, desc, detail) in enumerate(data_sources):
        col = idx % cols
        row = idx // cols
        x0 = start_x + col * (card_w + gap_x)
        y0 = start_y + row * (card_h + gap_y)
        
        fill_c, stroke_c, text_c = card_colors[idx]
        
        rect = [x0, y0, x0 + card_w, y0 + card_h]
        draw_card_with_shadow(draw, rect, fill=(255, 255, 255), outline=stroke_c, width=2)
        
        # Header strip inside card
        draw.rectangle([x0 + 1, y0 + 1, x0 + card_w - 1, y0 + 66], fill=fill_c)
        draw.line([(x0, y0 + 66), (x0 + card_w, y0 + 66)], fill=stroke_c, width=1)
        
        draw.text((x0 + 24, y0 + 33), title, fill=text_c, font=fonts["body_bold"], anchor="lm")
        
        # Tags/Badges
        sb_w = len(source) * 15 + 24
        draw.rounded_rectangle([x0 + 21, y0 + 84, x0 + 21 + sb_w, y0 + 118], radius=6, fill=fill_c, outline=stroke_c, width=1)
        draw.text((x0 + 21 + sb_w//2, y0 + 101), source, fill=text_c, font=fonts["badge"], anchor="mm")
        
        sc_w = len(scale) * 15 + 24
        draw.rounded_rectangle([x0 + 36 + sb_w, y0 + 84, x0 + 36 + sb_w + sc_w, y0 + 118], radius=6, fill=(241, 245, 249), outline=(203, 213, 225), width=1)
        draw.text((x0 + 36 + sb_w + sc_w//2, y0 + 101), scale, fill=(71, 85, 105), font=fonts["badge"], anchor="mm")
        
        # Role text
        y_cursor = y0 + 140
        draw.text((x0 + 27, y_cursor), "规划功能:", fill=(15, 23, 42), font=fonts["body_bold"])
        y_cursor += 36
        wrapped_desc = wrap_text_by_pixels(desc, fonts["body"], card_w - 60, draw)
        for line in wrapped_desc:
            draw.text((x0 + 33, y_cursor), line, fill=(71, 85, 105), font=fonts["body"])
            y_cursor += 30
            
        # Divider line
        y_cursor += 20
        draw.line([(x0 + 21, y_cursor), (x0 + card_w - 21, y_cursor)], fill=(226, 232, 240), width=1)
        
        # Detail text
        y_cursor += 22
        draw.text((x0 + 27, y_cursor), "数据加工与采集详情:", fill=(15, 23, 42), font=fonts["body_bold"])
        y_cursor += 36
        wrapped_detail = wrap_text_by_pixels(detail, fonts["body"], card_w - 60, draw)
        for line in wrapped_detail:
            draw.text((x0 + 33, y_cursor), line, fill=(100, 116, 139), font=fonts["body"])
            y_cursor += 30
            
    dest_path = ATLAS_DIR / "DR-006_原始数据清单.png"
    img.save(dest_path)
    print(f"Saved: {dest_path}")



# -------------------------------------------------------------
# 2. DR-025_核心算法与数学公式 (全量版 — 4列×3行 卡片网格)
# -------------------------------------------------------------
def generate_formulas_sheet():
    print("Generating DR-025_核心算法与数学公式.png...")
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), color=(250, 252, 254))
    draw = ImageDraw.Draw(img)
    fonts = load_fonts()

    draw_grid_and_base(draw)
    draw_header_card(draw, "核心算法与数学公式",
                     "本平台涉及的全部数学公式与算法体系，覆盖空间分析、视觉感知、博弈决策、合规审计等 12 项核心技术。",
                     fonts, color=(217, 119, 6))

    # 4 columns × 3 rows card grid — scaled 1.5x
    cols, rows_n = 4, 3
    card_w = 768
    card_h = 615
    gap_x = 45
    gap_y = 33
    start_x = 63
    start_y = 315

    # (序号, 标题, 公式表达式, 参数说明列表, 应用说明, 颜色组 fill/stroke/text)
    formulas = [
        # ── Row 1 ──
        ("1.", "AHP-MPI 更新潜力指数",
         "MPI = (W_s * S + W_d * D + W_e * (1 - E)) / sum(W) * 100",
         [("W_s=0.4, W_d=0.3, W_e=0.3", "AHP层次分析法确定权重"),
          ("S - 空间区位优势度", "空间句法集成度+配套覆盖率加权"),
          ("D - 现状品质缺陷度", "绿视率偏低+建筑老化程度"),
          ("E - 风貌价值敏感度", "紫线保护范围与历史建筑占比")],
         "对20m×20m栅格单元评估更新优先级，高斯平滑后输出热力分布图。",
         (254, 243, 199), (245, 158, 11), (180, 83, 9)),

        ("2.", "空间句法全局整合度",
         "Integration(i) = (n-1) / sum_j d(i,j)",
         [("n - 轴线系统总节点数", "路网拓扑图的节点集合"),
          ("d(i,j) - 最短拓扑深度", "Dijkstra最短路径算法计算"),
          ("Closeness - 近似采样法", "随机采样k=300节点加速计算")],
         "分析步行可达性瓶颈与'交通孤岛效应'，输出Spectral色谱路网图。",
         (239, 246, 255), (59, 130, 246), (30, 58, 138)),

        ("3.", "空间句法协同度 analysis",
         "R^2 = (sum((Rn_i - Rn_mean) * (Ch_i - Ch_mean)))^2 / (sum(Rn_i-Rn_mean)^2 * sum(Ch_i-Ch_mean)^2)",
         [("Rn_i - 全局整合度(归一化)", "反映路段全局可达性"),
          ("Ch_i - 全局选择度(归一化)", "反映路段穿行频率"),
          ("R^2 - 拟合决定系数", "OLS线性回归评估协同度")],
         "R^2越高说明全局交通与局部慢行网络耦合越好，输出协同度散点图。",
         (240, 253, 244), (16, 185, 129), (6, 95, 70)),

        ("4.", "高斯核密度估计 (KDE)",
         "f(x,y) = sum(w_k * exp(-((x-x_k)^2 + (y-y_k)^2) / 2*sigma^2))",
         [("(x_k, y_k) - POI 坐标", "百度地图API获取的服务节点"),
          ("w_k - 权重系数", "按商圈等级分配1.5/1.2/0.9/0.6"),
          ("sigma - 高斯核带宽", "按集聚半径300~420m设定")],
         "生成POI产业活力热力图，识别服务真空区与活力极核。",
         (255, 241, 242), (244, 63, 94), (159, 18, 57)),

        # ── Row 2 ──
        ("5.", "SegFormer 语义分割四维测度",
         "GVI = sum(px(veg)) / sum(px(total)) * 100%\nSVF = sum(px(sky)) / sum(px(total)) * 100%",
         [("GVI - 绿视率", "Cityscapes类8(vegetation)像素占比"),
          ("SVF - 天空开阔度", "Cityscapes类10(sky)像素占比"),
          ("Enclosure - 围合度", "(建筑+墙体+植被)像素占比"),
          ("Clutter - 杂乱度", "(杆+标识+栅栏)像素占比")],
         "SegFormer-B0模型对1,788张街景四方向均值聚合，GPU推理。",
         (240, 253, 244), (16, 185, 129), (6, 95, 70)),

        ("6.", "NLP 舆情情感分析算法",
         "Score = (|pos and W| - |neg and W|) / (|pos and W| + |neg and W| + 1)",
         [("pos / neg - 情感词典", "城市规划领域定制正/负面词库"),
          ("W - 分词集合", "Jieba中文分词提取关键词"),
          ("LLM增强", "DeepSeek-V4批量语义打分0~100")],
         "双路径：LLM语义评分 + 词典回退，输出情感分布与词云。",
         (250, 245, 255), (168, 85, 247), (107, 33, 168)),

        ("7.", "多主体博弈满意度效用函数",
         "S_role = min(100, 50 + 7 * sum([1 if w in K_role]))",
         [("K_res - 居民词库", "{'绿化','配套','社区','医院','养老'}"),
          ("K_dev - 运营商词库", "{'容积率','投资','商业','品牌','客流'}"),
          ("K_gov - 规划师词库", "{'紫线','限高','风貌','退让','合规'}"),
          ("LLM语义审计", "DeepSeek-V4-Flash对话评分覆盖")],
         "三方满意度均>60%判定共识达成，驱动协商收敛。",
         (254, 243, 199), (245, 158, 11), (180, 83, 9)),

        ("8.", "法定控规红线指标审计",
         "FAR = sum(F_i * A_i) / A_land\nDensity = sum(A_i) / A_land * 100%\nGAR = sum(S_green) / A_land * 100%",
         [("FAR - 容积率", "总建筑面积/用地面积 <= 1.40"),
          ("Density - 建筑密度", "基底投影面积/用地面积 <= 30%"),
          ("GAR - 绿地率", "绿地面积/用地面积 >= 35%")],
         "实时校验方案合规性，超限自动红色警示拦截。",
         (239, 246, 255), (59, 130, 246), (30, 58, 138)),

        # ── Row 3 ──
        ("9.", "矢量日照阴影投射算法",
         "Shadow = Union(Poly, Translate(Poly, dx, dy))\ndx = -4.86e-6 * H,  dy = 3.5e-6 * H",
         [("H - 建筑高度(m)", "层数×3.5m估算"),
          ("dx, dy - 阴影位移", "长春纬度43.9°太阳夹角投影"),
          ("侧壁阴影", "相邻顶点对连接四边形拓扑并集")],
         "生成全域11,289栋建筑精确矢量阴影图层。",
         (255, 241, 242), (244, 63, 94), (159, 18, 57)),

        ("10.", "向量面积 (Shoelace) 公式",
         "Area = |sum(x_i*y_{i+1} - x_{i+1}*y_i)| / 2\nArea_ha = Area_deg * 80 * 111 * 100",
         [("(x_i, y_i) - 多边形顶点", "WGS84经纬度坐标序列"),
          ("80*111 - 度 to km 换算", "长春纬度1°经度≈80km"),
          ("墨卡托纠偏系数", "EPSG:3857投影误差 < 0.02%")],
         "计算研究范围面积与用地指标，支撑规划指标表。",
         (240, 253, 244), (16, 185, 129), (6, 95, 70)),

        ("11.", "RAG 向量检索与语义匹配",
         "Score(q, d) = cos_sim(q, d) = (q * d) / (||q|| * ||d||)",
         [("q - 查询向量", "BGE-Micro嵌入模型L2归一化"),
          ("d - 文档向量", "330个政策法规知识块预计算"),
          ("||q|| - 向量模长", "L2范数归一化因子")],
         "法规合规校验与导则引用的语义检索引擎。",
         (250, 245, 255), (168, 85, 247), (107, 33, 168)),

        ("12.", "图纸质量双通道评估模型",
         "Q = 0.4 * V_score + 0.6 * C_score\nRating: A(>=8) B(>=6) C(>=4) D(<4)",
         [("V_score - 视觉评分", "Gemma3视觉模型图面评估0~10"),
          ("C_score - 内容评分", "DeepSeek-V4语义准确性0~10"),
          ("权重分配", "内容准确性权重0.6 > 视觉0.4")],
         "AIGC出图后自动质量审计，D级触发重绘。",
         (248, 250, 252), (100, 116, 139), (51, 65, 85)),
    ]

    for idx, (num, title, formula, params, app_note, fill_c, stroke_c, text_c) in enumerate(formulas):
        col = idx % cols
        row = idx // cols
        x0 = start_x + col * (card_w + gap_x)
        y0 = start_y + row * (card_h + gap_y)

        # Card with shadow
        rect = [x0, y0, x0 + card_w, y0 + card_h]
        draw_card_with_shadow(draw, rect, fill=(255, 255, 255), outline=stroke_c, width=2)

        # Header strip
        draw.rectangle([x0 + 1, y0 + 1, x0 + card_w - 1, y0 + 66], fill=fill_c)
        draw.line([(x0, y0 + 66), (x0 + card_w, y0 + 66)], fill=stroke_c, width=1)
        draw.text((x0 + 24, y0 + 33), f"{num} {title}", fill=text_c, font=fonts["body_bold"], anchor="lm")

        # Formula box
        f_y = y0 + 84
        f_h = 118
        draw.rounded_rectangle([x0 + 21, f_y, x0 + card_w - 21, f_y + f_h], radius=9, fill=(248, 250, 252), outline=(226, 232, 240), width=1)
        f_lines = formula.split("\n")
        f_font = fonts["badge"]
        try:
            f_font = ImageFont.truetype(FONT_BOLD_PATH, 30)
        except Exception:
            pass
        line_h = 36
        fy_start = f_y + (f_h - len(f_lines) * line_h) // 2
        for li, fl in enumerate(f_lines):
            draw.text((x0 + card_w // 2, fy_start + li * line_h + 12), fl, fill=(15, 23, 42), font=f_font, anchor="mm")

        # Parameters
        y_cursor = f_y + f_h + 18
        try:
            font_param_name = ImageFont.truetype(FONT_BOLD_PATH, 24)
            font_param_desc = ImageFont.truetype(FONT_PATH, 22)
        except Exception:
            font_param_name = fonts["badge"]
            font_param_desc = fonts["badge"]

        for pname, pdesc in params:
            draw.text((x0 + 27, y_cursor), f"· {pname}", fill=text_c, font=font_param_name)
            y_cursor += 30
            wrapped = wrap_text_by_pixels(pdesc, font_param_desc, card_w - 63, draw)
            for wl in wrapped:
                draw.text((x0 + 39, y_cursor), wl, fill=(100, 116, 139), font=font_param_desc)
                y_cursor += 28
            y_cursor += 8

        # Application note at bottom
        draw.line([(x0 + 21, y0 + card_h - 76), (x0 + card_w - 21, y0 + card_h - 76)], fill=(226, 232, 240), width=1)
        wrapped_app = wrap_text_by_pixels(app_note, font_param_desc, card_w - 54, draw)
        ay = y0 + card_h - 64
        for al in wrapped_app:
            draw.text((x0 + 27, ay), al, fill=(71, 85, 105), font=font_param_desc)
            ay += 28

    dest_path = ATLAS_DIR / "DR-025_核心算法与数学公式.png"
    img.save(dest_path)
    print(f"Saved: {dest_path}")

# -------------------------------------------------------------
# 3. DR-026_平台核心代码清单 (全量模块版 — 4列×3行)
# -------------------------------------------------------------
def generate_code_list_sheet():
    print("Generating DR-026_平台核心代码清单.png...")
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), color=(250, 252, 254))
    draw = ImageDraw.Draw(img)
    fonts = load_fonts()

    draw_grid_and_base(draw)
    draw_header_card(draw, "平台核心代码清单",
                     "基于 Python + Streamlit + DeepSeek + SegFormer + GeoPandas 构建的全链路智能设计平台核心模块清单。",
                     fonts, color=(16, 185, 129))

    cols, rows_n = 4, 3
    card_w = 768
    card_h = 615
    gap_x = 45
    gap_y = 33
    start_x = 63
    start_y = 315

    try:
        font_mod_title = ImageFont.truetype(FONT_BOLD_PATH, 30)
        font_mod_file = ImageFont.truetype(FONT_CODE_PATH if os.path.exists(FONT_CODE_PATH) else FONT_PATH, 22)
        font_mod_body = ImageFont.truetype(FONT_PATH, 24)
        font_mod_bold = ImageFont.truetype(FONT_BOLD_PATH, 25)
        font_mod_tag = ImageFont.truetype(FONT_BOLD_PATH, 20)
    except Exception:
        font_mod_title = fonts["body_bold"]
        font_mod_file = fonts["badge"]
        font_mod_body = fonts["badge"]
        font_mod_bold = fonts["badge"]
        font_mod_tag = fonts["badge"]

    modules = [
        # Row 1
        ("1.", "MPI 更新潜力评估引擎",
         "tools/drawings/dr_061.py",
         ["compute_mpi_grid()", "gaussian_filter()", "proximity_boost()"],
         "GeoPandas + SciPy + NumPy",
         "在20m×20m栅格上计算空间潜力(S)、需求(D)、环境品质(E)三维度MPI指数，高斯平滑后输出连续渐变热力图。支持重点地块近邻增强与百分位直方图拉伸。",
         (254, 243, 199), (245, 158, 11), (180, 83, 9)),

        ("2.", "SegFormer 街景语义分割引擎",
         "src/engines/urban_image_segmentation.py",
         ["calculate_urban_indices()", "run_pipeline()", "360°聚合"],
         "NVIDIA SegFormer-B0 + PyTorch",
         "加载Cityscapes预训练模型，对1,788张四方向街景执行GPU语义分割，提取19类像素占比，计算GVI/SVF/Enclosure/Clutter四维视觉品质指标，支持断点续传。",
         (240, 253, 244), (16, 185, 129), (6, 95, 70)),

        ("3.", "空间句法可达性分析模块",
         "tools/drawings/dr_021.py",
         ["approx_closeness()", "Dijkstra()", "Synergy R^2"],
         "NetworkX + GeoPandas",
         "构建道路拓扑图，采样k=300节点近似计算全局整合度与选择度，OLS线性回归输出协同度散点图，诊断'交通孤岛效应'与步行微循环瓶颈。",
         (239, 246, 255), (59, 130, 246), (30, 58, 138)),

        ("4.", "POI 核密度产业活力分析",
         "tools/drawings/dr_027.py",
         ["KDE contourf()", "void_zone()", "glow_scatter()"],
         "NumPy + Matplotlib",
         "基于高斯核密度估计生成50级等值线热力图，按商圈权重(1.5/1.2/0.9/0.6)与核带宽(300~420m)参数化，标注POI服务真空区与活力极核。",
         (255, 241, 242), (244, 63, 94), (159, 18, 57)),

        # Row 2
        ("5.", "NLP 舆情情感分析引擎",
         "src/engines/nlp_engine.py",
         ["classify_sentiment()", "_llm_classify_batch()", "jieba分词"],
         "DeepSeek-V4 + Jieba + LLM",
         "双路径情感分析：优先DeepSeek批量语义打分(0~100)，降级为城市规划定制词典正/负面词匹配。输出情感分布图与Top-15高频词云。",
         (250, 245, 255), (168, 85, 247), (107, 33, 168)),

        ("6.", "多主体博弈协商系统",
         "pages/07_设计策略.py",
         ["calculate_dynamic_satisfaction()", "LLM角色扮演", "共识判定"],
         "DeepSeek-V4-Flash + Streamlit",
         "居民/运营商/规划师三角色LLM对话系统。关键词命中+LLM语义双重评分计算满意度S_role，三方均>60%判定共识达成，实时可视化协商收敛曲线。",
         (254, 243, 199), (245, 158, 11), (180, 83, 9)),

        ("7.", "RAG 政策法规检索引擎",
         "src/engines/rag_engine.py",
         ["retrieve_rag_context()", "compute_query_embedding()", "BGE向量化"],
         "BGE-Micro-ZH-V4 + Jieba",
         "加载330个政策法规向量块，BGE嵌入+余弦相似度Top-K检索。持久化缓存MD5校验机制，嵌入失败时Jieba分词TF匹配回退。支撑法规合规自动校验。",
         (240, 253, 244), (16, 185, 129), (6, 95, 70)),

        ("8.", "矢量日照阴影生成器",
         "tools/generate_building_shadows.py",
         ["compute_shadow_geometry()", "Translate()", "unary_union()"],
         "Shapely + GeoPandas",
         "基于长春纬度(43.9°)太阳高度角计算阴影位移系数，对11,289栋建筑执行底面平移+侧壁四边形拓扑并集，生成精确矢量阴影GeoJSON图层。",
         (239, 246, 255), (59, 130, 246), (30, 58, 138)),

        # Row 3
        ("9.", "控规指标实时审计引擎",
         "tools/generate_indicator_images.py",
         ["calculate_metrics()", "GIS空间裁剪", "墨卡托纠偏"],
         "GeoPandas + Shapely",
         "基于GIS矢量数据实时计算容积率(FAR)、建筑密度、绿地率等控规指标。支持五地块分项统计、现状/规划对比、高斯-克吕格投影精度校验(<0.02%)。",
         (255, 241, 242), (244, 63, 94), (159, 18, 57)),

        ("10.", "三维白模渲染引擎",
         "src/engines/white_model_renderer.py",
         ["render_3d()", "等角透视投影", "高斯模糊后处理"],
         "PIL + NumPy + GeoPandas",
         "加载建筑基底GeoJSON，按层高(Floor×3.5m)拉伸为三维棱柱体，等角透视投影渲染白模鸟瞰效果图，支持彩色用地覆盖与高斯模糊景深效果。",
         (240, 253, 244), (16, 185, 129), (6, 95, 70)),

        ("11.", "AIGC 图纸质量审计器",
         "src/engines/quality_assessor.py",
         ["assess()", "视觉+内容双通道", "ABCD等级"],
         "Gemma3 + DeepSeek-V4",
         "双通道质量评估：Ollama Gemma视觉模型评图面整洁度(V_score)，DeepSeek评内容准确性(C_score)。综合加权Q=0.4V+0.6C，D级自动触发重绘。",
         (250, 245, 255), (168, 85, 247), (107, 33, 168)),

        ("12.", "Prompt 编译与出图管线",
         "src/engines/drawing_pipeline.py",
         ["PromptCompiler()", "StableDiffusion()", "版本存档"],
         "Stable Diffusion + LLM",
         "端到端AIGC出图流水线：Prompt编译器注入GIS指标与政策约束，Stable Diffusion生成效果图，质量审计器自动评分，版本存档器管理迭代历史。",
         (248, 250, 252), (100, 116, 139), (51, 65, 85)),
    ]

    for idx, (num, title, filepath, funcs, tech, desc, fill_c, stroke_c, text_c) in enumerate(modules):
        col = idx % cols
        row = idx // cols
        x0 = start_x + col * (card_w + gap_x)
        y0 = start_y + row * (card_h + gap_y)

        rect = [x0, y0, x0 + card_w, y0 + card_h]
        draw_card_with_shadow(draw, rect, fill=(255, 255, 255), outline=stroke_c, width=2)

        # Header strip
        draw.rectangle([x0 + 1, y0 + 1, x0 + card_w - 1, y0 + 66], fill=fill_c)
        draw.line([(x0, y0 + 66), (x0 + card_w, y0 + 66)], fill=stroke_c, width=1)
        draw.text((x0 + 24, y0 + 33), f"{num} {title}", fill=text_c, font=font_mod_title, anchor="lm")

        # File path badge
        fp_w = len(filepath) * 11 + 24
        draw.rounded_rectangle([x0 + 21, y0 + 84, x0 + 21 + fp_w, y0 + 118], radius=6, fill=(30, 41, 59), outline=(71, 85, 105), width=1)
        draw.text((x0 + 21 + fp_w // 2, y0 + 101), filepath, fill=(148, 163, 184), font=font_mod_file, anchor="mm")

        # Tech stack badge
        ts_x = x0 + 21 + fp_w + 15
        ts_w = len(tech) * 11 + 24
        if ts_x + ts_w > x0 + card_w - 21:
            ts_w = x0 + card_w - 21 - ts_x
        draw.rounded_rectangle([ts_x, y0 + 84, ts_x + ts_w, y0 + 118], radius=6, fill=fill_c, outline=stroke_c, width=1)
        draw.text((ts_x + ts_w // 2, y0 + 101), tech, fill=text_c, font=font_mod_tag, anchor="mm")

        # Key functions section
        y_cursor = y0 + 138
        draw.text((x0 + 27, y_cursor), "核心函数:", fill=(15, 23, 42), font=font_mod_bold)
        y_cursor += 36
        for fn in funcs:
            draw.text((x0 + 39, y_cursor), f"· {fn}", fill=stroke_c, font=font_mod_bold)
            y_cursor += 31

        # Description
        y_cursor += 15
        draw.line([(x0 + 21, y_cursor), (x0 + card_w - 21, y_cursor)], fill=(226, 232, 240), width=1)
        y_cursor += 18
        draw.text((x0 + 27, y_cursor), "模块说明:", fill=(15, 23, 42), font=font_mod_bold)
        y_cursor += 34
        wrapped_desc = wrap_text_by_pixels(desc, font_mod_body, card_w - 60, draw)
        for dl in wrapped_desc:
            draw.text((x0 + 33, y_cursor), dl, fill=(71, 85, 105), font=font_mod_body)
            y_cursor += 30

    dest_path = ATLAS_DIR / "DR-026_平台核心代码清单.png"
    img.save(dest_path)
    print(f"Saved: {dest_path}")

def generate_all_list_diagrams():
    generate_data_list_sheet()
    generate_formulas_sheet()
    generate_code_list_sheet()
    print("All 3 horizontal lists/formulas infographics redrawn successfully!")

if __name__ == "__main__":
    generate_all_list_diagrams()
