import sys
import yaml
import pytest
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.append(str(root))

# Mock streamlit before imports
sys.modules.setdefault("streamlit", type(sys)("streamlit_mock"))

from src.config.runtime import resolve_path
from src.config.loader import load_global_config


@pytest.fixture(autouse=True)
def mock_spatial_data(monkeypatch):
    monkeypatch.setattr(
        "src.engines.spatial_engine.get_hud_statistics",
        lambda: {"poi_count": 10, "gvi_count": 5, "boundary_ha": 150.0},
    )
    monkeypatch.setattr(
        "src.engines.spatial_engine.get_skyline_features",
        lambda: {"building_count": 100, "max_height": 20.0, "avg_height": 10.0, "high_rise_ratio": 5.0},
    )
    monkeypatch.setattr(
        "src.engines.site_diagnostic_engine.get_plot_diagnostics",
        lambda: [],
    )



@pytest.fixture
def mock_config():
    config_path = resolve_path("config/config.yaml")
    assert config_path.exists()

    # Backup original config
    with open(config_path, "r", encoding="utf-8") as f:
        orig_content = f.read()
        orig_data = yaml.safe_load(orig_content)

    # Write mock site configuration using correct config.yaml keys
    mock_data = orig_data.copy()
    mock_data["site"] = {
        "city_name": "\u6d4b\u8bd5\u5e02",  # 测试市
        "district_name": "\u6d4b\u8bd5\u533a",  # 测试区
        "site_name": "\u6d4b\u8bd5\u5730\u5757",  # 测试地块
        "description": "\u6d4b\u8bd5\u5730\u5757\u7ea699\u516c\u9877",  # 测试地块约99公顷
        "adjacent_features": "\u6d4b\u8bd5\u5468\u8fb9",  # 测试周边
        "policies": ["\u6d4b\u8bd5\u653f\u7b56\u4e00", "\u6d4b\u8bd5\u653f\u7b56\u4e8c"]  # 测试政策一, 测试政策二
    }

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(mock_data, f, allow_unicode=True)

    # Clear cached resource loaders
    if hasattr(load_global_config, "clear"):
        load_global_config.clear()

    yield mock_data

    # Restore original config
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(orig_content)
    if hasattr(load_global_config, "clear"):
        load_global_config.clear()


def test_decoupled_guideline_prompt(mock_config):
    from src.engines.guideline_prompt import build_guideline_prompt
    prompt = build_guideline_prompt()
    assert "\u6d4b\u8bd5\u5e02" in prompt
    assert "\u6d4b\u8bd5\u533a" in prompt
    assert "\u6d4b\u8bd5\u5730\u5757" in prompt
    assert "99" in prompt


def test_decoupled_drawing_prompt(mock_config):
    from src.engines.drawing_prompt_templates import build_drawing_prompt
    prompt, sys_prompt = build_drawing_prompt("\u5468\u8fb9\u5173\u7cfb\u56fe") # 周边关系图
    # Even if missing uploaded assets, it should print out template demands containing new site name or city
    assert "\u6d4b\u8bd5" in prompt or "\u6d4b\u8bd5" in sys_prompt


def test_decoupled_report_prompt(mock_config):
    from src.engines.document_composer import get_document_system_prompt
    prompt = get_document_system_prompt()
    assert "\u6d4b\u8bd5\u5e02" in prompt
    assert "\u6d4b\u8bd5\u533a" in prompt
    assert "\u6d4b\u8bd5\u5730\u5757" in prompt
    assert "\u6d4b\u8bd5\u5730\u5757\u7ea699\u516c\u9877" in prompt
