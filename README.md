<p align="right">
  <a href="#readme-en">English</a> | <strong>中文</strong>
</p>

<h1 align="center">🏙️ UltimateDESIGN</h1>
<h3 align="center">长春伪满皇宫周边街区微更新决策支持平台</h3>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10~3.12-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-1.38-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/LLM-Ollama%20%2F%20Gemma-8A2BE2" alt="LLM">
  <img src="https://img.shields.io/badge/AIGC-Stable%20Diffusion-green" alt="AIGC">
  <img src="https://img.shields.io/badge/License-Academic-orange" alt="License">
</p>

<p align="center">
  面向城乡规划毕业设计与城市更新研究的循证式工作流平台。<br/>
  围绕长春伪满皇宫周边街区，将任务书、开题报告、空间数据、AIGC 图景推演、LLM 多主体协商和成果展示整合为一套完整的决策支持系统。
</p>

---

## ✨ 功能亮点

- 📊 **数据底座** — MPI 更新潜力评估、空间数据资产清单、任务书/开题报告智能资料台
- 🗺️ **现状诊断** — 3D 现状底座、建筑/地块/POI/交通/街景品质多图层叠加、地块雷达诊断
- 🎨 **AIGC 推演** — 基于 Stable Diffusion 的空间图景生成、Before/After 对比、历史图集
- 🤖 **LLM 博弈** — RAG 政策检索、五阶段循证推演、多主体协商、共识雷达可视化
- 📋 **成果展示** — 设计总图、导则文本、效果图集、Word 文档一键导出

## 📸 模块预览

| 数据底座与规划策略 | 现状空间全景诊断 | AIGC 设计推演 |
|:-:|:-:|:-:|
| ![数据底座](assets/01_data_overview.png) | ![空间诊断](assets/04_urban_diagnosis.png) | ![AIGC推演](assets/05_design_inference.png) |

| LLM 博弈决策 | 更新设计成果展示 | 系统配置 |
|:-:|:-:|:-:|
| ![LLM博弈](assets/06_llm_consultation_v2.png) | ![成果展示](assets/02_strategy_library.png) | ![系统配置](assets/07_system_config_v2.png) |

---

## 🚀 快速启动

> **轻量演示模式** — 无需 GPU 或 AI 引擎，可直接查看首页、空间数据、3D 地图、诊断结果和成果展示。

### 环境要求

| 项目 | 轻量演示模式 | 全量本地模式 |
| --- | --- | --- |
| 操作系统 | Windows / macOS / Linux | Windows 10/11 优先 |
| Python | 3.10 ~ 3.12 | 3.10 ~ 3.12 |
| 内存 | ≥ 8 GB | ≥ 16 GB |
| GPU | 不需要 | NVIDIA RTX 3060 8GB+ |

### 安装与运行

```powershell
git clone https://github.com/Chain813/ultimateDESIGN.git
cd ultimateDESIGN

python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

streamlit run app.py
```

<details>
<summary>📌 国内网络加速</summary>

```powershell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```
</details>

<details>
<summary>📌 端口冲突处理</summary>

```powershell
streamlit run app.py --server.port 8502
```
</details>

启动后浏览器访问 → `http://localhost:8501`

---

## 🤖 可选 AI 引擎

如果需要 **第 03 页实时生图** 和 **第 04 页 LLM 多主体协商**，请额外启动以下服务：

| 引擎 | 用途 | 默认地址 | 启动方式 |
| --- | --- | --- | --- |
| Stable Diffusion WebUI | 第 03 页实时图景生成 | `http://127.0.0.1:7860` | 启动时需加 `--api` 参数 |
| Ollama / Gemma | 第 04 页 LLM 多主体协商 | `http://127.0.0.1:11434` | `ollama run gemma4:e2b-it-q4_K_M` |

<details>
<summary>🔧 Stable Diffusion WebUI 配置详情</summary>

- 本地服务地址: `http://127.0.0.1:7860`
- 启动参数必须包含 `--api`
- 推荐提前准备写实或建筑表现相关模型

```text
set COMMANDLINE_ARGS=--api
```

启动后可访问 `http://127.0.0.1:7860` 验证。

</details>

<details>
<summary>🔧 Ollama 配置详情</summary>

安装 Ollama 后运行：

```powershell
ollama run gemma4:e2b-it-q4_K_M
```

验证地址: `http://127.0.0.1:11434`

如果模型名称需要调整，可在第 04 页侧边栏修改模型标签。

</details>

> 💡 未启动 AI 引擎时，系统会显示离线提示，并尽量使用演示数据继续运行，不会崩溃。

---

## 📁 项目结构

```text
ultimateDESIGN/
├── app.py                          # Streamlit 首页与系统总台
├── pages/                          # 01-05 业务页面（文件名 = Streamlit 路由）
│   ├── 1_数据底座与规划策略.py
│   ├── 2_现状空间全景诊断.py
│   ├── 3_AIGC设计推演.py
│   ├── 4_LLM博弈决策.py
│   └── 5_更新设计成果展示.py
├── src/
│   ├── config/                     # 路径、运行配置、数据资产入口
│   │   ├── paths.py                # 数据/文档/静态资源路径注册
│   │   ├── loader.py               # 配置加载
│   │   └── runtime.py              # 运行时配置
│   ├── engines/                    # 空间分析、AIGC、RAG、LLM、诊断等领域引擎
│   │   ├── spatial_engine.py       # 空间测度
│   │   ├── diagnostic_engine.py    # 地块诊断与政策矩阵
│   │   ├── aigc_engine.py          # Stable Diffusion 调用
│   │   ├── rag_engine.py           # 政策知识库检索
│   │   ├── llm_engine.py           # Ollama 对话
│   │   └── core_engine.py          # 旧导入兼容出口
│   ├── ui/
│   │   ├── design_system.py        # 页面 Banner、Section Intro、摘要卡等统一布局
│   │   ├── chart_theme.py          # Plotly 色板与二维/雷达图主题
│   │   └── ui_components.py        # 顶部导航、引擎状态提示、兼容导出
│   └── utils/                      # 文档生成、服务探活、坐标转换、守护进程管理
│       ├── document_generator.py   # Word 成果导出
│       ├── service_check.py        # SD / Ollama 探活
│       ├── daemon_manager.py       # 本地守护进程控制
│       └── geo_transform.py        # 坐标转换 (BD09 → WGS84)
├── assets/                         # 全局 CSS、3D 地图 HTML、首页素材
├── data/                           # 脱敏指标表、GeoJSON、元数据文本
├── static/                         # Streamlit 静态文件 (大体积 GeoJSON)
├── tools/                          # 数据处理、质量检查、启动冒烟测试脚本
├── tests/                          # 单元测试
├── docs/                           # 本地规划资料与 PDF (默认不上传 GitHub)
├── config.yaml                     # 全局引擎与数据路径配置
├── requirements.txt                # Python 依赖
└── .github/                        # CI/CD 与 GitHub 协作模板
```

### UI 层约定

页面结构统一遵循 `Banner → 摘要卡 → 分段引导 → 工作面板` 模式：

```python
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.chart_theme import apply_plotly_theme, apply_plotly_polar_theme, get_chart_palette
from src.ui.ui_components import render_top_nav, render_engine_status_alert
```

### 数据路径约定

新增数据文件优先在 `src/config/paths.py` 中登记，避免页面硬编码路径。

---

## 🧪 开发与校验

```powershell
# 语法检查
python -m py_compile app.py src/ui/design_system.py src/ui/chart_theme.py src/ui/ui_components.py

# 单元测试
python -m pytest tests/ -q

# 启动冒烟测试
python tools/startup_smoke.py
```

CI 当前执行三类检查：`ruff` 关键错误扫描、密钥扫描、单元测试和启动冒烟测试。配置见 `.github/workflows/ci.yml`。

---

## 📦 GitHub 上传与部署

### 应上传的内容

| 类型 | 路径 |
| --- | --- |
| Streamlit 页面 | `app.py`, `pages/` |
| 核心代码 | `src/config/`, `src/engines/`, `src/ui/`, `src/utils/` |
| UI 和地图资源 | `assets/`, `static/` |
| 脱敏数据 | `data/*.csv`, `data/*.xlsx`, `data/shp/`, `data/meta/` |
| 工具与测试 | `tools/`, `tests/` |

### 不应上传的内容

项目 `.gitignore` 已默认排除以下内容：

| 类型 | 路径或规则 |
| --- | --- |
| 本地依赖环境 | `.venv/`, `.runtime-packages/` |
| 运行日志 | `*.log`, `*.err`, `*.err.log` |
| 本地密钥 | `.env` |
| 大体积原始影像 | `data/streetview/`, `data/raw_images/` |
| 本地规划资料 | `docs/`, `*.pdf` |

<details>
<summary>📌 推荐提交流程</summary>

```powershell
# 1. 提交前检查
git status --short
python tools/secret_scan.py
python -m pytest tests/ -q

# 2. 暂存并提交
git add app.py pages src assets data static tools tests .github .gitignore requirements.txt pyproject.toml pytest.ini config.yaml README.md
git commit -m "Update: description of changes"
git push
```
</details>

<details>
<summary>☁️ Streamlit Community Cloud 部署</summary>

1. 打开 [Streamlit Community Cloud](https://share.streamlit.io/)
2. 选择 GitHub 仓库
3. Main file path 填写 `app.py`
4. Python 依赖由 `requirements.txt` 自动安装
5. 云端无 GPU，第 03/04 页会以离线模式展示

| 检查项 | 预期 |
| --- | --- |
| 首页打开 | 能看到统一 Banner、模块入口和运行状态 |
| 01 页 | 能显示任务书/开题报告入口、MPI 表格 |
| 02 页 | 能显示 3D 底图或降级提示 |
| 03 页 | 无本地 SD 时不崩溃，有演示图或提示 |
| 04 页 | 无 Ollama 时显示引擎未就绪提示 |
| 05 页 | 能查看成果结构，可导出 Word |
</details>

---

## ❓ 常见问题

| 问题 | 处理方式 |
| --- | --- |
| `streamlit` 命令不存在 | 确认虚拟环境已激活，重新 `pip install -r requirements.txt` |
| 依赖安装慢 | 使用清华镜像：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple` |
| 第 03 页显示 SD 未就绪 | 确认 WebUI 已用 `--api` 启动并监听 7860 |
| 第 04 页显示 Gemma 未就绪 | 确认 Ollama 正在运行，且模型标签与侧边栏一致 |
| 页面找不到 PDF | `docs/` 是本地资料目录，GitHub 默认不上传 |
| 上传 GitHub 文件过大 | 检查是否误加入 `.runtime-packages/`、PDF 或原始影像 |

---

## 📜 使用声明

本项目用于学术研究、课程展示和毕业设计演示。项目中的规划资料、空间数据和社会感知数据应按来源授权和隐私要求使用，不建议直接用于商业决策。

---

---

<a id="readme-en"></a>

<p align="right">
  <strong>English</strong> | <a href="#top">中文</a>
</p>

<h1 align="center">🏙️ UltimateDESIGN</h1>
<h3 align="center">Changchun Puppet Manchukuo Palace Area — Micro-renewal Decision Support Platform</h3>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10~3.12-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-1.38-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/LLM-Ollama%20%2F%20Gemma-8A2BE2" alt="LLM">
  <img src="https://img.shields.io/badge/AIGC-Stable%20Diffusion-green" alt="AIGC">
  <img src="https://img.shields.io/badge/License-Academic-orange" alt="License">
</p>

<p align="center">
  An evidence-based workflow platform for urban micro-renewal research and graduation design.<br/>
  Integrates task briefs, spatial data, AIGC visual inference, LLM multi-stakeholder negotiation, and result showcase into a unified decision-support system.
</p>

---

## ✨ Highlights

- 📊 **Data Foundation** — MPI potential scoring, spatial asset inventory, and academic brief workspace
- 🗺️ **Spatial Diagnosis** — 3D base map with multi-layer overlays (building, plot, POI, traffic, street view quality), plot-level radar charts
- 🎨 **AIGC Inference** — Stable Diffusion-based design generation, before/after comparison, session gallery
- 🤖 **LLM Negotiation** — RAG policy retrieval, five-stage evidence-based reasoning, multi-stakeholder negotiation, consensus radar
- 📋 **Result Showcase** — Master plan, design guidelines, image gallery, one-click Word export

## Modules

| Page | Module | Main Capabilities |
| --- | --- | --- |
| Home | System console | Navigation, runtime status, project boundary, workflow overview |
| 01 | Data foundation & planning strategy | Task brief/proposal workspace, MPI scoring, spatial asset inventory |
| 02 | Existing condition diagnosis | 3D base map, multi-layer spatial diagnosis, plot-level radar charts |
| 03 | AIGC design inference | Image generation, planning controls, before/after comparison, session gallery |
| 04 | LLM negotiation | RAG policy retrieval, five-stage reasoning workflow, stakeholder negotiation |
| 05 | Design result showcase | Master plan, design guidelines, image gallery, Word document export |

---

## 🚀 Quick Start

```powershell
git clone https://github.com/Chain813/ultimateDESIGN.git
cd ultimateDESIGN

python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

streamlit run app.py
```

Open → `http://localhost:8501`

The app runs in a lightweight demo mode without local AI services. Real-time image generation (Page 03) and LLM negotiation (Page 04) require optional local engines:

| Engine | Usage | Default Endpoint |
| --- | --- | --- |
| Stable Diffusion WebUI | Page 03 visual generation | `http://127.0.0.1:7860` (start with `--api`) |
| Ollama / Gemma | Page 04 stakeholder negotiation | `http://127.0.0.1:11434` |

```powershell
ollama run gemma4:e2b-it-q4_K_M
```

---

## 📁 Repository Layout

```text
ultimateDESIGN/
├── app.py                          # Streamlit home page
├── pages/                          # 01-05 Streamlit business pages
├── src/
│   ├── config/                     # Paths and runtime configuration
│   ├── engines/                    # Spatial, AIGC, RAG, LLM, and diagnostic engines
│   ├── ui/                         # Shared UI system (banner, cards, chart themes)
│   └── utils/                      # Document export, service checks, utilities
├── assets/                         # CSS, 3D map HTML, and visual assets
├── data/                           # Sanitized tables, GeoJSON, and metadata
├── static/                         # Static files served by Streamlit
├── tools/                          # Data processing and smoke-test scripts
├── tests/                          # Unit tests
└── docs/                           # Local planning documents (ignored by Git)
```

## 🧪 Validation

```powershell
python -m py_compile app.py src/ui/design_system.py src/ui/chart_theme.py src/ui/ui_components.py
python -m pytest tests/ -q
python tools/startup_smoke.py
```

## GitHub Notes

The repository keeps source code, sanitized tables, GeoJSON assets, static UI assets, and tests. Local runtime folders, logs, PDF documents, and large raw imagery are ignored by default via `.gitignore`.

## 📜 License & Usage

This project is intended for academic research, coursework, and graduation design demonstration. Planning documents and spatial/social datasets should be used according to their source permissions and privacy constraints.
