# ultimateDESIGN 项目检查报告

生成时间：2026-05-01

## 1. 检查范围

本次检查覆盖项目结构、Python/Streamlit 运行入口、13 个页面、`src/` 核心模块、`tools/` 运维脚本、测试与 CI 配置、依赖环境、数据质量脚本、安全扫描脚本和本地启动能力。

未修改业务代码；仅运行检查命令并生成报告文件。

## 2. 项目概况

- 项目类型：Streamlit 城市设计决策支持平台。
- 主入口：`app.py`。
- 页面体系：`pages/01_任务解读.py` 到 `pages/13_成果表达.py`，共 13 个页面。
- 核心代码：`src/config/`、`src/engines/`、`src/ui/`、`src/utils/`、`src/workflow/`。
- 数据资产：`data/` 下包含 POI、交通、GVI、点位、GeoJSON、街景等数据。
- 自动化测试：`tests/` 下 12 个测试文件，当前共 61 个测试用例。
- CI：`.github/workflows/ci.yml` 已配置 lint、secret scan、unit tests、startup smoke。

## 3. 执行过的检查

| 检查项 | 命令 | 结果 |
| --- | --- | --- |
| 单元测试 | `python -m pytest` | 修复后通过，65 passed，2 third-party warnings |
| 项目默认 lint | `python -m ruff check .` | 通过 |
| 编译检查 | `python -m compileall -q app.py src pages tools` | 通过 |
| 依赖冲突检查 | `python -m pip check` | 通过 |
| 启动烟测 | `python tools/startup_smoke.py` | 通过 |
| 环境诊断 | `python tools/check_env.py` | 修复后通过，关键文件全部存在，退出码 0 |
| 密钥扫描 | `python tools/secret_scan.py` | 修复后拦截本地 `.env:1` 和 `.env:2`，不输出密钥内容 |
| 数据质量 | `python tools/data_quality_check.py` | 通过，建筑轮廓已升为 A，生成 `docs/STAGE2_DATA_QUALITY_REPORT.md` |
| 页面导入烟测 | 自定义 import smoke | 首页和 13 个页面全部导入成功 |
| Streamlit HTTP 启动 | `streamlit run app.py` 后探测 `127.0.0.1:8506` | 返回 HTTP 200 |
| 扩展 bug lint | `python -m ruff check . --select F,B,PLE --ignore F401,F541` | 发现 18 个潜在维护/代码质量问题 |

## 4. 正向结论

- 当前代码能编译，默认 ruff 规则通过。
- 单元测试全部通过，测试覆盖了 prompt 模板、引擎注册、异常、地理转换、LLM/RAG/NLP、空间引擎、服务检查等基础模块。
- 首页和 13 个 Streamlit 页面导入阶段无直接异常。
- 实际 Streamlit 服务可以拉起并返回 200。
- `pip check` 没有发现已安装包之间的 broken requirements。
- 数据质量脚本显示主要表格数据评级为 A。
- `secret_scan.py` 已能发现本地 `.env` 风险，输出不包含密钥内容。

## 5. 主要风险摘要

| 风险 | 级别 | 说明 |
| --- | --- | --- |
| 本地 `.env` 含真实格式凭据 | 高 | 扫描器已修复并会拦截；仍需轮换/移除本地凭据 |
| `tools/check_env.py` 使用过期页面清单且错误时仍返回 0 | 已修复 | 已更新当前 13 页面清单，并按检查结果返回退出码 |
| `requirements.txt` 缺少 `geopandas` 但代码依赖它 | 已修复 | 已补充 `geopandas==1.1.3` |
| 当前执行环境与 `requirements.txt` 锁定版本严重不一致 | 中 | 本次测试结果不能完全代表按 README/CI 安装后的环境 |
| 空间统计在经纬度 CRS 下计算 centroid | 已修复 | 已先投影再计算，相关测试已覆盖 |
| Streamlit 新版本提示 `use_container_width` 将移除 | 已修复 | 已用兼容 helper 自动选择 `width` 或旧参数 |
| 建筑轮廓 GeoJSON 缺少名称/对象 ID 属性 | 已修复 | 已补充 `building_id`，数据质量评级 A |
| `src/ui/app_shell.py` 保留旧实现又在文件末尾覆盖导入 | 已修复 | 已删除旧实现，保留兼容导出 |

## 6. 依赖环境观察

当前命令使用的解释器为 Python 3.14.2，而 CI 配置使用 Python 3.10。当前环境中多个包版本高于 `requirements.txt` 锁定值，例如：

- `streamlit`：要求 1.38.0，实际 1.55.0。
- `pandas`：要求 2.0.3，实际 2.3.3。
- `numpy`：要求 1.24.4，实际 2.4.3。
- `torch`：要求 2.2.2，实际 2.11.0。
- `transformers`：要求 4.41.2，实际 5.5.4。
- `plotly`：要求 5.24.1，实际 6.6.0。
- `pytest`：要求 8.3.3，实际 9.0.3。
- `ruff`：要求 0.6.9，实际 0.15.11。

建议使用项目虚拟环境或 CI 同款 Python 3.10 重新跑一遍完整检查，避免高版本依赖掩盖兼容性问题。

## 7. 数据质量结论

`tools/data_quality_check.py` 生成了 `docs/STAGE2_DATA_QUALITY_REPORT.md`，关键结果如下：

- POI：150 行，评级 A。
- 交通：125 行，评级 A。
- NLP 舆情：207 行，评级 A。
- GVI 环境品质：447 行，评级 A。
- 精确点位：458 行，评级 A。
- 研究范围边界：1 个要素，评级 A。
- 重点地块：5 个要素，评级 A。
- 建筑轮廓：110289 个要素，35.21 MB，评级 A，已补充稳定 `building_id`。

重点地块 POI 覆盖统计显示多个地块为 0 或极低覆盖，需要确认这是业务事实还是点位/范围匹配口径问题。

## 8. 测试与 CI 评估

现有测试能保证核心函数的基础行为，但有几个缺口：

- `tools/check_env.py` 没有测试，导致页面清单过期和退出码问题未被发现。
- `tools/secret_scan.py` 没有覆盖 `.env` 这类 dotfile。
- `get_skyline_features()` 的测试只断言返回类型和值为数值，不能防止缺少 `geopandas` 时空间指标悄悄变成 0。
- 启动 smoke 仅做 `py_compile`，不能覆盖 Streamlit 页面运行期 API 兼容性。
- CI 没有运行 `tools/check_env.py` 和 `tools/data_quality_check.py`，也没有检查依赖锁定版本是否被实际使用。

## 9. 建议修复优先级

1. 修复 `secret_scan.py` 对 `.env` 的漏扫，并立即轮换本地 `.env` 中真实格式的凭据。
2. 修复 `tools/check_env.py` 的页面清单，错误时返回非 0，加入 CI。
3. 明确地理依赖：把 `geopandas` 及其必要依赖加入安装文档/requirements，或在无依赖时给用户可见降级提示。
4. 修复 `get_skyline_features()` 的 CRS 处理：先投影到合适坐标系，再做 centroid/within；同时替换 `unary_union`。
5. 用 Python 3.10 和 `requirements.txt` 真实锁定版本重跑 `pytest`、ruff、smoke。
6. 处理 Streamlit `use_container_width` 弃用项，面向新版本改为 `width="stretch"`。
7. 清理 `src/ui/app_shell.py` 重复实现，保留单一来源。
8. 补充工具脚本测试，尤其是环境诊断、密钥扫描和数据质量报告退出码。
