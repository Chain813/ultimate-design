from html import escape
import re
import urllib.parse

import streamlit as st

from src.ui.design_system import load_design_css


CITY_DESIGN_STAGES = [
    {"code": "01", "title": "任务解读", "focus": "明确项目名称、类型、研究范围、设计深度、成果形式和重点问题。"},
    {"code": "02", "title": "资料收集", "focus": "汇总自然、用地、建筑、交通、公共空间、历史文化、人群活动与政策资料。"},
    {"code": "03", "title": "现场调研", "focus": "记录道路街巷、建筑界面、公共空间、商业业态、历史资源和消极空间。"},
    {"code": "04", "title": "现状分析", "focus": "形成区位、上位规划、用地、交通、建筑、公共空间、文化和活力分析。"},
    {"code": "05", "title": "问题诊断", "focus": "通过叠合分析、SWOT、更新潜力评价和机会约束分析归纳核心问题。"},
    {"code": "06", "title": "目标定位", "focus": "提出设计愿景、目标体系、功能定位和设计原则。"},
    {"code": "07", "title": "设计策略", "focus": "形成问题-目标-策略对应表，明确功能、交通、公共空间、文化和产业策略。"},
    {"code": "08", "title": "总体城市设计", "focus": "完成空间结构、总平面、功能布局、道路交通、公共空间和形态控制。"},
    {"code": "09", "title": "专项系统设计", "focus": "深化交通、公共空间、建筑形态、风貌景观等专项系统。"},
    {"code": "10", "title": "重点地段深化", "focus": "对核心公共空间、历史建筑周边、门户节点和低效地块做节点设计。"},
    {"code": "11", "title": "实施路径", "focus": "确定保护、修缮、改造、置换、拆除新建和微更新等方式及分期。"},
    {"code": "12", "title": "城市设计导则", "focus": "形成用地、强度、高度、界面、风貌、公共空间、慢行和标识导视管控。"},
    {"code": "13", "title": "成果表达", "focus": "整理图册、展板、文本、PPT、模型、动画和导出文件。"},
]


STAGE_LOOKUP = {stage["code"]: stage for stage in CITY_DESIGN_STAGES}

WORKFLOW_BOARDS = [
    {
        "key": "early",
        "title": "前期数据获取与现状分析",
        "path": "pages/01_前期数据获取与现状分析.py",
        "stages": ["01", "02", "03", "04", "05"],
        "accent": "#60a5fa",
        "summary": "边界、资料、调研、现状和问题诊断。",
    },
    {
        "key": "middle",
        "title": "中期概念生成与应对策略",
        "path": "pages/02_中期概念生成与应对策略.py",
        "stages": ["06", "07"],
        "accent": "#f59e0b",
        "summary": "愿景目标、设计策略和问题响应。",
    },
    {
        "key": "late",
        "title": "后期设计生成与成果表达",
        "path": "pages/03_后期设计生成与成果表达.py",
        "stages": ["08", "09", "10", "11", "12", "13"],
        "accent": "#34d399",
        "summary": "总体设计、专项深化、实施导则和交付。",
    },
]


STAGE_RESOURCE_MAP = {
    "01": {
        "board": "early",
        "status": "已接入",
        "chart": [("任务书", 90, "PDF 已挂载并可下载"), ("开题报告", 85, "摘要已接入语义台"), ("边界红线", 95, "GeoJSON 已用于底图")],
        "resources": [
            ("任务书 / 开题报告资料台", "/数据底座与规划策略?sub=策略语义萃取"),
            ("首页研究范围底图", "/"),
        ],
        "placeholder": "后续可深化为项目基本情况表与技术路线图生成器。",
    },
    "02": {
        "board": "early",
        "status": "已接入",
        "chart": [("政策文档", 80, "docs 政策资料已入库"), ("空间数据", 92, "边界/地块/建筑/POI 已挂载"), ("语义语料", 75, "支持批量萃取导出")],
        "resources": [
            ("空间数据资产清单", "/数据底座与规划策略?sub=物理底座管理"),
            ("语义萃取引擎", "/数据底座与规划策略?sub=策略语义萃取"),
        ],
        "placeholder": "后续可深化为资料缺口清单与数据质量评分。",
    },
    "03": {
        "board": "early",
        "status": "已接入",
        "chart": [("现场照片", 95, "data/streetview 已挂载"), ("采样点位", 90, "点位表与 Point 文件夹可对应"), ("街道观察", 55, "支持按四向照片人工复核")],
        "resources": [
            ("现场调研街景样本库", "/现场调研"),
            ("街景品质采样点", "/现状空间全景诊断?sub=3D现状全息底座"),
        ],
        "placeholder": "后续可扩展为现场问题标注、街道剖面记录和调研照片批注表。",
    },
    "04": {
        "board": "early",
        "status": "已接入",
        "chart": [("用地建筑", 90, "建筑/用地图层可视化"), ("交通活力", 82, "POI/交通热力可叠加"), ("街景品质", 88, "GVI/SVF 柱体已接入")],
        "resources": [
            ("3D现状全息底座", "/现状空间全景诊断?sub=3D现状全息底座"),
            ("空间数据资产台", "/数据底座与规划策略?sub=物理底座管理"),
        ],
        "placeholder": "后续可扩展区位、上位规划和历史沿革专题图生成。",
    },
    "05": {
        "board": "early",
        "status": "已接入",
        "chart": [("MPI", 90, "AHP + 地块排行可导出"), ("地块雷达", 86, "多维指标雷达已接入"), ("问题报告", 70, "LLM 报告依赖本地模型")],
        "resources": [
            ("地块级诊断面板", "/现状空间全景诊断?sub=地块级诊断面板"),
            ("前期问题诊断报告", "/LLM博弈决策?sub=阶段一：前期分析"),
            ("MPI 更新潜力测度", "/数据底座与规划策略?sub=资产综合评估"),
        ],
        "placeholder": "后续可深化为 SWOT、机会约束和问题综合图自动出图。",
    },
    "06": {
        "board": "middle",
        "status": "部分接入",
        "chart": [("愿景", 70, "可由设计理念报告生成"), ("目标体系", 55, "待补目标体系图"), ("功能定位", 45, "待补定位专题图")],
        "resources": [
            ("设计理念提炼", "/LLM博弈决策?sub=阶段三：设计理念"),
            ("任务书目标依据", "/数据底座与规划策略?sub=策略语义萃取"),
        ],
        "placeholder": "缺少独立目标体系图页面，已先放置目标定位占位。",
    },
    "07": {
        "board": "middle",
        "status": "已接入",
        "chart": [("案例借鉴", 80, "案例摘要已接入"), ("策略生成", 86, "问题-策略表已接入"), ("多方共识", 75, "依赖协商推演结果")],
        "resources": [
            ("案例对标分析", "/LLM博弈决策?sub=阶段二：方案借鉴"),
            ("问题-策略对应", "/LLM博弈决策?sub=阶段四：问题-策略对应"),
            ("动态共识雷达", "/LLM博弈决策?sub=动态共识雷达"),
        ],
        "placeholder": "后续可深化为问题-目标-策略矩阵图自动生成。",
    },
    "08": {
        "board": "late",
        "status": "部分接入",
        "chart": [("总平面", 45, "现为概念生形入口"), ("空间结构", 55, "可用鸟瞰/总图推演"), ("功能布局", 50, "待补正式布局图")],
        "resources": [
            ("概念总平面图生形", "/AIGC设计推演?sub=概念总平面图生形"),
            ("更新设计大地图", "/更新设计成果展示?sub=更新设计大地图"),
        ],
        "placeholder": "缺少正式总体城市设计图纸页，已先放置总平面、结构和功能布局占位。",
    },
    "09": {
        "board": "late",
        "status": "部分接入",
        "chart": [("交通系统", 45, "现有交通热点底图"), ("公共空间", 50, "待补系统图"), ("风貌景观", 60, "AIGC 风貌推演可支撑")],
        "resources": [
            ("3D 图层诊断", "/现状空间全景诊断?sub=3D现状全息底座"),
            ("地下管网 X-Ray", "/更新设计成果展示?sub=更新设计大地图"),
        ],
        "placeholder": "缺少独立专项系统设计页，已先放置交通、公共空间、形态和风貌占位。",
    },
    "10": {
        "board": "late",
        "status": "已接入",
        "chart": [("地块选择", 75, "继承地块诊断"), ("效果推演", 86, "AIGC 结果可生成"), ("图集沉淀", 70, "会话图集可被成果页调用")],
        "resources": [
            ("街区全景透视推演", "/AIGC设计推演?sub=街区全景透视推演"),
            ("轴测鸟瞰空间体块模拟", "/AIGC设计推演?sub=轴测鸟瞰空间体块模拟"),
            ("重点地块效果图", "/更新设计成果展示?sub=重点地块效果图"),
        ],
        "placeholder": "后续可深化为节点平面、剖面和活动场景图集。",
    },
    "11": {
        "board": "late",
        "status": "部分接入",
        "chart": [("留改拆", 80, "成果地图已接入"), ("分期", 40, "待补分期实施图"), ("项目库", 35, "待补重点项目库")],
        "resources": [
            ("留改拆总图", "/更新设计成果展示?sub=更新设计大地图"),
            ("空间成果方案", "/LLM博弈决策?sub=空间成果方案"),
        ],
        "placeholder": "缺少独立分期实施图和重点项目库页面，已先放置实施路径占位。",
    },
    "12": {
        "board": "late",
        "status": "已接入",
        "chart": [("总则", 78, "导则文本已展示"), ("控制条文", 70, "可由 LLM 汇总"), ("Word", 85, "DOCX 导出已接入")],
        "resources": [
            ("规划文本成果", "/更新设计成果展示?sub=规划文本成果"),
            ("最终规划导则", "/LLM博弈决策?sub=空间成果方案"),
        ],
        "placeholder": "后续可深化为地块控制图则、街道导则和公共空间导则。",
    },
    "13": {
        "board": "late",
        "status": "已接入",
        "chart": [("图纸提示词", 88, "Image 2.0 提示词助手"), ("效果图集", 75, "会话/本地图库"), ("导出", 85, "CSV/Markdown/Word 多出口")],
        "resources": [
            ("图纸提示词助手", "/LLM博弈决策?sub=图纸提示词助手"),
            ("重点地块效果图", "/更新设计成果展示?sub=重点地块效果图"),
            ("Word 成果导出", "/更新设计成果展示?sub=规划文本成果"),
        ],
        "placeholder": "后续可深化为完整图册目录、展板和 PPT 自动排版。",
    },
}


def _module_url(page_slug, subpage=None):
    if subpage:
        return f"/{page_slug}?sub={urllib.parse.quote(subpage, safe='')}"
    return f"/{page_slug}"


STAGE_MODULE_MAP = {
    "01": [
        {"title": "任务书与开题报告解析", "href": _module_url("数据底座与规划策略", "策略语义萃取"), "desc": "任务书、开题报告和政策文本语义萃取。", "kind": "资料模块"},
        {"title": "研究边界与底图核验", "href": _module_url("数据底座与规划策略", "物理底座管理"), "desc": "红线、地块、建筑和基础图层校验。", "kind": "底图模块"},
    ],
    "02": [
        {"title": "空间数据资产清单", "href": _module_url("数据底座与规划策略", "物理底座管理"), "desc": "边界、建筑、POI、街景和规划图层挂载。", "kind": "数据模块"},
        {"title": "策略语义萃取引擎", "href": _module_url("数据底座与规划策略", "策略语义萃取"), "desc": "政策、任务书和开题资料批量提取。", "kind": "语义模块"},
    ],
    "03": [
        {"title": "现场调研街景样本库", "href": _module_url("现场调研"), "desc": "读取 streetview 文件夹中的调研点街景图。", "kind": "调研模块"},
        {"title": "3D 现场底座核验", "href": _module_url("现状空间全景诊断", "3D现状全息底座"), "desc": "建筑、道路、公共空间和采样点叠合。", "kind": "空间模块"},
    ],
    "04": [
        {"title": "3D 现状全息底座", "href": _module_url("现状空间全景诊断", "3D现状全息底座"), "desc": "用地、建筑、交通、POI 和街景指标综合诊断。", "kind": "分析模块"},
        {"title": "空间数据资产台", "href": _module_url("数据底座与规划策略", "物理底座管理"), "desc": "现状分析所需空间图层统一管理。", "kind": "数据模块"},
    ],
    "05": [
        {"title": "地块级问题诊断面板", "href": _module_url("现状空间全景诊断", "地块级诊断面板"), "desc": "MPI、POI、GVI 与地块雷达评价。", "kind": "诊断模块"},
        {"title": "前期问题诊断报告", "href": _module_url("LLM博弈决策", "阶段一：前期分析"), "desc": "把指标诊断转成问题清单和报告。", "kind": "报告模块"},
        {"title": "更新潜力测度", "href": _module_url("数据底座与规划策略", "资产综合评估"), "desc": "AHP 权重和更新潜力排序。", "kind": "评价模块"},
    ],
    "06": [
        {"title": "设计理念与目标定位", "href": _module_url("LLM博弈决策", "阶段三：设计理念"), "desc": "由问题与案例提炼愿景、目标和定位。", "kind": "目标模块"},
        {"title": "目标依据语义库", "href": _module_url("数据底座与规划策略", "策略语义萃取"), "desc": "任务书和政策条款作为目标依据。", "kind": "依据模块"},
    ],
    "07": [
        {"title": "问题-策略对应推演", "href": _module_url("LLM博弈决策", "阶段四：问题-策略对应"), "desc": "形成问题、目标、策略和主体诉求对照。", "kind": "策略模块"},
        {"title": "案例对标分析", "href": _module_url("LLM博弈决策", "阶段二：方案借鉴"), "desc": "抽取开题案例并转成可借鉴策略。", "kind": "案例模块"},
        {"title": "动态共识雷达", "href": _module_url("LLM博弈决策", "动态共识雷达"), "desc": "查看多主体协商后的共识度结果。", "kind": "协商模块"},
    ],
    "08": [
        {"title": "概念总平面图生形", "href": _module_url("AIGC设计推演", "概念总平面图生形"), "desc": "生成总体结构、总平面和空间意向。", "kind": "总图模块"},
        {"title": "更新设计大地图", "href": _module_url("更新设计成果展示", "更新设计大地图"), "desc": "把总体方案叠加到成果地图。", "kind": "成果模块"},
    ],
    "09": [
        {"title": "专项系统空间叠合", "href": _module_url("现状空间全景诊断", "3D现状全息底座"), "desc": "交通、公共空间、建筑形态和风貌图层叠合。", "kind": "专项模块"},
        {"title": "更新设计大地图", "href": _module_url("更新设计成果展示", "更新设计大地图"), "desc": "承接专项系统图和留改拆图层。", "kind": "成果模块"},
    ],
    "10": [
        {"title": "重点地段街景推演", "href": _module_url("AIGC设计推演", "街区全景透视推演"), "desc": "重点界面、街景修缮和节点场景推演。", "kind": "深化模块"},
        {"title": "轴测鸟瞰体块模拟", "href": _module_url("AIGC设计推演", "轴测鸟瞰空间体块模拟"), "desc": "重点地块体量和空间关系推演。", "kind": "体块模块"},
        {"title": "重点地块效果图", "href": _module_url("更新设计成果展示", "重点地块效果图"), "desc": "沉淀重点节点效果图集。", "kind": "图集模块"},
    ],
    "11": [
        {"title": "实施路径与留改拆总图", "href": _module_url("更新设计成果展示", "更新设计大地图"), "desc": "将保护、修缮、改造和拆建策略落到图层。", "kind": "实施模块"},
        {"title": "空间成果方案", "href": _module_url("LLM博弈决策", "空间成果方案"), "desc": "汇总实施路径、规划导则和红头任务。", "kind": "方案模块"},
    ],
    "12": [
        {"title": "规划文本成果", "href": _module_url("更新设计成果展示", "规划文本成果"), "desc": "导则总则、管控条文和 Word 成果导出。", "kind": "导则模块"},
        {"title": "最终规划导则推演", "href": _module_url("LLM博弈决策", "空间成果方案"), "desc": "把空间策略转成可交付导则文本。", "kind": "文本模块"},
    ],
    "13": [
        {"title": "图纸提示词助手", "href": _module_url("LLM博弈决策", "图纸提示词助手"), "desc": "面向成果图纸的提示词组织与优化。", "kind": "表达模块"},
        {"title": "重点地块效果图集", "href": _module_url("更新设计成果展示", "重点地块效果图"), "desc": "管理和展示重点地块成果图。", "kind": "图集模块"},
        {"title": "Word 成果导出", "href": _module_url("更新设计成果展示", "规划文本成果"), "desc": "导出规划文本、导则和说明文件。", "kind": "交付模块"},
    ],
}


def _board_by_key(board_key):
    return next(board for board in WORKFLOW_BOARDS if board["key"] == board_key)


def board_stage_options(board_key):
    return [f'{code} {STAGE_LOOKUP[code]["title"]}' for code in _board_by_key(board_key)["stages"]]


def stage_code_from_option(option):
    return str(option).split(" ", 1)[0]


def resolve_stage_option(board_key, default_index=0):
    options = board_stage_options(board_key)
    requested = st.query_params.get("sub")
    if isinstance(requested, list):
        requested = requested[0] if requested else None
    if requested:
        requested_norm = _normalize_label(requested)
        for idx, option in enumerate(options):
            if _normalize_label(option) == requested_norm or requested_norm in _normalize_label(option):
                return idx
    return default_index


def sync_stage_query(board_key, session_key):
    options = board_stage_options(board_key)
    selected = st.session_state.get(session_key)
    if selected in options:
        st.query_params["sub"] = selected


def stage_modules(stage_code):
    return STAGE_MODULE_MAP.get(str(stage_code), [])


def stage_primary_href(stage_code):
    """Return the direct URL for a stage's independent page."""
    _STAGE_PAGE_MAP = {
        "01": "/任务解读",
        "02": "/资料收集",
        "03": "/现场调研",
        "04": "/现状分析",
        "05": "/问题诊断",
        "06": "/目标定位",
        "07": "/设计策略",
        "08": "/总体城市设计",
        "09": "/专项系统设计",
        "10": "/重点地段深化",
        "11": "/实施路径",
        "12": "/城市设计导则",
        "13": "/成果表达",
    }
    return _STAGE_PAGE_MAP.get(stage_code, "#")


def render_stage_workbench(stage_code):
    load_design_css()
    stage = STAGE_LOOKUP[stage_code]
    resource = STAGE_RESOURCE_MAP[stage_code]
    board = _board_by_key(resource["board"])
    chart_items = ""
    for item in resource["chart"]:
        label, value = item[0], item[1]
        basis = item[2] if len(item) > 2 else "按当前模块接入完整度估算"
        chart_items += (
            '<div class="stage-bar-row">'
            f'<span>{escape(label)}</span>'
            f'<div class="stage-bar"><i style="width:{int(value)}%;"></i></div>'
            f'<b>{int(value)}%</b>'
            f'<em>{escape(basis)}</em>'
            "</div>"
        )
    status_class = "ready" if resource["status"] == "已接入" else "partial" if resource["status"] == "部分接入" else "placeholder"
    st.markdown(
        f"""
        <section class="stage-workbench" style="--board-accent:{board["accent"]};">
            <div class="stage-workbench-head">
                <div>
                    <div class="stage-board-label">{escape(board["title"])}</div>
                    <div class="stage-headline"><span>{escape(stage_code)}</span><b>{escape(stage["title"])}</b></div>
                </div>
                <div class="stage-status {status_class}">{escape(resource["status"])}</div>
            </div>
            <div class="stage-workbench-grid compact">
                <div class="stage-chart-panel">
                    <div class="stage-panel-title">模块接入评分</div>
                    {chart_items}
                </div>
                <div class="stage-placeholder-panel">
                    <div class="stage-panel-title">占位深化方向</div>
                    <p>{escape(resource["placeholder"])}</p>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


PROJECT_FLOW_STEPS = [
    {
        "step": "1",
        "title": "边界与资料先锁定",
        "pages": "首页 + 页面01",
        "stages": ["01", "02", "03"],
        "work": "先核对研究红线、重点地块、任务书、开题报告、政策 PDF 和基础数据资产。",
    },
    {
        "step": "2",
        "title": "现状分析与问题诊断",
        "pages": "页面01 + 页面02 + 页面04",
        "stages": ["04", "05"],
        "work": "用 MPI、街景指标、POI、交通和地块雷达图生成问题清单与更新优先级。",
    },
    {
        "step": "3",
        "title": "目标定位与策略生成",
        "pages": "页面04",
        "stages": ["06", "07"],
        "work": "把问题诊断、案例借鉴、政策约束和多主体协商转为设计愿景、策略和空间落位。",
    },
    {
        "step": "4",
        "title": "总体方案与专项推演",
        "pages": "页面03 + 页面05",
        "stages": ["08", "09", "10"],
        "work": "用总平面、轴测、街景修缮和留改拆场景推进总体设计、专项系统和重点地段深化。",
    },
    {
        "step": "5",
        "title": "实施导则与成果交付",
        "pages": "页面04 + 页面05",
        "stages": ["11", "12", "13"],
        "work": "输出分期实施、城市设计导则、图纸提示词、Word 文本和重点地块效果图集。",
    },
]


PROJECT_FUNCTION_MAP = [
    {
        "page_key": "home",
        "page": "首页",
        "subpage": "平台状态",
        "function": "算力与资产状态 HUD",
        "stages": ["02", "13"],
        "description": "检查 Stable Diffusion、Ollama/Gemma、地理空间测度、文档解析、POI、UGC 和街景样本挂载情况，判断后续分析与交付能力是否就绪。",
        "output": "运行状态、数据挂载诊断和演示模式提示。",
    },
    {
        "page_key": "home",
        "page": "首页",
        "subpage": "街区范围及改造红线",
        "function": "全局 2D/3D 基底与图层控制",
        "stages": ["01", "02", "04"],
        "description": "用规划红线、重点更新单元、建筑轮廓、POI、交通拥堵和规划用地底色统一确认研究范围、基础资料和现状空间关系。",
        "output": "项目范围底板、核心图层开关和天际线指标。",
    },
    {
        "page_key": "home",
        "page": "首页",
        "subpage": "核心子系统导览",
        "function": "五个页面的工作流入口",
        "stages": ["01", "13"],
        "description": "按资料底座、现状诊断、AIGC 推演、博弈决策和成果展示的顺序进入项目流程。",
        "output": "页面级流程入口和模块说明。",
    },
    {
        "page_key": "page01",
        "page": "页面01 数据底座与规划策略",
        "subpage": "资产综合评估",
        "function": "AHP 权重配置",
        "stages": ["05"],
        "description": "通过空间潜力、社会需求和环境干预紧迫度三个滑块模拟专家判断，形成地块更新潜力评价权重。",
        "output": "当前权重组合、归一化特征向量和判断矩阵。",
    },
    {
        "page_key": "page01",
        "page": "页面01 数据底座与规划策略",
        "subpage": "资产综合评估",
        "function": "MPI 阈值筛选与排行榜",
        "stages": ["05", "11"],
        "description": "实时计算重点更新单元的 MPI 得分，并通过阈值筛出近期应优先启动的微更新地块。",
        "output": "候选更新单元数量、最高 MPI 地块和排序表。",
    },
    {
        "page_key": "page01",
        "page": "页面01 数据底座与规划策略",
        "subpage": "资产综合评估",
        "function": "MPI 公式、AHP 矩阵与耦合散点图",
        "stages": ["05"],
        "description": "展示 MPI 计算逻辑、权重相对重要性和空间潜力-社会需求耦合关系，辅助识别更新机会与约束。",
        "output": "测度模型、判断矩阵、耦合分布图和当前研判结论。",
    },
    {
        "page_key": "page01",
        "page": "页面01 数据底座与规划策略",
        "subpage": "资产综合评估",
        "function": "评估排行榜导出",
        "stages": ["13"],
        "description": "将当前权重配置下的地块评价结果导出为 CSV，作为后续问题诊断和实施路径依据。",
        "output": "Urban_Renewal_MPI_Report.csv。",
    },
    {
        "page_key": "page01",
        "page": "页面01 数据底座与规划策略",
        "subpage": "策略语义萃取",
        "function": "任务书 / 开题报告资料台",
        "stages": ["01", "02"],
        "description": "集中展示任务书、开题报告、案例摘要和规划约束，为项目边界、设计目标和资料来源提供原文依据。",
        "output": "文档下载、任务书摘要、案例摘要和约束摘录。",
    },
    {
        "page_key": "page01",
        "page": "页面01 数据底座与规划策略",
        "subpage": "策略语义萃取",
        "function": "语义萃取配置与批量文档转 Markdown",
        "stages": ["02"],
        "description": "通过 MarkItDown 批量转换 PDF、Word、PPT 等规划资料，并按插件、OCR 和后缀配置生成可检索语料。",
        "output": "结构化 Markdown 预览和 planning*_extracted_nlp_corpus.md。",
    },
    {
        "page_key": "page01",
        "page": "页面01 数据底座与规划策略",
        "subpage": "物理底座管理",
        "function": "空间数据资产清单",
        "stages": ["02"],
        "description": "核对规划边界、重点地块、建筑底图、POI、交通、街景分析和情绪语料的文件状态、数量和更新时间。",
        "output": "数据资产 manifest 表。",
    },
    {
        "page_key": "page01",
        "page": "页面01 数据底座与规划策略",
        "subpage": "物理底座管理",
        "function": "数据预览与覆盖上传",
        "stages": ["02", "04"],
        "description": "选择 POI、交通、CV 分析或情感分析数据，预览样例并覆盖写入新的 CSV 副本。",
        "output": "更新后的 data 目录数据文件和预览表。",
    },
    {
        "page_key": "page02",
        "page": "页面02 现状空间全景诊断",
        "subpage": "3D现状全息底座",
        "function": "物理基底图层控制",
        "stages": ["04"],
        "description": "开关建筑底座和规划用地分类，校核现状建筑肌理、地块关系和用地功能底色。",
        "output": "现状建筑与用地图层叠加结果。",
    },
    {
        "page_key": "page02",
        "page": "页面02 现状空间全景诊断",
        "subpage": "3D现状全息底座",
        "function": "社会活力图层控制",
        "stages": ["04", "05"],
        "description": "叠加公共服务 POI 和交通热力，用于识别服务设施密度、活动热点和交通压力。",
        "output": "POI 分布、活力热力和拥堵信号。",
    },
    {
        "page_key": "page02",
        "page": "页面02 现状空间全景诊断",
        "subpage": "3D现状全息底座",
        "function": "街景品质 3D 柱体",
        "stages": ["04", "05"],
        "description": "按 GVI、SVF、围合感、杂乱度等指标渲染采样柱体，定位环境品质短板。",
        "output": "街景品质指标三维表达。",
    },
    {
        "page_key": "page02",
        "page": "页面02 现状空间全景诊断",
        "subpage": "3D现状全息底座",
        "function": "3D / 2D / 漫游视角与光照",
        "stages": ["04", "13"],
        "description": "切换鸟瞰、平面和漫游视角，并用仿真光照改善汇报展示的空间阅读性。",
        "output": "可视化现状诊断场景。",
    },
    {
        "page_key": "page02",
        "page": "页面02 现状空间全景诊断",
        "subpage": "地块级诊断面板",
        "function": "更新潜力排行榜",
        "stages": ["05", "11"],
        "description": "按 MPI 得分对重点更新单元排序，明确近期、中期和远期实施对象的初步优先级。",
        "output": "地块名称、面积、POI、GVI 和 MPI 排行表。",
    },
    {
        "page_key": "page02",
        "page": "页面02 现状空间全景诊断",
        "subpage": "地块级诊断面板",
        "function": "逐地块雷达指标与靶向干预建议",
        "stages": ["05", "07"],
        "description": "用绿视率、开阔度、围合感、整洁度、POI 密度和 MPI 生成地块雷达图，并给出环境、业态或保护导向建议。",
        "output": "地块雷达图、指标卡和靶向干预建议。",
    },
    {
        "page_key": "page02",
        "page": "页面02 现状空间全景诊断",
        "subpage": "地块级诊断面板",
        "function": "地块诊断报告导出",
        "stages": ["13"],
        "description": "将地块级诊断结果导出为 CSV，供后续策略推演和成果文本引用。",
        "output": "Plot_Diagnostics_Report.csv。",
    },
    {
        "page_key": "page03",
        "page": "页面03 街区风貌修缮预演",
        "subpage": "地块导向推演",
        "function": "地块选择与策略推荐",
        "stages": ["07", "10"],
        "description": "继承页面02地块诊断结果，按 MPI、POI 和 GVI 推荐对应的更新方向。",
        "output": "地块指标卡和推荐方案方向。",
    },
    {
        "page_key": "page03",
        "page": "页面03 街区风貌修缮预演",
        "subpage": "空间生形模式",
        "function": "街区全景透视推演",
        "stages": ["10", "13"],
        "description": "上传现状街道实拍图，提取街景风貌底线结构并生成更新前后对比。",
        "output": "街景修缮意向图和 Before/After 对比。",
    },
    {
        "page_key": "page03",
        "page": "页面03 街区风貌修缮预演",
        "subpage": "空间生形模式",
        "function": "概念总平面图生形",
        "stages": ["08", "13"],
        "description": "上传路网与地块结构线图，辅助推演建筑体块、功能布局和空间结构表达。",
        "output": "概念总平面图或结构草图。",
    },
    {
        "page_key": "page03",
        "page": "页面03 街区风貌修缮预演",
        "subpage": "空间生形模式",
        "function": "轴测鸟瞰空间体块模拟",
        "stages": ["08", "10", "13"],
        "description": "上传航拍或卫星图，推演区域轴测、白模和鸟瞰空间体块关系。",
        "output": "鸟瞰体块模拟图。",
    },
    {
        "page_key": "page03",
        "page": "页面03 街区风貌修缮预演",
        "subpage": "空间测算与约束参数",
        "function": "ControlNet 空间约束",
        "stages": ["08", "09", "10"],
        "description": "选择 Canny、MLSD、Depth 或 Seg 算子，并调节结构网格贴合度，约束 AI 不偏离真实边界、路网和建筑肌理。",
        "output": "空间骨架约束参数。",
    },
    {
        "page_key": "page03",
        "page": "页面03 街区风貌修缮预演",
        "subpage": "空间测算与约束参数",
        "function": "画质重构、采样和提示词相关性",
        "stages": ["13"],
        "description": "配置 Upscale、Sampler、Steps 和 CFG，控制图像质量、速度和文本方案依从度。",
        "output": "渲染质量参数组。",
    },
    {
        "page_key": "page03",
        "page": "页面03 街区风貌修缮预演",
        "subpage": "输入与约束",
        "function": "现状底图上传、几何校正与裁剪",
        "stages": ["03", "13"],
        "description": "上传 JPG/PNG 现状资料，并通过旋转、顶切、底切、左切、右切校正生成底图。",
        "output": "待渲染底图预览。",
    },
    {
        "page_key": "page03",
        "page": "页面03 街区风貌修缮预演",
        "subpage": "输入与约束",
        "function": "规划算子与二阶段策略库",
        "stages": ["07", "09", "10"],
        "description": "通过景观介入度、历史锚定力、现代介入感、表现力负载，以及五类更新方向和二级方案控制设计倾向。",
        "output": "生成式设计策略和动态提示词。",
    },
    {
        "page_key": "page03",
        "page": "页面03 街区风貌修缮预演",
        "subpage": "输入与约束",
        "function": "提示词、反向提示词、种子和重绘幅度",
        "stages": ["10", "13"],
        "description": "编辑实时 Prompt、Negative Prompt、Seed 和 Denoising 后启动视觉图景衍生测算。",
        "output": "AIGC 推演图和参数记录。",
    },
    {
        "page_key": "page03",
        "page": "页面03 街区风貌修缮预演",
        "subpage": "生成结果与对比",
        "function": "Before/After 对比、下载与历史画廊",
        "stages": ["10", "13"],
        "description": "用滑块比较现状与推演图，下载渲染结果，并沉淀会话级推演历史供页面05调用。",
        "output": "结果图、下载文件和推演历史缩略图。",
    },
    {
        "page_key": "page04",
        "page": "页面04 数字城市议事厅",
        "subpage": "多主体利益协商 / 阶段一：前期分析",
        "function": "生成前期问题诊断报告",
        "stages": ["05"],
        "description": "选择重点地块并注入 MPI、GVI、POI 等真实指标，生成带数据和政策依据的问题诊断报告。",
        "output": "阶段一诊断报告和问题优先级。",
    },
    {
        "page_key": "page04",
        "page": "页面04 数字城市议事厅",
        "subpage": "多主体利益协商 / 阶段二：方案借鉴",
        "function": "案例对标分析报告",
        "stages": ["07"],
        "description": "读取开题报告案例摘要，把案例经验逐条对应到阶段一问题，并提出本地化落地建议。",
        "output": "案例经验综合提炼和可转译设计原则。",
    },
    {
        "page_key": "page04",
        "page": "页面04 数字城市议事厅",
        "subpage": "多主体利益协商 / 阶段三：设计理念",
        "function": "设计理念报告",
        "stages": ["06", "07"],
        "description": "融合前期问题、案例借鉴和开题主题，提炼总体设计理念、目标和策略。",
        "output": "设计理念、策略名称、理论依据、解决问题和空间方向。",
    },
    {
        "page_key": "page04",
        "page": "页面04 数字城市议事厅",
        "subpage": "多主体利益协商 / 阶段四：问题-策略对应",
        "function": "智能议题推荐与选定",
        "stages": ["07", "11"],
        "description": "基于前三阶段证据链生成或选择具有多方利益冲突的微更新议题。",
        "output": "议题标题、背景说明和选定提案。",
    },
    {
        "page_key": "page04",
        "page": "页面04 数字城市议事厅",
        "subpage": "多主体利益协商 / 阶段四：问题-策略对应",
        "function": "RAG 政策合规校验",
        "stages": ["07", "12"],
        "description": "在协商前检索政策知识库，对提案进行容积率、限高、历史保护和更新政策预审。",
        "output": "政策条文卡和合规提示。",
    },
    {
        "page_key": "page04",
        "page": "页面04 数字城市议事厅",
        "subpage": "多主体利益协商 / 阶段四：问题-策略对应",
        "function": "三角色多方协商推演",
        "stages": ["07", "11", "12"],
        "description": "模拟居民、开发商和规划师对同一提案的立场、反驳、妥协与评分，形成显性化利益平衡。",
        "output": "角色发言、共识度评分和问题-策略对应表。",
    },
    {
        "page_key": "page04",
        "page": "页面04 数字城市议事厅",
        "subpage": "动态共识雷达",
        "function": "共识度雷达与策略归集",
        "stages": ["07", "12"],
        "description": "独立查看多主体协商后的共识度雷达图和问题-策略归集结果。",
        "output": "角色共识雷达和协商摘要。",
    },
    {
        "page_key": "page04",
        "page": "页面04 数字城市议事厅",
        "subpage": "图纸提示词助手",
        "function": "图纸选择与精度识别",
        "stages": ["13"],
        "description": "按图册章节、图纸名称和输出场景识别图纸类型、精度等级、真实数据要求和 AI 发挥边界。",
        "output": "图纸画像、精度等级和生成约束。",
    },
    {
        "page_key": "page04",
        "page": "页面04 数字城市议事厅",
        "subpage": "图纸提示词助手",
        "function": "底图 / 资料通道确认",
        "stages": ["02", "13"],
        "description": "确认卫星底图、红线边界、GIS 专题图、建筑肌理图和图例参考图等可用于当前图纸的资料通道。",
        "output": "已确认资料通道和上传参考文件。",
    },
    {
        "page_key": "page04",
        "page": "页面04 数字城市议事厅",
        "subpage": "图纸提示词助手",
        "function": "必要信息、版式与文字规则",
        "stages": ["13"],
        "description": "填写主表达、图例内容、必须出现对象、重点地块、设计策略、分析结论、问题优势、避免内容和文字规则。",
        "output": "完整提示词输入要素。",
    },
    {
        "page_key": "page04",
        "page": "页面04 数字城市议事厅",
        "subpage": "图纸提示词助手",
        "function": "完整性检查、提示词生成与评级修正",
        "stages": ["13"],
        "description": "对缺失资料做拦截或降级，生成 Image 2.0 图纸提示词，并按 A/B/C/D 评级修正提示词。",
        "output": "可复制提示词、Markdown 下载和修正版提示词。",
    },
    {
        "page_key": "page04",
        "page": "页面04 数字城市议事厅",
        "subpage": "多主体利益协商 / 阶段五：空间成果方案",
        "function": "最终规划导则与报告导出",
        "stages": ["12", "13"],
        "description": "汇总前四阶段成果，生成规划导则成果书，并导出 Markdown 或 Word 版本。",
        "output": "五阶段循证报告、规划导则和红头 Word 文件。",
    },
    {
        "page_key": "page05",
        "page": "页面05 更新设计成果展示",
        "subpage": "更新设计大地图",
        "function": "留改拆总图与场景图例",
        "stages": ["08", "09", "11", "13"],
        "description": "展示修缮保护、功能改造、拆除腾退和绿地开敞空间等成果图层，表达综合更新方案。",
        "output": "成果总图和场景图例。",
    },
    {
        "page_key": "page05",
        "page": "页面05 更新设计成果展示",
        "subpage": "更新设计大地图",
        "function": "地下管网 X-Ray 与成果场景渲染",
        "stages": ["09", "11", "13"],
        "description": "叠加地下管网透视，展示基础设施韧性更新与地上留改拆策略的联动。",
        "output": "X-Ray 场景和 3D 成果展示。",
    },
    {
        "page_key": "page05",
        "page": "页面05 更新设计成果展示",
        "subpage": "规划文本成果",
        "function": "成果依据下载",
        "stages": ["01", "02"],
        "description": "下载任务书、开题报告和保护规划，核对导则文本的来源依据。",
        "output": "PDF 原件下载。",
    },
    {
        "page_key": "page05",
        "page": "页面05 更新设计成果展示",
        "subpage": "规划文本成果",
        "function": "总则、空间留改拆与实施要点",
        "stages": ["11", "12"],
        "description": "把保护原则、空间分类管控和近期行动计划整理成可交付的城市设计导则内容。",
        "output": "导则三组文本标签页。",
    },
    {
        "page_key": "page05",
        "page": "页面05 更新设计成果展示",
        "subpage": "规划文本成果",
        "function": "Word 成果导出",
        "stages": ["13"],
        "description": "将导则文本和 AIGC 图集写入带红头样式的 Word 文件。",
        "output": "宽城区历史文化街区微更新规划导则 DOCX。",
    },
    {
        "page_key": "page05",
        "page": "页面05 更新设计成果展示",
        "subpage": "重点地块效果图",
        "function": "会话 AIGC 图集与本地成果示意图库",
        "stages": ["10", "13"],
        "description": "优先展示页面03本次会话生成的推演图；暂无会话记录时回退到项目内置成果图和底图。",
        "output": "重点地块效果图集和本地成果示意图。",
    },
    {
        "page_key": "page05",
        "page": "页面05 更新设计成果展示",
        "subpage": "重点地块效果图",
        "function": "推演历史清理",
        "stages": ["13"],
        "description": "清空会话内 AIGC 推演历史，便于重新组织成果表达。",
        "output": "重置后的效果图集状态。",
    },
]


SUBPAGE_ALIASES = {
    "资产综合评估": "📊 资产综合评估",
    "MPI 更新潜力测度": "📊 资产综合评估",
    "策略语义萃取": "📑 策略语义萃取",
    "策略语义与红线": "📑 策略语义萃取",
    "物理底座管理": "⚙️ 物理底座管理",
    "多源异构底座": "⚙️ 物理底座管理",
    "3D现状全息底座": "🏙️ 3D现状全息底座",
    "3D 现状全息底座": "🏙️ 3D现状全息底座",
    "地块级诊断面板": "📍 地块级诊断面板",
    "街区全景透视推演": "🏙️ 街区全景透视推演 (现状修缮)",
    "概念总平面图生形": "🗺️ 概念总平面图生形 (辅助设计)",
    "轴测鸟瞰空间体块模拟": "🦅 轴测鸟瞰空间体块模拟 (辅助设计)",
    "更新设计大地图": "🏙️ 更新设计大地图",
    "3D 更新设计全景": "🏙️ 更新设计大地图",
    "规划文本成果": "📑 规划文本成果",
    "重点地块效果图": "🖼️ 重点地块效果图",
    "重点效果展示": "🖼️ 重点地块效果图",
}


def _stage_label(codes):
    return " / ".join(f"{code} {STAGE_LOOKUP[code]['title']}" for code in codes if code in STAGE_LOOKUP)


def _normalize_label(value):
    value = value or ""
    value = re.sub(r"[^\w\u4e00-\u9fff]+", "", str(value))
    return value.lower()


def resolve_subpage_option(options, default_index=0, aliases=None):
    requested = st.query_params.get("sub")
    if isinstance(requested, list):
        requested = requested[0] if requested else None
    aliases = {**SUBPAGE_ALIASES, **(aliases or {})}
    if requested:
        target = aliases.get(requested, requested)
        target_norm = _normalize_label(target)
        for idx, option in enumerate(options):
            option_norm = _normalize_label(option)
            if option == target or option_norm == target_norm or target_norm in option_norm or option_norm in target_norm:
                return idx
    return default_index


def page_entries(page_key):
    return [entry for entry in PROJECT_FUNCTION_MAP if entry["page_key"] == page_key]


def render_stage_strip():
    load_design_css()
    items = []
    for stage in CITY_DESIGN_STAGES:
        items.append(
            '<div class="workflow-stage-pill">'
            f'<span>{escape(stage["code"])}</span>'
            f'<b>{escape(stage["title"])}</b>'
            f'<p>{escape(stage["focus"])}</p>'
            "</div>"
        )
    st.markdown('<div class="workflow-stage-strip">' + "".join(items) + "</div>", unsafe_allow_html=True)


def render_project_flow_overview():
    load_design_css()
    cards = []
    for item in PROJECT_FLOW_STEPS:
        cards.append(
            '<article class="workflow-flow-card">'
            f'<div class="workflow-flow-top"><span>{escape(item["step"])}</span><b>{escape(item["title"])}</b></div>'
            f'<div class="workflow-flow-meta">{escape(item["pages"])} · {escape(_stage_label(item["stages"]))}</div>'
            f'<p>{escape(item["work"])}</p>'
            "</article>"
        )
    st.markdown('<div class="workflow-flow-grid">' + "".join(cards) + "</div>", unsafe_allow_html=True)


def render_function_stage_matrix(page_key=None, max_items=None):
    load_design_css()
    entries = page_entries(page_key) if page_key else PROJECT_FUNCTION_MAP
    if max_items:
        entries = entries[:max_items]

    cards = []
    for entry in entries:
        cards.append(
            '<article class="workflow-function-card">'
            f'<div class="workflow-function-stage">{escape(_stage_label(entry["stages"]))}</div>'
            f'<h4>{escape(entry["function"])}</h4>'
            f'<div class="workflow-function-path">{escape(entry["page"])} · {escape(entry["subpage"])}</div>'
            f'<p>{escape(entry["description"])}</p>'
            f'<div class="workflow-function-output"><b>输出</b><span>{escape(entry["output"])}</span></div>'
            "</article>"
        )
    st.markdown('<div class="workflow-function-grid">' + "".join(cards) + "</div>", unsafe_allow_html=True)
