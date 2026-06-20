from tools.render_exhibition_board_previews import BOARD_DIR, build_single_outputs


def test_build_single_outputs_matches_board_count():
    outputs = build_single_outputs(5)

    assert outputs == [
        BOARD_DIR / "a1_board_01_preview.png",
        BOARD_DIR / "a1_board_02_preview.png",
        BOARD_DIR / "a1_board_03_preview.png",
        BOARD_DIR / "a1_board_04_preview.png",
        BOARD_DIR / "a1_board_05_preview.png",
    ]
