# tools/generate_atlas_sheets.py
import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.draw_scope_map import draw_spatial_map, process_a3_layout, wrap_text_by_pixels

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
    # Create a clean canvas of 2240x1584
    toc_img = Image.new("RGB", (2240, 1584), color=(248, 250, 252)) # slate-50
    draw = ImageDraw.Draw(toc_img)

    # Fonts loading
    font_path = 'C:/Windows/Fonts/msyh.ttc'
    font_bold_path = 'C:/Windows/Fonts/msyhbd.ttc'
    try:
        font_large_title = ImageFont.truetype(font_bold_path, 36)
        font_card_title = ImageFont.truetype(font_bold_path, 20)
        font_table_header = ImageFont.truetype(font_bold_path, 15)
        font_body_bold = ImageFont.truetype(font_bold_path, 12)
        font_body = ImageFont.truetype(font_path, 12)
        font_desc = ImageFont.truetype(font_path, 15)
        font_desc_bold = ImageFont.truetype(font_bold_path, 15)
    except IOError:
        font_large_title = ImageFont.load_default()
        font_card_title = ImageFont.load_default()
        font_table_header = ImageFont.load_default()
        font_body_bold = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_desc = ImageFont.load_default()
        font_desc_bold = ImageFont.load_default()

    # Draw background grid
    grid_spacing = 79.2  # 5 units in coordinate space
    for x in range(1, int(2240 / grid_spacing)):
        lx = int(x * grid_spacing)
        draw.line([(lx, 0), (lx, 1584)], fill=(226, 232, 240), width=1)
    for y in range(1, int(1584 / grid_spacing)):
        ly = int(y * grid_spacing)
        draw.line([(0, ly), (2240, ly)], fill=(226, 232, 240), width=1)

    # 1. Header Card (X: 32 to 2198, Y: 60 to 174)
    draw.rectangle([36, 64, 2202, 178], fill=(226, 232, 240)) # drop shadow
    draw.rectangle([32, 60, 2198, 174], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 60, 2198, 66], fill=(217, 119, 6)) # top accent bar
    
    draw.text((55, 117), "图册目录", fill=(15, 23, 42), font=font_large_title, anchor="lm")
    draw.text((230, 117), "本图册的图纸索引与主要编制说明。本规划旨在重塑历史地段活力，推动数字孪生与古今共振。", 
              fill=(100, 116, 139), font=font_desc, anchor="lm")

    # 2. Left giant Table of Contents Card (X: 32 to 1584, Y: 206 to 1520)
    draw.rectangle([36, 210, 1588, 1524], fill=(226, 232, 240)) # drop shadow
    draw.rectangle([32, 206, 1584, 1520], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 206, 1584, 212], fill=(217, 119, 6)) # top accent bar

    draw.text((60, 250), "图例分类与图纸索引 / TABLE OF CONTENTS", fill=(217, 119, 6), font=font_card_title)
    
    # Table headers
    draw.text((80, 300), "图纸编号 / CODE", fill=(100, 116, 139), font=font_table_header)
    draw.text((220, 300), "图纸名称 / SHEET NAME", fill=(100, 116, 139), font=font_table_header)
    draw.text((550, 300), "图纸表达内容与说明 / DESCRIPTION", fill=(100, 116, 139), font=font_table_header)
    draw.line([(60, 325), (1556, 325)], fill=(203, 213, 225), width=2)

    sheets = [
        ("DR-001", "规划设计图册封面", "图册主标题与设计团队信息"),
        ("DR-002", "图册目录", "本图册的图纸索引与主要编制说明"),
        # 第1章 项目认知篇
        ("第1章 项目认知篇", "PROJECT BACKGROUND", "-------------------------------------------------------------------------------------------------------------"),
        ("DR-003", "项目背景与政策解读图", "国家城市更新·数字中国·历史名城三级政策框架"),
        ("DR-004", "现状区位图", "包含国家、省、市、区四级区位关系展示"),
        ("DR-005", "研究范围图", "约170公顷范围及5大重点地块设计边界"),
        ("A原始数据", "原始数据清单", "遥感影像、GVI、现状路网等14项核心现状底数"),
        ("DR-007", "上位规划解读图", "总体格局、历史保护与空间结构解译"),
        ("DR-008", "上位专项规划解读图", "土地利用、综合交通与绿地系统专项解译"),
        ("DR-068", "案例借鉴与对标分析图", "国内外类似片区更新案例参照"),
        # 第2章 数据诊断篇
        ("第2章 数据诊断篇", "DATA DIAGNOSIS & ANALYSIS", "-------------------------------------------------------------------------------------------------------------"),
        ("DR-013", "数据来源与遥感现状图", "2024高分辨率遥感影像底图及GIS数据源"),
        ("DR-014", "用地现状分析图", "居住56.6%、商服约20%等非均衡现状结构"),
        ("DR-020", "道路交通现状图", "宽马路表征与现状铁路割裂带分布诊断"),
        ("DR-017", "建筑高度现状图", "平均层高11.9米，低层及老旧住宅为主"),
        ("DR-018", "建筑风貌识别图", "历史保护、中车工业遗存与现代风貌分布"),
        ("DR-030", "环境品质问题地图", "绿视率仅8.7%硬质化区域与噪声污染源空间"),
        ("DR-028", "街区景观品质分析图", "平均绿视率仅8.7%，78.3%的采样点低于15%宜居阈值"),
        ("DR-019", "历史建筑与工业遗产分布图", "伪满皇宫核心区及中车老厂房遗存定位"),
        ("DR-023", "文化资源分析图", "伪满皇宫与中车厂区双核集聚及轴线割裂格局"),
        ("DR-032", "遗产价值评估热力图", "基于多准则分析的历史文化遗产价值衰减"),
        ("DR-027", "POI产业活力分析图", "生活服务及餐饮占40%、购物占4.9%的业态分布"),
        ("DR-029", "人群需求与老龄化分布图", "30%老龄化社区适老化设施500米供需缺口"),
        ("DR-021", "空间句法可达性分析图", "路网拓扑分析步行整合度与车行选择度"),
        ("DR-059", "综合现状问题诊断图", "四大问题汇总诊断与问题热点标注"),
        ("DR-061", "MPI更新潜力评估图", "AHP-MPI指数空间分布热力图"),
        # 第3章 设计理念与构思篇
        ("第3章 设计理念与构思篇", "DESIGN CONCEPT & STRATEGY", "-------------------------------------------------------------------------------------------------------------"),
        ("A数学公式", "核心算法与数学公式目录", "三维度综合加权评估、天际线纵深指数等13项公式"),
        ("A核心代码清单", "平台核心代码文件清单", "空间统计引擎、多智能体协同等14项核心引擎代码"),
        ("DR-037", "设计原则与理念图", "微创织补与全龄友好为核心的四项设计原则"),
        ("DR-038", "设计目标体系图", "生态韧性、全龄服务与风貌管控量化目标"),
        ("DR-039", "总体策略图", "微创修缮、细胞微更新与慢行系统搭桥"),
        # 第4章 总体规划篇
        ("第4章 总体规划篇", "MASTER PLAN DESIGN", "-------------------------------------------------------------------------------------------------------------"),
        ("DR-058", "总体鸟瞰白模效果图", "整体空间形态、建筑体量、景观系统白模展示"),
        ("DR-044", "用地规划图", "商业与文创混合区布局、结构优化与总体设计"),
        ("DR-049", "建筑高度控制图", "核心9米、过渡18米、外围24米三级管控"),
        ("DR-051", "道路交通系统规划图", "加密支路网，提升微循环与交通整合度"),
        ("DR-053", "慢行系统规划图", "无障碍适老化慢跑道与景观漫步双环系统"),
        ("DR-042", "空间结构规划图", "规划'一核、一廊、多点'的总体空间结构"),
        ("DR-055", "公共空间系统图", "500米半径5个邻里细胞生活盒子精准补缺"),
        ("DR-046", "产业业态规划图", "'三区一带'数字文创与全龄服务业态规划"),
        ("DR-056", "绿地景观系统图", "伊通河滨水生态廊道及绿地率35%的补绿规划"),
        ("DR-057", "历史文化展示系统图", "核心区文化游线路径与视觉通廊控制规划"),
        ("DR-040", "更新模式分区图", "保护修缮、整治提升、拆改更新控制分区"),
        ("DR-048", "建筑更新控制图", "建筑分类更新控制、修缮整治置换措施引导"),
        ("DR-065", "日照与风环境分析图", "CFD模拟或日照时数分析"),
        ("DR-069", "功能分区与策划定位图", "片区功能定位与策划方向"),
        ("DR-070", "开发强度与容积率分区策略图", "FAR分级控制策略"),
        ("DR-071", "天际线与视觉通廊控制图", "关键视廊保护与限高策略"),
        # 第5章 重点地块深化篇
        ("第5章 重点地块深化篇", "KEY PLOT DESIGN", "-------------------------------------------------------------------------------------------------------------"),
        ("DR-076", "五地块深化设计总图", "老水产、调料市场等5大深化地块核心指标"),
        ("DR-081", "AIGC技术推演过程图", "数字孪生—AIGC推演—MPI评估全流程技术矩阵"),
        ("DR-082", "实施分期图", "近期、中期、远期实施地块与分期节奏"),
        ("DR-091~115", "重点地块现状分析图集", "5个重点地块的现状卫星、土地利用、肌理、建筑高度与业态分区"),
        ("DR-116~140", "重点地块改造设计图集", "5个重点地块的改造平面、鸟瞰效果、前后对比、节点景观与指标表"),
        ("DR-072~075", "研究范围补充分析", "竖向排水、智慧基础设施、投资估算、公众参与"),
        # 附录 技术说明
        ("附录 技术说明", "TECHNICAL APPENDIX", "-------------------------------------------------------------------------------------------------------------"),
        ("DR-083", "图册章节结构导图", "图册五大章节与核心规划图纸树状组织结构"),
        ("DR-084", "数据处理管线导图", "多源异构数据至空间计算与GIS库流向管线"),
        ("DR-085", "规划协同工作流程图", "多利益智能体LLM博弈与指标刚性校验流程"),
        ("DR-086", "城乡规划知识体系导图", "上位法理、规划层级至图册成果金字塔树"),
    ]


    y = 338
    spacing = 23
    for code, name, desc in sheets:
        if ("第" in code and "章" in code) or "附录" in code:
            draw.rectangle([60, y - 2, 1556, y + 17], fill=(230, 235, 245))
            draw.text((80, y), code, fill=(15, 23, 42), font=font_body_bold)
            draw.text((220, y), name, fill=(71, 85, 105), font=font_body_bold)
            draw.text((550, y), desc, fill=(148, 163, 184), font=font_body)
        else:
            draw.text((80, y), code, fill=(15, 23, 42) if "DR-" in code or "A" in code else (100, 116, 139), font=font_body_bold)
            draw.text((220, y), name, fill=(15, 23, 42), font=font_body)
            draw.text((550, y), desc, fill=(71, 85, 105), font=font_body)
            draw.line([(60, y + 17), (1556, y + 17)], fill=(241, 245, 249), width=1)
        y += spacing

    # 3. Right Top Card (X: 1608 to 2198, Y: 206 to 602)
    draw.rectangle([1612, 210, 2202, 606], fill=(226, 232, 240)) # drop shadow
    draw.rectangle([1608, 206, 2198, 602], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1608, 206, 2198, 212], fill=(217, 119, 6)) # top accent bar

    draw.text((1630, 240), "图册编制说明 / PURPOSE", fill=(217, 119, 6), font=font_card_title)
    draw.line([(1630, 270), (2176, 270)], fill=(203, 213, 225), width=1)

    desc_lines = [
        "1. 编制目的：本图册旨在通过多源城市大数据分析与系统制图，对长春市宽城区伪满皇宫周边150公顷研究范围进行现状诊断与更新规划。",
        "2. 成果结构：本图册分为“现状调查与诊断篇”与“策略规划与方案篇”，侧重于空间物理诊断与多尺度方案的AI辅助推演设计表达。",
        "3. 数据基准：所有制图地理底图均采用 WGS-84 坐标系，核心矢量图层经由实地踏勘修正，保障现状测算与规划设计红线的精确度。"
    ]
    
    y_desc = 295
    for line in desc_lines:
        wrapped = wrap_text_by_pixels(line, font_desc, 510, draw)
        for wl in wrapped:
            draw.text((1630, y_desc), wl, fill=(71, 85, 105), font=font_desc)
            y_desc += 26
        y_desc += 10

    # 4. Right Bottom Card (X: 1608 to 2198, Y: 634 to 1520)
    draw.rectangle([1612, 638, 2202, 1524], fill=(226, 232, 240)) # drop shadow
    draw.rectangle([1608, 634, 2198, 1520], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([1608, 634, 2198, 640], fill=(217, 119, 6)) # top accent bar

    draw.text((1630, 668), "设计团队与版记 / SIGNATURE", fill=(217, 119, 6), font=font_card_title)
    draw.line([(1630, 698), (2176, 698)], fill=(203, 213, 225), width=1)

    # Stamp details
    details = [
        ("项目名称 / PROJECT NAME", "数字孪生·古今共振——\nAI赋能下的长春宽城区伪满皇宫周边街区更新规划设计"),
        ("设计团队 / AUTHOR TEAM", organization),
        ("制作人 / AUTHOR", f"{author} ({author_id})"),
        ("指导教师 / TUTOR", "崔诚慧"),
        ("制图标准 / STANDARDS", "图幅大小：A3 (420mm x 297mm)\n比例尺：如单图所示\n制图日期：2026年6月")
    ]
    
    y_detail = 720
    for label, val in details:
        draw.text((1630, y_detail), label, fill=(148, 163, 184), font=font_body_bold)
        y_detail += 22
        val_lines = val.split('\n')
        for vl in val_lines:
            draw.text((1630, y_detail), vl, fill=(15, 23, 42), font=font_desc)
            y_detail += 24
        y_detail += 12

    toc_img.save(output_path)
    print(f"Table of Contents generated and saved to {output_path}")

def generate_single_sheet(args):
    drawing_type, filename, code = args
    print(f"Generating sheet: {filename}...")
    output_path = ATLAS_DIR / filename
    if code == "DR-045":
        try:
            from tools.generate_indicator_images import draw_tables
            draw_tables()
            print(f"Successfully generated custom sheet {filename}")
        except Exception as e:
            print(f"Failed to generate custom sheet {filename}: {e}")
        return
    temp_map_path = STATIC_DIR / f"temp_drawn_map_{code}.png"
    try:
        view_w = draw_spatial_map(temp_map_path, drawing_type=drawing_type)
        from tools.draw_scope_map import get_drawing_module
        module = get_drawing_module(drawing_type)
        has_no_frame = (module is not None and getattr(module, "NO_FRAME", False))
        
        if has_no_frame:
            img = Image.open(str(temp_map_path))
            img_resized = img.resize((2240, 1584), Image.Resampling.LANCZOS)
            img_resized.save(str(output_path))
            print(f"Skipped layout template frame and resized to 2240x1584 for {code}.")
        else:
            title_to_use = "用地规划图" if "用地规划图" in drawing_type else ("系统架构图" if drawing_type == "AIGC技术推演过程图" else drawing_type)
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
        # 第1章 项目认知篇
        ("项目背景与政策解读图", "DR-003_项目背景与政策解读图.png", "DR-003"),
        ("现状区位图", "DR-004_现状区位图.png", "DR-004"),
        ("研究范围图", "DR-005_研究范围图.png", "DR-005"),
        ("上位规划解读图", "DR-007_上位规划解读图.png", "DR-007"),
        ("上位专项规划解读图", "DR-008_上位专项规划解读图.png", "DR-008"),
        ("案例借鉴与对标分析图", "DR-068_案例借鉴与对标分析图.png", "DR-068"),
        # 第2章 数据诊断篇
        ("数据来源与遥感现状图", "DR-013_数据来源与遥感现状图.png", "DR-013"),
        ("用地现状分析图", "DR-014_用地现状分析图.png", "DR-014"),
        ("道路交通现状图", "DR-020_道路交通现状图.png", "DR-020"),
        ("建筑高度现状图", "DR-017_建筑高度现状图.png", "DR-017"),
        ("建筑风貌识别图", "DR-018_建筑风貌识别图.png", "DR-018"),
        ("环境品质问题地图", "DR-030_环境品质问题地图.png", "DR-030"),
        ("街区景观品质分析图", "DR-028_街区景观品质分析图.png", "DR-028"),
        ("历史建筑与工业遗产分布图", "DR-019_历史建筑与工业遗产分布图.png", "DR-019"),
        ("文化资源分析图", "DR-023_文化资源分析图.png", "DR-023"),
        ("遗产价值评估热力图", "DR-032_遗产价值评估热力图.png", "DR-032"),
        ("POI产业活力分析图", "DR-027_POI产业活力分析图.png", "DR-027"),
        ("人群需求与老龄化分布图", "DR-029_人群需求与老龄化分布图.png", "DR-029"),
        ("空间句法可达性分析图", "DR-021_空间句法可达性分析图.png", "DR-021"),
        ("综合现状问题诊断图", "DR-059_综合现状问题诊断图.png", "DR-059"),
        ("MPI更新潜力评估图", "DR-061_MPI更新潜力评估图.png", "DR-061"),
        # 第3章 设计理念与构思篇
        ("设计原则与理念图", "DR-037_设计原则与理念图.png", "DR-037"),
        ("设计目标体系图", "DR-038_设计目标体系图.png", "DR-038"),
        ("总体策略图", "DR-039_总体策略图.png", "DR-039"),
        # 第4章 总体规划篇
        ("用地规划图", "DR-044_用地规划图.png", "DR-044"),
        ("用地规划图_带建筑轮廓", "DR-044_用地规划图_带建筑轮廓.png", "DR-044_WITH_BUILDINGS"),
        ("用地规划指标表", "DR-045_用地规划指标表.png", "DR-045"),
        ("建筑高度控制图", "DR-049_建筑高度控制图.png", "DR-049"),
        ("道路交通系统规划图", "DR-051_道路交通系统规划图.png", "DR-051"),
        ("慢行系统规划图", "DR-053_慢行系统规划图.png", "DR-053"),
        ("空间结构规划图", "DR-042_空间结构规划图.png", "DR-042"),
        ("公共空间系统图", "DR-055_公共空间系统图.png", "DR-055"),
        ("产业业态规划图", "DR-046_产业业态规划图.png", "DR-046"),
        ("绿地景观系统图", "DR-056_绿地景观系统图.png", "DR-056"),
        ("历史文化展示系统图", "DR-057_历史文化展示系统图.png", "DR-057"),
        ("更新模式分区图", "DR-040_更新模式分区图.png", "DR-040"),
        ("建筑更新控制图", "DR-048_建筑更新控制图.png", "DR-048"),
        ("日照与风环境分析图", "DR-065_日照与风环境分析图.png", "DR-065"),
        ("功能分区与策划定位图", "DR-069_功能分区与策划定位图.png", "DR-069"),
        ("开发强度与容积率分区策略图", "DR-070_开发强度与容积率分区策略图.png", "DR-070"),
        ("天际线与视觉通廊控制图", "DR-071_天际线与视觉通廊控制图.png", "DR-071"),
        # 第5章 重点地块深化篇
        ("AIGC技术推演过程图", "DR-081_AIGC技术推演过程图.png", "DR-081"),
        ("实施分期图", "DR-082_实施分期图.png", "DR-082"),
        ("五地块深化设计总图", "DR-076_五地块深化设计总图.png", "DR-076"),
        # 重点地块现状分析图集 (DR-091 ~ DR-115)
        ("老水产市场-现状卫星图", "DR-091_老水产市场-现状卫星图.png", "DR-091"),
        ("老水产市场-现状土地利用", "DR-092_老水产市场-现状土地利用.png", "DR-092"),
        ("老水产市场-现状肌理", "DR-093_老水产市场-现状肌理.png", "DR-093"),
        ("老水产市场-现状建筑高度", "DR-094_老水产市场-现状建筑高度.png", "DR-094"),
        ("老水产市场-现状业态分区", "DR-095_老水产市场-现状业态分区.png", "DR-095"),
        ("食品调料市场-现状卫星图", "DR-096_食品调料市场-现状卫星图.png", "DR-096"),
        ("食品调料市场-现状土地利用", "DR-097_食品调料市场-现状土地利用.png", "DR-097"),
        ("食品调料市场-现状肌理", "DR-098_食品调料市场-现状肌理.png", "DR-098"),
        ("食品调料市场-现状建筑高度", "DR-099_食品调料市场-现状建筑高度.png", "DR-099"),
        ("食品调料市场-现状业态分区", "DR-100_食品调料市场-现状业态分区.png", "DR-100"),
        ("市一中北侧-现状卫星图", "DR-101_市一中北侧-现状卫星图.png", "DR-101"),
        ("市一中北侧-现状土地利用", "DR-102_市一中北侧-现状土地利用.png", "DR-102"),
        ("市一中北侧-现状肌理", "DR-103_市一中北侧-现状肌理.png", "DR-103"),
        ("市一中北侧-现状建筑高度", "DR-104_市一中北侧-现状建筑高度.png", "DR-104"),
        ("市一中北侧-现状业态分区", "DR-105_市一中北侧-现状业态分区.png", "DR-105"),
        ("清禾集贸市场-现状卫星图", "DR-106_清禾集贸市场-现状卫星图.png", "DR-106"),
        ("清禾集贸市场-现状土地利用", "DR-107_清禾集贸市场-现状土地利用.png", "DR-107"),
        ("清禾集贸市场-现状肌理", "DR-108_清禾集贸市场-现状肌理.png", "DR-108"),
        ("清禾集贸市场-现状建筑高度", "DR-109_清禾集贸市场-现状建筑高度.png", "DR-109"),
        ("清禾集贸市场-现状业态分区", "DR-110_清禾集贸市场-现状业态分区.png", "DR-110"),
        ("中国石油-现状卫星图", "DR-111_中国石油-现状卫星图.png", "DR-111"),
        ("中国石油-现状土地利用", "DR-112_中国石油-现状土地利用.png", "DR-112"),
        ("中国石油-现状肌理", "DR-113_中国石油-现状肌理.png", "DR-113"),
        ("中国石油-现状建筑高度", "DR-114_中国石油-现状建筑高度.png", "DR-114"),
        ("中国石油-现状业态分区", "DR-115_中国石油-现状业态分区.png", "DR-115"),
        # 研究范围补充分析
        ("竖向规划与排水分析图", "DR-072_竖向规划与排水分析图.png", "DR-072"),
        ("智慧城市与数字基础设施规划图", "DR-073_智慧城市与数字基础设施规划图.png", "DR-073"),
        ("投资估算与经济测算图", "DR-074_投资估算与经济测算图.png", "DR-074"),
        ("公众参与与博弈协商成果图", "DR-075_公众参与与博弈协商成果图.png", "DR-075"),
        # 附录 技术说明
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
    
    if num_workers <= 1:
        print(f"Starting sequential generation of {len(gis_drawings)} sheet...")
        for drawing in gis_drawings:
            generate_single_sheet(drawing)
    else:
        print(f"Starting parallel generation of {len(gis_drawings)} sheets using {num_workers} processes...")
        with multiprocessing.Pool(processes=num_workers) as pool:
            pool.map(generate_single_sheet, gis_drawings)

if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else None
    generate_all_atlas_drawings(targets)
