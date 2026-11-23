#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UltimateDESIGN v7.0 Desktop Studio Portable Launcher (`run_desktop.py`)
Supports:
  - Native Electron Desktop mode (default when Electron binary is installed)
  - Direct FastAPI + Uvicorn Server mode (`--server-only` or `--web` or fallback)
Strictly portable: zero hardcoded personal paths.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = REPO_ROOT / "desktop" / "frontend"
FRONTEND_DIST_INDEX = FRONTEND_DIR / "dist" / "index.html"
ELECTRON_DIR = REPO_ROOT / "desktop" / "electron"


def discover_python_executable() -> str:
    """Discover portable WinPython first, then current sys.executable."""
    win_py = REPO_ROOT / "WinPython" / "python" / "python.exe"
    if win_py.exists():
        return str(win_py)
    env_py = os.environ.get("UD_PYTHON_PATH")
    if env_py and Path(env_py).exists():
        return env_py
    return sys.executable or "python"


def ensure_frontend_dist(force_build: bool = False) -> bool:
    """Ensure `desktop/frontend/dist/index.html` exists; build via pnpm if missing."""
    if FRONTEND_DIST_INDEX.exists() and not force_build:
        return True

    pnpm_bin = shutil.which("pnpm")
    if not pnpm_bin:
        print(
            "[WARN] 未检测到 pnpm，跳过前端自动构建。若 dist 已存在将直接使用现有静态包。",
            file=sys.stderr,
        )
        return FRONTEND_DIST_INDEX.exists()

    if not (FRONTEND_DIR / "node_modules").exists():
        print("[INFO] 正在安装前端依赖 (pnpm --dir desktop/frontend install)...")
        subprocess.run(
            [
                pnpm_bin,
                "--dir",
                str(FRONTEND_DIR),
                "--config.strict-dep-builds=false",
                "install",
            ],
            cwd=str(REPO_ROOT),
            check=False,
        )

    print("[INFO] 正在构建前端静态产物 (pnpm --dir desktop/frontend build)...")
    res = subprocess.run(
        [
            pnpm_bin,
            "--dir",
            str(FRONTEND_DIR),
            "--config.strict-dep-builds=false",
            "--verify-deps-before-run=false",
            "build",
        ],
        cwd=str(REPO_ROOT),
        check=False,
    )
    return res.returncode == 0 and FRONTEND_DIST_INDEX.exists()


def discover_electron_binary() -> str | None:
    """Locate local or global Electron executable."""
    if os.name == "nt":
        local_cmd = ELECTRON_DIR / "node_modules" / ".bin" / "electron.cmd"
        if local_cmd.exists():
            return str(local_cmd)
        root_cmd = REPO_ROOT / "node_modules" / ".bin" / "electron.cmd"
        if root_cmd.exists():
            return str(root_cmd)
    else:
        local_bin = ELECTRON_DIR / "node_modules" / ".bin" / "electron"
        if local_bin.exists():
            return str(local_bin)
        root_bin = REPO_ROOT / "node_modules" / ".bin" / "electron"
        if root_bin.exists():
            return str(root_bin)

    global_electron = shutil.which("electron")
    return global_electron


def run_server_only(host: str, port: int) -> int:
    """Launch FastAPI + DuckDB Spatial sidecar directly on host:port."""
    python_exe = discover_python_executable()
    env = os.environ.copy()
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["PYTHONPATH"] = str(REPO_ROOT)

    url = f"http://{host}:{port}/"
    print("=" * 68)
    print("  UltimateDESIGN v7.0 Desktop Studio (FastAPI + DuckDB Spatial Engine)")
    print(f"  本地工作站地址: {url}")
    print(f"  API 健康检查:   {url}api/v1/system/health")
    print("=" * 68)

    cmd = [
        python_exe,
        "-m",
        "uvicorn",
        "desktop.backend.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    return subprocess.call(cmd, cwd=str(REPO_ROOT), env=env)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="UltimateDESIGN v7.0 Desktop Studio Launcher"
    )
    parser.add_argument(
        "--server-only",
        action="store_true",
        help="仅启动 FastAPI + Uvicorn 后端与内置前端服务 (默认端口 8765)",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="等同于 --server-only，通过本地端口 8765 提供桌面工作站服务",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="本地绑定地址 (默认 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="服务端口 (默认 8765)",
    )
    parser.add_argument(
        "--rebuild-frontend",
        action="store_true",
        help="启动前强制重新执行 pnpm build",
    )
    args = parser.parse_args()

    os.environ["PYTHONNOUSERSITE"] = "1"
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONPATH"] = str(REPO_ROOT)

    ensure_frontend_dist(force_build=args.rebuild_frontend)

    if args.server_only or args.web:
        return run_server_only(args.host, args.port)

    compiled_exe = REPO_ROOT / "release" / "win-unpacked" / "UltimateDESIGN.exe"
    if os.name == "nt" and compiled_exe.exists() and not args.rebuild_frontend:
        print(f"[INFO] 检测到已编译独立桌面可执行程序 ({compiled_exe})，直接启动原生 GUI 进程...")
        env = os.environ.copy()
        env["UD_WORKSPACE_ROOT"] = str(REPO_ROOT)
        subprocess.Popen([str(compiled_exe)], cwd=str(REPO_ROOT), env=env)
        return 0

    electron_bin = discover_electron_binary()
    if electron_bin:
        print(f"[INFO] 检测到 Electron 原生壳层 ({electron_bin})，正在启动桌面工作站...")
        env = os.environ.copy()
        env["PYTHONNOUSERSITE"] = "1"
        env["PYTHONUTF8"] = "1"
        env["PYTHONPATH"] = str(REPO_ROOT)
        env["UD_PYTHON_PATH"] = discover_python_executable()
        return subprocess.call([electron_bin, str(ELECTRON_DIR)], cwd=str(REPO_ROOT), env=env)

    print("[INFO] 未检测到本地 Electron 二进制包，自动切换为本地高性能服务模式 (127.0.0.1:8765)...")
    return run_server_only(args.host, args.port)


if __name__ == "__main__":
    raise SystemExit(main())
