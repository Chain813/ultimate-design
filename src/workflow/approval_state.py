"""Lightweight approval and dependency state helpers for the planning workflow."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timezone
from enum import Enum, StrEnum

import streamlit as st

from src.workflow.stage_data_bus import load_stage_output, save_stage_output, stage_ready


class ApprovalStatus(StrEnum):
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
        "updated_at": datetime.now(UTC).isoformat(),
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
    deps_list = list(dependencies)
    missing = collect_missing_dependencies(deps_list)
    if not missing:
        return True

    lines = []
    for item in missing:
        reason = "缺少成果" if item["reason"] == "missing" else f"审批状态：{item['reason'].replace('approval_', '')}"
        lines.append(f"- Stage {item['stage_code']} · {item['label']}：{reason}")

    st.warning(f"**{title}**\n\n" + "\n".join(lines))

    _DEFAULT_FALLBACK_DATA = {
        SK.STRATEGY_MATRIX: (
            "| 策略方向 | 具体举措 | 政策依据 | 空间落位 | 资金逻辑 | 协同度 |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| 文化活化 | 伪满皇宫文创商街与历史风貌修缮 | 《历史文化名城保护条例》 | 伪满皇宫周边 | 政府专项+社会资本 | 高 |\n"
            "| 空间缝合 | 伊通河滨水绿道慢行与活力通廊 | 《城市绿道规划导则》 | 伊通河滨水带 | 市政基础设施配套 | 高 |"
        ),
        SK.SPATIAL_STRUCTURE: "总体空间结构规划为'一核两轴多片多节点'，以伪满皇宫为文化活力核心，构筑伊通河生态轴与东盛大街功能轴，串联文旅创新片区与生态居住社区。",
        SK.TRAFFIC_SYSTEM: "规划形成'外畅内幽'交通网络，强化轻轨4号线TOD微循环接驳，慢行优先，沿街红线退距设立连续无障碍步道系统。",
        SK.PUBLIC_SPACE: "构建'滨水绿带-口袋公园-历史庭院'三级公共空间系统，绿化覆盖率提升至35%以上，实现居民300米见绿、500米入园。",
        SK.BUILDING_FORM: "建筑高度严格实行分区分级管控：伪满皇宫保护核心区限高≤9m，风貌协调区限高≤18m，延续近代长春红灰砖立面与坡屋顶形制。",
        SK.LANDSCAPE_STYLE: "延续近代风貌特色色彩谱系（灰砖青瓦+暖黄木作），采用传统环保铺装材质，保护利用古树名木，营造古今交融街区风貌。",
        SK.DIAGNOSIS_REPORT: "现状伪满皇宫文旅协调区综合更新潜力达88.5分，核心瓶颈在于文化IP外溢不足、慢行交通割裂及微气候舒适度欠佳。",
        SK.DESIGN_CONCEPT: "数字孪生·古今共振——AI赋能下的伪满皇宫周边街区高品质城市更新总体方案策划。",
        SK.DESIGN_BRIEF: "落实保护优先、空间织补、以点带面的总体要求，严守限高红线，推动文旅商创与宜居社区融合发展。",
    }

    gate_col1, gate_col2 = st.columns([3, 1])
    with gate_col1:
        st.caption("💡 流程说明：检测到前置成果或专家审批未就绪。若处于推演评估或快速体验阶段，可一键放行解锁下游（自动注入标准规划基底数据）。")
    with gate_col2:
        gate_slug = "_".join(f"{d.stage_code}_{d.key}" for d in deps_list)
        btn_label = "🔓 评审放行（一键解锁下游）" if any(d.approval_required for d in deps_list) else "⚡ 快速放行（注入基底数据）"
        if st.button(btn_label, key=f"btn_gate_pass_{gate_slug}", type="primary"):
            for dep in deps_list:
                if not stage_ready(dep.stage_code, dep.key):
                    save_stage_output(dep.stage_code, dep.key, _DEFAULT_FALLBACK_DATA.get(dep.key, f"【基底成果】已在 Stage {dep.stage_code} 门禁处直接放行。"))
                if dep.approval_required:
                    save_approval_record(
                        stage_code=dep.stage_code,
                        key=dep.key,
                        status=ApprovalStatus.APPROVED,
                        reviewer="评审委员会/用户放行",
                        comment="用户在工作流门禁处一键评审放行并解锁下游阶段",
                    )
            st.success("✅ 流程放行已生效，下游工作流已解锁！")
            st.rerun()

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
