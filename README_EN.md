# UltimateDESIGN

**Urban-design decision support platform for micro-renewal around the Puppet Manchukuo Palace area in Changchun.**

UltimateDESIGN is a Streamlit application for urban-planning coursework, graduation design, and research presentation. It organizes the project into **13 independent stage pages** following the standard urban-design workflow. Each page integrates functional modules, data-driven drawing prompt generation, and thesis-defense-oriented stage summaries.

## Three Boards & 13 Stages

| Board | Stages | Pages |
| --- | --- | --- |
| Early | 01-05 | `pages/01_任务解读.py` ~ `pages/05_问题诊断.py` |
| Mid | 06-07 | `pages/06_目标定位.py` ~ `pages/07_设计策略.py` |
| Late | 08-13 | `pages/08_总体城市设计.py` ~ `pages/13_成果表达.py` |

## 13-Stage Page Overview

Every stage page includes: **Functional Modules** + **Drawing Prompt Generation** + **Stage Summary**.

| Stage | Page | Core Functions |
| --- | --- | --- |
| 01 | Task Interpretation | Project brief, task book / proposal display, location map prompts |
| 02 | Data Collection | Semantic extraction engine (PDF/Word→Markdown), spatial asset management |
| 03 | Field Survey | Street-view sample library (four-way photo retrieval) |
| 04 | Status Analysis | 3D holographic base overview, POI / building / skyline statistics |
| 05 | Problem Diagnosis | **AHP-MPI assessment** + **plot radar** + **AI diagnostic report** |
| 06 | Goal Positioning | **LLM case benchmarking** + **design concept extraction** (LLM Stages 2+3) |
| 07 | Design Strategy | **3-role negotiation** + **consensus radar** + **RAG policy check** (LLM Stage 4) |
| 08 | Overall Urban Design | Conceptual master plan AIGC generation |
| 09 | Specialized Systems | Axonometric simulation + traffic / public space / facade / cultural heritage overlays |
| 10 | Key Area Design | 5-type plot selection + AIGC street-view inference + Before/After |
| 11 | Implementation Path | 6 update categories + near/mid/long-term phasing plan |
| 12 | Design Guidelines | **LLM 5-stage guideline generation** + control indicators + Word export |
| 13 | Deliverables | **Full-workflow drawing prompt library (16+ templates)** + gallery + export center |

## Core Modules

| Module | Responsibility |
| --- | --- |
| `src/workflow/stage_data_bus.py` | Cross-stage data bus and evidence chain progress bar |
| `src/ui/module_summary.py` | Stage research summary panel (thesis-defense oriented) |
| `src/engines/drawing_prompt_templates.py` | 16+ data-driven drawing prompt template library |
| `src/engines/spatial_engine.py` | POI, street-view, skyline, and spatial statistics |
| `src/engines/site_diagnostic_engine.py` | Plot-level diagnosis and strategy matrix |
| `src/engines/llm_engine.py` | Ollama/Gemma calls and streaming output |

## Run

```powershell
pip install -r requirements.txt
streamlit run app.py
```

## Verification

```powershell
python -m compileall app.py pages src tests tools
pytest
```
