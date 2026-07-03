from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from src.engines.drawing_layout_engine import A3_LANDSCAPE_SIZE
from src.engines.frame_generator import compose_framed_sheet, sheet_to_bytes


def _sample_image(color: str = "#94a3b8") -> Image.Image:
    return Image.new("RGB", (640, 360), color)


def test_compose_framed_sheet_legacy_call_returns_a3_landscape_size():
    sheet = compose_framed_sheet(
        main_image=_sample_image(),
        title="用地现状分析图",
        chapter="02 数据诊断篇",
        summary="保留旧调用方式的说明文本。",
        legend_items=[("居住用地", "#facc15")],
        drawing_number="DR-011",
        scale_text="1:5000",
    )

    assert sheet.size == A3_LANDSCAPE_SIZE
    assert sheet.mode == "RGB"
    assert sheet_to_bytes(sheet).startswith(b"\x89PNG")


def test_compose_framed_sheet_dual_compare_accepts_secondary_images_and_legend_items():
    sheet = compose_framed_sheet(
        main_image=_sample_image("#d1d5db"),
        title="地块2改造前后对比图",
        layout_id="dual_compare",
        secondary_images={
            "before_view": _sample_image("#64748b"),
            "after_view": _sample_image("#86efac"),
        },
        legend_items=[("保留", "#3b82f6"), ("新增", "#22c55e")],
    )

    assert sheet.size == A3_LANDSCAPE_SIZE
    assert sheet.mode == "RGB"


def test_results_page_wires_selected_layout_id_to_atlas_generation():
    page_source = (
        Path(__file__).resolve().parents[1] / "pages" / "13_成果表达.py"
    ).read_text(encoding="utf-8")

    assert "list_layout_profiles" in page_source
    assert "recommend_layout_profile" in page_source
    assert "图纸版式" in page_source
    assert "selected_layout_id" in page_source
    assert "layout_id=selected_layout_id" in page_source


def test_process_a3_layout_passes_legacy_metadata_to_selected_layout(tmp_path, monkeypatch):
    from src.engines import frame_generator
    from tools import draw_scope_map

    map_path = tmp_path / "map.png"
    output_path = tmp_path / "sheet.png"
    Image.new("RGB", (40, 20), "#f8fafc").save(map_path)

    drawing_module = SimpleNamespace(
        legend_items=[
            ("Boundary", "rect_red_border"),
            ("Blue link", "line_blue"),
            ("Fallback", "style_not_mapped"),
        ]
    )
    default_module = SimpleNamespace(legend_items=[("Default", "rect_water")])

    def fake_get_drawing_module(drawing_type):
        if drawing_type == "custom metadata drawing":
            return drawing_module
        return default_module

    captured = {}

    def fake_compose_framed_sheet(**kwargs):
        captured.update(kwargs)
        return Image.new("RGB", A3_LANDSCAPE_SIZE, "#ffffff")

    monkeypatch.setattr(draw_scope_map, "get_drawing_module", fake_get_drawing_module)
    monkeypatch.setattr(frame_generator, "compose_framed_sheet", fake_compose_framed_sheet)

    draw_scope_map.process_a3_layout(
        map_path,
        output_path,
        view_w=959.04,
        drawing_type="custom metadata drawing",
        title="Custom Metadata",
        description_lines=["diagnostic note"],
        drawing_number="DR-TST",
        layout_id="analysis_dashboard",
    )

    assert captured["layout_id"] == "analysis_dashboard"
    assert captured["legend_items"] == [
        ("Boundary", "#ff3b30"),
        ("Blue link", "#3b82f6"),
        ("Fallback", "#607d8b"),
    ]
    assert captured["scale_text"] == "1:3000"
    assert output_path.exists()
