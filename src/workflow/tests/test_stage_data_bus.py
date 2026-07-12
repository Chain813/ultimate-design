import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
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


def test_save_stage_summary_to_file(tmp_path):
    """save_stage_summary_to_file correctly writes and sorts stage data."""
    from unittest.mock import patch
    from src.workflow.stage_data_bus import save_stage_summary_to_file
    
    mock_file = tmp_path / "stage_generation_report.md"
    
    with patch("src.config.runtime.resolve_path", return_value=mock_file):
        # 1. 保存 Stage 02
        save_stage_summary_to_file(
            stage_code="02",
            title="资料收集",
            methodology="收集模板",
            findings=[{"point": "发现 A", "evidence": "依据 A"}],
            implication="影响 A",
            ai_summary="AI 小结 A"
        )
        
        # 2. 保存 Stage 01
        save_stage_summary_to_file(
            stage_code="01",
            title="任务解读",
            methodology="解读模版",
            findings=[{"point": "发现 B", "evidence": "依据 B"}],
            implication="影响 B",
            ai_summary="AI 小结 B"
        )
        
        # 验证文件存在并按照阶段 01 -> 02 排序
        assert mock_file.exists()
        content = mock_file.read_text(encoding="utf-8")
        
        # 验证排序与内容
        assert "Stage 01: 任务解读" in content
        assert "Stage 02: 资料收集" in content
        assert content.index("Stage 01: 任务解读") < content.index("Stage 02: 资料收集")
        assert "发现 A" in content
        assert "发现 B" in content
