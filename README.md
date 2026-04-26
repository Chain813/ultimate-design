# 长春伪满皇宫周边街区微更新决策支持平台

这是一个面向城乡规划毕业设计与城市更新研究的 Streamlit 应用。项目围绕长春伪满皇宫周边街区，把任务书、开题报告、空间数据、AIGC 图景推演、LLM 多主体协商和成果展示整合到一套循证式工作流中。

当前版本完成了 UI 与项目结构重构：页面统一为 `Banner + 摘要卡 + 分段引导 + 工作面板` 的表达方式，图表、卡片、按钮、输入控件和成果展示使用同一套设计系统。

## 核心模块

| 页面 | 模块 | 主要能力 |
| --- | --- | --- |
| 首页 | 系统总台 | 入口导航、运行状态、研究边界、模块导览 |
| 01 | 数据底座与规划策略 | 任务书与开题报告资料台、MPI 更新潜力评估、空间数据资产清单 |
| 02 | 现状空间全景诊断 | 3D 现状底座、建筑/地块/POI/交通/街景品质叠加、地块雷达诊断 |
| 03 | AIGC 设计推演 | 空间图景生成、规划参数控制、Before/After 对比、历史图集 |
| 04 | LLM 博弈决策 | RAG 政策检索、五阶段推演、多主体协商、共识雷达 |
| 05 | 更新设计成果展示 | 设计总图、导则文本、效果图集、Word 成果导出 |

## 项目结构

```text
ultimateDESIGN/
├── app.py                         # Streamlit 首页与系统总台
├── pages/                         # 01-05 业务页面，文件名同时承担 Streamlit 路由
├── src/
│   ├── config/                    # 路径、运行配置、数据资产入口
│   ├── engines/                   # 空间分析、AIGC、RAG、LLM、诊断等领域引擎
│   ├── ui/
│   │   ├── design_system.py       # 页面 Banner、Section Intro、摘要卡等统一布局组件
│   │   ├── chart_theme.py         # Plotly 色板与二维/雷达图主题
│   │   └── ui_components.py       # 顶部导航、引擎状态提示、兼容导出
│   └── utils/                     # 文档生成、服务探活、坐标转换、守护进程管理
├── assets/                        # 全局 CSS、3D 地图 HTML、首页素材
├── data/                          # 脱敏指标表、GeoJSON、元数据文本
├── static/                        # Streamlit 静态服务所需的大体积地图底图
├── tools/                         # 数据处理、质量检查、启动冒烟测试脚本
├── tests/                         # 单元测试
├── docs/                          # 本地规划资料与 PDF，默认不上传 GitHub
├── PROJECT_STRUCTURE.md           # 更详细的目录与维护说明
└── README_EN.md                   # English README
```

## 快速启动

建议使用 Python 3.10 到 3.12。Windows 用户可直接在项目根目录运行：

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

启动后访问：

```text
http://localhost:8501
```

如果只查看数据、地图、成果展示和演示内容，不需要启动本地 AI 服务。03 页和 04 页的实时生成能力需要额外挂载本地引擎。

## 可选 AI 引擎

| 引擎 | 用途 | 默认地址 |
| --- | --- | --- |
| Stable Diffusion WebUI | 第 03 页实时图景生成 | `http://127.0.0.1:7860` |
| Ollama / Gemma | 第 04 页 LLM 多主体协商 | `http://127.0.0.1:11434` |

Stable Diffusion WebUI 需要开启 `--api`。Ollama 可按项目默认配置运行：

```powershell
ollama run gemma4:e2b-it-q4_K_M
```

未启动这些服务时，系统会显示离线提示，并尽量使用演示数据继续运行。

## 开发与校验

```powershell
python -m py_compile app.py src/ui/design_system.py src/ui/chart_theme.py src/ui/ui_components.py
python -m pytest tests/ -q
python tools/startup_smoke.py
```

CI 当前执行三类检查：`ruff` 关键错误扫描、密钥扫描、单元测试和启动冒烟测试。配置见 `.github/workflows/ci.yml`。

## 数据与 GitHub 上传说明

仓库默认保留核心代码、脱敏表格、GeoJSON、前端素材和测试脚本。以下内容默认不上传：

- `.runtime-packages/`、`.venv/` 等本地依赖环境
- Streamlit 运行日志和错误日志
- `docs/` 中的规划 PDF 与任务资料
- `data/streetview/`、`data/raw_images/` 等大体积原始影像
- 所有 `*.pdf`

更详细的上传与部署说明见 [GITHUB_UPLOAD_GUIDE.md](GITHUB_UPLOAD_GUIDE.md)。

## 相关文档

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)：目录结构与维护边界
- [QUICK_START.md](QUICK_START.md)：快速启动路径
- [INSTALL_GUIDE.md](INSTALL_GUIDE.md)：本地环境和 AI 引擎部署
- [GITHUB_UPLOAD_GUIDE.md](GITHUB_UPLOAD_GUIDE.md)：GitHub 上传与 Streamlit Cloud 部署
- [README_EN.md](README_EN.md)：English overview

## 使用声明

本项目用于学术研究、课程展示和毕业设计演示。项目中的规划资料、空间数据和社会感知数据应按来源授权和隐私要求使用，不建议直接用于商业决策。
