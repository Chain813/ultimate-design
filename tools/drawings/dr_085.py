# -*- coding: utf-8 -*-
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"

def draw_map_early(output_path, view_w, view_h, STATIC_DIR):
    img_path = STATIC_DIR / "workflow_flowchart.png"
    if img_path.exists():
        try:
            img = Image.open(img_path)
            mw, mh = img.size

            # Crop to remove the top title bar and the bottom legend row
            # Top title ends at Y=100, bottom legend starts at Y=960
            cropped_img = img.crop((0, 100, mw, 960))
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
            print(f"Loaded workflow flowchart, cropped, and saved to {output_path}")
            return view_w
        except Exception as e:
            print(f"Error loading workflow flowchart: {e}")
    return None

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    pass

legend_items = [
    ("数据底座与分析", "rect_wf_blue"),
    ("智能决策与策略", "rect_wf_purple"),
    ("空间规划与深化", "rect_wf_green"),
    ("成果表达与交付", "rect_wf_yellow"),
    ("共享辅助工具", "rect_wf_slate")
]

legend_explanation = [
    ("【多源诊断】", "获取街区遥感、路网、建筑层数等空间现状，诊断步行连通度、绿视率、铁路割裂等环境病征。"),
    ("【AI推演】", "基于手绘总规图，输入 ControlNet 并配合天际线效果提示词，由 Diffusion 批量推演多样化更新方案。"),
    ("【指标核验】", "将 AI 生成的候选平面方案矢量化，导回 GIS 数据库，自动核算各地块用地性质、高度、密度等指标。"),
    ("【协同决策】", "依托 LLM Agent 对话框架，模拟政府、专家和居民决策，在满足指标刚性约束下，多轮协商评选最佳方案。")
]

description_lines = [
    "1. 智能诊断阶段：通过多源异构数据清洗与整合，利用大语言模型（LLM）智能体进行品质病征定位，确定更新的先导方向与改造级别。",
    "2. 协同生成阶段：通过交互式草图/提示词控制网（ControlNet），实现建筑天际线重塑与总体规划总平面图的多方案AIGC生成与方案评选。",
    "3. 方案闭环阶段：将选定方案以矢量要素导回 GIS 系统中，进行用地/高度/容积率等核心指标验算，自动输出规范的图册和导则。"
]
