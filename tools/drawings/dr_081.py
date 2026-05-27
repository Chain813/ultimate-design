# -*- coding: utf-8 -*-
from shapely.geometry import Point
import pandas as pd
import numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"
GIS_DIR = ROOT / "data/gis"
ASSETS_DIR = ROOT / "assets"

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patheffects as path_effects
import geopandas as gpd
from PIL import Image

def draw_map_early(output_path, view_w, view_h, STATIC_DIR):
    mindmap_path = STATIC_DIR / "system_architecture_mindmap.png"
    if mindmap_path.exists():
        try:
            mindmap_img = Image.open(mindmap_path)
            mw, mh = mindmap_img.size

            # Crop title banner and bottom padding
            # Header is at y=0..80, content is y=110..880. We crop [50, 82, 1870, 900]
            cropped_img = mindmap_img.crop((50, 82, 1870, 900))
            cw = 1870 - 50
            ch = 900 - 82

            # Scale to fit inside 1705x1369 proportionally
            new_w = 1705
            new_h = int(new_w * ch / cw) # 766

            mindmap_resized = cropped_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Create white background canvas
            bg = Image.new("RGB", (1705, 1369), color=(255, 255, 255))
            px = (1705 - new_w) // 2
            py = (1369 - new_h) // 2
            bg.paste(mindmap_resized, (px, py))

            bg.save(output_path)
            print(f"Directly loaded system architecture mindmap and saved to {output_path}")
            return view_w
        except Exception as e:
            print(f"Error loading system architecture mindmap: {e}")
    return None

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    # Renders a neat digital flowchart inside the primary map area
    ax.set_facecolor("#0F172A") # Dark cyberpunk feel
    # Draw clean flowchart nodes on ax
    nodes = [
        ("多源数据底盘", "GIS、POI、路网、建筑轮廓", 0.15, 0.75, "#38BDF8"),
        ("AI定量化诊断", "空间句法、GVI识别、情感分析", 0.50, 0.75, "#2DD4BF"),
        ("AIGC方案推演", "Stable Diffusion + ControlNet", 0.85, 0.75, "#A855F7"),
        ("多元协同决策", "LLM智能代理模拟多利益主体协商", 0.50, 0.25, "#F43F5E"),
        ("成果智能出图", "A3规划图册与导则Word一键导出", 0.85, 0.25, "#10B981")
    ]

    # Calculate coordinate boundaries
    xmin, xmax = cx - view_w / 2, cx + view_w / 2
    ymin, ymax = cy - view_h / 2, cy + view_h / 2

    # Background fill
    ax.axhspan(ymin, ymax, facecolor='#0F172A', zorder=0)

    # Draw connections and arrows
    def draw_arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color="#94A3B8", lw=3, alpha=0.8), zorder=1)

    # Draw connection lines
    px1, py1 = xmin + 0.15*(xmax-xmin), ymin + 0.75*(ymax-ymin)
    px2, py2 = xmin + 0.50*(xmax-xmin), ymin + 0.75*(ymax-ymin)
    px3, py3 = xmin + 0.85*(xmax-xmin), ymin + 0.75*(ymax-ymin)
    px4, py4 = xmin + 0.50*(xmax-xmin), ymin + 0.25*(ymax-ymin)
    px5, py5 = xmin + 0.85*(xmax-xmin), ymin + 0.25*(ymax-ymin)

    draw_arrow(px1, py1, px2, py2)
    draw_arrow(px2, py2, px3, py3)
    draw_arrow(px2, py2, px4, py4)
    draw_arrow(px3, py3, px5, py5)
    draw_arrow(px4, py4, px5, py5)

    for name, sub, rx, ry, col in nodes:
        nx_c = xmin + rx * (xmax - xmin)
        ny_c = ymin + ry * (ymax - ymin)

        # draw box
        box_w = (xmax - xmin) * 0.25
        box_h = (ymax - ymin) * 0.16
        rect = plt.Rectangle((nx_c - box_w/2, ny_c - box_h/2), box_w, box_h, 
                             facecolor="#1E293B", edgecolor=col, linewidth=2.5, zorder=2)
        ax.add_patch(rect)

        ax.text(nx_c, ny_c + box_h/5, name, color=col, ha='center', va='center', fontsize=16, fontweight='bold', zorder=3, fontproperties=fm.FontProperties(family=font_prop['family'], weight='bold', size=16))
        ax.text(nx_c, ny_c - box_h/6, sub, color='#E2E8F0', ha='center', va='center', fontsize=11, zorder=3, fontproperties=fm.FontProperties(family=font_prop['family'], size=11))

legend_items = []

legend_explanation = [
    ("【数据底盘】", "整合多源城市空间矢量与非结构化社交文本，提供精准的空间病征和痛点坐标定位。"),
    ("【定量诊断】", "运行空间句法与街景分割算法，实现步行可达性与街道绿视率的自动化精准度量。"),
    ("【方案生成】", "结合Stable Diffusion与ControlNet深度学习模型，输入意向草图自动生成设计效果。"),
    ("【协同决策】", "利用大语言模型（LLM）智能体模拟各利益相关方诉求，实现方案的多指标评估与闭环优化。")
]

description_lines = [
    "1. 数据底座：利用多源 GIS 空间图层与高分辨率街景图像建立数字底盘，通过 NLP 挖掘微博/小红书情感，诊断品质痛点。",
    "2. AIGC 生成：利用 Stable Diffusion 算法配合 ControlNet 控制网，输入手绘线稿、空间意向与提示词，自动推演 100+ 方案。",
    "3. 智能协商：通过 LLM 智能体模拟政府、专家、居民与开发商进行决策协商，综合评选最优方案，实现全链条数字化辅助。"
]