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
    cover = Image.new("RGB", (2440, 2000), color=(255, 255, 255))
    draw = ImageDraw.Draw(cover)
    
    font_large_title = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 64) # Bold YaHei
    font_sub_title = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 32)
    font_body = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 24)
    font_stamp = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 36)
    
    # Draw decorative lines simulating digital twin networks
    draw.rectangle([100, 260, 140, 1844], fill=(217, 119, 6)) # amber-600 gold strip
    
    for y in range(400, 1600, 150):
        draw.line([(200, y), (2200, y)], fill=(226, 232, 240), width=1)
    for x in range(300, 2100, 200):
        draw.line([(x, 300), (x, 1700)], fill=(226, 232, 240), width=1)
        
    draw.text((250, 450), "数字孪生 · 古今共振", fill=(217, 119, 6), font=font_stamp)
    draw.text((250, 520), "DIGITAL TWIN & HISTORICAL RESONANCE", fill=(148, 163, 184), font=font_sub_title)
    
    draw.text((250, 680), "长春市宽城区伪满皇宫周边街区更新规划设计", fill=(15, 23, 42), font=font_large_title)
    draw.text((250, 780), "Urban Renewal Design of Neighborhood Surrounding the Puppet Emperor's Palace, Changchun", fill=(71, 85, 105), font=font_sub_title)
    
    draw.rectangle([250, 920, 750, 924], fill=(217, 119, 6))
    
    draw.text((250, 980), "规划图册集 / URBAN RENEWAL ATLAS", fill=(15, 23, 42), font=font_stamp)
    
    meta_y = 1200
    draw.text((250, meta_y), "设计单位：吉林建筑大学建筑与规划学院", fill=(71, 85, 105), font=font_body)
    draw.text((250, meta_y + 50), f"设计团队：城乡规划211班 {author} ({author_id})", fill=(71, 85, 105), font=font_body)
    draw.text((250, meta_y + 100), "指导教师：崔诚慧", fill=(71, 85, 105), font=font_body)
    draw.text((250, meta_y + 150), "时间：2026.6", fill=(71, 85, 105), font=font_body)
    
    paper_frame = cover.crop((100, 260, 2340, 1844))
    paper_frame.save(output_path)
    print(f"Cover page generated and saved to {output_path}")

def draw_toc(output_path, author="陈礼冲", author_id="202111003", organization="吉林建筑大学建筑与规划学院\n城乡规划211班"):
    print("Generating Table of Contents...")
    template = Image.open(STATIC_DIR / 'a3_layout_preview_full.png').convert('RGB')
    draw = ImageDraw.Draw(template)
    
    font_title = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 24)
    font_body = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 13)
    font_body_bold = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 14)
    
    draw.rectangle([183, 289, 1888, 1658], fill=(248, 250, 252))
    
    draw.text((250, 310), "图册目录 / TABLE OF CONTENTS", fill=(15, 23, 42), font=font_title)
    draw.rectangle([250, 345, 1820, 347], fill=(226, 232, 240))
    
    draw.text((250, 360), "图纸编号 / CODE", fill=(100, 116, 139), font=font_body_bold)
    draw.text((420, 360), "图纸名称 / SHEET NAME", fill=(100, 116, 139), font=font_body_bold)
    draw.text((700, 360), "图纸表达内容与说明 / DESCRIPTION", fill=(100, 116, 139), font=font_body_bold)
    draw.rectangle([250, 385, 1820, 387], fill=(203, 213, 225))
    
    sheets = [
        ("DR-001", "规划设计图册封面", "图册主标题与设计团队信息"),
        ("DR-002", "图册目录", "本图册的图纸索引与主要编制说明"),
        # Section 1
        ("一、现状调查与诊断篇", "STATUS & DIAGNOSIS", "------------------------------------------------------------------------------------------------------------------------"),
        ("DR-004", "现状区位图", "规划研究范围及5大重点更新地块现状区位"),
        ("DR-005", "研究范围图", "明确研究范围、设计范围和重点地块边界"),
        ("DR-013", "数据来源与遥感现状图", "2024最新高分辨率遥感影像底图叠加"),
        ("DR-014", "用地现状分析图", "二类居住用地、商业用地、混合及工业遗存用地现状分布"),
        ("DR-017", "建筑高度现状图", "现状1-3层低层建筑、4-7层多层建筑及高层建筑层高分布"),
        ("DR-018", "建筑风貌识别图", "现状历史保护风貌、附属景观风貌、现代风貌分布识别"),
        ("DR-019", "历史建筑与工业遗产分布图", "现状重点历史遗存及中车老旧厂房工业遗产保护界线"),
        ("DR-020", "道路交通现状图", "城市快速路、主干路、次干路、支路及现状京哈线分布"),
        ("DR-021", "空间句法可达性分析图", "路网拓扑全局与步行可达性分析，协同度散点图表达"),
        ("DR-030", "环境品质问题地图", "识别低绿视率点、铁路噪声割裂带和界面痛点"),
        # Section 2
        ("二、策略规划与方案篇", "STRATEGY & DESIGN PLANS", "------------------------------------------------------------------------------------------------------------------------"),
        ("DR-040", "更新模式分区图", "保护修缮、整治提升、功能置换、拆改更新分区分布"),
        ("DR-042", "空间结构规划图", "规划“一核、双轴、五地块”的总体更新规划结构"),
        ("DR-044", "总体规划图", "商业与文创混合区布局、绿化修补与微更新布局"),
        ("DR-048", "建筑更新控制图", "保留、修缮、整治、置换、新建建筑控制分布"),
        ("DR-049", "建筑高度控制图", "伪满皇宫周边限高9m/18m/24m的三级分区控制"),
        ("DR-051", "道路交通系统规划图", "规划小街区密路网及内外交通转换顺畅组织"),
        ("DR-056", "绿地景观系统图", "伊通河滨水生态廊道与街区绿色触角蓝绿空间"),
        ("DR-057", "历史文化展示系统图", "文化游线展示路径与解说设施展示布点分布"),
        ("DR-081", "AIGC技术推演过程图", "NLP诊断、ControlNet手绘生成与LLM智能体协同决策"),
        ("DR-082", "实施分期图", "近期、中期、远期实施地块与分期更新节奏控制"),
        ("DR-083", "图册章节结构导图", "规划设计图册全册文章结构与页面导向脉络图"),
        ("DR-084", "数据处理管线导图", "GIS、遥感、街景绿视率及社交媒体情感分析处理流程"),
        ("DR-085", "规划协同工作流程图", "多源数据诊断、AIGC协同方案推演与指标闭环流程图"),
        ("DR-086", "城乡规划知识体系导图", "空间规划编制层级划分与三区三线用途管制知识框架"),
    ]
    
    y = 395
    spacing = 30
    for code, name, desc in sheets:
        if code in ["一、现状调查与诊断篇", "二、策略规划与方案篇"]:
            draw.rectangle([250, y, 1820, y + 24], fill=(230, 235, 245))
            draw.text((260, y + 2), code, fill=(15, 23, 42), font=font_body_bold)
            draw.text((420, y + 2), name, fill=(71, 85, 105), font=font_body_bold)
            y += spacing
            continue
            
        draw.text((250, y), code, fill=(15, 23, 42) if "DR-" in code else (100, 116, 139), font=font_body_bold)
        draw.text((420, y), name, fill=(15, 23, 42), font=font_body)
        draw.text((700, y), desc, fill=(71, 85, 105), font=font_body)
        draw.rectangle([250, y + 24, 1820, y + 25], fill=(241, 245, 249))
        y += spacing
        
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
    draw.line([(1890, 1734), (2312, 1734)], fill=(15, 23, 42), width=1)
    draw.line([(2090, 1734), (2090, 1816)], fill=(15, 23, 42), width=1)
    
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
        
    draw.text((1905, 1742), "制作人 / AUTHOR", fill=(120, 120, 125), font=font_stamp_label)
    draw.text((1905, 1768), author, fill=(15, 23, 42), font=font_stamp_title)
    
    draw.text((2105, 1742), "学号 / ID", fill=(120, 120, 125), font=font_stamp_label)
    draw.text((2105, 1768), author_id, fill=(15, 23, 42), font=font_stamp_body)
    
    draw.rectangle([184, 1661, 1887, 1815], fill=(248, 250, 252))
    draw.text((210, 1670), "设计说明与规划指标 (Design Notes & Planning Indicators)", fill=(29, 29, 31), font=font_title)
    
    desc_lines = [
        "1. 编制目的：本图册旨在通过多源城市大数据分析与系统制图，对长春市宽城区伪满皇宫周边150公顷研究范围进行现状诊断与更新规划。",
        "2. 成果结构：本图册分为“现状调查与诊断篇”与“策略规划与方案篇”，侧重于空间物理诊断与多尺度方案的AI辅助推演设计表达。",
        "3. 数据基准：所有制图地理底图均采用 WGS-84 坐标系，核心矢量图层经由实地踏勘修正，保障现状测算与规划设计红线的精确度。"
    ]
    y_desc = 1712
    for line in desc_lines:
        draw.text((210, y_desc), line, fill=(72, 72, 74), font=font_body)
        y_desc += 32
        
    paper_frame = template.crop((100, 260, 2340, 1844))
    paper_frame.save(output_path)
    print(f"Table of Contents generated and saved to {output_path}")

def generate_single_sheet(args):
    drawing_type, filename, code = args
    print(f"Generating sheet: {filename}...")
    output_path = ATLAS_DIR / filename
    temp_map_path = STATIC_DIR / f"temp_drawn_map_{code}.png"
    try:
        view_w = draw_spatial_map(temp_map_path, drawing_type=drawing_type)
        title_to_use = "系统架构图" if drawing_type == "AIGC技术推演过程图" else drawing_type
        process_a3_layout(
            map_path=temp_map_path,
            output_path=str(output_path),
            view_w=view_w,
            drawing_type=drawing_type,
            title=title_to_use,
            drawing_number=code
        )
        print(f"Successfully saved {filename}")
    except Exception as e:
        print(f"Failed to generate {filename}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if temp_map_path.exists():
            try:
                os.remove(temp_map_path)
            except Exception:
                pass

def generate_all_atlas_drawings(targets=None):
    ATLAS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Generate Cover
    if not targets or any(t.upper() in "DR-001" or t.upper() in "封面" for t in targets):
        draw_cover(ATLAS_DIR / "DR-001_规划设计图册封面.png")
    
    # 2. Generate TOC
    if not targets or any(t.upper() in "DR-002" or t.upper() in "目录" for t in targets):
        draw_toc(ATLAS_DIR / "DR-002_图册目录.png")
    
    # 3. Generate GIS Drawings
    gis_drawings = [
        ("现状区位图", "DR-004_现状区位图.png", "DR-004"),
        ("研究范围图", "DR-005_研究范围图.png", "DR-005"),
        ("卫星图", "DR-013_数据来源与遥感现状图.png", "DR-013"),
        ("土地利用现状图", "DR-014_用地现状分析图.png", "DR-014"),
        ("建筑高度现状图", "DR-017_建筑高度现状图.png", "DR-017"),
        ("建筑风貌现状图", "DR-018_建筑风貌识别图.png", "DR-018"),
        ("历史建筑与工业遗产分布图", "DR-019_历史建筑与工业遗产分布图.png", "DR-019"),
        ("交通分析图", "DR-020_道路交通现状图.png", "DR-020"),
        ("空间句法可达性分析图", "DR-021_空间句法可达性分析图.png", "DR-021"),
        ("环境品质问题地图", "DR-030_环境品质问题地图.png", "DR-030"),
        ("更新模式分区图", "DR-040_更新模式分区图.png", "DR-040"),
        ("空间结构规划图", "DR-042_空间结构规划图.png", "DR-042"),
        ("总平面图", "DR-044_总体规划图.png", "DR-044"),
        ("建筑更新控制图", "DR-048_建筑更新控制图.png", "DR-048"),
        ("建筑高度控制图", "DR-049_建筑高度控制图.png", "DR-049"),
        ("道路交通系统规划图", "DR-051_道路交通系统规划图.png", "DR-051"),
        ("绿地景观系统图", "DR-056_绿地景观系统图.png", "DR-056"),
        ("历史文化展示系统图", "DR-057_历史文化展示系统图.png", "DR-057"),
        ("AIGC技术推演过程图", "DR-081_AIGC技术推演过程图.png", "DR-081"),
        ("实施分期图", "DR-082_实施分期图.png", "DR-082"),
        ("图册章节结构导图", "DR-083_图册章节结构导图.png", "DR-083"),
        ("数据处理管线导图", "DR-084_数据处理管线导图.png", "DR-084"),
        ("规划协同工作流程图", "DR-085_规划协同工作流程图.png", "DR-085"),
        ("城乡规划知识体系导图", "DR-086_城乡规划知识体系导图.png", "DR-086"),
    ]
    
    if targets:
        gis_drawings = [
            d for d in gis_drawings 
            if any(t.upper() in d[2].upper() or t.upper() in d[1].upper() for t in targets)
        ]
        
    if not gis_drawings:
        print("No matching GIS drawings to generate.")
        return
        
    import multiprocessing
    num_workers = min(multiprocessing.cpu_count(), 8, len(gis_drawings))
    print(f"Starting parallel generation of {len(gis_drawings)} sheets using {num_workers} processes...")
    
    with multiprocessing.Pool(processes=num_workers) as pool:
        pool.map(generate_single_sheet, gis_drawings)

if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else None
    generate_all_atlas_drawings(targets)
