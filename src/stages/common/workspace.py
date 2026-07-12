from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
import re

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
    default_index: int = 0,
    requested_subpage: str | None = None,
) -> SubpageSpec:
    alias_map: dict[str, str] = {}
    for subpage in spec.subpages:
        for alias in subpage.aliases:
            alias_map[alias] = subpage.label

    labels = [subpage.label for subpage in spec.subpages]
    active_label = (
        _resolve_label(labels, requested_subpage, default_index, alias_map)
        if requested_subpage is not None
        else resolve_subpage_value(labels, default_index=default_index, aliases=alias_map)
    )
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
