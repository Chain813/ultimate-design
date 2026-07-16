from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from tools.generate_parcel_control_tables import (
    _scaled_fonts,
    build_control_table_rows,
    calculate_metrics,
    load_key_plot_areas,
    metric_card_text_positions,
)


def test_calculate_metrics_derives_post_renovation_values():
    metrics = calculate_metrics(
        area_sqm=37144.76329094557,
        far=1.3,
        building_density=0.25,
        green_ratio=0.38,
    )

    assert metrics.area_ha == pytest.approx(3.7145, abs=0.0001)
    assert metrics.floor_area_sqm == pytest.approx(48288.19, abs=0.01)
    assert metrics.footprint_sqm == pytest.approx(9286.19, abs=0.01)
    assert metrics.green_sqm == pytest.approx(14115.01, abs=0.01)
    assert metrics.hardscape_sqm == pytest.approx(13743.56, abs=0.01)


def test_load_key_plot_areas_uses_district_shape_area_properties():
    areas = load_key_plot_areas(Path("data/gis/Key_Plots_District.json"))

    assert [round(area / 10000, 2) for area in areas] == [3.71, 16.83, 2.78, 2.47, 1.3]


def test_control_table_rows_are_based_on_post_renovation_master_plan_specs():
    rows = build_control_table_rows(Path("data/gis/Key_Plots_District.json"))

    assert [row.sheet_code for row in rows] == ["DR-077", "DR-097", "DR-116", "DR-134", "DR-152"]
    assert rows[0].master_plan_code == "DR-067"
    assert rows[1].master_plan_code == "DR-088"
    assert rows[2].master_plan_code == "DR-108"
    assert rows[3].master_plan_code == "DR-127"
    assert rows[4].master_plan_code == "DR-145"
    assert [row.metrics.far for row in rows] == [1.3, 1.4, 1.3, 1.3, 0.2]
    assert [row.metrics.building_density for row in rows] == [0.25, 0.28, 0.26, 0.25, 0.15]
    assert [row.metrics.green_ratio for row in rows] == [0.38, 0.35, 0.35, 0.35, 0.85]


def test_metric_card_unit_text_does_not_overlap_large_value():
    scale = 2
    fonts = _scaled_fonts(scale)
    img = Image.new("RGB", (1000, 360), "white")
    draw = ImageDraw.Draw(img)
    box = (0, 0, 1000, 320)
    value = "11,079"
    unit = "㎡ = 用地面积 × 绿地率"

    positions = metric_card_text_positions(draw, box, value, unit, fonts, scale)
    value_bottom = draw.textbbox(positions["value"], value, font=fonts["card_value"])[3]
    unit_box = draw.textbbox(positions["unit"], unit, font=fonts["small"])

    assert unit_box[1] - value_bottom >= 16
    assert unit_box[3] <= box[3] - 24 * scale
