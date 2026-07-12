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
