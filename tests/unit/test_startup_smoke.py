"""Tests for tools/startup_smoke.py."""

from tools.startup_smoke import TARGETS, main


def test_targets_includes_all_pages():
    """TARGETS should include app.py + 3 workbenches + 10 stage modules (14 total)."""
    assert "app.py" in TARGETS
    assert "pages/01_全息空间诊断与数据沙盘.py" in TARGETS
    assert "pages/02_多主体博弈与空间AIGC工坊.py" in TARGETS
    assert "pages/03_数字图则与工程交付枢纽.py" in TARGETS
    assert "src/stages/stage04_diagnosis/page.py" in TARGETS
    assert "src/stages/stage07_strategy/page.py" in TARGETS
    assert "src/stages/stage08_master_plan/page.py" in TARGETS
    assert "src/stages/stage09_systems/page.py" in TARGETS
    assert "src/stages/stage10_detail_design/page.py" in TARGETS
    assert "src/stages/stage11_implementation/page.py" in TARGETS
    assert "src/stages/stage12_guideline/page.py" in TARGETS
    assert "src/stages/stage13_outputs/page.py" in TARGETS
    assert "src/stages/stage15_aigc/page.py" in TARGETS
    assert "src/stages/stage16_skills/page.py" in TARGETS
    assert len(TARGETS) == 14


def test_main_returns_zero():
    """All targets should compile successfully in this environment."""
    result = main()
    assert result == 0
