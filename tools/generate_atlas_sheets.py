# tools/generate_atlas_sheets.py
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.draw_scope_map import draw_spatial_map, process_a3_layout, wrap_text_by_pixels

STATIC_DIR = ROOT / "static"
ASSETS_DIR = ROOT / "assets"
ATLAS_DIR = STATIC_DIR / "atlas"

import contextlib

from src.config.site import get_author_info, get_institution_info

a = get_author_info()
i = get_institution_info()
def draw_cover(output_path, author=a.get("name",""), author_id=a.get("id",""), organization=f"{i.get('name','')} {i.get('department','')}"):
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
    draw.text((250, meta_y), f"设计单位：{i.get('name','')} {i.get('department','')}", fill=(71, 85, 105), font=font_body)
    draw.text((250, meta_y + 50), f"设计团队：城乡规划211班 {author} ({author_id})", fill=(71, 85, 105), font=font_body)
    draw.text((250, meta_y + 100), "指导教师：崔诚慧", fill=(71, 85, 105), font=font_body)
    draw.text((250, meta_y + 150), "时间：2026.6", fill=(71, 85, 105), font=font_body)
    
    paper_frame = cover.crop((100, 260, 2340, 1844))
    paper_frame.save(output_path)
    print(f"Cover page generated and saved to {output_path}")

def draw_toc(output_path, author=a.get("name",""), author_id=a.get("id",""), organization=f"{i.get('name','')} {i.get('department','')}"):
    print("Generating Table of Contents...")
    toc_img = Image.new("RGB", (2240, 1584), color=(248, 250, 252))
    draw = ImageDraw.Draw(toc_img)

    font_path = 'C:/Windows/Fonts/msyh.ttc'
    font_bold_path = 'C:/Windows/Fonts/msyhbd.ttc'
    try:
        font_large_title = ImageFont.truetype(font_bold_path, 36)
        font_card_title = ImageFont.truetype(font_bold_path, 20)
        font_table_header = ImageFont.truetype(font_bold_path, 12)
        font_body_bold = ImageFont.truetype(font_bold_path, 12)
        font_body = ImageFont.truetype(font_path, 12)
        font_desc = ImageFont.truetype(font_path, 14)
        font_tbl_desc = ImageFont.truetype(font_path, 11)
        font_meta = ImageFont.truetype(font_path, 11)
    except OSError:
        font_large_title = font_card_title = font_table_header = ImageFont.load_default()
        font_body_bold = font_body = font_desc = font_tbl_desc = font_meta = ImageFont.load_default()

    # Background grid
    for x in range(1, int(2240 / 79.2)):
        draw.line([(int(x * 79.2), 0), (int(x * 79.2), 1584)], fill=(226, 232, 240), width=1)
    for y in range(1, int(1584 / 79.2)):
        draw.line([(0, int(y * 79.2)), (2240, int(y * 79.2))], fill=(226, 232, 240), width=1)

    # ── Header Card ──
    draw.rectangle([36, 44, 2202, 138], fill=(226, 232, 240))
    draw.rectangle([32, 40, 2198, 134], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([32, 40, 2198, 46], fill=(217, 119, 6))
    draw.text((55, 87), "图册目录", fill=(15, 23, 42), font=font_large_title, anchor="lm")
    draw.text((230, 78), "本图册的图纸索引与主要编制说明。", fill=(100, 116, 139), font=font_desc, anchor="lm")
    draw.text((230, 100), "本规划旨在重塑历史地段活力，推动数字孪生与古今共振。", fill=(100, 116, 139), font=font_desc, anchor="lm")
    draw.text((1380, 68), f"设计团队：{i.get('name','')} {i.get('department','')}", fill=(100, 116, 139), font=font_meta)
    draw.text((1380, 86), f"制 作 人：{author} ({author_id})   指导教师：崔诚慧", fill=(100, 116, 139), font=font_meta)
    draw.text((1380, 104), "图幅：A3 (420\u00d7297mm)   坐标：WGS-84   日期：2026年6月", fill=(100, 116, 139), font=font_meta)

    # ── Three-Column Table Card ──
    card_top, card_bottom = 158, 1540
    card_left, card_right = 32, 2198

    draw.rectangle([card_left+4, card_top+4, card_right+4, card_bottom+4], fill=(226, 232, 240))
    draw.rectangle([card_left, card_top, card_right, card_bottom], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([card_left, card_top, card_right, card_top+6], fill=(217, 119, 6))

    sheets = [
        ("DR-001", "规划设计图册封面", "图册主标题与设计团队信息"),
        ("DR-002", "图册目录", "本图册的图纸索引与主要编制说明"),
    ]
    
    # Import CHAPTERS dynamically from gen_ppt
    try:
        import sys
        from pathlib import Path
        ROOT_DIR = Path(__file__).resolve().parent.parent
        if str(ROOT_DIR) not in sys.path:
            sys.path.insert(0, str(ROOT_DIR))
        if str(ROOT_DIR / "scratch") not in sys.path:
            sys.path.insert(0, str(ROOT_DIR / "scratch"))
        from gen_ppt import CHAPTERS
    except ImportError:
        CHAPTERS = []

    # Build the sheets list dynamically from CHAPTERS
    for ch_name, ch_en, ch_sheets in CHAPTERS:
        sheets.append((ch_name, ch_en, ""))
        for fn, title in ch_sheets:
            code = fn.split("_")[0]
            
            # Map descriptions based on keywords
            desc = ""
            if "地块导引" in fn:
                desc = "地块范围与现状问题指引"
            elif "现状卫星" in fn:
                desc = "高清航空遥感卫星图底图"
            elif "现状土地" in fn:
                desc = "现状用地分类与权属构成"
            elif "现状肌理" in fn:
                desc = "现状建筑外部空间轮廓肌理"
            elif "现状建筑高度" in fn:
                desc = "现状建筑层数及垂直特征"
            elif "现状业态" in fn:
                desc = "现状商户网点及产业分布"
            elif "改造总平面" in fn:
                desc = "地块改造总平面设计方案"
            elif "平面改造" in fn:
                desc = "地块平面改造方案与图例"
            elif "场地功能" in fn:
                desc = "地块功能策划与空间布局"
            elif "交通流线" in fn:
                desc = "车行、步行及消防流线分析"
            elif "绿化分析" in fn:
                desc = "绿化景观与步行活动空间"
            elif "场地剖面" in fn:
                desc = "地块竖向标高与剖面分析"
            elif "鸟瞰效果" in fn:
                desc = "地块改造更新后鸟瞰效果图"
            elif "鸟瞰改造" in fn:
                desc = "地块鸟瞰更新效果图（方案二）"
            elif "对比" in fn:
                desc = "改造前现状与改造后对比"
            elif "指标" in fn:
                desc = "规划控制指标与强度要求"
            elif "AIGC效果" in fn:
                desc = "AI辅助立面设计与意向推演"
            elif "节点景观" in fn:
                desc = "重点节点景观深化设计方案"
            else:
                desc_map = {
                    "DR-003": "国家城市更新与历史保护政策框架",
                    "DR-004": "区域级、市级、区位关系展示",
                    "DR-005": "规划研究范围与核心更新边界",
                    "DR-006": "数据源底数及多维数据清单表",
                    "DR-007": "上位国土空间及控制规划解译",
                    "DR-008": "上位道路、绿地等专项规划解译",
                    "DR-009": "国内外历史街区更新借鉴案例",
                    "DR-010": "数据来源底图与遥感影像现状",
                    "DR-011": "规划范围用地现状构成统计",
                    "DR-012": "现状路网密度与交通痛点识别",
                    "DR-013": "现状建筑层数与层高分级统计",
                    "DR-014": "现状街区建筑风貌质量识别",
                    "DR-015": "微气候、硬质化等环境问题",
                    "DR-016": "绿视率空间插值与环境诊断",
                    "DR-017": "伪满与中车工业遗产定位分布",
                    "DR-018": "街区文化旅游资源整合分析",
                    "DR-019": "历史文化建筑评估价值分级",
                    "DR-020": "现状POI产业网点活力评估",
                    "DR-021": "老龄化人口空间集聚与需求",
                    "DR-022": "空间句法集成度与可达性计算",
                    "DR-023": "街区四大现状瓶颈综合诊断",
                    "DR-024": "街区单元更新优先级潜力评估",
                    "DR-025": "潜力评估与可达性计算等公式",
                    "DR-026": "空间计算引擎与指标校验代码",
                    "DR-027": "相关法律法规及行业技术标准",
                    "DR-028": "微创织补与人本主义设计原则",
                    "DR-029": "生态、交通及指标等量化目标",
                    "DR-030": "古今共振与数字孪生定位策划",
                    "DR-031": "微更新与织补等核心设计策略",
                    "DR-032": "微创织补与人本主义理念图",
                    "DR-033": "规划设计目标体系及指标分解",
                    "DR-034": "规划设计三大维度总体策略",
                    "DR-035": "保护修缮、整治提升等分区控制",
                    "DR-036": "一核一廊多点总体结构规划",
                    "DR-037": "规划用地平衡与各类性质调整",
                    "DR-038": "带建筑形态的规划总平面图",
                    "DR-039": "用地指标增减平衡与控制要求",
                    "DR-040": "三区一带数字文创产业引导",
                    "DR-041": "建筑立面、结构分类更新控制",
                    "DR-042": "高度分级控制与风貌视线管控",
                    "DR-043": "路网加密、微循环及停车规划",
                    "DR-044": "慢跑道与漫步道无障碍双环",
                    "DR-045": "邻里中心与适老生活盒子补缺",
                    "DR-046": "滨水绿廊与口袋公园布点规划",
                    "DR-047": "文化游线路径与视廊景观控制",
                    "DR-048": "规划总体白模鸟瞰效果图",
                    "DR-049": "带规划用地着色的白模渲染",
                    "DR-050": "日照时数与CFD风环境模拟",
                    "DR-051": "三大主导功能板块划分设计",
                    "DR-052": "FAR强度分级控制空间分布",
                    "DR-053": "视线通廊空间开敞度控制",
                    "DR-054": "规划场地高程、排水及径流",
                    "DR-055": "5G基站、智慧杆件等新基建",
                    "DR-056": "更新投资估算与资金平衡分析",
                    "DR-057": "多主体博弈决策推荐均衡解",
                    "DR-058": "五大重点深化地块设计总图",
                    "DR-059": "数字孪生驱动的AIGC推演",
                    "DR-060": "近期、中期、远期分期开发节奏",
                    "DR-155": "规划图册结构层级树状导图",
                    "DR-156": "异构数据处理及GIS计算流程",
                    "DR-157": "多智能体协同博弈更新流线",
                    "DR-158": "城乡规划学科与数字技术体系",
                }
                desc = desc_map.get(code, "规划设计深化与效果表达")
                
            sheets.append((code, title, desc))

    spacing = 23
    start_y = card_top + 42
    
    num_cols = 3
    max_per_col = (len(sheets) + num_cols - 1) // num_cols # e.g. 164/3 -> 55
    
    # Calculate column boundaries
    card_width = card_right - card_left # 2166
    col_gap = 20
    col_w = (card_width - (num_cols - 1) * col_gap) // num_cols # (2166 - 40)//3 = 708
    
    # Draw two vertical column divider lines in the gaps
    draw.line([(750, card_top+6), (750, card_bottom)], fill=(226, 232, 240), width=2)
    draw.line([(1478, card_top+6), (1478, card_bottom)], fill=(226, 232, 240), width=2)

    # Column headers
    hy = card_top + 18
    for col_idx in range(num_cols):
        bx = card_left + col_idx * (col_w + col_gap)
        draw.text((bx + 5, hy), "编号", fill=(100, 116, 139), font=font_table_header)
        draw.text((bx + 80, hy), "图纸名称", fill=(100, 116, 139), font=font_table_header)
        draw.text((bx + 380, hy), "说明", fill=(100, 116, 139), font=font_table_header)
        draw.line([(bx + 2, hy+20), (bx + col_w - 2, hy+20)], fill=(203, 213, 225), width=2)

    # Function to draw a single entry
    def draw_entry(code, name, desc, x_base, y_pos, col_w):
        is_ch = ("第" in code and "章" in code) or "附录" in code
        xc = x_base + 5
        xn = x_base + 80
        xd = x_base + 380
        
        # Truncate title and description if too long
        max_title_len = 16
        max_desc_len = 16
        if len(name) > max_title_len:
            name = name[:max_title_len] + "..."
        if len(desc) > max_desc_len:
            desc = desc[:max_desc_len] + "..."
            
        if is_ch:
            # Chapter header styling
            draw.rectangle([x_base + 2, y_pos - 1, x_base + col_w - 2, y_pos + 18], fill=(230, 235, 245))
            draw.text((xc, y_pos), code, fill=(15, 23, 42), font=font_body_bold)
            draw.text((xn, y_pos), name, fill=(100, 116, 139), font=font_body_bold)
        else:
            # Regular sheet styling
            draw.text((xc, y_pos), code, fill=(15, 23, 42), font=font_body_bold)
            draw.text((xn, y_pos), name, fill=(15, 23, 42), font=font_body)
            draw.text((xd, y_pos), desc, fill=(100, 116, 139), font=font_tbl_desc)
            # Add thin separator line
            draw.line([(x_base + 2, y_pos + 19), (x_base + col_w - 2, y_pos + 19)], fill=(241, 245, 249), width=1)

    # Draw columns
    for col_idx in range(num_cols):
        col_sheets = sheets[col_idx * max_per_col : (col_idx + 1) * max_per_col]
        x_base = card_left + col_idx * (col_w + col_gap)
        y = start_y
        for code, name, desc in col_sheets:
            draw_entry(code, name, desc, x_base, y, col_w)
            y += spacing

    toc_img.save(output_path)
    print(f"Table of Contents generated and saved to {output_path}")


def generate_single_sheet(args):
    drawing_type, filename, code = args
    print(f"Generating sheet: {filename}...")
    output_path = ATLAS_DIR / filename
    
    # Check if this code is a programmatic drawing or a static one
    from tools.restore_static_sheets import PROGRAMMATIC_CODES
    if code not in PROGRAMMATIC_CODES:
        print(f"Skipping programmatic generation for static sheet: {filename}")
        # Ensure it exists in output_path by restoring it from backup if missing
        if not output_path.exists():
            try:
                import shutil

                from scripts.rename_atlas_sheets import MAPPING_RULES
                BACKUP_DIR = STATIC_DIR / "atlas_backup"
                
                # Find the matched file in backup
                matched_file = None
                for old_pattern, new_name in MAPPING_RULES:
                    if new_name == filename:
                        # Find it in backup folder
                        for root_dir, _dirs, files in os.walk(str(BACKUP_DIR)):
                            for f in files:
                                if f.lower().endswith(".png") and old_pattern in (Path(root_dir) / f).relative_to(BACKUP_DIR).as_posix():
                                    matched_file = Path(root_dir) / f
                                    break
                            if matched_file:
                                break
                        if matched_file:
                            break
                            
                if matched_file:
                    print(f"Copying static drawing {filename} from backup {matched_file.name}")
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(matched_file), str(output_path))
                else:
                    print(f"Warning: Static drawing {filename} could not be restored from backup.")
            except Exception as e:
                print(f"Failed to copy static drawing from backup: {e}")
        return

    if code == "DR-039":
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
            with contextlib.suppress(Exception):
                os.remove(temp_map_path)

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
        ("案例借鉴与对标分析图", "DR-009_案例借鉴与对标分析图.png", "DR-009"),
        # 第2章 数据诊断篇
        ("数据来源与遥感现状图", "DR-010_数据来源与遥感现状图.png", "DR-010"),
        ("用地现状分析图", "DR-011_用地现状分析图.png", "DR-011"),
        ("道路交通现状图", "DR-012_道路交通现状图.png", "DR-012"),
        ("建筑高度现状图", "DR-013_建筑高度现状图.png", "DR-013"),
        ("建筑风貌识别图", "DR-014_建筑风貌识别图.png", "DR-014"),
        ("环境品质问题地图", "DR-015_环境品质问题地图.png", "DR-015"),
        ("街区景观品质分析图", "DR-016_街区景观品质分析图.png", "DR-016"),
        ("历史建筑与工业遗产分布图", "DR-017_历史建筑与工业遗产分布图.png", "DR-017"),
        ("文化资源分析图", "DR-018_文化资源分析图.png", "DR-018"),
        ("遗产价值评估热力图", "DR-019_遗产价值评估热力图.png", "DR-019"),
        ("POI产业活力分析图", "DR-020_POI产业活力分析图.png", "DR-020"),
        ("人群需求与老龄化分布图", "DR-021_人群需求与老龄化分布图.png", "DR-021"),
        ("空间句法可达性分析图", "DR-022_空间句法可达性分析图.png", "DR-022"),
        ("综合现状问题诊断图", "DR-023_综合现状问题诊断图.png", "DR-023"),
        ("MPI更新潜力评估图", "DR-024_MPI更新潜力评估图.png", "DR-024"),
        # 第3章 设计理念与构思篇
        ("设计原则与理念图", "DR-032_设计原则与理念图.png", "DR-032"),
        ("设计目标体系图", "DR-033_设计目标体系图.png", "DR-033"),
        ("总体策略图", "DR-034_总体策略图.png", "DR-034"),
        # 第4章 总体规划篇
        ("更新模式分区图", "DR-035_更新模式分区图.png", "DR-035"),
        ("空间结构规划图", "DR-036_空间结构规划图.png", "DR-036"),
        ("用地规划图", "DR-037_用地规划图.png", "DR-037"),
        ("用地规划图_带建筑轮廓", "DR-038_用地规划图_带建筑轮廓.png", "DR-038"),
        ("用地规划指标表", "DR-039_用地规划指标表.png", "DR-039"),
        ("产业业态规划图", "DR-040_产业业态规划图.png", "DR-040"),
        ("建筑更新控制图", "DR-041_建筑更新控制图.png", "DR-041"),
        ("建筑高度控制图", "DR-042_建筑高度控制图.png", "DR-042"),
        ("道路交通系统规划图", "DR-043_道路交通系统规划图.png", "DR-043"),
        ("慢行系统规划图", "DR-044_慢行系统规划图.png", "DR-044"),
        ("公共空间系统图", "DR-045_公共空间系统图.png", "DR-045"),
        ("绿地景观系统图", "DR-046_绿地景观系统图.png", "DR-046"),
        ("历史文化展示系统图", "DR-047_历史文化展示系统图.png", "DR-047"),
        ("总体鸟瞰白模效果图", "DR-048_总体鸟瞰白模效果图.png", "DR-048"),
        ("总体鸟瞰白模_彩色总图", "DR-049_总体鸟瞰白模_彩色总图.png", "DR-049"),
        ("日照与风环境分析图", "DR-050_日照与风环境分析图.png", "DR-050"),
        ("功能分区与策划定位图", "DR-051_功能分区与策划定位图.png", "DR-051"),
        ("开发强度与容积率分区策略图", "DR-052_开发强度与容积率分区策略图.png", "DR-052"),
        ("天际线与视觉通廊控制图", "DR-053_天际线与视觉通廊控制图.png", "DR-053"),
        ("竖向规划与排水分析图", "DR-054_竖向规划与排水分析图.png", "DR-054"),
        ("智慧城市与数字基础设施规划图", "DR-055_智慧城市与数字基础设施规划图.png", "DR-055"),
        ("投资估算与经济测算图", "DR-056_投资估算与经济测算图.png", "DR-056"),
        ("公众参与与博弈协商成果图", "DR-057_公众参与与博弈协商成果图.png", "DR-057"),
        # 第5章 重点地块设计
        ("五地块深化设计总图", "DR-058_五地块深化设计总图.png", "DR-058"),
        ("AIGC技术推演过程图", "DR-059_AIGC技术推演过程图.png", "DR-059"),
        ("实施分期图", "DR-060_实施分期图.png", "DR-060"),
        # 重点地块现状分析图集 (DR-061 ~ DR-154)
        ("老水产市场_地块导引", "DR-061_老水产市场_地块导引.png", "DR-061"),
        ("老水产市场-现状卫星图", "DR-062_老水产市场-现状卫星图.png", "DR-062"),
        ("老水产市场-现状土地利用", "DR-063_老水产市场-现状土地利用.png", "DR-063"),
        ("老水产市场-现状肌理", "DR-064_老水产市场-现状肌理.png", "DR-064"),
        ("老水产市场-现状建筑高度", "DR-065_老水产市场-现状建筑高度.png", "DR-065"),
        ("老水产市场-现状业态分区", "DR-066_老水产市场-现状业态分区.png", "DR-066"),
        ("老水产市场-改造总平面图", "DR-067_老水产市场-改造总平面图.png", "DR-067"),
        ("老水产市场-平面改造带图例", "DR-068_老水产市场-平面改造带图例.png", "DR-068"),
        ("老水产市场-场地功能策划图", "DR-069_老水产市场-场地功能策划图.png", "DR-069"),
        ("老水产市场-交通流线分析图", "DR-070_老水产市场-交通流线分析图.png", "DR-070"),
        ("老水产市场-绿化分析图", "DR-071_老水产市场-绿化分析图.png", "DR-071"),
        ("老水产市场-场地剖面解析图", "DR-072_老水产市场-场地剖面解析图.png", "DR-072"),
        ("老水产市场-鸟瞰效果图", "DR-073_老水产市场-鸟瞰效果图.png", "DR-073"),
        ("老水产市场鸟瞰改造2", "DR-074_老水产市场鸟瞰改造2.png", "DR-074"),
        ("老水产市场-改造前后对比图", "DR-075_老水产市场-改造前后对比图.png", "DR-075"),
        ("老水产市场-节点景观设计图", "DR-076_老水产市场-节点景观设计图.png", "DR-076"),
        ("老水产市场-控制性指标表", "DR-077_老水产市场-控制性指标表.png", "DR-077"),
        ("老水产市场-AIGC效果图1", "DR-078_老水产市场-AIGC效果图1.png", "DR-078"),
        ("老水产市场-AIGC效果图2", "DR-079_老水产市场-AIGC效果图2.png", "DR-079"),
        ("老水产市场-AIGC效果图3", "DR-080_老水产市场-AIGC效果图3.png", "DR-080"),
        ("老水产市场-AIGC效果图4", "DR-081_老水产市场-AIGC效果图4.png", "DR-081"),
        # 食品调料市场
        ("食品调料市场_地块导引", "DR-082_食品调料市场_地块导引.png", "DR-082"),
        ("食品调料市场-现状卫星图", "DR-083_食品调料市场-现状卫星图.png", "DR-083"),
        ("食品调料市场-现状土地利用", "DR-084_食品调料市场-现状土地利用.png", "DR-084"),
        ("食品调料市场-现状肌理", "DR-085_食品调料市场-现状肌理.png", "DR-085"),
        ("食品调料市场-现状建筑高度", "DR-086_食品调料市场-现状建筑高度.png", "DR-086"),
        ("食品调料市场-现状业态分区", "DR-087_食品调料市场-现状业态分区.png", "DR-087"),
        ("食品调料市场-改造总平面图", "DR-088_食品调料市场-改造总平面图.png", "DR-088"),
        ("食品调料市场-平面改造带图例", "DR-089_食品调料市场-平面改造带图例.png", "DR-089"),
        ("食品调料市场-场地功能策划图", "DR-090_食品调料市场-场地功能策划图.png", "DR-090"),
        ("食品调料市场-交通流线分析图", "DR-091_食品调料市场-交通流线分析图.png", "DR-091"),
        ("食品调料市场-绿化分析图", "DR-092_食品调料市场-绿化分析图.png", "DR-092"),
        ("食品调料市场-场地剖面解析图", "DR-093_食品调料市场-场地剖面解析图.png", "DR-093"),
        ("食品调料市场-鸟瞰效果图", "DR-094_食品调料市场-鸟瞰效果图.png", "DR-094"),
        ("食品调料市场-改造前后对比图", "DR-095_食品调料市场-改造前后对比图.png", "DR-095"),
        ("食品调料市场-节点景观设计图", "DR-096_食品调料市场-节点景观设计图.png", "DR-096"),
        ("食品调料市场-控制性指标表", "DR-097_食品调料市场-控制性指标表.png", "DR-097"),
        ("食品调料市场-AIGC效果图1", "DR-098_食品调料市场-AIGC效果图1.png", "DR-098"),
        ("食品调料市场-AIGC效果图2", "DR-099_食品调料市场-AIGC效果图2.png", "DR-099"),
        ("食品调料市场-AIGC效果图3", "DR-100_食品调料市场-AIGC效果图3.png", "DR-100"),
        ("食品调料市场-AIGC效果图4", "DR-101_食品调料市场-AIGC效果图4.png", "DR-101"),
        # 市一中北侧
        ("市一中北侧_地块导引", "DR-102_市一中北侧_地块导引.png", "DR-102"),
        ("市一中北侧-现状卫星图", "DR-103_市一中北侧-现状卫星图.png", "DR-103"),
        ("市一中北侧-现状土地利用", "DR-104_市一中北侧-现状土地利用.png", "DR-104"),
        ("市一中北侧-现状肌理", "DR-105_市一中北侧-现状肌理.png", "DR-105"),
        ("市一中北侧-现状建筑高度", "DR-106_市一中北侧-现状建筑高度.png", "DR-106"),
        ("市一中北侧-现状业态分区", "DR-107_市一中北侧-现状业态分区.png", "DR-107"),
        ("市一中北侧-改造总平面图", "DR-108_市一中北侧-改造总平面图.png", "DR-108"),
        ("市一中北侧-场地功能策划图", "DR-109_市一中北侧-场地功能策划图.png", "DR-109"),
        ("市一中北侧-交通流线分析图", "DR-110_市一中北侧-交通流线分析图.png", "DR-110"),
        ("市一中北侧-绿化分析图", "DR-111_市一中北侧-绿化分析图.png", "DR-111"),
        ("市一中北侧-场地剖面解析图", "DR-112_市一中北侧-场地剖面解析图.png", "DR-112"),
        ("市一中北侧-鸟瞰效果图", "DR-113_市一中北侧-鸟瞰效果图.png", "DR-113"),
        ("市一中北侧-改造前后对比图", "DR-114_市一中北侧-改造前后对比图.png", "DR-114"),
        ("市一中北侧-节点景观设计图", "DR-115_市一中北侧-节点景观设计图.png", "DR-115"),
        ("市一中北侧-控制性指标表", "DR-116_市一中北侧-控制性指标表.png", "DR-116"),
        ("市一中北侧-AIGC效果图1", "DR-117_市一中北侧-AIGC效果图1.png", "DR-117"),
        ("市一中北侧-AIGC效果图2", "DR-118_市一中北侧-AIGC效果图2.png", "DR-118"),
        ("市一中北侧-AIGC效果图3", "DR-119_市一中北侧-AIGC效果图3.png", "DR-119"),
        ("市一中北侧-AIGC效果图4", "DR-120_市一中北侧-AIGC效果图4.png", "DR-120"),
        # 清禾集贸市场
        ("清禾集贸市场_地块导引", "DR-121_清禾集贸市场_地块导引.png", "DR-121"),
        ("清禾集贸市场-现状卫星图", "DR-122_清禾集贸市场-现状卫星图.png", "DR-122"),
        ("清禾集贸市场-现状土地利用", "DR-123_清禾集贸市场-现状土地利用.png", "DR-123"),
        ("清禾集贸市场-现状肌理", "DR-124_清禾集贸市场-现状肌理.png", "DR-124"),
        ("清禾集贸市场-现状建筑高度", "DR-125_清禾集贸市场-现状建筑高度.png", "DR-125"),
        ("清禾集贸市场-现状业态分区", "DR-126_清禾集贸市场-现状业态分区.png", "DR-126"),
        ("清禾集贸市场-改造总平面图", "DR-127_清禾集贸市场-改造总平面图.png", "DR-127"),
        ("清禾集贸市场-场地功能策划图", "DR-128_清禾集贸市场-场地功能策划图.png", "DR-128"),
        ("清禾集贸市场-交通流线分析图", "DR-129_清禾集贸市场-交通流线分析图.png", "DR-129"),
        ("清禾集贸市场-场地剖面解析图", "DR-130_清禾集贸市场-场地剖面解析图.png", "DR-130"),
        ("清禾集贸市场-鸟瞰效果图", "DR-131_清禾集贸市场-鸟瞰效果图.png", "DR-131"),
        ("清禾集贸市场-改造前后对比图", "DR-132_清禾集贸市场-改造前后对比图.png", "DR-132"),
        ("清禾集贸市场-节点景观设计图", "DR-133_清禾集贸市场-节点景观设计图.png", "DR-133"),
        ("清禾集贸市场-控制性指标表", "DR-134_清禾集贸市场-控制性指标表.png", "DR-134"),
        ("清禾集贸市场-AIGC效果图1", "DR-135_清禾集贸市场-AIGC效果图1.png", "DR-135"),
        ("清禾集贸市场-AIGC效果图2", "DR-136_清禾集贸市场-AIGC效果图2.png", "DR-136"),
        ("清禾集贸市场-AIGC效果图3", "DR-137_清禾集贸市场-AIGC效果图3.png", "DR-137"),
        ("清禾集贸市场-AIGC效果图4", "DR-138_清禾集贸市场-AIGC效果图4.png", "DR-138"),
        # 中国石油
        ("中国石油_地块导引", "DR-139_中国石油_地块导引.png", "DR-139"),
        ("中国石油-现状卫星图", "DR-140_中国石油-现状卫星图.png", "DR-140"),
        ("中国石油-现状土地利用", "DR-141_中国石油-现状土地利用.png", "DR-141"),
        ("中国石油-现状肌理", "DR-142_中国石油-现状肌理.png", "DR-142"),
        ("中国石油-现状建筑高度", "DR-143_中国石油-现状建筑高度.png", "DR-143"),
        ("中国石油-现状业态分区", "DR-144_中国石油-现状业态分区.png", "DR-144"),
        ("中国石油-改造总平面图", "DR-145_中国石油-改造总平面图.png", "DR-145"),
        ("中国石油-场地功能策划图", "DR-146_中国石油-场地功能策划图.png", "DR-146"),
        ("中国石油-交通流线分析图", "DR-147_中国石油-交通流线分析图.png", "DR-147"),
        ("中国石油-场地剖面解析图", "DR-148_中国石油-场地剖面解析图.png", "DR-148"),
        ("中国石油-鸟瞰效果图", "DR-149_中国石油-鸟瞰效果图.png", "DR-149"),
        ("中国石油-改造前后对比图", "DR-150_中国石油-改造前后对比图.png", "DR-150"),
        ("中国石油-节点景观设计图", "DR-151_中国石油-节点景观设计图.png", "DR-151"),
        ("中国石油-控制性指标表", "DR-152_中国石油-控制性指标表.png", "DR-152"),
        ("中国石油-AIGC效果图1", "DR-153_中国石油-AIGC效果图1.png", "DR-153"),
        ("中国石油-AIGC效果图2", "DR-154_中国石油-AIGC效果图2.png", "DR-154"),
        # 附录 技术说明
        ("图册章节结构导图", "DR-155_图册章节结构导图.png", "DR-155"),
        ("数据处理管线导图", "DR-156_数据处理管线导图.png", "DR-156"),
        ("规划协同工作流程图", "DR-157_规划协同工作流程图.png", "DR-157"),
        ("城乡规划知识体系导图", "DR-158_城乡规划知识体系导图.png", "DR-158"),
        ("智能体协同规划平台功能架构图", "DR-159_智能体协同规划平台功能架构图.png", "DR-159"),
        ("规划智能体核心决策与工具调用图", "DR-160_规划智能体核心决策与工具调用图.png", "DR-160"),
        ("空间数据库实体关系设计图", "DR-161_空间数据库实体关系设计图.png", "DR-161"),
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
