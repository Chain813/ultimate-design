"""将 GCJ-02 坐标系的 GeoJSON 文件精确转换为 WGS-84

诊断结论:
- Key_Plots_District.json 和 Boundary_Scope.geojson 来源于高德/腾讯等国内平台,
  使用的是 GCJ-02 (火星坐标系)
- POI 数据经过 bd09_to_wgs84 转换后已经是 WGS-84
- 两套坐标系之间存在约 0.003-0.006° 的偏移, 导致 point-in-polygon 判定失败

本脚本使用与 src/utils/geo_transform.py 相同的精确算法进行逐点转换。

使用方法:
    python scripts/convert_gcj02_to_wgs84.py
"""
import sys
import json
import math
import copy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---- GCJ-02 → WGS-84 精确转换 (与 src/utils/geo_transform.py 一致) ----
PI = 3.1415926535897932384626
A = 6378245.0
EE = 0.00669342162296594323


def _transformlat(lng, lat):
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat + 0.2 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * PI) + 20.0 * math.sin(2.0 * lng * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * PI) + 40.0 * math.sin(lat / 3.0 * PI)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * PI) + 320 * math.sin(lat * PI / 30.0)) * 2.0 / 3.0
    return ret


def _transformlng(lng, lat):
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng * lat + 0.1 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * PI) + 20.0 * math.sin(2.0 * lng * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * PI) + 40.0 * math.sin(lng / 3.0 * PI)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * PI) + 300.0 * math.sin(lng / 30.0 * PI)) * 2.0 / 3.0
    return ret


def gcj02_to_wgs84(lng, lat):
    """GCJ-02 → WGS-84 精确转换"""
    dlat = _transformlat(lng - 105.0, lat - 35.0)
    dlng = _transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * PI
    magic = math.sin(radlat)
    magic = 1 - EE * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * PI)
    dlng = (dlng * 180.0) / (A / sqrtmagic * math.cos(radlat) * PI)
    mglat = lat + dlat
    mglng = lng + dlng
    return round(lng * 2 - mglng, 6), round(lat * 2 - mglat, 6)


def convert_coords(coords):
    """递归转换 GeoJSON coordinates 结构"""
    if isinstance(coords[0], (int, float)):
        # 单个坐标点 [lng, lat] or [lng, lat, alt]
        wgs_lng, wgs_lat = gcj02_to_wgs84(coords[0], coords[1])
        if len(coords) > 2:
            return [wgs_lng, wgs_lat, coords[2]]
        return [wgs_lng, wgs_lat]
    return [convert_coords(c) for c in coords]


def convert_geojson_file(input_path, output_path):
    """转换整个 GeoJSON 文件"""
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    converted = copy.deepcopy(data)

    # Add CRS declaration
    converted["crs"] = {
        "type": "name",
        "properties": {"name": "urn:ogc:def:crs:EPSG::4326"}
    }

    feature_count = 0
    coord_count = 0
    for feat in converted["features"]:
        feat["geometry"]["coordinates"] = convert_coords(feat["geometry"]["coordinates"])
        feature_count += 1
        # Count coords for reporting
        def count_pts(c):
            if isinstance(c[0], (int, float)):
                return 1
            return sum(count_pts(x) for x in c)
        coord_count += count_pts(feat["geometry"]["coordinates"])

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)

    return feature_count, coord_count


def main():
    print("=" * 60)
    print("GCJ-02 → WGS-84 坐标系统一转换")
    print("=" * 60)

    files_to_convert = [
        ("data/gis/Key_Plots_District.json", "重点地块"),
        ("data/gis/Boundary_Scope.geojson", "研究范围边界"),
    ]

    for rel_path, label in files_to_convert:
        src = ROOT / rel_path
        if not src.exists():
            print(f"  ⚠️ 文件不存在: {rel_path}")
            continue

        # Backup original
        backup = src.with_suffix(src.suffix + ".gcj02_backup")
        if not backup.exists():
            import shutil
            shutil.copy2(src, backup)
            print(f"  📦 已备份原始文件: {backup.name}")

        features, coords = convert_geojson_file(src, src)
        print(f"  ✅ {label}: 转换 {features} 个要素, {coords} 个坐标点 → WGS-84")

    # Verification
    print()
    print("=" * 60)
    print("转换后验证")
    import pandas as pd
    poi = pd.read_csv(ROOT / "data/csv/Changchun_POI_Real.csv", encoding="utf-8-sig")

    with open(ROOT / "data/gis/Key_Plots_District.json", encoding="utf-8") as f:
        geo = json.load(f)

    total_bbox_hits = 0
    for feat in geo["features"]:
        props = feat["properties"]
        name = props.get("Name", props.get("name", "?"))
        coords_flat = []

        def flatten(c):
            if isinstance(c[0], (int, float)):
                coords_flat.append((c[0], c[1]))
                return
            for item in c:
                flatten(item)

        flatten(feat["geometry"]["coordinates"])
        lngs = [p[0] for p in coords_flat]
        lats = [p[1] for p in coords_flat]

        hits = poi[
            (poi["Lng"] >= min(lngs)) & (poi["Lng"] <= max(lngs))
            & (poi["Lat"] >= min(lats)) & (poi["Lat"] <= max(lats))
        ]
        total_bbox_hits += len(hits)
        print(f"  {name}: BBox 内 POI = {len(hits)}")

    print(f"\n  5地块总命中: {total_bbox_hits} (转换前: 10)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
