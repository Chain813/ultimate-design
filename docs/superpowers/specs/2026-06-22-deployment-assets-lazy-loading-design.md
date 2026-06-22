# 部署资产与懒加载优化设计

日期：2026-06-22

## 背景

当前 Streamlit 首页和 3D 数字孪生地图依赖多个静态资源。首页 `Study Area Map` 使用 `static/research_scope_2d_cropped.png`，3D 地图使用 `static/buildings.geojson`、`static/building_shadows.geojson`、`static/landuse.geojson`、`static/rail_clipped.geojson`、`static/road_clipped.geojson`、`static/road_syntax.geojson` 等资源。用户希望这些必备资源在云端链接中可用，同时避免首次打开页面时等待过久。

## 目标

- 确保首页和 3D 地图运行必需的静态资产被部署，不出现图片或地图图层缺失。
- 明确排除 `static/atlas` 中的 PPT、几十 MB 效果图、图册级大图，避免部署包和页面加载过重。
- 优化首屏体验：用户通过链接进入网页时先看到首页内容，3D 地图资源在后台静默预取或按需加载。
- 保留 3D 地图的核心视觉资产：默认显示建筑、红线、重点地块，扩展图层可按用户操作逐步加载。
- 增加自动化检查，防止后续改动漏传运行必需资产。

## 非目标

- 不将 `static/atlas` 全量纳入线上部署。
- 不在首屏一次性加载所有 3D 地图图层。
- 不在云端启动时预热 RAG embedding 模型或重型 GeoPandas 统计。
- 不改动地图交互的核心视觉设计，只调整资源可用性和加载顺序。

## 资产分级

### Critical

首屏或基础运行立即需要的文件：

- `static/research_scope_2d_cropped.png`
- `static/03_digital_twin.png`
- `static/04_urban_diagnosis.png`
- `static/05_design_inference.png`
- `static/06_llm_consultation_v2.png`
- `static/boundary.geojson`
- `data/gis/Boundary_Scope.geojson`
- `data/gis/Key_Plots_District.json`

### Default Map

3D 地图默认体验需要，但不应阻塞首页首屏的文件：

- `static/buildings.geojson`
- `static/building_shadows.geojson`
- `data/gis/Building_Footprints.geojson`

### Optional Layers

用户切换对应图层时才需要的文件：

- `static/landuse.geojson`
- `static/rail_clipped.geojson`
- `static/road_clipped.geojson`
- `static/road_syntax.geojson`
- `static/water.geojson`
- `data/gis/landuse_clipped.geojson`
- `data/gis/rail_clipped.geojson`
- `data/gis/road_clipped.geojson`

### Excluded

不进入线上部署包的展示资产：

- `static/atlas/**/*.pptx`
- `static/atlas/**/*.png` 中的图册页、效果图和测试输出
- `static/atlas_enhanced/**`
- 本地导出、录屏、PSD、超大 ZIP 和原始数据包

## 加载设计

### 首页首屏

首页只渲染小型图片、摘要卡片、状态信息和轻量边界数据。`Study Area Map` 图片必须直接可访问，但不与 3D 地图大 GeoJSON 绑定。

### 服务器端预加载

现有 `start_preloading()` 需要增加云端轻量模式：

- 允许预热小配置、小 JSON、CSV 计数。
- 跳过 RAG embedding 模型加载。
- 跳过重型 GeoPandas 图层统计。
- 避免云端冷启动时 CPU 和内存被后台线程抢占。

本地演示仍可保留重型预热，但应通过配置或环境变量显式启用。

### 浏览器端静默预取

在首页渲染后注入一个轻量预取脚本：

- 使用 `requestIdleCallback`，浏览器空闲时预取 `Default Map` 资源。
- 不支持 `requestIdleCallback` 时使用短延迟 `setTimeout` 降级。
- 使用 `fetch(url, { cache: "force-cache" })` 触发浏览器缓存。
- 预取失败只写入控制台日志，不影响页面渲染。
- 预取清单只包含运行必需地图资产，不包含 `static/atlas`。

### 地图图层按需加载

`render_digital_twin_map()` 继续只把默认开启图层交给 Deck.GL。扩展图层保持现有按开关加载方式：

- 默认开启建筑、红线、重点地块。
- 默认关闭用地、道路、铁路、句法、街景质量等扩展层。
- 用户打开扩展层后由 Deck.GL 异步请求对应 GeoJSON。
- 资源已被后台预取时，Deck.GL 会从浏览器缓存读取，减少等待。

## 错误处理

- 如果必备静态文件缺失，自动化测试失败。
- 如果浏览器预取失败，不阻塞页面，只在控制台输出失败 URL。
- 如果 3D 图层请求 404，保留现有 `/app/static/` 到 `/static/` fallback。
- 如果云端缺少可选图层，图层开关不应导致整页崩溃，应显示当前图层加载失败提示。

## 测试方案

- 新增部署资产测试，检查 Critical、Default Map、Optional Layers 中要求部署的文件存在。
- 检查关键部署资产没有被 `.gitignore` 排除到无法提交。
- 检查 `static/atlas` 大文件不被列入必备部署清单。
- 补充预取清单测试，确保清单包含 3D 默认资源且不包含 atlas 路径。
- 运行相关 pytest 测试和启动烟测，确认改动没有破坏首页导入。

## 成功标准

- 线上首页 `Study Area Map` 图片正常显示。
- 3D 地图默认建筑资产可显示。
- `static/atlas` PPT 和几十 MB 效果图不参与部署。
- 首屏不等待 RAG 模型、重型 GeoPandas 统计或全量扩展图层下载。
- 自动化测试能在缺少关键资源时失败，防止漏传。
