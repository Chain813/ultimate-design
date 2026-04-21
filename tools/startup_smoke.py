"""Minimal startup smoke checks for CI."""

from pathlib import Path
import py_compile
import sys


TARGETS = [
    "app.py",
    "pages/1_数据底座与规划策略.py",
    "pages/2_数字孪生与全息诊断.py",
    "pages/3_AIGC设计推演.py",
    "pages/4_LLM博弈决策.py",
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
