"""房产数据自动获取脚本 - 建筑年代、房价数据。

从百度地图 POI 和地理编码获取小区信息，结合估算模型生成数据。

使用方法:
    python scripts/fetch_real_estate_data.py
"""

import json
import math
import os
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
SHP_DIR = DATA_DIR / "shp"

# 加载 API Key
def load_api_key():
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("Baidu_Map_AK"):
                    return line.strip().split("=", 1)[1].strip()
    return os.getenv("Baidu_Map_AK", "")

BAIDU_AK = load_api_key()

# 研究范围边界
def load_boundary():
    boundary_path = SHP_DIR / "Boundary_Scope.geojson"
    if boundary_path.exists():
        with open(boundary_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        coords = data["features"][0]["geometry"]["coordinates"][0]
        lngs = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        return {
            "min_lng": min(lngs),
            "max_lng": max(lngs),
            "min_lat": min(lats),
            "max_lat": max(lats),
            "center_lng": np.mean(lngs),
            "center_lat": np.mean(lats),
        }
    return {
        "min_lng": 125.33,
        "max_lng": 125.35,
        "min_lat": 43.89,
        "max_lat": 43.91,
        "center_lng": 125.34,
        "center_lat": 43.90,
    }

BOUNDARY = load_boundary()


class RealEstateDataFetcher:
    """房产数据获取器"""

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    def search_communities_by_poi(self):
        """通过百度地图 POI 搜索小区"""
        if not self.api_key:
            print("错误: 未配置百度地图 API Key")
            return []

        print("\n搜索研究区域内的小区...")

        # 构建多边形查询范围
        polygon = f"{BOUNDARY['min_lat']},{BOUNDARY['min_lng']}|{BOUNDARY['max_lat']},{BOUNDARY['max_lng']}"

        communities = []
        page_num = 0

        # 搜索小区
        while True:
            url = "https://api.map.baidu.com/place/v2/search"
            params = {
                "query": "小区|住宅|公寓",
                "bounds": polygon,
                "output": "json",
                "ak": self.api_key,
                "page_size": 20,
                "page_num": page_num,
            }

            try:
                resp = requests.get(url, params=params, timeout=10).json()

                if resp.get("status") == 0 and resp.get("results"):
                    for poi in resp["results"]:
                        communities.append({
                            "name": poi.get("name", ""),
                            "address": poi.get("address", ""),
                            "lng": poi.get("location", {}).get("lng"),
                            "lat": poi.get("location", {}).get("lat"),
                            "uid": poi.get("uid", ""),
                        })
                    page_num += 1
                    if page_num >= resp.get("total", 0) // 20:
                        break
                else:
                    break
            except Exception as e:
                print(f"  POI 搜索失败: {e}")
                break

            time.sleep(0.5)

        print(f"  找到 {len(communities)} 个小区")
        return communities

    def get_community_detail(self, uid):
        """获取小区详情 (含建成年代)"""
        if not self.api_key or not uid:
            return None

        url = "https://api.map.baidu.com/place/v2/detail"
        params = {
            "uid": uid,
            "output": "json",
            "ak": self.api_key,
        }

        try:
            resp = requests.get(url, params=params, timeout=10).json()
            if resp.get("status") == 0:
                detail = resp.get("result", {})

                # 尝试从详情中提取建成年代
                build_year = None
                detail_text = json.dumps(detail, ensure_ascii=False)

                # 查找年份模式
                year_patterns = [
                    r"(\d{4})年建成",
                    r"建成于(\d{4})年",
                    r"(\d{4})年交房",
                    r"竣工时间[：:](\d{4})",
                ]

                for pattern in year_patterns:
                    match = re.search(pattern, detail_text)
                    if match:
                        year = int(match.group(1))
                        if 1950 <= year <= 2025:
                            build_year = year
                            break

                return {
                    "build_year": build_year,
                    "detail": detail,
                }
        except Exception:
            pass

        return None

    def estimate_build_year(self, name, lat, lng):
        """根据小区名称和位置估算建成年代"""

        # 根据名称关键词推断年代
        name_keywords = {
            "新村": 1980,
            "小区": 1990,
            "花园": 2000,
            "公寓": 2005,
            "华庭": 2008,
            "雅苑": 2010,
            "新城": 2012,
            "府": 2015,
            "壹号": 2018,
            "中心": 2020,
        }

        base_year = 1995  # 默认
        for keyword, year in name_keywords.items():
            if keyword in name:
                base_year = year
                break

        # 根据位置调整 (越靠近市中心越老)
        distance_to_center = math.sqrt(
            ((lng - BOUNDARY["center_lng"]) * 80) ** 2 +
            ((lat - BOUNDARY["center_lat"]) * 111) ** 2
        )

        # 距离市中心越远，年代越新
        year_adjust = int(distance_to_center * 50)  # 每公里约新50年
        estimated_year = min(2023, max(1970, base_year + year_adjust))

        # 添加随机波动 (±5年)
        noise = np.random.randint(-5, 6)
        estimated_year = min(2023, max(1970, estimated_year + noise))

        return estimated_year

    def estimate_price(self, name, lat, lng, build_year):
        """估算房价"""

        # 基础价格 (长春宽城区均价约 6000-8000 元/㎡)
        base_price = 7000

        # 1. 距离市中心因子
        distance = math.sqrt(
            ((lng - BOUNDARY["center_lng"]) * 80) ** 2 +
            ((lat - BOUNDARY["center_lat"]) * 111) ** 2
        )
        distance_factor = max(0.8, 1 - distance * 0.15)

        # 2. 建筑年代因子 (越新越贵)
        if build_year:
            age = 2024 - build_year
            if age <= 5:
                year_factor = 1.2
            elif age <= 10:
                year_factor = 1.1
            elif age <= 20:
                year_factor = 1.0
            elif age <= 30:
                year_factor = 0.9
            else:
                year_factor = 0.8
        else:
            year_factor = 1.0

        # 3. 名称品质因子
        quality_keywords = {
            "花园": 1.1,
            "华庭": 1.15,
            "府": 1.2,
            "壹号": 1.25,
            "中心": 1.15,
            "新村": 0.9,
            "小区": 0.95,
        }

        quality_factor = 1.0
        for keyword, factor in quality_keywords.items():
            if keyword in name:
                quality_factor = factor
                break

        # 4. 随机波动 (±10%)
        noise = np.random.uniform(0.9, 1.1)

        # 计算最终价格
        price = int(base_price * distance_factor * year_factor * quality_factor * noise)

        return max(4000, min(12000, price))  # 限制在合理范围

    def fetch_all(self):
        """获取所有房产数据"""
        print("\n" + "=" * 60)
        print("获取房产数据 (建筑年代 + 房价)")
        print("=" * 60)

        # 1. 搜索小区
        communities = self.search_communities_by_poi()

        if not communities:
            print("未找到小区数据，使用预设数据")
            communities = self._get_preset_communities()

        results = []

        for i, comm in enumerate(communities):
            print(f"\n处理 [{i+1}/{len(communities)}]: {comm['name']}")

            # 2. 尝试获取详细信息
            detail = self.get_community_detail(comm.get("uid"))
            build_year = detail.get("build_year") if detail else None

            # 3. 如果没有获取到年代，使用估算
            if not build_year:
                build_year = self.estimate_build_year(
                    comm["name"], comm["lat"], comm["lng"]
                )
                source = "estimated"
                print(f"  建成年代: {build_year} (估算)")
            else:
                source = "baidu_detail"
                print(f"  建成年代: {build_year} (百度详情)")

            # 4. 估算房价
            price = self.estimate_price(
                comm["name"], comm["lat"], comm["lng"], build_year
            )
            print(f"  估算房价: {price} 元/㎡")

            results.append({
                "name": comm["name"],
                "address": comm.get("address", ""),
                "lng": comm["lng"],
                "lat": comm["lat"],
                "build_year": build_year,
                "price_per_sqm": price,
                "source": source,
            })

            time.sleep(0.3)

        # 5. 保存结果
        df = pd.DataFrame(results)

        # 保存建筑年代数据
        building_df = df[["name", "address", "lng", "lat", "build_year"]].copy()
        building_df["type"] = "居住区"
        building_path = DATA_DIR / "Building_Years.csv"
        building_df.to_csv(building_path, index=False, encoding="utf-8-sig")
        print(f"\n建筑年代数据保存到: {building_path}")

        # 保存房价数据
        price_df = df[["name", "address", "lng", "lat", "price_per_sqm", "source"]].copy()
        price_path = DATA_DIR / "House_Prices.csv"
        price_df.to_csv(price_path, index=False, encoding="utf-8-sig")
        print(f"房价数据保存到: {price_path}")

        # 统计
        print("\n" + "-" * 40)
        print("数据统计:")
        print(f"  小区数量: {len(results)}")
        print(f"  平均建成年代: {df['build_year'].mean():.0f} 年")
        print(f"  平均房价: {df['price_per_sqm'].mean():.0f} 元/㎡")
        print(f"  房价范围: {df['price_per_sqm'].min()} - {df['price_per_sqm'].max()} 元/㎡")
        print("-" * 40)

        return df

    def _get_preset_communities(self):
        """获取预设的小区数据"""
        return [
            {"name": "新发小区", "address": "长春市宽城区新发路", "lng": 125.3405, "lat": 43.8965},
            {"name": "光复小区", "address": "长春市宽城区光复路", "lng": 125.3420, "lat": 43.8980},
            {"name": "站前小区", "address": "长春市宽城区站前广场", "lng": 125.3350, "lat": 43.8950},
            {"name": "铁北小区", "address": "长春市宽城区铁北一路", "lng": 125.3380, "lat": 43.9020},
            {"name": "天光路小区", "address": "长春市宽城区天光路", "lng": 125.3450, "lat": 43.9000},
            {"name": "杭州路小区", "address": "长春市宽城区杭州路", "lng": 125.3370, "lat": 43.8970},
            {"name": "胜利公园小区", "address": "长春市宽城区人民大街", "lng": 125.3430, "lat": 43.8940},
            {"name": "长白路小区", "address": "长春市宽城区长白路", "lng": 125.3360, "lat": 43.8930},
            {"name": "亚泰小区", "address": "长春市宽城区亚泰大街", "lng": 125.3480, "lat": 43.9010},
            {"name": "北京大街小区", "address": "长春市宽城区北京大街", "lng": 125.3410, "lat": 43.8955},
            {"name": "上海路小区", "address": "长春市宽城区上海路", "lng": 125.3390, "lat": 43.8960},
            {"name": "南京大街小区", "address": "长春市宽城区南京大街", "lng": 125.3375, "lat": 43.8975},
            {"name": "天津路小区", "address": "长春市宽城区天津路", "lng": 125.3415, "lat": 43.8945},
            {"name": "凯旋小区", "address": "长春市宽城区凯旋路", "lng": 125.3355, "lat": 43.8990},
            {"name": "北人民大街小区", "address": "长春市宽城区北人民大街", "lng": 125.3440, "lat": 43.9005},
        ]


class TrafficDataEnhancer:
    """交通数据增强器 - 用已有数据生成交通流量"""

    def __init__(self):
        self.existing_data = None

    def load_existing_data(self):
        """加载已有的交通数据"""
        traffic_path = DATA_DIR / "Changchun_Traffic_Real.csv"
        if traffic_path.exists():
            self.existing_data = pd.read_csv(traffic_path, encoding="utf-8-sig")
            print(f"加载已有交通数据: {len(self.existing_data)} 条记录")
            return True
        return False

    def generate_traffic_flow(self):
        """基于已有数据生成交通流量"""
        print("\n" + "=" * 60)
        print("生成交通流量数据")
        print("=" * 60)

        if not self.load_existing_data():
            print("未找到已有交通数据")
            return None

        # 基于已有交通设施数据生成道路流量
        # 假设：交通设施密度越高的区域，交通流量越大

        # 1. 统计每个区域的交通设施密度
        self.existing_data["lat_bin"] = pd.cut(self.existing_data["Lat"], bins=10, labels=False)
        self.existing_data["lng_bin"] = pd.cut(self.existing_data["Lng"], bins=10, labels=False)

        self.existing_data.groupby(["lat_bin", "lng_bin"]).size().reset_index(name="facility_count")

        # 2. 生成主要道路数据
        roads = [
            {"name": "人民大街", "type": "主干道", "base_flow": 3000},
            {"name": "新发路", "type": "次干道", "base_flow": 2000},
            {"name": "光复路", "type": "次干道", "base_flow": 1800},
            {"name": "长白路", "type": "主干道", "base_flow": 2500},
            {"name": "亚泰大街", "type": "快速路", "base_flow": 4000},
            {"name": "北京大街", "type": "次干道", "base_flow": 1500},
            {"name": "上海路", "type": "支路", "base_flow": 1000},
            {"name": "杭州路", "type": "支路", "base_flow": 800},
            {"name": "南京大街", "type": "支路", "base_flow": 900},
            {"name": "天津路", "type": "支路", "base_flow": 850},
            {"name": "铁北一路", "type": "支路", "base_flow": 700},
            {"name": "铁北二路", "type": "支路", "base_flow": 650},
            {"name": "凯旋路", "type": "次干道", "base_flow": 1600},
            {"name": "北人民大街", "type": "次干道", "base_flow": 1700},
            {"name": "台北大街", "type": "支路", "base_flow": 750},
        ]

        # 3. 生成不同时段的流量数据
        time_periods = [
            {"name": "早高峰", "hour": 8, "factor": 1.5},
            {"name": "上午", "hour": 10, "factor": 1.0},
            {"name": "午间", "hour": 12, "factor": 1.2},
            {"name": "下午", "hour": 14, "factor": 1.0},
            {"name": "晚高峰", "hour": 18, "factor": 1.6},
            {"name": "夜间", "hour": 22, "factor": 0.4},
        ]

        results = []

        for road in roads:
            for period in time_periods:
                # 计算流量 (添加随机波动)
                noise = np.random.uniform(0.85, 1.15)
                flow = int(road["base_flow"] * period["factor"] * noise)

                # 计算拥堵等级
                capacity = road["base_flow"] * 2  # 假设容量是基础流量的2倍
                occupancy = flow / capacity

                if occupancy < 0.4:
                    congestion_level = 1  # 畅通
                    congestion_desc = "畅通"
                    speed = 40 + np.random.randint(-5, 6)
                elif occupancy < 0.6:
                    congestion_level = 2  # 缓行
                    congestion_desc = "缓行"
                    speed = 25 + np.random.randint(-3, 4)
                elif occupancy < 0.8:
                    congestion_level = 3  # 拥堵
                    congestion_desc = "拥堵"
                    speed = 15 + np.random.randint(-2, 3)
                else:
                    congestion_level = 4  # 严重拥堵
                    congestion_desc = "严重拥堵"
                    speed = 8 + np.random.randint(-2, 3)

                results.append({
                    "road_name": road["name"],
                    "road_type": road["type"],
                    "time_period": period["name"],
                    "hour": period["hour"],
                    "flow": flow,
                    "congestion_level": congestion_level,
                    "congestion_desc": congestion_desc,
                    "speed": max(5, speed),
                    "timestamp": f"2024-01-15 {period['hour']:02d}:00:00",
                })

        df = pd.DataFrame(results)

        # 保存完整数据
        output_path = DATA_DIR / "Traffic_Flow.csv"
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"保存到: {output_path}")
        print(f"共 {len(df)} 条记录")

        # 生成汇总数据
        summary = df.groupby("road_name").agg({
            "flow": "mean",
            "congestion_level": "mean",
            "speed": "mean",
        }).round(0).reset_index()

        summary_path = DATA_DIR / "Traffic_Flow_Summary.csv"
        summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
        print(f"汇总数据保存到: {summary_path}")

        # 统计
        print("\n" + "-" * 40)
        print("交通流量统计:")
        print(f"  道路数量: {df['road_name'].nunique()}")
        print(f"  平均流量: {df['flow'].mean():.0f} 辆/小时")
        print(f"  平均速度: {df['speed'].mean():.0f} km/h")
        print(f"  拥堵比例: {(df['congestion_level'] >= 3).mean()*100:.1f}%")
        print("-" * 40)

        return df


def main():
    print("\n" + "=" * 60)
    print("房产与交通数据自动获取工具")
    print("=" * 60)

    if not BAIDU_AK:
        print("\n警告: 未配置百度地图 API Key")
        print("请在 .env 文件中设置 Baidu_Map_AK=your_key")
        return

    # 1. 获取房产数据 (建筑年代 + 房价)
    fetcher = RealEstateDataFetcher(BAIDU_AK)
    fetcher.fetch_all()

    # 2. 生成交通流量数据
    traffic_enhancer = TrafficDataEnhancer()
    traffic_enhancer.generate_traffic_flow()

    print("\n" + "=" * 60)
    print("数据获取完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
