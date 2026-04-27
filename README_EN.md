# Changchun Puppet Manchukuo Palace Area Micro-renewal Decision Platform

This repository contains a Streamlit-based decision support platform for evidence-based urban micro-renewal research. The current study area is the neighborhood around the Puppet Manchukuo Palace in Changchun, China.

---

## 📁 Repository Structure

```text
ultimateDESIGN/
├── app.py                         # Main Streamlit entrance
├── pages/                         # Business modules (01-05 Evidence-based workflow)
│   ├── 1_Data_Foundation.py       # Data assets & planning brief
│   ├── 2_Spatial_Diagnosis.py     # 3D interactive conditioned environment
│   ├── 3_AIGC_Design.py           # Stable Diffusion based visual inference
│   ├── 4_LLM_Negotiation.py       # RAG-based stakeholder consensus model and drawing prompt assistant
│   └── 5_Result_Showcase.py       # Outcome compilation & export
├── src/                           # Core logic components
│   ├── config/                    # System paths & runtime configuration
│   ├── engines/                   # Engines: Spatial, AIGC, RAG, LLM, drawing prompt templates
│   ├── ui/                        # UI system: Shared components & themes
│   └── utils/                     # Utilities: Geo-transform, service checks
├── assets/                        # Static assets: CSS, HTML templates, workflow graphics, images
├── data/                          # Planning data foundation (GIS, POI, Tables)
├── tools/                         # Standalone utility scripts (Scrapers, indexers)
├── docs/                          # Local PDFs and planning documents (Git-ignored)
├── config.yaml                    # Global runtime configuration
└── requirements.txt               # Python dependencies
```

---

## 📖 Project Overview

**UltimateDESIGN** is an evidence-based digital platform designed for **Urban Planning** and **Architecture** students and researchers. It bridges the gap between raw spatial data and qualitative urban design decisions.

### 1. Research Background
Focusing on the historical neighborhood of the **Puppet Manchukuo Palace in Changchun**, the project addresses the complexities of urban renewal in heritage-sensitive areas. Traditional planning often suffers from fragmented data and subjective decision-making.

### 2. The Solution
The platform implements a **"Data Foundation + Evidence-based Diagnosis + AI Collaboration"** workflow:
- **Digital Twin Base**: Integrates multi-source spatial data (GIS, road networks, POIs, street view quality) into a 3D interactive conditioned environment.
- **Evidence-based Induction**: A 5-stage decision path from "Task Brief Analysis" to "Spatial Diagnosis" and finally "Multi-party Consensus."
- **AI-Driven Engines**:
    - **AIGC (Stable Diffusion)**: Transforms planning parameters into high-fidelity design renderings for instant visual feedback.
    - **LLM (Ollama/Gemma)**: Utilizes RAG (Retrieval-Augmented Generation) to search local policy documents and simulate negotiations between stakeholders (government, developers, residents).
- **Drawing Prompt Assistant**: Adds a ChatGPT Image 2.0 prompt workflow inside the LLM decision page. It combines atlas chapters, drawing types, precision levels, uploaded basemaps, legend rules, style rules and negative prompts into one copy-ready prompt.

---

## ✨ Key Features

1.  **📊 Data & Strategy**: Integration of task briefs, proposals, and the MPI potential assessment model.
2.  **🗺️ Spatial Diagnosis**: 3D map interaction with overlays for traffic, quality, and sentiment, including plot-level radar charts.
3.  **🎨 AIGC Design Inference**: Real-time generation of design scenarios using Stable Diffusion with before/after comparisons.
4.  **🤖 LLM Negotiation**: Simulated stakeholder博弈 based on localized policy knowledge bases.
5.  **📋 Showcase & Export**: Comprehensive gallery of design results and master plans with one-click Word report export.
6.  **🖼️ Drawing Prompt Assistant**: Generates ChatGPT Image 2.0 prompts for A3 atlases, A1 boards and presentation decks. It blocks high-precision drawings when required basemaps are missing and downgrades unsupported analysis drawings to visual-expression templates.

---

## 📄 Documentation

- **[GLOSSARY.md](GLOSSARY.md): Technical terms explained using Urban Planning & Architecture analogies.**
- **[BEGINNER_GUIDE.md](BEGINNER_GUIDE.md): Super detailed guide for absolute beginners (Chinese).**
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md): Detailed repository layout and maintenance guide.
- [QUICK_START.md](QUICK_START.md): Fast-track to running the application.
- [INSTALL_GUIDE.md](INSTALL_GUIDE.md): Full installation guide including local AI engines.
- [GITHUB_UPLOAD_GUIDE.md](GITHUB_UPLOAD_GUIDE.md): Instructions for GitHub and Streamlit Cloud deployment.

---

## 🚀 Quick Start

Python 3.10 to 3.12 is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open: `http://localhost:8501`

The app can run in a lightweight demo mode without local AI services. Real-time image generation and LLM negotiation require optional local engines.

---

## 🧪 Validation

```powershell
python -m py_compile app.py src/ui/design_system.py src/ui/chart_theme.py src/ui/ui_components.py
python -m pytest tests/ -q
python -m pytest tests/test_core_engine.py tests/test_image_prompt_engine.py -q
python tools/startup_smoke.py
```

## 📜 License and Usage

This project is intended for academic research, coursework and graduation design demonstration. Planning documents and spatial/social datasets should be used according to their source permissions and privacy constraints.
