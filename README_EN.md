<p align="center">
  <a href="README.md">简体中文 🇨🇳</a> | <a href="README_EN.md">English 🇬🇧</a>
</p>

<h1 align="center">Evidence-based Decision Support Platform for Changchun Tiebei Historic District Micro-renewal</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Subject-Urban%20Planning%20%2F%20Urban%20Science-blue.svg" alt="Subject">
  <img src="https://img.shields.io/badge/Methodology-Evidence--based%20%2F%20Multi--modal-FF4B4B.svg" alt="Methodology">
  <img src="https://img.shields.io/badge/Framework-Digital%20Twin%20%2F%20GenAI-818cf8.svg" alt="UI">
  <img src="https://img.shields.io/badge/Engines-Stable%20Diffusion%20%2F%20LLM-purple.svg" alt="Engines">
</p>

## 🏙️ Project Vision & Scientific Positioning

This platform (formerly the **ultimateDESIGN** Digital Twin System) is an **evidence-based spatial decision support system** developed for the micro-renewal of the Tiebei Historic District and the area surrounding the Puppet Emperor's Palace in Kuancheng District, Changchun.

The platform aims to solve the pain points of "subjective perception," "qualitative evaluation," and "opaque negotiation" in traditional urban renewal by integrating multi-source heterogeneous big data. By merging **3D Spatial Digital Twins**, **Computer Vision (CV)**, and **Large Generative Models (AIGC/LLM)**, it provides planners, government departments, and the public with a quantifiable and dynamic foundation for proposal pre-rendering and consensus building.

---

## ✨ Core Research Laboratory Modules

### 1. 📊 Spatial Asset Assessment (01 Strategy Lab)
- **MPI Index System (Multi-dimensional Potential Index)**: A multi-dimensional evaluation model based on AHP (Analytic Hierarchy Process). It converts expert qualitative experience into quantitative weights to scientifically classify the renewal potential of blocks.
- **Policy Semantic Extraction Engine**: Integrated cross-modal analysis algorithms to perform precise semantic dimensionality reduction and key guideline extraction from high-level protection planning texts (e.g., "Historic City Protection Regulations").

### 2. 🌐 Digital Twin & Holistic Diagnosis (02 Diagnosis Lab)
- **Multi-indicator Spatial Sandbox**: Built on a WebGL engine to achieve 3D holographic mapping of street quality factors such as Green View Index (GVI), Sky View Factor (SVF), and spatial enclosure.
- **Human-centric Factor Perception**: Integrates Gaode POI distribution, traffic tides, and social perception (UGC) sentiment extremes to construct a holistic urban map reflecting both "physical and social" attributes.

### 3. 🎨 Urban Character Pre-rendering (03 Simulation Lab)
- **Constraint-based Generative Pre-rendering**: Utilizes ControlNet to simulate the evolution of urban character under different repair interventions while preserving the skeletal texture of historic buildings.
- **Planning Operator Control Matrix**: Achieves parametric control of proposal generation by dynamically adjusting core operators such as landscape intervention and historical anchorage.

### 4. ⚖️ Stakeholder Consultation (04 Game Theory Lab)
- **Multi-agent Negotiation Simulation**: Introduces Large Language Models (LLM) to simulate dynamic interest conflicts among "Public Representatives, Market Investors, and Planning Experts."
- **Consensus Convergence Mechanism**: Based on a Policy RAG (Retrieval-Augmented Generation) mechanism, it automatically verifies the compliance of negotiation conclusions and generates final policy recommendations.

### 5. 🎯 Renewal Design Results Showcase (05 Presentation Lab)
- **Evidence-based Document Automation**: Aggregates data from all labs (measurement, inference, and consensus) to generate standardized Markdown/PDF administrative documents with one click.
- **4D Spatio-temporal Walkthrough**: Integrates "Retention-Renovation-Demolition" pipeline perspective and AIGC vision reconstruction to provide multi-scale digital delivery solutions for micro-renewal.

---

## 📂 Modular Architecture

```text
ultimateDESIGN/
├── app.py                      # System Control Console (Core Navigation & Status Monitoring)
├── pages/                      # 5 Core Labs (Asset/Diagnosis/Simulation/Game Theory/Presentation)
├── src/                        # Core Analytical Engine Package
│   ├── engines/                # Spatial Measurement, CV Semantic Extraction, NLP Sentiment Engines
│   ├── ui/                     # Unified Design System (Apple/Cyber Aesthetic)
│   └── utils/                  # Coordinate Transformation & Spatio-temporal Projection
├── data/                       # Data Foundation Assets
│   ├── shp/                    # Statutory Boundaries & Key Plot GeoJSONs
│   └── streetview/             # Captured Panoramic Imagery for CV Input
├── docs/                       # Academic Documents, Specifications, Legal Compilations
├── tools/                      # Environment Self-check & Data Quality Smoke Tests
└── .gitignore                  # Data Security & Privacy Anonymization Config
```

---

## 🚀 Deployment & Experience Guide

This project supports two execution modes to balance presentation convenience and computational integrity:

### 1. 🌐 Cloud Demo Mode
If accessing via Streamlit Community Cloud, the system automatically enters **Demo Mode**. Due to the lack of GPU power in the cloud, AIGC inference and LLM negotiations will display pre-rendered high-quality results, while map interactions and assessment algorithms remain 100% real-time.

### 2. 💻 Local Full-Power Mode (Local Perfect Experience)
To unlock real-time AIGC image generation and authentic LLM dialogues, please deploy locally.
(👉 **[Click here: Step-by-Step Newbie Guide](#newbie-guide-en)**)

- **Requirements**: NVIDIA RTX 3060 (8GB VRAM) or higher recommended.
- **Preparation**:
    1. Start [Ollama](https://ollama.com/) and run `gemma4:e2b-it-q4_K_M`.
    2. Start **Stable Diffusion WebUI** with the `--api` flag enabled.
- **Quick Start**:
    ```bash
    pip install -r requirements.txt
    streamlit run app.py
    ```

---

<a name="newbie-guide-en"></a>

## 🐣 Step-by-Step Newbie Guide

If you have zero programming knowledge, follow these steps to run the project on your computer:

### Step 1: Environment Preparation
1.  **Install Python**: Download from [Python.org](https://www.python.org/downloads/). **CRITICAL**: Check the box "Add Python to PATH" during installation.
2.  **Download the Code**: Click the green `Code` button at the top of this page -> `Download ZIP`. Extract it to a folder.

### Step 2: Install Dependencies
1.  Open your project folder. Hold `Shift` and right-click on an empty space, then select "Open PowerShell window here" or "Open in Terminal".
2.  Type the following command and press Enter:
    ```bash
    pip install -r requirements.txt
    ```

### Step 3: Start the AI Brain (Ollama)
1.  Install [Ollama](https://ollama.com/).
2.  After installation, open your terminal (Win+R, type cmd, Enter) and run:
    ```bash
    ollama run gemma4:e2b-it-q4_K_M
    ```
    *Wait for the model to download on the first run.*

### Step 4: Start the Visual Engine (Stable Diffusion)
1.  Ensure you have SD WebUI installed.
2.  **Crucial Setting**: Enable the "API" option in your launcher. If running manually, add `--api` to your `webui-user.bat` arguments.
3.  Launch it and ensure it's accessible in your browser.

### Step 5: Launch the Platform
Go back to the terminal from Step 2 and type:
```bash
streamlit run app.py
```
A browser window will open automatically with your Digital Twin platform.

---

## 📚 Advanced Documentation

If you wish to delve deeper into the underlying logic or obtain comprehensive deployment help, please refer to the following guides:
- ⚡ **[Quick Start Guide (3-minute demo)](QUICK_START.md)**: Includes both the lightweight and hardcore mode routes.
- 🖥️ **[Deep Installation & Deployment Guide](INSTALL_GUIDE.md)**: Detailed interpretation of the Python environment setup and local mounting of Stable Diffusion and Ollama.
- 📤 **[GitHub Upload & Cloud Deployment Guide](GITHUB_UPLOAD_GUIDE.md)**: A newbie-friendly guide for deploying to Streamlit Community Cloud.

---

## 🛠️ Core Development Components
- **Dynamic Geo-transform Utility** (`src/utils/geo_transform.py`): Integrated industrial-grade conversion algorithms for BD09 / GCJ02 / WGS84 to support multi-source data alignment.
- **AHP Decision Matrix**: Built into `pages/1_数据底座与规划策略.py`, supporting real-time recalculation of expert weights.
- **WebGL Rendering Pipeline**: Millisecond-level rendering of millions of building elements based on Deck.GL.

---

## ⚠️ Disclaimer

This project is for academic discussion, graduation project demonstration, and Changchun urban science research only. Data involves anonymized social perception info and Gaode API snapshots; commercial use is strictly prohibited.

---

**Evidence-based · Scientific Repair · Intelligent Decision**
