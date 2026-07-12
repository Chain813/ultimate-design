"""Lightweight approval and dependency state helpers for the planning workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable

import streamlit as st

from src.workflow.stage_data_bus import load_stage_output, save_stage_output, stage_ready


class ApprovalStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    REVISE = "revise"
    BLOCKED = "blocked"
    APPROVED = "approved"
    OVERRIDE = "override"


@dataclass(frozen=True)
class StageDependency:
    stage_code: str
    key: str
    label: str
    approval_required: bool = False


APPROVAL_ALLOWED_STATUSES = {ApprovalStatus.APPROVED.value, ApprovalStatus.OVERRIDE.value}


def approval_record_key(key: str) -> str:
    return f"approval_{key}"


def policy_review_key(key: str) -> str:
    return f"policy_review_{key}"


def save_approval_record(
    stage_code: str,
    key: str,
    status: ApprovalStatus | str,
    reviewer: str = "",
    comment: str = "",
    risk_level: str = "none",
    metadata: dict | None = None,
) -> dict:
    status_value = status.value if isinstance(status, ApprovalStatus) else str(status)
    record = {
        "stage_code": stage_code,
        "key": key,
        "status": status_value,
        "reviewer": reviewer,
        "comment": comment,
        "risk_level": risk_level,
        "metadata": metadata or {},
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    save_stage_output(stage_code, approval_record_key(key), record)
    return record


def load_approval_record(stage_code: str, key: str, default=None):
    return load_stage_output(stage_code, approval_record_key(key), default or {})


def record_policy_review(stage_code: str, key: str, matrix: list[dict]) -> dict:
    save_stage_output(stage_code, policy_review_key(key), matrix)

    if not matrix:
        return save_approval_record(
            stage_code=stage_code,
            key=key,
            status=ApprovalStatus.REVIEW,
            reviewer="policy",
            comment="未检索到可用于合规复核的政策条文，请补充政策知识库或重新研判。",
            risk_level="unknown",
            metadata={"policy_items": "0"},
        )

    critical_items = _matching_policy_items(matrix, ("违规",))
    risk_items = _matching_policy_items(matrix, ("风险", "⚠️", "需核查"))

    if critical_items:
        status = ApprovalStatus.BLOCKED
        risk_level = "critical"
        comment = _summarize_policy_items(critical_items)
    elif risk_items:
        status = ApprovalStatus.REVISE
        risk_level = "high"
        comment = _summarize_policy_items(risk_items)
    else:
        status = ApprovalStatus.APPROVED
        risk_level = "low"
        comment = "政策合规复核通过，未识别阻断性风险。"

    return save_approval_record(
        stage_code=stage_code,
        key=key,
        status=status,
        reviewer="policy",
        comment=comment,
        risk_level=risk_level,
        metadata={"policy_items": str(len(matrix))},
    )


def collect_missing_dependencies(dependencies: Iterable[StageDependency]) -> list[dict]:
    missing = []
    for dep in dependencies:
        if not stage_ready(dep.stage_code, dep.key):
            missing.append(_dependency_issue(dep, "missing"))
            continue

        if dep.approval_required:
            record = load_approval_record(dep.stage_code, dep.key)
            status = str(record.get("status", "missing"))
            if status not in APPROVAL_ALLOWED_STATUSES:
                missing.append(_dependency_issue(dep, f"approval_{status}"))

    return missing


def render_dependency_gate(dependencies: Iterable[StageDependency], title: str = "上游依赖未就绪") -> bool:
    missing = collect_missing_dependencies(dependencies)
    if not missing:
        return True

    lines = []
    for item in missing:
        reason = "缺少成果" if item["reason"] == "missing" else f"审批状态：{item['reason'].replace('approval_', '')}"
        lines.append(f"- Stage {item['stage_code']} · {item['label']}：{reason}")

    st.warning(f"**{title}**\n\n" + "\n".join(lines))
    return False


def _dependency_issue(dep: StageDependency, reason: str) -> dict:
    return {
        "stage_code": dep.stage_code,
        "key": dep.key,
        "label": dep.label,
        "reason": reason,
    }


def _matching_policy_items(matrix: list[dict], needles: tuple[str, ...]) -> list[dict]:
    matched = []
    for item in matrix:
        note = str(item.get("compliance_note", ""))
        if any(needle in note for needle in needles):
            matched.append(item)
    return matched


def _summarize_policy_items(items: list[dict]) -> str:
    parts = []
    for item in items[:5]:
        source = str(item.get("source", "未知来源"))
        note = str(item.get("compliance_note", ""))
        parts.append(f"{source}: {note}")
    return "；".join(parts)
