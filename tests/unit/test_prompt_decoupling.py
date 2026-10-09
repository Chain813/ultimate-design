import sys
from pathlib import Path

import pytest
import yaml

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.append(str(root))

# Mock streamlit before imports
sys.modules.setdefault("streamlit", type(sys)("streamlit_mock"))

from src.config.loader import load_global_config
from src.config.runtime import resolve_path


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
def mock_config(monkeypatch):
    import copy
    orig_data = copy.deepcopy(load_global_config())
    mock_data = copy.deepcopy(orig_data)
    mock_data["site"] = {
        "city_name": "测试市",
        "district_name": "测试区",
        "site_name": "测试地块",
        "description": "测试地块约99公顷",
        "adjacent_features": "测试周边",
        "policies": ["测试政策一", "测试政策二"],
    }

    monkeypatch.setattr("src.config.loader.load_global_config", lambda: mock_data)
    monkeypatch.setattr("src.config.site.load_global_config", lambda: mock_data)
    monkeypatch.setattr("src.config.site._load_project_yaml", lambda: {})
    yield mock_data


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
