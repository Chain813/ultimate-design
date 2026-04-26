# Changchun Puppet Manchukuo Palace Area Micro-renewal Decision Platform

This repository contains a Streamlit-based decision support platform for evidence-based urban micro-renewal research. The current study area is the neighborhood around the Puppet Manchukuo Palace in Changchun, China.

The latest refactor aligns the whole product around a shared UI system: page banners, compact summary cards, section intros, consistent Streamlit controls, and shared Plotly chart themes.

## 📄 Documentation

- **[BEGINNER_GUIDE.md](BEGINNER_GUIDE.md): Super detailed guide for absolute beginners (Chinese).**
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md): Detailed repository layout and maintenance guide.
- [QUICK_START.md](QUICK_START.md): Fast-track to running the application.
- [INSTALL_GUIDE.md](INSTALL_GUIDE.md): Full installation guide including local AI engines.
- [GITHUB_UPLOAD_GUIDE.md](GITHUB_UPLOAD_GUIDE.md): Instructions for GitHub and Streamlit Cloud deployment.

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

## 🤖 Optional AI Engines

| Engine | Usage | Default endpoint |
| --- | --- | --- |
| Stable Diffusion WebUI | Page 03 real-time visual generation | `http://127.0.0.1:7860` |
| Ollama / Gemma | Page 04 stakeholder negotiation | `http://127.0.0.1:11434` |

Stable Diffusion WebUI must be started with `--api`. For Ollama:

```powershell
ollama run gemma4:e2b-it-q4_K_M
```

## 🧪 Validation

```powershell
python -m py_compile app.py src/ui/design_system.py src/ui/chart_theme.py src/ui/ui_components.py
python -m pytest tests/ -q
python tools/startup_smoke.py
```

## 📜 License and Usage

This project is intended for academic research, coursework and graduation design demonstration. Planning documents and spatial/social datasets should be used according to their source permissions and privacy constraints.
