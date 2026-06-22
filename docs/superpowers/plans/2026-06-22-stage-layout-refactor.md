# Stage Layout Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor Streamlit stage pages into thin route wrappers plus structured stage modules while preserving existing links, stage data keys, approval gates, and artifact outputs.

**Architecture:** Add a shared `src/stages/common/workspace.py` layer for secondary-page navigation and workflow context. Migrate stage pages incrementally into concrete packages such as `src/stages/stage12_guideline`, `src/stages/stage07_strategy`, and `src/stages/stage09_systems`, keeping all `pages/*.py` filenames as stable Streamlit route entrypoints.

**Tech Stack:** Python, Streamlit, pytest, ruff, existing `stage_data_bus`, `approval_state`, `artifact_registry`, and `resolve_subpage_value()`.

---

## File Structure

- Create `src/stages/__init__.py`: package marker for migrated stage modules.
- Create `src/stages/common/__init__.py`: package marker for shared stage UI helpers.
- Create `src/stages/common/workspace.py`: dataclasses, active subpage resolution, pure HTML builder, Streamlit renderer.
- Modify `assets/style.css`: append workspace bar classes with scoped `.stage-workspace-*` selectors.
- Create `tests/test_stage_workspace.py`: tests for subpage resolution and HTML generation.
- Create `src/stages/stage12_guideline/config.py`: Stage 12 metadata and subpage specs.
- Create `src/stages/stage12_guideline/page.py`: Stage 12 page orchestrator.
- Create `src/stages/stage12_guideline/actions.py`: Stage 12 non-UI helper actions for guideline registration.
- Create `src/stages/stage12_guideline/views/*.py`: Stage 12 subpage renderers.
- Modify `pages/12_城市设计导则.py`: thin wrapper that delegates to `src.stages.stage12_guideline.page.render_page()`.
- Create `tests/test_stage12_guideline_config.py`: config and compatibility tests.
- Repeat the same package pattern for Stage 07 after Stage 12 passes.

---

### Task 1: Add Shared Workspace Model

**Files:**
- Create: `src/stages/__init__.py`
- Create: `src/stages/common/__init__.py`
- Create: `src/stages/common/workspace.py`
- Test: `tests/test_stage_workspace.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_stage_workspace.py`:

```python
import streamlit as st


def setup_function():
    st.session_state.clear()
    st.query_params.clear()


def test_resolve_active_subpage_uses_query_param_alias():
    from src.stages.common.workspace import StageWorkspaceSpec, SubpageSpec, resolve_active_subpage

    spec = StageWorkspaceSpec(
        stage_code="12",
        title="城市设计导则",
        description="导则生成与导出",
        subpages=[
            SubpageSpec(label="📜 分板块导则生成", title="分板块导则生成"),
            SubpageSpec(label="📄 一键导出", title="一键导出", aliases=("导则导出",)),
        ],
    )
    st.query_params["sub"] = "导则导出"

    active = resolve_active_subpage(spec)

    assert active.label == "📄 一键导出"
    assert active.title == "一键导出"


def test_build_stage_workspace_html_contains_subpage_links_and_output_key():
    from src.stages.common.workspace import StageWorkspaceSpec, SubpageSpec, build_stage_workspace_html

    spec = StageWorkspaceSpec(
        stage_code="07",
        title="设计策略",
        description="多主体协同策略推演",
        subpages=[
            SubpageSpec(
                label="⚖️ 多主体协同推演",
                title="多主体协同推演",
                description="组织居民、开发商和规划师协同推演。",
                output_key="strategy_matrix",
                artifact_category="report",
            ),
            SubpageSpec(label="📊 共识雷达", title="共识雷达"),
        ],
    )

    html = build_stage_workspace_html(spec, spec.subpages[0])

    assert "Stage 07" in html
    assert "设计策略" in html
    assert "多主体协同推演" in html
    assert "共识雷达" in html
    assert "stage_bus: 07_strategy_matrix" in html
    assert "artifact: report" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests/test_stage_workspace.py -v
```

Expected: fail with `ModuleNotFoundError: No module named 'src.stages'`.

- [ ] **Step 3: Add the minimal implementation**

Create `src/stages/__init__.py`:

```python
"""Structured stage modules for Streamlit page refactors."""
```

Create `src/stages/common/__init__.py`:

```python
"""Shared helpers for structured stage pages."""
```

Create `src/stages/common/workspace.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from html import escape

import streamlit as st

from src.workflow import resolve_subpage_value


@dataclass(frozen=True)
class SubpageSpec:
    label: str
    title: str
    description: str = ""
    output_key: str = ""
    artifact_category: str = ""
    aliases: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class StageWorkspaceSpec:
    stage_code: str
    title: str
    description: str
    subpages: list[SubpageSpec]
    evidence_stages: tuple[str, ...] = field(default_factory=tuple)


def resolve_active_subpage(spec: StageWorkspaceSpec, default_index: int = 0) -> SubpageSpec:
    alias_map: dict[str, str] = {}
    for subpage in spec.subpages:
        for alias in subpage.aliases:
            alias_map[alias] = subpage.label
    labels = [subpage.label for subpage in spec.subpages]
    active_label = resolve_subpage_value(labels, default_index=default_index, aliases=alias_map)
    for subpage in spec.subpages:
        if subpage.label == active_label:
            return subpage
    return spec.subpages[default_index]


def build_stage_workspace_html(spec: StageWorkspaceSpec, active: SubpageSpec) -> str:
    nav_items = []
    for subpage in spec.subpages:
        cls = "stage-workspace-tab is-active" if subpage.label == active.label else "stage-workspace-tab"
        nav_items.append(
            f'<a class="{cls}" href="?sub={escape(subpage.label)}" target="_self">{escape(subpage.title)}</a>'
        )

    output_parts = []
    if active.output_key:
        output_parts.append(f"stage_bus: {escape(spec.stage_code)}_{escape(active.output_key)}")
    if active.artifact_category:
        output_parts.append(f"artifact: {escape(active.artifact_category)}")
    output_html = "".join(f'<span class="stage-workspace-meta-pill">{part}</span>' for part in output_parts)

    return (
        '<section class="stage-workspace-shell">'
        '<div class="stage-workspace-heading">'
        f'<span class="stage-workspace-code">Stage {escape(spec.stage_code)}</span>'
        f'<h2>{escape(spec.title)}</h2>'
        f'<p>{escape(spec.description)}</p>'
        "</div>"
        f'<nav class="stage-workspace-tabs">{"".join(nav_items)}</nav>'
        '<div class="stage-workspace-active">'
        f'<div><strong>{escape(active.title)}</strong><p>{escape(active.description)}</p></div>'
        f'<div class="stage-workspace-meta">{output_html}</div>'
        "</div>"
        "</section>"
    )


def render_stage_workspace(spec: StageWorkspaceSpec, default_index: int = 0) -> SubpageSpec:
    active = resolve_active_subpage(spec, default_index=default_index)
    st.markdown(build_stage_workspace_html(spec, active), unsafe_allow_html=True)
    return active
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m pytest tests/test_stage_workspace.py -v
```

Expected: `2 passed`.

- [ ] **Step 5: Commit**

```powershell
git add src/stages/__init__.py src/stages/common/__init__.py src/stages/common/workspace.py tests/test_stage_workspace.py
git commit -m "feat: add stage workspace model"
```

---

### Task 2: Add Scoped Workspace CSS

**Files:**
- Modify: `assets/style.css`
- Test: `tests/test_stage_workspace.py`

- [ ] **Step 1: Add a failing CSS assertion**

Append to `tests/test_stage_workspace.py`:

```python
def test_workspace_css_is_scoped_to_stage_workspace_classes():
    css = open("assets/style.css", encoding="utf-8").read()

    assert ".stage-workspace-shell" in css
    assert ".stage-workspace-tab.is-active" in css
    assert "h1 {" not in css[css.index(".stage-workspace-shell"):]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_stage_workspace.py::test_workspace_css_is_scoped_to_stage_workspace_classes -v
```

Expected: fail because `.stage-workspace-shell` is missing.

- [ ] **Step 3: Append scoped CSS**

Append this block to `assets/style.css`:

```css
/* --- Structured Stage Workspace --- */
.stage-workspace-shell {
    background: #ffffff !important;
    border: 1px solid rgba(0, 0, 0, 0.08) !important;
    border-radius: 20px;
    padding: 20px 24px;
    margin: 0 0 24px 0;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.02) !important;
}

.stage-workspace-heading {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 6px 14px;
    align-items: baseline;
    margin-bottom: 16px;
}

.stage-workspace-heading h2 {
    margin: 0 !important;
    padding: 0 !important;
    border-left: none !important;
    font-size: 1.25rem !important;
    line-height: 1.25 !important;
    letter-spacing: 0 !important;
}

.stage-workspace-heading p {
    grid-column: 1 / -1;
    margin: 0 !important;
    color: #6e6e73 !important;
    font-size: 0.95rem !important;
}

.stage-workspace-code {
    color: #0071e3 !important;
    font-size: 0.76rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase;
}

.stage-workspace-tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 16px;
}

.stage-workspace-tab {
    display: inline-flex;
    align-items: center;
    min-height: 36px;
    padding: 7px 12px !important;
    border-radius: 8px !important;
    border: 1px solid rgba(0, 0, 0, 0.08) !important;
    background: #f5f5f7 !important;
    color: #424245 !important;
    text-decoration: none !important;
    font-size: 0.88rem !important;
    font-weight: 650 !important;
}

.stage-workspace-tab.is-active {
    background: #0071e3 !important;
    border-color: #0071e3 !important;
    color: #ffffff !important;
}

.stage-workspace-active {
    display: flex;
    justify-content: space-between;
    gap: 18px;
    align-items: flex-start;
    padding-top: 14px;
    border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.stage-workspace-active strong {
    display: block;
    color: #1d1d1f !important;
    font-size: 0.95rem !important;
}

.stage-workspace-active p {
    margin: 4px 0 0 0 !important;
    color: #6e6e73 !important;
    font-size: 0.88rem !important;
}

.stage-workspace-meta {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 6px;
    min-width: 220px;
}

.stage-workspace-meta-pill {
    display: inline-flex;
    align-items: center;
    min-height: 26px;
    padding: 4px 8px;
    border-radius: 8px;
    background: rgba(0, 113, 227, 0.08);
    color: #0071e3;
    font-size: 0.74rem;
    font-weight: 700;
}

@media (max-width: 760px) {
    .stage-workspace-shell { padding: 16px; }
    .stage-workspace-active { flex-direction: column; }
    .stage-workspace-meta { justify-content: flex-start; min-width: 0; }
}
```

- [ ] **Step 4: Run tests and lint**

Run:

```powershell
python -m pytest tests/test_stage_workspace.py -v
python -m ruff check src/stages/common/workspace.py tests/test_stage_workspace.py
```

Expected: tests pass and ruff reports `All checks passed!`.

- [ ] **Step 5: Commit**

```powershell
git add assets/style.css tests/test_stage_workspace.py
git commit -m "style: add stage workspace layout"
```

---

### Task 3: Create Stage 12 Config and Actions

**Files:**
- Create: `src/stages/stage12_guideline/__init__.py`
- Create: `src/stages/stage12_guideline/config.py`
- Create: `src/stages/stage12_guideline/actions.py`
- Test: `tests/test_stage12_guideline_config.py`

- [ ] **Step 1: Write failing config tests**

Create `tests/test_stage12_guideline_config.py`:

```python
import streamlit as st


def setup_function():
    st.session_state.clear()
    st.session_state["stage_bus"] = {}
    st.query_params.clear()


def test_stage12_workspace_preserves_legacy_subpage_labels():
    from src.stages.stage12_guideline.config import STAGE12_WORKSPACE

    labels = [item.label for item in STAGE12_WORKSPACE.subpages]

    assert labels == ["📜 分板块导则生成", "📊 管控指标汇总", "📄 一键导出"]


def test_stage12_export_subpage_maps_to_design_guideline_output():
    from src.stages.stage12_guideline.config import STAGE12_WORKSPACE

    export = STAGE12_WORKSPACE.subpages[2]

    assert export.output_key == "design_guideline"
    assert export.artifact_category == "guideline"


def test_register_guideline_artifact_records_stage12_output():
    from src.stages.stage12_guideline.actions import register_guideline_artifact
    from src.workflow.artifact_registry import get_artifact

    register_guideline_artifact(total_sections=9, total_chars=1234)

    artifact = get_artifact("12:design_guideline")
    assert artifact["label"] == "城市设计导则"
    assert artifact["category"] == "guideline"
    assert artifact["metadata"] == {"sections": "9", "total_chars": "1234"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests/test_stage12_guideline_config.py -v
```

Expected: fail with `ModuleNotFoundError: No module named 'src.stages.stage12_guideline'`.

- [ ] **Step 3: Add Stage 12 config and action helper**

Create `src/stages/stage12_guideline/__init__.py`:

```python
"""Stage 12 structured page package."""
```

Create `src/stages/stage12_guideline/config.py`:

```python
from src.stages.common.workspace import StageWorkspaceSpec, SubpageSpec
from src.workflow.stage_keys import SK


STAGE12_WORKSPACE = StageWorkspaceSpec(
    stage_code="12",
    title="城市设计导则",
    description="分板块生成导则、汇总管控指标，并导出完整成果。",
    evidence_stages=("05", "06", "07", "12"),
    subpages=[
        SubpageSpec(
            label="📜 分板块导则生成",
            title="分板块导则生成",
            description="逐章生成城市设计导则正文，并汇总为完整导则。",
            output_key=SK.DESIGN_GUIDELINE,
            artifact_category="guideline",
            aliases=("分板块导则", "导则生成"),
        ),
        SubpageSpec(
            label="📊 管控指标汇总",
            title="管控指标汇总",
            description="查看容积率、高度、绿地率和街道界面等管控指标。",
            aliases=("指标汇总", "管控指标体系"),
        ),
        SubpageSpec(
            label="📄 一键导出",
            title="一键导出",
            description="导出已生成的完整城市设计导则。",
            output_key=SK.DESIGN_GUIDELINE,
            artifact_category="guideline",
            aliases=("导则导出", "导出"),
        ),
    ],
)
```

Create `src/stages/stage12_guideline/actions.py`:

```python
from src.workflow.artifact_registry import register_artifact
from src.workflow.stage_keys import SK


def register_guideline_artifact(total_sections: int, total_chars: int) -> dict:
    return register_artifact(
        stage_code="12",
        key=SK.DESIGN_GUIDELINE,
        label="城市设计导则",
        category="guideline",
        location="stage_bus",
        mime="text/markdown; charset=utf-8",
        metadata={"sections": str(total_sections), "total_chars": str(total_chars)},
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m pytest tests/test_stage12_guideline_config.py tests/test_stage_workspace.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/stages/stage12_guideline tests/test_stage12_guideline_config.py
git commit -m "feat: add stage 12 workspace config"
```

---

### Task 4: Migrate Stage 12 Into a Thin Wrapper

**Files:**
- Create: `src/stages/stage12_guideline/page.py`
- Create: `src/stages/stage12_guideline/views/__init__.py`
- Create: `src/stages/stage12_guideline/views/section_generation.py`
- Create: `src/stages/stage12_guideline/views/indicators.py`
- Create: `src/stages/stage12_guideline/views/export.py`
- Modify: `pages/12_城市设计导则.py`
- Test: `tests/test_startup_smoke.py`
- Test: `tests/test_navigation_routes.py`

- [ ] **Step 1: Write an import smoke test for the new page renderer**

Append to `tests/test_stage12_guideline_config.py`:

```python
def test_stage12_page_renderer_is_importable():
    from src.stages.stage12_guideline.page import render_page

    assert callable(render_page)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_stage12_guideline_config.py::test_stage12_page_renderer_is_importable -v
```

Expected: fail because `src.stages.stage12_guideline.page` does not exist.

- [ ] **Step 3: Create Stage 12 view modules**

Create `src/stages/stage12_guideline/views/__init__.py`:

```python
"""Stage 12 subpage renderers."""
```

Create each view module by moving the corresponding branch body from `pages/12_城市设计导则.py`:

- Move the existing `if selected_sub == "📜 分板块导则生成":` body into `views/section_generation.py` as `render_section_generation(model_tag: str) -> None`.
- Move the existing `elif selected_sub == "📊 管控指标汇总":` body into `views/indicators.py` as `render_indicators() -> None`.
- Move the existing `elif selected_sub == "📄 一键导出":` body into `views/export.py` as `render_export() -> None`.

Use this module header pattern for `views/section_generation.py`:

```python
import streamlit as st

from src.engines.llm_engine import call_llm_engine_stream
from src.engines.spatial_data_injector import get_full_spatial_context
from src.stages.stage12_guideline.actions import register_guideline_artifact
from src.ui.design_system import render_section_intro
from src.ui.streamlit_compat import stretch_width
from src.workflow.approval_state import StageDependency, render_dependency_gate
from src.workflow.stage_data_bus import load_stage_output, save_stage_output
from src.workflow.stage_keys import SK
```

When moving the guideline summary action, replace the inline `register_artifact(...)` call with:

```python
register_guideline_artifact(total_sections=total, total_chars=total_chars)
```

- [ ] **Step 4: Create Stage 12 page orchestrator**

Create `src/stages/stage12_guideline/page.py`:

```python
import streamlit as st

from src.stages.common.workspace import render_stage_workspace
from src.stages.stage12_guideline.config import STAGE12_WORKSPACE
from src.stages.stage12_guideline.views.export import render_export
from src.stages.stage12_guideline.views.indicators import render_indicators
from src.stages.stage12_guideline.views.section_generation import render_section_generation
from src.ui.app_shell import render_engine_status_alert, render_top_nav
from src.ui.design_system import render_page_banner
from src.ui.module_summary import render_stage_summary
from src.workflow.stage_data_bus import render_evidence_chain_bar


def render_page() -> None:
    render_top_nav()
    render_engine_status_alert()
    render_page_banner(
        title="城市设计导则",
        description=(
            "分板块深度生成：将导则拆分为多个专项模块，"
            "对每个模块注入真实空间数据并调用 DeepSeek-V4 Pro 展开。"
        ),
        eyebrow="Stage 12",
        tags=["分板块生成", "数据驱动", "管控条文", "Word 导出"],
    )

    with st.sidebar:
        model_tag = st.selectbox(
            "DeepSeek 模型",
            ["deepseek-v4-flash", "deepseek-v4-pro"],
            index=1,
            key="p12_model",
            help="城市设计导则建议使用 deepseek-v4-pro 确保深度与准确度",
        )

    active = render_stage_workspace(STAGE12_WORKSPACE)
    render_evidence_chain_bar("12", list(STAGE12_WORKSPACE.evidence_stages))

    if active.label == "📜 分板块导则生成":
        render_section_generation(model_tag=model_tag)
    elif active.label == "📊 管控指标汇总":
        render_indicators()
    elif active.label == "📄 一键导出":
        render_export()

    st.markdown("---")
    render_stage_summary(
        stage_code="12",
        title="城市设计导则体系",
        findings=[
            {"point": "导则覆盖总则、空间、建筑、交通、景观、历史、业态、市政、实施九大板块", "evidence": "城市设计导则标准体系"},
            {"point": "核心区限高不超过9m，一般区不超过18m，容积率不超过1.4", "evidence": "历史文化名城保护规划约束"},
            {"point": "分板块深度生成，每个板块注入真实空间数据", "evidence": "DeepSeek-V4 Pro 分发式调用"},
        ],
        methodology="分板块多轮深度生成引擎 + 全域空间数据驱动 + RAG 政策检索",
        implication="为成果表达 Stage 13 提供可交付的导则文本和管控指标体系。",
    )
```

- [ ] **Step 5: Convert Streamlit page file into a thin wrapper**

Replace `pages/12_城市设计导则.py` with:

```python
import streamlit as st

from src.stages.stage12_guideline.page import render_page


st.set_page_config(page_title="12 城市设计导则", layout="wide", initial_sidebar_state="collapsed")
render_page()
```

- [ ] **Step 6: Run compatibility tests**

Run:

```powershell
python -m pytest tests/test_stage12_guideline_config.py tests/test_stage_workspace.py tests/test_navigation_routes.py tests/test_startup_smoke.py tests/test_streamlit_compat.py -v
python -m ruff check src/stages/stage12_guideline pages/12_城市设计导则.py tests/test_stage12_guideline_config.py
```

Expected: all tests pass and ruff reports `All checks passed!`.

- [ ] **Step 7: Commit**

```powershell
git add src/stages/stage12_guideline pages/12_城市设计导则.py tests/test_stage12_guideline_config.py
git commit -m "refactor: split stage 12 guideline page"
```

---

### Task 5: Add Stage 07 Config and Migrate Strategy Page

**Files:**
- Create: `src/stages/stage07_strategy/__init__.py`
- Create: `src/stages/stage07_strategy/config.py`
- Create: `src/stages/stage07_strategy/page.py`
- Create: `src/stages/stage07_strategy/actions.py`
- Create: `src/stages/stage07_strategy/views/__init__.py`
- Create: `src/stages/stage07_strategy/views/negotiation.py`
- Create: `src/stages/stage07_strategy/views/consensus_radar.py`
- Create: `src/stages/stage07_strategy/views/design_brief.py`
- Modify: `pages/07_设计策略.py`
- Test: `tests/test_stage07_strategy_config.py`

- [ ] **Step 1: Write failing Stage 07 config tests**

Create `tests/test_stage07_strategy_config.py`:

```python
def test_stage07_workspace_preserves_legacy_subpage_labels():
    from src.stages.stage07_strategy.config import STAGE07_WORKSPACE

    labels = [item.label for item in STAGE07_WORKSPACE.subpages]

    assert labels == ["⚖️ 多主体协同推演", "📊 共识雷达", "📐 设计纲领提炼"]


def test_stage07_strategy_matrix_output_key_is_preserved():
    from src.stages.stage07_strategy.config import STAGE07_WORKSPACE

    negotiation = STAGE07_WORKSPACE.subpages[0]

    assert negotiation.output_key == "strategy_matrix"
    assert negotiation.artifact_category == "report"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests/test_stage07_strategy_config.py -v
```

Expected: fail with `ModuleNotFoundError`.

- [ ] **Step 3: Add Stage 07 config**

Create `src/stages/stage07_strategy/__init__.py`:

```python
"""Stage 07 structured page package."""
```

Create `src/stages/stage07_strategy/config.py`:

```python
from src.stages.common.workspace import StageWorkspaceSpec, SubpageSpec
from src.workflow.stage_keys import SK


STAGE07_WORKSPACE = StageWorkspaceSpec(
    stage_code="07",
    title="设计策略",
    description="通过多主体协同推演形成可审查、可下传的策略矩阵。",
    evidence_stages=("05", "06", "07"),
    subpages=[
        SubpageSpec(
            label="⚖️ 多主体协同推演",
            title="多主体协同推演",
            description="组织居民、开发商和规划师进行策略协商，形成共识矩阵。",
            output_key=SK.STRATEGY_MATRIX,
            artifact_category="report",
            aliases=("多主体协同", "协同推演"),
        ),
        SubpageSpec(
            label="📊 共识雷达",
            title="共识雷达",
            description="查看三方协同推演后的共识度分布。",
            aliases=("动态共识雷达", "共识度"),
        ),
        SubpageSpec(
            label="📐 设计纲领提炼",
            title="设计纲领提炼",
            description="将策略矩阵提炼为总体设计和专项设计的纲领。",
            output_key=SK.DESIGN_BASIS,
            artifact_category="report",
            aliases=("设计纲领", "纲领提炼"),
        ),
    ],
)
```

- [ ] **Step 4: Move Stage 07 branches into views**

Move the existing `pages/07_设计策略.py` branch bodies into:

- `views/negotiation.py` with `render_negotiation(model_tag: str) -> None`
- `views/consensus_radar.py` with `render_consensus_radar() -> None`
- `views/design_brief.py` with `render_design_brief(model_tag: str) -> None`

Keep these calls unchanged inside the moved code:

```python
record_policy_review("07", SK.STRATEGY_MATRIX, matrix if matrix else [])
register_report_output(label="策略共识矩阵", content=summary, stage_code="07", key="strategy_matrix")
save_stage_output("07", SK.STRATEGY_MATRIX, summary)
```

- [ ] **Step 5: Create Stage 07 page orchestrator and thin wrapper**

Create `src/stages/stage07_strategy/page.py` using the same pattern as Stage 12, then replace `pages/07_设计策略.py` with:

```python
import streamlit as st

from src.stages.stage07_strategy.page import render_page


st.set_page_config(page_title="07 设计策略", layout="wide", initial_sidebar_state="collapsed")
render_page()
```

- [ ] **Step 6: Run compatibility tests**

Run:

```powershell
python -m pytest tests/test_stage07_strategy_config.py tests/test_stage_workspace.py tests/test_approval_state.py tests/test_artifact_registry.py tests/test_navigation_routes.py tests/test_startup_smoke.py -v
python -m ruff check src/stages/stage07_strategy pages/07_设计策略.py tests/test_stage07_strategy_config.py
```

Expected: all tests pass and ruff reports `All checks passed!`.

- [ ] **Step 7: Commit**

```powershell
git add src/stages/stage07_strategy pages/07_设计策略.py tests/test_stage07_strategy_config.py
git commit -m "refactor: split stage 7 strategy page"
```

---

### Task 6: Migrate Remaining Core Stages in Batches

**Files:**
- Create: `src/stages/stage04_diagnosis/*`
- Create: `src/stages/stage08_master_plan/*`
- Create: `src/stages/stage09_systems/*`
- Create: `src/stages/stage10_detail_design/*`
- Create: `src/stages/stage11_implementation/*`
- Create: `src/stages/stage13_outputs/*`
- Modify: matching `pages/*.py`
- Test: one config test per stage package.

- [ ] **Step 1: Add config tests for each stage before moving code**

For each stage, create a test file that asserts the legacy `SUB_OPTIONS` labels remain unchanged and key output targets remain unchanged. Example for Stage 09:

```python
def test_stage09_workspace_preserves_legacy_subpage_labels():
    from src.stages.stage09_systems.config import STAGE09_WORKSPACE

    labels = [item.label for item in STAGE09_WORKSPACE.subpages]

    assert labels == [
        "🚗 交通网络与TOD",
        "🌳 公共空间与15分钟圈",
        "🏛️ 建筑形态、风貌与立面",
        "🎨 风貌景观与文保",
        "🏭 产业业态规划",
    ]
```

- [ ] **Step 2: Run each new test to verify it fails**

Run the relevant command after adding each test:

```powershell
python -m pytest tests/test_stage09_systems_config.py -v
```

Expected: fail with missing stage package.

- [ ] **Step 3: Create the stage package config**

Use the exact labels from the current page's `SUB_OPTIONS` and existing keys from `src/workflow/stage_keys.py`.

- [ ] **Step 4: Move branch bodies into view functions**

For each page, move each `if selected_sub == ...` branch body into a view module. Keep data calls unchanged:

```python
save_stage_output(...)
load_stage_output(...)
render_dependency_gate(...)
register_report_output(...)
register_artifact(...)
```

- [ ] **Step 5: Replace the page file with a thin wrapper**

Use these exact wrappers for the remaining core stages:

```python
import streamlit as st

from src.stages.stage04_diagnosis.page import render_page


st.set_page_config(page_title="04 现状分析与问题诊断", layout="wide", initial_sidebar_state="collapsed")
render_page()
```

```python
import streamlit as st

from src.stages.stage08_master_plan.page import render_page


st.set_page_config(page_title="08 总体城市设计", layout="wide", initial_sidebar_state="collapsed")
render_page()
```

```python
import streamlit as st

from src.stages.stage09_systems.page import render_page


st.set_page_config(page_title="09 专项系统设计", layout="wide", initial_sidebar_state="collapsed")
render_page()
```

```python
import streamlit as st

from src.stages.stage10_detail_design.page import render_page


st.set_page_config(page_title="10 重点地段深化", layout="wide", initial_sidebar_state="collapsed")
render_page()
```

```python
import streamlit as st

from src.stages.stage11_implementation.page import render_page


st.set_page_config(page_title="11 实施路径", layout="wide", initial_sidebar_state="collapsed")
render_page()
```

```python
import streamlit as st

from src.stages.stage13_outputs.page import render_page


st.set_page_config(page_title="13 成果表达", layout="wide", initial_sidebar_state="collapsed")
render_page()
```

- [ ] **Step 6: Run batch compatibility tests after each stage**

Run:

```powershell
python -m pytest tests/test_stage_workspace.py tests/test_navigation_routes.py tests/test_startup_smoke.py tests/test_streamlit_compat.py -v
python -m ruff check src/stages pages tests
```

Expected: all tests pass.

- [ ] **Step 7: Commit each migrated stage separately**

Use these exact commit commands:

```powershell
git add src/stages/stage04_diagnosis "pages/04_现状分析与问题诊断.py" tests/test_stage04_diagnosis_config.py
git commit -m "refactor: split stage 4 diagnosis page"
```

```powershell
git add src/stages/stage08_master_plan "pages/08_总体城市设计.py" tests/test_stage08_master_plan_config.py
git commit -m "refactor: split stage 8 master plan page"
```

```powershell
git add src/stages/stage09_systems "pages/09_专项系统设计.py" tests/test_stage09_systems_config.py
git commit -m "refactor: split stage 9 systems page"
```

```powershell
git add src/stages/stage10_detail_design "pages/10_重点地段深化.py" tests/test_stage10_detail_design_config.py
git commit -m "refactor: split stage 10 detail design page"
```

```powershell
git add src/stages/stage11_implementation "pages/11_实施路径.py" tests/test_stage11_implementation_config.py
git commit -m "refactor: split stage 11 implementation page"
```

```powershell
git add src/stages/stage13_outputs "pages/13_成果表达.py" tests/test_stage13_outputs_config.py
git commit -m "refactor: split stage 13 outputs page"
```

---

### Task 7: Final Verification and Push

**Files:**
- No new files unless a test exposes a compatibility bug.

- [ ] **Step 1: Run full targeted verification**

Run:

```powershell
python -m pytest tests/test_stage_workspace.py tests/test_navigation_routes.py tests/test_startup_smoke.py tests/test_streamlit_compat.py tests/test_approval_state.py tests/test_artifact_registry.py -v
python -m ruff check src/stages src/workflow src/ui pages tests
git diff --check
```

Expected:

- pytest exits with all selected tests passing.
- ruff reports `All checks passed!`.
- `git diff --check` reports no whitespace errors. Windows LF-to-CRLF warnings are acceptable.

- [ ] **Step 2: Verify worktree status**

Run:

```powershell
git status --short --branch
```

Expected: branch is clean after final commit.

- [ ] **Step 3: Push branch and main for Streamlit Cloud**

Run:

```powershell
git push origin codex/deployment-assets-lazy-loading
git push origin HEAD:main
git ls-remote origin refs/heads/main refs/heads/codex/deployment-assets-lazy-loading
```

Expected: both remote refs point to the same final commit hash.

---

## Self-Review

Spec coverage: the plan covers the shared workspace model, scoped CSS, Stage 12 first migration, Stage 07 complex migration, remaining stage batches, route compatibility, data-key compatibility, tests, and push flow.

Placeholder scan: the plan contains no open placeholder tasks, and all wrapper and commit examples use concrete stage package names.

Type consistency: `SubpageSpec`, `StageWorkspaceSpec`, `resolve_active_subpage()`, `build_stage_workspace_html()`, and `render_stage_workspace()` are defined before later tasks reference them.
