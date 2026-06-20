from pathlib import Path

from tools.export_a1_editable_psd_package import build_readme_text


def test_build_readme_text_uses_dynamic_board_count():
    readme = build_readme_text(board_count=5, output_dir=Path("out"))

    assert "create 5 A1 vertical PSD files" in readme
    assert "A1_Board_05_editable_text.psd" in readme
    assert "A1_Board_05_raster_layers.psd" in readme
