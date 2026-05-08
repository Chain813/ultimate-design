"""数据类别定义和辅助函数。

从 Stage 0 数据准备页面提取的独立模块，包含所有数据类别的定义、
检查函数和工具函数。

Usage:
    from src.data.data_categories import DATA_CATEGORIES, check_data_exists, get_data_size
"""


from src.config import DATA_DIR, SHP_DIR, STREETVIEW_DIR

DATA_CATEGORIES = [
    {
        "id": "boundary",
        "title": "研究范围边界",
        "icon": "📐",
        "description": "研究区域的规划红线边界，用于限定所有分析的空间范围。",
        "target_path": SHP_DIR / "Boundary_Scope.geojson",
        "accept": [".geojson", ".json"],
        "format_desc": "GeoJSON (Polygon / MultiPolygon)",
        "required": True,
        "tutorial": {
            "summary": "从 GIS 软件导出研究范围红线为 GeoJSON 格式。",
            "methods": [
                {
                    "name": "方法一：从 ArcGIS/QGIS 导出 (推荐)",
                    "steps": [
                        "1. 在 ArcGIS Pro 或 QGIS 中打开项目工程文件",
                        "2. 选中研究范围的面要素图层",
                        "3. 右键图层 → 导出要素 → 选择 GeoJSON 格式",
                        "4. 坐标系选择 WGS 84 (EPSG:4326)",
                        "5. 保存文件命名为 Boundary_Scope.geojson",
                    ],
                    "code_example": '''# QGIS Python 控制台导出
import processing

# 获取当前图层
layer = iface.activeLayer()

# 设置输出路径
output_path = "data/shp/Boundary_Scope.geojson"

# 导出为 GeoJSON
processing.run("native:savefeatures", {
    'INPUT': layer,
    'OUTPUT': output_path,
    'LAYER_NAME': 'Boundary_Scope',
    'DATASOURCE_OPTIONS': '',
    'LAYER_OPTIONS': 'RFC7946=YES'
})

print(f"导出完成: {output_path}")''',
                    "tip": "确保导出的坐标系为 WGS 84，否则地图定位会偏移。",
                },
                {
                    "name": "方法二：使用 geojson.io 在线绘制",
                    "steps": [
                        "1. 访问 geojson.io 网站",
                        "2. 使用绘图工具绘制研究范围多边形",
                        "3. 在右侧 JSON 面板中复制 GeoJSON 内容",
                        "4. 保存为 .geojson 文件",
                    ],
                    "tip": "适合小范围快速绘制，不适合复杂边界。",
                },
                {
                    "name": "方法三：从 OpenStreetMap 提取",
                    "steps": [
                        "1. 访问 overpass-turbo.eu",
                        "2. 使用查询语句获取行政边界",
                        "3. 导出为 GeoJSON 格式",
                        "4. 使用 QGIS 裁剪到研究范围",
                    ],
                    "code_example": '''# Overpass API 查询语句 (长春市宽城区)
[out:json][timeout:25];
// 搜索宽城区行政边界
relation["name"="宽城区"]["admin_level"="6"](43.8,125.2,44.0,125.5);
out body;
>;
out skel qt;''',
                    "tip": "OSM 边界可能与实际规划红线有差异，需手动调整。",
                },
            ],
            "sample_fields": "type: FeatureCollection, features: [{geometry: Polygon, properties: {name, area}}]",
            "reference": "参考文件：data/shp/Boundary_Scope.geojson",
        },
    },
    {
        "id": "buildings",
        "title": "建筑轮廓数据",
        "icon": "🏢",
        "description": "研究范围内的建筑底面轮廓，包含楼层信息，用于建筑肌理分析和天际线计算。",
        "target_path": SHP_DIR / "Building_Footprints.geojson",
        "accept": [".geojson", ".json", ".shp", ".zip"],
        "format_desc": "GeoJSON / Shapefile (含 Floor 或 levels 字段)",
        "required": True,
        "tutorial": {
            "summary": "从 OpenStreetMap 或测绘数据获取建筑轮廓。",
            "methods": [
                {
                    "name": "方法一：OpenStreetMap 建筑数据提取 (推荐)",
                    "steps": [
                        "1. 访问 download.geofabrik.de 下载中国吉林省数据",
                        "2. 使用 osmium 或 QGIS 筛选 building=* 要素",
                        "3. 裁剪到研究范围，导出为 GeoJSON",
                        "4. 如有楼层信息 (building:levels)，保留该字段",
                    ],
                    "code_example": '''import osmium
import json
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

class BuildingHandler(osmium.SimpleHandler):
    def __init__(self, boundary_geojson):
        super().__init__()
        self.buildings = []
        with open(boundary_geojson, 'r', encoding='utf-8') as f:
            boundary_data = json.load(f)
        self.boundary = shape(boundary_data['features'][0]['geometry'])

    def way(self, w):
        if 'building' in w.tags:
            coords = [(n.lon, n.lat) for n in w.nodes]
            if len(coords) >= 3:
                from shapely.geometry import Polygon
                try:
                    poly = Polygon(coords)
                    if self.boundary.contains(poly.centroid):
                        self.buildings.append({
                            "type": "Feature",
                            "geometry": mapping(poly),
                            "properties": {
                                "building": w.tags.get("building", "yes"),
                                "levels": w.tags.get("building:levels", ""),
                                "height": w.tags.get("height", ""),
                                "name": w.tags.get("name", "")
                            }
                        })
                except:
                    pass

# 使用示例
handler = BuildingHandler("data/shp/Boundary_Scope.geojson")
handler.apply_file("changchun.osm.pbf")

geojson = {"type": "FeatureCollection", "features": handler.buildings}
with open("data/shp/Building_Footprints.geojson", "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False, indent=2)

print(f"提取了 {len(handler.buildings)} 个建筑")''',
                    "tip": "OSM 建筑数据覆盖率因地区而异，部分区域可能不完整。",
                },
                {
                    "name": "方法二：使用天地图矢量瓦片",
                    "steps": [
                        "1. 申请天地图开发者密钥 (天地图官网注册)",
                        "2. 使用矢量瓦片下载工具获取建筑数据",
                        "3. 转换为 GeoJSON 格式并裁剪到研究范围",
                    ],
                    "code_example": '''import requests
import json

# 天地图 API (需要申请密钥)
API_KEY = "your_tianditu_key"

# 获取矢量瓦片
url = f"http://t0.tianditu.gov.cn/vec_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=vec&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX=18&TILEROW=100&TILECOL=200&tk={API_KEY}"

# 注意：实际使用需要更复杂的瓦片拼接和建筑提取逻辑
# 建议使用 QGIS 插件或专业工具''',
                    "tip": "需注意数据使用授权范围。",
                },
                {
                    "name": "方法三：测绘院/规划局数据申请",
                    "steps": [
                        "1. 联系当地测绘院或规划局申请建筑普查数据",
                        "2. 通常为 Shapefile 或 GDB 格式",
                        "3. 使用 QGIS 转换为 GeoJSON (WGS 84 坐标系)",
                        "4. 确保包含 Floor 或 levels 字段",
                    ],
                    "tip": "官方数据最准确，但申请流程可能较长。",
                },
            ],
            "sample_fields": "geometry: Polygon, properties: {Floor: 6, levels: 6, building: residential}",
            "reference": "参考文件：data/shp/Building_Footprints.geojson (36.9MB)",
        },
    },
    {
        "id": "key_plots",
        "title": "重点地块边界",
        "icon": "📍",
        "description": "划定 5 个重点更新单元的边界，用于深化设计和地块级诊断。",
        "target_path": SHP_DIR / "Key_Plots_District.json",
        "accept": [".json", ".geojson"],
        "format_desc": "GeoJSON FeatureCollection (5 个 Polygon 要素)",
        "required": True,
        "tutorial": {
            "summary": "根据任务书要求，划定重点深化设计的 5 个地块边界。",
            "methods": [
                {
                    "name": "方法一：GIS 软件手动划定 (推荐)",
                    "steps": [
                        "1. 在 ArcGIS/QGIS 中加载研究范围底图",
                        "2. 参考任务书或现状分析，识别 5 个重点地块",
                        "3. 新建面要素图层，逐一绘制地块边界",
                        "4. 添加 name 或 id 属性字段标识地块",
                        "5. 导出为 GeoJSON 格式",
                    ],
                    "code_example": '''# QGIS Python 控制台创建地块
from qgis.core import *
from PyQt5.QtCore import *

# 创建新图层
layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "Key_Plots", "memory")
provider = layer.dataProvider()

# 添加字段
provider.addAttributes([
    QgsField("id", QVariant.Int),
    QgsField("name", QVariant.String),
    QgsField("area_ha", QVariant.Double)
])
layer.updateFields()

# 添加地块要素 (示例坐标，需替换为实际坐标)
plots = [
    {"id": 1, "name": "伪满皇宫周边", "coords": [...]},
    {"id": 2, "name": "新民大街历史街区", "coords": [...]},
    {"id": 3, "name": "光复路片区", "coords": [...]},
    {"id": 4, "name": "胜利公园片区", "coords": [...]},
    {"id": 5, "name": "站前商业区", "coords": [...]},
]

for plot in plots:
    feat = QgsFeature()
    feat.setGeometry(QgsGeometry.fromPolygonXY([plot["coords"]]))
    feat.setAttributes([plot["id"], plot["name"], 0])
    provider.addFeature(feat)

layer.updateExtents()
QgsProject.instance().addMapLayer(layer)

# 导出为 GeoJSON
QgsVectorFileWriter.writeAsVectorFormat(
    layer, "data/shp/Key_Plots_District.json",
    "utf-8", layer.crs(), "GeoJSON"
)''',
                    "tip": "地块划分应结合用地性质、更新潜力和设计重点。",
                },
                {
                    "name": "方法二：从控规图层提取",
                    "steps": [
                        "1. 加载控规用地图层",
                        "2. 选择需要深化的控规单元",
                        "3. 合并或拆分为 5 个设计地块",
                        "4. 导出为 GeoJSON",
                    ],
                    "tip": "确保地块边界与控规单元边界对齐。",
                },
            ],
            "sample_fields": "type: FeatureCollection, features: [{geometry: Polygon, properties: {id: 1, name: 伪满皇宫周边}}]",
            "reference": "参考文件：data/shp/Key_Plots_District.json",
        },
    },
    {
        "id": "poi",
        "title": "POI 兴趣点数据",
        "icon": "🏪",
        "description": "餐饮、商业、公共服务等兴趣点，用于活力分析、业态分布和服务设施评估。",
        "target_path": DATA_DIR / "Changchun_POI_Real.csv",
        "accept": [".csv", ".xlsx"],
        "format_desc": "CSV (Name, Lat, Lng) 或 (Name, Type, Lat, Lng)",
        "required": True,
        "tutorial": {
            "summary": "通过高德/百度地图 API 批量获取研究范围内的 POI 数据。",
            "methods": [
                {
                    "name": "方法一：高德地图 POI 搜索 API (推荐)",
                    "steps": [
                        "1. 注册高德开放平台账号 (lbs.amap.com)",
                        "2. 创建应用并获取 API Key",
                        "3. 使用「周边搜索」或「多边形搜索」接口",
                        "   - 接口：https://restapi.amap.com/v3/place/polygon",
                        "   - 参数：polygon=研究范围边界坐标, types=餐饮|购物|教育等",
                        "4. 使用 Python 脚本分页获取所有结果",
                        "5. 整理为 CSV 格式 (Name, Lat, Lng)",
                    ],
                    "code_example": '''import requests
import pandas as pd
import json

# 高德地图 API 配置
API_KEY = "your_amap_key"  # 替换为你的 API Key

# 研究范围边界坐标 (从 Boundary_Scope.geojson 提取)
with open("data/shp/Boundary_Scope.geojson", "r", encoding="utf-8") as f:
    boundary = json.load(f)

# 提取边界坐标
coords = boundary["features"][0]["geometry"]["coordinates"][0]
polygon_str = ";".join([f"{c[0]},{c[1]}" for c in coords])

# POI 类型代码
poi_types = [
    "050000",  # 餐饮服务
    "060000",  # 购物服务
    "070000",  # 生活服务
    "080000",  # 体育休闲服务
    "090000",  # 医疗保健服务
    "100000",  # 住宿服务
    "110000",  # 风景名胜
    "120000",  # 商务住宅
    "130000",  # 政府机构及社会团体
    "140000",  # 科教文化服务
    "150000",  # 交通设施服务
]

all_pois = []
page = 1

while True:
    url = f"https://restapi.amap.com/v3/place/polygon"
    params = {
        "key": API_KEY,
        "polygon": polygon_str,
        "types": "|".join(poi_types),
        "offset": 25,
        "page": page,
        "extensions": "all"
    }

    resp = requests.get(url, params=params).json()

    if resp["status"] == "1" and resp["pois"]:
        for poi in resp["pois"]:
            lng, lat = poi["location"].split(",")
            all_pois.append({
                "Name": poi["name"],
                "Type": poi.get("type", ""),
                "Lat": float(lat),
                "Lng": float(lng),
                "Address": poi.get("address", ""),
                "Tel": poi.get("tel", "")
            })
        page += 1
    else:
        break

# 保存为 CSV
df = pd.DataFrame(all_pois)
df.to_csv("data/Changchun_POI_Real.csv", index=False, encoding="utf-8-sig")

print(f"获取了 {len(all_pois)} 个 POI")''',
                    "tip": "高德 API 每日调用次数有限，建议使用企业认证提升配额。",
                },
                {
                    "name": "方法二：百度地图 POI 检索 API",
                    "steps": [
                        "1. 注册百度地图开放平台账号 (lbsyun.baidu.com)",
                        "2. 创建应用并获取 AK (已在 .env 中配置)",
                        "3. 使用「多边形区域检索」接口",
                        "   - 接口：https://api.map.baidu.com/place/v2/search",
                        "   - 参数：bounds=研究范围, query=美食|购物 等",
                        "4. 分页获取并整理为 CSV",
                    ],
                    "code_example": '''import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("Baidu_Map_AK")

# 研究范围边界 (经纬度范围)
bounds = "43.89,125.33,43.91,125.35"  # 格式：lat_min,lng_min,lat_max,lng_max

all_pois = []
page_num = 0

while True:
    url = "https://api.map.baidu.com/place/v2/search"
    params = {
        "query": "美食|购物|教育|医疗",
        "bounds": bounds,
        "output": "json",
        "ak": API_KEY,
        "page_size": 20,
        "page_num": page_num
    }

    resp = requests.get(url, params=params).json()

    if resp.get("status") == 0 and resp.get("results"):
        for poi in resp["results"]:
            all_pois.append({
                "Name": poi["name"],
                "Lat": poi["location"]["lat"],
                "Lng": poi["location"]["lng"],
                "Address": poi.get("address", ""),
                "Tel": poi.get("telephone", "")
            })
        page_num += 1
    else:
        break

df = pd.DataFrame(all_pois)
df.to_csv("data/Changchun_POI_Real.csv", index=False, encoding="utf-8-sig")

print(f"获取了 {len(all_pois)} 个 POI")''',
                    "tip": "百度地图坐标系为 BD-09，需转换为 WGS-84。",
                },
            ],
            "sample_fields": "Name: 椒爱水煮鱼川菜, Lat: 43.897, Lng: 125.338",
            "reference": "参考文件：data/Changchun_POI_Real.csv",
        },
    },
    {
        "id": "traffic",
        "title": "交通设施数据",
        "icon": "🚌",
        "description": "公交站、地铁站、停车场等交通设施点位，用于交通分析和可达性评估。",
        "target_path": DATA_DIR / "Changchun_Traffic_Real.csv",
        "accept": [".csv", ".xlsx"],
        "format_desc": "CSV (Name, Type, Lat, Lng)",
        "required": True,
        "tutorial": {
            "summary": "从地图 API 获取交通设施 POI 或从公交/地铁官方数据整理。",
            "methods": [
                {
                    "name": "方法一：高德地图交通设施 POI (推荐)",
                    "steps": [
                        "1. 使用高德 POI 搜索 API，types 参数设为交通设施类",
                        "   - 150000: 交通设施服务",
                        "   - 150100: 公交站",
                        "   - 150200: 地铁站",
                        "   - 150300: 停车场",
                        "2. 获取数据后整理为 CSV 格式",
                        "3. 添加 Type 字段标识设施类型",
                    ],
                    "code_example": '''import requests
import pandas as pd

API_KEY = "your_amap_key"

# 研究范围边界坐标
polygon = "125.33,43.89;125.35,43.91"

# 交通设施类型
traffic_types = ["150000", "150100", "150200", "150300"]

all_facilities = []
for poi_type in traffic_types:
    url = f"https://restapi.amap.com/v3/place/polygon"
    params = {
        "key": API_KEY,
        "polygon": polygon,
        "types": poi_type,
        "offset": 25,
        "page": 1
    }

    resp = requests.get(url, params=params).json()
    if resp["status"] == "1" and resp["pois"]:
        for poi in resp["pois"]:
            lng, lat = poi["location"].split(",")
            all_facilities.append({
                "Name": poi["name"],
                "Type": poi.get("type", ""),
                "Lat": float(lat),
                "Lng": float(lng)
            })

df = pd.DataFrame(all_facilities)
df.to_csv("data/Changchun_Traffic_Real.csv", index=False, encoding="utf-8-sig")

print(f"获取了 {len(all_facilities)} 个交通设施")''',
                    "tip": "可结合公交线路数据做更深入的可达性分析。",
                },
                {
                    "name": "方法二：公交公司/地铁官网数据",
                    "steps": [
                        "1. 访问长春公交集团或长春地铁官网",
                        "2. 下载站点信息表 (通常为 Excel 或 CSV)",
                        "3. 使用地理编码 API 将站点名称转为坐标",
                        "4. 整理为标准 CSV 格式",
                    ],
                    "code_example": '''import requests
import pandas as pd

# 站点名称列表 (从公交公司获取)
stations = [
    {"Name": "伪满皇宫", "Type": "公交站"},
    {"Name": "城科所", "Type": "公交站"},
    {"Name": "陕西路", "Type": "公交站"},
    # ... 更多站点
]

API_KEY = "your_amap_key"

# 地理编码
for station in stations:
    url = f"https://restapi.amap.com/v3/geocode/geo"
    params = {
        "key": API_KEY,
        "address": station["Name"] + " 长春",
        "city": "长春"
    }
    resp = requests.get(url, params=params).json()
    if resp["status"] == "1" and resp["geocodes"]:
        lng, lat = resp["geocodes"][0]["location"].split(",")
        station["Lat"] = float(lat)
        station["Lng"] = float(lng)

df = pd.DataFrame(stations)
df.to_csv("data/Changchun_Traffic_Real.csv", index=False, encoding="utf-8-sig")''',
                    "tip": "官方数据更准确，但可能需要申请或付费。",
                },
                {
                    "name": "方法三：OpenStreetMap 交通数据",
                    "steps": [
                        "1. 使用 Overpass API 查询研究范围内的交通设施",
                        "2. 查询语句：node[\"highway\"=\"bus_stop\"](bbox);",
                        "3. 导出为 GeoJSON 后转换为 CSV",
                    ],
                    "code_example": '''# Overpass API 查询语句
[out:json][timeout:25];
// 查询公交站
node["highway"="bus_stop"](43.89,125.33,43.91,125.35);
out body;
// 查询地铁站
node["railway"="station"](43.89,125.33,43.91,125.35);
out body;
// 查询停车场
node["amenity"="parking"](43.89,125.33,43.91,125.35);
out body;''',
                    "tip": "OSM 数据更新可能滞后，需核实站点是否仍在运营。",
                },
            ],
            "sample_fields": "Name: 伪满皇宫, Type: 交通设施, Lat: 43.901, Lng: 125.341",
            "reference": "参考文件：data/Changchun_Traffic_Real.csv",
        },
    },
    {
        "id": "streetview",
        "title": "街景采样点照片",
        "icon": "📸",
        "description": "研究范围内各采样点的四方向街景照片 (0°/90°/180°/270°)，用于绿视率、围合度等视觉品质分析。",
        "target_path": STREETVIEW_DIR,
        "accept": [".jpg", ".jpeg", ".png", ".zip"],
        "format_desc": "JPG/PNG (每点 4 张：heading_0/90/180/270.jpg)",
        "required": True,
        "tutorial": {
            "summary": "通过百度/腾讯街景 API 批量获取采样点的四方向街景图。",
            "methods": [
                {
                    "name": "方法一：百度地图街景静态图 API (推荐)",
                    "steps": [
                        "1. 注册百度地图开放平台并申请街景 API 权限",
                        "2. 生成采样点坐标网格 (参考 Changchun_Precise_Points.csv)",
                        "3. 对每个采样点，调用 4 次 API 获取四个方向的街景图",
                        "   - 接口：https://map.baidu.com/?qt=qsdata",
                        "   - 参数：location=lat,lng&heading=0/90/180/270&width=512&height=512",
                        "4. 按 Point_ID 目录结构保存图片",
                    ],
                    "code_example": '''import requests
import pandas as pd
import os
import time

# 读取采样点坐标
points = pd.read_csv("data/Changchun_Precise_Points.csv")

# 百度地图 API (需要申请)
API_KEY = "your_baidu_key"

# 创建输出目录
output_dir = "data/streetview"
os.makedirs(output_dir, exist_ok=True)

for idx, row in points.iterrows():
    point_id = int(row["ID"])
    lat = row["Lat"]
    lng = row["Lng"]

    # 创建该点的目录
    point_dir = os.path.join(output_dir, f"Point_{point_id}")
    os.makedirs(point_dir, exist_ok=True)

    # 获取四个方向的街景
    for heading in [0, 90, 180, 270]:
        url = "https://map.baidu.com/"
        params = {
            "qt": "qsdata",
            "x": lng,
            "y": lat,
            "heading": heading,
            "width": 512,
            "height": 512,
            "fov": 120,
            "ak": API_KEY
        }

        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200 and resp.content:
                # 保存图片
                img_path = os.path.join(point_dir, f"heading_{heading}.jpg")
                with open(img_path, "wb") as f:
                    f.write(resp.content)
                print(f"Point_{point_id} heading_{heading} saved")
        except Exception as e:
            print(f"Error: Point_{point_id} heading_{heading}: {e}")

        # 控制请求频率
        time.sleep(0.5)

print("街景数据获取完成！")''',
                    "tip": "百度街景覆盖范围有限，部分采样点可能无街景数据。",
                },
                {
                    "name": "方法二：腾讯地图街景 API",
                    "steps": [
                        "1. 注册腾讯位置服务并申请街景 API",
                        "2. 使用全景静态图接口获取街景",
                        "   - 接口：https://apis.map.qq.com/ws/streetview/v1/image",
                        "   - 参数：location=lat,lng&heading=0/90/180/270&size=512x512",
                        "3. 保存为标准目录结构",
                    ],
                    "code_example": '''import requests
import pandas as pd
import os

points = pd.read_csv("data/Changchun_Precise_Points.csv")
API_KEY = "your_tencent_key"

output_dir = "data/streetview"
os.makedirs(output_dir, exist_ok=True)

for idx, row in points.iterrows():
    point_id = int(row["ID"])
    lat = row["Lat"]
    lng = row["Lng"]

    point_dir = os.path.join(output_dir, f"Point_{point_id}")
    os.makedirs(point_dir, exist_ok=True)

    for heading in [0, 90, 180, 270]:
        url = "https://apis.map.qq.com/ws/streetview/v1/image"
        params = {
            "key": API_KEY,
            "location": f"{lat},{lng}",
            "heading": heading,
            "pitch": 0,
            "fov": 120,
            "size": "512x512"
        }

        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            img_path = os.path.join(point_dir, f"heading_{heading}.jpg")
            with open(img_path, "wb") as f:
                f.write(resp.content)

print("街景数据获取完成！")''',
                    "tip": "腾讯街景覆盖城市较多，可作为百度的补充。",
                },
                {
                    "name": "方法三：现场实拍 + 后期处理",
                    "steps": [
                        "1. 使用相机或手机在采样点拍摄四方向照片",
                        "2. 使用 GPS 记录拍摄位置坐标",
                        "3. 后期裁剪为统一尺寸 (建议 512x512 或 1024x1024)",
                        "4. 按标准目录结构整理",
                    ],
                    "code_example": '''# 批量重命名和裁剪脚本
from PIL import Image
import os
import glob

# 原始照片目录 (假设按拍摄顺序命名)
raw_dir = "raw_photos"
output_dir = "data/streetview"

# 读取采样点坐标表
points = pd.read_csv("data/Changchun_Precise_Points.csv")

# 假设照片按 Point_ID 顺序拍摄
photos = sorted(glob.glob(os.path.join(raw_dir, "*.jpg")))

for i, photo_path in enumerate(photos):
    point_id = int(points.iloc[i]["ID"])
    point_dir = os.path.join(output_dir, f"Point_{point_id}")
    os.makedirs(point_dir, exist_ok=True)

    # 打开并裁剪图片
    img = Image.open(photo_path)

    # 假设每张照片包含 4 个方向 (需要根据实际情况调整)
    # 这里简化为每张照片对应一个方向
    heading = (i % 4) * 90
    output_path = os.path.join(point_dir, f"heading_{heading}.jpg")

    # 裁剪和调整大小
    img = img.resize((512, 512), Image.Resampling.LANCZOS)
    img.save(output_path, "JPEG", quality=95)

print("照片整理完成！")''',
                    "tip": "实拍数据最真实，但工作量大且受天气影响。",
                },
            ],
            "sample_fields": "目录结构：Point_1/heading_0.jpg, heading_90.jpg, heading_180.jpg, heading_270.jpg",
            "reference": "参考目录：data/streetview/ (约 400+ 采样点)",
        },
    },
    {
        "id": "nlp_text",
        "title": "社交媒体评论数据",
        "icon": "💬",
        "description": "微博、大众点评等平台关于研究区域的用户评论，用于情感分析和公众意见挖掘。",
        "target_path": DATA_DIR / "CV_NLP_RawData.csv",
        "accept": [".csv", ".xlsx"],
        "format_desc": "CSV (Text, Keyword, Source)",
        "required": True,
        "tutorial": {
            "summary": "通过社交媒体 API 或网络爬取获取用户评论文本。",
            "methods": [
                {
                    "name": "方法一：微博超话/话题爬取 (推荐)",
                    "steps": [
                        "1. 使用 Python 爬虫获取微博话题页面",
                        "2. 搜索关键词如「伪满皇宫」「长春历史街区」等",
                        "3. 提取评论文本、发布时间、用户信息",
                        "4. 整理为 CSV 格式 (Text, Keyword, Source)",
                    ],
                    "code_example": '''import requests
import pandas as pd
import re
import time
from bs4 import BeautifulSoup

# 微博搜索 API (需要登录获取 cookie)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Cookie": "your_weibo_cookie"  # 需要登录微博获取
}

keywords = ["伪满皇宫", "长春历史街区", "宽城区更新"]
all_comments = []

for keyword in keywords:
    for page in range(1, 11):  # 获取前 10 页
        url = f"https://s.weibo.com/weibo?q={keyword}&page={page}"
        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")

        # 提取评论文本
        for item in soup.find_all("p", class_="txt"):
            text = item.get_text().strip()
            if text:
                all_comments.append({
                    "Text": text,
                    "Keyword": keyword,
                    "Source": "新浪微博"
                })

        time.sleep(2)  # 控制请求频率

df = pd.DataFrame(all_comments)
df.to_csv("data/CV_NLP_RawData.csv", index=False, encoding="utf-8-sig")

print(f"获取了 {len(all_comments)} 条评论")''',
                    "tip": "注意遵守平台服务条款，控制爬取频率。",
                },
                {
                    "name": "方法二：大众点评评论获取",
                    "steps": [
                        "1. 获取研究区域内商户列表",
                        "2. 爬取商户评论页面",
                        "3. 提取评论文本和评分",
                        "4. 整理为标准 CSV 格式",
                    ],
                    "code_example": '''import requests
import pandas as pd
import time

# 大众点评商户 ID 列表 (需要手动收集或爬取)
shop_ids = [123456, 234567, 345678]  # 示例

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Cookie": "your_dianping_cookie"
}

all_comments = []

for shop_id in shop_ids:
    url = f"https://www.dianping.com/shop/{shop_id}/review_all"
    resp = requests.get(url, headers=headers)
    # 解析 HTML 提取评论
    # ... (需要根据实际页面结构编写解析逻辑)

    time.sleep(3)

df = pd.DataFrame(all_comments)
df.to_csv("data/CV_NLP_RawData.csv", index=False, encoding="utf-8-sig")''',
                    "tip": "大众点评反爬较严格，建议使用官方 API 或代理池。",
                },
                {
                    "name": "方法三：使用现成数据集",
                    "steps": [
                        "1. 在学术数据平台搜索相关数据集",
                        "2. 下载并筛选研究范围内的评论",
                        "3. 整理为标准格式",
                    ],
                    "tip": "适合快速获取，但数据时效性可能不足。",
                },
            ],
            "sample_fields": "Text: 受邀来长春参观，第一站是伪满皇宫..., Keyword: 长春伪满皇宫, Source: 新浪微博",
            "reference": "参考文件：data/CV_NLP_RawData.csv",
        },
    },
    {
        "id": "gvi",
        "title": "街景视觉品质指标",
        "icon": "🌿",
        "description": "绿视率 (GVI)、天空开阔度 (SVF)、围合度 (Enclosure)、杂乱度 (Clutter) 等指标计算结果。",
        "target_path": DATA_DIR / "GVI_Results_Analysis.csv",
        "accept": [".csv", ".xlsx"],
        "format_desc": "CSV (ID, GVI, SVF, Enclosure, Clutter)",
        "required": True,
        "tutorial": {
            "summary": "使用语义分割模型对街景图像进行分析，计算视觉品质指标。",
            "methods": [
                {
                    "name": "方法一：使用 SegFormer 语义分割 (推荐)",
                    "steps": [
                        "1. 安装语义分割模型 (SegFormer 或 MIT SegNet)",
                        "2. 对每张街景图进行像素级语义分割",
                        "3. 根据分割结果计算各指标",
                        "4. 汇总为 CSV 格式",
                    ],
                    "code_example": '''import torch
import numpy as np
from PIL import Image
from transformers import SegformerFeatureExtractor, SegformerForSemanticSegmentation
import pandas as pd
from pathlib import Path

# 加载预训练模型
feature_extractor = SegformerFeatureExtractor.from_pretrained("nvidia/segformer-b0-finetuned-ade-512-512")
model = SegformerForSemanticSegmentation.from_pretrained("nvidia/segformer-b0-finetuned-ade-512-512")

# ADE20K 数据集的类别映射 (部分)
# 0: background, 4: tree, 9: grass, 12: sky, 14: wall, 15: building
GREEN_CLASSES = [4, 9]  # 树木和草地
SKY_CLASS = 12
BUILDING_CLASSES = [14, 15]

def calc_metrics(img_path):
    """计算单张图片的视觉品质指标"""
    image = Image.open(img_path).convert("RGB")

    # 语义分割
    inputs = feature_extractor(images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    predicted = logits.argmax(dim=1).squeeze().numpy()

    total_pixels = predicted.size

    # 绿视率 (GVI)
    green_pixels = np.isin(predicted, GREEN_CLASSES).sum()
    gvi = round(green_pixels / total_pixels * 100, 2)

    # 天空开阔度 (SVF)
    sky_pixels = (predicted == SKY_CLASS).sum()
    svf = round(sky_pixels / total_pixels * 100, 2)

    # 围合度 (Enclosure)
    enclosure = round(100 - svf, 2)

    # 杂乱度 (Clutter) - 非结构化物体占比
    structured_classes = GREEN_CLASSES + SKY_CLASS + BUILDING_CLASSES + [0]
    clutter_pixels = ~np.isin(predicted, structured_classes)
    clutter = round(clutter_pixels.sum() / total_pixels * 100, 2)

    return {"GVI": gvi, "SVF": svf, "Enclosure": enclosure, "Clutter": clutter}

# 批量处理
results = []
streetview_dir = Path("data/streetview")

for point_dir in streetview_dir.iterdir():
    if point_dir.is_dir():
        point_id = point_dir.name.replace("Point_", "")
        metrics_list = []

        for img_path in point_dir.glob("*.jpg"):
            metrics = calc_metrics(str(img_path))
            metrics_list.append(metrics)

        # 取四张图片的平均值
        avg_metrics = {
            "ID": point_id,
            "GVI": round(np.mean([m["GVI"] for m in metrics_list]), 2),
            "SVF": round(np.mean([m["SVF"] for m in metrics_list]), 2),
            "Enclosure": round(np.mean([m["Enclosure"] for m in metrics_list]), 2),
            "Clutter": round(np.mean([m["Clutter"] for m in metrics_list]), 2),
        }
        results.append(avg_metrics)
        print(f"Point_{point_id} done")

df = pd.DataFrame(results)
df.to_csv("data/GVI_Results_Analysis.csv", index=False)

print(f"处理完成，共 {len(results)} 个采样点")''',
                    "tip": "需要 GPU 支持，处理 400+ 采样点约需 1-2 小时。",
                },
                {
                    "name": "方法二：简化版 HSV 颜色分割",
                    "steps": [
                        "1. 使用 OpenCV 的 HSV 颜色空间",
                        "2. 设定绿色和天空的颜色范围",
                        "3. 计算各颜色占比",
                        "4. 汇总为 CSV 格式",
                    ],
                    "code_example": '''import cv2
import numpy as np
import pandas as pd
from pathlib import Path

def calc_gvi_simple(img_path):
    """简化版 GVI 计算 (基于 HSV 颜色分割)"""
    img = cv2.imread(img_path)
    if img is None:
        return None

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    total_pixels = img.shape[0] * img.shape[1]

    # 绿色范围 (HSV)
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([85, 255, 255])
    green_mask = cv2.inRange(hsv, lower_green, upper_green)
    gvi = round(np.sum(green_mask > 0) / total_pixels * 100, 2)

    # 天空范围 (HSV) - 浅蓝色
    lower_sky = np.array([100, 50, 50])
    upper_sky = np.array([130, 255, 255])
    sky_mask = cv2.inRange(hsv, lower_sky, upper_sky)
    svf = round(np.sum(sky_mask > 0) / total_pixels * 100, 2)

    # 围合度
    enclosure = round(100 - svf, 2)

    # 杂乱度 (非绿非天非建筑的其他区域)
    # 建筑通常为灰色/棕色
    lower_building = np.array([10, 30, 30])
    upper_building = np.array([25, 200, 200])
    building_mask = cv2.inRange(hsv, lower_building, upper_building)

    structured_mask = green_mask | sky_mask | building_mask
    clutter = round(np.sum(structured_mask == 0) / total_pixels * 100, 2)

    return {"GVI": gvi, "SVF": svf, "Enclosure": enclosure, "Clutter": clutter}

# 批量处理
results = []
streetview_dir = Path("data/streetview")

for point_dir in sorted(streetview_dir.iterdir()):
    if point_dir.is_dir():
        point_id = point_dir.name.replace("Point_", "")
        metrics_list = []

        for img_path in sorted(point_dir.glob("*.jpg")):
            metrics = calc_gvi_simple(str(img_path))
            if metrics:
                metrics_list.append(metrics)

        if metrics_list:
            avg_metrics = {
                "ID": int(point_id),
                "GVI": round(np.mean([m["GVI"] for m in metrics_list]), 2),
                "SVF": round(np.mean([m["SVF"] for m in metrics_list]), 2),
                "Enclosure": round(np.mean([m["Enclosure"] for m in metrics_list]), 2),
                "Clutter": round(np.mean([m["Clutter"] for m in metrics_list]), 2),
            }
            results.append(avg_metrics)

df = pd.DataFrame(results)
df = df.sort_values("ID").reset_index(drop=True)
df.to_csv("data/GVI_Results_Analysis.csv", index=False)

print(f"处理完成，共 {len(results)} 个采样点")''',
                    "tip": "简化版精度较低，但无需 GPU 且处理速度快。",
                },
                {
                    "name": "方法三：使用本平台内置分析引擎",
                    "steps": [
                        "1. 先上传街景照片到 data/streetview/",
                        "2. 在 Stage 04 现状分析页面使用内置分析功能",
                        "3. 系统会自动计算并保存指标",
                    ],
                    "tip": "需确保街景数据已上传且格式正确。",
                },
            ],
            "sample_fields": "ID: 1, GVI: 6.42, SVF: 42.71, Enclosure: 49.87, Clutter: 2.09",
            "reference": "参考文件：data/GVI_Results_Analysis.csv",
        },
    },
    {
        "id": "precise_points",
        "title": "采样点坐标表",
        "icon": "📍",
        "description": "街景采样点的精确坐标，用于匹配街景照片和空间分析。",
        "target_path": DATA_DIR / "Changchun_Precise_Points.xlsx",
        "accept": [".csv", ".xlsx"],
        "format_desc": "CSV/XLSX (ID, Lng, Lat)",
        "required": True,
        "tutorial": {
            "summary": "在研究范围内生成均匀采样点网格并记录坐标。",
            "methods": [
                {
                    "name": "方法一：GIS 软件生成采样点网格 (推荐)",
                    "steps": [
                        "1. 在 ArcGIS/QGIS 中加载研究范围边界",
                        "2. 使用「创建渔网」工具生成规则点网格",
                        "   - 间距建议：50-100 米",
                        "3. 裁剪到研究范围内部",
                        "4. 提取每个点的经纬度坐标",
                        "5. 导出为 CSV (ID, Lng, Lat)",
                    ],
                    "code_example": '''# QGIS Python 控制台
from qgis.core import *
import processing

# 加载研究范围边界
boundary_layer = QgsVectorLayer("data/shp/Boundary_Scope.geojson", "boundary", "ogr")
extent = boundary_layer.extent()

# 创建渔网 (50米间距)
result = processing.run("native:creategrid", {
    'TYPE': 0,  # 点
    'EXTENT': extent,
    'HSPACING': 0.0005,  # 约 50 米 (经度方向)
    'VSPACING': 0.00045,  # 约 50 米 (纬度方向)
    'HOVERLAY': 0,
    'VOVERLAY': 0,
    'CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
    'OUTPUT': 'memory:'
})

grid_layer = result['OUTPUT']

# 裁剪到研究范围
clipped = processing.run("native:clip", {
    'INPUT': grid_layer,
    'OVERLAY': boundary_layer,
    'OUTPUT': 'memory:'
})

# 导出为 CSV
layer = clipped['OUTPUT']
features = []

for i, feat in enumerate(layer.getFeatures()):
    geom = feat.geometry()
    features.append({
        'ID': i + 1,
        'Lng': round(geom.asPoint().x(), 6),
        'Lat': round(geom.asPoint().y(), 6)
    })

import pandas as pd
df = pd.DataFrame(features)
df.to_csv("data/Changchun_Precise_Points.csv", index=False)

print(f"生成了 {len(features)} 个采样点")''',
                    "tip": "采样密度影响分析精度和计算量，建议 50 米间距。",
                },
                {
                    "name": "方法二：Python 脚本生成",
                    "steps": [
                        "1. 读取研究范围边界 GeoJSON",
                        "2. 计算边界框 (Bounding Box)",
                        "3. 在边界框内生成规则网格点",
                        "4. 使用 Shapely 判断点是否在边界内",
                        "5. 导出为 CSV",
                    ],
                    "code_example": '''import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# 读取研究范围边界
boundary = gpd.read_file("data/shp/Boundary_Scope.geojson")
boundary_geom = boundary.geometry.iloc[0]

# 计算边界框
bounds = boundary.total_bounds  # [minx, miny, maxx, maxy]

# 生成网格点 (间距约 50 米)
# 在长春纬度 (43.89°N)，1度经度 ≈ 80km，1度纬度 ≈ 111km
# 50米 ≈ 0.000625度经度，0.00045度纬度
x_step = 0.000625  # 经度步长
y_step = 0.00045   # 纬度步长

x = np.arange(bounds[0], bounds[2], x_step)
y = np.arange(bounds[1], bounds[3], y_step)
xx, yy = np.meshgrid(x, y)

# 筛选在边界内的点
points_inside = []
for px, py in zip(xx.ravel(), yy.ravel()):
    point = Point(px, py)
    if boundary_geom.contains(point):
        points_inside.append({"Lng": round(px, 6), "Lat": round(py, 6)})

# 创建 DataFrame 并添加 ID
df = pd.DataFrame(points_inside)
df = df.reset_index(drop=True)
df["ID"] = df.index + 1
df = df[["ID", "Lng", "Lat"]]

# 保存
df.to_csv("data/Changchun_Precise_Points.csv", index=False)
df.to_excel("data/Changchun_Precise_Points.xlsx", index=False)

print(f"生成了 {len(df)} 个采样点")''',
                    "tip": "间距 0.000625 度约等于 50 米 (在长春纬度)。",
                },
            ],
            "sample_fields": "ID: 1, Lng: 125.3398763, Lat: 43.89209257",
            "reference": "参考文件：data/Changchun_Precise_Points.csv",
        },
    },
    {
        "id": "rag_knowledge",
        "title": "RAG 政策法规知识库",
        "icon": "📜",
        "description": "城市更新、历史保护等相关政策法规的向量化文本，用于政策合规校验和导则引用。",
        "target_path": DATA_DIR / "rag_knowledge.json",
        "accept": [".json", ".pdf"],
        "format_desc": "JSON (结构化文本块，含 source 和 content 字段)",
        "required": True,
        "tutorial": {
            "summary": "收集相关政策法规 PDF，使用 RAG 工具转为向量知识库。",
            "methods": [
                {
                    "name": "方法一：使用本平台语义萃取引擎 (推荐)",
                    "steps": [
                        "1. 收集相关政策法规 PDF 文件 (见 docs/ 目录)",
                        "2. 在 Stage 02 资料收集页面使用「语义萃取引擎」",
                        "3. 上传 PDF 文件，系统自动转为 Markdown",
                        "4. 使用 RAG 工具 (如 LangChain) 向量化并存储",
                    ],
                    "code_example": '''# 使用 LangChain 构建 RAG 知识库
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import json

# 1. 加载 PDF 文档
pdf_files = [
    "docs/中共中央办公厅国务院办公厅关于持续推进城市更新行动的意见.pdf",
    "docs/伪满皇宫保护规划.pdf",
    "docs/历史文化名城保护规划规范.pdf",
    "docs/长春市历史文化名城保护条例.pdf",
    # ... 更多 PDF
]

all_documents = []
for pdf_path in pdf_files:
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    all_documents.extend(documents)

# 2. 文本分割
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\\n\\n", "\\n", "。", "；", " "]
)
chunks = text_splitter.split_documents(all_documents)

# 3. 向量化
embeddings = HuggingFaceEmbeddings(
    model_name="shibing624/text2vec-base-chinese"
)

# 4. 构建向量数据库
vectorstore = FAISS.from_documents(chunks, embeddings)

# 5. 保存为 JSON 格式 (兼容项目格式)
knowledge_base = {}
for i, doc in enumerate(chunks):
    key = f"chunk_{i:04d}"
    knowledge_base[key] = {
        "source": doc.metadata.get("source", ""),
        "content": doc.page_content,
        "embedding": embeddings.embed_query(doc.page_content)
    }

with open("data/rag_knowledge.json", "w", encoding="utf-8") as f:
    json.dump(knowledge_base, f, ensure_ascii=False, indent=2)

print(f"构建了 {len(knowledge_base)} 个知识块")''',
                    "tip": "确保 PDF 可选中文字，扫描版需先 OCR。",
                },
                {
                    "name": "方法二：手动整理 + 向量化",
                    "steps": [
                        "1. 收集政策法规 PDF 并手动转为文本",
                        "2. 按章节或段落分割为文本块",
                        "3. 添加元数据 (来源文件名、章节标题)",
                        "4. 使用 Sentence Transformers 等模型向量化",
                        "5. 存储为 JSON 格式",
                    ],
                    "code_example": '''from sentence_transformers import SentenceTransformer
import json
from pathlib import Path

# 加载中文嵌入模型
model = SentenceTransformer("shibing624/text2vec-base-chinese")

# 读取已提取的文本文件
text_files = list(Path("docs").glob("*.txt"))

chunks = []
for text_file in text_files:
    with open(text_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 按段落分割
    paragraphs = content.split("\\n\\n")

    for para in paragraphs:
        para = para.strip()
        if len(para) > 50:  # 过滤太短的段落
            chunks.append({
                "source": text_file.name,
                "content": para
            })

# 向量化
for chunk in chunks:
    chunk["embedding"] = model.encode(chunk["content"]).tolist()

# 保存为 JSON
knowledge_base = {}
for i, chunk in enumerate(chunks):
    key = f"{chunk['source']}_{i:04d}"
    knowledge_base[key] = chunk

with open("data/rag_knowledge.json", "w", encoding="utf-8") as f:
    json.dump(knowledge_base, f, ensure_ascii=False, indent=2)

print(f"构建了 {len(knowledge_base)} 个知识块")''',
                    "tip": "建议使用中文优化的嵌入模型。",
                },
            ],
            "sample_fields": "fe4c9ab64f6e: {source: 文件名.pdf, content: 文本内容...}",
            "reference": "参考文件：data/rag_knowledge.json (330KB)",
        },
    },
    # ============================================================
    # 补充数据类别 (通过脚本获取)
    # ============================================================
    {
        "id": "building_years",
        "title": "建筑年代数据",
        "icon": "🏚️",
        "description": "研究区域内建筑/小区的建成年代，用于评估建筑老化程度和更新优先级。",
        "target_path": DATA_DIR / "Building_Years.csv",
        "accept": [".csv", ".xlsx"],
        "format_desc": "CSV (name, address, type, build_year, lng, lat)",
        "required": False,
        "tutorial": {
            "summary": "通过百度百科、贝壳/链家或实地调研获取建筑年代。",
            "methods": [
                {
                    "name": "方法一：运行自动获取脚本 (推荐)",
                    "steps": [
                        "1. 确保已配置百度地图 API Key (.env 文件)",
                        "2. 运行命令: python scripts/fetch_supplementary_data.py --building",
                        "3. 脚本会自动从百度百科查询建筑信息",
                        "4. 结果保存到 data/Building_Years.csv",
                    ],
                    "code_example": '''# 直接运行脚本
python scripts/fetch_supplementary_data.py --building

# 或在 Python 中调用
from scripts.fetch_supplementary_data import BuildingYearFetcher

fetcher = BuildingYearFetcher(api_key="your_baidu_key")
df = fetcher.fetch_all()''',
                    "tip": "脚本会自动查询预设的小区列表，可修改 COMMUNITIES 变量添加更多建筑。",
                },
                {
                    "name": "方法二：贝壳/链家数据",
                    "steps": [
                        "1. 访问贝壳找房 (cc.ke.com) 或链家 (cc.lianjia.com)",
                        "2. 搜索研究区域内的小区",
                        "3. 在小区详情页查看「建筑年代」信息",
                        "4. 手动整理为 CSV 格式",
                    ],
                    "tip": "贝壳数据较准确，但需要手动收集。",
                },
                {
                    "name": "方法三：实地调研",
                    "steps": [
                        "1. 到现场拍摄建筑铭牌、门牌",
                        "2. 记录小区名称和建成年代",
                        "3. 整理为 CSV 格式",
                    ],
                    "tip": "最准确的方式，但工作量较大。",
                },
            ],
            "sample_fields": "name: 新发小区, build_year: 1995, lng: 125.34, lat: 43.89",
            "reference": "参考文件：data/Building_Years.csv",
        },
    },
    {
        "id": "traffic_flow",
        "title": "交通流量数据",
        "icon": "🚗",
        "description": "主要道路的实时路况和拥堵等级，用于交通承载力分析。",
        "target_path": DATA_DIR / "Traffic_Flow.csv",
        "accept": [".csv", ".xlsx"],
        "format_desc": "CSV (road_name, congestion_level, congestion_desc, speed, timestamp)",
        "required": False,
        "tutorial": {
            "summary": "通过百度地图实时路况 API 获取道路拥堵数据。",
            "methods": [
                {
                    "name": "方法一：运行自动获取脚本 (推荐)",
                    "steps": [
                        "1. 确保已配置百度地图 API Key (.env 文件)",
                        "2. 运行命令: python scripts/fetch_supplementary_data.py --traffic",
                        "3. 脚本会获取研究区域内主要道路的实时路况",
                        "4. 结果保存到 data/Traffic_Flow.csv",
                    ],
                    "code_example": '''# 直接运行脚本
python scripts/fetch_supplementary_data.py --traffic

# 获取多时间点数据 (用于分析交通规律)
python scripts/fetch_supplementary_data.py --traffic --multi-time''',
                    "tip": "基础版 API 只能获取实时路况，无法获取历史流量数据。",
                },
                {
                    "name": "方法二：百度地图 API 直接调用",
                    "steps": [
                        "1. 调用百度地图交通态势 API",
                        "2. 接口: https://api.map.baidu.com/traffic/v1/road",
                        "3. 参数: road_name=道路名&city=长春&ak=你的密钥",
                        "4. 返回拥堵等级 (0-4) 和速度",
                    ],
                    "code_example": '''import requests

API_KEY = "your_baidu_key"

def get_road_status(road_name):
    url = "https://api.map.baidu.com/traffic/v1/road"
    params = {
        "road_name": road_name,
        "city": "长春",
        "ak": API_KEY,
        "output": "json"
    }
    resp = requests.get(url, params=params).json()

    if resp["status"] == 0:
        traffic = resp["road_traffic"][0]
        return {
            "road": road_name,
            "level": traffic["status"],  # 0:未知 1:畅通 2:缓行 3:拥堵 4:严重拥堵
            "speed": traffic["speed"]
        }
    return None

# 获取路况
roads = ["人民大街", "新发路", "光复路", "长白路", "亚泰大街"]
for road in roads:
    status = get_road_status(road)
    print(f"{road}: {status}")''',
                    "tip": "路况数据实时变化，建议在不同时段多次采集。",
                },
            ],
            "sample_fields": "road_name: 人民大街, congestion_level: 2, congestion_desc: 缓行, speed: 25",
            "reference": "参考文件：data/Traffic_Flow.csv",
        },
    },
    {
        "id": "house_prices",
        "title": "房价数据",
        "icon": "🏠",
        "description": "研究区域内的住宅价格，用于土地价值评估和更新经济可行性分析。",
        "target_path": DATA_DIR / "House_Prices.csv",
        "accept": [".csv", ".xlsx"],
        "format_desc": "CSV (name, address, lng, lat, price_per_sqm, source)",
        "required": False,
        "tutorial": {
            "summary": "通过贝壳/链家或百度地图获取房价数据。",
            "methods": [
                {
                    "name": "方法一：运行自动获取脚本 (推荐)",
                    "steps": [
                        "1. 确保已配置百度地图 API Key (.env 文件)",
                        "2. 运行命令: python scripts/fetch_supplementary_data.py --price",
                        "3. 脚本会获取研究区域内的小区和估算房价",
                        "4. 结果保存到 data/House_Prices.csv",
                    ],
                    "code_example": '''# 直接运行脚本
python scripts/fetch_supplementary_data.py --price''',
                    "tip": "脚本使用估算模型，实际应用建议结合贝壳数据。",
                },
                {
                    "name": "方法二：贝壳/链家房价数据",
                    "steps": [
                        "1. 访问贝壳找房 (cc.ke.com)",
                        "2. 搜索研究区域内的小区",
                        "3. 查看小区均价 (元/㎡)",
                        "4. 整理为 CSV 格式",
                    ],
                    "code_example": '''# 贝壳小区列表页示例
# https://cc.ke.com/xiaoqu/kuaichengqu/

# 手动整理的数据示例
import pandas as pd

prices = [
    {"name": "新发小区", "price": 6500, "year": 1995},
    {"name": "光复小区", "price": 7200, "year": 2000},
    {"name": "站前小区", "price": 8500, "year": 2005},
    # ... 更多小区
]

df = pd.DataFrame(prices)
df.to_csv("data/House_Prices.csv", index=False, encoding="utf-8-sig")''',
                    "tip": "贝壳数据更新及时，但需要手动收集。",
                },
            ],
            "sample_fields": "name: 新发小区, price_per_sqm: 6500, source: 贝壳找房",
            "reference": "参考文件：data/House_Prices.csv",
        },
    },
    {
        "id": "land_prices",
        "title": "基准地价数据",
        "icon": "📍",
        "description": "政府公布的基准地价，用于土地价值评估和开发强度测算。",
        "target_path": DATA_DIR / "Land_Prices.csv",
        "accept": [".csv", ".xlsx"],
        "format_desc": "CSV (zone, description, base_price)",
        "required": False,
        "tutorial": {
            "summary": "从政府网站获取基准地价公示数据。",
            "methods": [
                {
                    "name": "方法一：运行自动获取脚本",
                    "steps": [
                        "1. 运行命令: python scripts/fetch_supplementary_data.py --price",
                        "2. 脚本会生成基准地价模板数据",
                        "3. 结果保存到 data/Land_Prices.csv",
                    ],
                    "code_example": '''# 运行脚本
python scripts/fetch_supplementary_data.py --price''',
                    "tip": "脚本生成的是估算数据，建议参考官方基准地价表更新。",
                },
                {
                    "name": "方法二：政府网站查询",
                    "steps": [
                        "1. 访问长春市自然资源局官网",
                        "2. 搜索「基准地价」公示文件",
                        "3. 下载基准地价表",
                        "4. 提取研究区域对应的地价数据",
                    ],
                    "tip": "基准地价通常每2-3年更新一次。",
                },
            ],
            "sample_fields": "zone: 一级地, description: 人民大街沿线, base_price: 4500",
            "reference": "参考文件：data/Land_Prices.csv",
        },
    },
    {
        "id": "historical_images",
        "title": "历史卫星影像",
        "icon": "🛰️",
        "description": "多时相卫星影像，用于分析城市演变和历史风貌变化。",
        "target_path": DATA_DIR / "historical_images",
        "accept": [".jpg", ".jpeg", ".png", ".tif"],
        "format_desc": "JPG/PNG/GeoTIFF (按年份命名)",
        "required": False,
        "tutorial": {
            "summary": "使用 Google Earth Pro 或 91卫图助手下载历史影像。",
            "methods": [
                {
                    "name": "方法一：运行获取指南脚本",
                    "steps": [
                        "1. 运行命令: python scripts/fetch_supplementary_data.py --history",
                        "2. 脚本会显示详细的获取指南",
                        "3. 创建下载目录和记录模板",
                    ],
                    "code_example": '''# 运行脚本查看指南
python scripts/fetch_supplementary_data.py --history''',
                    "tip": "历史影像需要手动下载，脚本提供指南和模板。",
                },
                {
                    "name": "方法二：Google Earth Pro (推荐)",
                    "steps": [
                        "1. 下载安装 Google Earth Pro (免费)",
                        "2. 搜索「长春市宽城区」",
                        "3. 点击工具栏时钟图标 (历史影像)",
                        "4. 选择年份: 2000, 2005, 2010, 2015, 2020, 2024",
                        "5. 文件 → 保存 → 保存图像",
                    ],
                    "tip": "Google Earth Pro 免费，影像质量好。",
                },
                {
                    "name": "方法三：91卫图助手",
                    "steps": [
                        "1. 下载安装 91卫图助手",
                        "2. 框选研究区域",
                        "3. 选择影像源和时间范围",
                        "4. 导出为 GeoTIFF 格式",
                    ],
                    "tip": "91卫图助手支持批量下载和导出带坐标的影像。",
                },
            ],
            "sample_fields": "文件命名: 2000_satellite.jpg, 2005_satellite.jpg, ...",
            "reference": "保存目录: data/historical_images/",
        },
    },
    {
        "id": "sunshine",
        "title": "日照数据",
        "icon": "☀️",
        "description": "太阳位置、日照时数、建筑阴影等数据，用于日照分析和建筑间距校验。",
        "target_path": DATA_DIR / "Sunshine_Annual.csv",
        "accept": [".csv", ".xlsx"],
        "format_desc": "CSV (month, sunshine_hours, max_altitude, sunrise_hour, sunset_hour)",
        "required": False,
        "tutorial": {
            "summary": "使用日照模拟算法计算太阳位置和建筑阴影。",
            "methods": [
                {
                    "name": "方法一：运行自动计算脚本 (推荐)",
                    "steps": [
                        "1. 运行命令: python scripts/fetch_supplementary_data.py --sunshine",
                        "2. 脚本会计算全年日照统计、冬至/夏至日照、建筑阴影",
                        "3. 结果保存到 data/ 目录下的多个 CSV 文件",
                    ],
                    "code_example": '''# 运行脚本
python scripts/fetch_supplementary_data.py --sunshine

# 生成的文件:
# - Sunshine_Annual.csv: 全年日照统计
# - Sunshine_Winter_Solstice.csv: 冬至日日照
# - Sunshine_Summer_Solstice.csv: 夏至日日照
# - Sunshine_Building_Shadow.csv: 建筑阴影校验''',
                    "tip": "脚本使用天文算法计算，精度满足规划要求。",
                },
                {
                    "name": "方法二：使用 pvlib 库",
                    "steps": [
                        "1. 安装: pip install pvlib",
                        "2. 使用 pvlib 计算太阳位置",
                        "3. 结合建筑高度计算阴影",
                    ],
                    "code_example": '''import pvlib
import pandas as pd

# 长春位置
location = pvlib.location.Location(43.89, 125.34, tz='Asia/Shanghai')

# 计算冬至日太阳位置
times = pd.date_range('2024-12-21', periods=24, freq='h', tz='Asia/Shanghai')
solar_pos = location.get_solarposition(times)

# 查看太阳高度角
print(solar_pos[['apparent_elevation', 'azimuth']])''',
                    "tip": "pvlib 是专业的太阳能分析库，计算精度高。",
                },
            ],
            "sample_fields": "month: 12, sunshine_hours: 6.5, max_altitude: 22.5",
            "reference": "参考文件：data/Sunshine_Annual.csv",
        },
    },
]


# ============================================================
# 辅助函数
# ============================================================

def check_data_exists(category_id: str) -> bool:
    """检查数据文件是否存在。"""
    cat = next((c for c in DATA_CATEGORIES if c["id"] == category_id), None)
    if not cat:
        return False
    target = cat["target_path"]
    if target.is_dir():
        return any(target.iterdir())
    return target.exists()


def get_data_size(category_id: str) -> str:
    """获取数据文件大小。"""
    cat = next((c for c in DATA_CATEGORIES if c["id"] == category_id), None)
    if not cat:
        return "未知"
    target = cat["target_path"]
    if not target.exists():
        return "未上传"
    if target.is_dir():
        total = sum(f.stat().st_size for f in target.rglob("*") if f.is_file())
    else:
        total = target.stat().st_size
    if total < 1024:
        return f"{total} B"
    elif total < 1024 * 1024:
        return f"{total / 1024:.1f} KB"
    else:
        return f"{total / (1024 * 1024):.1f} MB"


def get_categories_by_group(required_only: bool = False):
    """按必备/可选分组获取数据类别。

    Args:
        required_only: 如果为 True，只返回必备类别

    Returns:
        tuple: (required_categories, optional_categories) 或仅 required_categories
    """
    required = [c for c in DATA_CATEGORIES if c["required"]]
    optional = [c for c in DATA_CATEGORIES if not c["required"]]

    if required_only:
        return required
    return required, optional


def get_data_readiness() -> dict:
    """获取数据就绪状态统计。

    Returns:
        dict: 包含 total, loaded, required_count, required_loaded, is_ready
    """
    total = len(DATA_CATEGORIES)
    loaded = sum(1 for c in DATA_CATEGORIES if check_data_exists(c["id"]))
    required_count = sum(1 for c in DATA_CATEGORIES if c["required"])
    required_loaded = sum(1 for c in DATA_CATEGORIES if c["required"] and check_data_exists(c["id"]))

    return {
        "total": total,
        "loaded": loaded,
        "required_count": required_count,
        "required_loaded": required_loaded,
        "is_ready": required_loaded == required_count,
    }
