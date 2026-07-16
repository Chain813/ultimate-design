def test_stage04_workspace_preserves_legacy_subpage_labels():
    from src.stages.stage04_diagnosis.config import STAGE04_WORKSPACE

    labels = [item.label for item in STAGE04_WORKSPACE.subpages]

    assert labels == [
        "🏙️ 3D 现状全息底座",
        "📊 MPI 更新潜力评估",
        "🎯 地块雷达诊断",
        "🔬 AI 前期诊断报告",
        "📋 专项资源分析",
    ]


def test_stage04_output_keys_are_preserved():
    from src.stages.stage04_diagnosis.config import STAGE04_WORKSPACE

    output_keys = [item.output_key for item in STAGE04_WORKSPACE.subpages]

    assert output_keys == [
        "digital_twin_metrics",
        "mpi_ranking",
        "radar_data",
        "diagnosis_report",
        "resource_analysis",
    ]


def test_stage04_page_renderer_is_importable():
    from src.stages.stage04_diagnosis.page import render_page

    assert callable(render_page)
