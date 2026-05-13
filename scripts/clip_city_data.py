import geopandas as gpd
import json
import os
import sys
import time
from pathlib import Path

# 强制 UTF-8 输出
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def log(msg):
    print(msg, flush=True)

ROOT = Path(__file__).resolve().parent.parent

def clip_and_process():
    log("="*60)
    log("🚀 正在应用专业映射规则刷新全市数据...")
    log("="*60)

    # 1. 获取研究范围 BBox
    boundary_path = ROOT / "data/gis/Boundary_Scope.geojson"
    gdf_boundary = gpd.read_file(boundary_path)
    bbox = gdf_boundary.total_bounds
    bbox_buffered = (bbox[0]-0.005, bbox[1]-0.005, bbox[2]+0.005, bbox[3]+0.005)

    # 2. 定义高精度映射字典
    LANDUSE_MAPPING = {
        0: {"type": "居住用地", "color": "#FFFF00", "gb": "R"},
        1: {"type": "商业办公", "color": "#E60000", "gb": "B"},
        2: {"type": "商业服务业", "color": "#FF7F00", "gb": "B"},
        3: {"type": "工业用地", "color": "#AA7855", "gb": "M"},
        4: {"type": "交通场站", "color": "#9C9C9C", "gb": "S"},
        5: {"type": "机场设施", "color": "#686868", "gb": "S"},
        6: {"type": "行政办公", "color": "#FF7F7F", "gb": "A"},
        7: {"type": "教育科研", "color": "#FF7FFF", "gb": "A"},
        8: {"type": "医疗卫生", "color": "#FF7FBF", "gb": "A"},
        9: {"type": "体育文化", "color": "#7FFFFF", "gb": "A"},
        10: {"type": "公园与绿地", "color": "#38A800", "gb": "G"}
    }

    RAIL_MAPPING = {
        1: "铁路",
        2: "地铁",
        3: "轻轨/地面轨道",
        4: "其他"
    }

    ROAD_MAPPING = {
        1: "一级道路",
        2: "二级道路",
        3: "三级道路",
        4: "其他道路"
    }

    tasks = [
        {
            "src": "static/landuse.geojson",
            "dst": "data/gis/landuse_clipped.geojson",
            "label": "用地现状 (53MB)",
            "map_field": "Class",
            "mapping": LANDUSE_MAPPING,
            "mode": "landuse"
        },
        {
            "src": "data/gis/raw/rail_network.json",
            "dst": "data/gis/rail_clipped.geojson",
            "label": "铁路网 (155MB)",
            "map_field": "level",
            "mapping": RAIL_MAPPING,
            "mode": "standard"
        },
        {
            "src": "data/gis/raw/road_network.json",
            "dst": "data/gis/road_clipped.geojson",
            "label": "道路网 (4.1GB)",
            "map_field": "level",
            "mapping": ROAD_MAPPING,
            "mode": "standard"
        }
    ]

    for task in tasks:
        src_path = ROOT / task["src"]
        dst_path = ROOT / task["dst"]
        
        if not src_path.exists():
            continue
            
        log(f"📦 正在处理 {task['label']}...")
        try:
            gdf = gpd.read_file(src_path, engine="pyogrio", bbox=bbox_buffered)
            
            if len(gdf) == 0:
                log(f"   ⚠️ 裁切结果为空。")
                continue
            
            if task["mode"] == "landuse":
                log(f"   -> 正在应用专业色值与用地映射...")
                gdf["Type"] = gdf["Class"].map(lambda x: LANDUSE_MAPPING.get(x, {}).get("type", "未知"))
                gdf["Color"] = gdf["Class"].map(lambda x: LANDUSE_MAPPING.get(x, {}).get("color", "#CCCCCC"))
                gdf["GB_Code"] = gdf["Class"].map(lambda x: LANDUSE_MAPPING.get(x, {}).get("gb", "U"))
            else:
                log(f"   -> 正在应用等级映射...")
                gdf["Type"] = gdf[task["map_field"]].map(task["mapping"]).fillna("未知")
            
            gdf.to_file(dst_path, driver="GeoJSON")
            log(f"   ✅ 完成！保留 {len(gdf)} 个要素")
            
        except Exception as e:
            log(f"   ❌ 失败: {e}")

    log("="*60)
    log("✨ 高精度数据刷新完成！")
    log("="*60)

if __name__ == "__main__":
    clip_and_process()
