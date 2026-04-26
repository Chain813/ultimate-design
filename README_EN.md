# Changchun Puppet Manchukuo Palace Area Micro-renewal Decision Platform

This repository contains a Streamlit-based decision support platform for evidence-based urban micro-renewal research. The current study area is the neighborhood around the Puppet Manchukuo Palace in Changchun, China.

The latest refactor aligns the whole product around a shared UI system: page banners, compact summary cards, section intros, consistent Streamlit controls, and shared Plotly chart themes.

## Modules

| Page | Module | Main capabilities |
| --- | --- | --- |
| Home | System console | Navigation, runtime status, project boundary, workflow overview |
| 01 | Data foundation and planning strategy | task brief/proposal workspace, MPI scoring, spatial asset inventory |
| 02 | Existing condition diagnosis | 3D base map, multi-layer spatial diagnosis, plot-level radar charts |
| 03 | AIGC design inference | image generation, planning controls, before/after comparison, session gallery |
| 04 | LLM negotiation | RAG policy retrieval, five-stage reasoning workflow, stakeholder negotiation |
| 05 | Design result showcase | master plan, design guidelines, image gallery, Word document export |

## Repository Layout

```text
ultimateDESIGN/
├── app.py                         # Streamlit home page
├── pages/                         # 01-05 Streamlit business pages
├── src/
│   ├── config/                    # paths and runtime config
│   ├── engines/                   # spatial, AIGC, RAG, LLM and diagnostic engines
│   ├── ui/
│   │   ├── design_system.py       # shared page layout primitives
│   │   ├── chart_theme.py         # shared Plotly palette and themes
│   │   └── ui_components.py       # navigation, engine status and compatibility exports
│   └── utils/                     # document export, service checks and utilities
├── assets/                        # CSS, 3D map HTML and visual assets
├── data/                          # sanitized tables, GeoJSON and metadata
├── static/                        # static files served by Streamlit
├── tools/                         # data processing and smoke-test scripts
├── tests/                         # unit tests
└── docs/                          # local planning documents, ignored by Git by default
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for the detailed maintenance guide.

## Quick Start

Python 3.10 to 3.12 is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

The app can run in a lightweight demo mode without local AI services. Real-time image generation and LLM negotiation require optional local engines.

## Optional AI Engines

| Engine | Usage | Default endpoint |
| --- | --- | --- |
| Stable Diffusion WebUI | Page 03 real-time visual generation | `http://127.0.0.1:7860` |
| Ollama / Gemma | Page 04 stakeholder negotiation | `http://127.0.0.1:11434` |

Stable Diffusion WebUI must be started with `--api`. For Ollama:

```powershell
ollama run gemma4:e2b-it-q4_K_M
```

## Validation

```powershell
python -m py_compile app.py src/ui/design_system.py src/ui/chart_theme.py src/ui/ui_components.py
python -m pytest tests/ -q
python tools/startup_smoke.py
```

## GitHub Notes

The repository is configured to keep source code, sanitized tables, GeoJSON assets, static UI assets and tests. Local runtime folders, logs, PDF documents and large raw imagery are ignored by default. See [GITHUB_UPLOAD_GUIDE.md](GITHUB_UPLOAD_GUIDE.md).

## License and Usage

This project is intended for academic research, coursework and graduation design demonstration. Planning documents and spatial/social datasets should be used according to their source permissions and privacy constraints.
