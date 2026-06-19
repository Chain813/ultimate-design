# -*- coding: utf-8 -*-
"""DR-003 项目背景与政策解读图 — 对应答辩稿 1.1 项目背景"""
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

def wrap_text(text, max_len=20):
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
            if current_w + w <= 20:
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

    # 1. Main Title and Subtitle Area (Spanning full width)
    header_shadow = mpatches.Rectangle((2.3, 88.7), 136.8, 7.3, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    header_bg = mpatches.Rectangle((2, 89.0), 136.8, 7.3, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(header_shadow)
    ax.add_patch(header_bg)
    
    ax.text(3.5, 93.6, "相关规划与设计整理", 
            color='#0F172A', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=26), zorder=3)
    
    ax.text(3.5, 90.7, "对相关规划进行整理，对场地及周边区域的定位、土地利用规划、蓝绿山水格局、风貌形象定位等方面进行梳理，以指导本次规划设计定位与落地。", 
            color='#475569', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=15.0), zorder=3)

    # 2. Left Column Mindmap/Knowledge Graph Card (X: 1.5 to 21.5, Y: 4.0 to 87.8)
    mind_shadow = mpatches.Rectangle((1.8, 3.7), 20.0, 83.8, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    mind_bg = mpatches.Rectangle((1.5, 4.0), 20.0, 83.8, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(mind_shadow)
    ax.add_patch(mind_bg)
    ax.add_patch(mpatches.Rectangle((1.5, 86.3), 20.0, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(3.0, 84.0, "规划传导与政策演进逻辑", color='#D97706', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=14.0), zorder=4)
    ax.text(3.0, 81.3, "POLICY TRANSMISSION MINDMAP", color='#94A3B8', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.0), zorder=4)
    
    # Draw flowchart elements stacked vertically with denser policy transmission notes
    nodes = [
        (
            "国家战略：城市更新",
            64.0,
            '#EF4444',
            '#FEE2E2',
            '#EF4444',
            "约束：存量提质 / 补齐民生短板",
            "传导：公共空间织补 + 数字治理",
        ),
        (
            "名城保护：格局传导",
            41.0,
            '#3B82F6',
            '#DBEAFE',
            '#3B82F6',
            "约束：历史城区-街区-文物点管控",
            "传导：中轴视廊延续 + 风貌协调",
        ),
        (
            "街区细则：刚性管控",
            18.0,
            '#10B981',
            '#D1FAE5',
            '#10B981',
            "约束：核心区13.55ha / 建控11.5ha",
            "传导：限高9-18m + 分类修缮整治",
        ),
    ]
    for name, ny_bottom, border_color, fill_color, text_color, constraint, response in nodes:
        n_shadow = mpatches.Rectangle((3.2, ny_bottom - 0.2), 16.6, 11.2, facecolor='#E2E8F0', edgecolor='none', zorder=3)
        n_bg = mpatches.Rectangle((3.0, ny_bottom), 16.6, 11.2, facecolor=fill_color, edgecolor=border_color, linewidth=1.0, zorder=4)
        ax.add_patch(n_shadow)
        ax.add_patch(n_bg)
        ax.text(11.3, ny_bottom + 8.6, name, color=text_color, ha='center', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=11.4), zorder=5)
        ax.plot([4.0, 18.6], [ny_bottom + 6.6, ny_bottom + 6.6], color=border_color, linewidth=0.8, alpha=0.35, zorder=5)
        ax.text(11.3, ny_bottom + 4.6, constraint, color='#334155', ha='center', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], size=8.4), zorder=5)
        ax.text(11.3, ny_bottom + 2.5, response, color='#334155', ha='center', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], size=8.4), zorder=5)

    # Draw vertical connection arrows
    ax.annotate("", xy=(11.3, 53.0), xytext=(11.3, 62.7),
                arrowprops=dict(arrowstyle="->", color='#64748B', lw=1.5), zorder=4)
    ax.annotate("", xy=(11.3, 30.0), xytext=(11.3, 39.7),
                arrowprops=dict(arrowstyle="->", color='#64748B', lw=1.5), zorder=4)

    # 3. TOP OF CENTRAL AREA: 要点图组 — 横向的一行四张图 (Y-axis height compressed to 33.5 to leave room for bottom maps)
    c3_shadow = mpatches.Rectangle((23.3, 53.7), 95.0, 33.8, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    c3_bg = mpatches.Rectangle((23.0, 54.0), 95.0, 33.8, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(c3_shadow)
    ax.add_patch(c3_bg)
    
    # 4 maps in 1 horizontal row
    top_maps = [
        {
            "filename": "weiman_p12_crop.png", 
            "x1": 24.5, "x2": 46.5, 
            "title": "03 历史资源分布图 (文保单位14处)"
        },
        {
            "filename": "weiman_p13_crop.png", 
            "x1": 48.0, "x2": 70.0, 
            "title": "05 保护区划图 (核心区13.55ha/建控区11.5ha)"
        },
        {
            "filename": "weiman_p14_crop.png", 
            "x1": 71.5, "x2": 93.5, 
            "title": "06 建筑高度控制图 (新建限高18m/视廊限高9m)"
        },
        {
            "filename": "weiman_p15_crop.png", 
            "x1": 95.0, "x2": 117.0, 
            "title": "07 建筑保护与整治图 (修缮类占比85%)"
        }
    ]
    
    for item in top_maps:
        filename = item["filename"]
        x1, x2 = item["x1"], item["x2"]
        cx_cell = (x1 + x2) / 2
        
        # Display Map with Fit (preserving ~1.6 aspect ratio)
        img_path = STATIC_DIR / "extracted_images" / filename
        if img_path.exists():
            try:
                img = Image.open(img_path)
                ext = get_fit_extent(img.size[0], img.size[1], x1, x2, 59.0, 81.5)
                ax.imshow(img, extent=ext, zorder=3)
                rect = mpatches.Rectangle((ext[0], ext[2]), ext[1]-ext[0], ext[3]-ext[2], facecolor='none', edgecolor='#CBD5E1', linewidth=1.0, zorder=4)
                ax.add_patch(rect)
            except Exception as e:
                ax.text(cx_cell, 70.25, f"[Error: {e}]", ha='center', va='center', zorder=3)
        else:
            ax.text(cx_cell, 70.25, "[Not Found]", color='#94A3B8', ha='center', va='center', zorder=3)
            
        ax.text(cx_cell, 57.2, item["title"], color='#0F172A', ha='center', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=10.9), zorder=4)
        
    ax.text(70.5, 84.8, "《长春市伪满皇宫历史文化街区保护规划》要点图组", color='#0F172A', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=15.0), zorder=4)

    # 4. BOTTOM-LEFT OF CENTRAL AREA: 格局图 (X: 23.0 to 77.5, Y: 4.0 to 52.5) - ENLARGED in both width and height!
    c1_shadow = mpatches.Rectangle((23.3, 3.7), 54.5, 48.5, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    c1_bg = mpatches.Rectangle((23.0, 4.0), 54.5, 48.5, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(c1_shadow)
    ax.add_patch(c1_bg)

    # Large Center Map: zg_p94_crop (X: 23.0 to 77.5, Y: 4.0 to 52.5)
    img_p94_path = STATIC_DIR / "extracted_images" / "zg_p94_crop.png"
    if img_p94_path.exists():
        try:
            img = Image.open(img_p94_path)
            # Center of box X is (23.0 + 77.5)/2 = 50.25
            ext = get_fit_extent(img.size[0], img.size[1], 24.0, 76.5, 9.0, 51.0)
            ax.imshow(img, extent=ext, zorder=3)
            rect = mpatches.Rectangle((ext[0], ext[2]), ext[1]-ext[0], ext[3]-ext[2], facecolor='none', edgecolor='#CBD5E1', linewidth=1.2, zorder=4)
            ax.add_patch(rect)
        except Exception as e:
            ax.text(50.25, 30.0, f"[Error: {e}]", ha='center', va='center', zorder=3)
    else:
        ax.text(50.25, 30.0, "[Not Found]", color='#94A3B8', ha='center', va='center', zorder=3)
        
    ax.text(50.25, 6.0, "《长春市国土空间总体规划（2021—2035年）》格局图", color='#0F172A', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13.5), zorder=4)

    # 5. BOTTOM-RIGHT OF CENTRAL AREA: 表格 (X: 79.5 to 118.0, Y: 4.0 to 52.5) - COMPRESSED in width to fit expanded map!
    table_shadow = mpatches.Rectangle((79.8, 3.7), 38.5, 48.5, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    ax.add_patch(table_shadow)
    table_bg = mpatches.Rectangle((79.5, 4.0), 38.5, 48.5, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(table_bg)
    
    # Table Header background
    t_header_bg = mpatches.Rectangle((79.5, 48.5), 38.5, 4.0, facecolor='#1E293B', edgecolor='none', zorder=3)
    ax.add_patch(t_header_bg)
    
    # Header texts
    ax.text(85.0, 50.5, "规划类别", color='#FFFFFF', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13.5), zorder=4)
    ax.text(104.25, 50.5, "规划名称及主要依据文件", color='#FFFFFF', ha='center', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=13.5), zorder=4)
    
    # Table grid lines
    ax.plot([90.5, 90.5], [4.0, 52.5], color='#E2E8F0', linewidth=1.0, zorder=3)
    y_lines = [48.5, 41.1, 33.7, 26.3, 18.9, 11.5]
    for y in y_lines:
        ax.plot([79.5, 118.0], [y, y], color='#E2E8F0', linewidth=1.0, zorder=3)
        
    # Table Content (Wrap detail text to 20 Chinese characters per line)
    rows = [
        (44.8, "国土空间总体规划", "《长春市国土空间总体规划（2021—2035年）》"),
        (37.4, "历史文化保护规划", "《长春历史文化名城保护规划（2021—2035年）》\n《长春市历史文化名城保护条例》及《实施办法》"),
        (30.0, "历史文化街区规划", "《伪满皇宫历史文化街区保护规划（2023—2035年）》"),
        (22.6, "交通类专项规划", "《长春市综合交通体系规划》\n《长春市慢行交通系统规划》"),
        (15.2, "绿地空间专项规划", "《长春市绿地系统规划》"),
        (7.75, "相关城市设计与更新", "《伪满皇宫周边区域城市更新重点指导意见建议》\n《宽城区城市更新三年行动计划（2023—2025年）》")
    ]
    
    for idx, (y_center, cat, name) in enumerate(rows):
        if idx % 2 == 1:
            y_top = y_lines[idx]
            y_bot = 4.0 if idx == 5 else y_lines[idx+1]
            row_bg = mpatches.Rectangle((79.5, y_bot), 38.5, y_top - y_bot, facecolor='#F8FAFC', edgecolor='none', zorder=2)
            ax.add_patch(row_bg)

        # Wrap details text to 20 characters
        wrapped_name = wrap_text(name, max_len=20)

        ax.text(85.0, y_center, cat, color='#334155', ha='center', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=12.5), zorder=4)
        ax.text(92.0, y_center, wrapped_name, color='#334155', ha='left', va='center',
                fontproperties=fm.FontProperties(family=font_prop['family'], size=11.5), zorder=4)

    # 6. Right Column Design说明 Card (X: 119.5 to 139.9, Y: 4.0 to 87.8) - Stretched text height!
    stamp_shadow = mpatches.Rectangle((119.8, 3.7), 20.4, 83.8, facecolor='#E2E8F0', edgecolor='none', zorder=1)
    stamp_bg = mpatches.Rectangle((119.5, 4.0), 20.4, 83.8, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(stamp_shadow)
    ax.add_patch(stamp_bg)
    ax.add_patch(mpatches.Rectangle((119.5, 86.3), 20.4, 1.5, facecolor='#D97706', edgecolor='none', zorder=3))
    
    ax.text(121.0, 84.0, "设计说明与分析", color='#D97706', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=14.0), zorder=4)
    ax.text(121.0, 81.5, "DESIGN BRIEF", color='#94A3B8', ha='left', va='center',
            fontproperties=fm.FontProperties(family=font_prop['family'], size=10.0), zorder=4)
    
    # 3 bullet lines of description with denser source-control-response structure.
    desc_lines_to_draw = [
        ("1. 依据来源：\n   整合国土空间总规、名城\n   保护规划与街区保护规划，\n   明确历史文化核心区定位。", 74.0),
        ("2. 控制要求：\n   落实核心区13.55ha、建控区\n   11.5ha边界，执行9-18m\n   限高、视廊与风貌管控。", 49.0),
        ("3. 设计响应：\n   以保留修缮、整治提升和\n   微更新织补组织实施路径，\n   衔接公共空间与慢行系统。", 24.0)
    ]
    for text, y_pos in desc_lines_to_draw:
        ax.text(121.0, y_pos, text, color='#334155', ha='left', va='top',
                fontproperties=fm.FontProperties(family=font_prop['family'], size=13.5), zorder=4)

legend_items = []

description_lines = [
    "1. 依据来源：整合《长春市国土空间总体规划（2021—2035年）》、名城保护规划与《伪满皇宫历史文化街区保护规划》，明确片区历史文化核心区定位。",
    "2. 控制要求：落实保护规划中的核心区13.55ha、建设控制区11.5ha边界，执行9—18m限高、重要视线廊道与建筑风貌分类管控。",
    "3. 设计响应：以保留修缮、整治提升和微更新织补组织实施路径，将政策约束转译为空间结构、公共空间、慢行系统与建筑整治策略。"
]
