[**English**](./README_EN.md) · [**简体中文**](./README.md)

<div align="center">

# UltimateDESIGN

**Digital Twin · Temporal Resonance — AI-Powered Urban Micro-Renewal Planning & Design Platform**

*Changchun Puppet Emperor's Palace District · 150 ha · 15 Modules · 41 Professional Drawings · End-to-End Evidence-Based Workflow*

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.55-FF4B4B?logo=streamlit)](https://streamlit.io)
[![Tests](https://img.shields.io/badge/Tests-167%20passed-brightgreen?logo=pytest)](./tests/)
[![License](https://img.shields.io/badge/License-Academic-orange)]()

</div>

---

## 🌟 Overview

UltimateDESIGN is a **full-stack Streamlit decision support platform** built for urban planning graduate design and studio coursework. Using a 150-hectare district surrounding Changchun's Puppet Emperor's Palace as its case study, the platform decomposes urban design into 15 standardized stages — from data preparation through site diagnostics, conceptual strategy, design detailing, to video presentation — forming a complete closed loop across **GIS data collection → LLM evidence-based reasoning → AIGC professional drawing generation → defense video production**.

---

## ✨ Key Capabilities

| Capability | Description |
|---|---|
| **15-Stage Workflow** | Each stage encapsulates independent data panels, AI reasoning, and defense charts |
| **41 Drawing Templates** | SD + ControlNet auto-injection of spatial assets for planning-standard outputs |
| **GIS → AIGC Alignment** | Novel Vector→Raster→ControlNet pipeline eliminates spatial hallucination |
| **Tri-Stakeholder Simulation** | LLM-driven Resident / Developer / Planner role-play with consensus radar output |
| **Dual Quality Loop** | Gemma visual + DeepSeek content assessment; auto-correction for C/D-rated outputs |
| **Versioned Atlas Export** | `VersionStore` full history + `BatchExporter` one-click 70+ drawing atlas |
| **HyperFrames Video** | One-click ~9 min defense video with 3D layered displays and GSAP animations |
| **167 Automated Tests** | Pytest + CI integration: lint / secret scan / smoke test / data quality check |

---

## 🚀 Quick Start

### 📦 1. Installation

```powershell
git clone https://github.com/Chain813/ultimate-design.git
cd ultimate-design

# Option A: Automated script (Windows)
.\scripts\setup_env.bat

# Option B: Manual
conda create -n gis_ai python=3.12 -y && conda activate gis_ai
pip install -r requirements.txt
```

### ▶️ 2. Launch

```powershell
streamlit run app.py
# or double-click run.bat
```

Navigate via the **top navigation bar**, stages `[00]` through `[14]`.

### 🩺 3. Health Check

```powershell
python -m pytest                    # 167 unit tests
python tools/check_env.py           # 15-page integrity check
python tools/secret_scan.py         # Credential leak scan
```

---

## 🖥️ Engine Integration

The platform runs all analytical features in CPU-only mode. To activate AIGC drawing and LLM reasoning:

### 🧠 LLM Engine (DeepSeek / Ollama)

```env
# .env
DEEPSEEK_API_KEY="<your-api-key>"
```

### 🎨 Visual Rendering (Stable Diffusion WebUI)

Launch SD WebUI with `--api --listen` flags on `127.0.0.1:7860`.

### 🗺️ GIS Asset Rasterization

```powershell
python scripts/render_gis_assets.py
```

Converts GeoJSON vector data into ControlNet guidance maps (road skeleton / landuse segmentation / satellite basemap) stored in `static/assets/generated_base/`.

---

## 🔄 Workflow Stages

### 🟢 Diagnostics (Stage 00–05)

| Stage | Page | Core Function |
|---|---|---|
| 00 | Data Preparation | 16-category upload, quality check, coordinate sync |
| 01 | Brief Interpretation | Task brief parsing, constraint extraction |
| 02 | Data Collection | Semantic extraction engine, asset completeness |
| 03 | Site Survey | 458-point × 4-direction street view library |
| 04 | Status Analysis | WebGL 3D building base, POI aggregation, skyline |
| 05 | Problem Diagnosis | AHP-MPI renewal potential ranking, radar diagnostics |

### 🟡 Strategy (Stage 06–07)

| Stage | Page | Core Function |
|---|---|---|
| 06 | Goal Setting | LLM case benchmarking (Xintiandi / King's Cross) |
| 07 | Design Strategy | Tri-stakeholder simulation, consensus radar |

### 🔴 Design & Delivery (Stage 08–14)

| Stage | Page | Core Function |
|---|---|---|
| 08 | Overall Urban Design | Spatial structure generation, Interactive landuse sandbox, AIGC masterplan |
| 09 | Specialized Systems | Transport & TOD / 15-min city / Skyline control / Heritage landscape planning |
| 10 | Key Plot Detailing | Radar diagnostics, Regulatory metrics, Micro-personas, Deep design schemes |
| 11 | Implementation Path | 6 renewal modes, 3-phase timeline Gantt chart |
| 12 | Design Guidelines | Two-step guideline generation + RAG policy retrieval |
| 13 | Output & Presentation | Python map rendering, Web LLM redraw prompts, Auto PIL title block |
| 14 | Video Generation | Dynamic data injection, storyboard script generation for screen recording |

---

## 🏗️ Project Structure

```text
ultimateDESIGN/
├── app.py                              # Entry point / Home / Global map base
├── pages/                              # 15 stage pages (00–14)
├── src/
│   ├── config/                         # YAML config / paths / runtime flags
│   ├── engines/                        # AI & computation (NO UI code)
│   │   ├── llm_engine.py              #   DeepSeek / Ollama unified API
│   │   ├── stable_diffusion_engine.py #   SDPipeline (txt2img / ControlNet)
│   │   ├── drawing_pipeline.py        #   End-to-end drawing orchestrator
│   │   ├── quality_assessor.py        #   Dual quality assessment
│   │   ├── spatial_engine.py          #   GIS parsing / MPI / skyline
│   │   └── ...                        #   (18 engine modules total)
│   ├── ui/                             # Streamlit components & theming
│   ├── utils/                          # I/O, geo transform, service checks
│   └── workflow/                       # 14-stage state machine & data bus
├── scripts/                            # Automation (data fetch / GIS render)
├── tools/                              # DevOps (env check / secret scan / QA)
├── tests/                              # 24 modules / 167 test cases
├── data/                               # Spatial & tabular assets (decoupled)
└── .github/workflows/ci.yml           # CI pipeline
```

---

## ⚙️ AIGC Pipeline Architecture

```
GeoJSON Vector Data                   Stable Diffusion WebUI
       │                                       ▲
       ▼                                       │
  render_gis_assets.py              ┌──────────┴──────────┐
  (Vector Rasterization)            │   ControlNet Units   │
       │                            │  • Canny (roads)     │
       ├── road_guidance.png ──────▶│  • Seg (landuse)     │
       ├── landuse_seg.png ────────▶│  • Tile (satellite)  │
       └── satellite.png ─────────▶│                      │
                                    └──────────┬──────────┘
  DrawingPipeline                              │
       ├── Prompt Build (41 templates)         ▼
       ├── Quality Assess (A/B/C/D)    Professional Drawing
       ├── Auto-Correct & Regenerate   (Spatially Aligned)
       └── VersionStore Archive
```

---

## 📚 Documentation

| Document | Description |
|---|---|
| [BUG_REPORT.md](./BUG_REPORT.md) | Known issues and fix log |
| [PROJECT_INSPECTION_REPORT.md](./PROJECT_INSPECTION_REPORT.md) | System architecture audit |
| [GLOSSARY.md](./GLOSSARY.md) | Terminology (MPI / GVI / ControlNet) |
| [README.md](./README.md) | 中文文档 |

---

<div align="center">
<sub>Built with Streamlit · Stable Diffusion · DeepSeek · GeoPandas · Plotly · HyperFrames</sub>
</div>
