def test_stage13_workspace_preserves_legacy_subpage_labels():
    from src.stages.stage13_outputs.config import STAGE13_WORKSPACE

    labels = [item.label for item in STAGE13_WORKSPACE.subpages]

    assert labels == [
        "🗺️ 规划图纸代码生成",
        "🖼️ 图册自动组装",
        "📤 文档导出",
        "📝 毕业设计答辩稿",
    ]


def test_stage13_output_keys_describe_export_artifacts():
    from src.stages.stage13_outputs.config import STAGE13_WORKSPACE

    output_keys = [item.output_key for item in STAGE13_WORKSPACE.subpages]

    assert output_keys == ["planning_drawings", "atlas_package", "final_report", "thesis_defense"]


def test_stage13_page_renderer_is_importable():
    from src.stages.stage13_outputs.page import render_page

    assert callable(render_page)


def test_stage13_project_root_resolves_to_repo_root():
    from src.stages.stage13_outputs.page import PROJECT_ROOT

    assert (PROJECT_ROOT / "scripts" / "export_high_precision_gis.py").exists()
