import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.append(str(root))
sys.modules.setdefault("streamlit", type(sys)("streamlit_mock"))

from src.workflow.stage_data_bus import save_stage_output, load_stage_output, stage_ready, list_completed_stages


def test_save_and_load():
    """save_stage_output stores data that load_stage_output can retrieve."""
    save_stage_output("test", "key1", "value1")
    assert load_stage_output("test", "key1") == "value1"


def test_load_default():
    """load_stage_output returns default for missing keys."""
    assert load_stage_output("test", "nonexistent", "default") == "default"


def test_stage_ready():
    """stage_ready returns True after saving."""
    save_stage_output("test", "ready_key", 42)
    assert stage_ready("test", "ready_key") is True
    assert stage_ready("test", "missing_key") is False


def test_list_completed_stages():
    """list_completed_stages returns sorted stage codes."""
    save_stage_output("99", "test", True)
    stages = list_completed_stages()
    assert "99" in stages
