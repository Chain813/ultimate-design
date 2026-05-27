# -*- coding: utf-8 -*-
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"

def draw_map_early(output_path, view_w, view_h, STATIC_DIR):
    img_path = STATIC_DIR / "data_pipeline_mindmap.png"
    if img_path.exists():
        try:
            img = Image.open(img_path)
            mw, mh = img.size

            # Crop the top title bar (starts at Y=81)
            cropped_img = img.crop((0, 81, mw, mh))
            cmw, cmh = cropped_img.size

            # Scale to fit inside 1705x1369 proportionally
            new_w = 1705
            new_h = int(new_w * cmh / cmw)

            img_resized = cropped_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Create white background canvas
            bg = Image.new("RGB", (1705, 1369), color=(255, 255, 255))
            px = (1705 - new_w) // 2
            py = (1369 - new_h) // 2
            bg.paste(img_resized, (px, py))

            bg.save(output_path)
            print(f"Loaded data pipeline mindmap, cropped top title bar, and saved to {output_path}")
            return view_w
        except Exception as e:
            print(f"Error loading data pipeline mindmap: {e}")
    return None

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    pass

legend_items = []

legend_explanation = [
    ("【地理矢量数据】", "包含路网、建筑轮廓、铁轨及公园绿地等 GIS 图层，作为空间底座并统一投影为 WGS-84 坐标系。"),
    ("【街景影像数据】", "通过百度街景 API 批量获取全域多视角图像，经由 PyTorch 深度语义分割网络计算街道绿视率（GVI）。"),
    ("【社交媒体文本】", "爬取微博和小红书的打卡文本与定位，使用自然语言处理模型分析情感倾向，识别环境与品质痛点。"),
    ("【数据融合计算】", "将非结构化的情感文本与空间点 POI 进行融合，构建多维度的街区品质诊断热力底图。")
]

description_lines = [
    "1. 原始数据获取：抓取社交媒体（微博、小红书）POI 及街景影像，以及获取高分辨率卫星遥感、建筑轮廓与路网 GIS 矢量底数据。",
    "2. 空间计算与清洗：包含空间句法（Space Syntax）全局拓扑计算、街景图像绿视率（GVI）分割，以及多源 POI 的空间落点清洗融合。",
    "3. LLM智能体分析：利用大语言模型（LLM）对收集到的居民反馈与文本数据进行情感倾向分析，生成品质痛点坐标信息并写入地理要素。"
]
