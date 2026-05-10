"""Tests for tools/startup_smoke.py."""

from tools.startup_smoke import main, TARGETS


def test_targets_includes_all_15_pages():
    """TARGETS should include app.py + 15 page files (00 through 14)."""
    assert "app.py" in TARGETS
    assert "pages/00_数据准备.py" in TARGETS
    assert "pages/01_任务解读.py" in TARGETS
    assert "pages/13_成果表达.py" in TARGETS
    assert "pages/14_视频生成.py" in TARGETS
    # Total: app.py + 15 pages = 16
    assert len(TARGETS) == 16


def test_main_returns_zero():
    """All targets should compile successfully in this environment."""
    result = main()
    assert result == 0
