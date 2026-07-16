"""Artifact registry for generated planning deliverables."""

from __future__ import annotations

from datetime import UTC, datetime, timezone
from typing import Any

from src.workflow.approval_state import ApprovalStatus, load_approval_record
from src.workflow.stage_data_bus import load_stage_output, save_stage_output

ARTIFACT_REGISTRY_STAGE = "artifact"
ARTIFACT_REGISTRY_KEY = "registry"


def build_artifact_id(stage_code: str, key: str) -> str:
    return f"{stage_code}:{key}"


def load_artifact_registry() -> dict[str, dict[str, Any]]:
    registry = load_stage_output(ARTIFACT_REGISTRY_STAGE, ARTIFACT_REGISTRY_KEY, {})
    if not isinstance(registry, dict):
        return {}
    return {k: v for k, v in registry.items() if isinstance(v, dict)}


def save_artifact_registry(registry: dict[str, dict[str, Any]]) -> None:
    save_stage_output(ARTIFACT_REGISTRY_STAGE, ARTIFACT_REGISTRY_KEY, registry)


def register_artifact(
    stage_code: str,
    key: str,
    label: str,
    category: str = "report",
    location: str = "stage_bus",
    mime: str = "text/markdown; charset=utf-8",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    registry = load_artifact_registry()
    artifact_id = build_artifact_id(stage_code, key)
    previous = registry.get(artifact_id, {})
    version = int(previous.get("version", 0)) + 1
    approval = load_approval_record(stage_code, key, {})

    record = {
        "artifact_id": artifact_id,
        "stage_code": stage_code,
        "key": key,
        "label": label,
        "category": category,
        "location": location,
        "mime": mime,
        "version": version,
        "approval_status": approval.get("status", ApprovalStatus.DRAFT.value),
        "risk_level": approval.get("risk_level", "none"),
        "updated_at": datetime.now(UTC).isoformat(),
        "metadata": metadata or {},
    }
    registry[artifact_id] = record
    save_artifact_registry(registry)
    return record


def get_artifact(artifact_id: str) -> dict[str, Any] | None:
    return load_artifact_registry().get(artifact_id)


def list_artifacts(stage_code: str | None = None, category: str | None = None) -> list[dict[str, Any]]:
    artifacts = list(load_artifact_registry().values())
    if stage_code is not None:
        artifacts = [item for item in artifacts if item.get("stage_code") == stage_code]
    if category is not None:
        artifacts = [item for item in artifacts if item.get("category") == category]
    return sorted(artifacts, key=lambda item: str(item.get("artifact_id", "")))
