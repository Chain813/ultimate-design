# -*- coding: utf-8 -*-
"""
Add a wind rose (North arrow / compass) to atlas images that are missing one.
The wind rose is drawn as a transparent PNG overlay using PIL, matching
the style seen in DR-011 and DR-012 (N letter + 8-point star compass).
"""
import os
import sys
import math
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding='utf-8')

ATLAS_DIR = r"e:\AI-based-project\urban-platform\static\atlas"

# Target images that need wind rose added
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

def create_wind_rose(size=90):
    """
    Create a wind rose (N arrow compass) as a transparent PIL Image.
    Matches the style of DR-011/DR-012: 8-point star with N label on top.
    """
    # Create transparent canvas with some padding
    canvas_size = size + 60  # extra space for N label
    img = Image.new('RGBA', (canvas_size, canvas_size + 30), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cx = canvas_size // 2
    cy = canvas_size // 2 + 25  # offset down to leave room for "N"
    
    r_outer = size // 2      # outer radius for main 4 points
    r_inner = size // 4      # inner radius (between main points)
    r_small = size // 3      # small points radius
    
    # Draw 8-point star compass
    # Main 4 directions (N, E, S, W) - longer points
    # Secondary 4 directions (NE, SE, SW, NW) - shorter points
    points_main = []
    points_secondary = []
    
    for i in range(8):
        angle = math.radians(i * 45 - 90)  # Start from North (top)
        if i % 2 == 0:
            # Main direction (N, E, S, W)
            x = cx + r_outer * math.cos(angle)
            y = cy + r_outer * math.sin(angle)
            points_main.append((x, y))
        else:
            # Secondary direction (NE, SE, SW, NW)
            x = cx + r_small * math.cos(angle)
            y = cy + r_small * math.sin(angle)
            points_secondary.append((x, y))
    
    # Draw the star: alternate between main and secondary points
    all_points = []
    mi, si = 0, 0
    for i in range(8):
        if i % 2 == 0:
            all_points.append(points_main[mi])
            mi += 1
        else:
            all_points.append(points_secondary[si])
            si += 1
    
    # Draw the dark half (east side) and light half (west side) of each triangle
    for i in range(8):
        p1 = all_points[i]
        p2 = all_points[(i + 1) % 8]
        center = (cx, cy)
        
        # Determine fill color: alternate dark/light for 3D effect
        if i % 2 == 0:
            # Main point triangles
            fill_color = (60, 60, 60, 220)  # dark
        else:
            fill_color = (160, 160, 160, 200)  # light
        
        draw.polygon([center, p1, p2], fill=fill_color, outline=(50, 50, 50, 255))
    
    # Draw center circle
    cr = 4
    draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(255, 255, 255, 255), outline=(50, 50, 50, 255))
    
    # Draw "N" label above the compass
    try:
        font = ImageFont.truetype("arial.ttf", 22)
    except:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
        except:
            font = ImageFont.load_default()
    
    n_y = cy - r_outer - 18
    draw.text((cx, n_y), "N", fill=(50, 50, 50, 255), font=font, anchor="mb")
    
    return img


def add_wind_rose_to_image(img_path, output_path=None):
    """
    Add a wind rose to the top area of the map panel in the atlas image.
    Position: top-center of the map area (left panel), similar to DR-011/DR-012.
    """
    if output_path is None:
        output_path = img_path  # overwrite in place
        
    base_img = Image.open(img_path).convert('RGBA')
    w, h = base_img.size
    
    # Create wind rose
    wr = create_wind_rose(size=70)
    wr_w, wr_h = wr.size
    
    # Position: The map panel typically occupies x=[45..1415] in a 2240px wide image.
    # The wind rose in DR-011 is at approximately x=1060, y=170 (top-right of map panel)
    # We'll place it at a similar position
    paste_x = 1060 - wr_w // 2
    paste_y = 140
    
    # Composite the wind rose onto the base image
    base_img.paste(wr, (paste_x, paste_y), wr)
    
    # Convert back to RGB for PNG saving
    final = base_img.convert('RGB')
    final.save(output_path, 'PNG', quality=95)
    return True


def main():
    print(f"Adding wind rose to {len(TARGETS)} images...")
    
    success = 0
    for fname in TARGETS:
        fpath = os.path.join(ATLAS_DIR, fname)
        if not os.path.exists(fpath):
            print(f"  SKIP (not found): {fname}")
            continue
        
        try:
            add_wind_rose_to_image(fpath)
            print(f"  OK: {fname}")
            success += 1
        except Exception as e:
            print(f"  ERROR: {fname} - {e}")
    
    print(f"\nDone. Successfully processed {success}/{len(TARGETS)} images.")


if __name__ == "__main__":
    main()
