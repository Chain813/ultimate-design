import streamlit as st


def setup_function():
    st.session_state.clear()
    st.session_state["stage_bus"] = {}


def test_register_artifact_uses_approval_status_and_starts_version_one():
    from src.workflow.approval_state import ApprovalStatus, save_approval_record
    from src.workflow.artifact_registry import get_artifact, register_artifact

    save_approval_record(
        stage_code="07",
        key="strategy_matrix",
        status=ApprovalStatus.APPROVED,
        reviewer="policy",
        comment="approved",
        risk_level="low",
    )

    record = register_artifact(
        stage_code="07",
        key="strategy_matrix",
        label="Strategy matrix",
        category="report",
        location="stage_bus",
        mime="text/markdown; charset=utf-8",
    )

    assert record["artifact_id"] == "07:strategy_matrix"
    assert record["stage_code"] == "07"
    assert record["key"] == "strategy_matrix"
    assert record["version"] == 1
    assert record["approval_status"] == "approved"
    assert record["risk_level"] == "low"
    assert get_artifact("07:strategy_matrix") == record


def test_register_artifact_increments_version_for_existing_artifact():
    from src.workflow.artifact_registry import register_artifact

    first = register_artifact("08", "spatial_structure", "Spatial structure")
    second = register_artifact("08", "spatial_structure", "Spatial structure v2")

    assert first["version"] == 1
    assert second["version"] == 2
    assert second["label"] == "Spatial structure v2"


def test_list_artifacts_filters_by_stage_and_category():
    from src.workflow.artifact_registry import list_artifacts, register_artifact

    register_artifact("07", "strategy_matrix", "Strategy matrix", category="report")
    register_artifact("08", "spatial_structure", "Spatial structure", category="drawing")
    register_artifact("08", "sandbox", "Landuse sandbox", category="data")

    stage08 = list_artifacts(stage_code="08")
    data_artifacts = list_artifacts(category="data")

    assert [item["artifact_id"] for item in stage08] == ["08:sandbox", "08:spatial_structure"]
    assert [item["artifact_id"] for item in data_artifacts] == ["08:sandbox"]


def test_register_report_output_adds_stage_artifact_record():
    from src.ui import persistent_outputs
    from src.workflow.artifact_registry import get_artifact

    st.session_state[persistent_outputs.OUTPUT_REGISTRY_KEY] = {}

    persistent_outputs.register_report_output(
        label="Strategy matrix",
        content="approved strategy",
        stage_code="07",
        key="strategy_matrix",
    )

    artifact = get_artifact("07:strategy_matrix")

    assert artifact is not None
    assert artifact["label"] == "Strategy matrix"
    assert artifact["category"] == "report"
    assert artifact["location"] == "Strategy matrix.md"
    assert artifact["metadata"]["persistent_output_key"] == "strategy_matrix"
