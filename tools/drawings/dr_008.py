"""DR-008 上位专项规划解读图 — 对应答辩稿 3.1 上位专项规划"""
from pathlib import Path

import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
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
    
    ax.text(3.5, 93.6, "相关上位专项规划解读", 
            color='#0F172A', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=26), zorder=4)
    
    ax.text(3.5, 90.7, "对中心城区土地利用规划、综合交通系统规划与绿地系统规划等上位专项规划进行深度整理与分析，以指导片区的功能置换、交通缝合与蓝绿生态织补设计。", 
            color='#334155', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=15.0), zorder=4)

    # 2. UPPER AREA: Three Columns (X: 2.0 to 139.4, Y: 21.5 to 87.8) - Width = 44.0 per col, Gap = 2.7
    cols = [
        # Column 1
        {
            "cx": 24.0, "x_start": 2.0, "x_end": 46.0,
            "filename": "zg_p95_crop.png",
            "title": "中心城区土地利用规划图",
            "box_title": "功能优化与用途管制：",
            "box_desc": "以空间管控、集约高效为导向，促进存量用地的二次开发；引导公共资源向轨道站点聚集，提高土地复合效益。"
        },
        # Column 2
        {
            "cx": 70.7, "x_start": 48.7, "x_end": 92.7,
            "filename": "zg_p96_crop.png",
            "title": "中心城区综合交通规划图",
            "box_title": "互联互通多网融合：",
            "box_desc": "依托快速路与主要干道，建立连通内外、网络完备的综合交通体系；强化跨铁节点联系，打破铁路的空间割裂。"
        },
        # Column 3
        {
            "cx": 117.4, "x_start": 95.4, "x_end": 139.4,
            "filename": "zg_p102_crop.png",
            "title": "中心城区绿地系统规划图",
            "box_title": "楔向引入生态织补：",
            "box_desc": "依托伊通河、东干渠等生态走廊，将绿意楔向引入核心街区；建立均质分布的公园绿地网络，提升微气候环境。"
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
    
    ax.text(3.5, 17.0, "专项规划融合与传导逻辑 / SPECIAL PLANNING TRANSMISSION MINDMAP", color='#D97706', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=16.0), zorder=4)
    
    # Draw flowchart elements horizontally with source-control-response notes.
    nodes = [
        (
            "用地管制：功能置换",
            14.8,
            '#3B82F6',
            '#DBEAFE',
            '#3B82F6',
            "约束：严守建设用地总量红线",
            "响应：商业文创主导+混合用地",
        ),
        (
            "交通缝合：TOD导向",
            36.0,
            '#EF4444',
            '#FEE2E2',
            '#EF4444',
            "约束：站点接驳与线网接入",
            "响应：慢行优先+共享单车接驳",
        ),
        (
            "生态基底：蓝绿织补",
            57.2,
            '#10B981',
            '#D1FAE5',
            '#10B981',
            "约束：绿地红线与沿河廊道",
            "响应：口袋公园+生态廊道贯通",
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
    
    brief_cards = [
        (
            73.0,
            "功能置换",
            "腾退低效仓储用地\n置换为商旅文创\n提高土地复合效益",
            '#EEF2FF',
            '#4F46E5',
        ),
        (
            95.0,
            "交通缝合",
            "增设跨铁高架/地道\n打通微循环断头路\n实现站城无缝衔接",
            '#F0FDF4',
            '#15803D',
        ),
        (
            117.0,
            "蓝绿网格",
            "织补袖珍口袋公园\n打通慢行生态游廊\n形成均质开敞空间",
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
    "1. 用地管制：落实总体规划中中心城区用地管制要求，腾退低效工业仓储地块，置换商旅文创功能，提升土地集约度和复合利用绩效。",
    "2. 交通缝合：衔接中心城区综合交通网络，通过跨铁高架、立交节点和站点TOD接驳，打破铁路空间阻隔，构建内外通达的道路系统。",
    "3. 蓝绿织补：衔接中心城区绿地系统网络，构建伊通河生态廊道与城市公园构成的蓝绿微循环系统，提升街区的生态微气候与环境品质。"
]
