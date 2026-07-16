def test_stage09_workspace_preserves_legacy_subpage_labels():
    from src.stages.stage09_systems.config import STAGE09_WORKSPACE

    labels = [item.label for item in STAGE09_WORKSPACE.subpages]

    assert labels == [
        "🚗 交通网络与TOD",
        "🌳 公共空间与15分钟圈",
        "🏛️ 建筑形态、风貌与立面",
        "🎨 风貌景观与文保",
        "🏭 产业业态规划",
    ]


def test_stage09_output_keys_are_preserved():
    from src.stages.stage09_systems.config import STAGE09_WORKSPACE

    output_keys = [item.output_key for item in STAGE09_WORKSPACE.subpages]

    assert output_keys == [
        "traffic_system",
        "public_space",
        "building_form",
        "landscape_style",
        "p09_industry_planning",
    ]


def test_stage09_page_renderer_is_importable():
    from src.stages.stage09_systems.page import render_page

    assert callable(render_page)
