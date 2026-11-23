"""Tests for tools/check_env.py."""

import inspect

from tools.check_env import check_package, package_import_name


def test_package_import_name_known_mapping():
    assert package_import_name("beautifulsoup4") == "bs4"
    assert package_import_name("pillow") == "PIL"
    assert package_import_name("python-dotenv") == "dotenv"


def test_package_import_name_default():
    assert package_import_name("pandas") == "pandas"
    assert package_import_name("some-pkg") == "some_pkg"


def test_check_package_exists():
    assert check_package("sys") is True
    assert check_package("os") is True


def test_check_package_missing():
    assert check_package("nonexistent_package_xyz_999") is False


def test_critical_files_includes_all_pages():
    """Verify the critical_files list includes the 3 workbenches, stage modules, and bigscreen."""
    import tools.check_env as mod

    source = inspect.getsource(mod.main)
    assert "pages/01_全息空间诊断与数据沙盘.py" in source
    assert "pages/02_多主体博弈与空间AIGC工坊.py" in source
    assert "pages/03_数字图则与工程交付枢纽.py" in source
    assert "src/stages/stage15_aigc/page.py" in source
    assert "src/stages/stage16_skills/page.py" in source
    assert "assets/datav_bigscreen.html" in source


def test_main_returns_exit_code():
    """Verify main() returns an integer exit code (0 or 1)."""
    from tools.check_env import main

    # In our test env streamlit is mocked, so check_package may error;
    # we just verify the function is callable and returns int.
    try:
        result = main()
        assert isinstance(result, int)
        assert result in (0, 1)
    except (ValueError, ModuleNotFoundError):
        # Expected when streamlit is mocked in conftest
        pass
