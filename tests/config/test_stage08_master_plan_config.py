def test_stage08_workspace_preserves_legacy_subpage_labels():
    from src.stages.stage08_master_plan.config import STAGE08_WORKSPACE

    labels = [item.label for item in STAGE08_WORKSPACE.subpages]

    assert labels == ["🗺️ 空间结构推演", "🎛️ 用地结构优化沙盘"]


def test_stage08_output_keys_are_preserved():
    from src.stages.stage08_master_plan.config import STAGE08_WORKSPACE

    structure, sandbox = STAGE08_WORKSPACE.subpages

    assert structure.output_key == "spatial_structure"
    assert structure.artifact_category == "report"
    assert sandbox.output_key == "landuse_sandbox"
    assert sandbox.artifact_category == "data"


def test_stage08_page_renderer_is_importable():
    from src.stages.stage08_master_plan.page import render_page

    assert callable(render_page)
