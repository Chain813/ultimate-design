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

## 🧭 页面命名

`pages/` 文件名直接影响 Streamlit 页面入口。当前采用两段编号：

| 编号 | 类型 | 说明 |
| --- | --- | --- |
| 🧩 `01-04` | 专业流程入口 | 对应城市设计 13 阶段的三大板块和现场调研 |
| 🧰 `11-15` | 功能模块页面 | 可被不同阶段挂载复用的具体功能 |

```text
pages/
├─ 01_前期数据获取与现状分析.py
├─ 02_中期概念生成与应对策略.py
├─ 03_后期设计生成与成果表达.py
├─ 04_现场调研.py
├─ 11_数据底座与规划策略.py
├─ 12_现状空间全景诊断.py
├─ 13_AIGC设计推演.py
├─ 14_LLM博弈决策.py
└─ 15_更新设计成果展示.py
```

## 🧩 13 阶段映射

| 阶段 | 阶段名称 | 所属板块 | 主要挂载功能 |
| --- | --- | --- | --- |
| 01 | 任务解读 | 前期数据获取与现状分析 | 任务书、开题报告、项目边界 |
| 02 | 资料收集 | 前期数据获取与现状分析 | 文档语义萃取、空间资产清单 |
| 03 | 现场调研 | 前期数据获取与现状分析 | 街景图、调研点、现场照片 |
| 04 | 现状分析 | 前期数据获取与现状分析 | 3D 现状底座、POI、街景指标 |
| 05 | 问题诊断 | 前期数据获取与现状分析 | 地块诊断、问题清单、诊断报告 |
| 06 | 目标定位 | 中期概念生成与应对策略 | 愿景目标、策略关键词、政策依据 |
| 07 | 设计策略 | 中期概念生成与应对策略 | 多主体协商、策略矩阵、图纸提示词 |
| 08 | 总体城市设计 | 后期设计生成与成果表达 | 总平面、空间结构、总体图景 |
| 09 | 专项系统设计 | 后期设计生成与成果表达 | 交通、绿地、公共服务等专项表达 |
| 10 | 重点地段深化 | 后期设计生成与成果表达 | 重点地块效果图和深化方案 |
| 11 | 实施路径 | 后期设计生成与成果表达 | 分期实施、更新时序、行动清单 |
| 12 | 城市设计导则 | 后期设计生成与成果表达 | 导则条文、管控图则、风貌控制 |
| 13 | 成果表达 | 后期设计生成与成果表达 | 图集、文本、Word 成果导出 |

## 🧬 源码目录职责

| 图标 | 路径 | 职责 | 维护规则 |
| --- | --- | --- | --- |
| ⚙️ | `src/config/` | 路径注册、配置加载、运行时定位 | 新增数据路径先登记在 `paths.py` |
| 🧠 | `src/engines/` | 空间、诊断、AIGC、RAG、LLM 等计算逻辑 | 不写 Streamlit UI，不直接渲染页面 |
| 🎛️ | `src/ui/app_shell.py` | 顶部导航、全局 CSS 注入、引擎状态提示 | 只放应用外壳层能力 |
| 🧱 | `src/ui/design_system.py` | Banner、分段标题、摘要卡等通用 UI | 页面复用组件优先沉淀到这里 |
| 📊 | `src/ui/chart_theme.py` | Plotly 配色、图表主题、透明底样式 | 页面不要重复手写图表主题 |
| 🧩 | `src/workflow/city_design_workflow.py` | 13 阶段、阶段资源、路由映射 | 阶段顺序和挂载关系只在这里维护 |
| 🧰 | `src/utils/` | 文本读取、文档导出、服务探测、坐标转换 | 放跨页面复用的非 UI 工具 |

## 🧠 引擎命名

| 图标 | 模块 | 功能边界 |
| --- | --- | --- |
| 🧭 | `engine_registry.py` | 聚合导出常用引擎函数，减少页面导入噪声 |
| 🗺️ | `spatial_engine.py` | POI、街景、天际线、地块和空间统计 |
| 🔎 | `site_diagnostic_engine.py` | 地块诊断、策略矩阵、问题判断 |
| 🎨 | `stable_diffusion_engine.py` | Stable Diffusion WebUI 请求和图像生成 |
| ✍️ | `drawing_prompt_engine.py` | 城市设计图纸提示词模板和生成规则 |
| 📚 | `rag_engine.py` | 本地知识库、向量检索、政策上下文召回 |
| 🤖 | `llm_engine.py` | Ollama/Gemma 调用、流式输出和提示词封装 |
| 💬 | `nlp_engine.py` | 社交文本清洗、情绪分析、词频统计 |
| 🕸️ | `social_media_crawler.py` | 社交平台抓取逻辑 |
| 🖼️ | `urban_image_segmentation.py` | 街景图像语义分割、GVI 等视觉指标 |

## 🎛️ 页面组织建议

新页面建议保持以下结构，便于读代码和维护：

```python
from src.ui.app_shell import render_top_nav
from src.ui.design_system import render_page_banner, render_section_intro

render_top_nav()
render_page_banner(...)
render_section_intro(...)

# 1. 读取数据
# 2. 组织控件
# 3. 调用 engine/utils
# 4. 渲染图表、表格、地图或结果
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
