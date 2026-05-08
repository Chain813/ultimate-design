"""补充数据获取脚本 - 建筑年代、交通流量、房价地价、历史影像、日照数据。

使用方法:
    python scripts/fetch_supplementary_data.py --all          # 获取所有数据
    python scripts/fetch_supplementary_data.py --building     # 仅建筑年代
    python scripts/fetch_supplementary_data.py --traffic      # 仅交通流量
    python scripts/fetch_supplementary_data.py --price        # 仅房价地价
    python scripts/fetch_supplementary_data.py --sunshine     # 仅日照数据
"""

import argparse
import json
import math
import os
import re
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
SHP_DIR = DATA_DIR / "shp"

# ============================================================
# 配置
# ============================================================

# 百度地图 API Key (从 .env 读取)
def load_api_key():
    """加载百度地图 API Key"""
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("Baidu_Map_AK"):
                    return line.strip().split("=", 1)[1].strip()
    return os.getenv("Baidu_Map_AK", "")

BAIDU_AK = load_api_key()

# 研究范围边界 (从 GeoJSON 读取)
def load_boundary():
    """加载研究范围边界"""
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
    # 默认长春宽城区范围
    return {
        "min_lng": 125.33,
        "max_lng": 125.35,
        "min_lat": 43.89,
        "max_lat": 43.91,
        "center_lng": 125.34,
        "center_lat": 43.90,
    }

BOUNDARY = load_boundary()

# 研究区域内的主要小区/建筑 (示例数据)
COMMUNITIES = [
    {"name": "伪满皇宫博物院", "address": "长春市宽城区光复北路5号", "type": "历史建筑"},
    {"name": "长春站", "address": "长春市宽城区长白路5号", "type": "交通枢纽"},
    {"name": "胜利公园", "address": "长春市宽城区人民大街9518号", "type": "公园"},
    {"name": "中车长春轨道客车", "address": "长春市宽城区青荫路435号", "type": "工业遗存"},
    {"name": "新发小区", "address": "长春市宽城区新发路", "type": "居住区"},
    {"name": "光复小区", "address": "长春市宽城区光复路", "type": "居住区"},
    {"name": "站前小区", "address": "长春市宽城区站前广场", "type": "居住区"},
    {"name": "铁北小区", "address": "长春市宽城区铁北一路", "type": "居住区"},
    {"name": "天光路小区", "address": "长春市宽城区天光路", "type": "居住区"},
    {"name": "杭州路小区", "address": "长春市宽城区杭州路", "type": "居住区"},
    # 可以根据实际情况添加更多
]

# 主要道路
ROADS = [
    "人民大街", "新发路", "光复路", "长白路", "亚泰大街",
    "北京大街", "上海路", "杭州路", "南京大街", "天津路",
    "铁北一路", "铁北二路", "凯旋路", "北人民大街", "台北大街",
]


# ============================================================
# 1. 建筑年代数据获取
# ============================================================

class BuildingYearFetcher:
    """建筑年代数据获取器"""

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    def fetch_from_baidu_baike(self, keyword):
        """从百度百科获取建筑/小区信息"""
        try:
            url = f"https://baike.baidu.com/item/{keyword}"
            resp = requests.get(url, headers=self.headers, timeout=10)
            resp.encoding = "utf-8"

            # 查找建成年代
            patterns = [
                r"建成时间[：:]\s*(\d{4})",
                r"(\d{4})年建成",
                r"竣工时间[：:]\s*(\d{4})",
                r"建成于(\d{4})年",
                r"始建于(\d{4})年",
                r"创建于(\d{4})年",
                r"建于(\d{4})年",
            ]

            for pattern in patterns:
                match = re.search(pattern, resp.text)
                if match:
                    return int(match.group(1))

            return None
        except Exception as e:
            print(f"  获取 {keyword} 失败: {e}")
            return None

    def fetch_from_geocoding(self, address):
        """通过地理编码获取建筑信息"""
        if not self.api_key:
            return None

        try:
            url = "https://api.map.baidu.com/geocoding/v3/"
            params = {
                "address": address,
                "city": "长春",
                "output": "json",
                "ak": self.api_key,
            }
            resp = requests.get(url, params=params, timeout=10).json()

            if resp.get("status") == 0:
                result = resp.get("result", {})
                return {
                    "lng": result.get("location", {}).get("lng"),
                    "lat": result.get("location", {}).get("lat"),
                    "formatted_address": result.get("formatted_address"),
                }
            return None
        except Exception as e:
            print(f"  地理编码失败 {address}: {e}")
            return None

    def fetch_all(self):
        """获取所有建筑年代数据"""
        print("\n" + "=" * 60)
        print("获取建筑年代数据")
        print("=" * 60)

        results = []

        for community in COMMUNITIES:
            print(f"\n处理: {community['name']}")

            # 获取建成年代
            year = self.fetch_from_baidu_baike(community["name"])
            print(f"  建成年代: {year if year else '未找到'}")

            # 获取坐标
            geo = self.fetch_from_geocoding(community["address"])

            results.append({
                "name": community["name"],
                "address": community["address"],
                "type": community["type"],
                "build_year": year,
                "lng": geo.get("lng") if geo else None,
                "lat": geo.get("lat") if geo else None,
            })

            time.sleep(1)  # 控制请求频率

        # 保存结果
        df = pd.DataFrame(results)
        output_path = DATA_DIR / "Building_Years.csv"
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n保存到: {output_path}")
        print(f"共获取 {len(results)} 条记录")

        return df


# ============================================================
# 2. 交通流量数据获取
# ============================================================

class TrafficFlowFetcher:
    """交通流量数据获取器 (基于百度地图实时路况)"""

    def __init__(self, api_key):
        self.api_key = api_key

    def get_road_status(self, road_name):
        """获取道路实时路况"""
        if not self.api_key:
            return None

        try:
            # 获取路况
            url = "https://api.map.baidu.com/traffic/v1/road"
            params = {
                "road_name": road_name,
                "city": "长春",
                "ak": self.api_key,
                "output": "json",
            }
            resp = requests.get(url, params=params, timeout=10).json()

            if resp.get("status") == 0:
                road_traffic = resp.get("road_traffic", [{}])[0] if resp.get("road_traffic") else {}

                # 状态映射
                status_map = {
                    0: "未知",
                    1: "畅通",
                    2: "缓行",
                    3: "拥堵",
                    4: "严重拥堵",
                }

                congestion_level = road_traffic.get("status", 0)

                return {
                    "road_name": road_name,
                    "congestion_level": congestion_level,
                    "congestion_desc": status_map.get(congestion_level, "未知"),
                    "speed": road_traffic.get("speed", 0),
                    "timestamp": datetime.now().isoformat(),
                }
            return None
        except Exception as e:
            print(f"  获取路况失败 {road_name}: {e}")
            return None

    def get_traffic_flow_by_location(self, lng, lat):
        """获取指定位置的交通流量"""
        if not self.api_key:
            return None

        try:
            url = "https://api.map.baidu.com/traffic/v1/around"
            params = {
                "location": f"{lat},{lng}",
                "radius": 500,
                "ak": self.api_key,
                "output": "json",
            }
            resp = requests.get(url, params=params, timeout=10).json()

            if resp.get("status") == 0:
                return resp.get("traffic_info", [])
            return None
        except Exception as e:
            print(f"  获取流量失败: {e}")
            return None

    def fetch_all_roads(self):
        """获取所有道路的路况"""
        print("\n" + "=" * 60)
        print("获取交通流量数据")
        print("=" * 60)

        results = []

        for road in ROADS:
            print(f"\n处理: {road}")
            status = self.get_road_status(road)

            if status:
                print(f"  拥堵等级: {status['congestion_desc']}")
                results.append(status)
            else:
                results.append({
                    "road_name": road,
                    "congestion_level": -1,
                    "congestion_desc": "获取失败",
                    "speed": 0,
                    "timestamp": datetime.now().isoformat(),
                })

            time.sleep(0.5)

        # 保存结果
        df = pd.DataFrame(results)
        output_path = DATA_DIR / "Traffic_Flow.csv"
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n保存到: {output_path}")
        print(f"共获取 {len(results)} 条记录")

        return df

    def fetch_multi_time_points(self, intervals=6):
        """获取多个时间点的路况数据 (用于分析交通规律)"""
        print("\n" + "=" * 60)
        print("获取多时间点交通数据")
        print("=" * 60)

        all_results = []
        interval_hours = 24 // intervals

        for i in range(intervals):
            hour = i * interval_hours
            print(f"\n时间点: {hour:02d}:00")

            for road in ROADS[:5]:  # 只取前5条道路示例
                status = self.get_road_status(road)
                if status:
                    status["hour"] = hour
                    all_results.append(status)
                time.sleep(0.3)

        df = pd.DataFrame(all_results)
        output_path = DATA_DIR / "Traffic_Flow_Timeline.csv"
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n保存到: {output_path}")

        return df


# ============================================================
# 3. 房价地价数据获取
# ============================================================

class PriceDataFetcher:
    """房价地价数据获取器"""

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    def fetch_from_baidu_poi(self):
        """从百度地图 POI 获取房产信息"""
        if not self.api_key:
            return []

        results = []
        url = "https://api.map.baidu.com/place/v2/search"

        # 搜索小区
        params = {
            "query": "小区",
            "bounds": f"{BOUNDARY['min_lat']},{BOUNDARY['min_lng']},{BOUNDARY['max_lat']},{BOUNDARY['max_lng']}",
            "output": "json",
            "ak": self.api_key,
            "page_size": 20,
            "page_num": 0,
        }

        try:
            resp = requests.get(url, params=params, timeout=10).json()

            if resp.get("status") == 0:
                for poi in resp.get("results", []):
                    results.append({
                        "name": poi.get("name"),
                        "address": poi.get("address"),
                        "lng": poi.get("location", {}).get("lng"),
                        "lat": poi.get("location", {}).get("lat"),
                    })
        except Exception as e:
            print(f"  POI 搜索失败: {e}")

        return results

    def estimate_price_by_location(self, lng, lat):
        """根据位置估算房价 (基于区位因素)"""
        # 简化模型：根据到市中心距离、交通便利度等估算
        center_lng = BOUNDARY["center_lng"]
        center_lat = BOUNDARY["center_lat"]

        # 计算到中心距离 (km)
        distance = math.sqrt(
            ((lng - center_lng) * 80) ** 2 +  # 经度转换
            ((lat - center_lat) * 111) ** 2    # 纬度转换
        )

        # 基础价格 (长春宽城区均价约 6000-8000 元/㎡)
        base_price = 7000

        # 距离衰减
        distance_factor = max(0.7, 1 - distance * 0.1)

        # 添加随机波动 (±10%)
        noise = np.random.uniform(0.9, 1.1)

        return int(base_price * distance_factor * noise)

    def fetch_all(self):
        """获取房价数据"""
        print("\n" + "=" * 60)
        print("获取房价数据")
        print("=" * 60)

        # 方式1: 从 POI 获取小区列表
        print("\n搜索研究区域内的小区...")
        communities = self.fetch_from_baidu_poi()
        print(f"找到 {len(communities)} 个小区")

        results = []

        for comm in communities:
            # 估算房价 (实际应从贝壳/链家获取)
            price = self.estimate_price_by_location(comm["lng"], comm["lat"])

            results.append({
                "name": comm["name"],
                "address": comm.get("address", ""),
                "lng": comm["lng"],
                "lat": comm["lat"],
                "price_per_sqm": price,
                "source": "estimated",
            })

        # 方式2: 添加预设的基准地价数据
        land_prices = [
            {"zone": "一级地", "description": "人民大街沿线", "base_price": 4500},
            {"zone": "二级地", "description": "主要商圈周边", "base_price": 3500},
            {"zone": "三级地", "description": "一般居住区", "base_price": 2500},
            {"zone": "四级地", "description": "城市边缘", "base_price": 1500},
        ]

        # 保存房价数据
        df = pd.DataFrame(results)
        output_path = DATA_DIR / "House_Prices.csv"
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n房价数据保存到: {output_path}")

        # 保存基准地价
        df_land = pd.DataFrame(land_prices)
        land_output_path = DATA_DIR / "Land_Prices.csv"
        df_land.to_csv(land_output_path, index=False, encoding="utf-8-sig")
        print(f"基准地价保存到: {land_output_path}")

        return df, df_land


# ============================================================
# 4. 历史影像获取说明
# ============================================================

class HistoricalImageFetcher:
    """历史影像获取指导"""

    def print_guide(self):
        """打印历史影像获取指南"""
        print("\n" + "=" * 60)
        print("历史影像获取指南")
        print("=" * 60)

        guide = """
历史影像无法通过 API 直接获取，需要使用以下工具手动下载：

1. Google Earth Pro (推荐)
   - 下载地址: https://www.google.com/earth/versions/
   - 操作步骤:
     a) 安装并打开 Google Earth Pro
     b) 搜索 "长春市宽城区"
     c) 点击工具栏的时钟图标 (历史影像)
     d) 选择不同年份: 2000, 2005, 2010, 2015, 2020, 2024
     e) 文件 → 保存 → 保存图像
     f) 保存为 JPG/PNG 格式

2. 91卫图助手 (国产工具)
   - 下载地址: https://www.91weitu.com/
   - 支持下载多时相卫星影像
   - 可直接导出 GeoTIFF 格式

3. 天地图历史影像
   - 访问: https://www.tianditu.gov.cn/
   - 部分区域提供历史影像服务

4. Landsat 遥感影像 (免费，分辨率30m)
   - 访问: https://earthexplorer.usgs.gov/
   - 可下载 1972 年至今的影像
   - 适合大范围城市演变分析

建议获取的年份:
   - 2000年: 城市扩张前
   - 2005年: 快速发展期
   - 2010年: 世博会前后
   - 2015年: 近期基准
   - 2020年: 现状参考
   - 2024年: 最新影像

保存位置: data/historical_images/
        """

        print(guide)

        # 创建保存目录
        img_dir = DATA_DIR / "historical_images"
        img_dir.mkdir(exist_ok=True)
        print(f"\n已创建保存目录: {img_dir}")

        # 生成下载记录模板
        template = [
            {"year": 2000, "source": "Google Earth", "filename": "2000_satellite.jpg", "downloaded": False},
            {"year": 2005, "source": "Google Earth", "filename": "2005_satellite.jpg", "downloaded": False},
            {"year": 2010, "source": "Google Earth", "filename": "2010_satellite.jpg", "downloaded": False},
            {"year": 2015, "source": "Google Earth", "filename": "2015_satellite.jpg", "downloaded": False},
            {"year": 2020, "source": "Google Earth", "filename": "2020_satellite.jpg", "downloaded": False},
            {"year": 2024, "source": "Google Earth", "filename": "2024_satellite.jpg", "downloaded": False},
        ]

        df = pd.DataFrame(template)
        template_path = img_dir / "download_template.csv"
        df.to_csv(template_path, index=False, encoding="utf-8-sig")
        print(f"下载记录模板: {template_path}")

        return guide


# ============================================================
# 5. 日照数据获取与模拟
# ============================================================

class SunshineDataFetcher:
    """日照数据获取与模拟"""

    def __init__(self, lat=43.89, lon=125.34):
        self.lat = lat
        self.lon = lon
        self.timezone = "Asia/Shanghai"

    def calculate_sun_position(self, month, day, hour):
        """计算太阳位置 (简化算法)"""
        # 儒略日
        if month <= 2:
            year = 2024
            month += 12
        else:
            year = 2024

        A = int(year / 100)
        B = 2 - A + int(A / 4)
        JD = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5

        # 儒略世纪数
        T = (JD - 2451545.0) / 36525.0

        # 太阳平黄经
        L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
        L0 = L0 % 360

        # 太阳平近点角
        M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T
        M = math.radians(M % 360)

        # 太阳中心方程
        C = (1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M)
        C += (0.019993 - 0.000101 * T) * math.sin(2 * M)
        C += 0.000289 * math.sin(3 * M)

        # 太阳真黄经
        theta = L0 + C

        # 太阳倾角
        epsilon = 23.439 - 0.00000036 * T
        epsilon = math.radians(epsilon)

        # 太阳赤纬
        theta_rad = math.radians(theta)
        declination = math.asin(math.sin(epsilon) * math.sin(theta_rad))

        # 时角
        # 真太阳时
        B_angle = math.radians(360 * (day - 81) / 365)
        EoT = 9.87 * math.sin(2 * B_angle) - 7.53 * math.cos(B_angle) - 1.5 * math.sin(B_angle)

        # 标准时间转真太阳时
        longitude_correction = (self.lon - 120) * 4  # 长春在东经125度
        solar_time = hour + EoT / 60 + longitude_correction / 60

        # 时角 (度)
        hour_angle = (solar_time - 12) * 15

        # 太阳高度角
        lat_rad = math.radians(self.lat)
        hour_angle_rad = math.radians(hour_angle)

        altitude = math.asin(
            math.sin(lat_rad) * math.sin(declination) +
            math.cos(lat_rad) * math.cos(declination) * math.cos(hour_angle_rad)
        )

        # 太阳方位角
        azimuth = math.atan2(
            -math.cos(declination) * math.sin(hour_angle_rad),
            math.sin(declination) * math.cos(lat_rad) -
            math.cos(declination) * math.sin(lat_rad) * math.cos(hour_angle_rad)
        )

        return {
            "altitude": math.degrees(altitude),
            "azimuth": (math.degrees(azimuth) + 360) % 360,
            "declination": math.degrees(declination),
            "is_daylight": math.degrees(altitude) > 0,
        }

    def calculate_daily_sunshine(self, month, day):
        """计算一天的日照情况"""
        results = []

        for hour in range(6, 19):  # 6:00 - 18:00
            for minute in [0, 30]:
                time_hour = hour + minute / 60
                sun = self.calculate_sun_position(month, day, time_hour)

                results.append({
                    "time": f"{hour:02d}:{minute:02d}",
                    "hour": time_hour,
                    "altitude": round(sun["altitude"], 2),
                    "azimuth": round(sun["azimuth"], 2),
                    "is_daylight": sun["is_daylight"],
                })

        return pd.DataFrame(results)

    def calculate_annual_sunshine(self):
        """计算全年日照统计"""
        print("\n计算全年日照统计...")

        monthly_stats = []

        for month in range(1, 13):
            # 每月15日作为代表
            day = 15
            daily = self.calculate_daily_sunshine(month, day)

            # 计算日照小时数
            sunshine_hours = len(daily[daily["is_daylight"]]) * 0.5

            # 最高太阳高度角
            max_altitude = daily["altitude"].max()

            monthly_stats.append({
                "month": month,
                "sunshine_hours": sunshine_hours,
                "max_altitude": round(max_altitude, 2),
                "sunrise_hour": daily[daily["is_daylight"]]["hour"].min() if len(daily[daily["is_daylight"]]) > 0 else None,
                "sunset_hour": daily[daily["is_daylight"]]["hour"].max() if len(daily[daily["is_daylight"]]) > 0 else None,
            })

        return pd.DataFrame(monthly_stats)

    def calculate_building_shadow(self, building_height, building_distance, month=12, day=21, hour=12):
        """计算建筑阴影"""
        sun = self.calculate_sun_position(month, day, hour)

        if not sun["is_daylight"]:
            return {
                "shadow_length": float("inf"),
                "meets_standard": False,
                "note": "无日照",
            }

        altitude_rad = math.radians(sun["altitude"])

        # 阴影长度
        if sun["altitude"] > 0:
            shadow_length = building_height / math.tan(altitude_rad)
        else:
            shadow_length = float("inf")

        # 判断是否满足日照标准 (冬至日满窗日照≥2小时)
        # 简化判断：阴影长度是否小于建筑间距
        meets_standard = shadow_length <= building_distance

        # 建议间距
        if not meets_standard:
            suggested_distance = shadow_length * 1.1  # 增加10%余量
        else:
            suggested_distance = building_distance

        return {
            "sun_altitude": sun["altitude"],
            "sun_azimuth": sun["azimuth"],
            "shadow_length": round(shadow_length, 2),
            "building_height": building_height,
            "building_distance": building_distance,
            "meets_standard": meets_standard,
            "suggested_distance": round(suggested_distance, 2),
        }

    def fetch_all(self):
        """获取所有日照数据"""
        print("\n" + "=" * 60)
        print("获取日照数据")
        print("=" * 60)
        print(f"位置: 纬度 {self.lat}°N, 经度 {self.lon}°E")

        # 1. 全年日照统计
        print("\n1. 计算全年日照统计...")
        annual = self.calculate_annual_sunshine()
        annual_path = DATA_DIR / "Sunshine_Annual.csv"
        annual.to_csv(annual_path, index=False, encoding="utf-8-sig")
        print(f"   保存到: {annual_path}")

        # 2. 冬至日日照分析 (最不利条件)
        print("\n2. 计算冬至日日照分析...")
        winter_solstice = self.calculate_daily_sunshine(12, 21)
        winter_path = DATA_DIR / "Sunshine_Winter_Solstice.csv"
        winter_solstice.to_csv(winter_path, index=False, encoding="utf-8-sig")
        print(f"   保存到: {winter_path}")

        # 3. 夏至日日照分析
        print("\n3. 计算夏至日日照分析...")
        summer_solstice = self.calculate_daily_sunshine(6, 21)
        summer_path = DATA_DIR / "Sunshine_Summer_Solstice.csv"
        summer_solstice.to_csv(summer_path, index=False, encoding="utf-8-sig")
        print(f"   保存到: {summer_path}")

        # 4. 建筑日照校验示例
        print("\n4. 建筑日照校验示例...")
        building_cases = [
            {"height": 12, "distance": 15, "name": "4层住宅"},
            {"height": 18, "distance": 20, "name": "6层住宅"},
            {"height": 27, "distance": 25, "name": "9层住宅"},
            {"height": 36, "distance": 30, "name": "12层住宅"},
            {"height": 54, "distance": 40, "name": "18层住宅"},
        ]

        shadow_results = []
        for case in building_cases:
            shadow = self.calculate_building_shadow(case["height"], case["distance"])
            shadow["building_name"] = case["name"]
            shadow_results.append(shadow)
            print(f"   {case['name']}: {'满足' if shadow['meets_standard'] else '不满足'}日照标准")

        shadow_df = pd.DataFrame(shadow_results)
        shadow_path = DATA_DIR / "Sunshine_Building_Shadow.csv"
        shadow_df.to_csv(shadow_path, index=False, encoding="utf-8-sig")
        print(f"   保存到: {shadow_path}")

        # 5. 输出关键信息
        print("\n" + "-" * 40)
        print("关键日照参数:")
        print(f"  冬至日最高太阳高度角: {winter_solstice['altitude'].max():.1f}°")
        print(f"  夏至日最高太阳高度角: {summer_solstice['altitude'].max():.1f}°")
        print(f"  年日照时数 (估算): {annual['sunshine_hours'].sum():.0f} 小时")
        print("-" * 40)

        return {
            "annual": annual,
            "winter_solstice": winter_solstice,
            "summer_solstice": summer_solstice,
            "shadow": shadow_df,
        }


# ============================================================
# 数据整合
# ============================================================

# ============================================================
# 6. OSMnx 开源数据获取 (GitHub 集成)
# ============================================================

class OSMnxDataFetcher:
    """使用 OSMnx 从 OpenStreetMap 获取完整数据"""

    def __init__(self):
        self.available = False
        try:
            import osmnx as ox
            self.ox = ox
            # 检查 API 版本
            if hasattr(ox, 'features_from_place'):
                self.use_features = True
            elif hasattr(ox, 'geometries_from_place'):
                self.use_features = False
            else:
                self.use_features = None
            self.available = True
        except ImportError:
            print("警告: 未安装 osmnx，请运行: pip install osmnx")

    def _get_features(self, place, tags):
        """兼容新旧版本的 API"""
        if self.use_features is None:
            raise Exception("OSMnx 版本不支持 features/geometries API")
        elif self.use_features:
            return self.ox.features_from_place(place, tags=tags)
        else:
            return self.ox.geometries_from_place(place, tags=tags)

    def fetch_buildings(self, place="宽城区, 长春市, 吉林省, 中国"):
        """获取建筑轮廓"""
        if not self.available:
            return None

        print(f"\n获取建筑数据: {place}")
        try:
            buildings = self._get_features(place, tags={"building": True})
            output_path = SHP_DIR / "Building_Footprints_OSM.geojson"
            buildings.to_file(str(output_path), driver="GeoJSON")
            print(f"保存到: {output_path}")
            print(f"共 {len(buildings)} 个建筑")
            return buildings
        except Exception as e:
            print(f"获取失败: {e}")
            return None

    def fetch_road_network(self, place="宽城区, 长春市, 吉林省, 中国"):
        """获取道路网络"""
        if not self.available:
            return None

        print(f"\n获取道路网络: {place}")
        try:
            G = self.ox.graph_from_place(place, network_type="drive")
            edges = self.ox.graph_to_gdfs(G, nodes=False)
            output_path = SHP_DIR / "Road_Network.geojson"
            edges.to_file(str(output_path), driver="GeoJSON")
            print(f"保存到: {output_path}")
            print(f"共 {len(edges)} 条路段")
            return edges
        except Exception as e:
            print(f"获取失败: {e}")
            return None

    def fetch_pois(self, place="宽城区, 长春市, 吉林省, 中国"):
        """获取 POI 数据"""
        if not self.available:
            return None

        print(f"\n获取 POI 数据: {place}")
        try:
            tags = {
                "amenity": True,    # 餐饮、医疗、教育等
                "shop": True,       # 商店
                "tourism": True,    # 旅游景点
                "leisure": True,    # 休闲设施
            }
            pois = self._get_features(place, tags=tags)

            # 转换为点数据
            pois_points = pois[pois.geometry.type.isin(["Point"])].copy()
            pois_points["lng"] = pois_points.geometry.x
            pois_points["lat"] = pois_points.geometry.y

            # 选择关键字段
            cols = ["name", "amenity", "shop", "tourism", "leisure", "lng", "lat"]
            available_cols = [c for c in cols if c in pois_points.columns]
            result = pois_points[available_cols].copy()

            output_path = DATA_DIR / "POI_OSM.csv"
            result.to_csv(str(output_path), index=False, encoding="utf-8-sig")
            print(f"保存到: {output_path}")
            print(f"共 {len(result)} 个 POI")
            return result
        except Exception as e:
            print(f"获取失败: {e}")
            return None

    def fetch_green_spaces(self, place="宽城区, 长春市, 吉林省, 中国"):
        """获取绿地数据"""
        if not self.available:
            return None

        print(f"\n获取绿地数据: {place}")
        try:
            tags = {
                "leisure": ["park", "garden", "playground"],
                "landuse": ["grass", "forest", "recreation_ground"],
                "natural": ["wood", "tree_row"],
            }
            green = self._get_features(place, tags=tags)
            output_path = SHP_DIR / "Green_Spaces.geojson"
            green.to_file(str(output_path), driver="GeoJSON")
            print(f"保存到: {output_path}")
            print(f"共 {len(green)} 个绿地")
            return green
        except Exception as e:
            print(f"获取失败: {e}")
            return None

    def fetch_all(self, place="宽城区, 长春市, 吉林省, 中国"):
        """获取所有 OSM 数据"""
        print("\n" + "=" * 60)
        print("使用 OSMnx 获取 OpenStreetMap 数据")
        print("=" * 60)

        if not self.available:
            print("\n请先安装 osmnx: pip install osmnx")
            return

        results = {}
        results["buildings"] = self.fetch_buildings(place)
        results["roads"] = self.fetch_road_network(place)
        results["pois"] = self.fetch_pois(place)
        results["green"] = self.fetch_green_spaces(place)

        return results


def integrate_data():
    """整合所有补充数据到地块诊断"""
    print("\n" + "=" * 60)
    print("数据整合")
    print("=" * 60)

    # 读取各类数据
    files = {
        "building_years": DATA_DIR / "Building_Years.csv",
        "house_prices": DATA_DIR / "House_Prices.csv",
        "traffic_flow": DATA_DIR / "Traffic_Flow.csv",
    }

    data = {}
    for name, path in files.items():
        if path.exists():
            data[name] = pd.read_csv(path, encoding="utf-8-sig")
            print(f"加载 {name}: {len(data[name])} 条记录")
        else:
            print(f"文件不存在: {path}")

    # 读取现有地块数据
    plots_path = SHP_DIR / "Key_Plots_District.json"
    if plots_path.exists():
        with open(plots_path, "r", encoding="utf-8") as f:
            plots_data = json.load(f)
        print(f"加载地块数据: {len(plots_data.get('features', []))} 个地块")

    # 生成整合报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "data_sources": list(data.keys()),
        "record_counts": {k: len(v) for k, v in data.items()},
    }

    report_path = DATA_DIR / "supplementary_data_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n整合报告保存到: {report_path}")

    return data


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="补充数据获取脚本")
    parser.add_argument("--all", action="store_true", help="获取所有数据")
    parser.add_argument("--building", action="store_true", help="获取建筑年代数据")
    parser.add_argument("--traffic", action="store_true", help="获取交通流量数据")
    parser.add_argument("--price", action="store_true", help="获取房价地价数据")
    parser.add_argument("--history", action="store_true", help="显示历史影像获取指南")
    parser.add_argument("--sunshine", action="store_true", help="获取日照数据")
    parser.add_argument("--osm", action="store_true", help="使用 OSMnx 获取 OpenStreetMap 数据")
    parser.add_argument("--integrate", action="store_true", help="整合所有数据")

    args = parser.parse_args()

    # 如果没有指定参数，显示帮助
    if not any(vars(args).values()):
        parser.print_help()
        return

    print("\n" + "=" * 60)
    print("UltimateDESIGN 补充数据获取工具")
    print("=" * 60)
    print("研究范围: 长春市宽城区")
    print(f"边界: {BOUNDARY['min_lng']:.4f}°E - {BOUNDARY['max_lng']:.4f}°E")
    print(f"       {BOUNDARY['min_lat']:.4f}°N - {BOUNDARY['max_lat']:.4f}°N")

    if not BAIDU_AK:
        print("\n警告: 未配置百度地图 API Key，部分功能将无法使用")
        print("请在 .env 文件中设置 Baidu_Map_AK=your_key")

    # 执行数据获取
    if args.all or args.building:
        fetcher = BuildingYearFetcher(BAIDU_AK)
        fetcher.fetch_all()

    if args.all or args.traffic:
        fetcher = TrafficFlowFetcher(BAIDU_AK)
        fetcher.fetch_all_roads()

    if args.all or args.price:
        fetcher = PriceDataFetcher(BAIDU_AK)
        fetcher.fetch_all()

    if args.all or args.history:
        fetcher = HistoricalImageFetcher()
        fetcher.print_guide()

    if args.all or args.sunshine:
        fetcher = SunshineDataFetcher()
        fetcher.fetch_all()

    if args.all or args.osm:
        fetcher = OSMnxDataFetcher()
        fetcher.fetch_all()

    if args.all or args.integrate:
        integrate_data()

    print("\n" + "=" * 60)
    print("数据获取完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
