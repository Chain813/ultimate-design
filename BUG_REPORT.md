# ultimateDESIGN Bug 报告

生成时间：2026-05-10 (第二次更新)

## 修复进展

- ✅ 已修复 BUG-001：`.env` 已清理真实凭据，扫描器已增加教程占位符白名单，扫描干净通过。
- ✅ 已修复 BUG-002：`tools/check_env.py` 已更新为当前 15 页面清单（含 00/14），发现缺失文件或依赖时返回非 0。已新增 6 个单元测试覆盖。
- ✅ 已修复 BUG-003：`requirements.txt` 已补充 `geopandas==1.1.3`。
- ✅ 已修复 BUG-004：`get_skyline_features()` 已改为先投影再计算建筑质心，并优先使用 `union_all()`。
- ✅ 已修复 BUG-005：`requirements.txt` 已统一升级至当前稳定运行版本，CI 已从 Python 3.10 升级至 3.12，消除双轨制风险。
- ✅ 已修复 BUG-006：新增 Streamlit 宽度兼容 helper，新版使用 `width="stretch"`，旧版回退 `use_container_width=True`。
- ✅ 已修复 BUG-007：两份建筑 GeoJSON 已补充稳定 `building_id`，数据质量检查已接受该字段。
- ✅ 已确认 BUG-008：重点地块 POI 覆盖为 0 确认为数据采集范围不足（非算法错误）。已增加覆盖诊断列，并提供扩展采集脚本。
- ✅ 已修复 BUG-009：`src/ui/app_shell.py` 的旧 UI/chart helper 重复实现已删除，保留兼容导出。
- ✅ 已修复 BUG-010：扩展 lint 中的未使用异常变量/循环变量已清理。
- ✅ 新增：DevOps 工具链测试全覆盖（check_env / secret_scan / startup_smoke / data_quality_check），CI 已集成环境诊断与数据质量检查。
- ✅ 新增：Git 历史泄漏审计完成，百度 AK 存在于 3 个历史提交中，需用 git filter-repo 清除。

## BUG-001：密钥扫描漏扫 `.env`，本地存在真实格式凭据

- 严重级别：高 → **已修复**
- 修复内容：
  1. `.env` 已重置为占位符格式 (`YOUR_BAIDU_MAP_AK` / `YOUR_DEEPSEEK_API_KEY`)。
  2. `.env.example` 已同步更新，包含 DEEPSEEK_API_KEY 占位符。
  3. `secret_scan.py` 新增 `KNOWN_SAFE_PATTERNS` 白名单，自动跳过教程代码中的占位 API Key。
  4. 扫描器现在对清理后的项目输出 `[OK] No obvious secrets found.`。
- ⚠️ Git 历史审计结果：百度地图 AK `W7iTpEM9...` 泄露于以下 3 个提交：
  - `fa5e76e` (Initial commit): `get_poi.py`、`get_traffic_poi.py` — 硬编码
  - `dd058a1`: `.env.example`、`get_poi.py`、`get_traffic_poi.py`
  - `8b71ca3`: `.env.example`
- DeepSeek Key 未被提交到 Git 历史。
- **后续操作**：需在百度地图开放平台轮换 AK，并使用 `git filter-repo` 从历史中移除泄露内容。

## BUG-005：本地验证环境与锁定依赖严重不一致

- 严重级别：中 → **已修复**
- 修复内容：
  1. `requirements.txt` 已全面升级至当前稳定运行版本（streamlit 1.55.0、pandas 2.3.3、numpy 2.4.3 等）。
  2. CI 配置 `.github/workflows/ci.yml` 已将 Python 从 3.10 升级至 3.12。
  3. CI 新增 `tools/check_env.py` 和 `tools/data_quality_check.py` 步骤。
  4. 167 个测试在统一环境下全部通过。

## BUG-008：重点地块 POI 覆盖统计显示 0

- 严重级别：中 → **已确认为数据覆盖问题**
- 诊断结论：
  - 农贸水产市场 / 食品大市场：完全超出 POI 数据纬度范围（地块纬度 43.906-43.908，POI 最大纬度 43.905）
  - 市一中北侧：边缘重叠但无 POI 落入
  - 清禾集贸市场 / 中国石油：bbox 内有少量候选但多边形精确匹配无命中
- 修复内容：
  1. `_count_poi_for_geometry()` 返回值扩展为 3 元组，新增 `coverage_note` 字段。
  2. 诊断卡新增「覆盖诊断」列，明确标注 "超出POI采集范围" / "范围内无POI命中" / "bbox有候选但多边形内无命中"。
  3. 新增 `scripts/fetch_expanded_poi.py` 扩展采集脚本，搜索范围扩大至 Lat 43.89-43.913，覆盖全部重点地块。
