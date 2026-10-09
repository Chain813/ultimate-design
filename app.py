import streamlit as st

# 🌟 强制隐藏侧边栏，设定宽屏模式
st.set_page_config(page_title="系统主页", layout="wide", initial_sidebar_state="collapsed")

from src.utils.logger_setup import setup_logger

# 🌟 初始化全局系统日志
setup_logger()
import json
import os
from pathlib import Path

import pandas as pd
import streamlit.components.v1 as components

from src.config import get_static_url
from src.engines.spatial_engine import get_hud_statistics
from src.ui.app_shell import (
    render_engine_status_alert,
    render_top_nav,
)
from src.ui.asset_prefetch import render_static_asset_prefetch
from src.ui.critical_images import get_inline_static_image_src
from src.ui.design_system import (
    render_page_banner,
    render_section_intro,
    render_summary_cards,
)
from src.ui.digital_twin import render_digital_twin_map, render_skyline_hud
from src.utils.service_check import check_engine_status


def get_page_route(page_path):
    """将文件路径转换为 Streamlit 路由 URL"""
    name = os.path.basename(page_path)
    if "_" in name and name.split("_")[0].isdigit():
        name = name.split("_", 1)[1]
    name = name.replace(".py", "")
    return name

# 项目配置检查 — 首次启动时引导填写
from src.ui.project_config_banner import render_project_config_banner
from src.ui.api_key_validator import render_api_key_banner_if_needed, silent_check_api_key

_project_ready = render_project_config_banner()
if not _project_ready:
    st.stop()  # 配置未完成，停止渲染后续内容

_api_key_ready = render_api_key_banner_if_needed()
if not _api_key_ready:
    st.stop()  # API Key 未验证，停止渲染后续内容

# 加载顶部导航与系统状态警报
render_top_nav()
render_engine_status_alert()

# 启动后台缓存预热（静默加载其他页面数据）
from src.utils.preloader import start_preloading

start_preloading()

# 🎬 演示模式：最大化显示区域 (使用 style.css 中的 .presentation-active 类)
if st.session_state.get("presentation_mode", False):
    st.markdown('<div class="presentation-active"></div>', unsafe_allow_html=True)

# ==========================================
# 🏛️ 三大核心工作台配置 (3 Core Workbenches)
# ==========================================
WORKBENCHES = [
    {
        "id": "workbench_1",
        "number": "01",
        "title": "全息空间诊断与数据沙盘",
        "short_title": "全息空间诊断与数据沙盘",
        "subtitle": "多源底模治理 · AHP-MPI 量化评估 · 3D 全息沙盘",
        "desc": "全域 GIS 空间资产解析、现状白模孪生底座、街景视觉指标分析与 AHP-MPI 潜力诊断，直通全屏数字沙盘。",
        "badge": "全息底座 · MPI潜力 · 3D沙盘",
        "badge_class": "badge-data",
        "btn_class": "btn-data",
        "accent": "#0071e3",
        "icon": "🏢",
        "image": "assets/04_urban_diagnosis.png",
        "primary_path": "pages/01_全息空间诊断与数据沙盘.py",
        "highlights": [
            "16 类空间资产与街景全自动解析入库",
            "AHP-MPI 潜力加权矩阵量化与雷达评估",
            "全息 3D 数字孪生底模与全屏监控看板",
        ],
        "modules": [
            {
                "code": "00",
                "title": "数据准备与任务解读",
                "desc": "上传原始数据、数据质量校验、锁定研究范围与任务目标。",
                "image": "assets/03_digital_twin.png",
                "path": "pages/00_数据准备与任务解读.py",
                "icon": "📦",
            },
            {
                "code": "02",
                "title": "资料收集与现场调研",
                "desc": "语义法规萃取、空间资产挂载、街景绿视率与开阔度复核。",
                "image": "assets/04_urban_diagnosis.png",
                "path": "pages/02_资料收集与现场调研.py",
                "icon": "📷",
            },
            {
                "code": "04",
                "title": "现状分析与问题诊断",
                "desc": "3D 全息底座分析、MPI 潜力评估、地块多维雷达与 AI 报告。",
                "image": "assets/04_urban_diagnosis.png",
                "path": "pages/04_现状分析与问题诊断.py",
                "icon": "🏗️",
            },
            {
                "code": "14",
                "title": "全屏空间数据大屏",
                "desc": "全域指标监控、动态空间沙盘与交互式决策大屏。",
                "image": "assets/03_digital_twin.png",
                "path": "pages/14_数据大屏.py",
                "icon": "📊",
            },
        ],
    },
    {
        "id": "workbench_2",
        "number": "02",
        "title": "多主体博弈与空间 AIGC 工坊",
        "short_title": "多主体博弈与空间 AIGC 工坊",
        "subtitle": "居民/规划师/资本多主体协商 · ControlNet 空间意向生形",
        "desc": "基于多智能体博弈达成多方共识，联动 ControlNet 多条件扩散生形管线，实现从设计意图到空间风貌的高保真推演。",
        "badge": "多主体博弈 · ControlNet · 生形渲染",
        "badge_class": "badge-mid",
        "btn_class": "btn-mid",
        "accent": "#8b5cf6",
        "icon": "🎨",
        "image": "assets/06_llm_consultation_v2.png",
        "primary_path": "pages/02_多主体博弈与空间AIGC工坊.py",
        "highlights": [
            "政府/居民/开发商三主体动态博弈雷达",
            "总体结构/总平用地优化与空间骨架推演",
            "ControlNet 空间约束生形与 Before/After 对比",
        ],
        "modules": [
            {
                "code": "06",
                "title": "目标定位与愿景体系",
                "desc": "设计愿景理念提炼、目标体系构建与开题标杆案例借鉴。",
                "image": "assets/06_llm_consultation_v2.png",
                "path": "pages/06_目标定位.py",
                "icon": "🎯",
            },
            {
                "code": "07",
                "title": "设计策略与博弈协商",
                "desc": "问题-策略矩阵对应推演、三主体协商共识与动态雷达。",
                "image": "assets/06_llm_consultation_v2.png",
                "path": "pages/07_设计策略.py",
                "icon": "🤝",
            },
            {
                "code": "08",
                "title": "总体城市设计",
                "desc": "空间结构推演、用地优化沙盘与概念总平面生形入口。",
                "image": "assets/05_design_inference.png",
                "path": "pages/08_总体城市设计.py",
                "icon": "🗺️",
            },
            {
                "code": "10",
                "title": "重点地段深化设计",
                "desc": "核心节点诊断、控规反推与节点 Before/After 对比推演。",
                "image": "assets/05_design_inference.png",
                "path": "pages/10_重点地段深化.py",
                "icon": "🔍",
            },
            {
                "code": "15",
                "title": "空间 AIGC 设计推演",
                "desc": "总平面图/全景透视/鸟瞰体块 ControlNet 空间意向生形。",
                "image": "assets/06_llm_consultation_v2.png",
                "path": "pages/15_AIGC设计推演.py",
                "icon": "✨",
            },
        ],
    },
    {
        "id": "workbench_3",
        "number": "03",
        "title": "数字图则与工程交付枢纽",
        "short_title": "数字图则与工程交付枢纽",
        "subtitle": "多专项系统深化 · 工业级 AutoCAD DXF · A3 标准成果汇编",
        "desc": "交通/公共空间多专项叠合、留改拆实施时序规划、法规控制图则生成，直通 AutoCAD 2000 工业级标准 DXF 导出与成果表达。",
        "badge": "专项系统 · 工业级DXF · 成果表达",
        "badge_class": "badge-late",
        "btn_class": "btn-late",
        "accent": "#10b981",
        "icon": "📐",
        "image": "assets/05_design_inference.png",
        "primary_path": "pages/03_数字图则与工程交付枢纽.py",
        "highlights": [
            "交通/公共空间/风貌多专项系统空间叠合",
            "AutoCAD 2000 (AC1015, ANSI_936) 国标图层 DXF 导出",
            "控制图则条文/A3展板画廊与 Word 说明书一键交付",
        ],
        "modules": [
            {
                "code": "09",
                "title": "专项系统设计",
                "desc": "交通系统、慢行网络、公共空间系统与建筑形态风貌深化。",
                "image": "assets/05_design_inference.png",
                "path": "pages/09_专项系统设计.py",
                "icon": "🔧",
            },
            {
                "code": "11",
                "title": "实施路径与时序",
                "desc": "六类更新模式划分、三期推进甘特图与留改拆总图。",
                "image": "assets/05_design_inference.png",
                "path": "pages/11_实施路径.py",
                "icon": "📅",
            },
            {
                "code": "12",
                "title": "城市设计数字导则",
                "desc": "地块控制图则、风貌条文管控与法规说明书 DOCX 导出。",
                "image": "assets/05_design_inference.png",
                "path": "pages/12_城市设计导则.py",
                "icon": "📜",
            },
            {
                "code": "13",
                "title": "成果表达与工程交付",
                "desc": "工业级标准 DXF 导出、A3 成果画廊与图纸提示词助手。",
                "image": "assets/05_design_inference.png",
                "path": "pages/13_成果表达.py",
                "icon": "🎁",
            },
            {
                "code": "16",
                "title": "智能体 Skill 规范手册",
                "desc": "规划绘图技能规范、多主体元指令定义与 Skill 导出。",
                "image": "assets/05_design_inference.png",
                "path": "pages/16_制图与设计智能体Skill手册.py",
                "icon": "📖",
            },
        ],
    },
]

# 保持对旧引用与计数的完全向后兼容
MODULE_SECTIONS = [
    {
        "label": wb["short_title"],
        "badge_class": wb["badge_class"],
        "modules": wb["modules"],
    }
    for wb in WORKBENCHES
]
MODULES = [mod for wb in WORKBENCHES for mod in wb["modules"]]

# 动态页面标题
from src.config.site import get_project_info, get_site_city, get_site_name

_proj = get_project_info()
_site_name = get_site_name()
_title = _proj.get("name") or "城市设计智能推演平台"
if _site_name:
    _title = f"{_title} — {_site_name}"

render_page_banner(
    title=_title,
    description="集成 AHP 空间潜力诊断、LLM 规划多主体协同决策与 AIGC + ControlNet 生成式设计推演，打造全流程智能城乡规划微更新支持底盘。",
    eyebrow="Home",
    tags=["AHP-MPI 空间量化分析法", "LLM 多智能体协同决策", "AIGC + ControlNet 视觉风貌推演"],
    metrics=[
        {"value": "AHP-MPI", "label": "多维量化评估", "meta": "基于空间、社会与环境特征的更新潜力诊断"},
        {"value": "LLM Agent", "label": "多主体协同决策", "meta": "居民、开发商与规划师在线协商博弈"},
        {"value": "AIGC+CNet", "label": "生成式风貌设计", "meta": "基于空间骨架控制的意向渲染技术"},
        {"value": "3 大工作台", "label": "核心工作流枢纽", "meta": "空间诊断沙盘 · 博弈AIGC工坊 · 数字图则交付"},
    ],
    image_url=get_inline_static_image_src("research_scope_2d_cropped.png")
)
render_static_asset_prefetch()

render_summary_cards(
    [
        {
            "icon": '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-shield-check"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/><path d="m9 12 2 2 4-4"/></svg>',
            "value": "动态空间评价", 
            "title": "Spatial Assessment", 
            "desc": "以地块、建筑、街景和设施数据为基础诊断更新潜力。",
            "svg_chart": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 70" width="100%" height="70">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="rgba(30, 41, 59, 0.8)" />
      <stop offset="100%" stop-color="rgba(15, 23, 42, 0.8)" />
    </linearGradient>
    <filter id="glow1" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>
  <path d="M 110 35 L 160 35" stroke="#38bdf8" stroke-width="2" stroke-dasharray="4,4" />
  <path d="M 260 35 L 310 35" stroke="#38bdf8" stroke-width="2" stroke-dasharray="4,4" />
  <rect x="0" y="15" width="110" height="40" rx="8" fill="url(#grad1)" stroke="#475569" stroke-width="1.5" />
  <text x="55" y="39" fill="#e2e8f0" font-size="13" font-family="sans-serif" text-anchor="middle" font-weight="600">多源空间数据</text>
  <rect x="160" y="15" width="100" height="40" rx="8" fill="url(#grad1)" stroke="#38bdf8" stroke-width="1.5" filter="url(#glow1)" />
  <text x="210" y="39" fill="#38bdf8" font-size="13" font-family="sans-serif" text-anchor="middle" font-weight="bold">AHP-MPI 测度</text>
  <rect x="310" y="15" width="110" height="40" rx="8" fill="url(#grad1)" stroke="#475569" stroke-width="1.5" />
  <text x="365" y="39" fill="#e2e8f0" font-size="13" font-family="sans-serif" text-anchor="middle" font-weight="600">潜力排行雷达</text>
  <polygon points="155,31 160,35 155,39" fill="#38bdf8" />
  <polygon points="305,31 310,35 305,39" fill="#38bdf8" />
</svg>"""
        },
        {
            "icon": '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-palette"><path d="M12 22C17.52 22 22 17.52 22 12C22 9.8 20.2 8 18 8H16C15.4 8 15 7.6 15 7V5C15 2.8 13.2 1 11 1C5.5 1 1 5.5 1 11C1 17.1 4.9 22 12 22Z"/><circle cx="7.5" cy="10.5" r="1.5" fill="currentColor"/><circle cx="11.5" cy="7.5" r="1.5" fill="currentColor"/><circle cx="16.5" cy="9.5" r="1.5" fill="currentColor"/></svg>',
            "value": "生成式视觉推演", 
            "title": "Generative Pre-rendering", 
            "desc": "将保护要求与设计策略转成可比选的空间图景。",
            "svg_chart": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 70" width="100%" height="70">
  <defs>
    <linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="rgba(30, 41, 59, 0.8)" />
      <stop offset="100%" stop-color="rgba(15, 23, 42, 0.8)" />
    </linearGradient>
    <filter id="glow2" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>
  <path d="M 120 20 L 140 20 L 140 35 L 160 35" stroke="#a855f7" stroke-width="2" stroke-dasharray="4,4" fill="none" />
  <path d="M 120 50 L 140 50 L 140 35 L 160 35" stroke="#a855f7" stroke-width="2" stroke-dasharray="4,4" fill="none" />
  <path d="M 260 35 L 300 35" stroke="#a855f7" stroke-width="2" stroke-dasharray="4,4" />
  <rect x="0" y="5" width="120" height="26" rx="6" fill="url(#grad2)" stroke="#475569" stroke-width="1" />
  <text x="60" y="22" fill="#e2e8f0" font-size="11" font-family="sans-serif" text-anchor="middle" font-weight="600">空间控制 (ControlNet)</text>
  <rect x="0" y="39" width="120" height="26" rx="6" fill="url(#grad2)" stroke="#475569" stroke-width="1" />
  <text x="60" y="56" fill="#e2e8f0" font-size="11" font-family="sans-serif" text-anchor="middle" font-weight="600">AI 润色提示词 (Prompt)</text>
  <rect x="160" y="15" width="100" height="40" rx="8" fill="url(#grad2)" stroke="#a855f7" stroke-width="1.5" filter="url(#glow2)" />
  <text x="210" y="39" fill="#a855f7" font-size="13" font-family="sans-serif" text-anchor="middle" font-weight="bold">SD 渲染推演</text>
  <rect x="300" y="15" width="120" height="40" rx="8" fill="url(#grad2)" stroke="#475569" stroke-width="1.5" />
  <text x="360" y="39" fill="#e2e8f0" font-size="12" font-family="sans-serif" text-anchor="middle" font-weight="600">Before/After 街景</text>
  <polygon points="155,31 160,35 155,39" fill="#a855f7" />
  <polygon points="295,31 300,35 295,39" fill="#a855f7" />
</svg>"""
        },
        {
            "icon": '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-users"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
            "value": "多主体协同测算", 
            "title": "Multi-agent Decision", 
            "desc": "模拟居民、开发商与规划师之间的协商与约束平衡。",
            "svg_chart": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 70" width="100%" height="70">
  <defs>
    <linearGradient id="grad3" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="rgba(30, 41, 59, 0.8)" />
      <stop offset="100%" stop-color="rgba(15, 23, 42, 0.8)" />
    </linearGradient>
    <filter id="glow3" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>
  <path d="M 80 35 L 120 35" stroke="#10b981" stroke-width="2" stroke-dasharray="4,4" />
  <path d="M 280 35 L 320 35" stroke="#10b981" stroke-width="2" stroke-dasharray="4,4" />
  <rect x="0" y="15" width="80" height="40" rx="8" fill="url(#grad3)" stroke="#475569" stroke-width="1.5" />
  <text x="40" y="39" fill="#e2e8f0" font-size="13" font-family="sans-serif" text-anchor="middle" font-weight="600">策划议题</text>
  <rect x="120" y="15" width="160" height="40" rx="8" fill="url(#grad3)" stroke="#10b981" stroke-width="1.5" filter="url(#glow3)" />
  <text x="200" y="31" fill="#10b981" font-size="11" font-family="sans-serif" text-anchor="middle" font-weight="bold">居民/运营商/规划师 协同</text>
  <text x="200" y="47" fill="#10b981" font-size="11" font-family="sans-serif" text-anchor="middle" font-weight="bold">+ RAG 政策校验</text>
  <rect x="320" y="15" width="100" height="40" rx="8" fill="url(#grad3)" stroke="#475569" stroke-width="1.5" />
  <text x="370" y="31" fill="#e2e8f0" font-size="11" font-family="sans-serif" text-anchor="middle" font-weight="600">共识雷达</text>
  <text x="370" y="47" fill="#e2e8f0" font-size="11" font-family="sans-serif" text-anchor="middle" font-weight="600">&amp; 策略矩阵</text>
  <polygon points="115,31 120,35 115,39" fill="#10b981" />
  <polygon points="315,31 320,35 315,39" fill="#10b981" />
</svg>"""
        },
    ]
)
# ==========================================
# 🏛️ 三大核心工作台控制中枢 (3 Core Workbenches Hub)
# ==========================================
render_section_intro(
    "三大核心工作台",
    "系统汇聚三大工作台枢纽，贯穿空间诊断底模、多主体协同 AIGC 推演与数字图则工程交付全流程。",
    eyebrow="Core Workbenches"
)

wb_html_parts = ['<div class="workbench-hub-grid">']
for wb in WORKBENCHES:
    primary_route = get_page_route(wb["primary_path"])

    highlights_html = "".join([
        f'<div class="wb-highlight-item"><span class="wb-highlight-dot" style="background:{wb["accent"]};"></span><span>{hl}</span></div>'
        for hl in wb["highlights"]
    ])

    steps_html = "".join([
        f'<a href="/{get_page_route(mod["path"])}" target="_self" class="wb-step-link">'
        f'<div class="wb-step-left">'
        f'<span class="wb-step-icon">{mod["icon"]}</span>'
        f'<span class="wb-step-title">{mod["code"]} {mod["title"]}</span>'
        f'</div>'
        f'<span class="wb-step-arrow">›</span>'
        f'</a>'
        for mod in wb["modules"]
    ])

    wb_card_html = (
        f'<div class="workbench-card">'
        f'<div class="workbench-card-banner">'
        f'<div class="wb-meta-row">'
        f'<span class="wb-number">WORKBENCH {wb["number"]}</span>'
        f'<span class="wb-badge {wb["badge_class"]}">{wb["badge"]}</span>'
        f'</div>'
        f'<h3 class="wb-title">{wb["icon"]} {wb["title"]}</h3>'
        f'<p class="wb-subtitle">{wb["subtitle"]}</p>'
        f'</div>'
        f'<div class="wb-content">'
        f'<p class="wb-desc">{wb["desc"]}</p>'
        f'<div class="wb-highlights">{highlights_html}</div>'
        f'<a href="/{primary_route}" target="_self" class="wb-cta-btn {wb["btn_class"]}">'
        f'<span>进入工作台枢纽</span>'
        f'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
        f'<line x1="5" y1="12" x2="19" y2="12"></line>'
        f'<polyline points="12 5 19 12 12 19"></polyline>'
        f'</svg>'
        f'</a>'
        f'<div class="wb-divider"></div>'
        f'<div class="wb-steps-title">包含核心阶段与工具：</div>'
        f'<div class="wb-steps-list">{steps_html}</div>'
        f'</div>'
        f'</div>'
    )
    wb_html_parts.append(wb_card_html)

wb_html_parts.append('</div>')
st.markdown("".join(wb_html_parts), unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="content-panel">
        <div class="content-panel-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-shield-check"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/><path d="m9 12 2 2 4-4"/></svg>
            <h3>研究范围声明与系统口径</h3>
        </div>
        <p><strong>当前基址合规性：</strong>系统所呈现的建筑三维模型、基础表格和街景照片等核心数据，
        均严格落在《任务书》与《开题报告》限定的研究区域内。</p>
        <p><strong>未来跨城拓展性：</strong>系统采用界面与数据分离的方式，只需替换地图与数据表即可迁移到新的研究片区，而不必重写核心逻辑。</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 📖 云端访客指南与本地部署教程 (Cloud Visitor Guide)
# ==========================================
engine_status_home = check_engine_status()
if not engine_status_home.sd or not engine_status_home.gemma:
    with st.expander("🚀 获取完整算力：本地化部署与完美体验教程 (Cloud Visitor Guide)", expanded=False):
        st.markdown("""
        ### ☁️ 云端演示模式说明 (Cloud Limitations)
        您当前访问的是部署在公有云服务器上的**在线演示版本**。
        由于标准云端环境缺乏 GPU 算力支持，本系统的两大核心 AI 引擎已自动切换为**预置演示模式 (Demo Mode)**：
        - 🎨 **视觉渲染引擎 (Stable Diffusion)**：生成式风貌推演功能将返回预先渲染好的高质量参考图。
        - 🧠 **决策博弈引擎 (Ollama/Gemma)**：多主体协商对话将返回结构化的预置专家推演剧本。

        *注：地图测度引擎 (Deck.GL)、AHP 评估算法、资产管理等核心逻辑不受影响，均可正常交互体验。*

        ---

        ### 💻 如何完美体验本项目 (Local Deployment Tutorial)
        若您希望解锁真实、实时的 AIGC 图像生成与 LLM 智能对话推演能力，请按照以下步骤将本项目部署至您拥有独立显卡（建议 8GB+ 显存）的本地计算机：

        #### 1. 获取项目源码与核心数据
        前往本项目的 GitHub 仓库 Clone 最新代码，并安装项目所需的全部 Python 依赖。
        ```bash
        git clone https://github.com/YourUsername/ultimateDESIGN.git
        cd ultimateDESIGN
        pip install -r requirements.txt
        ```

        #### 2. 挂载本地大模型引擎 (Ollama)
        前往 [Ollama 官网](https://ollama.com/) 下载并安装引擎。打开终端并运行以下命令，系统将在后台自动下载并运行经过量化压缩的 Gemma 模型：
        ```bash
        ollama run deepseek-v4-pro
        ```
        *(引擎默认将在 `http://127.0.0.1:11434` 端口保持监听，本系统会自动捕捉该端口)*

        #### 3. 挂载视觉渲染引擎 (Stable Diffusion WebUI)
        启动您本地的 SD WebUI（如秋叶一键包），**最关键的一步**是在启动参数中添加 API 开放指令：
        ```bash
        # 在您的 webui-user.bat (Windows) 或 webui-user.sh (Mac/Linux) 中添加：
        set COMMANDLINE_ARGS=--api --listen
        ```
        *(确保 SD WebUI 在 `http://127.0.0.1:7860` 运行。系统将通过此接口发送 ControlNet 骨架约束与 Prompt)*

        #### 4. 启动最终极的数字孪生总台
        当上述两大底层算力引擎均启动并处于监听状态后，回到本项目的根目录，运行以下命令：
        ```bash
        streamlit run app.py
        ```
        此时，主页的 **「底层算力设施调用监控」HUD** 将全面亮起🟢绿灯。恭喜您，已成功解锁 100% 算力全开的循证微更新平台！
        """)

# ==========================================
# 🛡️ 技术监测 HUD (实时探测)
# ==========================================
def render_status_hud(engine_status=None):
    """渲染深度客制化、带技术背书的监测 HUD (已同步全局探测逻辑)"""
    if engine_status is None:
        engine_status = check_engine_status()
    sd_online = engine_status.sd
    hud_stats = get_hud_statistics()

    # 静默自检 API Key 状态
    api_ok, api_msg = silent_check_api_key()
    gemma_status = "已联机 (静默自检正常)" if api_ok else ("未配置 Key" if "未配置" in api_msg else "密钥失效/余额不足")
    gemma_color = "#4ADE80" if api_ok else "#EF4444"

    sd_status = "已联机" if sd_online else "未挂载"
    sd_color = "#4ADE80" if sd_online else "#EF4444"

    st.markdown(f"""
<section class="platform-hud" style="--sd-color:{sd_color}; --gemma-color:{gemma_color};">
    <article class="platform-hud-card">
        <div class="platform-hud-title">底层算力设施</div>
        <div class="platform-hud-row"><span class="status-dot-gemma"></span><b>DeepSeek LLM 智算引擎</b><em>{gemma_status}</em></div>
        <p>承担角色推理与政策文书生成，自动后台静默检活。</p>
    </article>
    <article class="platform-hud-card">
        <div class="platform-hud-title">视觉渲染引擎</div>
        <div class="platform-hud-row"><span class="status-dot-sd"></span><b>空间影像衍生网络</b><em>{sd_status}</em></div>
        <p>承担街景风貌意向图计算，依托 Stable Diffusion。</p>
    </article>
    <article class="platform-hud-card">
        <div class="platform-hud-title">空间与资料引擎</div>
        <div class="platform-hud-row"><span class="status-dot-static"></span><b>测度 / 文档解析</b><em>正常</em></div>
        <p>AHP 测度与法定规划图文 PDF 萃取已就绪。</p>
    </article>
    <article class="platform-hud-card">
        <div class="platform-hud-title">数据资产挂载</div>
        <div class="platform-hud-row"><span class="status-dot-static"></span><b>{hud_stats['poi_count']} POI / {hud_stats['gvi_count']} 街景</b><em>已挂载</em></div>
        <p>研究边界约 {hud_stats['boundary_ha']} 公顷，含 POI、UGC 与街景采样。</p>
    </article>
</section>
""", unsafe_allow_html=True)

# ==========================================
# 🚀 渲染执行
# ==========================================
render_section_intro("平台状态", "先确认底层引擎和资产挂载情况，再进入地图与模块工作流。", eyebrow="Runtime")
render_status_hud(engine_status_home)

# 🗺️ 街区范围及改造红线 (Project Boundary)
render_section_intro("街区范围及改造红线", "统一查看研究边界、重点更新单元、建筑底图和辅助图层。", eyebrow="Project Boundary")

render_digital_twin_map(key_suffix="home")
render_skyline_hud()

# ==========================================
# 📊 数据就绪状态
# ==========================================
import contextlib

from src.data import get_data_readiness

readiness = get_data_readiness()
render_summary_cards([
    {"value": f"{readiness['loaded']}/{readiness['total']}", "title": "数据完备度", "desc": "已上传数据类别"},
    {"value": f"{readiness['required_loaded']}/{readiness['required_count']}", "title": "必备数据就绪", "desc": "核心数据完整性"},
    {"value": "✅ 就绪" if readiness["is_ready"] else "⏳ 待补充", "title": "数据状态", "desc": "可否进入工作流"},
])

# ==========================================
# 💾 项目缓存管理
# ==========================================
st.markdown("---")
c1, c2 = st.columns([3, 1])
with c1:
    render_section_intro("项目进度管理", "系统已自动在后台开启数据总线持久化，防止刷新丢失进度。如需开启新项目，请在此清空。", eyebrow="Project State")
with c2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ 开启全新项目 (清空缓存)", use_container_width=True, type="primary"):
        from src.workflow.stage_data_bus import _get_cache_path
        cache_file = _get_cache_path()
        if cache_file.exists():
            with contextlib.suppress(Exception):
                cache_file.unlink()
        if "stage_bus" in st.session_state:
            del st.session_state["stage_bus"]
        st.toast("✅ 缓存已清空，系统焕然一新！")
        import time
        time.sleep(1)
        st.rerun()



# ==========================================
# 📊 AI 参与度与性能监控
# ==========================================
def render_ai_monitoring_dashboard():
    """在主页底部渲染 AI 参与度监控面板。"""
    from src.utils.llm_monitor import get_llm_metrics

    metrics = get_llm_metrics()
    if not metrics:
        return False
    
    st.markdown("---")
    render_section_intro(
        "AI 深度参与监测看板", 
        "实时监控全平台大语言模型 API 的调用频次、响应时长、Token 吞吐量和性能表现。", 
        eyebrow="AI Performance Dashboard"
    )
        
    total_calls = len(metrics)
    total_tokens = sum(m.get("total_tokens", 0) for m in metrics)
    avg_latency = sum(m.get("latency_sec", 0.0) for m in metrics) / total_calls if total_calls > 0 else 0.0
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("📊 API 总调用次数", f"{total_calls} 次")
    with c2:
        st.metric("🧠 累计消耗 Tokens", f"{total_tokens:,} tokens")
    with c3:
        st.metric("⚡ 平均响应时长", f"{avg_latency:.2f} 秒")
    
    st.markdown("#### 🕒 实时调用流水 (最新 5 条)")
    df = pd.DataFrame(metrics[::-1][:5])
    df_display = df.rename(columns={
        "timestamp": "时间戳",
        "model": "调用模型",
        "latency_sec": "耗时(秒)",
        "prompt_tokens": "输入Tokens",
        "completion_tokens": "输出Tokens",
        "total_tokens": "总Tokens"
    })
    st.dataframe(df_display, use_container_width=True)
    return True

render_ai_monitoring_dashboard()
st.markdown("<br>", unsafe_allow_html=True)
