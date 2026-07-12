# Stage Layout Refactor Design

## Context

The Streamlit app currently keeps most stage pages as large single files under `pages/`. Most pages follow the same pattern: global navigation, page banner, `SUB_OPTIONS`, `resolve_subpage_value()`, then a long `if selected_sub == ...` branch for each subpage. This keeps the online route stable, but the internal structure is hard to maintain and the user experience is uneven across secondary pages.

The selected direction is a full structural refactor, with a compatibility layer so Streamlit Cloud links, `?sub=` URLs, stage bus keys, approval gates, artifact ids, and existing generated outputs continue to work.

## Goals

1. Convert each large stage page into a thin Streamlit entry file that delegates to a stage module.
2. Split each stage module into config, layout, actions, and subpage views.
3. Standardize secondary page and subpage structure around a workflow model: inputs, process, outputs, next step.
4. Preserve all public routes and existing `?sub=` values.
5. Preserve all existing `stage_bus` keys, artifact ids, approval records, and download flows.
6. Add compatibility tests so every migration batch is safe to push to `main`.

## Non-Goals

1. Do not rename files in `pages/`.
2. Do not change Streamlit page slugs.
3. Do not change the meaning of existing `stage_bus` keys.
4. Do not redesign the whole visual language from scratch.
5. Do not remove working features while migrating.

## Compatibility Contract

The refactor must keep these interfaces stable:

- `pages/00_数据准备与任务解读.py`
- `pages/02_资料收集与现场调研.py`
- `pages/04_现状分析与问题诊断.py`
- `pages/06_目标定位.py`
- `pages/07_设计策略.py`
- `pages/08_总体城市设计.py`
- `pages/09_专项系统设计.py`
- `pages/10_重点地段深化.py`
- `pages/11_实施路径.py`
- `pages/12_城市设计导则.py`
- `pages/13_成果表达.py`
- `pages/15_AIGC设计推演.py`
- `pages/16_制图与设计智能体Skill手册.py`

Each page file remains importable and keeps its route. The page file may shrink to a thin entry, but it still calls `st.set_page_config()`, `render_top_nav()`, `render_engine_status_alert()` when appropriate, and then calls a stage-level `render_page()` function.

Existing links such as `/设计策略?sub=共识雷达` and `/城市设计导则?sub=一键导出` remain valid through `resolve_subpage_value()` and existing alias matching.

## Target Architecture

Create a stage module tree:

```text
src/stages/
  __init__.py
  common/
    __init__.py
    workspace.py
    compatibility.py
  stage04_diagnosis/
    __init__.py
    config.py
    page.py
    actions.py
    views/
      __init__.py
      digital_twin.py
      mpi_assessment.py
      plot_radar.py
      ai_report.py
      resource_analysis.py
  stage07_strategy/
    __init__.py
    config.py
    page.py
    actions.py
    views/
      __init__.py
      negotiation.py
      consensus_radar.py
      design_brief.py
  stage12_guideline/
    __init__.py
    config.py
    page.py
    actions.py
    views/
      __init__.py
      section_generation.py
      indicators.py
      export.py
```

The same pattern then extends to `stage08_master_plan`, `stage09_systems`, `stage10_detail_design`, `stage11_implementation`, `stage13_outputs`, and tool pages.

## Shared Workspace Model

`src/stages/common/workspace.py` provides:

- `SubpageSpec`: label, title, description, output key, artifact category, aliases.
- `StageWorkspaceSpec`: stage code, title, description, subpages, evidence stages.
- `resolve_active_subpage()`: wraps `resolve_subpage_value()` and returns a `SubpageSpec`.
- `build_stage_workspace_html()`: pure HTML builder for testable navigation markup.
- `render_stage_workspace()`: Streamlit renderer for the workspace bar and active subpage summary.

The workspace bar appears under the page banner and above the evidence chain or first content section. It shows:

- Current stage code and name.
- Subpage navigation links.
- Active subpage title and description.
- Output target such as `stage_bus: 12_design_guideline`.
- Artifact target when the subpage produces a registered deliverable.

## Page Structure

Each migrated stage follows this page order:

1. `set_page_config()`
2. `render_top_nav()`
3. `render_engine_status_alert()` when the current page already uses it.
4. `render_page_banner()`
5. `render_stage_workspace()`
6. `render_evidence_chain_bar()`
7. Active subpage view.
8. `render_stage_summary()`

Each subpage view should be organized into visible sections:

- Input: upstream data, selected plot, model choice, dependencies.
- Process: analysis/generation controls.
- Output: generated content, downloads, artifact registration.
- Next step: downstream use or required approval.

## Data Flow

No data key changes are allowed during migration. Existing calls to these helpers remain valid:

- `save_stage_output()`
- `load_stage_output()`
- `render_dependency_gate()`
- `record_policy_review()`
- `register_artifact()`
- `register_report_output()`

Generated deliverables continue to be saved through the same keys in `src/workflow/stage_keys.py`. The newly added artifact registry becomes a read model over the same outputs; it must not replace `stage_bus` during this refactor.

## Migration Order

1. Build and test common workspace model.
2. Add CSS for workspace bar using new class names only.
3. Migrate Stage 12 because it is medium size and has clear subpages.
4. Migrate Stage 07 because it has complex logic and approval/artifact integration.
5. Migrate Stage 04, 08, 09, 10, 11, and 13 in small batches.
6. Migrate tool pages 15 and 16 after the core workflow is stable.
7. Keep the old page files as thin wrappers throughout.

## Testing Strategy

Add tests for:

- Subpage resolution with old aliases.
- Workspace HTML containing all subpage links.
- Stage 12 config preserving labels and keys.
- Stage 07 config preserving labels and keys.
- Thin page imports through existing startup smoke tests.
- Navigation routes through existing `test_navigation_routes.py`.
- Streamlit width compatibility through existing `test_streamlit_compat.py`.

Run after each migration batch:

```powershell
python -m pytest tests/test_stage_workspace.py tests/test_navigation_routes.py tests/test_startup_smoke.py tests/test_streamlit_compat.py -v
python -m ruff check src/stages pages tests
```

## Risk Controls

The refactor uses a compatibility-first migration:

- Keep page routes unchanged.
- Move one stage at a time.
- Preserve existing function bodies while moving them into view modules.
- Commit after each stage migration.
- Push only after smoke and navigation tests pass.
- If a migrated stage fails, revert that stage package and its thin wrapper without touching unrelated stages.

## Self-Review

Placeholder scan: no open placeholders remain.

Consistency check: the architecture, migration order, tests, and compatibility contract all preserve the same public routes and data keys.

Scope check: this is one large refactor, but it is decomposed into independently testable stage migrations.

Ambiguity check: the first implementation target is the common workspace plus Stage 12, followed by Stage 07.
