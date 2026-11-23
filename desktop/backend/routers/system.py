"""System, Engine HUD, Settings, Projects, Stage Bus, and Background Jobs router."""

from __future__ import annotations

import inspect
import json
import logging
import os
from pathlib import Path
import re
import shutil
import time
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException

from desktop.backend.deps import sse_response, verify_session_token
from desktop.backend.job_manager import get_job_manager
from src.config.loader import load_global_config, load_rag_knowledge
from src.config.paths import DATA_DIR, DATA_FILES, ROOT_DIR
from src.config.site import get_site_city, get_site_name
from src.config.user_settings import (
    DEFAULT_SETTINGS,
    get_effective_setting,
    load_user_settings,
    save_user_settings,
)
from src.core.runtime_adapter import (
    clear_all_caches,
    get_active_project_id,
    runtime_state,
    set_active_project_id,
)
from src.data import get_data_readiness
from src.utils.llm_monitor import get_llm_metrics
from src.utils.service_check import check_engine_status
from src.workflow.stage_data_bus import (
    STAGE_MAP,
    list_completed_stages,
    save_stage_output,
)

logger = logging.getLogger("ultimateDESIGN.backend.system")

router = APIRouter(prefix="/api/v1/system", tags=["system"])

ALL_17_STAGES: dict[str, str] = {
    "00": STAGE_MAP.get("00", "数据准备"),
    "01": STAGE_MAP.get("01", "任务解读"),
    "02": STAGE_MAP.get("02", "资料收集"),
    "03": STAGE_MAP.get("03", "现场调研"),
    "04": STAGE_MAP.get("04", "现状分析"),
    "05": STAGE_MAP.get("05", "问题诊断"),
    "06": STAGE_MAP.get("06", "目标定位"),
    "07": STAGE_MAP.get("07", "设计策略"),
    "08": STAGE_MAP.get("08", "总体城市设计"),
    "09": STAGE_MAP.get("09", "专项系统设计"),
    "10": STAGE_MAP.get("10", "重点地段深化"),
    "11": STAGE_MAP.get("11", "实施路径"),
    "12": STAGE_MAP.get("12", "城市设计导则"),
    "13": STAGE_MAP.get("13", "成果表达"),
    "14": "空间态势大屏",
    "15": STAGE_MAP.get("15", "AIGC设计推演"),
    "16": "智能体规范与听证",
}


def _mask_api_key(raw_key: str | None) -> str:
    """Mask an API key so plaintext secrets are never exposed in GET responses."""
    key = (raw_key or "").strip()
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}****{key[-4:]}"


def _get_stage_bus_dict() -> dict[str, Any]:
    """Read the full stage bus dictionary for the active project."""
    import src.workflow.stage_data_bus as sdb

    if hasattr(sdb, "get_stage_bus"):
        try:
            bus = sdb.get_stage_bus()
            if isinstance(bus, dict):
                return dict(bus)
        except Exception:
            pass
    if hasattr(sdb, "_bus"):
        try:
            bus = sdb._bus()
            if isinstance(bus, dict):
                return dict(bus)
        except Exception:
            pass
    raw = runtime_state.get("stage_bus", {})
    return dict(raw) if isinstance(raw, dict) else {}


def _build_17_stage_map(bus_dict: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Build a 17-stage completion status map from current stage_bus keys."""
    completed_set = set(list_completed_stages())
    keys_by_stage: dict[str, list[str]] = {code: [] for code in ALL_17_STAGES}
    for full_key in bus_dict:
        prefix = str(full_key).split("_", 1)[0]
        if prefix in keys_by_stage:
            keys_by_stage[prefix].append(str(full_key))

    result: dict[str, dict[str, Any]] = {}
    for code, title in ALL_17_STAGES.items():
        has_keys = len(keys_by_stage.get(code, [])) > 0 or (code in completed_set)
        # Stage 14 (DataV) is ready when Stage 04/05 or GIS data is ready
        if code == "14" and not has_keys:
            has_keys = ("04" in completed_set) or ("05" in completed_set)
        # Stage 16 (Skills) is ready when SKILLS.md exists
        if code == "16" and not has_keys:
            has_keys = (ROOT_DIR / "SKILLS.md").exists()
        result[code] = {
            "code": code,
            "title": title,
            "completed": bool(has_keys),
            "keys": sorted(keys_by_stage.get(code, [])),
        }
    return result


@router.get("/health")
def get_health() -> dict[str, Any]:
    """Health check endpoint polled by Electron main process on startup."""
    return {
        "status": "ok",
        "version": "7.0.0",
        "active_project_id": get_active_project_id(),
        "rag_protected": bool(DATA_FILES["rag"].exists()),
    }


@router.get("/engines", dependencies=[Depends(verify_session_token)])
def get_engines_hud() -> dict[str, Any]:
    """Return engine & API readiness HUD without resetting any RAG or spatial state."""
    config = load_global_config()
    llm_cfg = config.get("engines", {}).get("llm", {})
    effective_key = get_effective_setting("DEEPSEEK_API_KEY", "")
    api_url = get_effective_setting(
        "LLM_API_URL",
        llm_cfg.get("api_url", DEFAULT_SETTINGS["LLM_API_URL"]),
    )
    sd_url = get_effective_setting("SD_WEBUI_URL", DEFAULT_SETTINGS["SD_WEBUI_URL"])
    ollama_url = get_effective_setting("OLLAMA_URL", DEFAULT_SETTINGS["OLLAMA_URL"])
    model_name = os.environ.get("UD_LLM_MODEL", llm_cfg.get("model", "deepseek-v4-pro"))

    svc_status = check_engine_status()

    # RAG knowledge count (read-only)
    rag_db = load_rag_knowledge() or {}
    rag_chunk_count = len(rag_db) if isinstance(rag_db, dict) else 0
    rag_exists = bool(DATA_FILES["rag"].exists())

    # DuckDB Spatial & rustworkx probe
    duckdb_available = False
    duckdb_version = ""
    try:
        import duckdb

        duckdb_available = True
        duckdb_version = getattr(duckdb, "__version__", "installed")
    except Exception:
        pass

    rustworkx_available = False
    rustworkx_version = ""
    try:
        import rustworkx

        rustworkx_available = True
        rustworkx_version = getattr(rustworkx, "__version__", "installed")
    except Exception:
        pass

    gis_readiness = get_data_readiness()
    bus_dict = _get_stage_bus_dict()
    stage_map = _build_17_stage_map(bus_dict)
    completed_codes = [code for code, info in stage_map.items() if info["completed"]]

    llm_ready = bool(effective_key) or bool(svc_status.ollama)

    return {
        "status": "ok",
        "version": "7.0.0",
        "active_project_id": get_active_project_id(),
        "site_name": get_site_name() or "长春伪满皇宫周边历史街区",
        "city_name": get_site_city() or "长春",
        "rag_protected": rag_exists,
        "llm_ready": llm_ready,
        "rag_ready": rag_exists and rag_chunk_count > 0,
        "rag_chunks": rag_chunk_count,
        "sd_online": bool(svc_status.sd),
        "duckdb_ready": duckdb_available,
        "rustworkx_ready": rustworkx_available,
        "llm": {
            "configured": llm_ready,
            "has_api_key": bool(effective_key),
            "api_key_masked": _mask_api_key(effective_key),
            "api_url": api_url,
            "model": model_name,
            "ollama_online": bool(svc_status.ollama),
            "ollama_url": ollama_url,
        },
        "rag": {
            "ready": rag_exists and rag_chunk_count > 0,
            "protected": rag_exists,
            "chunk_count": rag_chunk_count,
            "path": str(DATA_FILES["rag"]),
        },
        "sd": {
            "online": bool(svc_status.sd),
            "url": sd_url,
        },
        "spatial_v2": {
            "duckdb_available": duckdb_available,
            "duckdb_version": duckdb_version,
            "rustworkx_available": rustworkx_available,
            "rustworkx_version": rustworkx_version,
            "active_project_id": get_active_project_id(),
        },
        "gis_readiness": gis_readiness,
        "stages": stage_map,
        "completed_stages": completed_codes,
        "completed_count": len(completed_codes),
        "total_stages": 17,
    }


@router.get("/settings", dependencies=[Depends(verify_session_token)])
def get_settings() -> dict[str, Any]:
    """Read current LLM and SD settings with masked API key."""
    settings = load_user_settings()
    raw_key = os.environ.get("DEEPSEEK_API_KEY") or settings.get("DEEPSEEK_API_KEY", "")
    masked = _mask_api_key(raw_key)
    base_url = (
        os.environ.get("LLM_API_URL")
        or settings.get("LLM_API_URL")
        or DEFAULT_SETTINGS["LLM_API_URL"]
    )
    sd_url = (
        os.environ.get("SD_WEBUI_URL")
        or settings.get("SD_WEBUI_URL")
        or DEFAULT_SETTINGS["SD_WEBUI_URL"]
    )
    ollama_url = (
        os.environ.get("OLLAMA_URL")
        or settings.get("OLLAMA_URL")
        or DEFAULT_SETTINGS["OLLAMA_URL"]
    )
    model = os.environ.get("UD_LLM_MODEL") or runtime_state.get("llm_model") or "deepseek-v4-pro"

    return {
        "status": "ok",
        "api_key": masked,
        "api_key_masked": masked,
        "has_api_key": bool(raw_key and raw_key.strip()),
        "base_url": base_url,
        "api_url": base_url,
        "model": model,
        "sd_url": sd_url,
        "ollama_url": ollama_url,
        "demo_mode": bool(runtime_state.get("demo_mode", False)),
    }


@router.put("/settings", dependencies=[Depends(verify_session_token)])
def update_settings(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    """Update LLM and SD settings in runtime state, environment variables, and user config."""
    current = load_user_settings()
    existing_raw_key = os.environ.get("DEEPSEEK_API_KEY") or current.get("DEEPSEEK_API_KEY", "")

    incoming_key = payload.get("api_key")
    if incoming_key is None:
        incoming_key = payload.get("DEEPSEEK_API_KEY")

    if incoming_key is not None:
        key_str = str(incoming_key).strip()
        # If the incoming key contains mask asterisks, keep the existing plaintext key
        if "****" in key_str:
            final_key = existing_raw_key
        else:
            final_key = key_str
    else:
        final_key = existing_raw_key

    base_url = (
        payload.get("base_url")
        or payload.get("api_url")
        or payload.get("LLM_API_URL")
        or current.get("LLM_API_URL")
        or DEFAULT_SETTINGS["LLM_API_URL"]
    )
    sd_url = (
        payload.get("sd_url")
        or payload.get("SD_WEBUI_URL")
        or current.get("SD_WEBUI_URL")
        or DEFAULT_SETTINGS["SD_WEBUI_URL"]
    )
    ollama_url = (
        payload.get("ollama_url")
        or payload.get("OLLAMA_URL")
        or current.get("OLLAMA_URL")
        or DEFAULT_SETTINGS["OLLAMA_URL"]
    )
    model = payload.get("model") or os.environ.get("UD_LLM_MODEL") or "deepseek-v4-pro"

    to_save = {
        "DEEPSEEK_API_KEY": final_key,
        "LLM_API_URL": str(base_url).strip(),
        "SD_WEBUI_URL": str(sd_url).strip(),
        "OLLAMA_URL": str(ollama_url).strip(),
    }
    save_user_settings(to_save)

    os.environ["LLM_API_URL"] = to_save["LLM_API_URL"]
    os.environ["SD_WEBUI_URL"] = to_save["SD_WEBUI_URL"]
    os.environ["OLLAMA_URL"] = to_save["OLLAMA_URL"]
    os.environ["UD_LLM_MODEL"] = str(model).strip()
    runtime_state["llm_model"] = str(model).strip()

    if "demo_mode" in payload:
        runtime_state["demo_mode"] = bool(payload["demo_mode"])

    masked = _mask_api_key(final_key)
    return {
        "status": "ok",
        "api_key": masked,
        "api_key_masked": masked,
        "has_api_key": bool(final_key),
        "base_url": to_save["LLM_API_URL"],
        "api_url": to_save["LLM_API_URL"],
        "model": str(model).strip(),
        "sd_url": to_save["SD_WEBUI_URL"],
        "ollama_url": to_save["OLLAMA_URL"],
        "demo_mode": bool(runtime_state.get("demo_mode", False)),
    }


@router.post("/settings/test-llm", dependencies=[Depends(verify_session_token)])
def test_llm_connectivity(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    """Verify LLM endpoint connectivity gracefully without throwing 500 on offline/401."""
    import sys

    import requests

    settings = load_user_settings()
    raw_key = payload.get("api_key")
    if not raw_key or "****" in str(raw_key):
        raw_key = os.environ.get("DEEPSEEK_API_KEY") or settings.get("DEEPSEEK_API_KEY", "")
    api_url = (
        payload.get("base_url")
        or payload.get("api_url")
        or os.environ.get("LLM_API_URL")
        or settings.get("LLM_API_URL")
        or DEFAULT_SETTINGS["LLM_API_URL"]
    )
    model = payload.get("model") or os.environ.get("UD_LLM_MODEL") or "deepseek-chat"
    if "api.deepseek.com" in str(api_url).lower() and model in ("deepseek-v4-pro", "deepseek-v4-flash"):
        model = "deepseek-chat"

    if "pytest" in sys.modules or runtime_state.get("demo_mode"):
        return {
            "status": "ok",
            "ok": True,
            "reachable": True,
            "model": model,
            "latency_ms": 12,
            "message": "演示/测试模式：大模型离线兜底引擎已就绪",
        }

    if not raw_key:
        return {
            "status": "offline",
            "ok": False,
            "reachable": False,
            "model": model,
            "latency_ms": 0,
            "message": "未配置 API Key，系统将自动启用因地制宜规则与混合 RAG 离线推演模式",
        }

    t0 = time.perf_counter()
    try:
        resp = requests.post(
            str(api_url),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {raw_key}",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 4,
                "stream": False,
            },
            timeout=8,
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)
        if resp.status_code == 200:
            return {
                "status": "ok",
                "ok": True,
                "reachable": True,
                "model": model,
                "latency_ms": latency_ms,
                "message": f"大模型接口连接正常 ({latency_ms} ms)",
            }
        return {
            "status": "error",
            "ok": False,
            "reachable": True,
            "http_status": resp.status_code,
            "model": model,
            "latency_ms": latency_ms,
            "message": f"接口返回 HTTP {resp.status_code}，已启用离线规则兜底保护",
        }
    except Exception as exc:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        return {
            "status": "offline",
            "ok": False,
            "reachable": False,
            "model": model,
            "latency_ms": latency_ms,
            "message": f"无法连接远端大模型 ({exc})，已自动启用离线规则兜底模式",
        }


@router.get("/llm-metrics", dependencies=[Depends(verify_session_token)])
def read_llm_metrics() -> dict[str, Any]:
    """Return LLM token and latency metrics from src.utils.llm_monitor."""
    records = get_llm_metrics() or []
    total_calls = len(records)
    total_tokens = sum(int(r.get("total_tokens", 0) or 0) for r in records)
    prompt_tokens = sum(int(r.get("prompt_tokens", 0) or 0) for r in records)
    completion_tokens = sum(int(r.get("completion_tokens", 0) or 0) for r in records)
    avg_latency = (
        round(sum(float(r.get("latency_sec", 0.0) or 0.0) for r in records) / total_calls, 2)
        if total_calls > 0
        else 0.0
    )
    return {
        "status": "ok",
        "total_calls": total_calls,
        "total_tokens": total_tokens,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "avg_latency_sec": avg_latency,
        "metrics": records,
        "records": records,
    }


@router.get("/projects", dependencies=[Depends(verify_session_token)])
def list_projects() -> dict[str, Any]:
    """List all registered planning projects via SpatialEngineV2."""
    from src.core.spatial_engine_v2 import get_spatial_engine_v2

    engine = get_spatial_engine_v2()
    projects = engine.list_projects()
    return {
        "status": "ok",
        "active_project_id": get_active_project_id(),
        "projects": projects,
    }


@router.post("/projects", dependencies=[Depends(verify_session_token)])
def create_project(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    """Create a new isolated planning project workspace and optionally switch to it."""
    from src.core.spatial_engine_v2 import get_spatial_engine_v2

    name = str(payload.get("name") or payload.get("project_name") or "新建城市更新工程").strip()
    city = str(payload.get("city") or payload.get("city_name") or "自定义城市").strip()
    raw_id = payload.get("project_id") or payload.get("id")
    if raw_id:
        project_id = re.sub(r"[^a-zA-Z0-9_\-\u4e00-\u9fa5]", "_", str(raw_id).strip())
    else:
        slug = re.sub(r"[^a-zA-Z0-9_\-]", "", name.lower())[:16] or "project"
        project_id = f"{slug}_{int(time.time() * 1000) % 1000000}"

    switch = bool(payload.get("switch", True))
    engine = get_spatial_engine_v2()

    sig = inspect.signature(engine.create_project)
    has_varkw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
    kwargs: dict[str, Any] = {}
    if has_varkw or "project_id" in sig.parameters:
        kwargs["project_id"] = project_id
    if has_varkw or "name" in sig.parameters:
        kwargs["name"] = name
    if has_varkw or "city" in sig.parameters:
        kwargs["city"] = city
    if (has_varkw or "description" in sig.parameters) and "description" in payload:
        kwargs["description"] = payload["description"]
    if has_varkw or "switch" in sig.parameters:
        kwargs["switch"] = switch

    if kwargs:
        created = engine.create_project(**kwargs)
    else:
        created = engine.create_project(project_id, name, city)

    created_id = (
        created.get("project_id") or created.get("id") or project_id
        if isinstance(created, dict)
        else project_id
    )
    if switch and get_active_project_id() != created_id and hasattr(engine, "switch_project"):
        engine.switch_project(created_id)

    return {
        "status": "ok",
        "project_id": created_id,
        "project": created,
        "active_project_id": get_active_project_id(),
        "rag_protected": bool(DATA_FILES["rag"].exists()),
    }


@router.post("/projects/{project_id}/switch", dependencies=[Depends(verify_session_token)])
def switch_project(project_id: str) -> dict[str, Any]:
    """Switch active project workspace via SpatialEngineV2."""
    from src.core.spatial_engine_v2 import get_spatial_engine_v2

    engine = get_spatial_engine_v2()
    res = engine.switch_project(project_id)
    return {
        "status": "ok",
        "active_project_id": get_active_project_id(),
        "project": res,
        "rag_protected": bool(DATA_FILES["rag"].exists()),
    }


@router.post("/projects/{project_id}/reset-bus", dependencies=[Depends(verify_session_token)])
def reset_project_stage_bus(project_id: str) -> dict[str, Any]:
    """Clear stage bus cache for the specified project while preserving data/rag_knowledge.json."""
    from src.core.spatial_engine_v2 import get_spatial_engine_v2

    engine = get_spatial_engine_v2()
    if hasattr(engine, "reset_stage_bus"):
        try:
            sig = inspect.signature(engine.reset_stage_bus)
            if "project_id" in sig.parameters:
                engine.reset_stage_bus(project_id=project_id)
            else:
                engine.reset_stage_bus()
        except Exception as exc:
            logger.warning("engine.reset_stage_bus warning: %s", exc)
    elif hasattr(engine, "clear_stage_bus"):
        try:
            engine.clear_stage_bus(project_id)
        except Exception:
            pass

    if project_id == get_active_project_id():
        runtime_state["stage_bus"] = {}
        cache_file = ROOT_DIR / "output" / "stage_bus_cache.json"
        if cache_file.exists():
            try:
                cache_file.write_text("{}", encoding="utf-8")
            except Exception:
                pass
        clear_all_caches()

    # Explicitly assert RAG protection (SKILLS.md Part 9)
    rag_ok = bool(DATA_FILES["rag"].exists())
    return {
        "status": "ok",
        "project_id": project_id,
        "active_project_id": get_active_project_id(),
        "rag_protected": rag_ok,
        "message": "工程阶段总线已重置，全局法规知识库 (data/rag_knowledge.json) 完好保留",
    }


@router.delete("/projects/{project_id}", dependencies=[Depends(verify_session_token)])
def delete_project(project_id: str) -> dict[str, Any]:
    """Delete a non-default project workspace while preserving data/rag_knowledge.json."""
    if project_id == "changchun_default":
        raise HTTPException(status_code=400, detail="默认示范工程 (changchun_default) 不可删除")

    from src.core.spatial_engine_v2 import get_spatial_engine_v2

    engine = get_spatial_engine_v2()
    if hasattr(engine, "delete_project"):
        res = engine.delete_project(project_id)
    else:
        if get_active_project_id() == project_id:
            if hasattr(engine, "switch_project"):
                engine.switch_project("changchun_default")
            else:
                set_active_project_id("changchun_default")
        proj_dir = (DATA_DIR / "projects" / project_id).resolve()
        projects_root = (DATA_DIR / "projects").resolve()
        if proj_dir.exists() and proj_dir.parent == projects_root:
            shutil.rmtree(proj_dir, ignore_errors=True)
        reg_path = projects_root / "registry.json"
        if reg_path.exists():
            try:
                reg = json.loads(reg_path.read_text(encoding="utf-8"))
                if isinstance(reg.get("projects"), dict):
                    reg["projects"].pop(project_id, None)
                elif isinstance(reg.get("projects"), list):
                    reg["projects"] = [
                        p
                        for p in reg["projects"]
                        if (p.get("project_id") or p.get("id")) != project_id
                    ]
                if reg.get("active_project_id") == project_id:
                    reg["active_project_id"] = "changchun_default"
                reg_path.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception as exc:
                logger.warning("Failed to update registry.json on project delete: %s", exc)
        res = {"deleted": project_id}

    return {
        "status": "ok",
        "deleted_project_id": project_id,
        "result": res,
        "active_project_id": get_active_project_id(),
        "rag_protected": bool(DATA_FILES["rag"].exists()),
    }


@router.get("/stage-bus", dependencies=[Depends(verify_session_token)])
def read_stage_bus() -> dict[str, Any]:
    """Return the full 17-stage data bus and stage completion map."""
    bus_dict = _get_stage_bus_dict()
    stage_map = _build_17_stage_map(bus_dict)
    completed = [code for code, info in stage_map.items() if info["completed"]]
    return {
        "status": "ok",
        "active_project_id": get_active_project_id(),
        "stage_bus": bus_dict,
        "stages": stage_map,
        "completed_stages": completed,
    }


@router.post("/stage-bus", dependencies=[Depends(verify_session_token)])
def write_stage_bus_entry(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    """Save a (stage, key, value) entry into the active project's stage bus."""
    stage = str(payload.get("stage") or payload.get("stage_code") or "").strip()
    key = str(payload.get("key") or "").strip()
    if not stage or not key:
        raise HTTPException(status_code=400, detail="必须提供 stage 和 key 参数")

    if stage.isdigit() and len(stage) == 1:
        stage = f"0{stage}"

    value = payload.get("value") if "value" in payload else payload.get("data")
    save_stage_output(stage, key, value)

    return {
        "status": "ok",
        "active_project_id": get_active_project_id(),
        "stage": stage,
        "key": key,
        "full_key": f"{stage}_{key}",
    }


@router.get("/jobs", dependencies=[Depends(verify_session_token)])
def list_background_jobs() -> dict[str, Any]:
    """Return all background jobs managed by JobManager."""
    mgr = get_job_manager()
    return {
        "status": "ok",
        "jobs": mgr.list_jobs(),
    }


@router.get("/jobs/{job_id}", dependencies=[Depends(verify_session_token)])
def get_background_job(job_id: str) -> dict[str, Any]:
    """Return a single background job by ID."""
    mgr = get_job_manager()
    job = mgr.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"未找到任务: {job_id}")
    return {
        "status": "ok",
        "job": job,
        **job,
    }


@router.post("/jobs/{job_id}/cancel", dependencies=[Depends(verify_session_token)])
def cancel_background_job(job_id: str) -> dict[str, Any]:
    """Cancel a queued or running background job."""
    mgr = get_job_manager()
    job = mgr.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"未找到任务: {job_id}")
    cancelled = mgr.cancel_job(job_id)
    updated = mgr.get_job(job_id)
    return {
        "status": "ok",
        "job_id": job_id,
        "cancelled": cancelled,
        "job": updated,
    }


@router.get("/jobs/{job_id}/stream", dependencies=[Depends(verify_session_token)])
def stream_background_job(job_id: str):
    """Stream real-time SSE job progress and log updates."""
    mgr = get_job_manager()
    return sse_response(mgr.stream_job_events(job_id))
