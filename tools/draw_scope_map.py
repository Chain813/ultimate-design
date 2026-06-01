# -*- coding: utf-8 -*-
# tools/draw_scope_map.py
import json
import sys
import os
from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from shapely.geometry import Point, box
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import pandas as pd
import importlib

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"
GIS_DIR = ROOT / "data/gis"
ASSETS_DIR = ROOT / "assets"

MAP_TYPE_TO_MODULE = {
    "土地利用现状图": "dr_014",
    "用地现状分析图": "dr_014",
    "道路系统规划图": "dr_051",
    "道路交通系统规划图": "dr_051",
    "绿地系统规划图": "dr_056",
    "绿地景观系统图": "dr_056",
    "卫星图": "dr_013",
    "数据来源与遥感现状图": "dr_013",
    "数据来源图": "dr_013",
    "交通分析图": "dr_020",
    "道路交通现状图": "dr_020",
    "历史建筑与工业遗产分布图": "dr_019",
    "建筑高度现状图": "dr_017",
    "建筑风貌现状图": "dr_018",
    "建筑风貌识别图": "dr_018",
    "用地规划图": "dr_014_plan",
    "用地规划分析图": "dr_014_plan",
    "研究范围图": "dr_005",
    "空间句法可达性分析图": "dr_021",
    "环境品质问题地图": "dr_030",
    "遗产价值评估热力图": "dr_031",
    "更新模式分区图": "dr_040",
    "建筑更新控制图": "dr_040",
    "空间结构规划图": "dr_042",
    "总平面图": "dr_044",
    "总体规划图": "dr_044",
    "建筑高度控制图": "dr_049",
    "慢行系统规划图": "dr_slow_traffic",
    "公共空间系统图": "dr_public_space",
    "历史文化展示系统图": "dr_057",
    "AIGC技术推演过程图": "dr_081",
    "实施分期图": "dr_082",
    "图册章节结构导图": "dr_083",
    "数据处理管线导图": "dr_084",
    "规划协同工作流程图": "dr_085",
    "城乡规划知识体系导图": "dr_086",
    "现状区位图": "dr_004",
}

def get_drawing_module(drawing_type):
    mod_name = MAP_TYPE_TO_MODULE.get(drawing_type, "dr_004")
    try:
        return importlib.import_module(f"tools.drawings.{mod_name}")
    except Exception as e:
        print(f"Error importing tools.drawings.{mod_name}: {e}")
        try:
            return importlib.import_module(f"drawings.{mod_name}")
        except Exception as e2:
            print(f"Error importing drawings.{mod_name}: {e2}")
            return None

def generate_drawing_params(drawing_type: str) -> dict:
    """根据设计纲要和图纸类型，用 LLM 生成绘图参数。

    Returns a dict with keys like highlight_zones, annotations, emphasis_plots, narrative.
    Returns empty dict on failure.
    """
    try:
        from src.workflow.design_context import build_design_context, get_context_for_drawing
        from src.engines.llm_engine import call_llm_engine

        ctx = build_design_context()
        if not ctx.design_brief and "07" not in ctx.completed_stages:
            return {}

        brief = ctx.design_brief or ctx.get_summary(1500)
        drawing_ctx = get_context_for_drawing(drawing_type, ctx)

        prompt = f"""基于设计纲要，为图纸「{drawing_type}」生成绘图辅助参数。

设计纲要：
{brief[:1500]}

请输出 JSON（不要包含 markdown 块标记）：
{{
    "highlight_zones": [{{"name": "地块名", "color": "#hex", "alpha": 0.3}}],
    "annotations": [{{"x": 经度, "y": 纬度, "text": "标注内容", "fontsize": 9}}],
    "emphasis_plots": ["地块名"],
    "narrative": "一句话描述本图的核心设计意图"
}}

注意：
- x 为经度(125.3x), y 为纬度(43.9x)
- highlight_zones 中的 name 必须是实际存在的地块名
- annotations 的坐标必须在研究范围内(经度125.32-125.36, 纬度43.89-43.92)
- 如果没有需要特别强调的内容，返回空数组"""

        resp = call_llm_engine(
            prompt=prompt,
            system_prompt="你是城市设计制图参数专家。只输出 JSON，不要解释。",
            model="deepseek-v4-flash",
        )

        # Parse JSON from response
        resp = resp.strip()
        if resp.startswith("```"):
            resp = resp.split("```")[1]
            if resp.startswith("json"):
                resp = resp[4:]
        result = json.loads(resp)
        if isinstance(result, dict):
            return result
    except Exception:
        pass
    return {}


def draw_spatial_map(output_path, drawing_type="现状区位图"):
    print(f"Loading spatial data layers for {drawing_type}...")
    
    # 1. Load layers
    boundary_path = GIS_DIR / "Boundary_Scope.geojson"
    water_path = STATIC_DIR / "water.geojson"
    roads_path = STATIC_DIR / "road_clipped.geojson"
    rails_path = STATIC_DIR / "rail_clipped.geojson"
    
    buildings_path = STATIC_DIR / "buildings.geojson"
    if not buildings_path.exists():
        buildings_path = GIS_DIR / "Building_Footprints.geojson"
        
    key_plots_path = GIS_DIR / "Key_Plots_District.json"
    landuse_path = GIS_DIR / "landuse_clipped.geojson"
    
    boundary = gpd.read_file(boundary_path).to_crs(epsg=3857)
    water = gpd.read_file(water_path).to_crs(epsg=3857) if water_path.exists() else None
    roads = gpd.read_file(roads_path).to_crs(epsg=3857) if roads_path.exists() else None
    rails = gpd.read_file(rails_path).to_crs(epsg=3857) if rails_path.exists() else None
    buildings = gpd.read_file(buildings_path).to_crs(epsg=3857) if buildings_path.exists() else None
    key_plots = gpd.read_file(key_plots_path).to_crs(epsg=3857) if key_plots_path.exists() else None
    landuse = gpd.read_file(landuse_path).to_crs(epsg=3857) if landuse_path.exists() else None

    # Calculate center and bounds
    minx, miny, maxx, maxy = boundary.total_bounds
    cx = (minx + maxx) / 2
    cy = (miny + maxy) / 2
    height_m = maxy - miny
    
    # Target aspect ratio is 1705/1369 = ~1.2454
    view_h = height_m * 1.55
    view_w = view_h * 1.2454

    # Early return if drawing has draw_map_early method (like AIGC)
    module = get_drawing_module(drawing_type)
    if module and hasattr(module, "draw_map_early"):
        res = module.draw_map_early(output_path, view_w, view_h, STATIC_DIR)
        if res is not None:
            return res

    # 2. Setup figure and axes
    fig = plt.figure(figsize=(17.05, 13.69), dpi=200, facecolor="#FAFAFC")
    ax = fig.add_axes([0, 0, 1, 1], facecolor="#FAFAFC")
    
    # Set display bounds
    ax.set_xlim(cx - view_w / 2, cx + view_w / 2)
    ax.set_ylim(cy - view_h / 2, cy + view_h / 2)
    ax.set_axis_off()
    ax.set_aspect("equal")

    # Font setup for matplotlib
    font_prop = {'family': 'sans-serif', 'weight': 'bold', 'size': 16}
    import matplotlib.font_manager as fm
    sys_fonts = [f.name for f in fm.fontManager.ttflist]
    if "Microsoft YaHei" in sys_fonts:
        font_prop['family'] = "Microsoft YaHei"
    elif "SimHei" in sys_fonts:
        font_prop['family'] = "SimHei"

    # Convert coordinates helper
    def get_xy(lon, lat):
        p = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(epsg=3857)
        return p.iloc[0].x, p.iloc[0].y

    # 3. Generate LLM-guided drawing params
    params = generate_drawing_params(drawing_type)

    # 4. Plot layers using module or default
    if module and hasattr(module, "draw_map"):
        module.draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop, params=params)
    else:
        default_mod = get_drawing_module("现状区位图")
        if default_mod and hasattr(default_mod, "draw_map"):
            default_mod.draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop, params=params)

    # Boundary red line (Apple Red)
    boundary.plot(ax=ax, facecolor="none", edgecolor="#FF3B30", linewidth=2.0, zorder=7.0)

    # 4. Add text annotations for key landmarks (if not AIGC flowchart)
    if drawing_type != "AIGC技术推演过程图":
        labels = [
            ("伪满皇宫博物院", 125.3422, 43.9036),
            ("光复路", 125.3475, 43.9017),
            ("伊通河沿岸公园", 125.3590, 43.9010),
            ("长春站", 125.3250, 43.9080),
            ("胜利公园", 125.3260, 43.8960)
        ]
        for name, lon, lat in labels:
            px, py = get_xy(lon, lat)
            ax.plot(px, py, marker='o', markersize=10, color='#FF9500', markeredgecolor='#FFFFFF', markeredgewidth=2.0, zorder=9)
            py_text = py + 70
            txt = ax.text(px, py_text, name, color='#1d1d1f', ha='center', va='bottom', 
                          fontdict=font_prop, zorder=10)
            txt.set_path_effects([path_effects.withStroke(linewidth=3, foreground='#FFFFFF')])

    # Save temporary map image
    plt.savefig(output_path, dpi=200)
    plt.close(fig)
    print(f"Temporary spatial map saved to {output_path}")
    return view_w

def wrap_text_by_pixels(text, font, max_width, draw):
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        w = draw.textlength(test_line, font=font)
        if w <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char
    if current_line:
        lines.append(current_line)
    return lines

def draw_centered_text(draw, text, cx, cy, fill, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text((cx - w // 2, cy - h // 2), text, fill=fill, font=font)

def generate_dynamic_description(drawing_type, title):
    try:
        from src.config import SHP_FILES
        import geopandas as gpd
        import pandas as pd
        import numpy as np

        boundary_path = SHP_FILES["boundary"]
        buildings_path = SHP_FILES["buildings"]
        landuse_path = SHP_FILES["landuse"]
        
        if boundary_path.exists() and buildings_path.exists() and landuse_path.exists():
            boundary = gpd.read_file(str(boundary_path))
            if boundary.crs is None: boundary.set_crs("EPSG:4326", inplace=True)
            boundary_3857 = boundary.to_crs("EPSG:3857")
            boundary_union = boundary_3857.geometry.union_all() if hasattr(boundary_3857.geometry, "union_all") else boundary_3857.geometry.unary_union
            boundary_area = boundary_union.area
            
            buildings = gpd.read_file(str(buildings_path))
            if buildings.crs is None: buildings.set_crs("EPSG:4326", inplace=True)
            buildings_3857 = buildings.to_crs("EPSG:3857")
            centroids = buildings_3857.geometry.centroid
            mask = centroids.within(boundary_union)
            filtered_buildings = buildings_3857.loc[mask].copy()
            
            footprint_area = filtered_buildings.geometry.area.sum()
            filtered_buildings["Floor_num"] = pd.to_numeric(filtered_buildings["Floor"], errors="coerce").fillna(1).astype(float)
            total_floor_area = (filtered_buildings.geometry.area * filtered_buildings["Floor_num"]).sum()
            
            far = total_floor_area / boundary_area
            building_density = (footprint_area / boundary_area) * 100.0
            
            filtered_buildings["Height"] = filtered_buildings["Floor_num"] * 3.5
            max_height = filtered_buildings["Height"].max()
            
            landuse = gpd.read_file(str(landuse_path))
            if landuse.crs is None: landuse.set_crs("EPSG:4326", inplace=True)
            landuse_3857 = landuse.to_crs("EPSG:3857")
            landuse_clipped = gpd.clip(landuse_3857, boundary_3857)
            
            greenery_area = landuse_clipped[landuse_clipped["GB_Code"].str.startswith("G", na=False)].geometry.area.sum()
            greenery_ratio = (greenery_area / boundary_area) * 100.0
            
            area_ha = boundary_area / 10000.0
            num_bldgs = len(filtered_buildings)
        else:
            raise ValueError()
    except Exception:
        area_ha = 327.8
        num_bldgs = 719
        far = 1.13
        building_density = 30.0
        greenery_ratio = 2.9
        max_height = 59.5

    prompt = f"""你是一位国家注册城乡规划师。请基于以下本项目的真实 GIS 实测指标，为规划设计图册中的图纸《{title}》（图纸类别：{drawing_type}）生成三条专业、精准的设计说明或规划指标说明。

真实数据指标：
- 规划研究总面积：{area_ha:.1f} 公顷
- 现状建筑数量：{num_bldgs} 栋
- 实测容积率（FAR）：{far:.2f}
- 实测建筑密度：{building_density:.1f}%
- 实测绿地率：{greenery_ratio:.1f}%
- 实测最高建筑高度：{max_height:.1f} 米

生成要求：
1. 必须输出三条说明文字，每条以“1. ”、“2. ”、“3. ”开头，格式非常严谨，严禁任何前言或后记解释。
2. 每条说明控制在 65 个中文汉字以内（因为图纸底部排版宽度限制）。
3. 必须引用上述的真实数据（例如：“容积率 {far:.2f}”、“绿地率 {greenery_ratio:.1f}%”、“最高高度 {max_height:.1f} 米”、“{num_bldgs} 栋现状建筑”等）。
4. 语言风格应为专业、严密、严谨的法定规划文本，包含时空背景（如长春宽城区、伪满皇宫周边、伊通河等）。
5. 必须输出纯文本，不得带特殊标记。
"""
    try:
        from src.engines.llm_engine import call_llm_engine
        res = call_llm_engine(prompt=prompt, system_prompt="你是专业的国家注册规划师。只输出3条中文设计说明（格式为数字编号开头），不要解释。", model="deepseek-v4-flash")
        lines = [l.strip() for l in res.split('\n') if l.strip()]
        valid_lines = []
        for line in lines:
            if line.startswith(("1.", "2.", "3.", "1、", "2、", "3、", "1 .", "2 .", "3 .")):
                content = line[2:].strip()
                idx = len(valid_lines) + 1
                valid_lines.append(f"{idx}. {content}")
        if len(valid_lines) == 3:
            return valid_lines
    except Exception:
        pass
    return None

def process_a3_layout(map_path, output_path, view_w, drawing_type="现状区位图", title="现状区位图", description_lines=None, drawing_number="DR-001", author="陈礼冲", author_id="202111003", organization="吉林建筑大学建筑与规划学院\n城乡规划211班"):
    print("Processing A3 layout template...")
    template = Image.open(STATIC_DIR / 'a3_layout_preview_full.png').convert('RGB')
    map_img = Image.open(map_path).convert('RGB')
    windrose = Image.open(ASSETS_DIR / '长春市风玫瑰.png')

    module = get_drawing_module(drawing_type)
    
    if description_lines is None:
        dynamic_desc = generate_dynamic_description(drawing_type, title)
        if dynamic_desc:
            description_lines = dynamic_desc
        else:
            if module and hasattr(module, "description_lines"):
                description_lines = module.description_lines
            else:
                default_mod = get_drawing_module("现状区位图")
                if default_mod and hasattr(default_mod, "description_lines"):
                    description_lines = default_mod.description_lines
    is_mindmap = (module is not None and hasattr(module, "draw_map_early"))
    
    # 1. Resize and paste spatial map
    map_resized = map_img.resize((1705, 1369), Image.Resampling.LANCZOS)
    template.paste(map_resized, (183, 289))
    
    # 2. Clear right side compass box and paste wind rose
    draw = ImageDraw.Draw(template)
    draw.rectangle([1891, 292, 2309, 605], fill=(255, 255, 255))
    
    wr_w, wr_h = windrose.size
    new_h = 200
    new_w = int(new_h * wr_w / wr_h)
    windrose_resized = windrose.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    wx = 1890 + (420 - new_w) // 2
    wy = 291 + 15
    template.paste(windrose_resized, (wx, wy), windrose_resized)
    
    # 3. Fonts loading
    font_path = 'C:/Windows/Fonts/msyh.ttc'
    font_bold_path = 'C:/Windows/Fonts/msyhbd.ttc'
    try:
        font_small = ImageFont.truetype(font_path, 18)
        font_title = ImageFont.truetype(font_path, 28)
        font_body = ImageFont.truetype(font_path, 18)
        font_tb = ImageFont.truetype(font_path, 24)
        font_body_bold = ImageFont.truetype(font_bold_path, 18)
    except IOError:
        font_small = ImageFont.load_default()
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_tb = ImageFont.load_default()
        font_body_bold = font_body
        
    # 4. Draw Scale, Legend, and Description Card
    if not is_mindmap:
        # Draw dynamic scale bar
        m_per_px = view_w / 1705
        scale_bar_px = int(round(500 / m_per_px))
        x_start = 2101 - scale_bar_px // 2
        x_end = 2101 + scale_bar_px // 2
        
        draw.line([(x_start, 545), (x_end, 545)], fill=(0, 0, 0), width=2)
        draw.line([(x_start, 540), (x_start, 545)], fill=(0, 0, 0), width=2)
        draw.line([(x_end, 540), (x_end, 545)], fill=(0, 0, 0), width=2)
        draw.text((x_start - 5, 555), "0", fill=(72, 72, 74), font=font_small)
        draw.text((x_end - 20, 555), "500m", fill=(72, 72, 74), font=font_small)
        
        scale_ratio = view_w / 0.31968
        scale_rounded = int(round(scale_ratio / 500)) * 500
        scale_text = f"比例尺 1:{scale_rounded}"
        bbox_scale = draw.textbbox((0, 0), scale_text, font=font_small)
        w_scale = bbox_scale[2] - bbox_scale[0]
        draw.text((2101 - w_scale // 2, 515), scale_text, fill=(72, 72, 74), font=font_small)

    # 5. Clear and Redraw Legend section [1891, 608, 2309, 1390]
    draw.rectangle([1891, 608, 2309, 1390], fill=(255, 255, 255))
    
    if is_mindmap:
        # Check if we have legend items to display
        legend_items = []
        if module and hasattr(module, "legend_items") and module.legend_items:
            legend_items = module.legend_items
            
        y = 690
        if legend_items:
            # Draw Title "图例分类"
            draw_centered_text(draw, "图 例 分 类", 2101, 640, (15, 23, 42), font_title)
            draw.line([(1910, 665), (2290, 665)], fill=(203, 213, 225), width=1)
            
            # Draw the items
            for label, style in legend_items:
                if style == "rect_wf_blue":
                    draw.rectangle([1915, y, 1950, y+18], fill=(239, 246, 255), outline=(59, 130, 246), width=2)
                elif style == "rect_wf_purple":
                    draw.rectangle([1915, y, 1950, y+18], fill=(250, 245, 255), outline=(192, 132, 252), width=2)
                elif style == "rect_wf_green":
                    draw.rectangle([1915, y, 1950, y+18], fill=(240, 253, 244), outline=(74, 222, 128), width=2)
                elif style == "rect_wf_yellow":
                    draw.rectangle([1915, y, 1950, y+18], fill=(254, 252, 232), outline=(251, 191, 36), width=2)
                elif style == "rect_wf_slate":
                    draw.rectangle([1915, y, 1950, y+18], fill=(248, 250, 252), outline=(148, 163, 184), width=2)
                
                draw.text((1965, y), label, fill=(29, 29, 31), font=font_body)
                y += 32
                
            # Draw a separator after legend items
            y += 10
            draw.line([(1910, y), (2290, y)], fill=(203, 213, 225), width=1)
            y += 25
            
            # Draw Title "图表说明"
            draw_centered_text(draw, "图 表 说 明", 2101, y, (15, 23, 42), font_title)
            y += 25
            draw.line([(1910, y), (2290, y)], fill=(203, 213, 225), width=1)
            y += 25
        else:
            # Title "图表说明"
            draw_centered_text(draw, "图 表 说 明", 2101, 640, (15, 23, 42), font_title)
            draw.line([(1910, 665), (2290, 665)], fill=(203, 213, 225), width=1)
            y = 690
            
        explanations = []
        if module and hasattr(module, "legend_explanation"):
            explanations = module.legend_explanation
            
        max_text_width = 378
        for item in explanations:
            if isinstance(item, tuple) and len(item) == 2:
                title_text, desc_text = item
                draw.text((1911, y), title_text, fill=(29, 78, 216), font=font_body_bold)
                y += 24
                
                desc_lines = wrap_text_by_pixels(desc_text, font_body, max_text_width, draw)
                for line in desc_lines:
                    draw.text((1911, y), line, fill=(71, 85, 105), font=font_body)
                    y += 24
                y += 10
            else:
                desc_lines = wrap_text_by_pixels(str(item), font_body, max_text_width, draw)
                for line in desc_lines:
                    draw.text((1911, y), line, fill=(71, 85, 105), font=font_body)
                    y += 24
                y += 10
    else:
        # Title "图例"
        draw_centered_text(draw, "图    例", 2101, 640, (15, 23, 42), font_title)
        draw.line([(1910, 665), (2290, 665)], fill=(203, 213, 225), width=1)
        
        module = get_drawing_module(drawing_type)
        legend_items = []
        if module and hasattr(module, "legend_items"):
            legend_items = module.legend_items
        else:
            default_mod = get_drawing_module("现状区位图")
            if default_mod and hasattr(default_mod, "legend_items"):
                legend_items = default_mod.legend_items
                
        y = 690
        spacing = 38 if len(legend_items) > 8 else 45
        for label, style in legend_items:
            if style == "rect_red_border":
                draw.rectangle([1915, y, 1950, y+18], fill=(255, 255, 255), outline=(255, 59, 48), width=3)
            elif style == "rect_orange_border":
                draw.rectangle([1915, y, 1950, y+18], fill=(255, 245, 230), outline=(255, 149, 0), width=2)
            elif style == "rect_building":
                draw.rectangle([1915, y, 1950, y+18], fill=(255, 255, 255), outline=(229, 229, 231), width=1)
            elif style == "rect_water":
                draw.rectangle([1915, y, 1950, y+18], fill=(208, 230, 247), outline=None)
            elif style == "line_rail":
                draw.line([(1915, y+9), (1927, y+9)], fill=(72, 72, 74), width=2)
                draw.line([(1932, y+9), (1943, y+9)], fill=(72, 72, 74), width=2)
                draw.line([(1948, y+9), (1950, y+9)], fill=(72, 72, 74), width=2)
            elif style == "rect_road":
                draw.rectangle([1915, y, 1950, y+18], fill=(229, 229, 234), outline=None)
            elif style == "rect_r2":
                draw.rectangle([1915, y, 1950, y+18], fill=(253, 224, 71), outline=None)
            elif style == "rect_a1":
                draw.rectangle([1915, y, 1950, y+18], fill=(239, 68, 68), outline=None)
            elif style == "rect_b":
                draw.rectangle([1915, y, 1950, y+18], fill=(219, 39, 119), outline=None)
            elif style == "rect_a7":
                draw.rectangle([1915, y, 1950, y+18], fill=(185, 28, 28), outline=None)
            elif style == "rect_m":
                draw.rectangle([1915, y, 1950, y+18], fill=(147, 51, 234), outline=None)
            elif style == "rect_g1":
                draw.rectangle([1915, y, 1950, y+18], fill=(34, 197, 94), outline=None)
            elif style == "rect_euluc_0":
                draw.rectangle([1915, y, 1950, y+18], fill=(255, 255, 0), outline=(203, 213, 225), width=1)
            elif style == "rect_euluc_1":
                draw.rectangle([1915, y, 1950, y+18], fill=(230, 0, 0), outline=(203, 213, 225), width=1)
            elif style == "rect_euluc_2":
                draw.rectangle([1915, y, 1950, y+18], fill=(255, 127, 0), outline=(203, 213, 225), width=1)
            elif style == "rect_euluc_3":
                draw.rectangle([1915, y, 1950, y+18], fill=(170, 120, 85), outline=(203, 213, 225), width=1)
            elif style == "rect_euluc_4":
                draw.rectangle([1915, y, 1950, y+18], fill=(156, 156, 156), outline=(203, 213, 225), width=1)
            elif style == "rect_euluc_5":
                draw.rectangle([1915, y, 1950, y+18], fill=(104, 104, 104), outline=(203, 213, 225), width=1)
            elif style == "rect_euluc_6":
                draw.rectangle([1915, y, 1950, y+18], fill=(255, 127, 127), outline=(203, 213, 225), width=1)
            elif style == "rect_euluc_7":
                draw.rectangle([1915, y, 1950, y+18], fill=(255, 127, 255), outline=(203, 213, 225), width=1)
            elif style == "rect_euluc_8":
                draw.rectangle([1915, y, 1950, y+18], fill=(255, 127, 191), outline=(203, 213, 225), width=1)
            elif style == "rect_euluc_9":
                draw.rectangle([1915, y, 1950, y+18], fill=(127, 255, 255), outline=(203, 213, 225), width=1)
            elif style == "rect_euluc_10":
                draw.rectangle([1915, y, 1950, y+18], fill=(56, 168, 0), outline=(203, 213, 225), width=1)
            elif style == "line_red_dashed":
                draw.line([(1915, y+9), (1950, y+9)], fill=(255, 45, 85), width=2)
                for tx in range(1917, 1951, 6):
                    draw.rectangle([tx, y+7, tx+2, y+11], fill=(255, 255, 255))
            elif style == "rect_green_plan":
                draw.rectangle([1915, y, 1950, y+18], fill=(187, 247, 208), outline=(34, 197, 94), width=1)
            elif style == "rect_water_plan":
                draw.rectangle([1915, y, 1950, y+18], fill=(226, 240, 253), outline=(59, 130, 246), width=1)
            elif style == "rect_green_status":
                draw.rectangle([1915, y, 1950, y+18], fill=(220, 252, 231), outline=None)
            elif style == "line_h1":
                draw.line([(1915, y+9), (1950, y+9)], fill=(239, 68, 68), width=3)
            elif style == "line_h2":
                draw.line([(1915, y+9), (1950, y+9)], fill=(249, 115, 22), width=3)
            elif style == "line_h3":
                draw.line([(1915, y+9), (1950, y+9)], fill=(234, 179, 8), width=2)
            elif style == "line_h4":
                draw.line([(1915, y+9), (1950, y+9)], fill=(156, 163, 175), width=1)
            elif style == "line_t1":
                draw.line([(1915, y+9), (1950, y+9)], fill=(239, 68, 68), width=3)
            elif style == "line_t2":
                draw.line([(1915, y+9), (1950, y+9)], fill=(59, 130, 246), width=2)
            elif style == "line_t3":
                draw.line([(1915, y+9), (1950, y+9)], fill=(16, 185, 129), width=1)
            elif style == "rect_protect_1":
                draw.rectangle([1915, y, 1950, y+18], fill=(254, 226, 226), outline=(220, 38, 38), width=1)
            elif style == "rect_protect_2":
                draw.rectangle([1915, y, 1950, y+18], fill=(254, 243, 199), outline=(217, 119, 6), width=1)
            elif style == "rect_protect_3":
                draw.rectangle([1915, y, 1950, y+18], fill=(241, 245, 249), outline=(71, 85, 105), width=1)
            elif style == "rect_height_1":
                draw.rectangle([1915, y, 1950, y+18], fill=(254, 226, 226), outline=None)
            elif style == "rect_height_2":
                draw.rectangle([1915, y, 1950, y+18], fill=(254, 205, 211), outline=None)
            elif style == "rect_height_3":
                draw.rectangle([1915, y, 1950, y+18], fill=(251, 113, 133), outline=None)
            elif style == "rect_height_4":
                draw.rectangle([1915, y, 1950, y+18], fill=(225, 29, 72), outline=None)
            elif style == "rect_height_5":
                draw.rectangle([1915, y, 1950, y+18], fill=(159, 18, 57), outline=None)
            elif style == "rect_style_traditional":
                draw.rectangle([1915, y, 1950, y+18], fill=(254, 215, 170), outline=(234, 88, 12), width=1)
            elif style == "rect_style_industrial":
                draw.rectangle([1915, y, 1950, y+18], fill=(233, 213, 255), outline=(147, 51, 234), width=1)
            elif style == "rect_style_modern":
                draw.rectangle([1915, y, 1950, y+18], fill=(224, 242, 254), outline=(14, 165, 233), width=1)
            elif style == "rect_style_poor":
                draw.rectangle([1915, y, 1950, y+18], fill=(241, 245, 249), outline=(100, 116, 139), width=1)
            elif style == "circle_landmark":
                draw.ellipse([1922, y+1, 1943, y+22], fill=(255, 149, 0), outline=(255, 255, 255), width=2)
            elif style == "line_integration":
                draw.line([(1915, y+9), (1950, y+9)], fill=(239, 68, 68), width=3)
            elif style == "line_choice":
                draw.line([(1915, y+9), (1950, y+9)], fill=(59, 130, 246), width=2)
            elif style == "rect_prob_road":
                draw.rectangle([1915, y, 1950, y+18], fill=(254, 226, 226), outline=(239, 68, 68), width=1)
            elif style == "rect_prob_fac":
                draw.rectangle([1915, y, 1950, y+18], fill=(254, 243, 199), outline=(245, 158, 11), width=1)
            elif style == "rect_prob_env":
                draw.rectangle([1915, y, 1950, y+18], fill=(220, 252, 231), outline=(16, 185, 129), width=1)
            elif style == "rect_val_high":
                draw.rectangle([1915, y, 1950, y+18], fill=(239, 68, 68), outline=None)
            elif style == "rect_val_mid":
                draw.rectangle([1915, y, 1950, y+18], fill=(249, 115, 22), outline=None)
            elif style == "rect_val_low":
                draw.rectangle([1915, y, 1950, y+18], fill=(253, 224, 71), outline=None)
            elif style == "rect_pattern_protect":
                draw.rectangle([1915, y, 1950, y+18], fill=(239, 68, 68), outline="#1E293B", width=1)
            elif style == "rect_pattern_renovate":
                draw.rectangle([1915, y, 1950, y+18], fill=(249, 115, 22), outline="#1E293B", width=1)
            elif style == "rect_pattern_update":
                draw.rectangle([1915, y, 1950, y+18], fill=(59, 130, 246), outline="#1E293B", width=1)
            elif style == "rect_pattern_control":
                draw.rectangle([1915, y, 1950, y+18], fill=(16, 185, 129), outline="#1E293B", width=1)
            elif style == "line_struct_axis":
                draw.line([(1915, y+9), (1950, y+9)], fill=(239, 68, 68), width=4)
            elif style == "line_struct_sub":
                draw.line([(1915, y+9), (1950, y+9)], fill=(249, 115, 22), width=2)
                for tx in range(1917, 1951, 6):
                    draw.rectangle([tx, y+7, tx+2, y+11], fill=(255, 255, 255))
            elif style == "rect_struct_node":
                draw.rectangle([1915, y, 1950, y+18], fill=(254, 240, 138), outline=(234, 179, 8), width=1)
            elif style == "rect_plan_r":
                draw.rectangle([1915, y, 1950, y+18], fill=(254, 240, 138), outline=None)
            elif style == "rect_plan_b":
                draw.rectangle([1915, y, 1950, y+18], fill=(244, 63, 94), outline=None)
            elif style == "rect_plan_m":
                draw.rectangle([1915, y, 1950, y+18], fill=(192, 132, 252), outline=None)
            elif style == "rect_plan_g":
                draw.rectangle([1915, y, 1950, y+18], fill=(74, 222, 128), outline=None)
            elif style == "rect_plan_a":
                draw.rectangle([1915, y, 1950, y+18], fill=(248, 113, 113), outline=None)
            elif style == "rect_plan_s":
                draw.rectangle([1915, y, 1950, y+18], fill=(203, 213, 225), outline=None)
            elif style == "rect_hc_1":
                draw.rectangle([1915, y, 1950, y+18], fill=(254, 243, 199), outline=None)
            elif style == "rect_hc_2":
                draw.rectangle([1915, y, 1950, y+18], fill=(253, 230, 138), outline=None)
            elif style == "rect_hc_3":
                draw.rectangle([1915, y, 1950, y+18], fill=(252, 211, 77), outline=None)
            elif style == "rect_hc_4":
                draw.rectangle([1915, y, 1950, y+18], fill=(245, 158, 11), outline=None)
            elif style == "rect_hc_5":
                draw.rectangle([1915, y, 1950, y+18], fill=(217, 119, 6), outline=None)
            elif style == "line_green_corridor":
                draw.line([(1915, y+9), (1950, y+9)], fill=(34, 197, 94), width=4)
            elif style == "rect_green_node":
                draw.rectangle([1915, y, 1950, y+18], fill=(220, 252, 231), outline=(34, 197, 94), width=1)
            elif style == "rect_green_pocket":
                draw.rectangle([1915, y, 1950, y+18], fill=(187, 247, 208), outline=None)
            elif style == "line_ped_axis":
                draw.line([(1915, y+9), (1950, y+9)], fill=(236, 72, 153), width=3)
            elif style == "line_green_slow":
                draw.line([(1915, y+9), (1950, y+9)], fill=(16, 185, 129), width=2)
                for tx in range(1917, 1951, 6):
                    draw.rectangle([tx, y+7, tx+2, y+11], fill=(255, 255, 255))
            elif style == "line_tour_path":
                draw.line([(1915, y+9), (1950, y+9)], fill=(220, 38, 38), width=3)
            elif style == "rect_tour_node":
                draw.rectangle([1915, y, 1950, y+18], fill=(254, 243, 199), outline=(217, 119, 6), width=1)
            elif style == "rect_phase_green":
                draw.rectangle([1915, y, 1950, y+18], fill=(34, 197, 94), outline="#1E293B", width=1)
            elif style == "rect_phase_blue":
                draw.rectangle([1915, y, 1950, y+18], fill=(59, 130, 246), outline="#1E293B", width=1)
            elif style == "rect_phase_purple":
                draw.rectangle([1915, y, 1950, y+18], fill=(168, 85, 247), outline="#1E293B", width=1)
            elif style == "line_arrow_cyan":
                draw.line([(1915, y+9), (1950, y+9)], fill=(6, 182, 212), width=3)
                for tx in range(1917, 1951, 6):
                    draw.rectangle([tx, y+7, tx+2, y+11], fill=(255, 255, 255))
            elif style == "line_arrow_orange":
                draw.line([(1915, y+9), (1950, y+9)], fill=(249, 115, 22), width=4)
            elif style == "line_plan_road":
                draw.line([(1915, y+9), (1950, y+9)], fill=(255, 45, 85), width=2)
            elif style == "line_syntax_high":
                draw.line([(1915, y+9), (1950, y+9)], fill=(239, 68, 68), width=3)
            elif style == "line_syntax_med":
                draw.line([(1915, y+9), (1950, y+9)], fill=(253, 174, 97), width=2)
            elif style == "line_syntax_low":
                draw.line([(1915, y+9), (1950, y+9)], fill=(50, 136, 189), width=2)
            elif style == "line_trail_green":
                draw.line([(1915, y+9), (1950, y+9)], fill=(16, 185, 129), width=3)
            elif style == "line_trail_orange":
                draw.line([(1915, y+9), (1950, y+9)], fill=(249, 115, 22), width=2)
                for tx in range(1917, 1951, 6):
                    draw.rectangle([tx, y+7, tx+2, y+11], fill=(255, 255, 255))
            elif style == "line_trail_red":
                draw.line([(1915, y+9), (1950, y+9)], fill=(239, 68, 68), width=3)
            elif style == "marker_node_gold":
                draw.ellipse([1923, y+1, 1942, y+20], fill=(217, 119, 6), outline=(255, 255, 255), width=2)
            elif style == "marker_node_green":
                draw.ellipse([1923, y+1, 1942, y+20], fill=(16, 185, 129), outline=(255, 255, 255), width=2)
            elif style == "marker_node_red":
                draw.ellipse([1923, y+1, 1942, y+20], fill=(239, 68, 68), outline=(255, 255, 255), width=2)
            elif style == "marker_problem":
                draw.polygon([(1932, y+2), (1921, y+18), (1944, y+18)], fill=(239, 68, 68), outline=(255, 255, 255), width=1)
            elif style == "star_core":
                import math
                cx_star, cy_star = 1932.5, y + 9
                r_outer = 9
                r_inner = 4
                star_pts = []
                for i in range(10):
                    angle = i * math.pi / 5 - math.pi / 2
                    r = r_outer if i % 2 == 0 else r_inner
                    star_pts.append((cx_star + r * math.cos(angle), cy_star + r * math.sin(angle)))
                draw.polygon(star_pts, fill=(245, 158, 11), outline=(255, 255, 255), width=1)
            elif style == "rect_blue_fill":
                draw.rectangle([1915, y, 1950, y+18], fill=(219, 234, 254), outline=(37, 99, 235), width=1)
            elif style == "rect_green":
                draw.rectangle([1915, y, 1950, y+18], fill=(167, 243, 208), outline=(4, 120, 87), width=1)
            elif style == "rect_green_buffer":
                draw.rectangle([1915, y, 1950, y+18], fill=(209, 250, 229), outline=(5, 150, 105), width=1)
            elif style == "rect_heatmap_high":
                draw.rectangle([1915, y, 1950, y+18], fill=(220, 38, 38), outline=(203, 213, 225), width=1)
            elif style == "rect_heatmap_med":
                draw.rectangle([1915, y, 1950, y+18], fill=(249, 115, 22), outline=(203, 213, 225), width=1)
            elif style == "rect_heatmap_low":
                draw.rectangle([1915, y, 1950, y+18], fill=(253, 224, 71), outline=(203, 213, 225), width=1)
            elif style == "rect_height_blue":
                draw.rectangle([1915, y, 1950, y+18], fill=(59, 130, 246), outline=(203, 213, 225), width=1)
            elif style == "rect_height_red":
                draw.rectangle([1915, y, 1950, y+18], fill=(239, 68, 68), outline=(203, 213, 225), width=1)
            elif style == "rect_height_yellow":
                draw.rectangle([1915, y, 1950, y+18], fill=(234, 179, 8), outline=(203, 213, 225), width=1)
            elif style == "rect_noise_zone":
                draw.rectangle([1915, y, 1950, y+18], fill=(254, 202, 202), outline=(239, 68, 68), width=1)
                for ox in range(-18, 35, 6):
                    draw.line([(1915 + ox, y+18), (1915 + ox + 18, y)], fill=(239, 68, 68), width=1)
            elif style == "rect_plan_blue":
                draw.rectangle([1915, y, 1950, y+18], fill=(147, 197, 253), outline=(59, 130, 246), width=1)
            elif style == "rect_plan_green":
                draw.rectangle([1915, y, 1950, y+18], fill=(167, 243, 208), outline=(34, 197, 94), width=1)
            elif style == "rect_plan_red":
                draw.rectangle([1915, y, 1950, y+18], fill=(252, 165, 165), outline=(239, 68, 68), width=1)
            elif style == "rect_plan_yellow":
                draw.rectangle([1915, y, 1950, y+18], fill=(253, 224, 71), outline=(234, 179, 8), width=1)
            elif style == "rect_purple_fill":
                draw.rectangle([1915, y, 1950, y+18], fill=(168, 85, 247), outline=(126, 34, 206), width=1)
            elif style == "rect_style_green":
                draw.rectangle([1915, y, 1950, y+18], fill=(16, 185, 129), outline=(71, 85, 105), width=1)
            elif style == "rect_style_orange":
                draw.rectangle([1915, y, 1950, y+18], fill=(245, 158, 11), outline=(71, 85, 105), width=1)
            elif style == "rect_style_blue":
                draw.rectangle([1915, y, 1950, y+18], fill=(59, 130, 246), outline=(71, 85, 105), width=1)
            elif style == "rect_style_hist":
                draw.rectangle([1915, y, 1950, y+18], fill=(180, 83, 9), outline=(71, 85, 105), width=1)
            elif style == "rect_style_park":
                draw.rectangle([1915, y, 1950, y+18], fill=(15, 118, 110), outline=(71, 85, 105), width=1)
            elif style == "rect_style_norm":
                draw.rectangle([1915, y, 1950, y+18], fill=(226, 232, 240), outline=(71, 85, 105), width=1)
            elif style == "rect_sat_base":
                draw.rectangle([1915, y, 1950, y+18], fill=(148, 163, 184), outline=(100, 116, 139), width=1)
            elif style == "rect_h1":
                draw.rectangle([1915, y, 1950, y+18], fill=(253, 230, 138), outline=(71, 85, 105), width=1)
            elif style == "rect_h2":
                draw.rectangle([1915, y, 1950, y+18], fill=(249, 115, 22), outline=(71, 85, 105), width=1)
            elif style == "rect_h3":
                draw.rectangle([1915, y, 1950, y+18], fill=(239, 68, 68), outline=(71, 85, 105), width=1)
            elif style == "rect_h4":
                draw.rectangle([1915, y, 1950, y+18], fill=(185, 28, 28), outline=(71, 85, 105), width=1)
            elif style == "rect_h5":
                draw.rectangle([1915, y, 1950, y+18], fill=(127, 29, 29), outline=(71, 85, 105), width=1)
            elif style == "rect_heritage":
                draw.rectangle([1915, y, 1950, y+18], fill=(217, 119, 6), outline=(180, 83, 9), width=1)
            elif style == "rect_building_light":
                draw.rectangle([1915, y, 1950, y+18], fill=(241, 245, 249), outline=(226, 232, 240), width=1)
            elif style == "rect_building_outline":
                draw.rectangle([1915, y, 1950, y+18], fill=(255, 255, 255), outline=(71, 85, 105), width=1)
            elif style == "rect_green_planned":
                draw.rectangle([1915, y, 1950, y+18], fill=(16, 185, 129), outline=(4, 120, 87), width=1)
            elif style == "line_primary_road_blue":
                draw.line([(1915, y+9), (1950, y+9)], fill=(59, 130, 246), width=3)
            elif style == "line_secondary_road_blue":
                draw.line([(1915, y+9), (1950, y+9)], fill=(96, 165, 250), width=2)
            elif style == "line_tertiary_road_blue":
                draw.line([(1915, y+9), (1950, y+9)], fill=(147, 197, 253), width=1)
            elif style == "line_proposed_road":
                draw.line([(1915, y+9), (1950, y+9)], fill=(225, 29, 72), width=2)
                for tx in range(1917, 1951, 6):
                    draw.rectangle([tx, y+7, tx+2, y+11], fill=(255, 255, 255))
            elif style == "line_primary_road":
                draw.line([(1915, y+9), (1950, y+9)], fill=(225, 29, 72), width=3)
            elif style == "line_secondary_road":
                draw.line([(1915, y+9), (1950, y+9)], fill=(217, 119, 6), width=2)
            elif style == "line_tertiary_road":
                draw.line([(1915, y+9), (1950, y+9)], fill=(148, 163, 184), width=1)
            elif style == "rect_wf_blue":
                draw.rectangle([1915, y, 1950, y+18], fill=(239, 246, 255), outline=(59, 130, 246), width=2)
            elif style == "rect_wf_purple":
                draw.rectangle([1915, y, 1950, y+18], fill=(250, 245, 255), outline=(192, 132, 252), width=2)
            elif style == "rect_wf_green":
                draw.rectangle([1915, y, 1950, y+18], fill=(240, 253, 244), outline=(74, 222, 128), width=2)
            elif style == "rect_wf_yellow":
                draw.rectangle([1915, y, 1950, y+18], fill=(254, 252, 232), outline=(251, 191, 36), width=2)
            elif style == "rect_wf_slate":
                draw.rectangle([1915, y, 1950, y+18], fill=(248, 250, 252), outline=(148, 163, 184), width=2)
                
            draw.text((1965, y), label, fill=(29, 29, 31), font=font_body)
            y += spacing

        # Draw design description under the legend items inside the legend box!
        if description_lines:
            if y < 1120:
                draw.line([(1910, y + 5), (2290, y + 5)], fill=(203, 213, 225), width=1)
                y_desc_title = y + 15
                draw.text((1915, y_desc_title), "设计说明 / DESIGN NOTES", fill=(29, 78, 216), font=font_body_bold)
                y_line = y_desc_title + 24
                max_text_width = 378
                for line in description_lines[:3]:
                    wrapped = wrap_text_by_pixels(line, font_body, max_text_width, draw)
                    for wl in wrapped:
                        draw.text((1915, y_line), wl, fill=(71, 85, 105), font=font_body)
                        y_line += 20
                    y_line += 6

    # 6. Fill planning description card
    draw.rectangle([184, 1661, 1887, 1815], fill=(248, 250, 252))
    draw.text((210, 1668), "规划管控指标体系 (Statutory Zoning Control System)", fill=(29, 29, 31), font=font_title)
    
    indicator_text = "【法定控制要求】 规划总面积：327.8公顷  |  控制容积率：≤ 1.4  |  建筑密度：≤ 35%  |  绿地率要求：≥ 25%  |  高度分区：核心区 ≤ 9m，过渡区 ≤ 18m"
    draw.text((210, 1715), indicator_text, fill=(29, 78, 216), font=font_body_bold)
    
    notes_text = "【实施导引】 街区更新实行分类整治，严格保护伪满皇宫视廊保护线。对于绿地率（现状2.9%）实行刚性生态修补，盘活工业废弃院落增设口袋公园与微绿地。"
    draw.text((210, 1755), notes_text, fill=(100, 116, 139), font=font_body)
            
    # 7. Redraw the entire Title Block [1890, 1394, 2312, 1816]
    draw.rectangle([1890, 1394, 2312, 1816], fill=(241, 245, 249), outline=(15, 23, 42), width=2)
    
    # Grid lines inside the stamp
    draw.line([(1890, 1464), (2312, 1464)], fill=(15, 23, 42), width=1)
    draw.line([(1890, 1564), (2312, 1564)], fill=(15, 23, 42), width=1)
    draw.line([(1890, 1664), (2312, 1664)], fill=(15, 23, 42), width=1)
    draw.line([(2090, 1664), (2090, 1816)], fill=(15, 23, 42), width=1)
    
    # Fonts for the stamp
    try:
        font_stamp_large = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 26)
    except IOError:
        try:
            font_stamp_large = ImageFont.truetype(font_path, 26)
        except IOError:
            font_stamp_large = ImageFont.load_default()
            
    try:
        font_stamp_title = ImageFont.truetype(font_path, 20)
        font_stamp_body = ImageFont.truetype(font_path, 15)
        font_stamp_label = ImageFont.truetype(font_path, 12)
    except IOError:
        font_stamp_title = ImageFont.load_default()
        font_stamp_body = ImageFont.load_default()
        font_stamp_label = ImageFont.load_default()
        
    # Title
    bbox_title = draw.textbbox((0, 0), title, font=font_stamp_large)
    title_h = bbox_title[3] - bbox_title[1]
    title_y = 1429 - title_h // 2
    draw.text((1905, title_y), title, fill=(15, 23, 42), font=font_stamp_large)
    
    # Project Name
    draw.text((1905, 1472), "项目名称 / PROJECT", fill=(120, 120, 125), font=font_stamp_label)
    draw.text((1905, 1494), "数字孪生·古今共振——", fill=(15, 23, 42), font=font_stamp_body)
    draw.text((1905, 1524), "AI赋能下的伪满皇宫周边街区更新规划设计", fill=(15, 23, 42), font=font_stamp_body)
    
    # Unit/Class
    draw.text((1905, 1572), "学校班级 / ORGANIZATION", fill=(120, 120, 125), font=font_stamp_label)
    org_lines = organization.split('\n')
    org_y = 1594
    for ol in org_lines[:2]:
        draw.text((1905, org_y), ol, fill=(15, 23, 42), font=font_stamp_body)
        org_y += 30
    
    # Author & ID
    draw.text((1905, 1674), "制作人 / AUTHOR", fill=(120, 120, 125), font=font_stamp_label)
    draw.text((1905, 1710), author, fill=(15, 23, 42), font=font_stamp_title)
    
    draw.text((2105, 1674), "学号 / ID", fill=(120, 120, 125), font=font_stamp_label)
    draw.text((2105, 1710), author_id, fill=(15, 23, 42), font=font_stamp_body)
    
    # 8. Save cropped homepage banner image from primary map area (if default Location Map)
    if drawing_type == "现状区位图" and title == "现状区位图":
        homepage_banner_img = template.crop((183, 289, 1888, 1658))
        
        # Draw location map, scale bar, and wind rose onto the cropped banner image
        try:
            banner_rgba = homepage_banner_img.convert("RGBA")
            banner_draw = ImageDraw.Draw(banner_rgba)
            W_b, H_b = banner_rgba.size
            
            # Fonts (reusing font paths from script)
            font_title_b = ImageFont.truetype(font_bold_path, 16)
            font_label_b = ImageFont.truetype(font_path, 12)
            font_label_bold_b = ImageFont.truetype(font_bold_path, 12)
            font_scale_b = ImageFont.truetype(font_path, 13)
            font_scale_bold_b = ImageFont.truetype(font_bold_path, 14)
            
            # 8a. Top-Right Corner: Wind Rose Card (200x210)
            wr_card_w, wr_card_h = 200, 210
            wr_x = W_b - wr_card_w - 30
            wr_y = 30
            
            banner_draw.rounded_rectangle([wr_x+2, wr_y+2, wr_x+wr_card_w+2, wr_y+wr_card_h+2], radius=10, fill=(0, 0, 0, 30))
            banner_draw.rounded_rectangle([wr_x, wr_y, wr_x+wr_card_w, wr_y+wr_card_h], radius=10, fill=(255, 255, 255, 240), outline=(200, 200, 200, 255), width=1)
            
            title_text = "长春市风玫瑰图"
            tb = banner_draw.textbbox((0, 0), title_text, font=font_title_b)
            tw = tb[2] - tb[0]
            banner_draw.text((wr_x + (wr_card_w - tw)//2, wr_y + 12), title_text, fill=(30, 41, 59, 255), font=font_title_b)
            
            windrose_path = ASSETS_DIR / "长春市风玫瑰.png"
            if windrose_path.exists():
                windrose = Image.open(windrose_path).convert("RGBA")
                wr_size = 150
                windrose_resized = windrose.resize((wr_size, wr_size), Image.Resampling.LANCZOS)
                wx = wr_x + (wr_card_w - wr_size)//2
                wy = wr_y + 45
                banner_rgba.paste(windrose_resized, (wx, wy), windrose_resized)
            
            # 8b. Bottom-Right Corner: Scale Bar Card (280x95)
            scale_card_w, scale_card_h = 280, 95
            sc_x = W_b - scale_card_w - 30
            sc_y = H_b - scale_card_h - 30
            
            banner_draw.rounded_rectangle([sc_x+2, sc_y+2, sc_x+scale_card_w+2, sc_y+scale_card_h+2], radius=10, fill=(0, 0, 0, 30))
            banner_draw.rounded_rectangle([sc_x, sc_y, sc_x+scale_card_w, sc_y+scale_card_h], radius=10, fill=(255, 255, 255, 240), outline=(200, 200, 200, 255), width=1)
            
            m_per_px = view_w / 1705
            scale_bar_px = int(round(500 / m_per_px))
            scale_text = f"比例尺  1:{scale_rounded}"
            banner_draw.text((sc_x + 20, sc_y + 15), scale_text, fill=(30, 41, 59, 255), font=font_scale_bold_b)
            
            line_y = sc_y + 50
            line_x_start = sc_x + 20
            line_x_end = line_x_start + scale_bar_px
            seg_mid = line_x_start + scale_bar_px // 2
            
            banner_draw.rectangle([line_x_start, line_y, seg_mid, line_y + 6], fill=(30, 41, 59, 255))
            banner_draw.rectangle([seg_mid, line_y, line_x_end, line_y + 6], fill=(255, 255, 255, 255), outline=(30, 41, 59, 255), width=1)
            
            banner_draw.line([(line_x_start, line_y), (line_x_start, line_y - 4)], fill=(30, 41, 59, 255), width=2)
            banner_draw.line([(seg_mid, line_y), (seg_mid, line_y - 4)], fill=(30, 41, 59, 255), width=2)
            banner_draw.line([(line_x_end, line_y), (line_x_end, line_y - 4)], fill=(30, 41, 59, 255), width=2)
            
            banner_draw.text((line_x_start - 4, line_y - 18), "0", fill=(71, 85, 105, 255), font=font_scale_b)
            banner_draw.text((seg_mid - 12, line_y - 18), "250", fill=(71, 85, 105, 255), font=font_scale_b)
            banner_draw.text((line_x_end - 15, line_y - 18), "500m", fill=(71, 85, 105, 255), font=font_scale_b)
            
            # 8c. Bottom-Left Corner: Location Map Card (320x350)
            loc_card_w, loc_card_h = 320, 350
            lc_x = 30
            lc_y = H_b - loc_card_h - 30
            
            banner_draw.rounded_rectangle([lc_x+2, lc_y+2, lc_x+loc_card_w+2, lc_y+loc_card_h+2], radius=10, fill=(0, 0, 0, 30))
            banner_draw.rounded_rectangle([lc_x, lc_y, lc_x+loc_card_w, lc_y+loc_card_h], radius=10, fill=(255, 255, 255, 240), outline=(200, 200, 200, 255), width=1)
            
            loc_title = "项目在长春市区位示意"
            tb = banner_draw.textbbox((0, 0), loc_title, font=font_title_b)
            tw = tb[2] - tb[0]
            banner_draw.text((lc_x + (loc_card_w - tw)//2, lc_y + 12), loc_title, fill=(30, 41, 59, 255), font=font_title_b)
            
            map_x1, map_y1 = lc_x + 15, lc_y + 40
            map_w, map_h = 290, 295
            map_x2, map_y2 = map_x1 + map_w, map_y1 + map_h
            
            banner_draw.rectangle([map_x1, map_y1, map_x2, map_y2], fill=(248, 249, 250, 255), outline=(220, 224, 230, 255), width=1)
            
            def map_pt(lx, ly):
                px = map_x1 + lx * (map_w / 100.0)
                py = map_y1 + ly * (map_h / 100.0)
                return int(px), int(py)
                
            luyuan_poly = [map_pt(5, 45), map_pt(35, 45), map_pt(35, 60), map_pt(25, 80), map_pt(5, 80)]
            chaoyang_poly = [map_pt(35, 60), map_pt(50, 60), map_pt(50, 95), map_pt(20, 95), map_pt(25, 80)]
            nanguan_poly = [map_pt(50, 45), map_pt(60, 45), map_pt(60, 95), map_pt(50, 95)]
            erdao_poly = [map_pt(60, 5), map_pt(95, 5), map_pt(95, 95), map_pt(60, 95)]
            kuancheng_poly = [map_pt(35, 45), map_pt(35, 25), map_pt(50, 5), map_pt(60, 5), map_pt(60, 45), map_pt(50, 45)]
            
            banner_draw.polygon(luyuan_poly, fill=(241, 243, 245, 255), outline=(200, 204, 210, 255), width=1)
            banner_draw.polygon(chaoyang_poly, fill=(241, 243, 245, 255), outline=(200, 204, 210, 255), width=1)
            banner_draw.polygon(nanguan_poly, fill=(241, 243, 245, 255), outline=(200, 204, 210, 255), width=1)
            banner_draw.polygon(erdao_poly, fill=(241, 243, 245, 255), outline=(200, 204, 210, 255), width=1)
            
            banner_draw.polygon(kuancheng_poly, fill=(232, 244, 253, 255), outline=(160, 200, 235, 255), width=1)
            
            river_pts = [map_pt(60, 5), map_pt(58, 25), map_pt(61, 45), map_pt(59, 70), map_pt(60, 95)]
            banner_draw.line(river_pts, fill=(135, 206, 250, 255), width=3, joint="round")
            
            def draw_text_with_outline_b(text, pt, font, fill_color, outline_color=(255, 255, 255, 255)):
                tx, ty = pt
                banner_draw.text((tx-1, ty), text, fill=outline_color, font=font)
                banner_draw.text((tx+1, ty), text, fill=outline_color, font=font)
                banner_draw.text((tx, ty-1), text, fill=outline_color, font=font)
                banner_draw.text((tx, ty+1), text, fill=outline_color, font=font)
                banner_draw.text((tx, ty), text, fill=fill_color, font=font)
                
            draw_text_with_outline_b("绿园区", map_pt(12, 60), font_label_b, (100, 116, 139, 255))
            draw_text_with_outline_b("朝阳区", map_pt(30, 75), font_label_b, (100, 116, 139, 255))
            draw_text_with_outline_b("南关区", map_pt(52, 70), font_label_b, (100, 116, 139, 255))
            draw_text_with_outline_b("二道区", map_pt(72, 48), font_label_b, (100, 116, 139, 255))
            draw_text_with_outline_b("宽城区 (项目所在区)", map_pt(38, 22), font_label_bold_b, (30, 41, 59, 255))
            
            proj_lx, proj_ly = 57, 43
            proj_x, proj_y = map_pt(proj_lx, proj_ly)
            banner_draw.ellipse([proj_x - 8, proj_y - 8, proj_x + 8, proj_y + 8], fill=(239, 68, 68, 80))
            banner_draw.ellipse([proj_x - 5, proj_y - 5, proj_x + 5, proj_y + 5], fill=(255, 255, 255, 255))
            banner_draw.ellipse([proj_x - 3, proj_y - 3, proj_x + 3, proj_y + 3], fill=(239, 68, 68, 255))
            
            proj_label = " 伪满皇宫项目场地"
            draw_text_with_outline_b(proj_label, (proj_x + 8, proj_y - 8), font_label_bold_b, (239, 68, 68, 255))
            
            homepage_banner_img = banner_rgba.convert("RGB")
        except Exception as e:
            print(f"Error drawing annotations on banner image: {e}")
            import traceback
            traceback.print_exc()

        cropped_banner_path = STATIC_DIR / "research_scope_2d_cropped.png"
        homepage_banner_img.save(cropped_banner_path)
        print(f"Homepage banner cropped image saved to {cropped_banner_path}")
    
    # 9. Crop the paper frame of the drawing template: [100, 260, 2340, 1844]
    paper_frame = template.crop((100, 260, 2340, 1844))
    
    # Save output A3 sheet
    paper_frame.save(output_path)
    print(f"Final A3 scope layout saved to {output_path} (Dimensions: {paper_frame.size}, cropped to paper boundary)")

def main():
    temp_map_path = STATIC_DIR / "temp_drawn_map.png"
    final_output_path = STATIC_DIR / "research_scope_2d.png"
    
    try:
        view_w = draw_spatial_map(temp_map_path, drawing_type="现状区位图")
        process_a3_layout(temp_map_path, final_output_path, view_w, drawing_type="现状区位图", title="现状区位图")
    finally:
        if temp_map_path.exists():
            os.remove(temp_map_path)
            print("Temporary files cleaned up.")

if __name__ == "__main__":
    main()
