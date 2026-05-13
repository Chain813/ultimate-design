# 补充数据获取工具使用指南

## 快速开始

### 1. 安装依赖

```bash
# 方式一：运行安装脚本 (Windows)
install_gis_deps.bat

# 方式二：手动安装
pip install -r requirements_gis.txt
```

### 2. 配置 API Key

在项目根目录的 `.env` 文件中配置百度地图 API Key：

```
Baidu_Map_AK=your_baidu_api_key
```

获取方式：https://lbsyun.baidu.com/

### 3. 运行数据获取

```bash
# 获取所有数据
python scripts/fetch_supplementary_data.py --all

# 或按需获取
python scripts/fetch_supplementary_data.py --building    # 建筑年代
python scripts/fetch_supplementary_data.py --traffic     # 交通流量
python scripts/fetch_supplementary_data.py --price       # 房价地价
python scripts/fetch_supplementary_data.py --history     # 历史影像指南
python scripts/fetch_supplementary_data.py --sunshine    # 日照数据
python scripts/fetch_supplementary_data.py --osm         # OSM 开源数据
python scripts/fetch_supplementary_data.py --integrate   # 整合数据
```

---

## 数据说明

### 1. 建筑年代数据 (Building_Years.csv)

| 字段 | 说明 | 示例 |
|------|------|------|
| name | 建筑/小区名称 | 新发小区 |
| address | 地址 | 长春市宽城区新发路 |
| type | 类型 | 居住区/历史建筑/工业遗存 |
| build_year | 建成年代 | 1995 |
| lng | 经度 | 125.34 |
| lat | 纬度 | 43.89 |

**用途**：评估建筑老化程度，确定更新优先级

### 2. 交通流量数据 (Traffic_Flow.csv)

| 字段 | 说明 | 值域 |
|------|------|------|
| road_name | 道路名称 | 人民大街 |
| congestion_level | 拥堵等级 | 0-4 |
| congestion_desc | 拥堵描述 | 畅通/缓行/拥堵/严重拥堵 |
| speed | 速度 (km/h) | 0-60 |
| timestamp | 采集时间 | ISO 格式 |

**拥堵等级**：
- 0: 未知
- 1: 畅通
- 2: 缓行
- 3: 拥堵
- 4: 严重拥堵

### 3. 房价数据 (House_Prices.csv)

| 字段 | 说明 | 示例 |
|------|------|------|
| name | 小区名称 | 新发小区 |
| address | 地址 | 长春市宽城区新发路 |
| lng | 经度 | 125.34 |
| lat | 纬度 | 43.89 |
| price_per_sqm | 均价 (元/㎡) | 6500 |
| source | 数据来源 | estimated/baidu/ke.com |

### 4. 基准地价 (Land_Prices.csv)

| 字段 | 说明 | 示例 |
|------|------|------|
| zone | 地价级别 | 一级地 |
| description | 区域描述 | 人民大街沿线 |
| base_price | 基准地价 (元/㎡) | 4500 |

### 5. 日照数据

生成多个文件：
- `Sunshine_Annual.csv`: 全年日照统计
- `Sunshine_Winter_Solstice.csv`: 冬至日日照 (最不利条件)
- `Sunshine_Summer_Solstice.csv`: 夏至日日照
- `Sunshine_Building_Shadow.csv`: 建筑阴影校验

**建筑阴影校验说明**：
| 字段 | 说明 |
|------|------|
| building_name | 建筑类型 |
| building_height | 建筑高度 (m) |
| building_distance | 建筑间距 (m) |
| shadow_length | 冬至日阴影长度 (m) |
| meets_standard | 是否满足日照标准 |
| suggested_distance | 建议间距 (m) |

---

## OSM 开源数据

使用 OSMnx 从 OpenStreetMap 获取数据：

```bash
python scripts/fetch_supplementary_data.py --osm
```

### 生成文件

| 文件 | 说明 |
|------|------|
| `Building_Footprints_OSM.geojson` | 建筑轮廓 |
| `Road_Network.geojson` | 道路网络 |
| `POI_OSM.csv` | POI 兴趣点 |
| `Green_Spaces.geojson` | 绿地数据 |

### 自定义获取范围

```python
from scripts.fetch_supplementary_data import OSMnxDataFetcher

fetcher = OSMnxDataFetcher()

# 自定义区域
fetcher.fetch_buildings("南关区, 长春市, 吉林省, 中国")
fetcher.fetch_road_network("朝阳区, 长春市, 吉林省, 中国")
```

---

## 开源项目集成

### 已集成的开源项目

| 项目 | 用途 | 安装 |
|------|------|------|
| OSMnx | OSM 数据获取 | `pip install osmnx` |
| Momepy | 城市形态分析 | `pip install momepy` |
| Pandana | 可达性分析 | `pip install pandana` |
| PySAL | 空间统计 | `pip install pysal` |
| Leafmap | 交互式地图 | `pip install leafmap` |
| PyDeck | 3D 可视化 | `pip install pydeck` |

### 使用示例

```python
import osmnx as ox
import momepy
import geopandas as gpd

# 1. 获取建筑数据
buildings = ox.geometries_from_place("宽城区, 长春市", tags={"building": True})

# 2. 计算形态指标
buildings["area"] = buildings.geometry.area
buildings["compactness"] = 4 * 3.14159 * buildings["area"] / buildings.geometry.length**2

# 3. 分析结果
print(f"平均紧凑度: {buildings['compactness'].mean():.2f}")
```

---

## 常见问题

### Q: OSMnx 安装失败？

A: 尝试以下方案：
```bash
# 方式一：使用 conda
conda install -c conda-forge osmnx

# 方式二：指定版本
pip install osmnx==1.9.3
```

### Q: 百度地图 API 调用失败？

A: 检查以下几点：
1. API Key 是否正确配置
2. API 配额是否用完
3. 网络连接是否正常

### Q: 数据坐标系不对？

A: 确保所有数据使用 WGS84 (EPSG:4326)：
```python
import geopandas as gpd

gdf = gpd.read_file("data.geojson")
gdf = gdf.to_crs(epsg=4326)
gdf.to_file("data_wgs84.geojson", driver="GeoJSON")
```

---

## 更新日志

- 2024-05-07: 初始版本，支持建筑年代、交通流量、房价、日照数据获取
- 2024-05-07: 集成 OSMnx，支持从 OpenStreetMap 获取完整数据
