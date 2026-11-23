"""FastAPI Desktop Sidecar Entrypoint for UltimateDESIGN v7.0.

Assembles all 7 domain routers, ORJSONResponse, GZip & CORS middlewares,
static directory mounts (/static, /output, /assets, and production React SPA dist),
and the optional Electron parent-process watchdog thread.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import ctypes
import logging
import os
from pathlib import Path
import threading
import time
from typing import Any

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse, ORJSONResponse
from fastapi.staticfiles import StaticFiles

from desktop.backend.deps import verify_session_token
from desktop.backend.routers import (
    copilot,
    delivery_skills,
    detail_aigc,
    diagnosis,
    site_assets,
    strategy_plan,
    system,
)
from src.config.paths import ROOT_DIR

logger = logging.getLogger("ultimateDESIGN.backend.main")


def _is_parent_alive(pid: int) -> bool:
    """Check whether parent process `pid` is still alive without sending destructive signals."""
    if pid <= 0:
        return True
    if os.name == "nt":
        try:
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not handle:
                return False
            try:
                exit_code = ctypes.c_ulong()
                if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                    return exit_code.value == STILL_ACTIVE
                return True
            finally:
                kernel32.CloseHandle(handle)
        except Exception:
            return True
    else:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False


def _start_parent_watchdog_if_configured() -> None:
    """Start a daemon thread monitoring `UD_PARENT_PID` every 3s if configured."""
    raw_pid = os.environ.get("UD_PARENT_PID", "").strip()
    if not raw_pid or not raw_pid.isdigit():
        return
    parent_pid = int(raw_pid)
    if parent_pid <= 0:
        return

    def _watchdog_loop() -> None:
        logger.info("Parent process watchdog started for PID %d", parent_pid)
        while True:
            time.sleep(3.0)
            if not _is_parent_alive(parent_pid):
                logger.warning("Parent process %d exited; terminating Python Sidecar.", parent_pid)
                os._exit(0)

    t = threading.Thread(target=_watchdog_loop, name="ud_parent_watchdog", daemon=True)
    t.start()


def _ensure_static_directories() -> None:
    """Ensure required output and static directories exist before mounting."""
    for rel in (
        "static",
        "output",
        "output/deliverables",
        "output/aigc",
        "output/aigc/previews",
        "assets",
    ):
        (ROOT_DIR / rel).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    _ensure_static_directories()
    _start_parent_watchdog_if_configured()
    yield


def create_app() -> FastAPI:
    """Create and configure the UltimateDESIGN v7.0 FastAPI Sidecar application."""
    _ensure_static_directories()

    # Suppress harmless Streamlit bare-mode ScriptRunContext warnings in FastAPI worker threads
    for _st_logger_name in (
        "streamlit.runtime.scriptrunner_utils.script_run_context",
        "streamlit.runtime.caching.cache_data_api",
        "streamlit.runtime.state.session_state_proxy",
    ):
        logging.getLogger(_st_logger_name).setLevel(logging.ERROR)

    application = FastAPI(
        title="UltimateDESIGN v7.0 Desktop Sidecar",
        description="Local High-Performance Urban Planning & Spatial Computing Desktop Sidecar API",
        version="7.0.0",
        default_response_class=JSONResponse,
        lifespan=_lifespan,
    )

    # 1. Middlewares: GZip & Loopback/Electron CORS
    application.add_middleware(GZipMiddleware, minimum_size=1024)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1",
            "http://localhost",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:4173",
            "http://localhost:4173",
            "file://",
            "null",
        ],
        allow_origin_regex=r"^(https?://(127\.0\.0\.1|localhost)(:\d+)?|app://.*|file://.*)$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-UD-Token", "Content-Disposition"],
    )

    # 2. Domain Routers (7 Routers)
    # Note: `system.router` keeps `/api/v1/system/health` public for startup health polling
    # and enforces `verify_session_token` on its other endpoints.
    application.include_router(system.router)
    application.include_router(
        site_assets.router,
        dependencies=[Depends(verify_session_token)],
    )
    application.include_router(
        diagnosis.router,
        dependencies=[Depends(verify_session_token)],
    )
    application.include_router(
        strategy_plan.router,
        dependencies=[Depends(verify_session_token)],
    )
    application.include_router(
        detail_aigc.router,
        dependencies=[Depends(verify_session_token)],
    )
    application.include_router(
        delivery_skills.router,
        dependencies=[Depends(verify_session_token)],
    )
    application.include_router(
        copilot.router,
        dependencies=[Depends(verify_session_token)],
    )

    # 3. Static Asset Directory Mounts
    static_dir = ROOT_DIR / "static"
    output_dir = ROOT_DIR / "output"
    legacy_assets_dir = ROOT_DIR / "assets"

    if static_dir.exists():
        application.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    if output_dir.exists():
        application.mount("/output", StaticFiles(directory=str(output_dir)), name="output")
    if legacy_assets_dir.exists():
        application.mount(
            "/legacy-assets",
            StaticFiles(directory=str(legacy_assets_dir)),
            name="legacy_assets",
        )

    # 4. Production Frontend SPA Hosting (if `desktop/frontend/dist` exists)
    frontend_dist = ROOT_DIR / "desktop" / "frontend" / "dist"
    frontend_index = frontend_dist / "index.html"
    if frontend_dist.exists() and frontend_index.exists():
        dist_assets = frontend_dist / "assets"
        if dist_assets.exists():
            application.mount(
                "/assets",
                StaticFiles(directory=str(dist_assets)),
                name="frontend_assets",
            )

        @application.get("/", include_in_schema=False)
        def serve_spa_root():
            return FileResponse(str(frontend_index))

        application.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend_spa")
    else:
        @application.get("/", tags=["root"])
        def root_info() -> dict[str, Any]:
            return {
                "service": "UltimateDESIGN v7.0 Desktop Sidecar",
                "version": "7.0.0",
                "status": "running",
                "health_url": "/api/v1/system/health",
                "docs_url": "/docs",
            }

    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("UD_HOST", "127.0.0.1")
    port = int(os.environ.get("UD_PORT", "8765"))
    uvicorn.run(app, host=host, port=port, log_level="info")
