# -*- coding: utf-8 -*-
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"

def draw_map_early(output_path, view_w, view_h, STATIC_DIR):
    img_path = STATIC_DIR / "atlas_chapters_mindmap.png"
    if img_path.exists():
        try:
            img = Image.open(img_path).convert("RGB")
            mw, mh = img.size

            # Cleanly cover the entire gray-blue banner with white, preserving the green box and connector line
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            left_x = 880
            right_x = 1220
            bottom_y = 145

            # 1. Paint white over the entire width from Y=0 to Y=54 (above the green box)
            draw.rectangle([0, 0, mw, 54], fill=(255, 255, 255))
            # 2. Paint white over the left side from X=0 to X=left_x, Y=54 to Y=200
            draw.rectangle([0, 54, left_x, 200], fill=(255, 255, 255))
            # 3. Paint white over the right side from X=right_x to X=mw, Y=54 to Y=200
            draw.rectangle([right_x, 54, mw, 200], fill=(255, 255, 255))
            # 4. Paint white below the green box, preserving the vertical line at X=1050
            draw.rectangle([left_x, bottom_y + 1, 1048, 200], fill=(255, 255, 255))
            # 5. Paint white below the green box on the right of the vertical line
            draw.rectangle([1052, bottom_y + 1, right_x, 200], fill=(255, 255, 255))

            # Scale to fit inside 1705x1369 proportionally
            new_w = 1705
            new_h = int(new_w * mh / mw) # mw=2100, mh=1400 -> 1136

            img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Create white background canvas
            bg = Image.new("RGB", (1705, 1369), color=(255, 255, 255))
            px = (1705 - new_w) // 2
            py = (1369 - new_h) // 2
            bg.paste(img_resized, (px, py))

            bg.save(output_path)
            print(f"Loaded atlas chapters mindmap, removed gray banner, and saved to {output_path}")
            return view_w
        except Exception as e:
            print(f"Error loading atlas chapters mindmap: {e}")
    return None

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    pass

legend_items = []

legend_explanation = [
    ("【认知篇】", "图纸 DR-001 至 DR-013，侧重于规划研究范围划定、区位关系解析及遥感数据基底建立。"),
    ("【诊断篇】", "图纸 DR-014 至 DR-030，对用地现状、建筑层高、历史风貌、可达性及环境品质进行定量测算。"),
    ("【策略篇】", "图纸 DR-040 至 DR-049，提出更新分区模式，控制建筑改造强度与伪满皇宫周边的视廊限高。"),
    ("【方案篇】", "图纸 DR-051 至 DR-082，详细规划路网交通、蓝绿景观系统、文化展示游线及近期实施时序。"),
    ("【技术支撑】", "图纸 DR-083 至 DR-086，展示全周期的数字化计算、数据管线、工作流以及空间规划体系。")
]

description_lines = [
    "1. 现状调查与诊断篇：涵盖区位、范围、遥感现状、用地现状、高度风貌等空间测算与空间句法可达性分析。",
    "2. 策略规划与方案篇：包含更新模式分区、空间结构、建筑更新控制、交通/绿地/历史文化展示系统等规划方案。",
    "3. AI赋能技术支撑：展示通过 NLP 与 LLM 协同决策，结合 AIGC 技术推演，实现多利益主体的城市更新全周期推演表达。"
]
