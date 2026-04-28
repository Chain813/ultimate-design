# 🏙️ UltimateDESIGN

**Urban-design decision support platform for micro-renewal around the Puppet Manchukuo Palace area in Changchun.**

UltimateDESIGN is a Streamlit application for urban-planning coursework, graduation design, and research presentation. It organizes the project around a **13-stage urban-design workflow** and separates planning documents, spatial analytics, street-view survey images, AIGC simulation, LLM negotiation, and final deliverables into clear modules.

## 🧭 At A Glance

| Icon | Keyword | Description |
| --- | --- | --- |
| 🧩 | 13-stage workflow | Professional urban-design process mapped into page routes |
| 🗺️ | Data foundation | Planning briefs, GeoJSON, POI, traffic, and street-view data |
| 🔎 | Diagnosis | Spatial indicators, street-view metrics, and plot-level assessment |
| 🧠 | AI collaboration | Stable Diffusion, Ollama/Gemma, RAG, and stakeholder negotiation |
| 🖼️ | Deliverables | Scenario images, drawing prompts, planning text, and Word export |

## 🧱 Modules

| Module | Stages | Page |
| --- | --- | --- |
| 🟦 Early Data Acquisition and Existing Condition Analysis | 01-05 | `pages/01_前期数据获取与现状分析.py` |
| 🟨 Mid-term Concept Generation and Strategy Response | 06-07 | `pages/02_中期概念生成与应对策略.py` |
| 🟩 Late Design Generation and Result Presentation | 08-13 | `pages/03_后期设计生成与成果表达.py` |

## 🧰 Functional Pages

| Icon | Page | Responsibility |
| --- | --- | --- |
| 🚶 | `pages/04_现场调研.py` | Field survey page backed by `data/streetview/Point_x/heading_*.jpg` |
| 📚 | `pages/11_数据底座与规划策略.py` | Planning documents, spatial assets, and MPI evaluation |
| 🗺️ | `pages/12_现状空间全景诊断.py` | 3D existing-condition scene and plot-level diagnosis |
| 🎨 | `pages/13_AIGC设计推演.py` | Stable Diffusion based visual design simulation |
| 🤝 | `pages/14_LLM博弈决策.py` | RAG, multi-stakeholder negotiation, and drawing prompt assistant |
| 📦 | `pages/15_更新设计成果展示.py` | Future scenario map, planning text, image gallery, and Word export |

In-page navigation cards were removed. Users navigate between modules through the top navigation bar.

## 📁 Repository Layout

```text
ultimateDESIGN/
├─ 🏠 app.py                       # Streamlit home page and platform status
├─ 🧭 pages/                       # Streamlit pages
├─ 🧬 src/
│  ├─ ⚙️ config/                   # Paths, config loading, runtime helpers
│  ├─ 🧠 engines/                  # Spatial, diagnostic, RAG, LLM, AIGC engines
│  ├─ 🎛️ ui/                       # App shell, design system, chart theme
│  ├─ 🧰 utils/                    # Text IO, document export, service checks
│  └─ 🧩 workflow/                 # 13-stage workflow and route mapping
├─ 🎨 assets/
├─ 🗃️ data/
├─ 📄 docs/
├─ 🛠️ tools/
└─ ✅ tests/
```

## 🧠 Core Naming

| Icon | Module | Responsibility |
| --- | --- | --- |
| 🧭 | `src/ui/app_shell.py` | Global CSS, top navigation, shell-level status alerts |
| 🧩 | `src/workflow/city_design_workflow.py` | 13-stage workflow and stage-to-module routing |
| 🧠 | `src/engines/engine_registry.py` | Stable aggregate import surface for page code |
| 🗺️ | `src/engines/spatial_engine.py` | POI, street-view, skyline, and spatial statistics |
| 🔎 | `src/engines/site_diagnostic_engine.py` | Plot-level diagnosis and strategy matrix |
| 🎨 | `src/engines/stable_diffusion_engine.py` | Stable Diffusion WebUI requests |
| ✍️ | `src/engines/drawing_prompt_engine.py` | Drawing prompt generation rules |

## 🚀 Run

```powershell
pip install -r requirements.txt
streamlit run app.py
```

Open:

```text
http://localhost:8501/
```

## 🧪 Verification

```powershell
python -m compileall app.py pages src tests tools
pytest
python tools/check_env.py
python tools/startup_smoke.py
```
