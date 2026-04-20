import os
import requests
import pandas as pd
import time
from dotenv import load_dotenv
from src.utils.geo_transform import bd09_to_wgs84

load_dotenv()

AK = os.getenv("Baidu_Map_AK")
if not AK:
    raise ValueError("请设置环境变量 Baidu_Map_AK，参考 .env.example 文件")

try:
    df_base = pd.read_excel("data/Changchun_Precise_Points.xlsx")
    CENTER_LAT = float(df_base['Lat'].mean())
    CENTER_LNG = float(df_base['Lng'].mean())
except Exception as e:
    print("❌ 未找到底表，使用默认坐标。")
    CENTER_LAT, CENTER_LNG = 43.902, 125.315

RADIUS = 2000
QUERY = "公交车站$地铁站$停车场"

print("🚀 开始扫描历史街区交通大动脉...")
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

if poi_list:
    df = pd.DataFrame(poi_list)
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/Changchun_Traffic_Real.csv", index=False, encoding="utf-8-sig")
    print(f"🎉 抓取完成！共捕获 {len(df)} 个无偏差交通枢纽节点！已保存为 Changchun_Traffic_Real.csv")
else:
    print("未抓取到数据。")

