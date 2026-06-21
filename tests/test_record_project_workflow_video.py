from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "tools" / "record_project_workflow_video.py"
    spec = importlib.util.spec_from_file_location("record_project_workflow_video", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_recording_script_targets_optimized_dynamic_video():
    module = _load_module()

    assert module.OUT_DIR.name == "live_recording_optimized"
    assert hasattr(module, "_prewarm_project")
    assert hasattr(module, "_wait_for_page_stable")
    assert hasattr(module, "_smooth_scroll_to_bottom")

    scenes = {str(scene["code"]): scene for scene in module.SCENES}
    assert int(scenes["00"]["seconds"]) >= 60
    assert "多主体协同推演" in str(scenes["05"]["route"])
    assert int(scenes["05"]["seconds"]) >= 90

    total_seconds = sum(int(scene["seconds"]) for scene in module.SCENES)
    assert 300 <= total_seconds <= 600
