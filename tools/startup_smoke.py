"""Minimal startup smoke checks for CI."""

import py_compile
from pathlib import Path

TARGETS = [
    "app.py",
    "pages/01_全息空间诊断与数据沙盘.py",
    "pages/02_多主体博弈与空间AIGC工坊.py",
    "pages/03_数字图则与工程交付枢纽.py",
    "src/stages/stage04_diagnosis/page.py",
    "src/stages/stage07_strategy/page.py",
    "src/stages/stage08_master_plan/page.py",
    "src/stages/stage09_systems/page.py",
    "src/stages/stage10_detail_design/page.py",
    "src/stages/stage11_implementation/page.py",
    "src/stages/stage12_guideline/page.py",
    "src/stages/stage13_outputs/page.py",
    "src/stages/stage15_aigc/page.py",
    "src/stages/stage16_skills/page.py",
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
