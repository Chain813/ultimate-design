# -*- coding: utf-8 -*-
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"

def draw_map_early(output_path, view_w, view_h, STATIC_DIR):
    img_path = STATIC_DIR / "urban_rural_planning_mindmap.png"
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
            print(f"Loaded urban rural planning mindmap, cropped top title bar, and saved to {output_path}")
            return view_w
        except Exception as e:
            print(f"Error loading urban rural planning mindmap: {e}")
    return None

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    pass

legend_items = []

legend_explanation = [
    ("【五级编制体系】", "国土空间规划分为国家级、省级、市级、县级、乡镇级，实现自上而下的规划指标分解与刚性管控约束。"),
    ("【三类规划类型】", "包含总体规划（空间开发保护总纲）、详细规划（开发建设和整治依据）以及专项规划（特定领域专项）。"),
    ("【三区三线】", "划定生态、农业、城镇三类空间，对应生态保护红线、永久基本农田、城镇开发边界三条红线，实行刚性管制。"),
    ("【国土用途管制】", "以“三区三线”为刚性底线，对所有的国土空间分区准入、用途转用以及规划许可实施统一、全域的管制。"),
    ("【工作流提示】", "本工作流涵盖了总体规划、控制性与修建性详细规划、城市设计及其实施阶段的核心内容体系。")
]

description_lines = [
    "1. 规划法律法规与技术标准体系：包括《国土空间规划法（草案）》等法律法规约束，以及国土空间规划编制规程等技术标准体系支撑。",
    "2. 规划编制层级划分：从国家、省、市、县、乡镇逐级向下落实细化，分为总体规划、专项规划与详细规划（控制性/修建性详细规划）。",
    "3. 空间开发治理要素：划定“三区三线”（生态、农业、城镇空间以及红线），建立健全国土空间用途管制和生态保护补偿机制。"
]
