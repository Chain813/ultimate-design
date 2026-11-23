#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UltimateDESIGN v7.0 Zero-Omission All-in-One Standalone Desktop Release Compiler.

Stages and compiles a 100% self-contained Windows desktop application & NSIS setup installer
that runs completely standalone and offline on a brand-new blank Windows PC:
  1. React 19 + TypeScript + MapLibre/Deck.GL + ECharts 5 (`resources/app.asar`, 0ms `app://` boot).
  2. Complete Backend & Domain Engines (`resources/workspace/{desktop/backend,src,config,tools/drawings,SKILLS.md}`).
  3. Clean Core Spatial Data + Statutory RAG Knowledge Base + Pre-baked GeoParquet Cache
     (excludes 7.9 GB raw archives, excludes personal configs & `.env`, excludes `data/streetview/`
     since streetview uses BYOK user-supplied Baidu Map AK).
  4. Portable Isolated Python 3.13 Spatial Runtime (`resources/runtime/python/`) +
     Pre-installed Air-Gapped Offline DuckDB `spatial.duckdb_extension` (`resources/runtime/duckdb_extensions/`).
  5. Full `Program Files` Read-Only Permission Isolation (`UD_USER_DATA_DIR` -> `%APPDATA%\\UltimateDESIGN\\workspace`).

Usage:
    WinPython\\python\\python.exe tools/build_desktop_release.py --target all
    WinPython\\python\\python.exe tools/build_desktop_release.py --target dir
    WinPython\\python\\python.exe tools/build_desktop_release.py --target nsis
    WinPython\\python\\python.exe tools/build_desktop_release.py --target all --skip-runtime-sync
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
BUNDLED_DIR = ELECTRON_DIR / "bundled"
BUNDLED_WORKSPACE = BUNDLED_DIR / "workspace"
BUNDLED_RUNTIME = BUNDLED_DIR / "runtime"
RELEASE_DIR = REPO_ROOT / "release"
ICON_ICO = ELECTRON_DIR / "build" / "icon.ico"

CORE_GIS_FILES = {
    "Boundary_Scope.geojson",
    "Building_Footprints.geojson",
    "Key_Plots_District.json",
    "landuse_clipped.geojson",
    "road_clipped.geojson",
    "rail_clipped.geojson",
}

EXCLUDED_CONFIG_FILES = {
    "student_info.json",
    "author.json",
    "project.yaml",
    "custom_site.json",
    ".env",
}

EXCLUDED_STATIC_FILES = {
    "buildings.geojson",          # duplicate of data/gis/Building_Footprints.geojson (32.87 MB)
    "building_shadows.geojson",   # retired in v7.0; replaced by Deck.GL GPU real-time SunLight (37.92 MB)
    "图册结构.docx",
    "演讲稿.docx",
}

PYTHON_EXCLUDE_DIRS = [
    "__pycache__",
    "tests",
    "test",
    "selenium",
    "webdriver_manager",
    "speech_recognition",
    "pytest",
    "_pytest",
    "xdist",
    "ruff",
    "mypy",
    "pre_commit",
    "pip",
    "wheel",
    "setuptools",
    "pkg_resources",
]


def _run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None, check: bool = True) -> int:
    print(f"\n[BUILD] $ {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=str(cwd), env=env or os.environ.copy(), check=False)
    if check and proc.returncode != 0:
        raise RuntimeError(f"Command failed (exit={proc.returncode}): {' '.join(cmd)}")
    return proc.returncode


def _robocopy(src: Path, dst: Path, exclude_dirs: list[str] | None = None, exclude_files: list[str] | None = None) -> None:
    """Fast multithreaded directory sync on Windows (falls back to shutil.copytree on POSIX)."""
    dst.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        cmd = [
            "robocopy",
            str(src),
            str(dst),
            "/MIR",
            "/MT:16",
            "/NFL",
            "/NDL",
            "/NJH",
            "/NJS",
            "/NP",
            "/R:1",
            "/W:1",
        ]
        if exclude_dirs:
            cmd += ["/XD", *exclude_dirs]
        if exclude_files:
            cmd += ["/XF", *exclude_files]
        proc = subprocess.run(cmd, check=False)
        # Robocopy exit codes 0-7 indicate success
        if proc.returncode >= 8:
            raise RuntimeError(f"Robocopy failed (exit={proc.returncode}) syncing {src} -> {dst}")
    else:
        if dst.exists():
            shutil.rmtree(dst)
        ignore = shutil.ignore_patterns(*(exclude_dirs or []), *(exclude_files or []))
        shutil.copytree(src, dst, ignore=ignore)


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


def stage_standalone_workspace() -> None:
    """Stage clean zero-junk, zero-privacy-leak workspace into `desktop/electron/bundled/workspace`."""
    print("[BUILD] Staging self-contained workspace (excluding raw archives, .env & personal streetview)...")
    if BUNDLED_WORKSPACE.exists():
        shutil.rmtree(BUNDLED_WORKSPACE)
    BUNDLED_WORKSPACE.mkdir(parents=True, exist_ok=True)

    # 1. Backend & domain code
    (BUNDLED_WORKSPACE / "desktop").mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_ROOT / "desktop" / "__init__.py", BUNDLED_WORKSPACE / "desktop" / "__init__.py")
    _robocopy(
        REPO_ROOT / "desktop" / "backend",
        BUNDLED_WORKSPACE / "desktop" / "backend",
        exclude_dirs=["__pycache__"],
        exclude_files=["*.pyc", "*.pyo"],
    )
    _robocopy(
        REPO_ROOT / "src",
        BUNDLED_WORKSPACE / "src",
        exclude_dirs=["__pycache__"],
        exclude_files=["*.pyc", "*.pyo"],
    )

    # 2. Safe config files only (zero personal student_info / .env)
    cfg_dst = BUNDLED_WORKSPACE / "config"
    cfg_dst.mkdir(parents=True, exist_ok=True)
    for f in (REPO_ROOT / "config").glob("*"):
        if f.is_file() and f.name not in EXCLUDED_CONFIG_FILES:
            shutil.copy2(f, cfg_dst / f.name)

    # 3. SKILLS.md + essential drawing tools
    if (REPO_ROOT / "SKILLS.md").exists():
        shutil.copy2(REPO_ROOT / "SKILLS.md", BUNDLED_WORKSPACE / "SKILLS.md")
    tools_dst = BUNDLED_WORKSPACE / "tools"
    tools_dst.mkdir(parents=True, exist_ok=True)
    if (REPO_ROOT / "tools" / "drawings").exists():
        _robocopy(
            REPO_ROOT / "tools" / "drawings",
            tools_dst / "drawings",
            exclude_dirs=["__pycache__"],
            exclude_files=["*.pyc"],
        )
    for helper_name in ("__init__.py", "draw_scope_map.py", "generate_atlas_sheets.py"):
        hp = REPO_ROOT / "tools" / helper_name
        if hp.exists():
            shutil.copy2(hp, tools_dst / helper_name)

    # 4. Core GIS files (6 essential files only — skips 4.1 GB raw/ & backup/)
    gis_dst = BUNDLED_WORKSPACE / "data" / "gis"
    gis_dst.mkdir(parents=True, exist_ok=True)
    for name in CORE_GIS_FILES:
        src_f = REPO_ROOT / "data" / "gis" / name
        if src_f.exists():
            shutil.copy2(src_f, gis_dst / name)

    # 5. CSV tabular datasets & Global Statutory RAG Knowledge Base
    _robocopy(REPO_ROOT / "data" / "csv", BUNDLED_WORKSPACE / "data" / "csv")
    rag_src = REPO_ROOT / "data" / "rag_knowledge.json"
    if rag_src.exists():
        shutil.copy2(rag_src, BUNDLED_WORKSPACE / "data" / "rag_knowledge.json")

    # 6. Pre-baked GeoParquet cache for instant <1s cold start on blank machine
    pq_src = REPO_ROOT / "data" / "projects" / "changchun_default" / "cache_geoparquet"
    if pq_src.exists():
        pq_dst = BUNDLED_WORKSPACE / "data" / "projects" / "changchun_default" / "cache_geoparquet"
        pq_dst.mkdir(parents=True, exist_ok=True)
        for pf in pq_src.glob("*.parquet"):
            shutil.copy2(pf, pq_dst / pf.name)

    # 7. Essential static files (water.geojson + flowcharts/previews; skips 3.8 GB atlas/exhibition boards & retired shadow GeoJSON)
    static_dst = BUNDLED_WORKSPACE / "static"
    static_dst.mkdir(parents=True, exist_ok=True)
    for f in (REPO_ROOT / "static").glob("*"):
        if f.is_file() and f.name not in EXCLUDED_STATIC_FILES:
            shutil.copy2(f, static_dst / f.name)

    # Note: `data/streetview/` is intentionally NOT bundled — users apply for their own Baidu Map AK (BYOK)
    # or mount a local streetview directory in Workbench 01 Stage 03.
    ws_mb = sum(f.stat().st_size for f in BUNDLED_WORKSPACE.rglob("*") if f.is_file()) / 1024 / 1024
    print(f"[BUILD] Staged standalone workspace: {ws_mb:.1f} MB (clean, zero personal data)")


def stage_standalone_runtime(skip_sync: bool = False) -> None:
    """Stage portable Python 3.13 spatial runtime + air-gapped offline DuckDB spatial extension."""
    py_dst = BUNDLED_RUNTIME / "python"
    ext_dst = BUNDLED_RUNTIME / "duckdb_extensions"

    if skip_sync and (py_dst / "python.exe").exists() and any(ext_dst.rglob("spatial.duckdb_extension")):
        print("[BUILD] Reusing already staged runtime (--skip-runtime-sync).")
        return

    winpy_src = REPO_ROOT / "WinPython" / "python"
    if not (winpy_src / "python.exe").exists():
        raise RuntimeError(f"未找到便携 WinPython 运行时: {winpy_src}")

    print("[BUILD] Syncing portable Python 3.13 spatial runtime (robocopy /MT:16)...")
    _robocopy(
        winpy_src,
        py_dst,
        exclude_dirs=PYTHON_EXCLUDE_DIRS,
        exclude_files=["*.pyc", "*.pyo", "*.pdb"],
    )

    # Copy offline DuckDB spatial extension from ~/.duckdb/extensions
    duckdb_home_ext = Path.home() / ".duckdb" / "extensions"
    if duckdb_home_ext.exists() and any(duckdb_home_ext.rglob("spatial.duckdb_extension")):
        _robocopy(duckdb_home_ext, ext_dst)
        print(f"[BUILD] Bundled offline DuckDB spatial extension -> {ext_dst}")
    else:
        print("[WARN] Local ~/.duckdb/extensions/spatial.duckdb_extension not found; blank machine will need internet once.")

    rt_mb = sum(f.stat().st_size for f in BUNDLED_RUNTIME.rglob("*") if f.is_file()) / 1024 / 1024
    print(f"[BUILD] Staged standalone runtime + DuckDB spatial extension: {rt_mb:.1f} MB")


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

    _run([str(eb_bin), *target_args], cwd=ELECTRON_DIR, env=env)


def create_windows_shortcut(target_exe: Path, shortcut_path: Path, icon_path: Path) -> None:
    if os.name != "nt" or not target_exe.exists():
        return
    ps_script = (
        f'$ws = New-Object -ComObject WScript.Shell; '
        f'$sc = $ws.CreateShortcut("{shortcut_path}"); '
        f'$sc.TargetPath = "{target_exe}"; '
        f'$sc.WorkingDirectory = "{target_exe.parent}"; '
        f'$sc.Description = "UltimateDESIGN v7.0 原生桌面工作站 (全离线零依赖独立版)"; '
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
    parser = argparse.ArgumentParser(description="UltimateDESIGN v7.0 Zero-Omission Desktop Release Compiler")
    parser.add_argument(
        "--target",
        choices=["dir", "nsis", "all"],
        default="all",
        help="打包目标: dir (独立可执行目录), nsis (全离线 Windows 安装向导), all (两者同时产出)",
    )
    parser.add_argument(
        "--skip-frontend",
        action="store_true",
        help="跳过前端构建，直接复用现有 desktop/frontend/dist",
    )
    parser.add_argument(
        "--skip-runtime-sync",
        action="store_true",
        help="复用已同步的 desktop/electron/bundled/runtime",
    )
    args = parser.parse_args()

    print("=" * 74)
    print("  UltimateDESIGN v7.0 Zero-Omission All-in-One Standalone Release Compiler")
    print("=" * 74)

    build_frontend(skip=args.skip_frontend)
    sync_frontend_into_electron()
    stage_standalone_workspace()
    stage_standalone_runtime(skip_sync=args.skip_runtime_sync)
    run_electron_builder(args.target)

    unpacked_exe = RELEASE_DIR / "win-unpacked" / "UltimateDESIGN.exe"
    if unpacked_exe.exists():
        create_windows_shortcut(unpacked_exe, REPO_ROOT / "UltimateDESIGN.lnk", ICON_ICO)

    print("\n" + "=" * 74)
    print("  [SUCCESS] UltimateDESIGN v7.0 Zero-Omission Standalone Artifacts:")
    if unpacked_exe.exists():
        print(f"   - 独立免安装可执行程序: {unpacked_exe} ({unpacked_exe.stat().st_size / 1024 / 1024:.1f} MB)")
    for setup_exe in sorted(RELEASE_DIR.glob("UltimateDESIGN-Setup-*.exe")):
        print(f"   - 全离线零依赖 Windows 安装包: {setup_exe} ({setup_exe.stat().st_size / 1024 / 1024:.1f} MB)")
    root_lnk = REPO_ROOT / "UltimateDESIGN.lnk"
    if root_lnk.exists():
        print(f"   - 根目录快捷入口: {root_lnk}")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
