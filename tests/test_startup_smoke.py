"""Tests for tools/startup_smoke.py."""

from tools.startup_smoke import main, TARGETS


def test_targets_includes_all_pages():
    """TARGETS should include app.py + page files."""
    assert "app.py" in TARGETS
    assert "pages/00_数据准备与任务解读.py" in TARGETS
    assert "pages/02_资料收集与现场调研.py" in TARGETS
    assert "pages/13_成果表达.py" in TARGETS
    assert "pages/14_视频生成.py" in TARGETS
    # Total: app.py + 12 pages = 13
    assert len(TARGETS) == 13


def test_main_returns_zero():
    """All targets should compile successfully in this environment."""
    result = main()
    assert result == 0
