# 🏙️ UltimateDESIGN

**长春伪满皇宫周边街区微更新与城市设计决策支持平台**

UltimateDESIGN 是一个面向城乡规划专业城市设计课程、毕业设计和研究展示的 Streamlit 应用。项目把城市设计工作拆解为 **13 个专业阶段**，并把资料读取、空间分析、现场调研、AIGC 图景推演、LLM 协商决策和成果表达整理成清晰的模块化页面。

> 当前版本强调“顶部导航直达功能”。页面主体不再放置二次跳转卡片，避免中转和重复入口。

## 🧭 快速理解

| 图标 | 关键词 | 说明 |
| --- | --- | --- |
| 🧩 | 13 阶段流程 | 按城乡规划专业城市设计工作流组织页面顺序 |
| 🗺️ | 数据底座 | 统一管理任务书、开题报告、GeoJSON、POI、交通和街景数据 |
| 🔎 | 现状诊断 | 基于空间指标、街景指标和地块信息生成诊断面板 |
| 🧠 | AI 协同 | 接入 Stable Diffusion、Ollama/Gemma、RAG 政策检索和多主体协商 |
| 🖼️ | 设计表达 | 生成图景推演、图纸提示词、规划文本和成果导出 |

## 🧱 三大板块与 13 阶段

```mermaid
flowchart LR
    A["🟦 前期数据获取与现状分析<br/>01-05"] --> B["🟨 中期概念生成与应对策略<br/>06-07"]
    B --> C["🟩 后期设计生成与成果表达<br/>08-13"]
```

| 板块 | 阶段 | 页面入口 |
| --- | --- | --- |
| 🟦 前期数据获取与现状分析 | 01 任务解读、02 资料收集、03 现场调研、04 现状分析、05 问题诊断 | `pages/01_前期数据获取与现状分析.py` |
| 🟨 中期概念生成与应对策略 | 06 目标定位、07 设计策略 | `pages/02_中期概念生成与应对策略.py` |
| 🟩 后期设计生成与成果表达 | 08 总体城市设计、09 专项系统设计、10 重点地段深化、11 实施路径、12 城市设计导则、13 成果表达 | `pages/03_后期设计生成与成果表达.py` |

## 🧰 功能页面

| 图标 | 页面 | 对应功能 |
| --- | --- | --- |
| 🚶 | `pages/04_现场调研.py` | 读取 `data/streetview/Point_x/heading_*.jpg`，展示现场调研点与四向街景照片 |
| 📚 | `pages/11_数据底座与规划策略.py` | 任务书、开题报告、语义萃取、空间资产清单、MPI 更新潜力测度 |
| 🗺️ | `pages/12_现状空间全景诊断.py` | 3D 现状底座、POI、街景指标、地块级诊断和空间评估 |
| 🎨 | `pages/13_AIGC设计推演.py` | Stable Diffusion 图景推演、街景修缮、总平面和轴测鸟瞰模拟 |
| 🤝 | `pages/14_LLM博弈决策.py` | RAG 政策检索、多主体协商、五阶段推演、图纸提示词生成 |
| 📦 | `pages/15_更新设计成果展示.py` | 留改拆总图、规划文本、重点地块效果图、Word 成果导出 |

## 📁 代码结构

```text
ultimateDESIGN/
├─ 🏠 app.py                       # Streamlit 首页、平台状态、总入口
├─ 🧭 pages/                       # Streamlit 页面，文件名影响路由顺序
├─ 🧬 src/
│  ├─ ⚙️ config/                   # 项目路径、数据路径、配置加载
│  ├─ 🧠 engines/                  # 领域引擎：空间、诊断、RAG、LLM、AIGC、提示词
│  ├─ 🎛️ ui/                       # 顶部导航、页面设计系统、图表主题
│  ├─ 🧰 utils/                    # 文本读取、文档导出、坐标转换、服务探测
│  └─ 🧩 workflow/                 # 13 阶段城市设计工作流与阶段路由映射
├─ 🎨 assets/                      # 全局 CSS、HTML 地图模板、展示资源
├─ 🗃️ data/                        # GeoJSON、CSV、街景图、语义中间文件
├─ 📄 docs/                        # 本地任务书、开题报告、规范和政策资料
├─ 🛠️ tools/                       # 数据抓取、清洗、压缩、环境检查脚本
├─ ✅ tests/                       # 单元测试
└─ 🌐 static/                      # Streamlit 静态资源目录
```

## 🧠 核心模块命名

| 图标 | 模块 | 职责 |
| --- | --- | --- |
| 🧭 | `src/ui/app_shell.py` | 全局 CSS 注入、顶部导航、引擎状态提示 |
| 🧩 | `src/workflow/city_design_workflow.py` | 13 阶段定义、阶段资源、顶部导航直达 URL |
| 🧠 | `src/engines/engine_registry.py` | 跨领域聚合导出，供页面按需使用 |
| 🗺️ | `src/engines/spatial_engine.py` | POI、街景、天际线、空间数据统计 |
| 🔎 | `src/engines/site_diagnostic_engine.py` | 地块诊断、策略矩阵、问题判断 |
| 🎨 | `src/engines/stable_diffusion_engine.py` | 本地 Stable Diffusion WebUI 调用 |
| ✍️ | `src/engines/drawing_prompt_engine.py` | 城市设计图纸提示词生成 |
| 📚 | `src/engines/rag_engine.py` | 政策文本向量检索和上下文召回 |
| 🤖 | `src/engines/llm_engine.py` | Ollama/Gemma 调用与流式输出 |
| 💬 | `src/engines/nlp_engine.py` | 社交文本情感和词频分析 |
| 🕸️ | `src/engines/social_media_crawler.py` | 社交平台抓取逻辑 |
| 🖼️ | `src/engines/urban_image_segmentation.py` | 街景图像语义分割和城市指标计算 |

## 🚀 启动

```powershell
pip install -r requirements.txt
streamlit run app.py
```

浏览器访问：

```text
http://localhost:8501/
```

## 🧪 验证

```powershell
python -m compileall app.py pages src tests tools
pytest
python tools/check_env.py
python tools/startup_smoke.py
```

## 🗃️ 数据说明

| 图标 | 路径 | 内容 |
| --- | --- | --- |
| 🗺️ | `data/shp/` | 研究边界、建筑底图、地块和空间 GeoJSON |
| 🚶 | `data/streetview/` | 现场调研街景图片，按 `Point_x/heading_*.jpg` 组织 |
| 🧾 | `data/meta/` | 任务书摘录、政策约束抽取、语义萃取中间结果 |
| 📄 | `docs/` | 本地 PDF、Markdown 规划资料、任务书和开题报告 |
| 🎨 | `assets/` | CSS、HTML 地图模板、页面展示资源 |

## 🛠️ 开发规则

- 🧭 页面跳转只放在顶部导航，页面主体不再放功能跳转卡片。
- 🧩 13 阶段流程只维护在 `src/workflow/city_design_workflow.py`。
- 🧠 计算逻辑放在 `src/engines/` 或 `src/utils/`，不要写进页面文件。
- 🎛️ 通用 UI 放在 `src/ui/`，页面内只保留必要交互和展示。
- 🗃️ 新增数据路径先登记在 `src/config/paths.py`。
- ✅ 修改后至少运行 `compileall`、`pytest` 和 `tools/check_env.py`。

## 📌 使用声明

本项目用于课程设计、毕业设计和学术研究展示。规划资料、街景数据和社会感知数据应按来源授权、隐私要求和学校/项目管理要求使用。
