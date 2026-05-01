"""Small compatibility helpers for Streamlit API drift."""

from __future__ import annotations

from inspect import signature


def stretch_width(component) -> dict:
    """Return full-width kwargs for both old and new Streamlit versions."""
    try:
        params = signature(component).parameters
    except (TypeError, ValueError):
        return {"use_container_width": True}

    if "width" in params:
        return {"width": "stretch"}
    return {"use_container_width": True}
