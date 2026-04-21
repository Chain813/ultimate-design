"""
📊 数据质量自动化检查脚本 (Data Quality Check)
-------------------------------------------------
对 data/ 目录下的所有核心数据集进行四维体检：
1. 完整性（空值率、缺字段）
2. 一致性（命名、编码、类型）
3. 合理性（取值范围与业务逻辑）
4. 可用性（是否满足当前模型输入）

输出：终端摘要 + docs/STAGE2_DATA_QUALITY_REPORT.md
"""
import sys
import os
import json
from pathlib import Path

# Windows 终端 UTF-8 编码修复
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 确保可以引用项目模块
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np


# ==========================================
# 📁 数据文件注册表
# ==========================================
DATA_REGISTRY = {
    "POI": {
        "path": ROOT / "data" / "Changchun_POI_Real.csv",
        "required_cols": ["Name", "Lat", "Lng"],
        "lat_range": (43.85, 43.95),
        "lng_range": (125.30, 125.40),
    },
    "交通": {
        "path": ROOT / "data" / "Changchun_Traffic_Real.csv",
        "required_cols": ["Name", "Lat", "Lng"],
        "lat_range": (43.85, 43.95),
        "lng_range": (125.30, 125.40),
    },
    "NLP 舆情": {
        "path": ROOT / "data" / "CV_NLP_RawData.csv",
        "required_cols": ["Text", "Keyword", "Source"],
    },
    "GVI 环境品质": {
        "path": ROOT / "data" / "GVI_Results_Analysis.csv",
        "required_cols": ["GVI", "SVF", "Enclosure", "Clutter"],
    },
    "精确点位": {
        "path": ROOT / "data" / "Changchun_Precise_Points.xlsx",
        "required_cols": ["ID", "Lng", "Lat"],
        "lat_range": (43.85, 43.95),
        "lng_range": (125.30, 125.40),
    },
}

GEO_REGISTRY = {
    "研究范围边界": ROOT / "data" / "shp" / "Boundary_Scope.geojson",
    "重点地块": ROOT / "data" / "shp" / "Key_Plots_District.json",
    "建筑轮廓": ROOT / "data" / "shp" / "Building_Footprints.geojson",
}


def check_csv_or_excel(name: str, cfg: dict) -> dict:
    """对一份表格数据进行四维体检，返回报告字典"""
    report = {"name": name, "status": "OK", "issues": [], "stats": {}}
    path = cfg["path"]

    if not path.exists():
        report["status"] = "MISSING"
        report["issues"].append(f"文件不存在: {path}")
        return report

    # 加载
    try:
        if path.suffix == ".xlsx":
            df = pd.read_excel(path)
        else:
            try:
                df = pd.read_csv(path, encoding="utf-8-sig")
            except Exception:
                df = pd.read_csv(path, encoding="gbk")
    except Exception as e:
        report["status"] = "ERROR"
        report["issues"].append(f"无法读取文件: {e}")
        return report

    report["stats"]["rows"] = len(df)
    report["stats"]["cols"] = len(df.columns)
    report["stats"]["columns"] = list(df.columns)

    # 1. 完整性
    null_pct = df.isnull().mean()
    high_null = null_pct[null_pct > 0.1]
    if not high_null.empty:
        for col, pct in high_null.items():
            report["issues"].append(f"列 '{col}' 空值率 {pct:.1%}")

    dup_count = df.duplicated().sum()
    report["stats"]["duplicate_rows"] = int(dup_count)
    if dup_count > 0:
        report["issues"].append(f"重复行 {dup_count} 行 ({dup_count / len(df):.1%})")

    # 2. 一致性 — 必需字段
    for col in cfg.get("required_cols", []):
        if col not in df.columns:
            report["issues"].append(f"缺失必需字段: '{col}'")
            report["status"] = "WARNING"

    # 3. 合理性 — 坐标范围
    lat_range = cfg.get("lat_range")
    lng_range = cfg.get("lng_range")
    if lat_range and "Lat" in df.columns:
        out_of_range = df[(df["Lat"] < lat_range[0]) | (df["Lat"] > lat_range[1])]
        if not out_of_range.empty:
            report["issues"].append(
                f"纬度超范围 ({lat_range}): {len(out_of_range)} 条"
            )

    if lng_range and "Lng" in df.columns:
        out_of_range = df[(df["Lng"] < lng_range[0]) | (df["Lng"] > lng_range[1])]
        if not out_of_range.empty:
            report["issues"].append(
                f"经度超范围 ({lng_range}): {len(out_of_range)} 条"
            )

    # 4. 可用性评分
    if not report["issues"]:
        report["grade"] = "A"
    elif report["status"] == "WARNING":
        report["grade"] = "C"
    elif len(report["issues"]) <= 2:
        report["grade"] = "B"
    else:
        report["grade"] = "C"

    return report


def check_geojson(name: str, path: Path) -> dict:
    """对一份 GeoJSON / JSON 文件进行基本体检"""
    report = {"name": name, "status": "OK", "issues": [], "stats": {}}

    if not path.exists():
        report["status"] = "MISSING"
        report["issues"].append(f"文件不存在: {path}")
        return report

    try:
        with open(path, "r", encoding="utf-8") as f:
            geo = json.load(f)
    except Exception as e:
        report["status"] = "ERROR"
        report["issues"].append(f"无法解析 JSON: {e}")
        return report

    features = geo.get("features", [])
    report["stats"]["feature_count"] = len(features)
    report["stats"]["file_size_mb"] = round(path.stat().st_size / 1024 / 1024, 2)

    if len(features) == 0:
        report["issues"].append("features 数组为空")
        report["status"] = "WARNING"

    # 检查属性完整性
    for i, feat in enumerate(features[:10]):
        props = feat.get("properties", {})
        geom = feat.get("geometry", {})
        if not geom.get("coordinates"):
            report["issues"].append(f"Feature #{i} 缺少坐标数据")
        name_field = props.get("name", props.get("Name"))
        if name_field is None and "OBJECTID" not in props:
            report["issues"].append(f"Feature #{i} 缺少 name/OBJECTID 属性")

    report["grade"] = "A" if not report["issues"] else "B"
    return report


def generate_plot_cards(plots_path: Path, gvi_path: Path, poi_path: Path) -> list:
    """为 5 个重点地块生成诊断卡"""
    cards = []
    if not all(p.exists() for p in [plots_path, gvi_path, poi_path]):
        return cards

    with open(plots_path, "r", encoding="utf-8") as f:
        geo = json.load(f)

    try:
        df_poi = pd.read_csv(poi_path, encoding="utf-8-sig")
    except Exception:
        df_poi = pd.DataFrame()

    try:
        df_gvi = pd.read_csv(gvi_path)
    except Exception:
        df_gvi = pd.DataFrame()

    for feat in geo.get("features", []):
        props = feat.get("properties", {})
        name = props.get("name", f"地块_{props.get('OBJECTID', '?')}")
        area_sqm = props.get("Shape_Area", 0)
        coords = feat["geometry"]["coordinates"][0]

        # 计算边界框
        lngs = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        bbox = {
            "min_lng": min(lngs),
            "max_lng": max(lngs),
            "min_lat": min(lats),
            "max_lat": max(lats),
        }

        # 统计 POI 覆盖
        poi_count = 0
        if not df_poi.empty and "Lng" in df_poi.columns and "Lat" in df_poi.columns:
            in_bbox = df_poi[
                (df_poi["Lng"] >= bbox["min_lng"])
                & (df_poi["Lng"] <= bbox["max_lng"])
                & (df_poi["Lat"] >= bbox["min_lat"])
                & (df_poi["Lat"] <= bbox["max_lat"])
            ]
            poi_count = len(in_bbox)

        cards.append(
            {
                "name": name,
                "area_ha": round(area_sqm / 10000, 2),
                "poi_count": poi_count,
                "bbox": bbox,
            }
        )

    return cards


def main():
    print("=" * 60)
    print("📊 ultimateDESIGN 数据质量自动化检查")
    print("=" * 60)

    all_reports = []

    # 表格数据检查
    print("\n📋 表格数据检查:")
    for name, cfg in DATA_REGISTRY.items():
        r = check_csv_or_excel(name, cfg)
        all_reports.append(r)
        icon = "✅" if r["grade"] in ("A", "B") else "⚠️" if r["status"] != "MISSING" else "❌"
        print(f"  {icon} [{r.get('grade', 'N/A')}] {name}: {r['stats'].get('rows', 'N/A')} 行, {len(r['issues'])} 个问题")
        for issue in r["issues"]:
            print(f"      ⮑ {issue}")

    # 空间数据检查
    print("\n🗺️ 空间数据检查:")
    for name, path in GEO_REGISTRY.items():
        r = check_geojson(name, path)
        all_reports.append(r)
        icon = "✅" if r.get("grade") in ("A", "B") else "⚠️"
        size = r["stats"].get("file_size_mb", "?")
        count = r["stats"].get("feature_count", "?")
        print(f"  {icon} [{r.get('grade', 'N/A')}] {name}: {count} 个要素, {size} MB")
        for issue in r["issues"]:
            print(f"      ⮑ {issue}")

    # 地块诊断卡
    print("\n📍 重点地块诊断卡:")
    cards = generate_plot_cards(
        GEO_REGISTRY["重点地块"],
        DATA_REGISTRY["GVI 环境品质"]["path"],
        DATA_REGISTRY["POI"]["path"],
    )
    for card in cards:
        print(f"  🏗️ {card['name']}: {card['area_ha']} ha, POI覆盖 {card['poi_count']} 个")

    # 输出 Markdown 报告
    md_path = ROOT / "docs" / "STAGE2_DATA_QUALITY_REPORT.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 第二阶段数据质量检查报告 (自动生成)\n\n")
        f.write(f"生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        f.write("## 1. 表格数据\n\n")
        f.write("| 数据集 | 行数 | 列数 | 评级 | 问题数 |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        for r in all_reports:
            if "feature_count" not in r.get("stats", {}):
                rows = r["stats"].get("rows", "N/A")
                cols = r["stats"].get("cols", "N/A")
                f.write(f"| {r['name']} | {rows} | {cols} | {r.get('grade', 'N/A')} | {len(r['issues'])} |\n")

        f.write("\n## 2. 空间数据\n\n")
        f.write("| 数据集 | 要素数 | 大小(MB) | 评级 | 问题数 |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        for r in all_reports:
            if "feature_count" in r.get("stats", {}):
                cnt = r["stats"].get("feature_count", "N/A")
                size = r["stats"].get("file_size_mb", "N/A")
                f.write(f"| {r['name']} | {cnt} | {size} | {r.get('grade', 'N/A')} | {len(r['issues'])} |\n")

        f.write("\n## 3. 问题详情\n\n")
        for r in all_reports:
            if r["issues"]:
                f.write(f"### {r['name']}\n\n")
                for issue in r["issues"]:
                    f.write(f"- ⚠️ {issue}\n")
                f.write("\n")

        f.write("## 4. 重点地块诊断卡\n\n")
        f.write("| 地块名称 | 面积(ha) | POI覆盖 |\n")
        f.write("| --- | --- | --- |\n")
        for card in cards:
            f.write(f"| {card['name']} | {card['area_ha']} | {card['poi_count']} |\n")

    print(f"\n✅ 报告已生成: {md_path}")
    print("=" * 60)

    # 返回退出码
    has_critical = any(r["status"] in ("MISSING", "ERROR") for r in all_reports)
    return 1 if has_critical else 0


if __name__ == "__main__":
    sys.exit(main())
