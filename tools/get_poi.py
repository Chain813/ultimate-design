import os
import requests
import pandas as pd
import time
from pathlib import Path
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
    print(f"成功锁定基准中心: 经度 {CENTER_LNG:.5f}, 纬度 {CENTER_LAT:.5f}")
except Exception as e:
    print("未找到底表数据，请确保 Changchun_Precise_Points.xlsx 存在！")
    exit()

RADIUS = 3000  # 扩大半径至 3km 以完全覆盖研究范围及周边 1km
# 扩充更全面的城市更新相关分类
QUERY = "餐饮$购物$生活服务$医疗$教育培训$交通设施$金融$房地产$酒店$休闲娱乐$旅游景点$政府机构$文化传媒"

print(f"开始连接百度地图 API，检索范围半径: {RADIUS}m...")
poi_list = []
seen_uids = set()

import sys

# 多类别分批抓取以突破单次 400 条限制 (如果 API 支持多 query)
# 实际上百度 API 一次 query 最多返回 400 条。为了更全，可以循环 query
queries = QUERY.split("$")

for q in queries:
    print(f"正在抓取分类: {q}...")
    for page_num in range(20):
        url = f"https://api.map.baidu.com/place/v2/search?query={q}&location={CENTER_LAT},{CENTER_LNG}&radius={RADIUS}&output=json&ak={AK}&coord_type=1&page_size=20&page_num={page_num}"
        
        try:
            response = requests.get(url, timeout=10).json()
            if response.get("status") == 0:
                results = response.get("results", [])
                if not results:
                    break
                
                for item in results:
                    uid = item.get("uid")
                    if uid not in seen_uids:
                        seen_uids.add(uid)
                        if "location" in item:
                            raw_lng = item["location"]["lng"]
                            raw_lat = item["location"]["lat"]
                            real_lng, real_lat = bd09_to_wgs84(raw_lng, raw_lat)

                            poi_list.append({
                                "Name": item.get("name"),
                                "Type": q,
                                "Lat": real_lat,
                                "Lng": real_lng,
                                "Address": item.get("address", "")
                            })
            elif response.get("status") in [302, 240, 210, 211]:
                print(f"Error: API 配额不足或未开放对应权限 (状态码: {response.get('status')})。中断提取。")
                sys.exit(1)
            else:
                print(f"Warning: API 报错 ({response.get('status')}): {response.get('message')}")
                break
        except Exception as e:
            print(f"Error: 网络出错：{e}")
            sys.exit(1)
        time.sleep(0.2) # 适当加速

if len(poi_list) > 0:
    df = pd.DataFrame(poi_list)
    os.makedirs("data", exist_ok=True)
    # 保存为系统标准 POI 文件
    df.to_csv("data/Changchun_POI_Real.csv", index=False, encoding="utf-8-sig")
    # 同时保留一个带分类的备份
    df.to_csv("data/Changchun_POI_Baidu_Full.csv", index=False, encoding="utf-8-sig")
    print(f"Success: 抓取完成！共获得 {len(df)} 个多维度 POI 数据，已同步至系统底座。")
else:
    print("Error: 未抓取到数据，请检查 AK 权限或网络环境。")

