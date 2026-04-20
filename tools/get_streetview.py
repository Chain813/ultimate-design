import os
import pandas as pd
import requests
import time
import sys
from dotenv import load_dotenv

load_dotenv()

AK = os.getenv("Baidu_Map_AK")
if not AK:
    raise ValueError("请设置环境变量 Baidu_Map_AK，参考 .env.example 文件")

INPUT_EXCEL = r"data/Changchun_Precise_Points.xlsx"
SAVE_DIR = r"data/streetview"

# ==========================================
# 2. 战前准备
# ==========================================
os.makedirs(SAVE_DIR, exist_ok=True)

try:
    df = pd.read_excel(INPUT_EXCEL)
    print(f"✅ 成功读取坐标底表，共 {len(df)} 个有效空间节点。")
except FileNotFoundError:
    print(f"❌ 找不到 Excel 文件！请检查路径：{INPUT_EXCEL}")
    sys.exit()

if 'ID' not in df.columns:
    df['ID'] = df.index + 1

# ==========================================
# 3. 工业级抓取引擎 (智能熔断 + 坏图清洗 + 断点续传)
# ==========================================
headings = [0, 90, 180, 270]
print("🚀 开始连接百度全景图 API 获取街景数据...")
print("💡 提示：已开启断点续传与配额熔断保护。跳过已下载节点时不消耗配额！")

download_count = 0

for index, row in df.iterrows():
    lat = row['Lat']
    lng = row['Lng']
    point_id = int(row['ID'])

    point_folder = os.path.join(SAVE_DIR, f"Point_{point_id}")
    os.makedirs(point_folder, exist_ok=True)

    for heading in headings:
        save_path = os.path.join(point_folder, f"heading_{heading}.jpg")

        # 🌟 核心防御 1：断点续传与坏图过滤
        # 如果本地有这张图，且文件大小大于 1KB (1024 bytes)，说明是一张正常的图，直接跳过！
        if os.path.exists(save_path) and os.path.getsize(save_path) > 1024:
            continue

        url = f"https://api.map.baidu.com/panorama/v2?ak={AK}&width=1024&height=512&location={lng},{lat}&fov=90&heading={heading}&pitch=0&coordtype=wgs84ll"

        try:
            response = requests.get(url, timeout=10)

            # 判断返回的是不是图片
            if response.headers.get('Content-Type', '').startswith('image/'):
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                download_count += 1
                print(f"📸 成功抓取: 节点 {point_id} - 视角 {heading}° (本次累计下载: {download_count}张)")

            # 如果不是图片，说明百度拒绝了请求，开始解析 JSON 真实死因
            else:
                try:
                    res_json = response.json()
                    status = int(res_json.get("status", -1))
                    msg = res_json.get("message", "未知错误")

                    # 🚨 核心防御 2：触发熔断的死亡代码
                    # 已移除 402。仅保留 302(天配额超限), 401(并发超限), 210/211/240(权限或服务被禁)
                    if status in [302, 401, 210, 211, 240]:
                        print("\n" + "🛑" * 20)
                        print(f"🚨 警报：触发智能熔断！")
                        print(f"百度 API 拒绝请求 -> 状态码: {status} | 原始信息: {msg}")
                        print("🛑 配额已彻底耗尽或并发受限。程序已强制中止，不再做无用功！")
                        print("💡 请明天配额刷新后重新运行。下次运行将自动在一秒内跳过已下载的图片，无缝续传。")
                        print("🛑" * 20 + "\n")
                        sys.exit(0)  # 拔掉电源，瞬间切断整个 Python 程序的运行！

                    # 状态码 2 和 402 代表真的没有街景数据或无法转换有效全景ID
                    elif status in [2, 402]:
                        print(f"👻 节点 {point_id} 视角 {heading}° 物理不可达或无街景 (状态码:{status})。跳过。")
                    else:
                        print(f"⚠️ 节点 {point_id} 视角 {heading}° 遇到未知状态: {status} - {msg}")

                except Exception as json_e:
                    print(f"⚠️ 无法解析百度的返回数据: {response.text}")

        except Exception as e:
            print(f"❌ 节点 {point_id} 网络请求出错: {e}")

        # 防并发封禁延迟
        time.sleep(0.2)

print(f"\n🎉 运行结束！本次成功抓取了 {download_count} 张街景切片。")
