"""设计上下文管理器 —— 统一提取所有阶段 AI 文本输出，供图纸生产管线消费。

核心功能：
1. build_design_context() — 从 stage_bus 提取所有 AI 输出，构建 DesignContext
2. synthesize_design_brief() — 用 LLM 合成结构化《设计纲要》
3. get_context_for_drawing() — 根据图纸类型提取相关上下文
4. get_context_for_guideline() — 提取导则生成所需上下文

Usage:
    from src.workflow.design_context import build_design_context, DesignContext
    ctx = build_design_context()
    if ctx.design_brief:
        # 使用纲要指导图纸生产
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

import streamlit as st

from src.workflow.stage_keys import SK

logger = logging.getLogger("ultimateDESIGN")


@dataclass
class DesignContext:
    """从 stage bus 提取的结构化设计上下文。"""

    # ── Stage 05：问题诊断 ──
    diagnosis_report: str = ""
    mpi_ranking: list = field(default_factory=list)
    top_plot: str = ""
    top_score: float = 0.0
    radar_data: dict = field(default_factory=dict)

    # ── Stage 06：目标定位 ──
    design_concept: str = ""
    case_benchmark: str = ""

    # ── Stage 07：设计策略 ──
    strategy_matrix: str = ""
    negotiation_result: str = ""
    voting_scores: dict = field(default_factory=dict)

    # ── Stage 08：总体城市设计 ──
    spatial_structure: str = ""
    landuse_sandbox: dict = field(default_factory=dict)

    # ── Stage 09：专项系统 ──
    traffic_system: str = ""
    public_space: str = ""
    building_form: str = ""
    landscape_style: str = ""

    # ── Stage 10：重点地段 ──
    plot_designs: dict = field(default_factory=dict)   # {地块名: 设计文本}
    plot_metrics: dict = field(default_factory=dict)    # {地块名: 指标文本}
    plot_personas: dict = field(default_factory=dict)   # {地块名: 人群画像}

    # ── Stage 11：实施路径 ──
    region_phasing: str = ""

    # ── Stage 12：导则 ──
    design_guideline: str = ""

    # ── 合成产物 ──
    design_brief: str = ""

    # ── 靶向地块（Stage 04/07贯通） ──
    target_plot: dict = field(default_factory=dict)

    # ── 元数据 ──
    completed_stages: list = field(default_factory=list)

    @property
    def has_diagnosis(self) -> bool:
        return bool(self.diagnosis_report)

    @property
    def has_strategy(self) -> bool:
        return bool(self.strategy_matrix)

    @property
    def has_brief(self) -> bool:
        return bool(self.design_brief)

    def get_summary(self, max_chars: int = 3000) -> str:
        """生成压缩摘要，供 LLM 使用。"""
        parts = []
        if self.diagnosis_report:
            parts.append(f"【问题诊断】{self.diagnosis_report[:800]}")
        if self.design_concept:
            parts.append(f"【设计概念】{self.design_concept[:600]}")
        if self.strategy_matrix:
            parts.append(f"【策略矩阵】{self.strategy_matrix[:600]}")
        if self.spatial_structure:
            parts.append(f"【空间结构】{self.spatial_structure[:400]}")
        if self.traffic_system:
            parts.append(f"【交通系统】{self.traffic_system[:300]}")
        if self.public_space:
            parts.append(f"【公共空间】{self.public_space[:300]}")
        if self.building_form:
            parts.append(f"【建筑形态】{self.building_form[:300]}")
        if self.landscape_style:
            parts.append(f"【风貌景观】{self.landscape_style[:300]}")

        text = "\n\n".join(parts)
        if len(text) > max_chars:
            text = text[:max_chars] + "...(已截断)"
        return text


def _load(key: str, default=None):
    """从 stage_bus 安全读取。"""
    from src.workflow.stage_data_bus import load_stage_output
    # 尝试所有可能的 stage code
    for code in ["05", "06", "07", "08", "09", "10", "11", "12", "13"]:
        val = load_stage_output(code, key, None)
        if val is not None:
            return val
    return default


def _load_from(stage_code: str, key: str, default=None):
    """从指定阶段的 stage_bus 读取。"""
    from src.workflow.stage_data_bus import load_stage_output
    return load_stage_output(stage_code, key, default)


def build_design_context() -> DesignContext:
    """从 stage_bus 提取所有 AI 输出，构建 DesignContext。"""
    from src.workflow.stage_data_bus import list_completed_stages

    ctx = DesignContext()
    ctx.completed_stages = list_completed_stages()

    # Stage 04 / 05 双向回退（修复阶段代号割裂）
    ctx.diagnosis_report = str(_load_from("04", SK.DIAGNOSIS_REPORT, "") or _load_from("05", SK.DIAGNOSIS_REPORT, ""))
    ctx.mpi_ranking = _load_from("04", SK.MPI_RANKING, None) or _load_from("05", SK.MPI_RANKING, [])
    ctx.top_plot = str(_load_from("04", SK.TOP_PLOT, "") or _load_from("05", SK.TOP_PLOT, ""))
    ctx.top_score = float(_load_from("04", SK.TOP_SCORE, None) or _load_from("05", SK.TOP_SCORE, 0) or 0)
    ctx.radar_data = _load_from("04", SK.RADAR_DATA, None) or _load_from("05", SK.RADAR_DATA, {})

    # 靶向地块提取
    target_p = _load_from("04", "target_plot") or _load_from("05", "target_plot") or _load_from("07", "target_plot")
    if not isinstance(target_p, dict) or not target_p:
        from src.config.site import get_site_config
        s_cfg = get_site_config()
        s_name = s_cfg.get("name", "示范重点地块") or "示范重点地块"
        target_p = {
            "name": s_name,
            "mpi": 85.0,
            "priority": "P1 优先更新",
            "issues": ["空间功能混杂低效", "公共服务设施短缺", "环境品质与微气候待提升"]
        }
    ctx.target_plot = target_p
    if not ctx.top_plot:
        ctx.top_plot = target_p.get("name", "示范重点地块")
    if not ctx.top_score:
        ctx.top_score = float(target_p.get("mpi", 85.0))

    # Stage 06
    ctx.design_concept = str(_load_from("06", SK.DESIGN_CONCEPT, ""))
    ctx.case_benchmark = str(_load_from("06", SK.CASE_BENCHMARK, ""))

    # Stage 07
    ctx.strategy_matrix = str(_load_from("07", SK.STRATEGY_MATRIX, ""))
    ctx.negotiation_result = str(_load_from("07", SK.NEGOTIATION_RESULT, ""))
    ctx.voting_scores = _load_from("07", SK.VOTING_SCORES, {})

    # Stage 08
    ctx.spatial_structure = str(_load_from("08", SK.SPATIAL_STRUCTURE, ""))
    ctx.landuse_sandbox = _load_from("08", SK.LANDUSE_SANDBOX, {})

    # Stage 09
    ctx.traffic_system = str(_load_from("09", SK.TRAFFIC_SYSTEM, ""))
    ctx.public_space = str(_load_from("09", SK.PUBLIC_SPACE, ""))
    ctx.building_form = str(_load_from("09", SK.BUILDING_FORM, ""))
    ctx.landscape_style = str(_load_from("09", SK.LANDSCAPE_STYLE, ""))

    # Stage 10 — 地块数据使用动态 key
    bus = st.session_state.get("stage_bus", {})
    for key, val in bus.items():
        if key.startswith("10_"):
            parts = key.split("_", 1)
            if len(parts) == 2:
                suffix = parts[1]
                if suffix.startswith("plot_design"):
                    plot_name = suffix.replace("plot_design_", "").replace("plot_design", "")
                    ctx.plot_designs[plot_name or "default"] = str(val)
                elif suffix.startswith("plot_metrics"):
                    plot_name = suffix.replace("plot_metrics_", "").replace("plot_metrics", "")
                    ctx.plot_metrics[plot_name or "default"] = str(val)
                elif suffix.startswith("plot_personas"):
                    plot_name = suffix.replace("plot_personas_", "").replace("plot_personas", "")
                    ctx.plot_personas[plot_name or "default"] = str(val)

    # Stage 11
    ctx.region_phasing = str(_load_from("11", "region_phasing", ""))

    # Stage 12
    ctx.design_guideline = str(_load_from("12", SK.DESIGN_GUIDELINE, ""))

    # 合成产物
    ctx.design_brief = str(_load_from("07", SK.DESIGN_BRIEF, ""))

    return ctx


def synthesize_design_brief(ctx: DesignContext) -> str:
    """用 LLM 将所有阶段 AI 输出与动态博弈共识合成为一份结构化《设计纲要》，提取共识控制关键词。"""
    from src.engines.llm_engine import call_llm_engine
    from src.config.site import get_site_config

    s_cfg = get_site_config()
    city = s_cfg.get("city", "当地") or "当地"

    target_name = ctx.target_plot.get("name", ctx.top_plot or "重点更新地块")
    target_mpi = ctx.target_plot.get("mpi", ctx.top_score or 85.0)
    target_priority = ctx.target_plot.get("priority", "P1 优先更新")
    raw_issues = ctx.target_plot.get("issues", [])
    if isinstance(raw_issues, list):
        target_issues = "、".join(str(x) for x in raw_issues)
    else:
        target_issues = str(raw_issues)
    if not target_issues:
        target_issues = "空间功能低效闲置、公共空间与绿地匮乏、微循环交通不畅"

    land_use = ctx.target_plot.get("land_use", ctx.target_plot.get("type", "综合用地"))
    far_max = ctx.target_plot.get("far_max", 1.4)
    height_max = ctx.target_plot.get("height_max", 18.0)
    density_max = ctx.target_plot.get("density_max", 35.0)
    green_min = ctx.target_plot.get("green_min", 25.0)

    prompt = f"""你是城市设计总负责人。请根据以下各阶段 AI 分析产出与多主体博弈共识，为【{city} · {target_name}】合成一份 800-1200 字的结构化《设计纲要》，
作为后续总体设计、重点深化、ControlNet/SD AIGC 生形与数字图则的统一最高控制依据。

【靶向更新地块（Stage 04/07贯通）】：
- 地块名称：{target_name}（MPI综合潜力: {target_mpi}，紧迫度: {target_priority}）
- 用地属性：{land_use}
- 现状核心痛点：{target_issues}
- 法定控规红线：容积率≤{far_max}，建筑限高≤{height_max}m，建筑密度≤{density_max}%，绿地率≥{green_min}%

【多主体博弈与协商结论（Stage 07）】：
{ctx.negotiation_result[:1500] if ctx.negotiation_result else ctx.strategy_matrix[:1500]}

【问题诊断】{ctx.diagnosis_report[:1200]}
【设计概念】{ctx.design_concept[:800]}
【空间结构】{ctx.spatial_structure[:800]}
【建筑形态与风貌】{ctx.building_form[:600]}
【风貌景观】{ctx.landscape_style[:600]}

输出格式（严格按以下四大结构标题）：

## 靶向地块定位与更新指引
- 靶向地块：{target_name}（MPI: {target_mpi}，{target_priority}）
- 更新模式与功能定位：（明确适应该地块的业态定位与功能复合导向）
- 规划控制指标：容积率≤{far_max}，建筑密度≤{density_max}%，绿地率≥{green_min}%，建筑高度≤{height_max}m
- 风貌与微气候控制要点：（结合属地气候与特色空间肌理）

## 核心问题与博弈共识
（阐明属地居民/使用者、投资开发运营商、规划监督三方围绕【{target_name}】展开协商达成的共识妥协条件：如何平衡民生诉求、商业运营资金平衡与法定刚性底线）

## 空间策略与 AIGC 控制关键词
- 核心控制关键词：（提炼 4-6 个精准的空间生形与AIGC控制关键词，逗号分隔）
- 总体空间形态与织补要点

## 图纸绘制与工程交付要点
（包含 CAD/DXF 矢量图层划分、控规指标法定审查、施工图与视廊退界管控）"""

    result = call_llm_engine(
        prompt=prompt,
        system_prompt="你是城市设计总负责人，擅长将各阶段分析结论与多主体博弈共识转化为可执行的设计指令。输出必须因地制宜、结构清晰、数据具体、严禁套用虚假地名或固定模板。",
        model="deepseek-v4-pro",
    )

    if not result or len(result) < 150:
        result = (
            f"## 靶向地块定位与更新指引\n"
            f"- 靶向地块：{target_name}（MPI: {target_mpi}，{target_priority}）\n"
            f"- 更新模式与功能定位：基于{land_use}属性的因地制宜高品质更新示范地块\n"
            f"- 规划控制指标：容积率≤{far_max}，建筑密度≤{density_max}%，绿地率≥{green_min}%，建筑高度≤{height_max}m\n"
            f"- 风貌与微气候控制要点：延续属地风貌基调，结合微气候被动式设计，营造开敞舒适微环境\n\n"
            f"## 核心问题与博弈共识\n"
            f"- 居民与使用者诉求：彻底解决{target_issues}，配建连续慢行系统、便民活动场所与适老无障碍环境；\n"
            f"- 投资运营商诉求：通过高附加值业态与复合功能导入保障投资回报，合理核定有效运营面积；\n"
            f"- 规划师监督底线：严守容积率≤{far_max}与限高≤{height_max}m刚性底线，落实法定绿地率与视廊管控。\n\n"
            f"## 空间策略与 AIGC 控制关键词\n"
            f"- 核心控制关键词：{target_name}空间织补、复合活力界面、立体生态绿道、适老友好社区、微气候通廊\n"
            f"- 空间形态策略：针灸式微更新改造，打通毛细路网微循环，保留重要空间肌理并织补公共界面。\n\n"
            f"## 图纸绘制与工程交付要点\n"
            f"- 矢量工程图纸严格套用 GB/T 城乡规划 AutoCAD 2000 DXF 标准图层与 1:1 米制世界坐标系；\n"
            f"- 重点对账【{target_name}】的容积率、建筑密度、绿地率与退线要求，确保法定图则指标闭环。"
        )

    return result


def get_context_for_drawing(drawing_type: str, ctx: DesignContext | None = None) -> dict:
    """根据图纸类型提取相关上下文子集。"""
    if ctx is None:
        ctx = build_design_context()

    base = {
        "design_brief": ctx.design_brief[:2000] if ctx.design_brief else ctx.get_summary(2000),
        "spatial_structure": ctx.spatial_structure[:800],
        "top_plot": ctx.top_plot,
    }

    # 根据图纸类型添加特定上下文
    type_lower = drawing_type.lower()

    if "用地" in drawing_type or "land" in type_lower:
        base["landuse_sandbox"] = ctx.landuse_sandbox
        base["strategy"] = ctx.strategy_matrix[:600]

    if "交通" in drawing_type or "traffic" in type_lower:
        base["traffic_system"] = ctx.traffic_system[:800]

    if "公共空间" in drawing_type or "public" in type_lower:
        base["public_space"] = ctx.public_space[:800]

    if "建筑" in drawing_type or "风貌" in drawing_type or "building" in type_lower:
        base["building_form"] = ctx.building_form[:600]
        base["landscape_style"] = ctx.landscape_style[:600]

    if "重点" in drawing_type or "深化" in drawing_type or "plot" in type_lower:
        base["plot_designs"] = ctx.plot_designs
        base["plot_metrics"] = ctx.plot_metrics

    if "历史" in drawing_type or "heritage" in type_lower:
        base["diagnosis"] = ctx.diagnosis_report[:800]
        base["landscape_style"] = ctx.landscape_style[:600]

    if "实施" in drawing_type or "分期" in drawing_type or "phase" in type_lower:
        base["region_phasing"] = ctx.region_phasing[:800]
        base["strategy"] = ctx.strategy_matrix[:600]

    if "导则" in drawing_type or "guideline" in type_lower:
        base["design_guideline"] = ctx.design_guideline[:1500]

    return base


def get_context_for_guideline(ctx: DesignContext | None = None) -> dict:
    """提取导则生成所需的上下文。"""
    if ctx is None:
        ctx = build_design_context()

    return {
        "diagnosis": ctx.diagnosis_report[:2000],
        "case_benchmark": ctx.case_benchmark[:1500],
        "design_concept": ctx.design_concept[:1500],
        "strategy_matrix": ctx.strategy_matrix[:2000],
        "spatial_structure": ctx.spatial_structure[:1000],
        "traffic_system": ctx.traffic_system[:800],
        "public_space": ctx.public_space[:800],
        "building_form": ctx.building_form[:800],
        "landscape_style": ctx.landscape_style[:800],
        "design_brief": ctx.design_brief[:2000],
    }


def ensure_design_brief(force: bool = False) -> str:
    """确保 design_brief 已生成。如果未生成则自动触发合成。"""
    ctx = build_design_context()
    if ctx.design_brief and not force:
        return ctx.design_brief

    # 至少需要 Stage 07 完成或包含策略共识，若强行合成则直接执行
    if not force and "07" not in ctx.completed_stages and not ctx.strategy_matrix:
        return ""

    with st.spinner("🧠 正在合成设计纲要..."):
        brief = synthesize_design_brief(ctx)
        if brief:
            from src.workflow.stage_data_bus import save_stage_output
            save_stage_output("07", SK.DESIGN_BRIEF, brief)
            ctx.design_brief = brief
            logger.info("Design brief synthesized successfully.")

    return ctx.design_brief
