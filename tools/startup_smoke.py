"""Minimal startup smoke checks for CI."""

import py_compile
from pathlib import Path

TARGETS = [
    "app.py",
    "pages/01_全息空间诊断与数据沙盘.py",
    "pages/02_多主体博弈与空间AIGC工坊.py",
    "pages/03_数字图则与工程交付枢纽.py",
    "src/legacy_pages/00_数据准备与任务解读.py",
    "src/legacy_pages/02_资料收集与现场调研.py",
    "src/legacy_pages/04_现状分析与问题诊断.py",
    "src/legacy_pages/06_目标定位.py",
    "src/legacy_pages/07_设计策略.py",
    "src/legacy_pages/08_总体城市设计.py",
    "src/legacy_pages/09_专项系统设计.py",
    "src/legacy_pages/10_重点地段深化.py",
    "src/legacy_pages/11_实施路径.py",
    "src/legacy_pages/12_城市设计导则.py",
    "src/legacy_pages/13_成果表达.py",
    "src/legacy_pages/14_数据大屏.py",
    "src/legacy_pages/15_AIGC设计推演.py",
    "src/legacy_pages/16_制图与设计智能体Skill手册.py",
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
