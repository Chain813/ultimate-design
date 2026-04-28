[**English**](./README_EN.md) • [**简体中文**](./README.md) • [**🚀 快速启动**](./QUICK_START.md) • [**🔧 安装指南**](./INSTALL_GUIDE.md) • [**👶 新手教程**](./BEGINNER_GUIDE.md) • [**📖 核心术语**](./GLOSSARY.md) • [**☁️ GitHub部署**](./GITHUB_UPLOAD_GUIDE.md)

---

# UltimateDESIGN

**Micro-Renewal & Urban Design Decision Support Platform**

UltimateDESIGN is a Streamlit application designed for urban planning courses, graduation projects, and research presentations. The project strictly organizes pages according to **13 professional stages**, covering the complete evidence-based planning workflow from "pre-analysis" to "mid-term concept strategies" to "post-design detailing and export".

---

### 🌟 Core Features & Architecture

- **13-Stage Independent Workflow**
  Breaks down urban design into 13 standardized steps, each encapsulating independent functional panels, AI drawing prompt generation logic, and stage defense summaries.
- **41 Professional Drawing Templates**
  Built-in 41 prompt templates based on Stable Diffusion and ControlNet. The system automatically extracts spatial assets (e.g., building heights, POI vitality) to inject and format prompts.
- **Dynamic Defense Charts**
  Utilizes Plotly to automatically generate highly relevant analysis charts for the defense summaries of the 13 stages, including MPI renewal potential rankings, multi-agent consensus radars, and phased implementation Gantt charts.
- **LLM Evidence-Based Reasoning Logic**
  Deep integration with local Gemma models. Through a cross-stage data bus (`stage_data_bus`), it generates academic reasoning paragraphs that are free of "AI flavor" and rich in professional terminology with one click.
- **High-Speed Rendering & Fragment Refreshing**
  Employs time-based data format caching optimization (`@st.cache_data`), combined with JS asynchronous map mounting and Streamlit fragment redrawing (`@st.fragment`), ensuring silky-smooth interaction on a 150-hectare base.

---

### 🗂️ Core File Structure & Explanations

```text
UltimateDESIGN
├── app.py                       --- Home, platform status, global 2D/3D map base entry
├── pages/                       --- Core views: divided into Pre, Mid, and Post phases
│   ├── 01_任务解读.py             --- [Pre] Project overview, task requirements extraction
│   ├── 02_资料收集.py             --- [Pre] Semantic extraction engine, asset completeness
│   ├── 03_现场调研.py             --- [Pre] Street view sample library and retrieval
│   ├── 04_现状分析.py             --- [Pre] 3D base, POI aggregation, skyline analysis
│   ├── 05_问题诊断.py             --- [Pre] AHP-MPI model and plot diagnostic radar
│   ├── 06_目标定位.py             --- [Mid] LLM case benchmarking and vision extraction
│   ├── 07_设计策略.py             --- [Mid] Tripartite negotiation and RAG policy check
│   ├── 08_总体城市设计.py         --- [Post] AIGC conceptual master plan generation
│   ├── 09_专项系统设计.py         --- [Post] Transport/Space/Style/Culture specializations
│   ├── 10_重点地段深化.py         --- [Post] AIGC Before/After inference for 5 key plots
│   ├── 11_实施路径.py             --- [Post] Six renewal modes and 3-phase timeline
│   ├── 12_城市设计导则.py         --- [Post] Spatial control indicators and guideline export
│   └── 13_成果表达.py             --- [Post] 41 drawing templates overview and atlas export
├── src/                         --- Domain code: core logic and reusable components
│   ├── config/                  --- Static variables, path registration, config loading
│   ├── engines/                 --- Computation, LLM, AIGC logic (Strictly NO UI here)
│   ├── ui/                      --- Global shell, atomic design system, chart themes
│   ├── utils/                   --- IO ops, data conversion, text cleaning utilities
│   └── workflow/                --- 13-stage workflow mapping engine and data bus
├── assets/                      --- Frontend statics: CSS styles, HTML WebGL templates
├── data/                        --- Data warehouse: spatial base, tables, semantic cache
├── docs/                        --- Planning docs: task briefs, statutory policy materials
├── static/                      --- Network static resources exposed by Streamlit Server
├── tools/                       --- DevOps: environment checks and smoke test scripts
└── tests/                       --- Automated verification: Pytest unit tests
```

---

### 🚀 Quick Exploration

If you are new to this project, we recommend reading in the following order:
1. Go to **[🚀 快速启动](./QUICK_START.md)** for the simplest running commands.
2. Read **[👶 新手教程](./BEGINNER_GUIDE.md)** to understand how the urban design workflow maps to the system.
3. Refer to **[🔧 安装指南](./INSTALL_GUIDE.md)** to complete the local computational configuration for Gemma and SD.
