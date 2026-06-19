# -*- coding: utf-8 -*-
# tools/generate_design_creed_sheets.py
import os
import sys
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

ATLAS_DIR = ROOT / "static" / "atlas"
ATLAS_DIR.mkdir(parents=True, exist_ok=True)

# Font Paths
FONT_PATH = 'C:/Windows/Fonts/msyh.ttc'
FONT_BOLD_PATH = 'C:/Windows/Fonts/msyhbd.ttc'

# ---- 原始 ChatGPT 高清图重命名映射 ----
# 旧文件名 -> 新文件名（根据图片内容命名）
_RENAME_MAP = {
    "ChatGPT Image 2026年6月5日 21_19_19.png": "A设计依据.png",
    "ChatGPT Image 2026年6月5日 02_17_59.png": "A设计原则.png",
    "ChatGPT Image 2026年6月5日 02_24_59.png": "A设计定位.png",
    "ChatGPT Image 2026年6月5日 02_21_51.png": "A设计目标.png",
    "ChatGPT Image 2026年6月5日 02_28_18.png": "A设计策略.png",
}

def _ensure_renamed():
    """首次运行时自动将 ChatGPT 长文件名重命名为内容语义化短名。"""
    for old_name, new_name in _RENAME_MAP.items():
        old_path = ATLAS_DIR / old_name
        new_path = ATLAS_DIR / new_name
        if old_path.exists() and not new_path.exists():
            old_path.rename(new_path)
            print(f"  [重命名] {old_name} -> {new_name}")

# 5 张 A 系列设计图的 源图 -> 目标 映射
_COPY_MAP = {
    "A设计依据.png": "A设计依据.png",
    "A设计原则.png": "A设计原则.png",
    "A设计定位.png": "A设计定位.png",
    "A设计目标.png": "A设计目标.png",
    "A设计策略.png": "A设计策略.png",
}

def load_fonts():
    try:
        fonts = {
            "large_title": ImageFont.truetype(FONT_BOLD_PATH, 36),
            "card_title": ImageFont.truetype(FONT_BOLD_PATH, 20),
            "box_header": ImageFont.truetype(FONT_BOLD_PATH, 18),
            "body": ImageFont.truetype(FONT_PATH, 14),
            "body_bold": ImageFont.truetype(FONT_BOLD_PATH, 14),
            "desc": ImageFont.truetype(FONT_PATH, 15),
            "large_number": ImageFont.truetype(FONT_BOLD_PATH, 64),
            "caption": ImageFont.truetype(FONT_PATH, 12),
        }
    except IOError:
        default = ImageFont.load_default()
        fonts = {
            "large_title": default,
            "card_title": default,
            "box_header": default,
            "body": default,
            "body_bold": default,
            "desc": default,
            "large_number": default,
            "caption": default,
        }
    return fonts

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
def draw_grid_and_base(draw):
    grid_spacing = 79.2
    for x in range(1, int(2240 / grid_spacing)):
        lx = int(x * grid_spacing)
        draw.line([(lx, 0), (lx, 1584)], fill=(226, 232, 240), width=1)
    for y in range(1, int(1584 / grid_spacing)):
        ly = int(y * grid_spacing)
        draw.line([(0, ly), (2240, ly)], fill=(226, 232, 240), width=1)

def draw_header_card(draw, title, subtitle, fonts):
    draw.rectangle([36, 64, 2202, 178], fill=(226, 232, 240))
    draw.rectangle([32, 60, 2198, 174], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 60, 2198, 66], fill=(217, 119, 6))
    draw.text((55, 117), title, fill=(15, 23, 42), font=fonts["large_title"], anchor="lm")
    draw.text((420, 117), subtitle, fill=(100, 116, 139), font=fonts["desc"], anchor="lm")

def draw_card_with_shadow(draw, rect, fill, outline, width=2, radius=8, shadow_color=(226, 232, 240), shadow_offset=4):
    x1, y1, x2, y2 = rect
    draw.rounded_rectangle([x1 + shadow_offset, y1 + shadow_offset, x2 + shadow_offset, y2 + shadow_offset], radius=radius, fill=shadow_color)
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)

# -------------------------------------------------------------
# 5 张 A 系列设计图：直接复制用户原始 ChatGPT 高清图
# -------------------------------------------------------------
def _copy_source(src_name, dst_name):
    src = ATLAS_DIR / src_name
    dst = ATLAS_DIR / dst_name
    if src.exists():
        shutil.copy2(src, dst)
        print(f"  [OK] {dst_name} (来源: {src_name})")
    else:
        print(f"  [ERR] 源文件不存在: {src_name}")

def generate_design_basis():
    _copy_source("A设计依据.png", "A设计依据.png")

def generate_design_principles():
    _copy_source("A设计原则.png", "A设计原则.png")

def generate_design_positioning():
    _copy_source("A设计定位.png", "A设计定位.png")

def generate_design_objectives():
    _copy_source("A设计目标.png", "A设计目标.png")

def generate_design_strategy():
    _copy_source("A设计策略.png", "A设计策略.png")

# -------------------------------------------------------------
# Drawing A特色专项设计.png (Pillow vector drawing)
# -------------------------------------------------------------
def generate_specialty_design():
    print("Generating A特色专项设计.png...")
    img = Image.new("RGB", (2240, 1584), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    fonts = load_fonts()
    
    draw_grid_and_base(draw)
    draw_header_card(draw, "5.1 特色专项设计", "融合'数智推演'与'空间深化'的特色专题研究与重点更新单元方案设计。", fonts)
    
    draw.rectangle([36, 210, 1588, 1524], fill=(226, 232, 240))
    draw.rectangle([32, 206, 1584, 1520], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 206, 1584, 212], fill=(217, 119, 6))
    
    draw.text((60, 250), "数智推演系统与五个重点更新单元深化 / SPECIAL UNIT DETAILED DESIGN", fill=(217, 119, 6), font=fonts["card_title"])
    draw.line([(60, 280), (1556, 280)], fill=(226, 232, 240), width=2)
    
    top_rect = [80, 310, 1536, 680]
    draw_card_with_shadow(draw, top_rect, fill=(239, 246, 255), outline=(59, 130, 246), width=2)
    draw.rectangle([80, 310, 1536, 335], fill=(59, 130, 246))
    draw.text((105, 360), "数智专题：LOD3底座 + AIGC生形 + 多智能体协商机制", fill=(30, 58, 138), font=fonts["box_header"])
    t_text = (
        "• 三维数字孪生底座：集成倾斜摄影与路景CV分割，识别水产市场1.87%绿视率、全域MPI为48.3的生态-活力'双重塌陷'病灶。\n"
        "• AIGC风貌审查引擎：以规划红线、建筑限高为刚性Mask，使用Stable Diffusion与ControlNet进行历史街区坡屋顶立面的自动控制生成。\n"
        "• 大模型博弈协商：利用大语言模型（LLM）扮演居民、开发商与规划师角色，历经三轮博弈取得利益一致的规划控制指标（容积率上限1.4等）。"
    )
    wrapped_t = wrap_text_by_pixels(t_text, fonts["body"], 1400, draw)
    y_text = 400
    for line in wrapped_t:
        draw.text((105, y_text), line, fill=(71, 85, 105), font=fonts["body"])
        y_text += 24

    unit_w = 270
    unit_h = 600
    gap = 20
    start_x = 80
    y_pos = 730
    
    units = [
        ("① 老水产地块 (3.71ha)", "御花园东巷文创生活街区", "• 功能定位：小尺度合院文创街区+垂直邻里中心\n• 规划控制：容积率≤1.3，绿地率≥38%，限高18m\n• 核心策略：化整为零聚落布局，缝合历史游线。"),
        ("② 调料大市场 (16.83ha)", "活态市集 · 风味院落", "• 功能定位：文创展示+特色坡屋顶餐饮街区+便民市场\n• 规划控制：容积率≤1.4，绿地率≥35%，限高18m\n• 核心策略：保留发酵广场与调料文化记忆，置换原棚架。"),
        ("③ 一中北侧地块 (2.78ha)", "全龄共享生活社区", "• 功能定位：适老社区照料+幼儿托管+老幼共享步道\n• 规划控制：容积率≤1.3，绿地率≥35%，限高15m\n• 核心策略：分流学生与长者生活动线，打造活力步行绿轴。"),
        ("④ 清禾集贸市场 (2.47ha)", "缝合者与社区发生器", "• 功能定位：下沉院落市集+青年创客工坊\n• 规划控制：容积率≤1.3，绿地率≥35%，限高9-15m\n• 核心策略：高度由北向南梯度过渡，二层连廊朝向皇宫对景。"),
        ("⑤ 石油公司地块 (1.30ha)", "宽城子能量花园", "• 功能定位：工业储油罐艺术活化公园+口袋大草坪\n• 规划控制：容积率≤1.2，绿地率≥35%，限高16m\n• 核心策略：拆除封闭围墙对街区完全开放，铺设漫步双环。")
    ]
    
    for idx, (title, subtitle, desc) in enumerate(units):
        ux1 = start_x + idx * (unit_w + gap)
        ux2 = ux1 + unit_w
        rect = [ux1, y_pos, ux2, y_pos + unit_h]
        
        colors = [
            ((254, 243, 199), (245, 158, 11)),
            ((240, 253, 244), (34, 197, 94)),
            ((239, 246, 255), (59, 130, 246)),
            ((250, 245, 255), (168, 85, 247)),
            ((255, 241, 242), (244, 63, 94))
        ]
        fill_c, stroke_c = colors[idx]
        
        draw_card_with_shadow(draw, rect, fill=fill_c, outline=stroke_c, width=2)
        draw.rectangle([ux1, y_pos, ux2, y_pos + 20], fill=stroke_c)
        
        draw.text((ux1 + 10, y_pos + 40), title, fill=(15, 23, 42), font=fonts["body_bold"])
        draw.text((ux1 + 10, y_pos + 65), subtitle, fill=stroke_c, font=fonts["caption"])
        
        wrapped_d = wrap_text_by_pixels(desc, fonts["caption"], unit_w - 20, draw)
        y_text = y_pos + 100
        for line in wrapped_d:
            draw.text((ux1 + 10, y_text), line, fill=(71, 85, 105), font=fonts["caption"])
            y_text += 18

    draw.rectangle([1612, 210, 2202, 606], fill=(226, 232, 240))
    draw.rectangle([1608, 206, 2198, 602], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1608, 206, 2198, 212], fill=(217, 119, 6))
    
    draw.text((1630, 240), "专题研究设计逻辑 / LOGIC OF PILOTS", fill=(217, 119, 6), font=fonts["card_title"])
    draw.line([(1630, 270), (2176, 270)], fill=(203, 213, 225), width=1)
    
    desc_lines = [
        "1. 技术与空间合一：专项设计体现了'技术诊断'与'空间落地'的有机结合。数智推演保证了方案的可行性与合规性，重点单元深化则保证了设计能落地。",
        "2. 差异化策略：根据五个地块不同的权属、规模和痛点，定制了适老共享、工业活化、历史缝合等差异化方案，以点带面激活街区。"
    ]
    y_desc = 295
    for line in desc_lines:
        wrapped = wrap_text_by_pixels(line, fonts["desc"], 510, draw)
        for wl in wrapped:
            draw.text((1630, y_desc), wl, fill=(71, 85, 105), font=fonts["desc"])
            y_desc += 26
        y_desc += 10

    draw.rectangle([1612, 638, 2202, 1524], fill=(226, 232, 240))
    draw.rectangle([1608, 634, 2198, 1520], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1608, 634, 2198, 640], fill=(217, 119, 6))
    
    draw.text((1630, 668), "重点单元详细指标控制表 / METRICS", fill=(217, 119, 6), font=fonts["card_title"])
    draw.line([(1630, 698), (2176, 698)], fill=(203, 213, 225), width=1)
    
    spec_lines = [
        "【五个单元更新指标汇总】 规划总占地面积约 26.89 公顷：",
        "• 老水产批发市场 (3.71ha)：容积率≤1.3，建筑密度≤25%，绿地率≥38%，限高18m。",
        "• 食品调料大市场 (16.83ha)：容积率≤1.4，建筑密度≤28%，绿地率≥35%，限高18m。",
        "• 一中北侧地块 (2.78ha)：容积率≤1.3，建筑密度≤26%，绿地率≥35%，限高15m。",
        "• 清禾集贸市场 (2.47ha)：容积率≤1.3，建筑密度≤25%，绿地率≥35%，限高15m。",
        "• 石油公司地块 (1.30ha)：容积率≤1.2，建筑密度≤30%，绿地率≥35%，限高16m。"
    ]
    y_spec = 720
    for line in spec_lines:
        wrapped = wrap_text_by_pixels(line, fonts["desc"], 510, draw)
        for wl in wrapped:
            draw.text((1630, y_spec), wl, fill=(71, 85, 105), font=fonts["desc"])
            y_spec += 26
        y_spec += 10
        
    img.save(ATLAS_DIR / "A特色专项设计.png")
    print("A特色专项设计.png saved successfully.")

def generate_all_creed_sheets():
    # 第一步：自动重命名 ChatGPT 长文件名 -> 语义化短名
    print("检查并重命名原始 ChatGPT 图片...")
    _ensure_renamed()

    # 第二步：复制原图到 A 系列目标文件名
    print("复制 5 张 A 系列设计图...")
    generate_design_basis()
    generate_design_principles()
    generate_design_positioning()
    generate_design_objectives()
    generate_design_strategy()

    # 第三步：Pillow 矢量绘制 A特色专项设计
    generate_specialty_design()
    print("All 6 design creed sheets generated successfully!")

if __name__ == "__main__":
    generate_all_creed_sheets()
