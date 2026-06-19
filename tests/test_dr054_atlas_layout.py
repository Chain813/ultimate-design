from tools.redraw_dr054_atlas_layout import (
    CANVAS_SIZE,
    DRAINAGE_ARROW_STYLE,
    OUTPUT_NAME,
    layout_boxes,
)


def test_dr054_uses_standard_atlas_sheet_layout():
    assert CANVAS_SIZE == (4480, 3168)
    assert OUTPUT_NAME == "DR-054_竖向规划与排水分析图.png"

    boxes = layout_boxes(scale=2)

    assert boxes["header"] == (64, 120, 4416, 356)
    assert boxes["map"] == (64, 416, 3184, 3036)
    assert boxes["legend"] == (3230, 416, 4420, 1060)
    assert boxes["description"] == (3230, 1120, 4420, 3036)


def test_dr054_drainage_arrows_are_visually_prominent():
    assert DRAINAGE_ARROW_STYLE["color"] == "#1D4ED8"
    assert DRAINAGE_ARROW_STYLE["stroke_width"] >= 12
    assert DRAINAGE_ARROW_STYLE["outline_width"] >= 10
    assert DRAINAGE_ARROW_STYLE["mutation_scale"] >= 44
