# -*- coding: utf-8 -*-
"""DR-007 上位规划解读图 — 对应答辩稿 3.1 设计依据"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patheffects as path_effects
import matplotlib.patches as mpatches
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"

# Bypasses the default A3 title frame
NO_FRAME = True

def get_fit_extent(img_w, img_h, x1, x2, y1, y2):
    box_w = x2 - x1
    box_h = y2 - y1
    box_cx = (x1 + x2) / 2
    box_cy = (y1 + y2) / 2
    
    img_ar = img_w / img_h
    box_ar = box_w / box_h
    
    if img_ar > box_ar:
        # Image is wider than box aspect ratio -> limit by width
        w = box_w
        h = w / img_ar
    else:
        # Image is taller than box aspect ratio -> limit by height
        h = box_h
        w = h * img_ar
    return [box_cx - w/2, box_cx + w/2, box_cy - h/2, box_cy + h/2]

def wrap_text(text, max_len=28):
    forbidden_start = set("，。、；：？！）】』」》〉〕”’）,.?!;:)】")
    forbidden_end = set("（【『「《〈〔“‘（([【")
    
    def char_width(c):
        return 2 if ord(c) > 127 else 1

    lines = []
    for part in text.split('\n'):
        if not part:
            lines.append("")
            continue
        current_line = ""
        current_w = 0
        i = 0
        while i < len(part):
            char = part[i]
            w = char_width(char)
            if current_w + w <= max_len:
                current_line += char
                current_w += w
                i += 1
            else:
                if not current_line:
                    current_line = char
                    current_w = w
                    i += 1
                else:
                    if part[i] in forbidden_start:
                        current_line += part[i]
                        i += 1
                        while i < len(part) and part[i] in forbidden_start:
                            current_line += part[i]
                            i += 1
                    while current_line and current_line[-1] in forbidden_end:
                        i -= 1
                        current_line = current_line[:-1]
                if current_line:
                    lines.append(current_line)
                current_line = ""
                current_w = 0
        if current_line:
            lines.append(current_line)
    return '\n'.join(lines)
def check_and_crop_image(filename):
    img_path = STATIC_DIR / "extracted_images" / filename
    if img_path.exists():
        return img_path
    
    # Try to find the source JPEG and crop it on the fly
    src_name = filename.replace("_crop.png", "_img1.jpeg")
    src_path = STATIC_DIR / "extracted_images" / src_name
    if not src_path.exists():
        src_name = filename.replace("_crop.png", "_img1.jpg")
        src_path = STATIC_DIR / "extracted_images" / src_name
        
    if src_path.exists():
        print(f"Dynamically cropping {src_name} -> {filename}...")
        try:
            img = Image.open(src_path)
            w, h = img.size
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Downsample to speed up scanning
            scale = 8
            small_img = img.resize((w // scale, h // scale))
            sw, sh = small_img.size
            
            left = sw
            right = 0
            top = sh
            bottom = 0
            
            pixels = small_img.load()
            for y in range(sh):
                for x in range(sw):
                    r, g, b = pixels[x, y]
                    # Map is colorful, background is near-white
                    if r < 242 or g < 242 or b < 242:
                        if x < left: left = x
                        if x > right: right = x
                        if y < top: top = y
                        if y > bottom: bottom = y
            
            # Margin and scale back
            margin = 15
            left = max(0, (left - margin) * scale)
            right = min(w, (right + margin) * scale)
            top = max(0, (top - margin) * scale)
            bottom = min(h, (bottom + margin) * scale)
            
            cropped = img.crop((left, top, right, bottom))
            cropped.save(img_path, "PNG")
            print(f" -> Successfully saved dynamic crop to {img_path.name}")
            return img_path
        except Exception as e:
            print(f" -> Error during dynamic crop of {src_name}: {e}")
            
    return None

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    # Use premium light background
    ax.set_facecolor("#F8FAFC")
    ax.set_xlim(0, 141.42)
    ax.set_ylim(0, 100)
    
    # Draw background architectural grid
    for x in range(5, 140, 5):
        ax.plot([x, x], [0, 100], color='#E2E8F0', linestyle='-', linewidth=0.6, zorder=0, alpha=0.5)
    for y in range(5, 100, 5):
        ax.plot([0, 141.42], [y, y], color='#E2E8F0', linestyle='-', linewidth=0.6, zorder=0, alpha=0.5)
    
    # 1. Main Title & Top Header Card (Spanning full width)
    header_shadow = mpatches.Rectangle((2.3, 88.7), 136.8, 7.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    header_bg = mpatches.Rectangle((2, 89.0), 136.8, 7.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(header_shadow)
    ax.add_patch(header_bg)
    
    # Teal top accent bar on the header card
    accent_bar = mpatches.Rectangle((2, 95.7), 136.8, 0.6, facecolor='#0D9488', edgecolor='none', zorder=3)
    ax.add_patch(accent_bar)
    
    ax.text(3.5, 93.6, "相关上位规划与名城保护解读", 
            color='#0F172A', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=26), zorder=4)
    
    ax.text(3.5, 90.7, "对相关规划进行整理，对场地及周边区域的定位、土地利用规划、蓝绿山水格局、风貌形象定位等方面进行梳理，以指导本次规划设计定位与落地。", 
            color='#334155', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=15.0), zorder=4)

    # 2. UPPER AREA: Three Columns (X: 2.0 to 139.4, Y: 21.5 to 87.8) - Width = 44.0 per col, Gap = 2.7
    cols = [
        # Column 1
        {
            "cx": 24.0, "x_start": 2.0, "x_end": 46.0,
            "filename": "zg_p94_crop.png",
            "title": "国土空间总体格局规划图",
            "box_title": "两轴三带总体格局：",
            "box_desc": "主要发展哈大、珲乌两大发展主轴；依托北部松花江带、中部现代农业带实现生态与城镇的红线管控与功能区划。"
        },
        # Column 2
        {
            "cx": 70.7, "x_start": 48.7, "x_end": 92.7,
            "filename": "zg_p98_crop.png",
            "title": "历史文化保护规划图",
            "box_title": "保护网络与线性活化：",
            "box_desc": "重点推进中东铁路、柳条边遗迹等线性文化遗产保护。落实历史城区、文化街区三级保护管控要求。"
        },
        # Column 3
        {
            "cx": 117.4, "x_start": 95.4, "x_end": 139.4,
            "filename": "zg_p100_crop.png",
            "title": "中心城区空间结构引导图",
            "box_title": "中心城区多组团联动：",
            "box_desc": "构建“一中心、多组团、四板块”结构。突出文创与综合服务能力，以宽城区更新带动北部片区统筹活化。"
        }
    ]

    for col in cols:
        cx_col = col["cx"]
        xs = col["x_start"]
        xe = col["x_end"]
        
        # Column Card Container Shadow & BG (Height = 66.3)
        col_shadow = mpatches.Rectangle((xs + 0.3, 21.2), xe - xs, 66.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
        col_bg = mpatches.Rectangle((xs, 21.5), xe - xs, 66.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
        ax.add_patch(col_shadow)
        ax.add_patch(col_bg)
        
        # Column Card Title Bar Fill
        title_fill = mpatches.Rectangle((xs, 82.0), xe - xs, 5.5, facecolor='#F1F5F9', edgecolor='none', zorder=3)
        ax.add_patch(title_fill)
        
        # Draw Map Title
        ax.text(cx_col, 84.8, col["title"], color='#0F172A', ha='center', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13.5), zorder=4)
        
        # Load and display map (Height box = 44.5, Y: 36.0 to 80.5)
        img_path = check_and_crop_image(col["filename"])
        if img_path and img_path.exists():
            try:
                img = Image.open(img_path)
                ext = get_fit_extent(img.size[0], img.size[1], xs + 1.0, xe - 1.0, 36.0, 80.5)
                ax.imshow(img, extent=ext, zorder=3)
                rect = mpatches.Rectangle((ext[0], ext[2]), ext[1]-ext[0], ext[3]-ext[2], facecolor='none', edgecolor='#CBD5E1', linewidth=1.0, zorder=4)
                ax.add_patch(rect)
            except Exception as e:
                ax.text(cx_col, 58.25, f"[Error: {e}]", ha='center', va='center', zorder=3)
        else:
            ax.text(cx_col, 58.25, "[Map Not Found]", color='#94A3B8', ha='center', va='center', zorder=3)
 
        # Compressed lower green box (Y: 22.5 to 34.5, Height = 12.0)
        desc_bg = mpatches.Rectangle((xs + 1.0, 22.5), (xe - xs) - 2.0, 12.0, facecolor='#F0FDF4', edgecolor='#BBF7D0', linewidth=1.0, zorder=3)
        ax.add_patch(desc_bg)
        
        green_line = mpatches.Rectangle((xs + 1.0, 22.5), 0.8, 12.0, facecolor='#15803D', edgecolor='none', zorder=4)
        ax.add_patch(green_line)
        
        # Write wrapped text inside description box
        ax.text(xs + 2.5, 32.2, col["box_title"], color='#15803D', ha='left', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=14.0), zorder=4)
        
        wrapped_desc = wrap_text(col["box_desc"], max_len=56)
        y_text = 29.5
        for line in wrapped_desc.split('\n'):
            ax.text(xs + 2.5, y_text, line, color='#334155', ha='left', va='center',
                    fontproperties=fm.FontProperties(family=font_prop['family'], size=12.5), zorder=4)
            y_text -= 3.0

    # 3. BOTTOM-LEFT: Horizontal Flowchart Card (X: 2.0 to 70.0, Y: 4.0 to 20.0)
    mind_shadow = mpatches.Rectangle((2.3, 3.7), 68.0, 16.0, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    mind_bg = mpatches.Rectangle((2.0, 4.0), 68.0, 16.0, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(mind_shadow)
    ax.add_patch(mind_bg)
    ax.add_patch(mpatches.Rectangle((2.0, 18.5), 68.0, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(3.5, 17.0, "规划传导与政策演进逻辑 / POLICY TRANSMISSION MINDMAP", color='#D97706', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=16.0), zorder=4)
    
    # Draw flowchart elements horizontally with source-control-response notes.
    nodes = [
        (
            "国家战略：城市更新",
            14.8,
            '#EF4444',
            '#FEE2E2',
            '#EF4444',
            "约束：存量提质 / 补短板",
            "响应：数字治理 + 微更新",
        ),
        (
            "名城保护：格局传导",
            36.0,
            '#3B82F6',
            '#DBEAFE',
            '#3B82F6',
            "约束：历史城区三级保护",
            "响应：视廊延续 + 风貌协调",
        ),
        (
            "街区细则：刚性管控",
            57.2,
            '#10B981',
            '#D1FAE5',
            '#10B981',
            "约束：核心区 / 建控区边界",
            "响应：限高 + 分类整治",
        ),
    ]
    for name, nx, border_color, fill_color, text_color, constraint, response in nodes:
        n_shadow = mpatches.Rectangle((nx - 8.2 + 0.2, 7.6), 16.4, 6.6, facecolor='#E2E8F0', edgecolor='none', zorder=3)
        n_bg = mpatches.Rectangle((nx - 8.2, 7.8), 16.4, 6.6, facecolor=fill_color, edgecolor=border_color, linewidth=1.0, zorder=4)
        ax.add_patch(n_shadow)
        ax.add_patch(n_bg)
        ax.text(nx, 12.6, name, color=text_color, ha='center', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=11.5), zorder=5)
        ax.plot([nx - 7.0, nx + 7.0], [11.2, 11.2], color=border_color, linewidth=0.7, alpha=0.35, zorder=5)
        ax.text(nx, 10.2, constraint, color='#334155', ha='center', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], size=9.0), zorder=5)
        ax.text(nx, 8.9, response, color='#334155', ha='center', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], size=9.0), zorder=5)

    # Draw horizontal connection arrows
    ax.annotate("", xy=(27.3, 11.0), xytext=(23.2, 11.0),
                arrowprops=dict(arrowstyle="->", color='#64748B', lw=1.5), zorder=4)
    ax.annotate("", xy=(49.2, 11.0), xytext=(44.5, 11.0),
                arrowprops=dict(arrowstyle="->", color='#64748B', lw=1.5), zorder=4)

    # 4. BOTTOM-RIGHT: Horizontal Design Brief Card (X: 71.5 to 139.4, Y: 4.0 to 20.0)
    stamp_shadow = mpatches.Rectangle((71.8, 3.7), 67.9, 16.0, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    stamp_bg = mpatches.Rectangle((71.5, 4.0), 67.9, 16.0, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(stamp_shadow)
    ax.add_patch(stamp_bg)
    ax.add_patch(mpatches.Rectangle((71.5, 18.5), 67.9, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(73.0, 17.0, "设计说明与分析 / DESIGN BRIEF", color='#D97706', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=16.0), zorder=4)
    
    # 3 compact note cards: source, control, response.
    brief_cards = [
        (
            73.0,
            "依据来源",
            "总规“两轴三带”\n名城保护体系\n中心城区结构引导",
            '#EEF2FF',
            '#4F46E5',
        ),
        (
            95.0,
            "控制要求",
            "生态与城镇边界\n历史城区分级保护\n街区风貌与视廊管控",
            '#F0FDF4',
            '#15803D',
        ),
        (
            117.0,
            "设计响应",
            "站城联动轴线\n遗产活化游线\n低影响微更新策略",
            '#FFF7ED',
            '#C2410C',
        ),
    ]
    for x0, title, body, fill_color, accent_color in brief_cards:
        b_shadow = mpatches.Rectangle((x0 + 0.2, 5.1), 20.0, 9.8, facecolor='#E2E8F0', edgecolor='none', zorder=3)
        b_bg = mpatches.Rectangle((x0, 5.3), 20.0, 9.8, facecolor=fill_color, edgecolor='#CBD5E1', linewidth=0.8, zorder=4)
        ax.add_patch(b_shadow)
        ax.add_patch(b_bg)
        ax.add_patch(mpatches.Rectangle((x0, 5.3), 0.6, 9.8, facecolor=accent_color, edgecolor='none', zorder=5))
        ax.text(x0 + 1.4, 13.2, title, color=accent_color, ha='left', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=12.5), zorder=5)
        ax.text(x0 + 1.4, 10.6, body, color='#334155', ha='left', va='top',
                fontproperties=fm.FontProperties(family=font_prop['family'], size=11.0), zorder=5)

legend_items = []

description_lines = [
    "1. 依据来源：以长春市国土空间总体规划“两轴三带、多射线”、名城保护体系与中心城区结构引导为上位依据，明确片区更新的战略坐标。",
    "2. 控制要求：落实生态与城镇边界、历史城区分级保护、线性文化遗产保护以及街区风貌视廊管控，形成刚性底线与弹性更新并行的传导框架。",
    "3. 设计响应：将上位规划要求转译为站城联动轴线、遗产活化游线、风貌协调界面和低影响微更新策略，支撑后续总体城市设计落地。"
]
