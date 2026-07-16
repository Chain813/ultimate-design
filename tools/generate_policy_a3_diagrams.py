from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CONTENT_PATH = ROOT / "data" / "policy_board_content.json"
GENERATED_DIR = ROOT / "static" / "atlas" / "policy_a3" / "generated"

FORBIDDEN_REAL_MAP_TERMS = (
    "真实地图",
    "卫星图",
    "遥感",
    "地理底图",
    "行政边界",
    "道路底图",
    "经纬度",
    "坐标",
    "OSM",
    "mapbox",
)

W, H = 1200, 1697
COLORS = {
    "paper": "#f6f7f8",
    "panel": "#ffffff",
    "ink": "#172033",
    "muted": "#5d6a76",
    "line": "#d7dde2",
    "red": "#c13a2b",
    "teal": "#007c78",
    "orange": "#d97706",
    "gold": "#c99a2e",
    "blue": "#315f96",
    "green": "#4f8a45",
}


def load_policy_content(path: Path = CONTENT_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _tool_names(content: dict[str, Any]) -> list[str]:
    return [item["name"] for item in content.get("policy_tools", [])]


def build_sheet_specs(content: dict[str, Any]) -> list[dict[str, Any]]:
    loop_nodes = content.get("loop_nodes", [])
    tools = content.get("policy_tools", [])
    tool_names = _tool_names(content)
    return [
        {
            "file": "a3_policy_01_loop.png",
            "title": "三方良性循环机制图",
            "subtitle": "政府定规则 · 市场做运营 · 居民得收益 · 社区再反馈",
            "modules": ["三方主体", "收益流线", "政策触发", "治理复盘", "实施指标"],
            "nodes": [
                {"label": f"{loop_nodes[0]['role']}｜{loop_nodes[0]['title']}", "body": loop_nodes[0]["body"]},
                {"label": f"{loop_nodes[1]['role']}｜{loop_nodes[1]['title']}", "body": loop_nodes[1]["body"]},
                {"label": f"{loop_nodes[2]['role']}｜{loop_nodes[2]['title']}", "body": loop_nodes[2]["body"]},
            ],
            "indicators": ["公共投入", "运营现金流", "社区基金", "满意度复盘", "二次投入"],
        },
        {
            "file": "a3_policy_02_tools.png",
            "title": "经济政策工具矩阵图",
            "subtitle": "把政策工具落实到政府、平台、资本、社区与居民五类主体",
            "modules": ["主体矩阵", "工具组合", "激励约束", "资金来源", "绩效指标"],
            "rows": tool_names,
            "cols": ["政府", "平台公司", "社会资本", "社区组织", "居民"],
            "cells": ["引导", "执行", "投资", "协同", "受益", "约束"],
        },
        {
            "file": "a3_policy_03_market.png",
            "title": "市场运营与收益回流图",
            "subtitle": "从业态导入到收益再投入，形成街区长期自我造血链条",
            "modules": ["业态组合", "客流增长", "租金稳定", "收益分成", "社区再投入", "滚动更新"],
            "steps": ["业态导入", "客流提升", "经营收入", "收益分成", "社区再投入", "下一地块启动"],
            "parcels": ["市集更新", "风味街巷", "校园边界", "社区商业", "服务节点"],
        },
        {
            "file": "a3_policy_04_residents.png",
            "title": "居民收益与治理反馈图",
            "subtitle": "把就业、服务、空间品质与协商治理纳入经济循环稳定器",
            "modules": ["就业机会", "公共服务", "空间品质", "社区基金", "协商议事", "满意度复盘"],
            "benefits": ["就业增收", "便民服务", "慢行环境", "基金共治"],
            "feedback": ["需求提出", "方案共创", "资金公示", "绩效评价", "滚动修正"],
        },
    ]


def _walk_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        result: list[str] = []
        for item in value.values():
            result.extend(_walk_values(item))
        return result
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(_walk_values(item))
        return result
    return []


def spec_uses_real_map_terms(spec: dict[str, Any]) -> bool:
    text = "\n".join(_walk_values(spec)).lower()
    return any(term.lower() in text for term in FORBIDDEN_REAL_MAP_TERMS)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/simfang.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


F_TITLE = _font(48, True)
F_SUB = _font(24)
F_H = _font(27, True)
F_B = _font(21, True)
F_TXT = _font(18)
F_SMALL = _font(15)
F_NUM = _font(42, True)


def _wrap(draw: ImageDraw.ImageDraw, value: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in value:
        test = current + char
        if draw.textlength(test, font=font) <= width or not current:
            current = test
        else:
            lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines


def _multiline(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    value: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
    width: int,
    line_height: int,
    max_lines: int = 5,
) -> int:
    x, y = xy
    for line in _wrap(draw, value, font, width)[:max_lines]:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def _rounded(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str,
    outline: str | None = None,
    width: int = 2,
    radius: int = 18,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    fill: str,
    width: int = 8,
) -> None:
    draw.line((start, end), fill=fill, width=width)
    sx, sy = start
    ex, ey = end
    angle = math.atan2(ey - sy, ex - sx)
    size = 24
    draw.polygon(
        [
            (ex, ey),
            (ex - size * math.cos(angle - math.pi / 7), ey - size * math.sin(angle - math.pi / 7)),
            (ex - size * math.cos(angle + math.pi / 7), ey - size * math.sin(angle + math.pi / 7)),
        ],
        fill=fill,
    )


def _base(title: str, subtitle: str, code: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (W, H), COLORS["paper"])
    draw = ImageDraw.Draw(image)
    for x in range(0, W, 58):
        draw.line((x, 0, x, H), fill="#e2e7eb")
    for y in range(0, H, 58):
        draw.line((0, y, W, y), fill="#e2e7eb")
    draw.rectangle((0, 0, W, 112), fill=COLORS["ink"])
    draw.rectangle((0, 112, W, 126), fill=COLORS["red"])
    draw.text((42, 27), title, font=F_TITLE, fill="white")
    draw.text((42, 135), subtitle, font=F_SUB, fill=COLORS["muted"])
    draw.rectangle((1010, 24, 1146, 88), fill=COLORS["red"])
    draw.text((1078, 56), code, font=F_NUM, fill="white", anchor="mm")
    return image, draw


def _draw_module_tabs(draw: ImageDraw.ImageDraw, modules: list[str], y: int) -> None:
    x = 54
    for index, module in enumerate(modules):
        color = [COLORS["red"], COLORS["blue"], COLORS["teal"], COLORS["orange"], COLORS["gold"], COLORS["green"]][
            index % 6
        ]
        _rounded(draw, (x, y, x + 168, y + 48), color, radius=9)
        draw.text((x + 84, y + 24), module, font=F_SMALL, fill="white", anchor="mm")
        x += 178


def _draw_loop_sheet(spec: dict[str, Any], output: Path) -> None:
    image, draw = _base(spec["title"], spec["subtitle"], "A3-1")
    _draw_module_tabs(draw, spec["modules"], 198)
    draw.ellipse((356, 535, 844, 1023), outline=COLORS["gold"], width=30)
    _rounded(draw, (462, 680, 738, 850), COLORS["ink"], radius=18)
    draw.text((600, 728), "共识中枢", font=F_H, fill="white", anchor="mm")
    draw.text((600, 772), "投入 / 运营 / 收益 / 共治", font=F_SMALL, fill="#d7dde2", anchor="mm")
    boxes = [
        (78, 350, 438, 565, COLORS["red"]),
        (760, 565, 1120, 780, COLORS["teal"]),
        (215, 1072, 575, 1287, COLORS["orange"]),
    ]
    for node, (x1, y1, x2, y2, color) in zip(spec["nodes"], boxes):
        _rounded(draw, (x1, y1, x2, y2), color, radius=18)
        draw.text((x1 + 28, y1 + 28), node["label"], font=F_B, fill="white")
        _multiline(draw, (x1 + 28, y1 + 70), node["body"], F_SMALL, "white", x2 - x1 - 54, 23, max_lines=5)
    _arrow(draw, (420, 560), (766, 650), COLORS["red"], width=9)
    _arrow(draw, (848, 780), (570, 1085), COLORS["teal"], width=9)
    _arrow(draw, (260, 1070), (172, 565), COLORS["orange"], width=9)
    y = 1370
    for index, item in enumerate(spec["indicators"]):
        _rounded(draw, (88 + index * 210, y, 270 + index * 210, y + 58), COLORS["panel"], COLORS["line"], 2, 10)
        draw.text((179 + index * 210, y + 29), item, font=F_SMALL, fill=COLORS["ink"], anchor="mm")
    image.save(output)


def _draw_matrix_sheet(spec: dict[str, Any], output: Path) -> None:
    image, draw = _base(spec["title"], spec["subtitle"], "A3-2")
    _draw_module_tabs(draw, spec["modules"], 198)
    left, top = 64, 330
    row_w, cell_w, cell_h = 176, 176, 116
    for c, col in enumerate(spec["cols"]):
        x = left + row_w + c * cell_w
        _rounded(draw, (x, top - 72, x + cell_w - 12, top - 16), COLORS["ink"], radius=10)
        draw.text((x + cell_w / 2 - 6, top - 44), col, font=F_SMALL, fill="white", anchor="mm")
    colors = [COLORS["red"], COLORS["blue"], COLORS["orange"], COLORS["teal"], COLORS["gold"], COLORS["green"]]
    for r, row in enumerate(spec["rows"][:6]):
        y = top + r * cell_h
        _rounded(draw, (left, y, left + row_w - 18, y + cell_h - 12), colors[r], radius=10)
        draw.text((left + row_w / 2 - 9, y + cell_h / 2 - 6), row, font=F_B, fill="white", anchor="mm")
        for c, _col in enumerate(spec["cols"]):
            x = left + row_w + c * cell_w
            fill = "#ffffff" if (r + c) % 2 == 0 else "#eef2f4"
            _rounded(draw, (x, y, x + cell_w - 12, y + cell_h - 12), fill, COLORS["line"], 1, 10)
            value = spec["cells"][(r + c) % len(spec["cells"])]
            draw.text((x + cell_w / 2 - 6, y + cell_h / 2 - 6), value, font=F_SMALL, fill=COLORS["ink"], anchor="mm")
    notes = ["公共资金撬动社会资本", "增量收益支撑长期运营", "居民满意度约束政策复盘"]
    for index, note in enumerate(notes):
        _rounded(draw, (120, 1220 + index * 76, 1080, 1275 + index * 76), COLORS["panel"], COLORS["line"], 2, 10)
        draw.text((150, 1237 + index * 76), note, font=F_B, fill=COLORS["ink"])
    image.save(output)


def _draw_market_sheet(spec: dict[str, Any], output: Path) -> None:
    image, draw = _base(spec["title"], spec["subtitle"], "A3-3")
    _draw_module_tabs(draw, spec["modules"], 198)
    step_colors = [COLORS["red"], COLORS["orange"], COLORS["teal"], COLORS["blue"], COLORS["gold"], COLORS["green"]]
    x0, y0 = 58, 390
    for index, step in enumerate(spec["steps"]):
        x = x0 + index * 184
        _rounded(draw, (x, y0, x + 150, y0 + 210), step_colors[index], radius=18)
        draw.text((x + 75, y0 + 42), f"{index + 1}", font=F_NUM, fill="white", anchor="mm")
        _multiline(draw, (x + 24, y0 + 86), step, F_B, "white", 102, 28, max_lines=2)
        if index < len(spec["steps"]) - 1:
            _arrow(draw, (x + 152, y0 + 106), (x + 180, y0 + 106), COLORS["ink"], width=5)
    _rounded(draw, (118, 735, 1082, 1116), COLORS["panel"], COLORS["line"], 2, 18)
    draw.text((154, 780), "五类更新样本的运营强度与收益回流优先级", font=F_H, fill=COLORS["ink"])
    values = [0.86, 0.72, 0.62, 0.68, 0.54]
    for index, (parcel, value) in enumerate(zip(spec["parcels"], values)):
        y = 850 + index * 48
        draw.text((160, y), parcel, font=F_SMALL, fill=COLORS["ink"])
        draw.rectangle((390, y + 4, 1010, y + 27), fill="#e6ebef")
        draw.rectangle((390, y + 4, 390 + int(620 * value), y + 27), fill=step_colors[index])
    _rounded(draw, (118, 1190, 1082, 1345), COLORS["ink"], radius=18)
    draw.text((600, 1238), "示范节点现金流 → 公共维护 → 下一地块启动", font=F_B, fill="white", anchor="mm")
    draw.text((600, 1288), "以滚动收益降低一次性开发压力，避免空间更新透支", font=F_SMALL, fill="#d7dde2", anchor="mm")
    image.save(output)


def _draw_resident_sheet(spec: dict[str, Any], output: Path) -> None:
    image, draw = _base(spec["title"], spec["subtitle"], "A3-4")
    _draw_module_tabs(draw, spec["modules"], 198)
    benefit_colors = [COLORS["red"], COLORS["teal"], COLORS["orange"], COLORS["gold"]]
    bodies = ["本地岗位、导览服务、市集运营", "适老托育、卫生便民、邻里商业", "慢行街巷、口袋公园、夜间照明", "微更新资金、困难群体支持、共治预算"]
    for index, (benefit, body) in enumerate(zip(spec["benefits"], bodies)):
        row, col = divmod(index, 2)
        x, y = 92 + col * 515, 330 + row * 235
        _rounded(draw, (x, y, x + 428, y + 176), COLORS["panel"], benefit_colors[index], 5, 18)
        draw.ellipse((x + 28, y + 34, x + 94, y + 100), fill=benefit_colors[index])
        draw.text((x + 61, y + 67), str(index + 1), font=F_H, fill="white", anchor="mm")
        draw.text((x + 122, y + 42), benefit, font=F_H, fill=COLORS["ink"])
        _multiline(draw, (x + 122, y + 86), body, F_SMALL, COLORS["muted"], 250, 24, max_lines=3)
    _rounded(draw, (182, 900, 1018, 1175), COLORS["ink"], radius=20)
    draw.text((600, 950), "居民协商议事闭环", font=F_H, fill="white", anchor="mm")
    points = [(325, 1048), (492, 995), (674, 1048), (492, 1106), (600, 1106)]
    colors = [COLORS["red"], COLORS["teal"], COLORS["orange"], COLORS["green"], COLORS["gold"]]
    for index, (label, point) in enumerate(zip(spec["feedback"], points)):
        draw.ellipse((point[0] - 62, point[1] - 34, point[0] + 62, point[1] + 34), fill=colors[index])
        draw.text(point, label, font=F_SMALL, fill="white", anchor="mm")
    for start, end in zip(points, points[1:] + points[:1]):
        _arrow(draw, start, end, COLORS["gold"], width=4)
    _rounded(draw, (120, 1255, 1080, 1370), COLORS["panel"], COLORS["line"], 2, 18)
    draw.text((600, 1298), "民生改善不是结果说明，而是经济循环中的稳定器", font=F_B, fill=COLORS["ink"], anchor="mm")
    draw.text((600, 1342), "稳定获得感 → 稳定消费 → 稳定参与 → 稳定治理", font=F_SMALL, fill=COLORS["muted"], anchor="mm")
    image.save(output)


def generate_policy_a3_diagrams(content: dict[str, Any] | None = None, output_dir: Path = GENERATED_DIR) -> list[Path]:
    content = content or load_policy_content()
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for index, spec in enumerate(build_sheet_specs(content), start=1):
        if spec_uses_real_map_terms(spec):
            raise ValueError(f"Policy A3 spec contains real-map terms: {spec['title']}")
        output = output_dir / spec["file"]
        if index == 1:
            _draw_loop_sheet(spec, output)
        elif index == 2:
            _draw_matrix_sheet(spec, output)
        elif index == 3:
            _draw_market_sheet(spec, output)
        elif index == 4:
            _draw_resident_sheet(spec, output)
        outputs.append(output)
    return outputs


def main() -> None:
    for output in generate_policy_a3_diagrams():
        print(output)


if __name__ == "__main__":
    main()
