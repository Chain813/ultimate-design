# -*- coding: utf-8 -*-
"""Generate dense technical diagrams for A1 exhibition board 01."""
from __future__ import annotations

from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "static" / "exhibition_boards" / "tech_diagrams"

NAVY = "#111827"
INK = "#172033"
MUTED = "#5d6a76"
LINE = "#d7dde2"
PAPER = "#f6f8fa"
LIGHT_PANEL = "#eef2f6"
BLUE = "#315f96"
TEAL = "#007c78"
RED = "#c13a2b"
ORANGE = "#d97706"
GREEN = "#4f8a45"
GOLD = "#c99a2e"
PURPLE = "#7c3aed"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


FONT_TITLE = _font(48, True)
FONT_H2 = _font(32, True)
FONT_BODY = _font(26)
FONT_SMALL = _font(22)
FONT_TINY = _font(19)


def canvas(width: int, height: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(img)
    for x in range(0, width, 64):
        draw.line((x, 0, x, height), fill="#e8edf1", width=1)
    for y in range(0, height, 64):
        draw.line((0, y, width, y), fill="#e8edf1", width=1)
    return img, draw


def wrap_text_by_width(text_str: str, font, max_width_px: int) -> list[str]:
    lines = []
    for paragraph in text_str.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        current_line = ""
        for char in paragraph:
            test_line = current_line + char
            bbox = font.getbbox(test_line)
            width = bbox[2] - bbox[0]
            if width <= max_width_px:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = char
                else:
                    lines.append(char)
                    current_line = ""
        if current_line:
            lines.append(current_line)
    return lines


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, font, fill=INK, width: int | None = None, line_gap: int = 6) -> int:
    x, y = xy
    if width is None:
        draw.text((x, y), value, font=font, fill=fill)
        return y + int(font.size * 1.3)
    
    lines = wrap_text_by_width(value, font, width)
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + line_gap
    return y


def rounded(draw: ImageDraw.ImageDraw, box, fill="#ffffff", outline=LINE, radius=18, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def arrow(draw: ImageDraw.ImageDraw, start, end, fill=BLUE, width=4):
    draw.line((start, end), fill=fill, width=width)
    x1, y1 = start
    x2, y2 = end
    if abs(x2 - x1) >= abs(y2 - y1):
        sign = 1 if x2 >= x1 else -1
        pts = [(x2, y2), (x2 - 18 * sign, y2 - 10), (x2 - 18 * sign, y2 + 10)]
    else:
        sign = 1 if y2 >= y1 else -1
        pts = [(x2, y2), (x2 - 10, y2 - 18 * sign), (x2 + 10, y2 - 18 * sign)]
    draw.polygon(pts, fill=fill)


def node(draw, box, title, body, color=BLUE):
    rounded(draw, box, fill="#ffffff", outline=color, radius=20, width=4)
    x0, y0, x1, _ = box
    draw.rectangle((x0, y0, x1, y0 + 12), fill=color)
    y = text(draw, (x0 + 24, y0 + 28), title, FONT_H2, fill=INK, width=x1 - x0 - 48)
    text(draw, (x0 + 24, y + 6), body, FONT_SMALL, fill=MUTED, width=x1 - x0 - 48)


def draw_architecture() -> None:
    img, d = canvas(2200, 900)
    text(d, (42, 30), "平台总体架构 / Platform Architecture", FONT_TITLE, INK)
    layers = [
        ("界面交互层", "Streamlit 多页面工作台、3D 全息底座、AIGC 参数面板、成果预览与导出", TEAL),
        ("工作流编排层", "S00-S15 阶段路由、StageDataBus、Persistent Outputs、证据链条", BLUE),
        ("空间计算层", "GeoPandas / AHP-MPI / 雷达诊断 / 日照与天际线 / 用地沙盘", GREEN),
        ("AI 推演层", "RAG 知识库、LLM 报告生成、ControlNet 深度约束、图像增强", PURPLE),
        ("成果生产层", "Atlas 图册、控制性指标表、A1 展板、答辩稿与动态录屏", ORANGE),
    ]
    x, y, w, h = 58, 120, 392, 590
    centers = []
    for i, (title, body, color) in enumerate(layers):
        bx = (x + i * (w + 34), y, x + i * (w + 34) + w, y + h)
        node(d, bx, title, body, color)
        centers.append((bx[0] + w // 2, bx[3]))
        if i < len(layers) - 1:
            arrow(d, (bx[2] + 6, y + h // 2), (bx[2] + 34, y + h // 2), fill=color, width=5)
    for i, c in enumerate(centers[:-1]):
        arrow(d, (c[0], c[1] + 24), (centers[i + 1][0], centers[i + 1][1] + 24), fill="#8b5cf6", width=3)
    text(d, (58, 760), "闭环逻辑：每一阶段既产生图纸/文本成果，也把诊断指标、策略约束与空间参数回写到后续阶段。", FONT_BODY, INK, width=1500)
    rounded(d, (1680, 730, 2138, 846), fill="#fff7ed", outline=ORANGE, radius=18, width=3)
    text(d, (1710, 755), "核心特征", FONT_H2, ORANGE)
    text(d, (1710, 800), "真实数据底座 + AI 协同推演 + 代码制图 + 可复核交付", FONT_SMALL, INK, width=380)
    img.save(OUT_DIR / "board01_platform_architecture.png", quality=95)


def draw_workflow() -> None:
    img, d = canvas(2200, 900)
    text(d, (42, 30), "S00-S15 全流程泳道 / End-to-End Workflow", FONT_TITLE, INK)
    lanes = [("数据底座", TEAL), ("诊断评价", BLUE), ("策略生成", GREEN), ("设计推演", PURPLE), ("成果交付", ORANGE)]
    y0 = 126
    for idx, (label, color) in enumerate(lanes):
        y = y0 + idx * 136
        d.rectangle((50, y, 2150, y + 96), fill="#ffffff", outline=LINE, width=2)
        d.rectangle((50, y, 210, y + 96), fill=color)
        text(d, (76, y + 30), label, FONT_H2, "#ffffff")
    stages = [
        ("S00", "数据准备", 0), ("S01", "任务解读", 0), ("S02", "资料收集", 0), ("S03", "现场调研", 0),
        ("S04", "现状分析", 1), ("S05", "问题诊断", 1), ("S06", "目标定位", 2), ("S07", "策略协商", 2),
        ("S08", "总体设计", 3), ("S09", "专项系统", 3), ("S10", "地块深化", 3), ("S11", "实施路径", 3),
        ("S12", "设计导则", 4), ("S13", "成果表达", 4), ("S14", "大屏集成", 4), ("S15", "AIGC 工具", 3),
    ]
    xs = [250 + i * 116 for i in range(16)]
    prev = None
    for i, (code, label, lane) in enumerate(stages):
        x = xs[i]
        y = y0 + lane * 136 + 18
        color = lanes[lane][1]
        rounded(d, (x, y, x + 96, y + 60), fill="#f8fafc", outline=color, radius=14, width=3)
        text(d, (x + 13, y + 8), code, FONT_SMALL, color)
        text(d, (x + 12, y + 32), label, FONT_TINY, INK)
        if prev:
            arrow(d, (prev[0] + 98, prev[1] + 30), (x - 8, y + 30), fill="#94a3b8", width=3)
        prev = (x, y)
    feedback = [((830, 318), (1020, 454), "诊断回流策略"), ((1370, 590), (1595, 726), "设计回流图册"), ((1830, 726), (1970, 590), "成果回写模型")]
    for start, end, label in feedback:
        arrow(d, start, end, fill=RED, width=4)
        text(d, ((start[0] + end[0]) // 2 - 60, (start[1] + end[1]) // 2 - 25), label, FONT_TINY, RED)
    img.save(OUT_DIR / "board01_workflow_s00_s15.png", quality=95)


def draw_data_loop() -> None:
    img, d = canvas(1500, 900)
    text(d, (36, 28), "数据到成果闭环", FONT_TITLE, INK)
    steps = [
        ("01", "多源输入", "GIS / POI / 街景 / 任务书"),
        ("02", "数据治理", "字段清洗、坐标校正、资产挂接"),
        ("03", "空间计算", "MPI、GVI、可达性、天际线"),
        ("04", "AI 生成", "LLM 报告、AIGC 图像、策略推演"),
        ("05", "代码制图", "专题图、总平、指标表"),
        ("06", "交付校核", "Atlas / A1 / 文档 / 视频"),
    ]
    center = (750, 480)
    positions = [(750, 150), (1120, 300), (1120, 640), (750, 790), (380, 640), (380, 300)]
    for i, (num, title, body) in enumerate(steps):
        x, y = positions[i]
        rounded(d, (x - 170, y - 70, x + 170, y + 70), fill="#ffffff", outline=[TEAL, BLUE, GREEN, PURPLE, ORANGE, RED][i], radius=22, width=4)
        text(d, (x - 145, y - 48), f"{num} {title}", FONT_H2, [TEAL, BLUE, GREEN, PURPLE, ORANGE, RED][i])
        text(d, (x - 145, y - 10), body, FONT_SMALL, MUTED, width=290)
        nx, ny = positions[(i + 1) % len(positions)]
        arrow(d, (x + (70 if nx > x else -70), y), (nx + (-190 if nx > x else 190), ny), fill="#64748b", width=4)
    rounded(d, (590, 390, 910, 570), fill="#ffffff", outline=TEAL, radius=24, width=5)
    text(d, (625, 425), "可复核工作流", FONT_H2, TEAL)
    text(d, (625, 472), "每张图纸、每个指标和每段文本均能追溯到数据源与生成脚本。", FONT_SMALL, INK, width=250)
    img.save(OUT_DIR / "board01_data_loop.png", quality=95)


def draw_ai_modules() -> None:
    img, d = canvas(1500, 900)
    text(d, (36, 28), "AI 与算法模块协同", FONT_TITLE, INK)
    rounded(d, (525, 340, 975, 560), fill="#ffffff", outline=TEAL, radius=28, width=5)
    text(d, (575, 392), "AI Planning Copilot", FONT_H2, TEAL)
    text(d, (575, 440), "把文本、空间指标、图像约束与制图脚本组织为连续决策链。", FONT_SMALL, INK, width=360)
    modules = [
        ("RAG 知识库", "任务书 / 案例 / 政策条文", TEAL, (115, 150)),
        ("AHP-MPI", "更新潜力排序与权重调节", BLUE, (1050, 150)),
        ("LLM 报告", "诊断、策略、导则自动撰写", GREEN, (1050, 645)),
        ("ControlNet", "边界、道路、建筑、深度图约束", PURPLE, (115, 645)),
        ("代码制图", "Python 图纸脚本与图框组装", ORANGE, (525, 115)),
        ("质量校核", "缺图、裁切、指标与版面检查", RED, (525, 675)),
    ]
    for title, body, color, (x, y) in modules:
        rounded(d, (x, y, x + 335, y + 130), fill="#ffffff", outline=color, radius=18, width=4)
        text(d, (x + 24, y + 24), title, FONT_H2, color)
        text(d, (x + 24, y + 66), body, FONT_SMALL, MUTED, width=280)
        # Prevent arrows from overlapping text in the central box
        if x == 115 and y == 150: # top-left
            arrow(d, (450, 280), (525, 340), fill=color, width=3)
        elif x == 1050 and y == 150: # top-right
            arrow(d, (1050, 280), (975, 340), fill=color, width=3)
        elif x == 1050 and y == 645: # bottom-right
            arrow(d, (1050, 645), (975, 560), fill=color, width=3)
        elif x == 115 and y == 645: # bottom-left
            arrow(d, (450, 645), (525, 560), fill=color, width=3)
        elif x == 525 and y == 115: # top-middle
            arrow(d, (693, 245), (693, 340), fill=color, width=3)
        elif x == 525 and y == 675: # bottom-middle
            arrow(d, (693, 675), (693, 560), fill=color, width=3)
    img.save(OUT_DIR / "board01_ai_modules.png", quality=95)


def draw_data_matrix() -> None:
    img, d = canvas(1500, 900)
    text(d, (36, 28), "多源数据资产矩阵", FONT_TITLE, INK)
    rows = ["GIS 边界/建筑", "POI/交通", "街景/GVI", "遥感/卫星", "任务书/政策", "案例/RAG", "地块指标", "AIGC 图像"]
    cols = ["诊断", "策略", "设计", "制图", "汇报"]
    x0, y0 = 70, 130
    cell_w, cell_h = 210, 78
    d.rectangle((x0, y0, x0 + 1320, y0 + 68), fill="#dbeafe", outline=LINE, width=2)
    text(d, (x0 + 24, y0 + 20), "数据类型", FONT_SMALL, INK)
    for j, col in enumerate(cols):
        text(d, (x0 + 360 + j * 170, y0 + 20), col, FONT_SMALL, INK)
    palette = [TEAL, BLUE, GREEN, PURPLE, ORANGE]
    usage = [
        [1, 1, 1, 1, 0],
        [1, 1, 1, 0, 1],
        [1, 0, 1, 1, 1],
        [1, 0, 1, 1, 0],
        [0, 1, 1, 0, 1],
        [0, 1, 1, 0, 1],
        [1, 1, 1, 1, 1],
        [0, 0, 1, 1, 1],
    ]
    for i, row in enumerate(rows):
        y = y0 + 68 + i * cell_h
        fill = "#f7f9fa" if i % 2 == 0 else "#e8edf1"
        d.rectangle((x0, y, x0 + 1320, y + cell_h), fill=fill, outline=LINE)
        text(d, (x0 + 24, y + 22), row, FONT_SMALL, INK)
        for j, used in enumerate(usage[i]):
            cx = x0 + 390 + j * 170
            cy = y + cell_h // 2
            if used:
                d.ellipse((cx - 17, cy - 17, cx + 17, cy + 17), fill=palette[j])
            else:
                d.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), outline="#cbd5e1", width=3)
    text(d, (78, 810), "说明：矩阵强调每类输入数据在诊断、策略、设计、制图和汇报中的复用关系，支撑全流程可追溯。", FONT_BODY, INK, width=1280)
    img.save(OUT_DIR / "board01_data_matrix.png", quality=95)


def draw_technical_highlights() -> None:
    img, d = canvas(2200, 900)
    text(d, (42, 30), "核心技术亮点总览 / Technical Innovation Map", FONT_TITLE, INK)
    text(d, (46, 92), "参照竞赛 PPT 的技术叙事：以“诊断粗糙、博弈断裂、AIGC 空间漂移”三类痛点为靶点，形成可计算、可协商、可控形、可交付的城市更新智能推演系统。", FONT_SMALL, MUTED, width=1960)

    pain_points = [
        ("01", "诊断粗糙", "719 栋建筑 + POI + 街景 + GIS\nAHP-MPI 量化排序", TEAL),
        ("02", "博弈断裂", "居民 / 开发商 / 规划师\nLLM 多主体协商", BLUE),
        ("03", "制图幻觉", "GIS 红线 / 道路 / 深度图\nControlNet 空间锁定", RED),
    ]
    for i, (num, title, body, color) in enumerate(pain_points):
        y = 170 + i * 190
        rounded(d, (62, y, 560, y + 145), fill="#ffffff", outline=color, radius=22, width=4)
        d.ellipse((92, y + 36, 158, y + 102), fill=color)
        text(d, (111, y + 54), num, FONT_H2, "#ffffff")
        text(d, (188, y + 28), title, FONT_H2, color)
        text(d, (188, y + 76), body, FONT_SMALL, INK, width=310)
        # Prevent arrows from overlapping the central panel
        arrow(d, (560, y + 72), (720, y + 72), fill=color, width=5)

    rounded(d, (720, 195, 1480, 705), fill="#ffffff", outline=TEAL, radius=28, width=5)
    text(d, (775, 245), "诊断 - 博弈 - 生成 - 校验", FONT_TITLE, TEAL)
    text(d, (780, 318), "平台把空间数据、政策知识、AIGC 图像生成与自动制图脚本组织为闭环，不停留在单张效果图，而是把每一步推演都落到指标、图纸与交付物。", FONT_BODY, INK, width=610)
    chain = [("DATA", TEAL), ("MPI", BLUE), ("RAG", GREEN), ("AIGC", PURPLE), ("ATLAS", ORANGE)]
    for i, (label, color) in enumerate(chain):
        x = 805 + i * 125
        rounded(d, (x, 520, x + 96, 585), fill="#ffffff", outline=color, radius=16, width=3)
        text(d, (x + 18, 540), label, FONT_SMALL, color)
        if i < len(chain) - 1:
            arrow(d, (x + 98, 552), (x + 124, 552), fill="#cbd5e1", width=3)
    text(d, (795, 628), "核心价值：规则可审、空间可控、过程可追溯、成果可批量生产。", FONT_H2, ORANGE, width=600)

    highlights = [
        ("多源数据资产化", "GeoJSON / CSV / JPG / PDF 统一挂接"),
        ("三维孪生交互底座", "Pydeck / 图层勾选 / 地图拖拽 / 指标联动"),
        ("AHP-MPI 可解释排序", "空间潜力、社会需求、环境紧迫度综合评价"),
        ("Zoning RAG 合规审计", "法规向量检索 + 红黄牌风险提示"),
        ("GIS-ControlNet 控形生成", "矢量红线转光栅掩膜，压制空间漂移"),
        ("自动化成果生产线", "Atlas、A1、报告、视频一体化输出"),
    ]
    for i, (head, body) in enumerate(highlights):
        x = 1540 + (i % 2) * 310
        y = 170 + (i // 2) * 180
        color = [TEAL, BLUE, GREEN, PURPLE, ORANGE, RED][i]
        rounded(d, (x, y, x + 280, y + 130), fill="#ffffff", outline=color, radius=18, width=4)
        d.rectangle((x, y, x + 280, y + 12), fill=color)
        text(d, (x + 22, y + 30), head, FONT_H2, color, width=230)
        text(d, (x + 22, y + 76), body, FONT_TINY, MUTED, width=230)

    stats = [("719", "栋建筑基底"), ("1,788", "张街景样本"), ("248", "法规向量块"), ("153", "图册成果")]
    for i, (value, label) in enumerate(stats):
        x = 1540 + i * 150
        rounded(d, (x, 750, x + 130, 835), fill="#fff7ed", outline=ORANGE, radius=14, width=3)
        text(d, (x + 18, 765), value, FONT_H2, RED)
        text(d, (x + 18, 805), label, FONT_TINY, INK, width=94)
    img.save(OUT_DIR / "board01_technical_highlights.png", quality=95)


def draw_linear_mechanism(title: str, subtitle: str, steps: list[tuple[str, str, str]], filename: str, width: int = 1500, height: int = 900) -> None:
    img, d = canvas(width, height)
    text(d, (36, 28), title, FONT_TITLE, INK)
    text(d, (40, 86), subtitle, FONT_SMALL, MUTED, width=width - 90)
    colors = [TEAL, BLUE, GREEN, PURPLE, ORANGE, RED, GOLD]
    x0, y0 = 70, 190
    gap = 26
    card_w = (width - x0 * 2 - gap * (len(steps) - 1)) // len(steps)
    for i, (label, head, body) in enumerate(steps):
        x = x0 + i * (card_w + gap)
        color = colors[i % len(colors)]
        rounded(d, (x, y0, x + card_w, y0 + 430), fill="#ffffff", outline=color, radius=22, width=4)
        d.rectangle((x, y0, x + card_w, y0 + 14), fill=color)
        text(d, (x + 22, y0 + 32), label, FONT_SMALL, color)
        y = text(d, (x + 22, y0 + 78), head, FONT_H2, INK, width=card_w - 44)
        text(d, (x + 22, y + 12), body, FONT_SMALL, MUTED, width=card_w - 44)
        if i < len(steps) - 1:
            arrow(d, (x + card_w + 4, y0 + 210), (x + card_w + gap - 8, y0 + 210), fill=color, width=4)
    rounded(d, (70, 690, width - 70, height - 70), fill="#ffffff", outline=LINE, radius=22, width=3)
    text(d, (108, 724), "设计含义", FONT_H2, INK)
    text(d, (108, 770), "该机制图用于解释平台内部如何把输入数据、算法参数与生成结果串联为可复核的规划工作流。", FONT_SMALL, MUTED, width=width - 220)
    img.save(OUT_DIR / filename, quality=95)


def draw_data_governance() -> None:
    draw_linear_mechanism(
        "数据治理机制",
        "把松散的任务书、GIS、街景、POI、政策文本转化为统一空间资产。",
        [
            ("INPUT", "原始资料接入", "任务书、红线、建筑、道路、POI、街景、遥感、案例文档。"),
            ("CLEAN", "标准化清洗", "统一编码、坐标、字段、数据来源和质量状态。"),
            ("LINK", "空间挂接", "按地块、道路、研究范围和阶段编号建立索引关系。"),
            ("STORE", "阶段总线", "写入 StageDataBus 与 persistent outputs，供后续复用。"),
            ("AUDIT", "质量检查", "缺字段、缺图、坐标偏移、空数据和版本差异自动提示。"),
        ],
        "board01_data_governance.png",
    )


def draw_spatial_diagnosis() -> None:
    draw_linear_mechanism(
        "空间诊断算法链",
        "以真实空间数据为底，建立现状问题识别与更新优先级判断。",
        [
            ("BASE", "三维底座", "建筑高度、用地类型、规划红线、铁路道路、水系。"),
            ("MEASURE", "指标测度", "POI 密度、GVI/SVF、可达性、道路密度、天际线。"),
            ("MODEL", "问题模型", "空间潜力、社会需求、环境紧迫度三类指标归一化。"),
            ("RANK", "优先级排序", "AHP-MPI 综合分值输出重点更新单元排行。"),
            ("REPORT", "诊断报告", "LLM 将量化结果转写为问题清单和设计依据。"),
        ],
        "board01_spatial_diagnosis.png",
    )


def draw_mpi_model() -> None:
    img, d = canvas(1500, 900)
    text(d, (36, 28), "AHP-MPI 更新潜力模型", FONT_TITLE, INK)
    text(d, (40, 88), "用可调权重把空间潜力、社会需求与环境紧迫度合成为更新优先级。", FONT_SMALL, MUTED, width=1250)
    factors = [
        ("空间潜力 S", "POI / 可达性 / 用地效率 / 建筑低效度", TEAL, 150),
        ("社会需求 D", "人口画像 / 公共服务缺口 / 老龄化需求", BLUE, 420),
        ("环境紧迫 E", "GVI / SVF / 噪声切割 / 铁路阻隔", RED, 690),
    ]
    for title, body, color, y in factors:
        rounded(d, (80, y, 560, y + 160), fill="#ffffff", outline=color, radius=20, width=4)
        text(d, (115, y + 30), title, FONT_H2, color)
        text(d, (115, y + 78), body, FONT_SMALL, MUTED, width=390)
        # Prevent arrows from overlapping the central panel
        if y == 150:
            arrow(d, (560, 230), (780, 300), fill=color, width=5)
        elif y == 420:
            arrow(d, (560, 500), (760, 500), fill=color, width=5)
        elif y == 690:
            arrow(d, (560, 770), (780, 600), fill=color, width=5)
    rounded(d, (760, 300, 1420, 600), fill="#ffffff", outline=BLUE, radius=28, width=5)
    text(d, (805, 350), "MPI = Σ Wi × Xi / Σ Wi × 100", FONT_TITLE, BLUE)
    text(d, (810, 430), "权重来自 AHP 判断矩阵，可在平台侧边栏实时调整；结果直接进入重点地块诊断、总体策略和控规指标推演。", FONT_BODY, INK, width=530)
    rounded(d, (760, 660, 1420, 810), fill="#fff7ed", outline=ORANGE, radius=20, width=4)
    text(d, (805, 700), "输出：五个重点地块更新优先级 + 指标解释 + 后续设计任务触发", FONT_H2, ORANGE, width=560)
    img.save(OUT_DIR / "board01_mpi_model.png", quality=95)


def draw_digital_twin_layers() -> None:
    img, d = canvas(1500, 900)
    text(d, (36, 28), "数字孪生图层栈", FONT_TITLE, INK)
    layers = [
        ("L6 交互控制", "图层开关、日照滑块、2D/3D 视角切换", ORANGE),
        ("L5 专项分析", "POI 热点、交通拥堵、空间句法、街景品质", PURPLE),
        ("L4 规划约束", "规划红线、重点地块、用地底色、保护建筑", RED),
        ("L3 建筑体量", "建筑轮廓、高度、风貌色彩、天际线特征", BLUE),
        ("L2 基础网络", "道路、铁路、水系、开放空间、地形底图", TEAL),
        ("L1 空间底座", "研究范围坐标、GeoJSON、影像参照", GREEN),
    ]
    for i, (title, body, color) in enumerate(layers):
        y = 140 + i * 105
        x = 120 + i * 44
        rounded(d, (x, y, 1380 - i * 44, y + 82), fill="#ffffff", outline=color, radius=18, width=4)
        text(d, (x + 28, y + 18), title, FONT_H2, color)
        text(d, (x + 340, y + 24), body, FONT_SMALL, INK, width=700)
    text(d, (110, 805), "用途：录屏和展板中展示的 3D 地图交互，就是该图层栈的前端表现。", FONT_BODY, INK, width=1200)
    img.save(OUT_DIR / "board01_digital_twin_layers.png", quality=95)


def draw_rag_pipeline() -> None:
    draw_linear_mechanism(
        "RAG + LLM 文本生成链",
        "从任务书与政策案例中检索依据，再组织为诊断、策略、导则与答辩文本。",
        [
            ("DOC", "文本资产", "任务书、开题报告、政策条文、案例库、设计说明草稿。"),
            ("INDEX", "知识索引", "关键词、章节、阶段、图纸编号与规划主题标签。"),
            ("RETRIEVE", "上下文检索", "按当前阶段提取相关依据，避免孤立生成。"),
            ("GENERATE", "LLM 生成", "诊断报告、目标定位、策略矩阵、设计导则。"),
            ("SAVE", "成果回写", "写回阶段数据总线，供图册说明和答辩稿复用。"),
        ],
        "board01_rag_llm_pipeline.png",
    )


def draw_aigc_pipeline() -> None:
    draw_linear_mechanism(
        "AIGC / ControlNet 生成式设计链",
        "把空间约束、深度图、提示词和风貌策略统一约束到效果图推演。",
        [
            ("BASE", "底图输入", "总平、鸟瞰、街景、白模、地块边界。"),
            ("LOCK", "空间锁定", "道路、建筑、红线、用地、重点地块 ControlNet。"),
            ("DEPTH", "深度约束", "平面尺度或透视远近关系生成深度图。"),
            ("PROMPT", "提示词", "风貌、材料、活动、人群、光照和负面约束。"),
            ("RENDER", "生成/增强", "img2img、inpainting、超分增强和对比筛选。"),
        ],
        "board01_aigc_controlnet_pipeline.png",
    )


def draw_atlas_pipeline() -> None:
    draw_linear_mechanism(
        "Atlas 自动制图与装帧链",
        "从空间底图脚本到 A3 图册、A1 展板和控规表的批量生产流程。",
        [
            ("SCRIPT", "代码绘图", "draw_scope_map / list diagrams / indicator images。"),
            ("FRAME", "图框组装", "标题、图例、比例尺、说明文字与制图信息。"),
            ("CROP", "主绘图区裁切", "保留原图，另存裁切副本供展板排版。"),
            ("FIT", "展板适配", "contain 前景 + 同图背景，避免裁切和空白框。"),
            ("EXPORT", "成果输出", "Atlas、A1、PPT、答辩稿、录屏视频。"),
        ],
        "board01_atlas_pipeline.png",
    )


def draw_quality_loop() -> None:
    draw_linear_mechanism(
        "质量校核与可追溯机制",
        "通过自动检查把图纸完整性、引用关系和版面问题前置暴露。",
        [
            ("EXIST", "缺图检查", "HTML 引用、Atlas 文件、裁切图、展板素材存在性。"),
            ("RATIO", "裁切检查", "slot ratio 与 natural ratio 对比，防止 cover 裁掉图纸。"),
            ("TEXT", "文字检查", "标题、图注、按钮、指标卡是否遮挡和溢出。"),
            ("VISUAL", "截图验收", "Playwright 生成 A1 预览与视频 QA 抽帧。"),
            ("ROLLBACK", "备份回退", "atlas_backup 与中间目录保留，避免破坏原文件。"),
        ],
        "board01_quality_loop.png",
    )


def draw_indicator_generation() -> None:
    draw_linear_mechanism(
        "控规指标生成机制",
        "依据改造后的总平面图和地块方案，输出用地面积、建筑面积、密度、绿地率等指标。",
        [
            ("PLAN", "改造总平", "五个重点地块改造后方案作为计算对象。"),
            ("MEASURE", "面积提取", "用地边界、建筑底面、绿地覆盖和道路面积。"),
            ("CALC", "指标计算", "FAR、建筑密度、绿地率、总建筑面积。"),
            ("TABLE", "指标表", "DR-077 / 097 / 116 / 134 / 152 控制性指标表。"),
            ("CHECK", "复核", "与图纸尺度、地块边界和设计意图交叉校验。"),
        ],
        "board01_indicator_generation.png",
    )


def draw_delivery_media() -> None:
    draw_linear_mechanism(
        "动态汇报与交付媒体链",
        "把平台操作、图册成果和展板逻辑转化为后期配音用的动态视频。",
        [
            ("ROUTE", "页面路由", "按工作流进入 3D、MPI、总设、地块、AIGC、成果页。"),
            ("ACTION", "真实交互", "点击按钮、勾选图层、拖动滑块、地图拖拽和页面下滑。"),
            ("TRIM", "自动裁剪", "去掉空白加载、外部引擎告警和无效等待。"),
            ("QA", "抽帧检查", "检查左下角文字框、空白界面、关键功能是否出现。"),
            ("VOICE", "配音准备", "输出无声 MP4 和分镜文档，便于后期录音。"),
        ],
        "board01_delivery_media.png",
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    draw_technical_highlights()
    draw_architecture()
    draw_workflow()
    draw_data_loop()
    draw_ai_modules()
    draw_data_matrix()
    draw_data_governance()
    draw_spatial_diagnosis()
    draw_mpi_model()
    draw_digital_twin_layers()
    draw_rag_pipeline()
    draw_aigc_pipeline()
    draw_atlas_pipeline()
    draw_quality_loop()
    draw_indicator_generation()
    draw_delivery_media()
    print(f"Generated diagrams in {OUT_DIR}")


if __name__ == "__main__":
    main()
