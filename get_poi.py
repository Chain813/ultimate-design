import os
import requests
import pandas as pd
import time
from pathlib import Path
from dotenv import load_dotenv
from utils.geo_transform import bd09_to_wgs84

load_dotenv()

AK = os.getenv("Baidu_Map_AK")
if not AK:
    raise ValueError("请设置环境变量 Baidu_Map_AK，参考 .env.example 文件")

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

print("开始连接百度地图 API...")
poi_list = []

for page_num in range(20):
    url = f"https://api.map.baidu.com/place/v2/search?query={QUERY}&location={CENTER_LAT},{CENTER_LNG}&radius={RADIUS}&output=json&ak={AK}&coord_type=1&page_size=20&page_num={page_num}"

    try:
        response = requests.get(url).json()
        if response.get("status") == 0:
            results = response.get("results", [])
            if not results:
                break

            for item in results:
                if "location" in item:
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

if len(poi_list) > 0:
    df = pd.DataFrame(poi_list)
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/Changchun_POI_Real.csv", index=False, encoding="utf-8-sig")
    print(f"抓取完成！共获得 {len(df)} 个完美对齐的 POI 数据。")
else:
    print("未抓取到数据。")
