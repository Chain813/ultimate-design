"""扩展 POI 数据采集脚本 — 覆盖重点地块区域

根据数据质量诊断报告，当前 POI 数据的纬度范围 (43.8939-43.9047) 未能覆盖
北部的农贸水产市场和食品调料大市场地块 (纬度高达 43.9083)。

本脚本使用百度地图 Place API v2 的矩形区域检索，以完整覆盖所有 5 个重点地块
以及现有 POI 范围的合并包围盒进行搜索。

使用方法:
    1. 确保 .env 中填写了有效的 Baidu_Map_AK
    2. 运行: python scripts/fetch_expanded_poi.py
    3. 新数据将自动合并到 data/Changchun_POI_Real.csv
"""
import os
import sys
import time
import math
import json
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

# ==========================================
# 配置
# ==========================================
AK = os.getenv("Baidu_Map_AK", "")
if not AK or AK.startswith("YOUR_"):
    print("❌ 请在 .env 中填写有效的 Baidu_Map_AK")
    sys.exit(1)

# 百度坐标偏移常量 (BD-09 → WGS-84 近似修正)
X_PI = math.pi * 3000.0 / 180.0


def bd09_to_gcj02(bd_lng, bd_lat):
    """百度坐标系 (BD-09) 转 火星坐标系 (GCJ-02)"""
    x = bd_lng - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * X_PI)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * X_PI)
    return z * math.cos(theta), z * math.sin(theta)


def gcj02_to_wgs84(lng, lat):
    """火星坐标系 (GCJ-02) 转 WGS-84 (近似)"""
    a = 6378245.0
    ee = 0.00669342162296594323
    d_lat = _transform_lat(lng - 105.0, lat - 35.0)
    d_lng = _transform_lng(lng - 105.0, lat - 35.0)
    rad_lat = lat / 180.0 * math.pi
    magic = math.sin(rad_lat)
    magic = 1 - ee * magic * magic
    sqrt_magic = math.sqrt(magic)
    d_lat = (d_lat * 180.0) / ((a * (1 - ee)) / (magic * sqrt_magic) * math.pi)
    d_lng = (d_lng * 180.0) / (a / sqrt_magic * math.cos(rad_lat) * math.pi)
    return lng - d_lng, lat - d_lat


def _transform_lat(lng, lat):
    ret = (-100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat +
           0.1 * lng * lat + 0.2 * math.sqrt(abs(lng)))
    ret += (20.0 * math.sin(6.0 * lng * math.pi) + 20.0 * math.sin(2.0 * lng * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * math.pi) + 40.0 * math.sin(lat / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * math.pi) + 320.0 * math.sin(lat * math.pi / 30.0)) * 2.0 / 3.0
    return ret


def _transform_lng(lng, lat):
    ret = (300.0 + lng + 2.0 * lat + 0.1 * lng * lng +
           0.1 * lng * lat + 0.1 * math.sqrt(abs(lng)))
    ret += (20.0 * math.sin(6.0 * lng * math.pi) + 20.0 * math.sin(2.0 * lng * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * math.pi) + 40.0 * math.sin(lng / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * math.pi) + 300.0 * math.sin(lng / 30.0 * math.pi)) * 2.0 / 3.0
    return ret


def bd09_to_wgs84(bd_lng, bd_lat):
    """百度坐标 → WGS-84"""
    gcj_lng, gcj_lat = bd09_to_gcj02(bd_lng, bd_lat)
    return gcj02_to_wgs84(gcj_lng, gcj_lat)


# ==========================================
# 搜索范围 (WGS-84)
# 合并现有 POI 范围 + 所有 5 个重点地块 + 外扩 0.005°缓冲
# ==========================================
# 现有 POI: Lat 43.8939-43.9047, Lng 125.3311-125.3472
# 重点地块最北: 43.9083 (农贸水产市场/食品大市场)
# 重点地块最东: 125.3456 (清禾集贸市场)
SEARCH_BOUNDS = {
    "lat_min": 43.8900,
    "lat_max": 43.9130,  # 向北扩展覆盖所有重点地块
    "lng_min": 125.3270,
    "lng_max": 125.3520,
}

# 百度 Place API v2 搜索类别
QUERY_CATEGORIES = [
    "美食", "购物", "生活服务", "休闲娱乐",
    "酒店", "旅游景点", "教育培训", "医疗健康",
    "交通设施", "金融", "房产",
]


def fetch_poi_for_query(query: str, bounds: dict) -> list:
    """使用百度地图 Place API 搜索指定类别的 POI"""
    # 百度 API bounds 格式: lat_min,lng_min,lat_max,lng_max
    bounds_str = f"{bounds['lat_min']},{bounds['lng_min']},{bounds['lat_max']},{bounds['lng_max']}"

    all_pois = []
    page_num = 0

    while True:
        url = "https://api.map.baidu.com/place/v2/search"
        params = {
            "query": query,
            "bounds": bounds_str,
            "output": "json",
            "ak": AK,
            "page_size": 20,
            "page_num": page_num,
            "coord_type": 1,  # 返回百度坐标
        }

        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()

            if data.get("status") != 0:
                print(f"  ⚠️ API 错误 (query={query}, page={page_num}): {data.get('message', 'unknown')}")
                break

            results = data.get("results", [])
            if not results:
                break

            for poi in results:
                loc = poi.get("location", {})
                bd_lng = loc.get("lng", 0)
                bd_lat = loc.get("lat", 0)

                if bd_lng == 0 or bd_lat == 0:
                    continue

                # 转换为 WGS-84
                wgs_lng, wgs_lat = bd09_to_wgs84(bd_lng, bd_lat)

                all_pois.append({
                    "Name": poi.get("name", ""),
                    "Type": poi.get("detail_info", {}).get("tag", query),
                    "Lat": round(wgs_lat, 6),
                    "Lng": round(wgs_lng, 6),
                })

            page_num += 1
            if page_num >= 20:  # 百度 API 最多 400 条 (20页×20条)
                break

            time.sleep(0.3)

        except Exception as e:
            print(f"  ❌ 网络错误 (query={query}): {e}")
            break

    return all_pois


def main():
    print("=" * 60)
    print("📍 扩展 POI 数据采集 — 覆盖全部重点地块")
    print("=" * 60)
    print(f"搜索范围: Lat {SEARCH_BOUNDS['lat_min']}-{SEARCH_BOUNDS['lat_max']}, "
          f"Lng {SEARCH_BOUNDS['lng_min']}-{SEARCH_BOUNDS['lng_max']}")
    print()

    all_pois = []
    for query in QUERY_CATEGORIES:
        pois = fetch_poi_for_query(query, SEARCH_BOUNDS)
        print(f"  ✅ {query}: {len(pois)} 个")
        all_pois.extend(pois)
        time.sleep(0.5)

    if not all_pois:
        print("❌ 未获取到任何 POI 数据，请检查 API Key 和网络")
        return 1

    # 去重 (按名称+坐标)
    df_new = pd.DataFrame(all_pois)
    df_new = df_new.drop_duplicates(subset=["Name", "Lat", "Lng"])
    print(f"\n🔄 新采集 POI (去重后): {len(df_new)} 个")

    # 合并现有数据
    existing_path = ROOT / "data" / "Changchun_POI_Real.csv"
    if existing_path.exists():
        try:
            df_existing = pd.read_csv(existing_path, encoding="utf-8-sig")
            print(f"📂 现有 POI: {len(df_existing)} 个")

            # 统一列结构
            if "Type" not in df_existing.columns:
                df_existing["Type"] = ""

            df_merged = pd.concat([df_existing, df_new], ignore_index=True)
            df_merged = df_merged.drop_duplicates(subset=["Name", "Lat", "Lng"])
            print(f"🔗 合并后 (去重): {len(df_merged)} 个 (新增 {len(df_merged) - len(df_existing)} 个)")
        except Exception as e:
            print(f"⚠️ 读取现有数据失败: {e}，使用新数据覆盖")
            df_merged = df_new
    else:
        df_merged = df_new

    # 保存
    output_path = ROOT / "data" / "Changchun_POI_Real.csv"
    df_merged.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n💾 已保存: {output_path}")
    print(f"   纬度范围: {df_merged['Lat'].min():.6f} - {df_merged['Lat'].max():.6f}")
    print(f"   经度范围: {df_merged['Lng'].min():.6f} - {df_merged['Lng'].max():.6f}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
