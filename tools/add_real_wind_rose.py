# -*- coding: utf-8 -*-
"""
Add the real Changchun wind rose (长春市风玫瑰.png) to the top-right corner
of the map panel in all 30 target atlas drawings.
"""
import os
import sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"e:\AI-based-project\urban-platform"
ATLAS_DIR = os.path.join(ROOT_DIR, "static", "atlas")
WIND_ROSE_PATH = os.path.join(ROOT_DIR, "assets", "长春市风玫瑰.png")

# Target images that need the real wind rose added
TARGETS = [
    "DR-009_案例借鉴与对标分析图.png",
    "DR-013_建筑高度现状图.png",
    "DR-014_建筑风貌识别图.png",
    "DR-016_街区景观品质分析图.png",
    "DR-017_历史建筑与工业遗产分布图.png",
    "DR-018_文化资源分析图.png",
    "DR-034_总体策略图.png",
    "DR-035_更新模式分区图.png",
    "DR-036_空间结构规划图.png",
    "DR-037_用地规划图.png",
    "DR-038_用地规划图_带建筑轮廓.png",
    "DR-039_用地规划指标表.png",
    "DR-040_产业业态规划图.png",
    "DR-041_建筑更新控制图.png",
    "DR-042_建筑高度控制图.png",
    "DR-043_道路交通系统规划图.png",
    "DR-044_慢行系统规划图.png",
    "DR-045_公共空间系统图.png",
    "DR-046_绿地景观系统图.png",
    "DR-047_历史文化展示系统图.png",
    "DR-050_日照与风环境分析图.png",
    "DR-051_功能分区与策划定位图.png",
    "DR-052_开发强度与容积率分区策略图.png",
    "DR-053_天际线与视觉通廊控制图.png",
    "DR-054_竖向规划与排水分析图.png",
    "DR-055_智慧城市与数字基础设施规划图.png",
    "DR-056_投资估算与经济测算图.png",
    "DR-057_公众参与与博弈协商成果图.png",
    "DR-058_五地块深化设计总图.png",
    "DR-060_实施分期图.png",
]

def add_wind_rose_to_image(img_path, wind_rose_img):
    """
    Overlay the wind rose image onto the top-right corner of the map panel in the target image.
    """
    base_img = Image.open(img_path).convert('RGBA')
    
    # Calculate target dimensions for wind rose
    target_width = 135
    target_height = int(target_width * wind_rose_img.size[1] / wind_rose_img.size[0])
    wr_resized = wind_rose_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    # Paste coordinates (center x=1485, center y=350)
    paste_x = 1485 - target_width // 2
    paste_y = 350 - target_height // 2
    
    # Composite the wind rose onto the base image
    base_img.paste(wr_resized, (paste_x, paste_y), wr_resized)
    
    # Convert back to RGB for PNG saving
    final = base_img.convert('RGB')
    final.save(img_path, 'PNG', quality=95)
    return True

def main():
    print(f"Loading wind rose from: {WIND_ROSE_PATH}")
    if not os.path.exists(WIND_ROSE_PATH):
        print(f"Error: Wind rose file not found at {WIND_ROSE_PATH}")
        return
        
    wind_rose_img = Image.open(WIND_ROSE_PATH).convert('RGBA')
    
    print(f"Adding real wind rose to {len(TARGETS)} images...")
    
    success = 0
    for fname in TARGETS:
        fpath = os.path.join(ATLAS_DIR, fname)
        if not os.path.exists(fpath):
            print(f"  SKIP (not found): {fname}")
            continue
        
        try:
            add_wind_rose_to_image(fpath, wind_rose_img)
            print(f"  OK: {fname}")
            success += 1
        except Exception as e:
            print(f"  ERROR: {fname} - {e}")
            
    print(f"\nDone. Successfully processed {success}/{len(TARGETS)} images.")

if __name__ == "__main__":
    main()
