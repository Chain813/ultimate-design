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

## 🧰 Functional Pages & Sub-page Structures

The system abstracts the professional workflow into 5 core functional pages and 1 field survey page. Each page uses subpages and specific algorithmic modules (Functions) to host fine-grained design inference tasks.

### 🏠 Home / Entry (`app.py`)
- **Platform Status**: Displays underlying computing facilities (SD, Gemma), spatial measurement status, and data asset mounting radar.
- **Project Boundary**: Provides global 2D/3D base and layer controls to verify project boundaries.
- **Subsystem Navigation**: Provides routing into the 01-05 core research modules.

### 🚶 Field Survey (`pages/04_现场调研.py`)
- **Streetview Sample Library**: Reads the local `streetview` folder, providing coordinates and four-way (0/90/180/270 degrees) streetview photo retrieval based on survey points.

### 📚 Page 01: Data Foundation & Planning Strategy (`pages/11_数据底座与规划策略.py`)
- **Asset Assessment**: AHP weight configuration for expert judgment; real-time MPI update potential measurement and key plot rankings; MPI formula and scatter plots; CSV export.
- **Strategy Semantic Extraction**: Original reference desk for assignments and proposals; batch configuration and preview for converting PDF/Word to structured Markdown.
- **Physical Base Management**: Full spatial data asset inventory (boundaries, buildings, POI, street views) verification; one-click preview and data overlay upload.

### 🗺️ Page 02: Site Diagnostic Engine (`pages/12_现状空间全景诊断.py`)
- **3D Holographic Base**: Physical base (buildings, land use) layer control; social vitality (POI, traffic) overlay; street quality (GVI, SVF) 3D cylinder evaluation; free 3D/2D/roaming perspectives with simulated lighting.
- **Plot-level Diagnostic Panel**: Inherits MPI to provide potential rankings; radar charts for multi-dimensional evaluation and targeted intervention advice per plot; diagnostic report export (CSV).

### 🎨 Page 03: Block Facade Restoration Pre-rendering (`pages/13_AIGC设计推演.py`)
- **Plot-oriented Inference**: Select key update units and get strategy recommendations based on indicators.
- **Spatial Morphogenesis**: Supports block panoramic perspective inference (status restoration), conceptual master plan generation, and axonometric volume simulation.
- **Spatial Measurement & Parameters**: Provides ControlNet (Canny/MLSD/Depth/Seg) operators to constrain AI grids; advanced parameters for quality, sampling, and prompt correlation.
- **Input & Constraints**: Base map upload, rotation/cropping; built-in planning operators and two-stage strategy library; custom Prompt/Negative Prompt and denoising strength.
- **Generation & Comparison**: Interactive Before/After slider; local file download and session history gallery.

### 🤝 Page 04: Digital City Hall (`pages/14_LLM博弈决策.py`)
- **Multi-agent Negotiation**:
  - *Stage 1: Preliminary Analysis*: Converts core data into structured diagnostic reports.
  - *Stage 2: Benchmarking*: Connects external experience for case analysis reports.
  - *Stage 3: Design Concept*: Extracts overall design visions, goals, and strategies.
  - *Stage 4: Issue-Strategy Matching*: Based on RAG policy compliance pre-checks, launches 3-role (resident, developer, planner) smart negotiation.
  - *Stage 5: Spatial Outcome*: Automatically organizes the final graphic and text planning guidelines.
- **Dynamic Consensus Radar**: Visualizes core conflicts and consensus after trilateral negotiation.
- **Drawing Prompt Assistant**: Expert system for Image 2.0 drawing generation; provides information completeness checks and A/B/C/D graded prompt revisions.

### 📦 Page 05: Update Design Outcome Showcase (`pages/15_更新设计成果展示.py`)
- **Update Master Map**: Integrates restoration, functional transformation, and demolition/retention layers; supports underground pipeline X-Ray views.
- **Planning Text Outcomes**: Quick download of assignment/standard references; online display of general guidelines and implementation points; Word export of the guidelines with text and graphics.
- **Key Plot Renderings**: Manages session AIGC images and local outcome graphics; one-click history clearing.

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
