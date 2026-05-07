"""数据格式优化脚本 — 将慢速格式转为快速格式。

用法:
    python scripts/optimize_data.py

主要操作:
    1. 将 points.xlsx → points.parquet (加速 ~10x)
    2. 预计算边界面积等静态指标并写入 JSON 缓存
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# 确保项目根目录在 sys.path 中
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DATA_DIR = ROOT / "data"
CACHE_FILE = DATA_DIR / "precomputed_metrics.json"


def convert_xlsx_to_parquet():
    """将 Changchun_Precise_Points.xlsx 转为 Parquet 格式。"""
    xlsx_path = DATA_DIR / "Changchun_Precise_Points.xlsx"
    parquet_path = DATA_DIR / "Changchun_Precise_Points.parquet"

    if not xlsx_path.exists():
        print(f"[跳过] {xlsx_path.name} 不存在")
        return

    df = pd.read_excel(str(xlsx_path))
    df.to_parquet(str(parquet_path), index=False, engine="pyarrow")
    print(f"[完成] {xlsx_path.name} → {parquet_path.name}  ({len(df)} 行)")


def precompute_boundary_area():
    """预计算研究边界面积并缓存。"""
    geojson_path = DATA_DIR / "shp" / "Boundary_Scope.geojson"
    if not geojson_path.exists():
        print(f"[跳过] {geojson_path.name} 不存在")
        return {}

    with open(geojson_path, "r", encoding="utf-8") as f:
        geo = json.load(f)

    total = 0.0
    for feat in geo.get("features", []):
        coords = np.array(feat["geometry"]["coordinates"][0])
        x, y = coords[:, 0], coords[:, 1]
        area_deg = abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / 2
        total += area_deg * 80 * 111 * 100

    result = {"boundary_ha": round(total, 1)}
    print(f"[完成] 边界面积预计算: {result['boundary_ha']} 公顷")
    return result


def precompute_data_counts():
    """预计算 POI/GVI/NLP 行数。"""
    counts = {}
    for key, filename in [
        ("poi_real_count", "Changchun_POI_Real.csv"),
        ("poi_baidu_count", "Changchun_POI_Baidu_New.csv"),
        ("gvi_count", "GVI_Results_Analysis.csv"),
        ("nlp_count", "CV_NLP_RawData.csv"),
    ]:
        path = DATA_DIR / filename
        if path.exists():
            df = pd.read_csv(str(path), encoding="utf-8-sig")
            counts[key] = len(df)
            print(f"[完成] {filename}: {counts[key]} 行")
        else:
            print(f"[跳过] {filename} 不存在")
    return counts


def main():
    print("=" * 50)
    print("📦 ultimateDESIGN 数据优化脚本")
    print("=" * 50)

    # 1. 格式转换
    print("\n--- 步骤 1: 数据格式转换 ---")
    convert_xlsx_to_parquet()

    # 2. 预计算指标
    print("\n--- 步骤 2: 预计算静态指标 ---")
    metrics = {}
    metrics.update(precompute_boundary_area())
    metrics.update(precompute_data_counts())

    # 3. 写入缓存
    if metrics:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        print(f"\n[完成] 缓存已写入: {CACHE_FILE}")

    print("\n✅ 优化完成！")


if __name__ == "__main__":
    main()
