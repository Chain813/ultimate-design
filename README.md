<h1 align="center">长春铁北微更新循证决策系统</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-Framework-FF4B4B.svg" alt="Streamlit">
  <img src="https://img.shields.io/badge/Modern-UI%2FCSS-818cf8.svg" alt="UI">
  <img src="https://img.shields.io/badge/AIGC-Stable%20Diffusion-purple.svg" alt="AIGC">
  <img src="https://img.shields.io/badge/LLM-Gemma%204-green.svg" alt="LLM">
</p>

## 🏙️ 项目简介

**Ultimate Design** 是一个针对长春伪满皇宫周边历史街区开发的**多模态城市微更新决策支持平台**。平台深度整合了 **3D 空间数字孪生**、**计算机视觉 (CV)** 与 **生成式大模型 (AIGC/LLM)** 技术，旨在通过多源大数据（街景、社媒、交通、POI 等）的跨尺度融合，为更新潜力评估、风貌修复及多主体博弈提供循证科研支撑。

---

## ✨ 核心功能实验室

### 1. 📊 资产综合评估与策略提取
- **MPI 指标体系**: 基于 AHP 层次分析法的多维度更新潜力评估，支持动态权重调节与排行榜实时生成。
- **语义萃取引擎**: 集成 Microsoft MarkItDown，实现对规划文档 (PDF/Word) 的跨模态语义解析。

### 2. 🌐 数字孪生与全息诊断
- **3D 交互沙盘**: 基于 PyDeck 构建，支持 GVI/SVF 空间指标、POI 密度及交通潮汐的 3D 可视化映射。
- **全要素叠加**: 实现历史锚点、路网脉冲与社会情感评价的地理全息对齐。

### 3. 🎨 AIGC 设计推演
- **生成式影像推演**: 利用 Stable Diffusion + ControlNet 技术，实现对历史街区建筑立面与公共空间的定向设计预演。
- **规划算子调控**: 实时调节景观介入度、历史锚定力等核心算子。

### 4. ⚖️ LLM 博弈协同决策
- **多主体协商**: 引入 Gemma 4 本地大模型，模拟“居民、开发商、政府”三方利益相关者的动态博弈与共识达成。

---

## 📂 工业级模块化架构

```text
ultimateDESIGN/
├── app.py                      # 系统主入口 (精简逻辑版)
├── pages/                      # 多页面模块中心 (已对齐数据同步逻辑)
├── src/                        # 核心源代码包
│   ├── engines/                # 核心引擎 (CV, LLM, Spider, Core Engine)
│   ├── ui/                     # UI 组件库 & CSS 动态加载器
│   └── utils/                  # 坐标转换及通用工具脚本
├── data/                       # 数据资产 (English Named)
│   ├── shp/                    # 核心地理矢量 asset (GeoJSON/JSON)
│   └── streetview/             # 街景分析圖像 (已通过 .gitignore 屏蔽)
├── docs/                       # 项目说明与审计报告
├── tools/                      # 离线批量处理与环境自检工具
└── .gitignore                  # GitHub 入库精细化忽略配置
```

---

## 🚀 快速启动指南

### 1. 环境构建
```bash
git clone https://github.com/yourusername/ultimateDESIGN.git
cd ultimateDESIGN
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
playwright install chromium
```

### 2. 外部引擎准备 (必选)
本平台依赖以下外部 API 服务以实现全功能体验：
- ** Stable Diffusion API**: 运行 WebUI 时需开启 `--api` 模式（默认端口 7860）。
- ** Ollama (LLM)**: 需下载并运行模型 `ollama run gemma4:e2b-it-q4_K_M`（默认端口 11434）。

### 3. 启动平台
```bash
streamlit run app.py
```

### 4. 环境变量
请先复制 `.env.example` 为 `.env`，并填写本地密钥（不要提交 `.env`）。

### 5. 贡献流程（开发 -> 检查 -> 提交）
```bash
# 1) 安装依赖
pip install -r requirements.txt

# 2) 启用本地提交前检查（仅需一次）
pre-commit install

# 3) 开发并本地验证
ruff check .
pytest -q
python tools/startup_smoke.py

# 4) 提交（会自动触发 pre-commit）
git add .
git commit -m "your message"
```

CI 会在远端并行执行 `lint`、`test`、`smoke` 三项检查，请确保本地先通过。

---

## ⚠️ 开发者注意事项

> [!IMPORTANT]
> **关于规划文档 (*.pdf)**: 
> 出于合规与体积考虑，本仓库不包含原始规划 PDF 文档。若需启用 Page 1 的“策略语义萃取”功能，请手动将相关的规划 PDF 文件放置于项目根目录的 `docs/` 文件夹下。

> [!TIP]
> **3D 地图 Token**: 
> 3D 模型渲染依赖 Mapbox/PyDeck 基础样式，请确保本地网络能够访问相应的基础底图服务。

> [!NOTE]
> 更完整的开发规范、数据目录约定、模型服务依赖与排障流程见 `docs/DEVELOPER_GUIDE.md`。
> 项目结构优化说明见 `docs/PROJECT_STRUCTURE.md`。
> 逐公式逐流程的详细技术说明见 `docs/PROJECT_DETAILED_SPEC.md`。
> 论文附录版（符号表、参数表、复现实验、失败案例）见 `docs/PROJECT_APPENDIX.md`。

---

## 📄 许可证与使用声明
本项目仅用于学术科研演示与毕业设计展示，严禁将内部算法组件直接用于商业营利性规划项目。
