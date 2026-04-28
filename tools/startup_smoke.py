"""Minimal startup smoke checks for CI."""

from pathlib import Path
import py_compile
import sys


TARGETS = [
    "app.py",
    "pages/01_前期数据获取与现状分析.py",
    "pages/02_中期概念生成与应对策略.py",
    "pages/03_后期设计生成与成果表达.py",
    "pages/04_现场调研.py",
    "pages/11_数据底座与规划策略.py",
    "pages/12_现状空间全景诊断.py",
    "pages/13_AIGC设计推演.py",
    "pages/14_LLM博弈决策.py",
    "pages/15_更新设计成果展示.py",
]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    failed = []
    for target in TARGETS:
        try:
            py_compile.compile(str(root / target), doraise=True)
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
