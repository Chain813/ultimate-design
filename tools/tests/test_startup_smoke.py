"""Tests for tools/startup_smoke.py."""

from tools.startup_smoke import main, TARGETS


def test_targets_includes_all_pages():
    """TARGETS should include app.py + page files."""
    assert "app.py" in TARGETS
    assert "pages/00_数据准备与任务解读.py" in TARGETS
    assert "pages/02_资料收集与现场调研.py" in TARGETS
    assert "pages/13_成果表达.py" in TARGETS
    assert "pages/14_数据大屏.py" in TARGETS
    assert "pages/15_AIGC设计推演.py" in TARGETS
    assert "pages/16_制图与设计智能体Skill手册.py" in TARGETS
    # Total: app.py + 14 pages = 15
    assert len(TARGETS) == 15


def test_main_returns_zero():
    """All targets should compile successfully in this environment."""
    result = main()
    assert result == 0
