# Contributing to UltimateDESIGN

Thank you for your interest in contributing to the **UltimateDESIGN** Urban Platform! This project is maintained as an open, modular architectural design assistant.

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd urban-platform
   ```

2. **Setup virtual environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   > [!TIP]
   > The project uses `pyproject.toml` with dependency groups (e.g. `[dev]`, `[gis]`, `[gpu]`).

## Architecture Overview

UltimateDESIGN is built with a highly decoupled, plugin-based architecture:
- **Core Platform (`src/engines`)**: The main processing pipelines including `DrawingPipeline`, `SDEngine`, `LLMEngine`, and `QualityAssessor`.
- **UI System (`src/ui`)**: Built with Streamlit and features externalized SVG templates for the `design_system`.
- **Data Layers (`src/workflow`)**: Managed by the `stage_data_bus` to handle incremental outputs across 13 distinct urban design stages.

## Code Style & Linting

We enforce strict coding standards using `ruff`:
- Please ensure your code passes our linting rules before submitting a PR.
- The project is fully typed. We recommend running `mypy` against `src/` to verify type annotations.

## Submitting Pull Requests

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature-name`.
3. Ensure all tests pass: `python -m pytest tests/`.
4. Commit your changes with descriptive messages.
5. Push to your fork and submit a PR against `main`.

## Bug Reports & Feature Requests

Please use the issue tracker to report bugs or request new features. Ensure you provide:
- A clear, descriptive title.
- Steps to reproduce the bug.
- Expected behavior vs actual behavior.
- Relevant logs or stack traces.
