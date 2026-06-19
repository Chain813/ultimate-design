# -*- coding: utf-8 -*-
"""
Restore original clean atlas images from static/atlas_backup into static/atlas.
Uses MAPPING_RULES from rename_atlas_sheets.py to find the correct source file in backup.
"""
import os
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"e:\AI-based-project\urban-platform")
BACKUP_DIR = ROOT / "static" / "atlas_backup"
ATLAS_DIR = ROOT / "static" / "atlas"

# Target files in static/atlas that we want to restore from clean backup
TARGET_FILES = [
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
    "DR-040_产业业态规划图.png",
    "DR-041_建筑更新控制图.png",
    "DR-042_建筑高度控制图.png",
    "DR-043_道路交通系统规划图.png",
    "DR-044_慢行系统规划图.png",
    "DR-045_公共空间系统图.png",
    "DR-046_绿地景观系统图.png",
    "DR-047_历史文化展示系统图.png",
    "DR-048_总体鸟瞰白模效果图.png",
    "DR-049_总体鸟瞰白模_彩色总图.png",
    "DR-050_日照与风环境分析图.png",
    "DR-051_功能分区与策划定位图.png",
    "DR-052_开发强度与容积率分区策略图.png",
    "DR-053_天际线与视觉通廊控制图.png",
    "DR-054_竖向规划与排水分析图.png",
    "DR-055_智慧城市 with 数字基础设施规划图.png", # wait, we will do fuzzy matching
    "DR-055_智慧城市与数字基础设施规划图.png",
    "DR-056_投资估算与经济测算图.png",
    "DR-057_公众参与与博弈协商成果图.png",
    "DR-058_五地块深化设计总图.png",
    "DR-060_实施分期图.png",
]

# Mapping rules imported from rename_atlas_sheets.py
MAPPING_RULES = [
    ("DR-003_项目背景与政策解读图", "DR-003_项目背景与政策解读图.png"),
    ("DR-004_现状区位图", "DR-004_现状区位图.png"),
    ("DR-005_研究范围图", "DR-005_研究范围图.png"),
    ("A原始数据_横版", "DR-006_原始数据清单.png"),
    ("DR-007_上位规划解读图", "DR-007_上位规划解读图.png"),
    ("DR-008_上位专项规划解读图", "DR-008_上位专项规划解读图.png"),
    ("DR-068_案例借鉴与对标分析图", "DR-009_案例借鉴与对标分析图.png"),
    ("DR-013_数据来源与遥感现状图", "DR-010_数据来源与遥感现状图.png"),
    ("DR-014_用地现状分析图", "DR-011_用地现状分析图.png"),
    ("DR-020_道路交通现状图", "DR-012_道路交通现状图.png"),
    ("DR-017_建筑高度现状图", "DR-013_建筑高度现状图.png"),
    ("DR-018_建筑风貌识别图", "DR-014_建筑风貌识别图.png"),
    ("DR-030_环境品质问题地图", "DR-015_环境品质问题地图.png"),
    ("DR-028_街区景观品质分析图", "DR-016_街区景观品质分析图.png"),
    ("DR-019_历史建筑与工业遗产分布图", "DR-017_历史建筑与工业遗产分布图.png"),
    ("DR-023_文化资源分析图", "DR-018_文化资源分析图.png"),
    ("DR-032_遗产价值评估热力图", "DR-019_遗产价值评估热力图.png"),
    ("DR-027_POI产业活力分析图", "DR-020_POI产业活力分析图.png"),
    ("DR-029_人群需求与老龄化分布图", "DR-021_人群需求与老龄化分布图.png"),
    ("DR-021_空间句法可达性分析图", "DR-022_空间句法可达性分析图.png"),
    ("DR-059_综合现状问题诊断图", "DR-023_综合现状问题诊断图.png"),
    ("DR-061_MPI更新潜力评估图", "DR-024_MPI更新潜力评估图.png"),
    ("A数学公式_横版", "DR-025_核心算法与数学公式.png"),
    ("A数学公式", "DR-025_核心算法与数学公式.png"),
    ("A核心代码清单_横版", "DR-026_平台核心代码清单.png"),
    ("A核心代码清单", "DR-026_平台核心代码清单.png"),
    ("A设计依据", "DR-027_规划设计依据.png"),
    ("A设计原则", "DR-028_规划设计原则.png"),
    ("A设计目标", "DR-029_规划设计目标.png"),
    ("A设计定位", "DR-030_规划设计定位.png"),
    ("A设计策略", "DR-031_规划设计策略.png"),
    ("DR-037_设计原则与理念图", "DR-032_设计原则与理念图.png"),
    ("DR-038_设计目标体系图", "DR-033_设计目标体系图.png"),
    ("DR-039_总体策略图", "DR-034_总体策略图.png"),
    ("DR-040_更新模式分区图", "DR-035_更新模式分区图.png"),
    ("DR-042_空间结构规划图", "DR-036_空间结构规划图.png"),
    ("DR-044_用地规划图.png", "DR-037_用地规划图.png"),
    ("DR-044_用地规划图_带建筑轮廓", "DR-038_用地规划图_带建筑轮廓.png"),
    ("DR-045_用地规划指标表", "DR-039_用地规划指标表.png"),
    ("DR-046_产业业态规划图", "DR-040_产业业态规划图.png"),
    ("DR-048_建筑更新控制图", "DR-041_建筑更新控制图.png"),
    ("DR-049_建筑高度控制图", "DR-042_建筑高度控制图.png"),
    ("DR-051_道路交通系统规划图", "DR-043_道路交通系统规划图.png"),
    ("DR-053_慢行系统规划图", "DR-044_慢行系统规划图.png"),
    ("DR-055_公共空间系统图", "DR-045_公共空间系统图.png"),
    ("DR-056_绿地景观系统图", "DR-046_绿地景观系统图.png"),
    ("DR-057_历史文化展示系统图", "DR-047_历史文化展示系统图.png"),
    ("DR-058_总体鸟瞰白模效果图", "DR-048_总体鸟瞰白模效果图.png"),
    ("总平面白模鸟瞰", "DR-049_总体鸟瞰白模_彩色总图.png"),
    ("DR-065_日照与风环境分析图", "DR-050_日照与风环境分析图.png"),
    ("DR-069_功能分区与策划定位图", "DR-051_功能分区与策划定位图.png"),
    ("DR-070_开发强度与容积率分区策略图", "DR-052_开发强度与容积率分区策略图.png"),
    ("DR-071_天际线与视觉通廊控制图", "DR-053_天际线与视觉通廊控制图.png"),
    ("DR-072_竖向规划与排水分析图", "DR-054_竖向规划与排水分析图.png"),
    ("DR-073_智慧城市与数字基础设施规划图", "DR-055_智慧城市与数字基础设施规划图.png"),
    ("DR-074_投资估算与经济测算图", "DR-056_投资估算与经济测算图.png"),
    ("DR-075_公众参与与博弈协商成果图", "DR-057_公众参与与博弈协商成果图.png"),
    ("DR-076_五地块深化设计总图", "DR-058_五地块深化设计总图.png"),
    ("DR-081_AIGC技术推演过程图", "DR-059_AIGC技术推演过程图.png"),
    ("DR-082_实施分期图", "DR-060_实施分期图.png"),
]

def restore_originals():
    # Get all files in backup dir
    backup_files = os.listdir(str(BACKUP_DIR))
    print(f"Backup folder contains {len(backup_files)} files.")
    
    restored = 0
    not_found = []
    
    for target_name in TARGET_FILES:
        # Find matching rule for target_name
        rule_src_pattern = None
        for old_pattern, new_name in MAPPING_RULES:
            if new_name == target_name:
                rule_src_pattern = old_pattern
                break
        
        # If no rule matches, use target name itself
        if not rule_src_pattern:
            rule_src_pattern = target_name.replace(".png", "")
            
        # Try to find a file in BACKUP_DIR that contains rule_src_pattern
        found_src_file = None
        for bf in backup_files:
            if rule_src_pattern in bf:
                found_src_file = bf
                break
                
        if found_src_file:
            src_path = BACKUP_DIR / found_src_file
            dst_path = ATLAS_DIR / target_name
            shutil.copy2(str(src_path), str(dst_path))
            print(f"Restored: {found_src_file} -> {target_name}")
            restored += 1
        else:
            not_found.append(target_name)
            
    print(f"\nRestored {restored}/{len(TARGET_FILES)} files.")
    if not_found:
        print("Warning: Could not find backup for these files:")
        for nf in not_found:
            print(f"  - {nf}")

if __name__ == "__main__":
    restore_originals()
