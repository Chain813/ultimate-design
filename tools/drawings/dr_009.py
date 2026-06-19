# -*- coding: utf-8 -*-
"""DR-009 案例借鉴与对标分析图"""
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
        w = box_w
        h = w / img_ar
    else:
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
    
    # 1. Main Title & Top Header Card
    header_shadow = mpatches.Rectangle((2.3, 88.7), 136.8, 7.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    header_bg = mpatches.Rectangle((2, 89.0), 136.8, 7.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(header_shadow)
    ax.add_patch(header_bg)
    
    # Teal top accent bar on the header card
    accent_bar = mpatches.Rectangle((2, 95.7), 136.8, 0.6, facecolor='#0D9488', edgecolor='none', zorder=3)
    ax.add_patch(accent_bar)
    
    ax.text(3.5, 93.6, "国内外相关案例借鉴与对标分析", 
            color='#0F172A', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=26), zorder=4)
    
    ax.text(3.5, 90.7, "梳理国内外在历史街区微更新、数字化治理、工业遗产活化及慢行系统重构等领域的典型案例，总结其核心理念与技术方法，以指导本次规划设计定位与落地。", 
            color='#334155', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=15.0), zorder=4)

    # 2. UPPER AREA: Four Columns (X: 2.0 to 139.4, Y: 21.5 to 87.8) - Width = 32.0 per col, Gap = 3.14
    cols = [
        {
            "cx": 18.0, "x_start": 2.0, "x_end": 34.0,
            "filename": "case_yongqingfang.jpeg",
            "title": "广州永庆坊微更新",
            "box_title": "微改造与有机更新：",
            "box_desc": "采用“绣花功夫”织补肌理，在保留历史风貌与原有街巷格局的同时，植入文创与特色餐饮，强调社会协同与可持续活力触媒激发。"
        },
        {
            "cx": 53.14, "x_start": 37.14, "x_end": 69.14,
            "filename": "case_baitasi.jpeg",
            "title": "北京白塔寺数字织补",
            "box_title": "数据驱动与数字织补：",
            "box_desc": "深度应用多源数据评估，对院落微气候与交通慢行流线进行科学模拟以指导基础设施现代化升级，并搭建高效的公众参与决策平台。"
        },
        {
            "cx": 88.28, "x_start": 72.28, "x_end": 104.28,
            "filename": "case_kingscross.jpeg",
            "title": "伦敦国王十字街区更新",
            "box_title": "遗产活化与站城联动：",
            "box_desc": "保留维多利亚铁路及工业建筑遗存并进行功能置换；重构“小街区、密路网”步行交通，促进TOD势能向街区活力的高效转化。"
        },
        {
            "cx": 123.42, "x_start": 107.42, "x_end": 139.42,
            "filename": "case_superblock.jpeg",
            "title": "巴塞罗那超级街区",
            "box_title": "交通重塑与慢行主导：",
            "box_desc": "借助数字化流量与空间句法模型限制外围过境车行，释放街区内部多余车道为慢行与绿化口袋空间，重建社区交往与邻里活力场所。"
        }
    ]

    for col in cols:
        cx_col = col["cx"]
        xs = col["x_start"]
        xe = col["x_end"]
        
        # Column Card Container Shadow & BG (Height = 67.8, Y: 20.0 to 87.8)
        col_shadow = mpatches.Rectangle((xs + 0.3, 19.7), xe - xs, 67.8, facecolor='#E2E8F0', edgecolor='none', zorder=1)
        col_bg = mpatches.Rectangle((xs, 20.0), xe - xs, 67.8, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
        ax.add_patch(col_shadow)
        ax.add_patch(col_bg)
        
        # Column Card Title Bar Fill
        title_fill = mpatches.Rectangle((xs, 82.0), xe - xs, 5.5, facecolor='#F1F5F9', edgecolor='none', zorder=3)
        ax.add_patch(title_fill)
        
        # Draw Map Title
        ax.text(cx_col, 84.8, col["title"], color='#0F172A', ha='center', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13.5), zorder=4)
        
        # Load and display map (Height box = 44.5, Y: 36.0 to 80.5)
        img_path = STATIC_DIR / "extracted_images" / col["filename"]
        if img_path.exists():
            try:
                img = Image.open(img_path)
                ext = get_fit_extent(img.size[0], img.size[1], xs + 1.0, xe - 1.0, 36.0, 80.5)
                ax.imshow(img, extent=ext, zorder=3)
                rect = mpatches.Rectangle((ext[0], ext[2]), ext[1]-ext[0], ext[3]-ext[2], facecolor='none', edgecolor='#CBD5E1', linewidth=1.0, zorder=4)
                ax.add_patch(rect)
            except Exception as e:
                ax.text(cx_col, 58.25, f"[Error: {e}]", ha='center', va='center', zorder=3)
        else:
            ax.text(cx_col, 58.25, "[Image Not Found]", color='#94A3B8', ha='center', va='center', zorder=3)
  
        # Expanded lower green box (Y: 20.5 to 34.5, Height = 14.0)
        desc_bg = mpatches.Rectangle((xs + 1.0, 20.5), (xe - xs) - 2.0, 14.0, facecolor='#F0FDF4', edgecolor='#BBF7D0', linewidth=1.0, zorder=3)
        ax.add_patch(desc_bg)
        
        green_line = mpatches.Rectangle((xs + 1.0, 20.5), 0.8, 14.0, facecolor='#15803D', edgecolor='none', zorder=4)
        ax.add_patch(green_line)
        
        # Write wrapped text inside description box
        ax.text(xs + 2.5, 32.7, col["box_title"], color='#15803D', ha='left', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=14.0), zorder=4)
        
        wrapped_desc = wrap_text(col["box_desc"], max_len=44)
        y_text = 29.8
        for line in wrapped_desc.split('\n'):
            ax.text(xs + 2.5, y_text, line, color='#334155', ha='left', va='center',
                    fontproperties=fm.FontProperties(family=font_prop['family'], size=12.5), zorder=4)
            y_text -= 2.7

    # 3. BOTTOM-LEFT: Horizontal Flowchart Card (X: 2.0 to 70.0, Y: 4.0 to 20.0)
    mind_shadow = mpatches.Rectangle((2.3, 3.7), 68.0, 16.0, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    mind_bg = mpatches.Rectangle((2.0, 4.0), 68.0, 16.0, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(mind_shadow)
    ax.add_patch(mind_bg)
    ax.add_patch(mpatches.Rectangle((2.0, 18.5), 68.0, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(3.5, 17.0, "案例价值转译与设计导引逻辑 / CASE VALUE TRANSLATION LOGIC", color='#D97706', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=18.0), zorder=4)
    
    # Draw flowchart elements horizontally with source-control-response notes.
    nodes = [
        (
            "“微改造”分类施策",
            14.8,
            '#EF4444',
            '#FEE2E2',
            '#EF4444',
            "要求：延续肌理与风貌原真性",
            "响应：分类保护整治+织补空间",
        ),
        (
            "“数据孪生”精准诊断",
            36.0,
            '#3B82F6',
            '#DBEAFE',
            '#3B82F6',
            "要求：微气候与多维精准量化",
            "响应：GIS叠合语义分割感知",
        ),
        (
            "“站城联动”活力缝合",
            57.2,
            '#10B981',
            '#D1FAE5',
            '#10B981',
            "要求：工业遗产活化与站城交通",
            "响应：TOD小路网慢行系统缝合",
        ),
    ]
    for name, nx, border_color, fill_color, text_color, constraint, response in nodes:
        n_shadow = mpatches.Rectangle((nx - 8.2 + 0.2, 7.3), 16.4, 7.2, facecolor='#E2E8F0', edgecolor='none', zorder=3)
        n_bg = mpatches.Rectangle((nx - 8.2, 7.5), 16.4, 7.2, facecolor=fill_color, edgecolor=border_color, linewidth=1.0, zorder=4)
        ax.add_patch(n_shadow)
        ax.add_patch(n_bg)
        ax.text(nx, 13.1, name, color=text_color, ha='center', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=14.0), zorder=5)
        ax.plot([nx - 7.0, nx + 7.0], [11.5, 11.5], color=border_color, linewidth=0.7, alpha=0.35, zorder=5)
        ax.text(nx, 10.3, constraint, color='#334155', ha='center', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], size=11.5), zorder=5)
        ax.text(nx, 9.0, response, color='#334155', ha='center', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], size=11.5), zorder=5)

    # Draw connection arrows
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
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=18.0), zorder=4)
    
    # 3 compact note cards: source, control, response.
    brief_cards = [
        (
            73.0,
            "功能织补",
            "腾退低效空置厂区\n植入多元创意产业\n提升土地空间效益",
            '#EEF2FF',
            '#4F46E5',
        ),
        (
            95.0,
            "数智赋能",
            "GIS与AI联合感知\n模拟人流交通流线\n构建数字孪生镜像",
            '#F0FDF4',
            '#15803D',
        ),
        (
            117.0,
            "站城共振",
            "重构小街区密路网\n缝合铁路隔断交通\n激发老城复兴活力",
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
        ax.text(x0 + 1.4, 13.5, title, color=accent_color, ha='left', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=15.0), zorder=5)
        ax.text(x0 + 1.4, 10.8, body, color='#334155', ha='left', va='top',
                fontproperties=fm.FontProperties(family=font_prop['family'], size=13.0), zorder=5)

legend_items = []

description_lines = [
    "1. 案例借鉴：借鉴广州永庆坊的微更新织补、北京白塔寺的数字织补、伦敦国王十字的工业遗产活化与站城联动、巴塞罗那的超级街区慢行重构，提炼普适化方法。",
    "2. 刚性与弹性控制：既要严守风貌原真性、历史红线和生态底线，又要利用AI大模型与数据计算对更新策划方案的包容性进行弹性评判与引导。",
    "3. 设计转译：将案例的先进理念在伪满皇宫周边进行本地化转译，推进“数字孪生·古今共振”主题的实效性落地。"
]
