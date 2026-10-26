from __future__ import annotations

import re
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


def resolve_active_subpage(
    spec: StageWorkspaceSpec,
    default_index: int | dict[str, str] = 0,
    requested_subpage: str | None = None,
    query_params: dict[str, str] | None = None,
) -> SubpageSpec:
    if isinstance(default_index, dict):
        query_params = default_index
        default_index = 0

    alias_map: dict[str, str] = {}
    for subpage in spec.subpages:
        for alias in subpage.aliases:
            alias_map[alias] = subpage.label
        alias_map[subpage.title] = subpage.label

    labels = [subpage.label for subpage in spec.subpages]
    if requested_subpage is not None:
        active_label = _resolve_label(labels, requested_subpage, default_index, alias_map)
    elif query_params is not None:
        active_label = resolve_subpage_value(
            labels, default_index=default_index, aliases=alias_map, query_params=query_params
        )
    else:
        active_label = resolve_subpage_value(labels, default_index=default_index, aliases=alias_map)

    for subpage in spec.subpages:
        if subpage.label == active_label:
            return subpage
    return spec.subpages[default_index]


ARTIFACT_CATEGORY_LABELS: dict[str, str] = {
    "report": "图文报告",
    "guideline": "管控图则",
    "data": "量化数据",
    "package": "工程交付包",
}


def build_stage_workspace_html(spec: StageWorkspaceSpec, active: SubpageSpec) -> str:
    raw_sub = st.query_params.get("sub", "")
    if isinstance(raw_sub, list):
        raw_sub = raw_sub[0] if raw_sub else ""
    current_sub = str(raw_sub).strip()

    nav_items = []
    for subpage in spec.subpages:
        cls = "stage-workspace-tab is-active" if subpage.label == active.label else "stage-workspace-tab"
        if current_sub:
            href = f"?sub={escape(current_sub)}&tab={escape(subpage.label)}"
        else:
            href = f"?tab={escape(subpage.label)}"
        nav_items.append(
            f'<a class="{cls}" href="{href}" target="_self">{escape(subpage.title)}</a>'
        )

    output_parts = []
    if active.output_key:
        bus_key = f"{escape(spec.stage_code)}_{escape(active.output_key)}"
        output_parts.append(f"🔗 数据总线：{bus_key}")
    elif getattr(spec, "stage_bus_key", ""):
        output_parts.append(f"🔗 数据总线：{escape(str(getattr(spec, 'stage_bus_key', '')))}")

    raw_artifact = active.artifact_category or getattr(spec, "artifact_type", "")
    if raw_artifact:
        artifact_label = ARTIFACT_CATEGORY_LABELS.get(str(raw_artifact).lower(), escape(str(raw_artifact)))
        output_parts.append(f"📄 成果形态：{artifact_label}")
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


def _resolve_label(options: list[str], requested: str | None, default_index: int, aliases: dict[str, str]) -> str:
    if requested:
        target = aliases.get(requested, requested)
        target_norm = _normalize_label(target)
        for option in options:
            option_norm = _normalize_label(option)
            if option == target or option_norm == target_norm or target_norm in option_norm or option_norm in target_norm:
                return option
    return options[default_index]


def _normalize_label(value: str | None) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", str(value or "")).lower()
