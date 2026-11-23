#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UltimateDESIGN v7.0 Industrial Desktop Executable & Installer Release Builder.

Visionary dual-body compilation pipeline (inspired by VS Code / Cursor / QGIS / ComfyUI Desktop):
  1. Builds React 19 + TypeScript + MapLibre/Deck.GL production assets (`desktop/frontend/dist`).
  2. Embeds frontend assets into `desktop/electron/frontend-dist` -> compiled into `resources/app.asar`
     served at 0ms over privileged `app://ultimatedesign/` protocol (zero browser feel).
  3. Compiles true Windows PE32+ GUI executable `release/win-unpacked/UltimateDESIGN.exe`
     (`SUBSYSTEM:WINDOWS`, zero CMD console window, single-instance lock, native menu bar,
     high-refresh / unlock-VSync FPS engine) and optional NSIS Windows Setup Installer
     `release/UltimateDESIGN-Setup-7.0.0-x64.exe`.
  4. Supports future `--compile-sidecar nuitka` C-compiled standalone `ud-sidecar.exe`
     for zero-Python / closed-source enterprise distribution while keeping data decoupled.
  5. Creates a native Windows desktop/root shortcut `UltimateDESIGN.lnk` with custom icon.

Usage:
    WinPython\\python\\python.exe tools/build_desktop_release.py --target all
    WinPython\\python\\python.exe tools/build_desktop_release.py --target dir
    WinPython\\python\\python.exe tools/build_desktop_release.py --target nsis
    WinPython\\python\\python.exe tools/build_desktop_release.py --target all --compile-sidecar nuitka
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = REPO_ROOT / "desktop" / "frontend"
FRONTEND_DIST = FRONTEND_DIR / "dist"
ELECTRON_DIR = REPO_ROOT / "desktop" / "electron"
ELECTRON_EMBEDDED_DIST = ELECTRON_DIR / "frontend-dist"
RELEASE_DIR = REPO_ROOT / "release"
ICON_ICO = ELECTRON_DIR / "build" / "icon.ico"


def _run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None, check: bool = True) -> int:
    print(f"\n[BUILD] $ {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=str(cwd), env=env or os.environ.copy(), check=False)
    if check and proc.returncode != 0:
        raise RuntimeError(f"Command failed (exit={proc.returncode}): {' '.join(cmd)}")
    return proc.returncode


def build_frontend(skip: bool = False) -> None:
    if skip and (FRONTEND_DIST / "index.html").exists():
        print("[BUILD] Skipping frontend build (--skip-frontend), using existing dist/.")
        return
    pnpm = shutil.which("pnpm") or shutil.which("pnpm.cmd")
    if not pnpm:
        raise RuntimeError("未检测到 pnpm，无法构建前端静态资源。")
    _run([pnpm, "--dir", str(FRONTEND_DIR), "build"], cwd=REPO_ROOT)
    if not (FRONTEND_DIST / "index.html").exists():
        raise RuntimeError(f"前端构建完成但未找到 {FRONTEND_DIST / 'index.html'}")


def sync_frontend_into_electron() -> None:
    if ELECTRON_EMBEDDED_DIST.exists():
        shutil.rmtree(ELECTRON_EMBEDDED_DIST)
    shutil.copytree(FRONTEND_DIST, ELECTRON_EMBEDDED_DIST)
    print(f"[BUILD] Synced frontend dist -> {ELECTRON_EMBEDDED_DIST}")


def compile_nuitka_sidecar() -> Path:
    """Optional enterprise pipeline: compile FastAPI + DuckDB sidecar into native C binary `ud-sidecar.exe`."""
    python_exe = str(REPO_ROOT / "WinPython" / "python" / "python.exe")
    if not Path(python_exe).exists():
        python_exe = sys.executable

    out_dir = RELEASE_DIR / "sidecar"
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        python_exe,
        "-m",
        "nuitka",
        "--standalone",
        "--assume-yes-for-downloads",
        "--output-filename=ud-sidecar.exe",
        f"--output-dir={out_dir}",
        "--include-package=desktop.backend",
        "--include-package=src.core",
        "--include-package=src.engines",
        "--include-package=src.workflow",
        "--include-package=src.config",
        str(REPO_ROOT / "desktop" / "backend" / "main.py"),
    ]
    _run(cmd, cwd=REPO_ROOT)
    return out_dir / "main.dist" / "ud-sidecar.exe"


def run_electron_builder(target: str) -> None:
    eb_bin = ELECTRON_DIR / "node_modules" / ".bin" / ("electron-builder.cmd" if os.name == "nt" else "electron-builder")
    if not eb_bin.exists():
        raise RuntimeError(f"未检测到 electron-builder ({eb_bin})，请先在 desktop/electron 执行 npm install。")

    env = os.environ.copy()
    env.setdefault("ELECTRON_MIRROR", "https://npmmirror.com/mirrors/electron/")
    env.setdefault(
        "ELECTRON_BUILDER_BINARIES_MIRROR",
        "https://npmmirror.com/mirrors/electron-builder-binaries/",
    )

    target_args = {
        "dir": ["--win", "dir"],
        "nsis": ["--win", "nsis"],
        "all": ["--win", "dir", "nsis"],
    }[target]

    # Note: signAndEditExecutable is configured in package.json (false avoids Windows
    # non-admin symlink extraction failure in winCodeSign while preserving full PE32+ GUI .exe + NSIS icon).
    _run([str(eb_bin), *target_args], cwd=ELECTRON_DIR, env=env)


def create_windows_shortcut(target_exe: Path, shortcut_path: Path, icon_path: Path) -> None:
    """Create a native Windows .lnk shortcut pointing straight to UltimateDESIGN.exe (zero CMD window)."""
    if os.name != "nt" or not target_exe.exists():
        return
    ps_script = (
        f'$ws = New-Object -ComObject WScript.Shell; '
        f'$sc = $ws.CreateShortcut("{shortcut_path}"); '
        f'$sc.TargetPath = "{target_exe}"; '
        f'$sc.WorkingDirectory = "{REPO_ROOT}"; '
        f'$sc.Description = "UltimateDESIGN v7.0 原生桌面工作站 (Electron + DuckDB Spatial + rustworkx)"; '
    )
    if icon_path.exists():
        ps_script += f'$sc.IconLocation = "{icon_path},0"; '
    ps_script += "$sc.Save()"
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
        check=False,
    )
    if shortcut_path.exists():
        print(f"[BUILD] Created native Windows shortcut: {shortcut_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="UltimateDESIGN v7.0 Desktop Release Compiler")
    parser.add_argument(
        "--target",
        choices=["dir", "nsis", "all"],
        default="all",
        help="打包目标: dir (绿色免安装 .exe 目录), nsis (Windows 安装向导 .exe), all (两者同时产出)",
    )
    parser.add_argument(
        "--skip-frontend",
        action="store_true",
        help="跳过前端构建，直接复用现有 desktop/frontend/dist",
    )
    parser.add_argument(
        "--compile-sidecar",
        choices=["none", "nuitka"],
        default="none",
        help="可选：将后端空间内核通过 Nuitka 编译为 C 原生独立 ud-sidecar.exe",
    )
    args = parser.parse_args()

    print("=" * 72)
    print("  UltimateDESIGN v7.0 Native Desktop Release Compiler")
    print("=" * 72)

    build_frontend(skip=args.skip_frontend)
    sync_frontend_into_electron()

    if args.compile_sidecar == "nuitka":
        compile_nuitka_sidecar()

    run_electron_builder(args.target)

    unpacked_exe = RELEASE_DIR / "win-unpacked" / "UltimateDESIGN.exe"
    if unpacked_exe.exists():
        create_windows_shortcut(unpacked_exe, REPO_ROOT / "UltimateDESIGN.lnk", ICON_ICO)

    print("\n" + "=" * 72)
    print("  [SUCCESS] UltimateDESIGN v7.0 Desktop Release Artifacts:")
    if unpacked_exe.exists():
        print(f"   - 独立可执行程序: {unpacked_exe} ({unpacked_exe.stat().st_size / 1024 / 1024:.1f} MB)")
    for setup_exe in sorted(RELEASE_DIR.glob("UltimateDESIGN-Setup-*.exe")):
        print(f"   - Windows 安装包: {setup_exe} ({setup_exe.stat().st_size / 1024 / 1024:.1f} MB)")
    root_lnk = REPO_ROOT / "UltimateDESIGN.lnk"
    if root_lnk.exists():
        print(f"   - 根目录快捷入口: {root_lnk}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
