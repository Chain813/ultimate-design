import streamlit as st


def setup_function():
    st.session_state.clear()
    st.session_state["stage_bus"] = {}


def test_save_and_load_approval_record_preserves_review_fields():
    from src.workflow.approval_state import ApprovalStatus, load_approval_record, save_approval_record

    save_approval_record(
        stage_code="07",
        key="strategy_matrix",
        status=ApprovalStatus.REVISE,
        reviewer="policy",
        comment="绿地率不足，需要回到公共空间系统优化。",
        risk_level="high",
    )

    record = load_approval_record("07", "strategy_matrix")

    assert record["status"] == "revise"
    assert record["reviewer"] == "policy"
    assert record["comment"] == "绿地率不足，需要回到公共空间系统优化。"
    assert record["risk_level"] == "high"
    assert record["key"] == "strategy_matrix"


def test_record_policy_review_sets_revision_when_any_item_has_risk():
    from src.workflow.approval_state import load_approval_record, record_policy_review
    from src.workflow.stage_data_bus import load_stage_output

    matrix = [
        {"source": "条例A", "compliance_note": "合规 — 可引用"},
        {"source": "条例B", "compliance_note": "存在风险 — 高度需复核"},
    ]

    record_policy_review("07", "strategy_matrix", matrix)

    record = load_approval_record("07", "strategy_matrix")
    saved_matrix = load_stage_output("07", "policy_review_strategy_matrix")

    assert record["status"] == "revise"
    assert record["risk_level"] == "high"
    assert "条例B" in record["comment"]
    assert saved_matrix == matrix


def test_record_policy_review_blocks_when_any_item_is_illegal():
    from src.workflow.approval_state import load_approval_record, record_policy_review

    matrix = [
        {"source": "保护条例", "compliance_note": "违规 — 核心区高度超过控制线"},
    ]

    record_policy_review("07", "strategy_matrix", matrix)

    record = load_approval_record("07", "strategy_matrix")
    assert record["status"] == "blocked"
    assert record["risk_level"] == "critical"
    assert "保护条例" in record["comment"]


def test_collect_missing_dependencies_reports_missing_stage_output():
    from src.workflow.approval_state import StageDependency, collect_missing_dependencies

    missing = collect_missing_dependencies([StageDependency("07", "strategy_matrix", "策略矩阵")])

    assert missing == [{"stage_code": "07", "key": "strategy_matrix", "label": "策略矩阵", "reason": "missing"}]


def test_collect_missing_dependencies_respects_required_approval_status():
    from src.workflow.approval_state import (
        ApprovalStatus,
        StageDependency,
        collect_missing_dependencies,
        save_approval_record,
    )
    from src.workflow.stage_data_bus import save_stage_output

    save_stage_output("07", "strategy_matrix", "策略内容")
    save_approval_record(
        "07",
        "strategy_matrix",
        ApprovalStatus.REVISE,
        reviewer="policy",
        comment="政策风险需修订",
        risk_level="high",
    )

    missing = collect_missing_dependencies(
        [StageDependency("07", "strategy_matrix", "策略矩阵", approval_required=True)]
    )

    assert missing == [
        {
            "stage_code": "07",
            "key": "strategy_matrix",
            "label": "策略矩阵",
            "reason": "approval_revise",
        }
    ]
