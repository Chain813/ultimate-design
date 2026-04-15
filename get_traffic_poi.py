import requests
import pandas as pd
import time
import math
import os

# ==========================================
# 1. 填入你的弹药
# ==========================================
AK = "W7iTpEM9P3wGO0kuft1fZhdM6YMB9ADr"  # <--- 填入你的真实 AK

# 读取基准中心 (WGS84)
try:
    df_base = pd.read_excel("data/Changchun_Precise_Points.xlsx")
    CENTER_LAT = float(df_base['Lat'].mean())
    CENTER_LNG = float(df_base['Lng'].mean())
except Exception as e:
    print("❌ 未找到底表，使用默认坐标。")
    CENTER_LAT, CENTER_LNG = 43.902, 125.315

RADIUS = 2000
# 🌟 核心修改：这次我们的猎物是交通大动脉！
QUERY = "公交车站$地铁站$停车场"  

# ==========================================
# 2. 坐标双向解密引擎 (BD09 -> GCJ02 -> WGS84)
# ==========================================
x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626
a = 6378245.0
ee = 0.00669342162296594323

def bd09_to_gcj02(bd_lon, bd_lat):
    x = bd_lon - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * x_pi)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * x_pi)
    return z * math.cos(theta), z * math.sin(theta)

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

def bd09_to_wgs84(bd_lon, bd_lat):
    lon, lat = bd09_to_gcj02(bd_lon, bd_lat)
    return gcj02_to_wgs84(lon, lat)

# ==========================================
# 3. 执行交通枢纽抓取
# ==========================================
print("🚀 开始扫描历史街区交通大动脉...")
poi_list = []

for page_num in range(20): 
    url = f"https://api.map.baidu.com/place/v2/search?query={QUERY}&location={CENTER_LAT},{CENTER_LNG}&radius={RADIUS}&output=json&ak={AK}&coord_type=1&page_size=20&page_num={page_num}"
    
    try:
        response = requests.get(url).json()
        if response.get("status") == 0:
            results = response.get("results", [])
            if not results: break
            
            for item in results:
                if "location" in item:
                    raw_lng, raw_lat = item["location"]["lng"], item["location"]["lat"]
                    real_lng, real_lat = bd09_to_wgs84(raw_lng, raw_lat)
                    poi_list.append({
                        "Name": item.get("name"),
                        "Type": item.get("detail_info", {}).get("tag", "交通设施"),
                        "Lat": real_lat,
                        "Lng": real_lng
                    })
        else:
            print(f"⚠️ API 报错：{response.get('message')}")
            break
    except Exception as e:
        print(f"❌ 网络出错：{e}")
        break
    time.sleep(0.5)

# ==========================================
# 4. 导出战利品
# ==========================================
if poi_list:
    df = pd.DataFrame(poi_list)
    # 🌟 另存为一个新的专门的交通文件
    df.to_csv("data/Changchun_Traffic_Real.csv", index=False, encoding="utf-8-sig")
    print(f"🎉 抓取完成！共捕获 {len(df)} 个无偏差交通枢纽节点！已保存为 Changchun_Traffic_Real.csv")
else:
    print("未抓取到数据。")