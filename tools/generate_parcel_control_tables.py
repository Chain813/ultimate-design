# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
ATLAS_DIR = ROOT / "static" / "atlas"
BACKUP_DIR = ROOT / "static" / "atlas_backup" / "control_tables_before_recalc_20260619"
KEY_PLOTS_PATH = ROOT / "data" / "gis" / "Key_Plots_District.json"


@dataclass(frozen=True)
class ParcelMetrics:
    area_sqm: float
    far: float
    building_density: float
    green_ratio: float
    area_ha: float
    floor_area_sqm: float
    footprint_sqm: float
    green_sqm: float
    hardscape_sqm: float


@dataclass(frozen=True)
class ControlTableRow:
    sheet_code: str
    output_filename: str
    parcel_name: str
    positioning: str
    master_plan_code: str
    master_plan_name: str
    landuse: str
    height_limit: str
    metrics: ParcelMetrics


@dataclass(frozen=True)
class ControlSpec:
    sheet_code: str
    output_filename: str
    parcel_name: str
    positioning: str
    master_plan_code: str
    master_plan_name: str
    landuse: str
    far: float
    building_density: float
    green_ratio: float
    height_limit: str


CONTROL_SPECS = [
    ControlSpec(
        sheet_code="DR-077",
        output_filename="DR-077_老水产市场-控制性指标表.png",
        parcel_name="老水产市场",
        positioning="御花园东巷文创街区",
        master_plan_code="DR-067",
        master_plan_name="老水产市场-改造总平面图",
        landuse="B/A 混合用地",
        far=1.30,
        building_density=0.25,
        green_ratio=0.38,
        height_limit="≤18m",
    ),
    ControlSpec(
        sheet_code="DR-097",
        output_filename="DR-097_食品调料市场-控制性指标表.png",
        parcel_name="食品调料市场",
        positioning="活态市集·风味院落",
        master_plan_code="DR-088",
        master_plan_name="食品调料市场-改造总平面图",
        landuse="B/A 混合用地",
        far=1.40,
        building_density=0.28,
        green_ratio=0.35,
        height_limit="≤18m",
    ),
    ControlSpec(
        sheet_code="DR-116",
        output_filename="DR-116_市一中北侧-控制性指标表.png",
        parcel_name="市一中北侧",
        positioning="全龄共享生活社区",
        master_plan_code="DR-108",
        master_plan_name="市一中北侧-改造总平面图",
        landuse="A/R 混合用地",
        far=1.30,
        building_density=0.26,
        green_ratio=0.35,
        height_limit="≤15m",
    ),
    ControlSpec(
        sheet_code="DR-134",
        output_filename="DR-134_清禾集贸市场-控制性指标表.png",
        parcel_name="清禾集贸市场",
        positioning="历史界面缝合者",
        master_plan_code="DR-127",
        master_plan_name="清禾集贸市场-改造总平面图",
        landuse="B/A 混合用地",
        far=1.30,
        building_density=0.25,
        green_ratio=0.35,
        height_limit="≤15m",
    ),
    ControlSpec(
        sheet_code="DR-152",
        output_filename="DR-152_中国石油-控制性指标表.png",
        parcel_name="中国石油",
        positioning="宽城子能量花园",
        master_plan_code="DR-145",
        master_plan_name="中国石油-改造总平面图",
        landuse="G/B 混合用地",
        far=0.20,
        building_density=0.15,
        green_ratio=0.85,
        height_limit="≤6m",
    ),
]


def load_key_plot_areas(path: Path = KEY_PLOTS_PATH) -> list[float]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return [float(feature["properties"]["Shape_Area"]) for feature in data["features"]]


def calculate_metrics(area_sqm: float, far: float, building_density: float, green_ratio: float) -> ParcelMetrics:
    footprint_sqm = area_sqm * building_density
    green_sqm = area_sqm * green_ratio
    return ParcelMetrics(
        area_sqm=area_sqm,
        far=far,
        building_density=building_density,
        green_ratio=green_ratio,
        area_ha=area_sqm / 10000,
        floor_area_sqm=area_sqm * far,
        footprint_sqm=footprint_sqm,
        green_sqm=green_sqm,
        hardscape_sqm=max(area_sqm - footprint_sqm - green_sqm, 0.0),
    )


def build_control_table_rows(path: Path = KEY_PLOTS_PATH) -> list[ControlTableRow]:
    areas = load_key_plot_areas(path)
    if len(areas) < len(CONTROL_SPECS):
        raise ValueError(f"Expected at least {len(CONTROL_SPECS)} key plot areas, got {len(areas)}")

    rows: list[ControlTableRow] = []
    for spec, area_sqm in zip(CONTROL_SPECS, areas):
        rows.append(
            ControlTableRow(
                sheet_code=spec.sheet_code,
                output_filename=spec.output_filename,
                parcel_name=spec.parcel_name,
                positioning=spec.positioning,
                master_plan_code=spec.master_plan_code,
                master_plan_name=spec.master_plan_name,
                landuse=spec.landuse,
                height_limit=spec.height_limit,
                metrics=calculate_metrics(area_sqm, spec.far, spec.building_density, spec.green_ratio),
            )
        )
    return rows


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
    ]
    for font_path in candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _scaled_fonts(scale: int) -> dict[str, ImageFont.FreeTypeFont | ImageFont.ImageFont]:
    return {
        "title": _font(38 * scale, True),
        "subtitle": _font(18 * scale),
        "section": _font(24 * scale, True),
        "card_label": _font(18 * scale, True),
        "card_value": _font(32 * scale, True),
        "header": _font(18 * scale, True),
        "cell": _font(17 * scale),
        "cell_bold": _font(17 * scale, True),
        "note": _font(16 * scale),
        "note_bold": _font(16 * scale, True),
        "small": _font(14 * scale),
    }


def _draw_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font, fill=(15, 23, 42)) -> None:
    draw.text(xy, text, font=font, fill=fill)


def _fmt_sqm(value: float) -> str:
    return f"{value:,.0f}"


def _fmt_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _draw_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], accent: tuple[int, int, int]) -> None:
    x1, y1, x2, y2 = box
    draw.rectangle([x1 + 6, y1 + 6, x2 + 6, y2 + 6], fill=(226, 232, 240))
    draw.rectangle([x1, y1, x2, y2], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([x1, y1, x2, y1 + 8], fill=accent)


def metric_card_text_positions(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    value: str,
    unit: str,
    fonts: dict[str, ImageFont.ImageFont],
    scale: int,
) -> dict[str, tuple[int, int]]:
    x1, y1, _, y2 = box
    text_x = x1 + 24 * scale
    label_y = y1 + 24 * scale
    value_y = y1 + 58 * scale

    value_box = draw.textbbox((text_x, value_y), value, font=fonts["card_value"])
    unit_origin_box = draw.textbbox((0, 0), unit, font=fonts["small"])
    unit_y = value_box[3] + 12 * scale - unit_origin_box[1]
    unit_box = draw.textbbox((text_x, unit_y), unit, font=fonts["small"])

    max_unit_bottom = y2 - 24 * scale
    if unit_box[3] > max_unit_bottom:
        unit_y -= unit_box[3] - max_unit_bottom

    return {
        "label": (text_x, label_y),
        "value": (text_x, value_y),
        "unit": (text_x, unit_y),
    }


def _draw_metric_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    value: str,
    unit: str,
    fonts: dict[str, ImageFont.ImageFont],
    accent: tuple[int, int, int],
    scale: int,
) -> None:
    _draw_card(draw, box, accent)
    positions = metric_card_text_positions(draw, box, value, unit, fonts, scale)
    _draw_text(draw, positions["label"], label, fonts["card_label"], (71, 85, 105))
    _draw_text(draw, positions["value"], value, fonts["card_value"], (15, 23, 42))
    _draw_text(draw, positions["unit"], unit, fonts["small"], (100, 116, 139))


def _draw_table(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    col_widths: list[int],
    row_h: int,
    headers: list[str],
    rows: list[list[str]],
    fonts: dict[str, ImageFont.ImageFont],
) -> int:
    total_w = sum(col_widths)
    draw.rectangle([x, y, x + total_w, y + row_h], fill=(241, 245, 249), outline=(203, 213, 225), width=2)
    cx = x
    for header, width in zip(headers, col_widths):
        _draw_text(draw, (cx + 16, y + 17), header, fonts["header"], (51, 65, 85))
        cx += width

    cy = y + row_h
    for ri, row in enumerate(rows):
        fill = (255, 255, 255) if ri % 2 == 0 else (248, 250, 252)
        draw.rectangle([x, cy, x + total_w, cy + row_h], fill=fill)
        cx = x
        for ci, (cell, width) in enumerate(zip(row, col_widths)):
            font = fonts["cell_bold"] if ci in (0, 2) else fonts["cell"]
            color = (15, 23, 42) if ci != 3 else (13, 148, 136)
            _draw_text(draw, (cx + 16, cy + 18), cell, font, color)
            cx += width
        cy += row_h

    bottom = cy
    draw.rectangle([x, y, x + total_w, bottom], outline=(203, 213, 225), width=2)
    line_y = y + row_h
    while line_y < bottom:
        draw.line([(x, line_y), (x + total_w, line_y)], fill=(226, 232, 240), width=1)
        line_y += row_h
    cx = x
    for width in col_widths[:-1]:
        cx += width
        draw.line([(cx, y), (cx, bottom)], fill=(226, 232, 240), width=1)
    return bottom


def draw_control_table(row: ControlTableRow, output_path: Path, scale: int = 2) -> None:
    width, height = 2240 * scale, 1584 * scale
    fonts = _scaled_fonts(scale)
    accent = (13, 148, 136)
    purple = (124, 58, 237)
    img = Image.new("RGB", (width, height), (248, 250, 252))
    draw = ImageDraw.Draw(img)

    grid = int(79.2 * scale)
    for x in range(grid, width, grid):
        draw.line([(x, 0), (x, height)], fill=(226, 232, 240), width=1)
    for y in range(grid, height, grid):
        draw.line([(0, y), (width, y)], fill=(226, 232, 240), width=1)

    m = row.metrics
    _draw_card(draw, (32 * scale, 42 * scale, 2208 * scale, 164 * scale), accent)
    _draw_text(
        draw,
        (58 * scale, 76 * scale),
        f"{row.positioning}地块 — 控制性指标表",
        fonts["title"],
    )
    _draw_text(
        draw,
        (58 * scale, 126 * scale),
        f"依据改造后总平面图 {row.master_plan_code}《{row.master_plan_name}》计算；地块红线面积采用 Key_Plots_District.Shape_Area。",
        fonts["subtitle"],
        (71, 85, 105),
    )
    _draw_text(draw, (1900 * scale, 82 * scale), row.sheet_code, fonts["title"], accent)

    card_y = 210 * scale
    card_w = 500 * scale
    gap = 32 * scale
    x0 = 80 * scale
    metric_cards = [
        ("用地面积", f"{m.area_ha:.2f}", "ha"),
        ("总建筑面积", _fmt_sqm(m.floor_area_sqm), "㎡ = 用地面积 × FAR"),
        ("建筑基底面积", _fmt_sqm(m.footprint_sqm), "㎡ = 用地面积 × 建筑密度"),
        ("绿地面积", _fmt_sqm(m.green_sqm), "㎡ = 用地面积 × 绿地率"),
    ]
    for idx, (label, value, unit) in enumerate(metric_cards):
        x = x0 + idx * (card_w + gap)
        _draw_metric_card(draw, (x, card_y, x + card_w, card_y + 160 * scale), label, value, unit, fonts, accent, scale)

    table_x = 80 * scale
    table_y = 430 * scale
    _draw_text(draw, (table_x, table_y - 54 * scale), "一、改造后总平面图计算指标", fonts["section"], (15, 23, 42))
    headers = ["指标项", "计算依据", "计算值", "单位/控制口径", "备注"]
    col_widths = [280, 520, 300, 260, 720]
    col_widths = [w * scale for w in col_widths]
    table_rows = [
        ["用地面积", "地块红线 Shape_Area", f"{_fmt_sqm(m.area_sqm)} / {m.area_ha:.2f}", "㎡ / ha", "采用重点地块边界面积，不使用现状卫星图估算。"],
        ["容积率", "总建筑面积 ÷ 用地面积", f"{m.far:.2f}", "FAR", f"与改造后总平面图 {row.master_plan_code} 的开发强度一致。"],
        ["总建筑面积", "用地面积 × 容积率", _fmt_sqm(m.floor_area_sqm), "㎡", "用于核算可建设计量与公共服务配套规模。"],
        ["建筑密度", "建筑基底面积 ÷ 用地面积", _fmt_pct(m.building_density), "%", "反映改造后建筑落位对场地的占用强度。"],
        ["建筑基底面积", "用地面积 × 建筑密度", _fmt_sqm(m.footprint_sqm), "㎡", "对应总平面图中的改造后建筑轮廓控制。"],
        ["绿地率", "绿地面积 ÷ 用地面积", _fmt_pct(m.green_ratio), "%", "按改造后绿化系统与开放空间组织控制。"],
        ["绿地面积", "用地面积 × 绿地率", _fmt_sqm(m.green_sqm), "㎡", "包含口袋公园、庭院绿化、边界绿带等。"],
        ["硬质活动/道路广场", "用地面积 - 建筑基底 - 绿地", _fmt_sqm(m.hardscape_sqm), "㎡", "用于慢行、消防、运营集散及市集活动空间。"],
        ["建筑限高", "总平面及高度管控", row.height_limit, "m", "满足历史风貌敏感区和街区天际线控制要求。"],
        ["用地性质", "改造后功能定位", row.landuse, "--", row.positioning],
    ]
    table_bottom = _draw_table(draw, table_x, table_y, col_widths, 56 * scale, headers, table_rows, fonts)

    left_box = (80 * scale, table_bottom + 56 * scale, 1080 * scale, 1500 * scale)
    right_box = (1160 * scale, table_bottom + 56 * scale, 2160 * scale, 1500 * scale)
    _draw_card(draw, left_box, purple)
    _draw_card(draw, right_box, purple)

    _draw_text(draw, (left_box[0] + 28 * scale, left_box[1] + 36 * scale), "二、计算口径", fonts["section"], purple)
    method_lines = [
        f"1. 面积基准：{m.area_sqm:,.2f}㎡，来自五个重点地块矢量红线 Shape_Area。",
        f"2. 强度基准：采用改造后总平面图 {row.master_plan_code}，不是现状卫星图或现状建筑轮廓。",
        "3. 建筑基底、总建筑面积、绿地面积均由总平控制参数反算，保证表内指标闭合。",
        "4. 各项数值按控规图则表达四舍五入，计算底稿保留完整浮点精度。",
    ]
    y = left_box[1] + 92 * scale
    for line in method_lines:
        _draw_text(draw, (left_box[0] + 34 * scale, y), line, fonts["note"], (51, 65, 85))
        y += 44 * scale

    _draw_text(draw, (right_box[0] + 28 * scale, right_box[1] + 36 * scale), "三、控制结论", fonts["section"], purple)
    conclusion_lines = [
        f"1. {row.parcel_name}改造后控制容积率为 {m.far:.2f}，对应总建筑面积约 {_fmt_sqm(m.floor_area_sqm)}㎡。",
        f"2. 建筑密度控制为 {_fmt_pct(m.building_density)}，建筑基底约 {_fmt_sqm(m.footprint_sqm)}㎡，为绿化和公共活动留出空间。",
        f"3. 绿地率控制为 {_fmt_pct(m.green_ratio)}，绿地面积约 {_fmt_sqm(m.green_sqm)}㎡，形成改造后生态修补指标。",
        f"4. 建筑高度按 {row.height_limit} 控制，服务于{row.positioning}的街区风貌与天际线要求。",
    ]
    y = right_box[1] + 92 * scale
    for line in conclusion_lines:
        _draw_text(draw, (right_box[0] + 34 * scale, y), line, fonts["note"], (51, 65, 85))
        y += 44 * scale

    draw.rectangle([32 * scale, 1532 * scale, 2208 * scale, 1540 * scale], fill=accent)
    _draw_text(
        draw,
        (58 * scale, 1550 * scale),
        "注：本表为改造后总平面图推算指标表，现状卫星图、现状用地和现状建筑高度图仅用于诊断，不参与本表计算。",
        fonts["small"],
        (71, 85, 105),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, compress_level=6)


def _find_existing_atlas_path(filename: str) -> Path:
    code = filename.split("_", 1)[0]
    matches = sorted(ATLAS_DIR.glob(f"{code}_*.png"))
    return matches[0] if matches else ATLAS_DIR / filename


def generate_control_tables(rows: list[ControlTableRow] | None = None) -> list[Path]:
    rows = build_control_table_rows() if rows is None else rows
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    output_paths: list[Path] = []
    for row in rows:
        output_path = _find_existing_atlas_path(row.output_filename)
        backup_path = BACKUP_DIR / output_path.name
        if output_path.exists() and not backup_path.exists():
            shutil.copy2(output_path, backup_path)
        draw_control_table(row, output_path)
        output_paths.append(output_path)
        print(f"Generated {row.sheet_code}: {output_path}")
    return output_paths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codes", help="Comma-separated sheet codes, for example DR-077,DR-097.")
    args = parser.parse_args()
    rows = build_control_table_rows()
    if args.codes:
        wanted = {code.strip().upper() for code in args.codes.split(",")}
        rows = [row for row in rows if row.sheet_code.upper() in wanted]
    generate_control_tables(rows)


if __name__ == "__main__":
    main()
