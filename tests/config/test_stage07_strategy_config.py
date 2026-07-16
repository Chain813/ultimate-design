def test_stage07_workspace_preserves_legacy_subpage_labels():
    from src.stages.stage07_strategy.config import STAGE07_WORKSPACE

    labels = [item.label for item in STAGE07_WORKSPACE.subpages]

    assert labels == ["⚖️ 多主体协同推演", "📊 共识雷达", "📐 设计纲领提炼"]


def test_stage07_strategy_matrix_output_key_is_preserved():
    from src.stages.stage07_strategy.config import STAGE07_WORKSPACE

    negotiation = STAGE07_WORKSPACE.subpages[0]

    assert negotiation.output_key == "strategy_matrix"
    assert negotiation.artifact_category == "report"


def test_stage07_page_renderer_is_importable():
    from src.stages.stage07_strategy.page import render_page

    assert callable(render_page)
