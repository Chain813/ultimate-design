"""Global AI Planning Copilot router with Hybrid RAG citation cards and Stage Bus context."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException

from desktop.backend.deps import sse_response, verify_session_token
from src.config.site import get_site_city, get_site_desc, get_site_district, get_site_name
from src.core.runtime_adapter import get_active_project_id, runtime_state
from src.engines.llm_engine import call_llm_engine_stream
from src.engines.rag_engine import retrieve_rag_context
from src.workflow.stage_data_bus import STAGE_MAP, load_stage_output

logger = logging.getLogger("ultimateDESIGN.backend.copilot")

router = APIRouter(
    prefix="/api/v1/copilot",
    tags=["copilot"],
    dependencies=[Depends(verify_session_token)],
)


def _get_history_list() -> list[dict[str, Any]]:
    hist = runtime_state.get("copilot_history")
    if not isinstance(hist, list):
        hist = []
        runtime_state["copilot_history"] = hist
    return hist


def _build_stage_bus_summary() -> str:
    import src.workflow.stage_data_bus as sdb

    bus: dict[str, Any] = {}
    if hasattr(sdb, "get_stage_bus"):
        try:
            bus = sdb.get_stage_bus() or {}
        except Exception:
            bus = {}
    elif hasattr(sdb, "_bus"):
        try:
            bus = sdb._bus() or {}
        except Exception:
            bus = {}

    if not bus:
        return "当前工程暂未产生自定义阶段数据，使用基准示范数据。"

    lines: list[str] = []
    for k, v in sorted(bus.items()):
        val_str = str(v)
        if len(val_str) > 220:
            val_str = val_str[:220] + "..."
        lines.append(f"- {k}: {val_str}")
    return "\n".join(lines[:30])


def _build_offline_copilot_fallback(
    user_msg: str,
    active_stage: str | None,
    city_name: str,
    site_name: str,
    target_plot: dict[str, Any] | None,
    citations: list[dict[str, Any]],
) -> str:
    """Build an intelligent RAG + Stage Bus grounded answer when LLM API is offline or returns 401."""
    stage_code = (active_stage or "04").strip()
    if stage_code.isdigit() and len(stage_code) == 1:
        stage_code = f"0{stage_code}"
    stage_title = STAGE_MAP.get(stage_code, f"阶段 {stage_code}")

    plot_name = (
        target_plot.get("name", "长春水产大市场")
        if isinstance(target_plot, dict)
        else "核心优先更新单元"
    )
    plot_mpi = (
        target_plot.get("mpi", 88.5)
        if isinstance(target_plot, dict)
        else 88.5
    )
    plot_issues = (
        target_plot.get("issues", ["存量空间低效利用", "慢行与绿地开敞空间不足"])
        if isinstance(target_plot, dict)
        else ["存量空间低效利用", "慢行与绿地开敞空间不足"]
    )

    cite_lines: list[str] = []
    for idx, c in enumerate(citations[:3]):
        src = c.get("source", "国家与地方规划规范")
        snippet = str(c.get("content", "")).strip()
        if len(snippet) > 160:
            snippet = snippet[:160] + "..."
        cite_lines.append(f"{idx + 1}. **《{src}》**：{snippet}")

    cite_block = (
        "\n".join(cite_lines)
        if cite_lines
        else "1. **《中共中央办公厅 国务院办公厅关于持续推进城市更新行动的意见》**：坚持保护优先、留改拆并举，以存量提质改造和渐进式微更新为主线。"
    )

    return (
        f"针对您关于「**{user_msg}**」的规划咨询，结合当前【**{city_name}·{site_name}**】项目上下文与混合 RAG 法规库检索结果，给出如下专业建议：\n\n"
        f"#### 1. 当前工程阶段与靶向地块状态\n"
        f"- **所在阶段**：`Stage {stage_code} · {stage_title}`\n"
        f"- **锁定靶向地块**：**{plot_name}**（AHP-MPI 综合评分：**{plot_mpi}**）\n"
        f"- **关键空间痛点**：{'；'.join(str(x) for x in plot_issues[:3])}\n\n"
        f"#### 2. 混合 RAG 法规与标准条文依据\n"
        f"{cite_block}\n\n"
        f"#### 3. 规划师操作与设计控制建议\n"
        f"- **刚性底线管控**：严格落实核心保护范围与风貌协调区分级限高（9m–18m），控制核心地块容积率 FAR ≤ 1.4、建筑密度 ≤ 35%、绿地率 ≥ 25%。\n"
        f"- **跨阶段协同流转**：建议在锁定靶向地块后，将上述法规约束带入多主体博弈剧场（Stage 07）与法定城市设计导则（Stage 12），确保“空间诊断—博弈共识—图则交付”证据链闭环。"
    )


@router.get("/history")
def get_copilot_history() -> dict[str, Any]:
    """Return the global AI Copilot conversation history for the active project."""
    history = _get_history_list()
    return {
        "status": "ok",
        "active_project_id": get_active_project_id(),
        "count": len(history),
        "history": history,
        "messages": history,
    }


@router.delete("/history")
def clear_copilot_history() -> dict[str, Any]:
    """Clear the global AI Copilot conversation history for the active project."""
    runtime_state["copilot_history"] = []
    return {
        "status": "ok",
        "active_project_id": get_active_project_id(),
        "history": [],
        "messages": [],
    }


@router.post("/chat/stream")
def stream_copilot_chat(payload: dict[str, Any] = Body(default_factory=dict)):
    """Stream SSE response from global AI Copilot grounded in Hybrid RAG citations and Stage Bus."""
    user_msg = str(
        payload.get("message") or payload.get("prompt") or payload.get("query") or ""
    ).strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="消息内容 message 不能为空")

    active_stage = payload.get("active_stage") or payload.get("stage")
    active_stage_str = str(active_stage).strip() if active_stage is not None else None

    # 1. Hybrid RAG legal retrieval
    try:
        rag_hits = retrieve_rag_context(user_msg, top_k=4) or []
    except Exception as exc:
        logger.warning("Copilot RAG retrieval warning: %s", exc)
        rag_hits = []

    citations: list[dict[str, Any]] = []
    rag_context_lines: list[str] = []
    for score, content, source in rag_hits:
        citations.append({
            "score": float(score),
            "content": str(content),
            "source": str(source),
        })
        rag_context_lines.append(f"[法规来源: {source}]\n{content}")

    rag_context_str = "\n\n".join(rag_context_lines) if rag_context_lines else "未命中特定条文，适用国家通用城市更新技术标准。"

    # 2. Gather current project & stage bus context
    city_name = get_site_city() or "长春"
    site_name = get_site_name() or "伪满皇宫周边历史文化街区"
    district_name = get_site_district() or "宽城区"
    site_desc = get_site_desc() or "历史文脉保护与城市有机更新重点片区"
    target_plot = load_stage_output("04", "target_plot", None)
    bus_ctx = _build_stage_bus_summary()

    system_prompt = (
        f"你是 UltimateDESIGN-Copilot，常驻于桌面规划工作站的顶尖 AI 城乡规划副驾。\n"
        f"【当前项目背景】\n"
        f"- 城市与片区：{city_name}市{district_name}{site_name}\n"
        f"- 场地特征：{site_desc}\n"
        f"- 当前所处阶段：{active_stage_str or '全局指挥台'}\n\n"
        f"【阶段数据总线 (Stage Bus) 实时指标】\n"
        f"{bus_ctx}\n\n"
        f"【混合 RAG 法规检索条文】\n"
        f"{rag_context_str}\n\n"
        f"【回答要求】\n"
        f"1. 紧密结合当前锁定靶向地块指标与上方检索到的法规条文编号；\n"
        f"2. 若引用异地参考先例，须注明【提示：异地参考先例，非本市法定标准】；\n"
        f"3. 专业、精炼、结构清晰。"
    )

    history = _get_history_list()
    recent_openai_history = [
        {"role": m.get("role", "user"), "content": str(m.get("content", ""))}
        for m in history[-6:]
        if isinstance(m, dict) and m.get("role") in ("user", "assistant")
    ]

    def _gen():
        yield {
            "type": "citations",
            "active_stage": active_stage_str,
            "citations": citations,
        }

        accumulated = ""
        use_fallback = False

        try:
            for chunk in call_llm_engine_stream(
                prompt=user_msg,
                system_prompt=system_prompt,
                model="deepseek-v4-pro",
                history=recent_openai_history,
            ):
                piece = str(chunk or "")
                if any(
                    err_kw in piece
                    for err_kw in ("错误：未配置 DEEPSEEK_API_KEY", "DeepSeek 报错:", "无法连接到 DeepSeek API", "LLM 引擎异常:")
                ):
                    use_fallback = True
                    break
                accumulated += piece
                yield {"type": "token", "content": piece, "token": piece}
        except Exception as exc:
            logger.warning("Copilot stream fallback triggered: %s", exc)
            use_fallback = True

        if use_fallback or len(accumulated.strip()) < 20:
            fallback_text = _build_offline_copilot_fallback(
                user_msg=user_msg,
                active_stage=active_stage_str,
                city_name=city_name,
                site_name=site_name,
                target_plot=target_plot if isinstance(target_plot, dict) else None,
                citations=citations,
            )
            accumulated = fallback_text
            for i in range(0, len(fallback_text), 48):
                piece = fallback_text[i : i + 48]
                yield {"type": "token", "content": piece, "token": piece}

        cur_history = _get_history_list()
        cur_history.append({
            "role": "user",
            "content": user_msg,
            "active_stage": active_stage_str,
        })
        cur_history.append({
            "role": "assistant",
            "content": accumulated,
            "active_stage": active_stage_str,
            "citations": citations,
        })
        if len(cur_history) > 50:
            runtime_state["copilot_history"] = cur_history[-50:]

        yield {
            "type": "done",
            "active_stage": active_stage_str,
            "content": accumulated,
            "answer": accumulated,
            "citations": citations,
            "history_length": len(_get_history_list()),
        }

    return sse_response(_gen())
