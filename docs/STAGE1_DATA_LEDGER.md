# 第一阶段数据资产台账（首版）

## 1. 资产总览

| 文件 | 类型 | 关键字段 | 当前状态 | 消费模块 |
| --- | --- | --- | --- | --- |
| `data/Changchun_POI_Real.csv` | CSV | `Name,Lat,Lng` | 可用 | 页面2活力/POI图层、页面1底座管理 |
| `data/Changchun_Traffic_Real.csv` | CSV | `Name,Type,Lat,Lng` | 可用 | 页面2交通诊断、页面1底座管理 |
| `data/CV_NLP_RawData.csv` | CSV | `Text,Keyword,Source` | 可用（需清洗） | 页面2社会感知、`core_engine` 情感分析 |
| `data/GVI_Results_Analysis.csv` | CSV | `ID,GVI,SVF,Enclosure,Clutter` | 可用 | 页面2 3D诊断、`core_engine` 统计 |
| `data/rag_knowledge.json` | JSON | `source,content` | 可用 | 页面4 LLM RAG 增强 |

## 2. 配置期望但当前缺失资产

| 配置键 | 期望文件 | 影响 |
| --- | --- | --- |
| `data.boundary_scope` | `data/shp/Boundary_Scope.geojson` | 研究范围边界与地图红线渲染受限 |
| `data.key_plots` | `data/shp/Key_Plots_District.json` | 地块级 MPI 与重点单元诊断受限 |
| `data.building_footprints` | `data/shp/Building_Footprints.geojson` | 建筑轮廓与三维可视化完整度受限 |
| `data.precise_points` | `data/Changchun_Precise_Points.xlsx` | GVI 指标与点位合并分析受限 |

## 3. 台账维护规范

1. 新增数据必须登记：来源、时间、字段、版权/合规说明  
2. 每次重大更新记录版本：`vYYYYMMDD`  
3. 所有数据需映射至少一个消费模块（页面/引擎）  
