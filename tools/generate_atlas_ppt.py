# tools/generate_atlas_ppt.py
import os
import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches
from PIL import Image, ImageFilter

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
ATLAS_DIR = ROOT / "static" / "atlas"
OUTPUT_DIR = ROOT / "static" / "附件"
OUTPUT_FILE = OUTPUT_DIR / "成果图册汇总_A3.pptx"

# 1. Define the complete atlas image sequence (~109 sheets)
image_sequence = [
    # ============================================================
    # 封面与目录（2 张）
    # ============================================================
    "DR-001_规划设计图册封面.png",
    "DR-002_图册目录.png",

    # ============================================================
    # 第一章：项目认知篇（7 张）
    # ============================================================
    "DR-003_项目背景与政策解读图.png",
    "DR-004_现状区位图.png",
    "DR-005_研究范围图.png",
    "A原始数据_横版.png",
    "DR-007_上位规划解读图.png",
    "DR-008_上位专项规划解读图.png",
    "DR-068_案例借鉴与对标分析图.png",

    # ============================================================
    # 第二章：数据诊断篇（15 张）
    # ============================================================
    "DR-013_数据来源与遥感现状图.png",
    "DR-014_用地现状分析图.png",
    "DR-020_道路交通现状图.png",
    "DR-017_建筑高度现状图.png",
    "DR-018_建筑风貌识别图.png",
    "DR-030_环境品质问题地图.png",
    "DR-028_街区景观品质分析图.png",
    "DR-019_历史建筑与工业遗产分布图.png",
    "DR-023_文化资源分析图.png",
    "DR-032_遗产价值评估热力图.png",
    "DR-027_POI产业活力分析图.png",
    "DR-029_人群需求与老龄化分布图.png",
    "DR-021_空间句法可达性分析图.png",
    "DR-059_综合现状问题诊断图.png",
    "DR-061_MPI更新潜力评估图.png",

    # ============================================================
    # 第三章：设计理念与构思篇（10 张）
    # ============================================================
    "A数学公式_横版.png",
    "A核心代码清单_横版.png",
    "A设计依据.png",
    "A设计原则.png",
    "A设计目标.png",
    "A设计定位.png",
    "A设计策略.png",
    "DR-037_设计原则与理念图.png",
    "DR-038_设计目标体系图.png",
    "DR-039_总体策略图.png",

    # ============================================================
    # 第四章：总体规划篇（18 张）
    # ============================================================
    "DR-058_总体鸟瞰白模效果图.png",
    "DR-044_用地规划图.png",
    "DR-044_用地规划图_带建筑轮廓.png",
    "DR-045_用地规划指标表.png",
    "DR-049_建筑高度控制图.png",
    "DR-051_道路交通系统规划图.png",
    "DR-053_慢行系统规划图.png",
    "DR-042_空间结构规划图.png",
    "DR-055_公共空间系统图.png",
    "DR-046_产业业态规划图.png",
    "DR-056_绿地景观系统图.png",
    "DR-057_历史文化展示系统图.png",
    "DR-040_更新模式分区图.png",
    "DR-048_建筑更新控制图.png",
    "DR-065_日照与风环境分析图.png",
    "DR-069_功能分区与策划定位图.png",
    "DR-070_开发强度与容积率分区策略图.png",
    "DR-071_天际线与视觉通廊控制图.png",

    # ============================================================
    # 第五章：重点地块深化篇（53 张）
    # ============================================================
    # --- 总览 ---
    "DR-076_五地块深化设计总图.png",
    "DR-081_AIGC技术推演过程图.png",
    "DR-082_实施分期图.png",

    # --- 老水产市场 现状分析 ---
    "DR-091_老水产市场-现状卫星图.png",
    "DR-092_老水产市场-现状土地利用.png",
    "DR-093_老水产市场-现状肌理.png",
    "DR-094_老水产市场-现状建筑高度.png",
    "DR-095_老水产市场-现状业态分区.png",
    # --- 老水产市场 改造设计 ---
    "DR-116_老水产市场-改造总平面图.png",
    "DR-117_老水产市场-鸟瞰效果图.png",
    "DR-118_老水产市场-改造前后对比图.png",
    "DR-119_老水产市场-节点景观设计图.png",
    "DR-120_老水产市场-控制性指标表.png",

    # --- 食品调料市场 现状分析 ---
    "DR-096_食品调料市场-现状卫星图.png",
    "DR-097_食品调料市场-现状土地利用.png",
    "DR-098_食品调料市场-现状肌理.png",
    "DR-099_食品调料市场-现状建筑高度.png",
    "DR-100_食品调料市场-现状业态分区.png",
    # --- 食品调料市场 改造设计 ---
    "DR-121_食品调料市场-改造总平面图.png",
    "DR-122_食品调料市场-鸟瞰效果图.png",
    "DR-123_食品调料市场-改造前后对比图.png",
    "DR-124_食品调料市场-节点景观设计图.png",
    "DR-125_食品调料市场-控制性指标表.png",

    # --- 市一中北侧 现状分析 ---
    "DR-101_市一中北侧-现状卫星图.png",
    "DR-102_市一中北侧-现状土地利用.png",
    "DR-103_市一中北侧-现状肌理.png",
    "DR-104_市一中北侧-现状建筑高度.png",
    "DR-105_市一中北侧-现状业态分区.png",
    # --- 市一中北侧 改造设计 ---
    "DR-126_市一中北侧-改造总平面图.png",
    "DR-127_市一中北侧-鸟瞰效果图.png",
    "DR-128_市一中北侧-改造前后对比图.png",
    "DR-129_市一中北侧-节点景观设计图.png",
    "DR-130_市一中北侧-控制性指标表.png",

    # --- 清禾集贸市场 现状分析 ---
    "DR-106_清禾集贸市场-现状卫星图.png",
    "DR-107_清禾集贸市场-现状土地利用.png",
    "DR-108_清禾集贸市场-现状肌理.png",
    "DR-109_清禾集贸市场-现状建筑高度.png",
    "DR-110_清禾集贸市场-现状业态分区.png",
    # --- 清禾集贸市场 改造设计 ---
    "DR-131_清禾集贸市场-改造总平面图.png",
    "DR-132_清禾集贸市场-鸟瞰效果图.png",
    "DR-133_清禾集贸市场-改造前后对比图.png",
    "DR-134_清禾集贸市场-节点景观设计图.png",
    "DR-135_清禾集贸市场-控制性指标表.png",

    # --- 中国石油 现状分析 ---
    "DR-111_中国石油-现状卫星图.png",
    "DR-112_中国石油-现状土地利用.png",
    "DR-113_中国石油-现状肌理.png",
    "DR-114_中国石油-现状建筑高度.png",
    "DR-115_中国石油-现状业态分区.png",
    # --- 中国石油 改造设计 ---
    "DR-136_中国石油-改造总平面图.png",
    "DR-137_中国石油-鸟瞰效果图.png",
    "DR-138_中国石油-改造前后对比图.png",
    "DR-139_中国石油-节点景观设计图.png",
    "DR-140_中国石油-控制性指标表.png",

    # --- 研究范围补充分析 ---
    "DR-072_竖向规划与排水分析图.png",
    "DR-073_智慧城市与数字基础设施规划图.png",
    "DR-074_投资估算与经济测算图.png",
    "DR-075_公众参与与博弈协商成果图.png",

    # ============================================================
    # 附录：技术说明（4 张）
    # ============================================================
    "DR-083_图册章节结构导图.png",
    "DR-084_数据处理管线导图.png",
    "DR-085_规划协同工作流程图.png",
    "DR-086_城乡规划知识体系导图.png",
]

# Files requested to be enhanced
# (Cleared: A-series images are now copied from original ChatGPT high-res sources)
enhance_targets = set()

def enhance_image(img_path):
    """Upscale image by 2x using Lanczos and apply a sharpening filter for crisp text."""
    try:
        with Image.open(img_path) as img:
            w, h = img.size
            if w >= 2500:
                # Already upscaled in a previous run, skip to avoid double processing
                print(f" -> [{img_path.name}] is already high resolution ({w}x{h}). Skipping enhancement.")
                return
            
            print(f" -> Enhancing resolution of [{img_path.name}] ({w}x{h} -> {w*2}x{h*2})...")
            # 2x upscale using LANCZOS interpolation
            upscaled = img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
            # Apply UnsharpMask to make lines and text crisp
            sharpened = upscaled.filter(ImageFilter.UnsharpMask(radius=1.5, percent=80, threshold=3))
            sharpened.save(img_path, "PNG")
            print(f" -> Successfully saved high-clarity [{img_path.name}].")
    except Exception as e:
        print(f" -> Error enhancing [{img_path.name}]: {e}")

def add_centered_picture(slide, img_path, slide_width, slide_height):
    """Fits and centers the image on the slide, maintaining its exact aspect ratio."""
    with Image.open(img_path) as img:
        img_w, img_h = img.size
        
    img_aspect = img_w / img_h
    slide_aspect = slide_width / slide_height
    
    if img_aspect > slide_aspect:
        # Constrain by width
        fit_width = slide_width
        fit_height = slide_width / img_aspect
    else:
        # Constrain by height
        fit_height = slide_height
        fit_width = slide_height * img_aspect
        
    # Center the coordinates
    left = (slide_width - fit_width) / 2
    top = (slide_height - fit_height) / 2
    
    slide.shapes.add_picture(
        str(img_path),
        left=left,
        top=top,
        width=fit_width,
        height=fit_height
    )

def generate_ppt():
    # 1. Enhance the resolution of the requested A-series images
    print("Checking and enhancing requested diagrams resolution...")
    for img_name in enhance_targets:
        img_path = ATLAS_DIR / img_name
        if img_path.exists():
            enhance_image(img_path)
            
    # Generate landscape copies of portrait tables
    print("\nGenerating landscape copies of portrait tables...")
    try:
        try:
            from tools.rearrange_tables_landscape import rearrange_table_to_landscape
        except ImportError:
            sys.path.insert(0, str(ROOT))
            try:
                from tools.rearrange_tables_landscape import rearrange_table_to_landscape
            except ImportError:
                from rearrange_tables_landscape import rearrange_table_to_landscape
        rearrange_table_to_landscape("A原始数据.png", "A原始数据_横版.png")
        rearrange_table_to_landscape("A数学公式.png", "A数学公式_横版.png")
        rearrange_table_to_landscape("A核心代码清单.png", "A核心代码清单_横版.png")
    except Exception as e:
        print(f"Error during landscape table generation: {e}")
            
    print("\nInitializing PPTX presentation...")
    prs = Presentation()
    
    # 2. Set slide dimensions to A3 paper size in inches (16.535 x 11.693)
    prs.slide_width = Inches(16.535)
    prs.slide_height = Inches(11.693)
    
    # Use blank layout
    blank_layout = prs.slide_layouts[6]
    
    missing_files = []
    
    # 3. Add slides in sequence, centering images without stretching
    for i, img_name in enumerate(image_sequence, start=1):
        img_path = ATLAS_DIR / img_name
        if not img_path.exists():
            print(f"Warning: File [{img_name}] not found. Skipping...")
            missing_files.append(img_name)
            continue
            
        print(f"[{i}/{len(image_sequence)}] Adding slide: {img_name}")
        slide = prs.slides.add_slide(blank_layout)
        
        # Center image and maintain original aspect ratio
        add_centered_picture(slide, img_path, prs.slide_width, prs.slide_height)
        
    # 4. Save the presentation
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT_FILE))
    print("\n" + "="*50)
    print(f"Success! PPTX generated at: {OUTPUT_FILE}")
    print(f"Total slides added: {len(image_sequence) - len(missing_files)} / {len(image_sequence)}")
    if missing_files:
        print(f"Missing files ({len(missing_files)}): {missing_files}")
    print("="*50)

if __name__ == "__main__":
    generate_ppt()
