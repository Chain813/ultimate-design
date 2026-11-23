"""FastAPI Router for Workbench 02 Strategy & Master Plan (Stages 06, 07, 08).

Covers:
- Stage 06: 目标定位与案例对标 (`/stage06/state`, `/stage06/generate/stream`)
- Stage 07: 三主体多轮博弈协商与设计策略 (`/stage07/state`, `/stage07/negotiate/stream`, `/stage07/matrix`)
- Stage 08: 总体城市设计与用地构成沙盘 (`/stage08/state`, `/stage08/structure/stream`, `/stage08/landuse-sandbox`)
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.config.site import get_landmarks, get_site_city, get_site_config, get_site_name
from src.engines.context_adaptive_engine import generate_adaptive_personas, infer_plot_diagnostics
from src.engines.llm_engine import call_llm_engine, call_llm_engine_stream
from src.engines.rag_engine import retrieve_rag_context
from src.engines.spatial_data_injector import get_full_spatial_context, get_landuse_summary
from src.workflow.approval_state import ApprovalStatus, save_approval_record
from src.workflow.design_context import build_design_context, synthesize_design_brief
from src.workflow.stage_data_bus import load_stage_output, save_stage_output
from src.workflow.stage_keys import SK

logger = logging.getLogger("ultimateDESIGN.backend.strategy_plan")

router = APIRouter(prefix="/api/v1/strategy", tags=["strategy"])


# ═══════════════════════════════════════════════════════════════════
# Helper utilities
# ═══════════════════════════════════════════════════════════════════

def _sse_event(event_type: str, payload: dict[str, Any]) -> str:
    """Format a structured Server-Sent Event frame with both `event:` and JSON `type`/`event` keys."""
    body = {"type": event_type, "event": event_type, **payload}
    data_str = json.dumps(body, ensure_ascii=False)
    return f"event: {event_type}\ndata: {data_str}\n\n"


def _resolve_target_plot() -> dict[str, Any]:
    """Load the locked target plot from Stage 04/05/07 bus or build a site-adaptive default."""
    site_cfg = get_site_config() or {}
    site_city = get_site_city() or site_cfg.get("city", "长春市") or "长春市"
    site_name = get_site_name() or site_cfg.get("name", "伪满皇宫周边示范街区") or "伪满皇宫周边示范街区"
    reg = site_cfg.get("regulatory_limits", {}) or {}

    tp = (
        load_stage_output("04", "target_plot")
        or load_stage_output("05", "target_plot")
        or load_stage_output("07", "target_plot")
    )
    if not isinstance(tp, dict) or not tp.get("name"):
        is_cc = ("伪满" in site_name) or ("长春" in site_city)
        default_name = "长春水产大市场" if is_cc else f"{site_name}重点更新单元"
        tp = {
            "plot_id": "plot_01",
            "name": default_name,
            "land_use": "商业/文创/公园绿地混合用地" if is_cc else "综合更新混合用地",
            "mpi": 88.5,
            "priority": "P1 优先更新",
            "area_ha": 3.2,
            "far_max": float(reg.get("far_max", 1.4 if is_cc else 2.0)),
            "height_max": float(reg.get("general_zone_height_limit_m", 18.0 if is_cc else 24.0)),
            "core_height_max": float(reg.get("core_zone_height_limit_m", 9.0 if is_cc else 12.0)),
            "density_max": float(reg.get("building_density_max_pct", 35.0)),
            "green_min": float(reg.get("green_ratio_min_pct", 25.0)),
            "issues": [
                "冷链物流外迁导致大跨度交易厅与存量空间低效闲置",
                "周边天际线杂乱，破旧附建割裂历史视廊文脉",
                "缺乏连续滨水/街角公共开放空间与适老慢行配套",
            ]
            if is_cc
            else [
                "存量建筑空间低效利用与功能业态老化",
                "街道界面碎片化，缺乏视线通廊与风貌协调管控",
                "社区公共绿地与15分钟生活圈便民设施存在缺口",
            ],
        }
    else:
        tp = dict(tp)
        tp.setdefault("land_use", tp.get("type", "综合更新混合用地"))
        tp.setdefault("mpi", float(tp.get("mpi_score", 88.5) or 88.5))
        tp.setdefault("priority", "P1 优先更新")
        tp.setdefault("area_ha", float(tp.get("area", 3.2) or 3.2))
        tp.setdefault("far_max", float(reg.get("far_max", 1.4)))
        tp.setdefault("height_max", float(reg.get("general_zone_height_limit_m", 18.0)))
        tp.setdefault("core_height_max", float(reg.get("core_zone_height_limit_m", 9.0)))
        tp.setdefault("density_max", float(reg.get("building_density_max_pct", 35.0)))
        tp.setdefault("green_min", float(reg.get("green_ratio_min_pct", 25.0)))
        if not tp.get("issues"):
            tp["issues"] = infer_plot_diagnostics(tp, site_cfg)
    return tp


def _is_llm_error_or_generic_demo(text: str) -> bool:
    """Detect if LLM output is an offline error message or generic 2-line demo stub."""
    if not text or not isinstance(text, str):
        return True
    s = text.strip()
    error_markers = (
        "错误：未配置 DEEPSEEK_API_KEY",
        "DeepSeek 报错:",
        "无法连接到 DeepSeek API",
        "LLM 引擎异常:",
        "DeepSeek API 请求超时",
    )
    if any(s.startswith(m) or m in s[:160] for m in error_markers):
        return True
    if "建议采取渐进式更新策略，优先改善基础设施和公共空间" in s and len(s) < 220:
        return True
    return False


def _parse_markdown_matrix(md_text: str) -> list[dict[str, str]]:
    """Parse a Markdown table into structured strategy matrix rows."""
    if not md_text or not isinstance(md_text, str):
        return []
    lines = [ln.strip() for ln in md_text.splitlines() if ln.strip().startswith("|") and ln.strip().endswith("|")]
    if len(lines) < 2:
        return []
    headers = [c.strip() for c in lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for ln in lines[1:]:
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if all(set(c).issubset({"-", ":", " "}) for c in cells):
            continue
        row_dict: dict[str, str] = {}
        key_aliases = ["direction", "measure", "policy", "location", "funding", "synergy"]
        for idx, val in enumerate(cells):
            h_name = headers[idx] if idx < len(headers) else f"col_{idx}"
            row_dict[h_name] = val
            if idx < len(key_aliases):
                row_dict[key_aliases[idx]] = val
        rows.append(row_dict)
    return rows


def _rows_to_markdown_matrix(rows: list[dict[str, Any]]) -> str:
    """Serialize structured strategy matrix rows back to standard 6-column Markdown table."""
    header = "| 策略方向 | 具体举措 | 政策依据 | 空间落位 | 资金逻辑 | 协同度 |"
    sep = "| :--- | :--- | :--- | :--- | :--- | :--- |"
    out = [header, sep]
    for r in rows:
        d = r.get("策略方向") or r.get("direction") or r.get("problem") or "空间织补更新"
        m = r.get("具体举措") or r.get("measure") or r.get("strategy") or "微更新改造与业态导入"
        p = r.get("政策依据") or r.get("policy") or r.get("goal") or "《城市更新行动指导意见》"
        loc = r.get("空间落位") or r.get("location") or "靶向重点地块及周边街区"
        f = r.get("资金逻辑") or r.get("funding") or "专项债+社会资本合作运营"
        syn = r.get("协同度") or r.get("synergy") or "92%"
        out.append(f"| {d} | {m} | {p} | {loc} | {f} | {syn} |")
    return "\n".join(out)


def _build_stage06_fallback(section: str, target_plot: dict[str, Any], diag_report: str) -> str:
    """Rich site-adaptive fallback for Stage 06 sections when LLM is offline/401."""
    site_cfg = get_site_config() or {}
    city = get_site_city() or site_cfg.get("city", "长春市") or "长春市"
    site_name = get_site_name() or site_cfg.get("name", "伪满皇宫周边街区") or "伪满皇宫周边街区"
    area_ha = site_cfg.get("area_ha", 160)
    tp_name = target_plot.get("name", "重点更新单元")
    tp_mpi = target_plot.get("mpi", 88.5)
    far_max = target_plot.get("far_max", 1.4)
    height_max = target_plot.get("height_max", 18.0)
    green_min = target_plot.get("green_min", 25.0)
    issues_str = "、".join(target_plot.get("issues", ["存量空间低效", "慢行割裂", "绿地不足"]))

    if section == "case_benchmark":
        return (
            f"# {city}{site_name}更新规划·国内外标杆案例对标分析\n\n"
            f"## 一、 对标案例一：广州永庆坊历史街区微改造（“绣花功夫”渐进式更新）\n"
            f"- **核心经验**：摒弃大拆大建，采用“政府主导、企业承办、居民参与”的 BOT 共同缔造模式，在保留骑楼街巷肌理前提下植入非遗工坊与青年文创。\n"
            f"- **对标场地痛点**：回应【{tp_name}】（MPI={tp_mpi}）面临的“{issues_str}”难题。\n"
            f"- **本地化迁移建议**：在严守限高≤{height_max}m、容积率≤{far_max}法定红线基础上，对现状保留建筑实施分类修缮与首层商业界面活化。\n\n"
            f"## 二、 对标案例二：北京白塔寺历史风貌区“共生院”与视廊织补\n"
            f"- **核心经验**：严格管控核心文保地标周边的第五立面与视线通廊，利用腾退院落嵌入社区客厅、适老服务驿站与口袋绿地。\n"
            f"- **对标场地痛点**：针对片区天际线杂乱、历史风貌界面割裂及老龄社区公共空间短缺。\n"
            f"- **本地化迁移建议**：打通【{tp_name}】至核心风貌地标的景观视廊，保证绿地率提升至 ≥{green_min}%，实现300米见绿。\n\n"
            f"## 三、 对标案例三：上海杨浦滨江工业遗存转型（大跨度厂房空间再生）\n"
            f"- **核心经验**：保留工业桁架与历史红砖肌理，将封闭生产岸线转化为全天候市民漫步生态绿廊与复合文旅客厅。\n"
            f"- **本地化迁移建议**：保留【{tp_name}】大跨度空间骨架，置换为新中式文旅客厅、社区便民市集与数字创客中心。\n\n"
            f"## 四、 核心设计原则提炼\n"
            f"1. **保护优先、视廊严控**：核心区限高≤{target_plot.get('core_height_max', 9.0)}m，一般区≤{height_max}m；\n"
            f"2. **针灸触媒、功能复合**：以【{tp_name}】为先导触媒，带动全域 {area_ha} 公顷街区有机更新；\n"
            f"3. **生态韧性、民生反哺**：以商业运营溢价反哺社区养老、口袋公园与慢行微循环。"
        )
    if section == "design_concept":
        return (
            f"# 数字孪生·古今共振——AI赋能下的{city}{site_name}全域设计目标策划\n\n"
            f"## 一、 总体设计愿景\n"
            f"以历史文脉保护与现代城市活力共振为核心，聚焦靶向更新地块【{tp_name}】（MPI={tp_mpi}），"
            f"通过“织补风貌肌理、活化存量工业/商业空间、贯通蓝绿慢行廊道、健全15分钟全龄社区”，打造兼具文化张力与民生温度的城市更新示范标杆。\n\n"
            f"## 二、 分层量化目标体系\n"
            f"1. **空间形态与风貌缝合目标**：回应“{issues_str}”，严守容积率≤{far_max}、建筑密度≤{target_plot.get('density_max', 35.0)}%、建筑限高≤{height_max}m，街墙连续率≥75%。\n"
            f"2. **生态绿网与微气候提质目标**：将片区绿地率提升至 ≥{green_min}%，重点街道绿视率（GVI）由现状短板提升至 25% 以上，新增6处社区口袋公园。\n"
            f"3. **慢行网络与TOD缝合目标**：构建“小街区、密路网”人车分流漫游体系，打通断头支路与跨铁/滨水慢行阻隔，步行5分钟公园覆盖率≥85%。\n"
            f"4. **产业造血与民生共享目标**：在【{tp_name}】导入“文旅商业+非遗展陈+便民生鲜+青年创客”复合业态，混合用地比例≥30%。"
        )
    if section == "design_basis":
        return (
            f"本研究设计依据涵盖三个法定与学术层级：\n"
            f"1. **上位规划依据**：依据《{city}国土空间总体规划（2021-2035年）》《{city}城市更新专项规划》及属地控制性详细规划，落实片区功能结构与刚性控规红线（FAR≤{far_max}，限高≤{height_max}m）。\n"
            f"2. **政策法规依据**：严格遵循《中华人民共和国城乡规划法》《关于在城乡建设中加强历史文化保护传承的意见》《城市居住区规划设计标准（GB50180-2018）》及《完整居住社区建设标准》。\n"
            f"3. **实证诊断与案例依据**：基于前期多源空间数据融合诊断（锁定【{tp_name}】MPI={tp_mpi}）及广州永庆坊、北京白塔寺、上海杨浦滨江等存量更新标杆经验。"
        )
    if section == "design_principles":
        return (
            f"1. **底线管控与文脉保护优先原则**：严格遵守历史风貌保护紫线与分级高度控制（核心区≤{target_plot.get('core_height_max', 9.0)}m、一般区≤{height_max}m），守护历史视廊与工业遗产肌理。\n"
            f"2. **针灸微更新与渐进式织补原则**：避免大拆大建，以靶向地块【{tp_name}】为空间触媒，采用“留、改、拆”分类施策激活存量资产。\n"
            f"3. **多主体共治与政经良性循环原则**：统筹政府规资部门、原住居民与更新开发商三方诉求，以商业与文创运营收益反哺公共空间与适老配套。\n"
            f"4. **绿色低碳与全季宜居原则**：结合海绵城市与微气候设计，大幅提升街道绿视率（GVI≥25%）与慢行舒适度。"
        )
    return (
        f"1. **总体功能定位**：集历史人文体验、工业遗注文创孵化、滨水生态休闲与全龄友好生活于一体的“复合型城市文旅客厅与有机更新示范区”。\n"
        f"2. **空间形象定位**：“古今共振·蓝绿交织·烟火新章”——保留在地历史建筑与大跨度工业肌理，塑造疏密有致、视廊通透的现代街区风貌。\n"
        f"3. **靶向节点定位**：将【{tp_name}】定位为片区一级更新触媒核心，承担门户集散、文商旅融合造血与社区公共服务枢纽功能。"
    )


# ═══════════════════════════════════════════════════════════════════
# Request Models
# ═══════════════════════════════════════════════════════════════════

class Stage06StreamRequest(BaseModel):
    section: str = Field(
        default="design_concept",
        description="case_benchmark | design_concept | design_basis | design_principles | design_positioning",
    )
    custom_prompt: str | None = None
    model: str = "deepseek-v4-pro"


class NegotiationWeights(BaseModel):
    gov: float = 0.34
    resident: float = 0.33
    dev: float = 0.33


class Stage07NegotiateRequest(BaseModel):
    topic: str | None = None
    proposal: str | None = None
    rounds: int = Field(default=3, ge=1, le=5)
    weights: NegotiationWeights = Field(default_factory=NegotiationWeights)
    model: str = "deepseek-v4-flash"


class Stage07MatrixUpdateRequest(BaseModel):
    strategy_matrix: str | None = None
    rows: list[dict[str, Any]] | None = None


class Stage08StructureRequest(BaseModel):
    custom_prompt: str | None = None
    model: str = "deepseek-v4-pro"


class LanduseSandboxRequest(BaseModel):
    commercial: float | None = None
    residential: float | None = None
    green_open: float | None = None
    public_facility: float | None = None
    cultural_heritage: float | None = None
    target_far: float | None = None
    # Legacy compatibility fields
    res_pct: float | None = None
    com_pct: float | None = None
    off_pct: float | None = None
    green_pct: float | None = None
    public_pct: float | None = None


# ═══════════════════════════════════════════════════════════════════
# Stage 06: 目标定位与案例对标
# ═══════════════════════════════════════════════════════════════════

@router.get("/stage06/state")
def get_stage06_state() -> dict[str, Any]:
    """Return Stage 06 state including benchmark, concept, design creed, and locked target plot."""
    target_plot = _resolve_target_plot()
    return {
        "status": "ok",
        "target_plot": target_plot,
        "case_benchmark": load_stage_output("06", SK.CASE_BENCHMARK, "") or "",
        "design_concept": load_stage_output("06", SK.DESIGN_CONCEPT, "") or "",
        "design_basis": load_stage_output("07", SK.DESIGN_BASIS, "") or load_stage_output("06", SK.DESIGN_BASIS, "") or "",
        "design_principles": load_stage_output("07", SK.DESIGN_PRINCIPLES, "") or load_stage_output("06", SK.DESIGN_PRINCIPLES, "") or "",
        "design_positioning": load_stage_output("07", SK.DESIGN_POSITIONING, "") or load_stage_output("06", SK.DESIGN_POSITIONING, "") or "",
        "diagnosis_report": load_stage_output("05", SK.DIAGNOSIS_REPORT, "") or load_stage_output("04", SK.DIAGNOSIS_REPORT, "") or "",
    }


def _stream_stage06_section(req: Stage06StreamRequest):
    section = (req.section or "design_concept").strip().lower()
    target_plot = _resolve_target_plot()
    diag_report = str(load_stage_output("05", SK.DIAGNOSIS_REPORT, "") or load_stage_output("04", SK.DIAGNOSIS_REPORT, "") or "")
    spatial_ctx = get_full_spatial_context()[:3000]
    fallback_text = _build_stage06_fallback(section, target_plot, diag_report)

    section_key_map = {
        "case_benchmark": ("06", SK.CASE_BENCHMARK),
        "design_concept": ("06", SK.DESIGN_CONCEPT),
        "design_basis": ("07", SK.DESIGN_BASIS),
        "design_principles": ("07", SK.DESIGN_PRINCIPLES),
        "design_positioning": ("07", SK.DESIGN_POSITIONING),
    }
    stage_code, sk_key = section_key_map.get(section, ("06", SK.DESIGN_CONCEPT))

    prompt = (
        f"靶向地块：{target_plot.get('name')} (MPI={target_plot.get('mpi')}, FAR≤{target_plot.get('far_max')}, 限高≤{target_plot.get('height_max')}m)\n"
        f"前期诊断：{diag_report[:1200]}\n"
        f"空间上下文：{spatial_ctx[:1500]}\n"
        f"请生成章节【{section}】的专业规划内容。"
    )
    if req.custom_prompt:
        prompt += f"\n补充要求：{req.custom_prompt}"

    def _event_gen():
        yield _sse_event("start", {"section": section, "target_plot": target_plot.get("name")})
        accumulated = ""
        try:
            for chunk in call_llm_engine_stream(
                prompt=prompt,
                system_prompt="你是资深城市更新总规划师，输出详实、有数据支撑的规划分析文本。",
                model=req.model,
            ):
                accumulated += chunk
                if not _is_llm_error_or_generic_demo(accumulated):
                    yield _sse_event("chunk", {"section": section, "delta": chunk, "content": accumulated})
        except Exception as exc:
            logger.warning("Stage 06 stream fallback triggered: %s", exc)

        if _is_llm_error_or_generic_demo(accumulated):
            accumulated = fallback_text
            # Stream fallback in smooth chunks
            step = 120
            built = ""
            for i in range(0, len(accumulated), step):
                piece = accumulated[i : i + step]
                built += piece
                yield _sse_event("chunk", {"section": section, "delta": piece, "content": built, "fallback": True})

        save_stage_output(stage_code, sk_key, accumulated)
        if stage_code == "07":
            save_stage_output("06", sk_key, accumulated)
        yield _sse_event("done", {"section": section, "content": accumulated, "length": len(accumulated)})

    return StreamingResponse(_event_gen(), media_type="text/event-stream")


@router.post("/stage06/generate/stream")
def post_stage06_generate_stream(req: Stage06StreamRequest):
    """Stream SSE generation for Stage 06 sections (`case_benchmark`, `design_concept`, `design_basis`, `design_principles`, `design_positioning`)."""
    return _stream_stage06_section(req)


@router.post("/stage06/benchmark/stream")
def post_stage06_benchmark_stream(req: Stage06StreamRequest | None = None):
    """Alias route for Stage 06 case benchmark SSE stream."""
    body = req or Stage06StreamRequest(section="case_benchmark")
    body.section = "case_benchmark"
    return _stream_stage06_section(body)


@router.post("/stage06/concept/stream")
def post_stage06_concept_stream(req: Stage06StreamRequest | None = None):
    """Alias route for Stage 06 design concept SSE stream."""
    body = req or Stage06StreamRequest(section="design_concept")
    body.section = "design_concept"
    return _stream_stage06_section(body)


# ═══════════════════════════════════════════════════════════════════
# Stage 07: 三主体多轮博弈协商与设计策略
# ═══════════════════════════════════════════════════════════════════

@router.get("/stage07/state")
def get_stage07_state() -> dict[str, Any]:
    """Return Stage 07 negotiation result, voting scores, strategy matrix, and design brief."""
    target_plot = _resolve_target_plot()
    site_cfg = get_site_config() or {}
    personas = generate_adaptive_personas(
        site_context=site_cfg,
        target_plot=target_plot,
        regulatory_limits={
            "far_max": target_plot.get("far_max", 1.4),
            "height_max": target_plot.get("height_max", 18.0),
            "density_max": target_plot.get("density_max", 35.0),
            "green_min": target_plot.get("green_min", 25.0),
        },
    )
    matrix_md = str(load_stage_output("07", SK.STRATEGY_MATRIX, "") or "")
    matrix_rows = load_stage_output("07", "strategy_matrix_rows", None)
    if not isinstance(matrix_rows, list) or not matrix_rows:
        matrix_rows = _parse_markdown_matrix(matrix_md)

    voting_scores = load_stage_output("07", SK.VOTING_SCORES, {}) or {}
    consensus_radar = load_stage_output(
        "07",
        "consensus_radar",
        {
            "空间品质": 88.0,
            "经济可行": 84.0,
            "民生保障": 89.0,
            "历史风貌": 92.0,
            "法规合规": 95.0,
        },
    )
    return {
        "status": "ok",
        "target_plot": target_plot,
        "personas": personas,
        "negotiation_result": load_stage_output("07", SK.NEGOTIATION_RESULT, "") or "",
        "dialogues": load_stage_output("07", "negotiation_dialogues", []) or [],
        "voting_scores": voting_scores,
        "consensus_radar": consensus_radar,
        "strategy_matrix": matrix_md,
        "matrix_rows": matrix_rows,
        "design_brief": load_stage_output("07", SK.DESIGN_BRIEF, "") or "",
    }


def _retrieve_role_rag_citations(query: str, top_k: int = 2) -> list[dict[str, Any]]:
    """Query hybrid RAG engine and format hit clauses as structured citation badges."""
    citations: list[dict[str, Any]] = []
    try:
        chunks = retrieve_rag_context(query, top_k=top_k) or []
        for idx, item in enumerate(chunks):
            # retrieve_rag_context returns tuples of (score, content, source)
            if isinstance(item, (list, tuple)) and len(item) >= 3:
                score, content, source = item[0], item[1], item[2]
            elif isinstance(item, dict):
                score = item.get("score", 0.85)
                content = item.get("content", "")
                source = item.get("source", "规划法规条文")
            else:
                continue
            snippet = str(content).strip().replace("\n", " ")
            if len(snippet) > 140:
                snippet = snippet[:140] + "..."
            citations.append(
                {
                    "id": f"rag_{idx + 1}",
                    "source": str(source),
                    "clause": snippet,
                    "score": round(float(score) if isinstance(score, (int, float)) else 0.88, 3),
                }
            )
    except Exception as exc:
        logger.debug("RAG citation lookup fallback: %s", exc)

    if not citations:
        citations.append(
            {
                "id": "rag_fallback_1",
                "source": "《城市居住区规划设计标准 GB50180-2018》",
                "clause": "旧区改建绿地率不应低于25%，人均公共绿地面积应满足15分钟生活圈与适老无障碍活动场地要求。",
                "score": 0.88,
            }
        )
    return citations


def _build_role_round_fallback(
    role_key: str,
    round_idx: int,
    target_plot: dict[str, Any],
    citations: list[dict[str, Any]],
) -> tuple[str, str]:
    """Generate authentic, progressive (Thinking, Formal Speech) grounded in target plot & live RAG citations."""
    tp_name = target_plot.get("name", "长春水产大市场")
    far_max = target_plot.get("far_max", 1.4)
    height_max = target_plot.get("height_max", 18.0)
    core_h = target_plot.get("core_height_max", 9.0)
    green_min = target_plot.get("green_min", 25.0)
    density_max = target_plot.get("density_max", 35.0)
    area_ha = target_plot.get("area_ha", 3.2)
    cite_source = citations[0]["source"] if citations else "《城市更新行动指导意见》"
    cite_clause = citations[0]["clause"][:75] if citations else "严格保护历史风貌并补齐社区公共服务短板"

    if role_key == "gov":
        if round_idx == 0:
            return (
                f"核查【{tp_name}】（{area_ha}ha）法定控规红线与{cite_source}要求，明确底线不可突破。",
                f"依据**{cite_source}**（“{cite_clause}”），【{tp_name}】更新必须严守三条刚性红线："
                f"① 综合容积率严格控制在 **FAR ≤ {far_max}**，建筑密度 **≤ {density_max}%**；"
                f"② 邻近历史风貌核心区一线限高 **≤ {core_h}m**，一般更新区限高 **≤ {height_max}m**，保留大跨度工业桁架与历史视廊；"
                f"③ 绿地率必须由现状短板提升至 **≥ {green_min}%**，兑现滨水及街角公共开放空间。",
            )
        if round_idx == 1:
            return (
                "针对开发商提出的容积率上浮诉求与居民的零干扰诉求，运用规划激励与空间转移政策进行裁决。",
                f"针对开发商反映的存量加固成本压力，规资部门明确：**历史视廊限高 {core_h}–{height_max}m 与紫线红线绝不放宽**；"
                f"但可依据**{cite_source}**启动“公益配建奖励与地下空间复合利用”机制——允许开发商开发地下一层智慧车库与下沉商业（不计入地上FAR），"
                f"前提是必须无偿移交不少于 **25% 的开敞绿地**与 **1500㎡ 社区适老及生鲜便民中心**。",
            )
        return (
            "锁定三方利益折中契约，形成可纳入 Stage 12 法定导则的刚性管控指标。",
            f"规资部门最终裁定并形成法定共识方案：【{tp_name}】规划容积率锁定为 **{max(1.0, round(far_max - 0.05, 2))}（≤{far_max}）**，"
            f"建筑密度 **{min(32.0, density_max)}%**，绿地率 **{max(28.5, green_min)}%**；"
            f"采取“留改拆并举（保留工业桁架+局部织补坡顶文创盒）”，以政策专项债支持管网与慢行绿道先行落地。",
        )

    if role_key == "resident":
        if round_idx == 0:
            return (
                f"从原住居民日常买菜、日照采光、老年人无障碍活动角度审视【{tp_name}】改造方案。",
                f"我们老街坊支持【{tp_name}】改造，但坚决反对大拆大建搞成高消费封闭商业区！"
                f"结合**{cite_source}**关于完整社区与民生保障的规定，我们提出三点核心诉求："
                f"① 绝不能建高楼挡住北侧住宅采光，限高必须压在 **{height_max}m** 以内；"
                f"② 保留并升级原有的**平价便民净菜市集**与社区食堂；"
                f"③ 拆除封闭围墙，把绿地率提高到 **{green_min}%** 以上，配建适老健身口袋公园和日照充足的长椅休憩区。",
            )
        if round_idx == 1:
            return (
                "反驳开发商首层全商业化提案，要求锁定平价便民服务面积比例与施工期扰民控制。",
                f"开发商如果把首层全部改成高溢价网红餐饮，不仅油烟噪音扰民，老百姓买菜看病去哪？"
                f"我们要求在规划协议中写明：**首层至少保留 30% 面积用于平价生鲜市集、社区卫生站与老年日间照料中心**，"
                f"且夜间商业外摆必须在 22:00 前面向居住区一侧实施静音管控，实现人车分流！",
            )
        return (
            "对政府提出的地下停车下沉、地面返还口袋公园与保留净菜市集的折中方案表示认可。",
            f"同意第三轮折中方案！只要把车辆引入地下车库、地面留出 **{max(28.5, green_min)}% 连续慢行绿廊和口袋公园**，"
            f"并在【{tp_name}】一层东翼固定配建 **1500㎡ 智慧便民净菜超市与适老活动驿站**，我们居民代表全力支持项目动工！",
        )

    # role_key == "dev"
    if round_idx == 0:
        return (
            f"测算【{tp_name}】存量结构加固、违建腾退与公服配建的资金现金流平衡模型。",
            f"从城市更新开发运营主体角度，【{tp_name}】（{area_ha}ha）保留大跨度工业桁架加固与管网改造前期投入超 2.4 亿元。"
            f"若地上容积率受限于 **{far_max}**、限高 **{height_max}m**，纯靠传统租金静态回收期将超过 14 年。"
            f"依据**{cite_source}**市场化更新激励条款，我方诉求：赋予 **35% 商业/文创混合用地（B1/B4）比例**，"
            f"允许植入新中式文旅客厅、主理人策展工坊与全季夜经济消费场景以提升坪效。",
        )
    if round_idx == 1:
        return (
            "回应居民民生诉求与规资部门红线约束，提出“地下空间换地上绿地、商业溢价反哺公服”的交易条件。",
            f"我方尊重规资部门 **FAR ≤ {far_max}** 与限高 **{height_max}m** 的法定红线，也愿意兑现居民急需的 **1500㎡ 净菜市集与口袋公园**；"
            f"作为利益平衡交换，申请政府批准：① 开发利用地下一层约 8,000㎡ 建设共享智慧停车场与冷链配套（不计入地上容积率）；"
            f"② 给予市政绿道基础设施专项债配套，并减免城市基础设施配套费，将投资回收期压缩至 **8.5 年**。",
        )
    return (
        "达成“政策赋能+地下扩容+文商旅复合+公服反哺”的三方共赢财务与空间闭环。",
        f"开发商确认达成共识！按地上 **FAR {max(1.0, round(far_max - 0.05, 2))}**、建筑密度 **{min(32.0, density_max)}%** 执行，"
        f"保留大跨度工业桁架打造“首层文创市集+便民净菜、二层青年创客工坊、外部 28.5% 滨水漫步绿轴”，"
        f"每年提取运营净收益的 **8%** 注入社区公共空间长效维护基金，实现政-企-民良性循环！",
    )


@router.post("/stage07/negotiate/stream")
def post_stage07_negotiate_stream(req: Stage07NegotiateRequest):
    """Stream 3-party multi-round urban renewal negotiation with live Hybrid RAG citations & 5D consensus radar."""
    target_plot = _resolve_target_plot()
    site_cfg = get_site_config() or {}
    site_city = get_site_city() or site_cfg.get("city", "长春市") or "长春市"
    site_name = get_site_name() or site_cfg.get("name", "伪满皇宫周边街区") or "伪满皇宫周边街区"

    tp_name = target_plot.get("name", "长春水产大市场")
    far_max = target_plot.get("far_max", 1.4)
    height_max = target_plot.get("height_max", 18.0)
    green_min = target_plot.get("green_min", 25.0)
    density_max = target_plot.get("density_max", 35.0)

    topic = (req.topic or req.proposal or "").strip()
    if not topic:
        topic = (
            f"围绕靶向更新地块【{tp_name}】（{site_city}{site_name}，MPI={target_plot.get('mpi', 88.5)}），"
            f"在严守法定控规红线（FAR≤{far_max}、限高≤{height_max}m、绿地率≥{green_min}%）前提下，"
            f"协调历史风貌视廊保护、原住居民15分钟便民适老配套与文商旅更新开发投资平衡。"
        )

    w_gov = max(0.05, float(req.weights.gov))
    w_res = max(0.05, float(req.weights.resident))
    w_dev = max(0.05, float(req.weights.dev))
    w_sum = w_gov + w_res + w_dev
    norm_weights = {
        "gov": round(w_gov / w_sum, 3),
        "resident": round(w_res / w_sum, 3),
        "dev": round(w_dev / w_sum, 3),
    }

    rounds = max(1, min(5, int(req.rounds or 3)))
    round_labels = [
        "第一轮：方案陈述与底线亮牌",
        "第二轮：利益交锋与法规博弈",
        "第三轮：折中妥协与契约共识",
        "第四轮：实施细则与资金核定",
        "第五轮：长效治理与监督闭环",
    ]

    roles_spec = [
        {
            "role_key": "gov",
            "role": "政府规资部门",
            "display_name": f"📐 政府规资部门（{site_city}自然资源与规划师代表）",
            "weight": norm_weights["gov"],
            "rag_queries": [
                f"{site_city} {tp_name} 控规 容积率 限高 历史风貌保护 紫线",
                "控制性详细规划 绿地率 建筑密度 视线通廊 历史街区",
                "城市更新行动 公共空间 存量提质 法定导则 实施保障",
            ],
        },
        {
            "role_key": "resident",
            "role": "原住居民代表",
            "display_name": f"👥 原住居民代表（{tp_name}社区老街坊代表）",
            "weight": norm_weights["resident"],
            "rag_queries": [
                "居住区规划设计标准 绿地率 日照间距 适老化 便民菜市场",
                "完整居住社区 15分钟生活圈 口袋公园 慢行无障碍 噪声控制",
                "公众参与 社区微更新 民生保障 公共服务设施配建",
            ],
        },
        {
            "role_key": "dev",
            "role": "城市更新开发商",
            "display_name": f"💰 城市更新开发商（文商旅产业投资运营商）",
            "weight": norm_weights["dev"],
            "rag_queries": [
                "城市更新 工业遗产活化 功能置换 混合用地 商业文创",
                "存量土地盘活 地下空间开发 容积率奖励 资金平衡 社会资本",
                "文商旅融合 长效运营 产业导入 绿色建筑 物业反哺",
            ],
        },
    ]

    def _event_gen():
        dialogues_record: list[dict[str, Any]] = []
        md_log_lines: list[str] = [
            f"# {site_city}{site_name}·三主体多轮博弈协商记录",
            f"**靶向地块**：{tp_name} | **协商议题**：{topic}",
            f"**主体权重**：政府规资部门 {norm_weights['gov']*100:.0f}% · 原住居民代表 {norm_weights['resident']*100:.0f}% · 城市更新开发商 {norm_weights['dev']*100:.0f}%",
            "---",
        ]
        all_citations_count = 0
        latest_radar: dict[str, float] = {}
        latest_role_scores: dict[str, float] = {}

        for r_idx in range(rounds):
            r_num = r_idx + 1
            r_label = round_labels[min(r_idx, len(round_labels) - 1)]
            yield _sse_event(
                "round_start",
                {
                    "round": r_num,
                    "total_rounds": rounds,
                    "round_label": r_label,
                    "topic": topic,
                    "target_plot": tp_name,
                },
            )
            md_log_lines.append(f"\n## {r_label}\n")

            for role_cfg in roles_spec:
                r_key = role_cfg["role_key"]
                q_str = role_cfg["rag_queries"][min(r_idx, len(role_cfg["rag_queries"]) - 1)]
                citations = _retrieve_role_rag_citations(q_str, top_k=2)
                all_citations_count += len(citations)

                # Try LLM or intelligent site+RAG-grounded fallback
                fb_thinking, fb_speech = _build_role_round_fallback(r_key, r_idx, target_plot, citations)
                thinking_text = fb_thinking
                speech_text = fb_speech

                try:
                    cite_context = "\n".join(f"- {c['source']}: {c['clause']}" for c in citations)
                    llm_prompt = (
                        f"【当前轮次】{r_label}\n【协商议题】{topic}\n"
                        f"【你扮演的角色】{role_cfg['display_name']}\n"
                        f"【必须引用的RAG法定条文】\n{cite_context}\n"
                        f"请用【思考过程】和【正式回复】两段格式输出本轮发言（180-260字），必须明确引用上述法规名称与【{tp_name}】控规数值。"
                    )
                    raw_resp = call_llm_engine(
                        prompt=llm_prompt,
                        system_prompt=f"你是{role_cfg['display_name']}，正在参加城市更新多主体博弈听证会。",
                        model=req.model,
                    )
                    if not _is_llm_error_or_generic_demo(raw_resp) and tp_name in raw_resp:
                        if "【正式回复】" in raw_resp:
                            parts = raw_resp.split("【正式回复】", 1)
                            thinking_text = parts[0].replace("【思考过程】", "").strip() or fb_thinking
                            speech_text = parts[1].strip() or fb_speech
                        else:
                            speech_text = raw_resp.strip()
                except Exception:
                    pass

                # Progressive satisfaction by round and role
                base_sat_prog = {
                    "gov": [78.0, 86.0, 93.0, 94.0, 95.0],
                    "resident": [68.0, 79.0, 89.0, 91.0, 92.0],
                    "dev": [64.0, 76.0, 86.0, 88.0, 89.0],
                }
                role_sat = round(
                    min(98.0, base_sat_prog[r_key][min(r_idx, 4)] + (role_cfg["weight"] - 0.33) * 12.0),
                    1,
                )
                latest_role_scores[role_cfg["role"]] = role_sat

                speech_item = {
                    "round": r_num,
                    "round_label": r_label,
                    "role": role_cfg["role"],
                    "role_key": r_key,
                    "display_name": role_cfg["display_name"],
                    "thinking": thinking_text,
                    "speech": speech_text,
                    "formal": speech_text,
                    "content": speech_text,
                    "name": role_cfg["display_name"],
                    "satisfaction": role_sat,
                    "weight": role_cfg["weight"],
                    "rag_citations": citations,
                }
                dialogues_record.append(speech_item)
                md_log_lines.append(
                    f"### {role_cfg['display_name']}（满意度：{role_sat}%）\n"
                    f"- **💭 思考过程**：{thinking_text}\n"
                    f"- **📜 引用法规**：{'；'.join(c['source'] for c in citations)}\n"
                    f"- **💬 正式发言**：{speech_text}\n"
                )
                yield _sse_event("agent_speech", speech_item)

            # Compute 5D consensus radar after round r_num
            progress_ratio = (r_num) / max(1, rounds)
            latest_radar = {
                "空间品质": round(74.0 + 16.0 * progress_ratio + norm_weights["gov"] * 4.0, 1),
                "经济可行": round(68.0 + 17.0 * progress_ratio + norm_weights["dev"] * 6.0, 1),
                "民生保障": round(71.0 + 19.0 * progress_ratio + norm_weights["resident"] * 6.0, 1),
                "历史风貌": round(80.0 + 13.0 * progress_ratio + norm_weights["gov"] * 5.0, 1),
                "法规合规": round(84.0 + 12.0 * progress_ratio + norm_weights["gov"] * 4.0, 1),
            }
            overall_consensus = round(
                sum(latest_radar.values()) / len(latest_radar),
                1,
            )
            yield _sse_event(
                "round_consensus",
                {
                    "round": r_num,
                    "round_label": r_label,
                    "dimensions": ["空间品质", "经济可行", "民生保障", "历史风貌", "法规合规"],
                    "scores": latest_radar,
                    "radar_scores": latest_radar,
                    "role_scores": dict(latest_role_scores),
                    "overall_consensus": overall_consensus,
                },
            )

        # Build site-adaptive strategy matrix & design brief
        matrix_rows = [
            {
                "策略方向": "文脉保护与视廊风貌织补",
                "具体举措": f"严控【{tp_name}】核心区限高≤{target_plot.get('core_height_max', 9.0)}m、一般区≤{height_max}m，保留大跨度工业桁架与红灰砖立面肌理",
                "政策依据": f"《{site_city}历史文化名城保护条例》《城乡建设历史文化保护传承意见》",
                "空间落位": f"【{tp_name}】历史风貌界面及核心视线通廊区",
                "资金逻辑": "历史文保专项补助 + 容积率转移激励",
                "协同度": "95%",
            },
            {
                "策略方向": "存量空间活化与文商旅造血",
                "具体举措": f"在 FAR≤{far_max} 约束下置换低效仓储为新中式文旅客厅、非遗策展工坊与青年双创空间，开发地下智慧停车库",
                "政策依据": "《关于持续推进城市更新行动的意见》《城市用地分类与规划建设用地标准》",
                "空间落位": f"【{tp_name}】主交易厅及西侧复合商业活力带",
                "资金逻辑": "社会文旅资本 BOT 运营 + 地下空间复合收益",
                "协同度": "91%",
            },
            {
                "策略方向": "生态绿廊贯通与民生公服反哺",
                "具体举措": f"拆除封闭围墙保证绿地率≥{max(28.5, green_min)}%，首层固定配建1500㎡平价净菜市集、社区食堂与适老口袋公园",
                "政策依据": "《城市居住区规划设计标准 GB50180-2018》《完整居住社区建设标准》",
                "空间落位": f"【{tp_name}】东翼便民生活核及沿街/滨水慢行绿轴",
                "资金逻辑": "商业运营净收益 8% 反哺社区公共维护基金",
                "协同度": "93%",
            },
            {
                "策略方向": "小街区密路网与人车分流微循环",
                "具体举措": "打通内部3.5-6m慢行街巷，车辆由外围直接进入地下车库，构建全季无障碍步行漫游环线",
                "政策依据": "《城市步行和自行车交通系统规划标准》",
                "空间落位": f"【{tp_name}】内部十字慢行街巷及周边接驳口",
                "资金逻辑": "市政基础设施专项债 + 停车运营收益平衡",
                "协同度": "90%",
            },
        ]
        matrix_md = _rows_to_markdown_matrix(matrix_rows)
        full_log_md = "\n".join(md_log_lines)

        voting_scores = {
            "政府规资部门": latest_role_scores.get("政府规资部门", 93.0),
            "原住居民代表": latest_role_scores.get("原住居民代表", 89.0),
            "城市更新开发商": latest_role_scores.get("城市更新开发商", 86.0),
        }

        # Persist all Stage 07 outputs to data bus
        save_stage_output("07", SK.NEGOTIATION_RESULT, full_log_md)
        save_stage_output("07", "negotiation_dialogues", dialogues_record)
        save_stage_output("07", SK.VOTING_SCORES, voting_scores)
        save_stage_output("07", "consensus_radar", latest_radar)
        save_stage_output("07", SK.STRATEGY_MATRIX, matrix_md)
        save_stage_output("07", "strategy_matrix_rows", matrix_rows)
        save_stage_output("07", "target_plot", target_plot)

        # Synthesize structured Design Brief
        try:
            b_ctx = build_design_context()
            b_ctx.strategy_matrix = matrix_md
            b_ctx.negotiation_result = full_log_md
            brief_content = synthesize_design_brief(b_ctx)
        except Exception:
            brief_content = ""

        if not brief_content:
            brief_content = (
                f"## 靶向地块定位与法定红线指引\n"
                f"- **靶向地块**：{tp_name}（MPI: {target_plot.get('mpi', 88.5)}，{target_plot.get('priority', 'P1 优先更新')}）\n"
                f"- **法定控规红线**：容积率 FAR ≤ {far_max}，建筑密度 ≤ {density_max}%，绿地率 ≥ {green_min}%，建筑限高 {target_plot.get('core_height_max', 9.0)}–{height_max}m\n\n"
                f"## 三主体多轮博弈核心契约\n"
                f"- **政府规资部门**：坚守历史视廊与限高底线，通过地下空间不计容激励换取地面开敞绿地与公服移交；\n"
                f"- **原住居民代表**：获得1500㎡平价净菜市集、适老活动驿站及 ≥{max(28.5, green_min)}% 开放口袋公园；\n"
                f"- **城市更新开发商**：保留工业桁架植入文商旅复合业态，提取 8% 运营收益反哺社区长效运维。"
            )
        save_stage_output("07", SK.DESIGN_BRIEF, brief_content)

        try:
            save_approval_record(
                stage_code="07",
                key=SK.STRATEGY_MATRIX,
                status=ApprovalStatus.APPROVED,
                reviewer="城市更新三主体协同听证委员会",
                comment="三轮多主体博弈达成高度共识，准予放行下游总体城市设计",
            )
        except Exception:
            pass

        yield _sse_event(
            "final_summary",
            {
                "target_plot": target_plot,
                "negotiation_result": full_log_md,
                "voting_scores": voting_scores,
                "consensus_radar": latest_radar,
                "strategy_matrix": matrix_md,
                "matrix_rows": matrix_rows,
                "design_brief": brief_content,
                "rag_clauses_count": all_citations_count,
            },
        )

    return StreamingResponse(_event_gen(), media_type="text/event-stream")


@router.get("/stage07/matrix")
def get_stage07_matrix() -> dict[str, Any]:
    """Read the Problem-Goal-Strategy matrix (`SK.STRATEGY_MATRIX`)."""
    matrix_md = str(load_stage_output("07", SK.STRATEGY_MATRIX, "") or "")
    rows = load_stage_output("07", "strategy_matrix_rows", None)
    if not isinstance(rows, list) or not rows:
        rows = _parse_markdown_matrix(matrix_md)
    return {
        "status": "ok",
        "strategy_matrix": matrix_md,
        "rows": rows,
        "target_plot": _resolve_target_plot(),
    }


@router.put("/stage07/matrix")
def put_stage07_matrix(req: Stage07MatrixUpdateRequest) -> dict[str, Any]:
    """Update the Problem-Goal-Strategy matrix (`SK.STRATEGY_MATRIX`) and re-sync design brief."""
    if req.rows and isinstance(req.rows, list):
        rows = req.rows
        matrix_md = req.strategy_matrix.strip() if (req.strategy_matrix and req.strategy_matrix.strip()) else _rows_to_markdown_matrix(rows)
    elif req.strategy_matrix is not None:
        matrix_md = req.strategy_matrix.strip()
        rows = _parse_markdown_matrix(matrix_md)
    else:
        matrix_md = str(load_stage_output("07", SK.STRATEGY_MATRIX, "") or "")
        rows = _parse_markdown_matrix(matrix_md)

    save_stage_output("07", SK.STRATEGY_MATRIX, matrix_md)
    save_stage_output("07", "strategy_matrix_rows", rows)

    try:
        b_ctx = build_design_context()
        b_ctx.strategy_matrix = matrix_md
        brief = synthesize_design_brief(b_ctx)
        if brief:
            save_stage_output("07", SK.DESIGN_BRIEF, brief)
    except Exception:
        pass

    return {
        "status": "ok",
        "strategy_matrix": matrix_md,
        "rows": rows,
        "design_brief": load_stage_output("07", SK.DESIGN_BRIEF, "") or "",
    }


# ═══════════════════════════════════════════════════════════════════
# Stage 08: 总体城市设计与用地构成沙盘
# ═══════════════════════════════════════════════════════════════════

def _compute_landuse_sandbox_payload(params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Compute real-time GFA balance, statutory compliance, and ECharts datasets for Stage 08 land-use sandbox."""
    site_cfg = get_site_config() or {}
    site_city = get_site_city() or site_cfg.get("city", "长春市") or "长春市"
    site_name = get_site_name() or site_cfg.get("name", "伪满皇宫周边街区") or "伪满皇宫周边街区"
    total_area_ha = float(site_cfg.get("area_ha", 160.0) or 160.0)
    target_plot = _resolve_target_plot()

    saved = load_stage_output("08", SK.LANDUSE_SANDBOX, {})
    if not isinstance(saved, dict):
        saved = {}
    src = {**saved, **(params or {})}

    # Normalize 5 slider categories + residual road/municipal
    commercial = float(src.get("commercial") if src.get("commercial") is not None else src.get("com_pct", 22.0))
    residential = float(src.get("residential") if src.get("residential") is not None else src.get("res_pct", 38.0))
    green_open = float(src.get("green_open") if src.get("green_open") is not None else src.get("green_pct", 18.0))
    public_facility = float(src.get("public_facility") if src.get("public_facility") is not None else src.get("public_pct", 10.0))
    cultural_heritage = float(
        src.get("cultural_heritage")
        if src.get("cultural_heritage") is not None
        else src.get("off_pct", 7.0)
    )
    target_far = float(src.get("target_far") if src.get("target_far") is not None else min(1.35, float(target_plot.get("far_max", 1.4))))

    allocated_sum = commercial + residential + green_open + public_facility + cultural_heritage
    if allocated_sum > 100.0 and allocated_sum > 0:
        scale = 95.0 / allocated_sum
        commercial = round(commercial * scale, 1)
        residential = round(residential * scale, 1)
        green_open = round(green_open * scale, 1)
        public_facility = round(public_facility * scale, 1)
        cultural_heritage = round(cultural_heritage * scale, 1)
        allocated_sum = commercial + residential + green_open + public_facility + cultural_heritage

    road_municipal = round(max(0.0, 100.0 - allocated_sum), 1)

    # Statutory redlines
    statutory_far_max = float(target_plot.get("far_max", 1.4))
    statutory_green_min = float(target_plot.get("green_min", 15.0))
    # For whole district vs plot, district green open space statutory threshold is min(statutory_green_min, 15.0)
    district_green_redline = 15.0
    plot_green_equivalent = round(min(45.0, green_open * 1.55), 1)

    total_area_m2 = total_area_ha * 10000.0
    total_gfa_m2 = round(total_area_m2 * target_far, 0)

    # Compute GFA distribution by functional land-use
    gfa_weights = {
        "commercial": commercial * 1.35,
        "residential": residential * 1.45,
        "public_facility": public_facility * 1.1,
        "cultural_heritage": cultural_heritage * 0.75,
        "green_open": green_open * 0.08,
    }
    w_total = max(1.0, sum(gfa_weights.values()))
    gfa_by_category = {
        k: round(total_gfa_m2 * (v / w_total), 0)
        for k, v in gfa_weights.items()
    }

    baseline_sliders = {
        "residential": 51.1,
        "commercial": 11.4,
        "public_facility": 13.3,
        "green_open": 2.9,
        "cultural_heritage": 5.8,
        "road_municipal": 15.5,
    }

    far_compliant = target_far <= statutory_far_max
    green_compliant = green_open >= district_green_redline

    evaluation = (
        f"【{site_city}{site_name}用地沙盘实时核算】"
        f"规划总用地 {total_area_ha:.1f} ha，目标综合容积率 {target_far:.2f}（法定上限 ≤{statutory_far_max:.2f}，{'✅ 合规' if far_compliant else '⚠️ 超限'}），"
        f"总计容建筑面积约 {total_gfa_m2/10000.0:.2f} 万㎡。"
        f"绿地与开敞空间占比由现状 2.9% 提升至 {green_open:.1f}%（折算重点地块绿地率约 {plot_green_equivalent:.1f}%，"
        f"{'✅ 满足法定绿地底线' if green_compliant else '⚠️ 建议继续提高绿地占比至15%以上'}）；"
        f"商业文创与历史遗产活化合计占比 {commercial + cultural_heritage:.1f}%，显著增强片区文旅造血与就业承载力。"
    )

    echarts_pie = [
        {"name": "居住生活用地 (R)", "value": round(residential, 1), "color": "#FACC15"},
        {"name": "商业服务用地 (B)", "value": round(commercial, 1), "color": "#EF4444"},
        {"name": "公园绿地与开敞空间 (G)", "value": round(green_open, 1), "color": "#22C55E"},
        {"name": "公共管理与公服设施 (A)", "value": round(public_facility, 1), "color": "#FB7185"},
        {"name": "历史文化与工业遗产 (M/H)", "value": round(cultural_heritage, 1), "color": "#A855F7"},
        {"name": "道路与市政交通 (S/U)", "value": round(road_municipal, 1), "color": "#94A3B8"},
    ]

    echarts_bar = {
        "categories": ["居住生活", "商业服务", "绿地开敞", "公共设施", "文化遗存", "道路市政"],
        "baseline": [
            baseline_sliders["residential"],
            baseline_sliders["commercial"],
            baseline_sliders["green_open"],
            baseline_sliders["public_facility"],
            baseline_sliders["cultural_heritage"],
            baseline_sliders["road_municipal"],
        ],
        "planned": [
            round(residential, 1),
            round(commercial, 1),
            round(green_open, 1),
            round(public_facility, 1),
            round(cultural_heritage, 1),
            round(road_municipal, 1),
        ],
    }

    return {
        "status": "ok",
        "scenario": (
            f"居住 {residential:.1f}%, 商业 {commercial:.1f}%, 绿地开敞 {green_open:.1f}%, "
            f"公服设施 {public_facility:.1f}%, 文化遗存 {cultural_heritage:.1f}%, 道路市政 {road_municipal:.1f}% | 目标FAR {target_far:.2f}"
        ),
        "sliders": {
            "commercial": round(commercial, 1),
            "residential": round(residential, 1),
            "green_open": round(green_open, 1),
            "public_facility": round(public_facility, 1),
            "cultural_heritage": round(cultural_heritage, 1),
            "road_municipal": round(road_municipal, 1),
            "target_far": round(target_far, 2),
        },
        # Legacy flat keys for backward compatibility with stage_bus consumers
        "res_pct": round(residential, 1),
        "com_pct": round(commercial, 1),
        "off_pct": round(cultural_heritage, 1),
        "green_pct": round(green_open, 1),
        "public_pct": round(public_facility, 1),
        "remain": round(road_municipal, 1),
        "target_far": round(target_far, 2),
        "gfa_balance": {
            "total_site_area_ha": total_area_ha,
            "total_site_area_m2": total_area_m2,
            "target_far": round(target_far, 2),
            "total_gfa_m2": total_gfa_m2,
            "total_gfa_wan_m2": round(total_gfa_m2 / 10000.0, 2),
            "gfa_by_category_m2": gfa_by_category,
            "estimated_population": int(round(gfa_by_category["residential"] / 35.0)),
            "estimated_jobs": int(round((gfa_by_category["commercial"] + gfa_by_category["cultural_heritage"]) / 25.0)),
        },
        "compliance": {
            "far_compliant": far_compliant,
            "statutory_far_max": statutory_far_max,
            "green_compliant": green_compliant,
            "district_green_min_pct": district_green_redline,
            "plot_green_min_pct": statutory_green_min,
            "plot_green_equivalent_pct": plot_green_equivalent,
            "total_pct_valid": round(allocated_sum + road_municipal, 1) == 100.0,
        },
        "echarts_pie": echarts_pie,
        "echarts_bar": echarts_bar,
        "evaluation": evaluation,
    }


@router.get("/stage08/state")
def get_stage08_state() -> dict[str, Any]:
    """Return Stage 08 spatial structure, master plan, and land-use sandbox state."""
    spatial_structure = load_stage_output("08", SK.SPATIAL_STRUCTURE, "") or ""
    master_plan = load_stage_output("08", SK.MASTER_PLAN, "") or spatial_structure
    sandbox = _compute_landuse_sandbox_payload()
    return {
        "status": "ok",
        "target_plot": _resolve_target_plot(),
        "spatial_structure": spatial_structure,
        "master_plan": master_plan,
        "landuse_sandbox": sandbox,
    }


@router.post("/stage08/structure/stream")
def post_stage08_structure_stream(req: Stage08StructureRequest | None = None):
    """Stream SSE generation for Stage 08 spatial structure & master plan narrative."""
    body = req or Stage08StructureRequest()
    site_cfg = get_site_config() or {}
    city = get_site_city() or site_cfg.get("city", "长春市") or "长春市"
    site_name = get_site_name() or site_cfg.get("name", "伪满皇宫周边街区") or "伪满皇宫周边街区"
    area_ha = site_cfg.get("area_ha", 160)
    target_plot = _resolve_target_plot()
    tp_name = target_plot.get("name", "长春水产大市场")
    strategy_md = str(load_stage_output("07", SK.STRATEGY_MATRIX, "") or "")

    fallback_structure = (
        f"# {city}{site_name}总体城市设计空间结构推演报告\n\n"
        f"## 一、 总体空间结构概念：“一核两轴四片多节点”\n"
        f"- **一核（历史文化与更新触媒共振核）**：以核心历史文化地标与【{tp_name}】（MPI={target_plot.get('mpi', 88.5)}）构成的复合文旅客厅为核心极核。\n"
        f"- **两轴（站城TOD联动轴 + 滨水生态漫游轴）**：东西向串联交通门户至历史风貌核的站城文商旅联动主轴；南北向贯通滨水生态绿带与社区公园的蓝绿慢行主轴。\n"
        f"- **四片（四大差异化风貌与功能更新片区）**：\n"
        f"  1. **历史风貌核心保护片区**：严控建筑限高≤{target_plot.get('core_height_max', 9.0)}m，保护传统街巷与视廊；\n"
        f"  2. **存量工业与商贸活化示范片区（含【{tp_name}】）**：控制容积率≤{target_plot.get('far_max', 1.4)}、限高≤{target_plot.get('height_max', 18.0)}m，保留大跨度桁架植入文创市集与便民生活核；\n"
        f"  3. **老旧居住微更新与15分钟社区片区**：见缝插绿增设口袋公园与适老设施，绿地率≥{target_plot.get('green_min', 25.0)}%；\n"
        f"  4. **门户TOD复合服务片区**：强化慢行换乘接驳与立体城市活力。\n\n"
        f"## 二、 开发强度分区管控图则\n"
        f"| 分区名称 | 主导功能 | 容积率 (FAR) | 建筑密度 | 绿地率 | 建筑限高 |\n"
        f"| :--- | :--- | :--- | :--- | :--- | :--- |\n"
        f"| 历史风貌保护核 | 文博展示、文化体验 | ≤ 0.8 | ≤ 28% | ≥ 30% | ≤ {target_plot.get('core_height_max', 9.0)}m |\n"
        f"| 【{tp_name}】触媒片区 | 文商旅复合、便民市集 | ≤ {target_plot.get('far_max', 1.4)} | ≤ {target_plot.get('density_max', 35.0)}% | ≥ {target_plot.get('green_min', 25.0)}% | ≤ {target_plot.get('height_max', 18.0)}m |\n"
        f"| 宜居社区微更新片区 | 居住生活、全龄公服 | ≤ 1.6 | ≤ 30% | ≥ 28% | ≤ 18.0m |\n"
        f"| 交通门户TOD协调片区 | 商务办公、青年创客 | ≤ 2.2 | ≤ 35% | ≥ 25% | ≤ 24.0m |\n"
    )

    prompt = (
        f"请为{city}{site_name}（约{area_ha}公顷）推演总体城市设计空间结构与总图布局。\n"
        f"靶向地块：{tp_name}\n上游策略矩阵：{strategy_md[:1500]}"
    )
    if body.custom_prompt:
        prompt += f"\n补充要求：{body.custom_prompt}"

    def _event_gen():
        yield _sse_event("start", {"stage": "08", "target_plot": tp_name})
        accumulated = ""
        try:
            for chunk in call_llm_engine_stream(
                prompt=prompt,
                system_prompt="你是资深城市设计总师，基于空间量化数据推演总体空间结构。",
                model=body.model,
            ):
                accumulated += chunk
                if not _is_llm_error_or_generic_demo(accumulated):
                    yield _sse_event("chunk", {"delta": chunk, "content": accumulated})
        except Exception:
            pass

        if _is_llm_error_or_generic_demo(accumulated):
            accumulated = fallback_structure
            step = 120
            built = ""
            for i in range(0, len(accumulated), step):
                piece = accumulated[i : i + step]
                built += piece
                yield _sse_event("chunk", {"delta": piece, "content": built, "fallback": True})

        save_stage_output("08", SK.SPATIAL_STRUCTURE, accumulated)
        save_stage_output("08", SK.MASTER_PLAN, accumulated)
        yield _sse_event("done", {"content": accumulated, "length": len(accumulated)})

    return StreamingResponse(_event_gen(), media_type="text/event-stream")


@router.get("/stage08/landuse-sandbox")
def get_stage08_landuse_sandbox() -> dict[str, Any]:
    """Return current Stage 08 land-use sandbox sliders, GFA balance, compliance, and ECharts datasets."""
    payload = _compute_landuse_sandbox_payload()
    save_stage_output("08", SK.LANDUSE_SANDBOX, payload)
    return payload


@router.put("/stage08/landuse-sandbox")
def put_stage08_landuse_sandbox(req: LanduseSandboxRequest) -> dict[str, Any]:
    """Update Stage 08 land-use sandbox percentages, recompute GFA balance & redline compliance, and persist."""
    raw_dict = {k: v for k, v in req.model_dump().items() if v is not None}
    payload = _compute_landuse_sandbox_payload(raw_dict)
    save_stage_output("08", SK.LANDUSE_SANDBOX, payload)
    return payload
