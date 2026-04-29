"""Workflow definitions for the urban-design planning process."""

from importlib import import_module

__all__ = [
    "CITY_DESIGN_STAGES",
    "STAGE_LOOKUP",
    "STAGE_MODULE_MAP",
    "WORKFLOW_BOARDS",
    "board_stage_options",
    "resolve_stage_option",
    "resolve_subpage_option",
    "render_stage_workbench",
    "stage_code_from_option",
    "stage_modules",
    "stage_primary_href",
]


def __getattr__(name):
    if name in __all__:
        workflow = import_module("src.workflow.city_design_workflow")
        return getattr(workflow, name)
    raise AttributeError(f"module 'src.workflow' has no attribute {name!r}")
