import requests
import pandas as pd
import time
import math
import os

# ==========================================
# 1. 填入你的弹药
# ==========================================
AK = "W7iTpEM9P3wGO0kuft1fZhdM6YMB9ADr"  # <--- 必须填入真实 AK

# ==========================================
# 2. 动态获取沙盘的绝对物理中心 (WGS84)
# ==========================================
try:
    df_base = pd.read_excel("data/Changchun_Precise_Points.xlsx")
    CENTER_LAT = float(df_base['Lat'].mean())
    CENTER_LNG = float(df_base['Lng'].mean())
    print(f"成功锁定基准中心: 经度 {CENTER_LNG:.5f}, 纬度 {CENTER_LAT:.5f}")
except Exception as e:
    print("未找到底表数据，请确保 Changchun_Precise_Points.xlsx 存在！")
    exit()

RADIUS = 2000
QUERY = "餐饮$购物$生活服务"

# ==========================================
# 3. 核心大杀器：完整的双重解密数学模型
# ==========================================
x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626
a = 6378245.0
ee = 0.00669342162296594323


# 第一步：脱去百度外衣 (BD09 -> GCJ02)
def bd09_to_gcj02(bd_lon, bd_lat):
    x = bd_lon - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * x_pi)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * x_pi)
    gg_lng = z * math.cos(theta)
    gg_lat = z * math.sin(theta)
    return gg_lng, gg_lat


def transformlat(lng, lat):
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 * math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * pi) + 40.0 * math.sin(lat / 3.0 * pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * pi) + 320 * math.sin(lat * pi / 30.0)) * 2.0 / 3.0
    return ret


def transformlng(lng, lat):
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 * math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * pi) + 40.0 * math.sin(lng / 3.0 * pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * pi) + 300.0 * math.sin(lng / 30.0 * pi)) * 2.0 / 3.0
    return ret


# 第二步：脱去火星外衣 (GCJ02 -> WGS84)
def gcj02_to_wgs84(lng, lat):
    dlat = transformlat(lng - 105.0, lat - 35.0)
    dlng = transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return lng * 2 - mglng, lat * 2 - mglat


# 终极集成转换
def bd09_to_wgs84(bd_lon, bd_lat):
    lon, lat = bd09_to_gcj02(bd_lon, bd_lat)
    return gcj02_to_wgs84(lon, lat)


# ==========================================
# 4. 爬取数据 (强制声明输入坐标系 coord_type=1)
# ==========================================
print("开始连接百度地图 API...")
poi_list = []

for page_num in range(20):
    # 注意这里加入了 coord_type=1，告诉百度我们的中心点是无偏差的 WGS84！
    url = f"https://api.map.baidu.com/place/v2/search?query={QUERY}&location={CENTER_LAT},{CENTER_LNG}&radius={RADIUS}&output=json&ak={AK}&coord_type=1&page_size=20&page_num={page_num}"

    try:
        response = requests.get(url).json()
        if response.get("status") == 0:
            results = response.get("results", [])
            if not results:
                break

            for item in results:
                if "location" in item:
                    # 百度返回的数据默认是 BD09，用我们的双重模型强制洗回 WGS84
                    raw_lng = item["location"]["lng"]
                    raw_lat = item["location"]["lat"]
                    real_lng, real_lat = bd09_to_wgs84(raw_lng, raw_lat)

                    poi_list.append({
                        "Name": item.get("name"),
                        "Lat": real_lat,
                        "Lng": real_lng
                    })
        else:
            print(f"API 报错：{response.get('message')}")
            break
    except Exception as e:
        print(f"网络出错：{e}")
        break
    time.sleep(0.5)

# ==========================================
# 5. 保存完美坐标
# ==========================================
if len(poi_list) > 0:
    df = pd.DataFrame(poi_list)
    df.to_csv("data/Changchun_POI_Real.csv", index=False, encoding="utf-8-sig")
    print(f"抓取完成！共获得 {len(df)} 个完美对齐的 POI 数据。")
else:
    print("未抓取到数据。")