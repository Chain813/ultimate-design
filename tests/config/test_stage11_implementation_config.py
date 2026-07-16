def test_stage11_workspace_preserves_legacy_subpage_labels():
    from src.stages.stage11_implementation.config import STAGE11_WORKSPACE

    labels = [item.label for item in STAGE11_WORKSPACE.subpages]

    assert labels == [
        "🌐 第一层：全域实施路径",
        "📍 第二层：重点地块实施路径",
        "🏗️ 更新方式分类",
    ]


def test_stage11_output_keys_are_preserved():
    from src.stages.stage11_implementation.config import STAGE11_WORKSPACE

    output_keys = [item.output_key for item in STAGE11_WORKSPACE.subpages]

    assert output_keys == ["region_phasing", "plot_phasing", "renewal_classification"]


def test_stage11_page_renderer_is_importable():
    from src.stages.stage11_implementation.page import render_page

    assert callable(render_page)
