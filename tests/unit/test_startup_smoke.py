"""Tests for tools/startup_smoke.py."""

from tools.startup_smoke import TARGETS, main


def test_targets_includes_all_pages():
    """TARGETS should include app.py + page files."""
    assert "app.py" in TARGETS
    assert "pages/00_数据准备与任务解读.py" in TARGETS
    assert "pages/02_资料收集与现场调研.py" in TARGETS
    assert "pages/13_成果表达.py" in TARGETS
    assert "pages/14_数据大屏.py" in TARGETS
    assert "pages/15_AIGC设计推演.py" in TARGETS
    assert "pages/16_制图与设计智能体Skill手册.py" in TARGETS
    assert "pages/01_全息空间诊断与数据沙盘.py" in TARGETS
    assert "pages/02_多主体博弈与空间AIGC工坊.py" in TARGETS
    assert "pages/03_数字图则与工程交付枢纽.py" in TARGETS
    # Total: app.py + 14 legacy pages + 3 unified workbenches = 18
    assert len(TARGETS) == 18


def test_main_returns_zero():
    """All targets should compile successfully in this environment."""
    result = main()
    assert result == 0
