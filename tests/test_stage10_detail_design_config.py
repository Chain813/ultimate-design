def test_stage10_workspace_preserves_legacy_subpage_labels():
    from src.stages.stage10_detail_design.config import STAGE10_WORKSPACE

    labels = [item.label for item in STAGE10_WORKSPACE.subpages]

    assert labels == [
        "📍 重点地块诊断雷达",
        "📊 控制性详细指标推演",
        "👥 目标人群与行为画像",
        "🏗️ 空间深化设计方案",
        "🔄 Before/After 推演",
        "🔬 特色专项研究",
    ]


def test_stage10_output_keys_are_preserved():
    from src.stages.stage10_detail_design.config import STAGE10_WORKSPACE

    output_keys = [item.output_key for item in STAGE10_WORKSPACE.subpages]

    assert output_keys == [
        "radar_data",
        "plot_metrics",
        "plot_personas",
        "plot_design",
        "before_after",
        "p10_specialized_study",
    ]


def test_stage10_page_renderer_is_importable():
    from src.stages.stage10_detail_design.page import render_page

    assert callable(render_page)
