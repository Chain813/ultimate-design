# ultimateDESIGN Bug 报告

生成时间：2026-05-01

## 修复进展

- 已修复 BUG-001：`.env` 现在会被扫描；发现风险时只输出文件和行号，不输出密钥内容。当前本地 `.env` 仍会让扫描失败，这是预期的安全拦截。
- 已修复 BUG-002：`tools/check_env.py` 已更新为当前 13 页面清单，发现缺失文件或依赖时返回非 0。
- 已修复 BUG-003：`requirements.txt` 已补充 `geopandas==1.1.3`。
- 已修复 BUG-004：`get_skyline_features()` 已改为先投影再计算建筑质心，并优先使用 `union_all()`。
- 已部分修复 BUG-008：重点地块 POI 覆盖统计已改为 point-in-polygon，只有缺少 GIS 依赖或几何异常时才回退 bbox。
- 已修复 BUG-006：新增 Streamlit 宽度兼容 helper，新版使用 `width="stretch"`，旧版回退 `use_container_width=True`。
- 已修复 BUG-007：两份建筑 GeoJSON 已补充稳定 `building_id`，数据质量检查已接受该字段。
- 已修复 BUG-009：`src/ui/app_shell.py` 的旧 UI/chart helper 重复实现已删除，保留兼容导出。
- 已修复 BUG-010：扩展 lint 中的未使用异常变量/循环变量已清理。
- 待处理 BUG-005：依赖版本整体锁定仍需单独决策，当前未把所有本地高版本依赖反写到 `requirements.txt`。

## BUG-001：密钥扫描漏扫 `.env`，本地存在真实格式凭据

- 严重级别：高
- 影响文件：`tools/secret_scan.py`、`.env`
- 证据：`python tools/secret_scan.py` 输出 `[OK] No obvious secrets found.`，但本地 `.env` 中存在真实格式的地图 AK 和 API Key。
- 根因：`tools/secret_scan.py:51` 仅按 `path.suffix.lower()` 判断扩展名；对 `.env` 来说 `Path(".env").suffix` 为空字符串，因此被跳过。
- 影响：安全扫描产生误报，开发者可能误以为本地环境文件已被检查。若 `.env` 被复制、打包或误提交，会增加泄露风险。
- 建议：显式允许 `path.name == ".env"`；同时只输出文件名和行号，不输出密钥片段。立即轮换本地 `.env` 中真实格式凭据。

## BUG-002：环境检查脚本引用过期页面路径，且发现错误仍返回 0

- 严重级别：高
- 影响文件：`tools/check_env.py`
- 证据：`python tools/check_env.py` 报告缺失 `pages/01_前期数据获取与现状分析.py` 等 9 个页面，但实际项目页面为 `pages/01_任务解读.py` 到 `pages/13_成果表达.py`。命令退出码仍为 0。
- 根因：`tools/check_env.py:70-88` 的 `critical_files` 清单与当前 13 页面结构不一致；`main()` 没有返回状态码，`__main__` 也没有 `sys.exit(main())`。
- 影响：新人环境检查会得到错误指引；CI 即使运行该脚本也不会失败。
- 建议：改用当前工作流注册表或动态读取 `pages/*.py`；缺失关键文件时返回 1。

## BUG-003：`requirements.txt` 缺少 `geopandas`，空间功能在新环境中会降级或失败

- 严重级别：高
- 影响文件：`requirements.txt`、`src/engines/spatial_engine.py`、`tools/clip_buildings.py`、`tools/prepare_landuse.py`、`tools/sync_building_landuse.py`
- 证据：`src/engines/spatial_engine.py:122` 和多个工具脚本直接导入 `geopandas`，但 `requirements.txt` 未声明该依赖。
- 影响：按 `pip install -r requirements.txt` 创建的新环境可能无法运行空间统计和地理处理工具。`get_skyline_features()` 会吞掉异常并返回 0 值，造成页面数据看似正常但实际失真。
- 建议：在依赖文件中声明 `geopandas` 及配套地理栈；或者将空间能力设为可选 extra，并在 UI 上显示明确的降级状态。

## BUG-004：空间统计在经纬度 CRS 下做 centroid/within，结果可能不准确

- 严重级别：中
- 影响文件：`src/engines/spatial_engine.py`
- 证据：`pytest` 和页面导入 smoke 均触发 GeoPandas warning：geographic CRS 下 `centroid` 结果可能不正确；代码位置为 `src/engines/spatial_engine.py:131`。
- 根因：建筑和边界没有先投影到米制 CRS，就直接 `buildings.centroid.within(boundary.unary_union)`。
- 影响：边界附近建筑筛选可能错误，进而影响建筑数量、平均高度、高层占比等 HUD 指标。
- 建议：读取后统一 CRS，投影到适合长春区域的投影坐标系再计算；同时将 `boundary.unary_union` 替换为 `boundary.union_all()`。

## BUG-005：本地验证环境与锁定依赖严重不一致

- 严重级别：中
- 影响文件：`requirements.txt`、`.github/workflows/ci.yml`
- 证据：当前 Python 为 3.14.2，CI 为 3.10；当前 `streamlit` 为 1.55.0，但 `requirements.txt` 锁定 1.38.0。`numpy`、`torch`、`transformers`、`plotly`、`pytest`、`ruff` 等也均高于锁定版本。
- 影响：本地 `pytest`/ruff/启动检查通过，不能完全证明项目在 README 或 CI 的安装环境中也通过。
- 建议：使用 `.venv` 或 CI 同款 Python 3.10 重跑检查；增加版本一致性检查，或更新并重新锁定依赖。

## BUG-006：Streamlit 新版本已提示 `use_container_width` 弃用

- 严重级别：中
- 影响文件：多处页面和 UI 组件
- 证据：页面导入 smoke 在 Streamlit 1.55.0 下输出：`Please replace use_container_width with width. use_container_width will be removed after 2025-12-31.`
- 影响：如果运行环境升级到较新 Streamlit，图表/表格/按钮相关调用会出现兼容性风险。
- 建议：按 Streamlit 新 API 将 `use_container_width=True` 迁移为 `width="stretch"`，将 `False` 迁移为 `width="content"`；如果继续锁定 1.38.0，则在 README 中明确不要混用全局 Python 环境。
- 修复：已新增 `src/ui/streamlit_compat.py`，所有调用点通过 `stretch_width()` 自动选择新旧参数。页面导入烟测确认不再出现 `use_container_width` 告警。

## BUG-007：建筑轮廓数据缺少可追踪标识字段

- 严重级别：中
- 影响文件：`data/shp/Building_Footprints.geojson`
- 证据：`tools/data_quality_check.py` 报告建筑轮廓 110289 个要素，评级 B，前 10 个 Feature 均缺少 `name`/`OBJECTID` 属性。
- 影响：问题定位、地块追踪、导出结果关联和增量更新会比较困难。
- 建议：为建筑轮廓补充稳定 ID 字段；如果源数据无法提供，则生成 `building_id` 并在数据质量脚本中把它纳入可接受字段。
- 修复：`data/shp/Building_Footprints.geojson` 和 `static/buildings.geojson` 已补充 `building_id`，`tools/data_quality_check.py` 已将其纳入稳定标识字段。

## BUG-008：重点地块 POI 覆盖统计使用 bbox，可能误判覆盖关系

- 严重级别：中
- 影响文件：`tools/data_quality_check.py`
- 证据：`tools/data_quality_check.py:210-229` 使用地块外包矩形过滤 POI，而非点在多边形内判断。
- 影响：凹多边形或不规则地块会被 bbox 过度覆盖，报告中的 POI 覆盖数可能偏高。当前报告中多个地块为 0 或极低覆盖，也需要复核是否为空间匹配口径导致。
- 建议：使用 `shapely`/`geopandas` 做 point-in-polygon，或者在报告中明确这是 bbox 粗筛结果。
- 修复：已改为 point-in-polygon 统计；仅在缺少几何依赖或几何异常时才标记为 `bbox_fallback`。

## BUG-009：`src/ui/app_shell.py` 旧 UI helper 被文件末尾导入覆盖

- 严重级别：低
- 影响文件：`src/ui/app_shell.py`
- 证据：扩展 ruff 检查报告 `F811`，`render_page_banner`、`render_section_intro`、`render_summary_cards`、`apply_plotly_theme` 等先在本文件定义，后又在 `src/ui/app_shell.py:491-502` 从 `chart_theme`/`design_system` 导入同名对象。
- 影响：维护者修改本文件旧实现时不会生效，容易产生误判。
- 建议：删除旧实现，保留兼容导出；或保留本文件实现并移除同名覆盖导入，保证单一来源。
- 修复：已删除旧的同名 UI/chart helper 实现，保留从 `design_system` 和 `chart_theme` 的兼容导出。

## BUG-010：扩展 lint 中存在若干未使用变量/循环变量

- 严重级别：低
- 影响文件：`app.py`、`src/engines/rag_engine.py`、`src/engines/social_media_crawler.py`、`tools/*`
- 证据：`python -m ruff check . --select F,B,PLE --ignore F401,F541` 报告 18 项，其中包括 `F841` 未使用异常变量和 `B007` 未使用循环变量。
- 影响：目前多为可维护性问题，不影响已跑通测试；但会降低后续错误处理清晰度。
- 建议：移除未使用变量或改为 `_`/`_exc`；对真正需要保留的兼容导出加精确 noqa，并补充说明。
- 修复：已清理扩展 lint 报告项，`python -m ruff check . --select F,B,PLE --ignore F401,F541` 通过。
