# 🧱 项目结构与命名规范

本文档说明 UltimateDESIGN 重构后的目录职责、文件命名、模块边界和维护规则。目标是让后续开发者能快速判断：**功能应该放在哪里、页面如何命名、哪些文件不能随意改动**。

## 🗂️ 顶层结构

```text
ultimateDESIGN/
├─ 🏠 app.py                       # 首页、平台状态、全局入口
├─ 🧭 pages/                       # Streamlit 页面，文件名决定侧栏/路由顺序
├─ 🧬 src/                         # 可复用源码
│  ├─ ⚙️ config/                   # 路径、配置、运行时定位
│  ├─ 🧠 engines/                  # 领域计算引擎
│  ├─ 🎛️ ui/                       # UI 外壳、设计系统、图表主题
│  ├─ 🧰 utils/                    # 通用工具函数
│  └─ 🧩 workflow/                 # 城市设计 13 阶段流程映射
├─ 🎨 assets/                      # CSS、HTML 模板、展示资源
├─ 🗃️ data/                        # 空间数据、表格、街景、语义中间文件
├─ 📄 docs/                        # 本地规划资料、任务书、开题报告
├─ 🌐 static/                      # Streamlit 静态资源
├─ 🛠️ tools/                       # 数据处理和环境检查脚本
└─ ✅ tests/                       # 单元测试
```

## 🧭 页面命名与路由架构

`pages/` 下每个阶段对应一个独立 `.py` 文件，编号 01-13 严格对应城市设计工作流。

```text
ultimateDESIGN/
├─ 🏠 app.py                       # 首页入口：状态 HUD、2D/3D 基底控制
├─ 🧭 pages/
│  ├─ 01_任务解读.py               # 项目概况、任务书/开题报告、区位图提示词
│  ├─ 02_资料收集.py               # 语义萃取引擎、空间数据资产管理
│  ├─ 03_现场调研.py               # 街景样本库（四向照片检索）
│  ├─ 04_现状分析.py               # 3D 底座概览、POI/建筑/天际线统计
│  ├─ 05_问题诊断.py               # AHP-MPI 评估 + 地块雷达 + AI 诊断报告
│  ├─ 06_目标定位.py               # LLM 案例对标 + 设计理念提炼
│  ├─ 07_设计策略.py               # 三角色协商 + 共识雷达 + RAG 政策校验
│  ├─ 08_总体城市设计.py           # 概念总平面图 AIGC 生形
│  ├─ 09_专项系统设计.py           # 轴测推演 + 四大专项叠合 + 图纸生成
│  ├─ 10_重点地段深化.py           # 5 类地块选择 + AIGC 街景推演
│  ├─ 11_实施路径.py               # 六类更新方式 + 三期实施计划
│  ├─ 12_城市设计导则.py           # LLM 导则生成 + 管控指标 + Word 导出
│  └─ 13_成果表达.py               # 图纸提示词总览(41个模板) + 导出中心
```

## 🧩 13 阶段映射

| 阶段 | 页面 | 板块 | 核心功能 |
| --- | --- | --- | --- |
| 01 | 任务解读 | 前期 | 项目概况、任务书/开题报告、区位图提示词 |
| 02 | 资料收集 | 前期 | 语义萃取引擎（PDF/Word→Markdown）、数据资产管理 |
| 03 | 现场调研 | 前期 | 街景样本库、四向照片检索 |
| 04 | 现状分析 | 前期 | 3D 底座、POI 活力、建筑形态、天际线 |
| 05 | 问题诊断 | 前期 | AHP-MPI + 地块雷达 + AI 诊断 + 图纸提示词 |
| 06 | 目标定位 | 中期 | LLM 案例对标 + 设计理念（LLM 阶段二+三） |
| 07 | 设计策略 | 中期 | 三角色协商 + 共识雷达 + RAG 校验（LLM 阶段四） |
| 08 | 总体城市设计 | 后期 | 概念总平面图 AIGC 生形 |
| 09 | 专项系统设计 | 后期 | 轴测鸟瞰 + 交通/公共空间/风貌/历史文化专项 |
| 10 | 重点地段深化 | 后期 | 5 类重点地块 + AIGC 街景推演 + Before/After |
| 11 | 实施路径 | 后期 | 六类更新方式 + 近中远三期实施 |
| 12 | 城市设计导则 | 后期 | LLM 五阶段导则汇总 + 管控指标 + Word/Markdown 导出 |
| 13 | 成果表达 | 后期 | 全流程图纸提示词总览(41个模板) + 效果图管理 + 多格式导出 |

## 🧬 源码目录职责

| 图标 | 路径 | 职责 | 维护规则 |
| --- | --- | --- | --- |
| ⚙️ | `src/config/` | 路径注册、配置加载、运行时定位 | 新增数据路径先登记在 `paths.py` |
| 🧠 | `src/engines/` | 空间、诊断、AIGC、RAG、LLM 等计算逻辑 | 不写 Streamlit UI，不直接渲染页面 |
| 🎛️ | `src/ui/app_shell.py` | 顶部导航、全局 CSS 注入、引擎状态提示 | 只放应用外壳层能力 |
| 🧱 | `src/ui/design_system.py` | Banner、分段标题、摘要卡等通用 UI | 页面复用组件优先沉淀到这里 |
| 📊 | `src/ui/chart_theme.py` | Plotly 配色、图表主题、透明底样式 | 页面不要重复手写图表主题 |
| 🧩 | `src/workflow/city_design_workflow.py` | 13 阶段、阶段资源、路由映射 | 阶段顺序和挂载关系只在这里维护 |
| 🔄 | `src/workflow/stage_data_bus.py` | 跨阶段数据总线、证据链进度条 | 阶段间数据传递只通过此模块 |
| 📝 | `src/ui/module_summary.py` | 阶段研究小结面板（答辩导向） | 每个阶段页面底部必须调用 |
| 🧰 | `src/utils/` | 文本读取、文档导出、服务探测、坐标转换 | 放跨页面复用的非 UI 工具 |

## 🧠 引擎命名

| 图标 | 模块 | 功能边界 |
| --- | --- | --- |
| 🧭 | `engine_registry.py` | 聚合导出常用引擎函数，减少页面导入噪声 |
| 🗺️ | `spatial_engine.py` | POI、街景、天际线、地块和空间统计 |
| 🔎 | `site_diagnostic_engine.py` | 地块诊断、策略矩阵、问题判断 |
| 🎨 | `stable_diffusion_engine.py` | Stable Diffusion WebUI 请求和图像生成 |
| ✍️ | `drawing_prompt_engine.py` | 城市设计图纸提示词模板和生成规则 |
| 🖼️ | `drawing_prompt_templates.py` | **41 个数据驱动的图纸提示词模板库** |
| 📚 | `rag_engine.py` | 本地知识库、向量检索、政策上下文召回 |
| 🤖 | `llm_engine.py` | Ollama/Gemma 调用、流式输出和提示词封装 |
| 💬 | `nlp_engine.py` | 社交文本清洗、情绪分析、词频统计 |
| 🕸️ | `social_media_crawler.py` | 社交平台抓取逻辑 |
| 🖼️ | `urban_image_segmentation.py` | 街景图像语义分割、GVI 等视觉指标 |

## 🎛️ 页面组织建议

每个阶段页面遵循统一结构：

```python
from src.ui.app_shell import render_top_nav
from src.ui.design_system import render_page_banner, render_section_intro
from src.ui.module_summary import render_stage_summary
from src.workflow.stage_data_bus import save_stage_output, render_evidence_chain_bar
from src.engines.drawing_prompt_templates import get_templates_by_stage

render_top_nav()
render_page_banner(title=..., eyebrow="Stage XX", ...)
render_evidence_chain_bar("XX", [...])

# 1. 子页面 radio 选择
# 2. 功能模块（数据分析 / LLM 推演 / AIGC 生成）
# 3. 图纸提示词生成面板
# 4. render_stage_summary() — 底部答辩小结
```

## 🗃️ 数据路径约定

| 图标 | 路径 | 说明 |
| --- | --- | --- |
| 🗺️ | `data/shp/` | GeoJSON、地块、建筑、研究边界 |
| 🚶 | `data/streetview/` | 街景现场调研照片 |
| 🧾 | `data/meta/` | 语义萃取、政策摘录、阶段中间文本 |
| 📄 | `docs/` | 任务书、开题报告、规范 PDF、政策资料 |
| 🎨 | `assets/` | CSS、HTML 模板、展示图片 |
| 🌐 | `static/` | Streamlit 可直接访问的静态文件 |

## 🛠️ 维护规则

- 🧭 **导航唯一**：跨页面跳转只放在顶部导航栏。
- 🧩 **流程集中**：13 阶段顺序、阶段名称、资源映射只改 `city_design_workflow.py`。
- 🧠 **逻辑下沉**：计算和模型调用放进 `src/engines/`，页面只负责交互展示。
- 🎛️ **UI 复用**：通用样式和组件放进 `src/ui/`，不要在页面复制大段 CSS。
- 🗃️ **路径集中**：新增数据路径先改 `src/config/paths.py`。
- ✅ **验证优先**：改完至少跑编译、测试和环境检查。

```powershell
python -m compileall app.py pages src tests tools
pytest
python tools/check_env.py
python tools/startup_smoke.py
```
