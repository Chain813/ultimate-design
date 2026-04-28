"""Minimal startup smoke checks for CI."""

from pathlib import Path
import py_compile
import sys


TARGETS = [
    "app.py",
    "pages/01_任务解读.py",
    "pages/02_资料收集.py",
    "pages/03_现场调研.py",
    "pages/04_现状分析.py",
    "pages/05_问题诊断.py",
    "pages/06_目标定位.py",
    "pages/07_设计策略.py",
    "pages/08_总体城市设计.py",
    "pages/09_专项系统设计.py",
    "pages/10_重点地段深化.py",
    "pages/11_实施路径.py",
    "pages/12_城市设计导则.py",
    "pages/13_成果表达.py",
]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    failed = []
    for target in TARGETS:
        target_path = root / target
        if not target_path.exists():
            failed.append((target, "File does not exist"))
            continue
        try:
            py_compile.compile(str(target_path), doraise=True)
        except Exception as exc:  # pragma: no cover - smoke diagnostics
            failed.append((target, str(exc)))

    if failed:
        print("[ERROR] Startup smoke check failed:")
        for target, message in failed:
            print(f" - {target}: {message}")
        return 1

    print("[OK] Startup smoke check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
