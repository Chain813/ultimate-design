import streamlit as st


def setup_function():
    st.session_state.clear()
    st.session_state["stage_bus"] = {}
    st.query_params.clear()


def test_stage12_workspace_preserves_legacy_subpage_labels():
    from src.stages.stage12_guideline.config import STAGE12_WORKSPACE

    labels = [item.label for item in STAGE12_WORKSPACE.subpages]

    assert labels == ["📜 分板块导则生成", "📊 管控指标汇总", "📄 一键导出"]


def test_stage12_export_subpage_maps_to_design_guideline_output():
    from src.stages.stage12_guideline.config import STAGE12_WORKSPACE

    export = STAGE12_WORKSPACE.subpages[2]

    assert export.output_key == "design_guideline"
    assert export.artifact_category == "guideline"


def test_register_guideline_artifact_records_stage12_output():
    from src.stages.stage12_guideline.actions import register_guideline_artifact
    from src.workflow.artifact_registry import get_artifact

    register_guideline_artifact(total_sections=9, total_chars=1234)

    artifact = get_artifact("12:design_guideline")
    assert artifact["label"] == "城市设计导则"
    assert artifact["category"] == "guideline"
    assert artifact["metadata"] == {"sections": "9", "total_chars": "1234"}


def test_stage12_page_renderer_is_importable():
    from src.stages.stage12_guideline.page import render_page

    assert callable(render_page)
