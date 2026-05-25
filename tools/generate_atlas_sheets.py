# tools/generate_atlas_sheets.py
import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.draw_scope_map import draw_spatial_map, process_a3_layout

STATIC_DIR = ROOT / "static"
ASSETS_DIR = ROOT / "assets"
ATLAS_DIR = STATIC_DIR / "atlas"

def draw_cover(output_path, author="陈礼冲", author_id="202111003", organization="吉林建筑大学建筑与规划学院\n城乡规划211班"):
    print("Generating Cover page...")
    cover = Image.new("RGB", (2440, 2000), color=(15, 23, 42)) # Deep Slate Blue #0F172A
    draw = ImageDraw.Draw(cover)
    
    font_large_title = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 64) # Bold YaHei
    font_sub_title = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 32)
    font_body = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 24)
    font_stamp = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 36)
    
    # Draw decorative lines simulating digital twin networks
    draw.rectangle([100, 260, 140, 1844], fill=(217, 119, 6)) # amber-600 gold strip
    
    for y in range(400, 1600, 150):
        draw.line([(200, y), (2200, y)], fill=(30, 41, 59), width=1)
    for x in range(300, 2100, 200):
        draw.line([(x, 300), (x, 1700)], fill=(30, 41, 59), width=1)
        
    draw.text((250, 450), "数字孪生 · 古今共振", fill=(217, 119, 6), font=font_stamp)
    draw.text((250, 520), "DIGITAL TWIN & HISTORICAL RESONANCE", fill=(148, 163, 184), font=font_sub_title)
    
    draw.text((250, 680), "长春市宽城区伪满皇宫周边街区更新规划设计", fill=(255, 255, 255), font=font_large_title)
    draw.text((250, 780), "Urban Renewal Design of Neighborhood Surrounding the Puppet Emperor's Palace, Changchun", fill=(148, 163, 184), font=font_sub_title)
    
    draw.rectangle([250, 920, 750, 924], fill=(217, 119, 6))
    
    draw.text((250, 980), "现状调研与诊断图册 / DIAGNOSIS ATLAS", fill=(255, 255, 255), font=font_stamp)
    
    meta_y = 1200
    draw.text((250, meta_y), "设计单位：吉林建筑大学建筑与规划学院", fill=(226, 232, 240), font=font_body)
    draw.text((250, meta_y + 50), f"设计团队：城乡规划211班 {author} ({author_id})", fill=(226, 232, 240), font=font_body)
    draw.text((250, meta_y + 100), "指导教师：规划设计教师组", fill=(226, 232, 240), font=font_body)
    draw.text((250, meta_y + 150), "时间：2026年5月", fill=(226, 232, 240), font=font_body)
    
    paper_frame = cover.crop((100, 260, 2340, 1844))
    paper_frame.save(output_path)
    print(f"Cover page generated and saved to {output_path}")

def draw_toc(output_path, author="陈礼冲", author_id="202111003", organization="吉林建筑大学建筑与规划学院\n城乡规划211班"):
    print("Generating Table of Contents...")
    template = Image.open(STATIC_DIR / 'a3_layout_preview_full.png').convert('RGB')
    draw = ImageDraw.Draw(template)
    
    font_title = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 24)
    font_body = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 15)
    font_body_bold = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 16)
    
    draw.rectangle([183, 289, 1888, 1658], fill=(248, 250, 252))
    
    draw.text((250, 325), "图册目录 / TABLE OF CONTENTS", fill=(15, 23, 42), font=font_title)
    draw.rectangle([250, 365, 1820, 367], fill=(226, 232, 240))
    
    draw.text((250, 385), "图纸编号 / CODE", fill=(100, 116, 139), font=font_body_bold)
    draw.text((450, 385), "图纸名称 / SHEET NAME", fill=(100, 116, 139), font=font_body_bold)
    draw.text((850, 385), "图纸表达内容与说明 / DESCRIPTION", fill=(100, 116, 139), font=font_body_bold)
    draw.rectangle([250, 410, 1820, 412], fill=(203, 213, 225))
    
    sheets = [
        ("DR-000", "规划设计图册封面", "图册主标题与设计团队信息"),
        ("TOC-01", "图册目录", "本图册的图纸索引与主要编制说明"),
        # Section 1
        ("现状调查与诊断篇", "STATUS & DIAGNOSIS", "------------------------------------------------------------------------------------------"),
        ("DR-001", "现状区位图", "规划研究范围及5大重点更新地块现状区位"),
        ("DR-002", "卫星现状图", "2024最新高分辨率遥感影像底图叠加"),
        ("DR-003", "土地利用现状图", "二类居住用地、商业用地、混合及工业遗存用地现状分布"),
        ("DR-004", "交通与道路分析图", "城市快速路、主干路、次干路、支路及现状京哈线分布"),
        ("DR-005", "历史建筑与工业遗产分布图", "现状重点历史遗存及中车老旧厂房工业遗产保护界线"),
        ("DR-006", "建筑高度现状图", "现状1-3层低层建筑、4-7层多层建筑及高层建筑层高分布"),
        ("DR-007", "建筑风貌现状图", "现状历史保护风貌、附属景观风貌、现代风貌分布识别"),
    ]
    
    y = 435
    for code, name, desc in sheets:
        if code in ["现状调查与诊断篇"]:
            draw.rectangle([250, y, 1820, y + 26], fill=(230, 235, 245))
            draw.text((260, y + 3), code, fill=(15, 23, 42), font=font_body_bold)
            draw.text((450, y + 3), name, fill=(71, 85, 105), font=font_body_bold)
            y += 36
            continue
            
        draw.text((250, y), code, fill=(15, 23, 42) if "DR-" in code or "TOC" in code else (100, 116, 139), font=font_body_bold)
        draw.text((450, y), name, fill=(15, 23, 42), font=font_body)
        draw.text((850, y), desc, fill=(71, 85, 105), font=font_body)
        draw.rectangle([250, y + 26, 1820, y + 27], fill=(241, 245, 249))
        y += 38
        
    windrose = Image.open(ASSETS_DIR / '长春市风玫瑰.png')
    draw.rectangle([1891, 292, 2309, 605], fill=(255, 255, 255))
    wr_w, wr_h = windrose.size
    new_h = 200
    new_w = int(new_h * wr_w / wr_h)
    wr_resized = windrose.resize((new_w, new_h), Image.Resampling.LANCZOS)
    template.paste(wr_resized, (1891 + (418 - new_w) // 2, 292 + (313 - new_h) // 2), wr_resized if wr_resized.mode == 'RGBA' else None)
    
    draw.rectangle([1890, 1394, 2312, 1816], fill=(241, 245, 249), outline=(15, 23, 42), width=2)
    draw.line([(1890, 1464), (2312, 1464)], fill=(15, 23, 42), width=1)
    draw.line([(1890, 1564), (2312, 1564)], fill=(15, 23, 42), width=1)
    draw.line([(1890, 1664), (2312, 1664)], fill=(15, 23, 42), width=1)
    draw.line([(2090, 1664), (2090, 1816)], fill=(15, 23, 42), width=1)
    
    font_stamp_large = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 26)
    font_stamp_title = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 20)
    font_stamp_label = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 12)
    font_stamp_body = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 13)
    
    draw.text((1905, 1406), "图纸名称 / TITLE", fill=(120, 120, 125), font=font_stamp_label)
    draw.text((1905, 1424), "图册目录", fill=(15, 23, 42), font=font_stamp_large)
    
    draw.text((1905, 1472), "项目名称 / PROJECT", fill=(120, 120, 125), font=font_stamp_label)
    draw.text((1905, 1494), "数字孪生·古今共振——", fill=(15, 23, 42), font=font_stamp_body)
    draw.text((1905, 1524), "AI赋能下的伪满皇宫周边街区更新规划设计", fill=(15, 23, 42), font=font_stamp_body)
    
    draw.text((1905, 1572), "学校班级 / ORGANIZATION", fill=(120, 120, 125), font=font_stamp_label)
    org_lines = organization.split('\n')
    org_y = 1594
    for ol in org_lines[:2]:
        draw.text((1905, org_y), ol, fill=(15, 23, 42), font=font_stamp_body)
        org_y += 30
        
    draw.text((1905, 1674), "制作人 / AUTHOR", fill=(120, 120, 125), font=font_stamp_label)
    draw.text((1905, 1710), author, fill=(15, 23, 42), font=font_stamp_title)
    
    draw.text((2105, 1674), "学号 / ID", fill=(120, 120, 125), font=font_stamp_label)
    draw.text((2105, 1710), author_id, fill=(15, 23, 42), font=font_stamp_body)
    
    draw.rectangle([184, 1661, 1887, 1815], fill=(248, 250, 252))
    draw.text((210, 1670), "设计说明与规划指标 (Design Notes & Planning Indicators)", fill=(29, 29, 31), font=font_title)
    
    desc_lines = [
        "1. 编制目的：本图册旨在通过多源城市大数据分析与系统制图，对长春市宽城区伪满皇宫周边150公顷研究范围进行现状诊断与更新规划。",
        "2. 图册分区：本册为“现状调查与诊断篇”，侧重于空间物理属性、历史风貌界线与生态/交通系统的量化梳理，为规划生成打下科学基础。",
        "3. 数据基准：所有制图地理底图均采用 WGS-84 坐标系，核心矢量图层经由实地踏勘修正，保障现状测算与规划设计红线的精确度。"
    ]
    y_desc = 1712
    for line in desc_lines:
        draw.text((210, y_desc), line, fill=(72, 72, 74), font=font_body)
        y_desc += 36
        
    paper_frame = template.crop((100, 260, 2340, 1844))
    paper_frame.save(output_path)
    print(f"Table of Contents generated and saved to {output_path}")

def generate_all_atlas_drawings():
    ATLAS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Generate Cover
    draw_cover(ATLAS_DIR / "DR-000_规划设计图册封面.png")
    
    # 2. Generate TOC
    draw_toc(ATLAS_DIR / "DR-000_图册目录.png")
    
    # 3. Generate GIS Drawings
    gis_drawings = [
        ("现状区位图", "DR-001_现状区位图.png", "DR-001"),
        ("卫星图", "DR-002_卫星现状图.png", "DR-002"),
        ("土地利用现状图", "DR-003_土地利用现状图.png", "DR-003"),
        ("交通分析图", "DR-004_交通与道路分析图.png", "DR-004"),
        ("历史建筑与工业遗产分布图", "DR-005_历史建筑与工业遗产分布图.png", "DR-005"),
        ("建筑高度现状图", "DR-006_建筑高度现状图.png", "DR-006"),
        ("建筑风貌现状图", "DR-007_建筑风貌现状图.png", "DR-007"),
    ]
    
    temp_map_path = STATIC_DIR / "temp_drawn_map_batch.png"
    
    for drawing_type, filename, code in gis_drawings:
        print(f"Generating sheet: {filename}...")
        output_path = ATLAS_DIR / filename
        
        try:
            view_w = draw_spatial_map(temp_map_path, drawing_type=drawing_type)
            process_a3_layout(
                map_path=temp_map_path,
                output_path=str(output_path),
                view_w=view_w,
                drawing_type=drawing_type,
                title=drawing_type,
                drawing_number=code
            )
            print(f"Successfully saved {filename}")
        except Exception as e:
            print(f"Failed to generate {filename}: {e}")
        finally:
            if temp_map_path.exists():
                os.remove(temp_map_path)

if __name__ == "__main__":
    generate_all_atlas_drawings()
