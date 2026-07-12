import logging
import re
import sys
import yaml
import pytest
from pathlib import Path
from types import SimpleNamespace

root = Path(__file__).resolve().parents[3]
if str(root) not in sys.path:
    sys.path.append(str(root))

# Mock streamlit before imports
sys.modules.setdefault("streamlit", type(sys)("streamlit_mock"))

from src.config.runtime import resolve_path
from src.config.loader import load_global_config


FIXED_KEY_PLOT_COUNT_PATTERNS = (
    re.compile(r"(?<![\d-])5\s*(?:个|大).*地块"),
    re.compile(r"五个.*地块"),
)

FIXED_KEY_PLOT_LAYOUT_PATTERNS = (
    re.compile(r"5\s*列并排布局"),
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


def test_decoupled_thesis_prompt(mock_config):
    from src.engines.thesis_composer import get_thesis_system_prompt
    prompt = get_thesis_system_prompt()
    assert "\u6d4b\u8bd5\u5e02" in prompt
    assert "\u6d4b\u8bd5\u533a" in prompt
    assert "\u6d4b\u8bd5\u5730\u5757" in prompt
    assert "\u6d4b\u8bd5\u5730\u5757\u7ea699\u516c\u9877" in prompt


def test_core_prompt_copy_does_not_assume_five_key_plots():
    files = [
        root / "src/engines/drawing_prompt_engine.py",
        root / "src/engines/drawing_prompt_templates.py",
        root / "src/workflow/template_assets.py",
        root / "src/data/data_categories.py",
        root / "src/ui/app_shell.py",
        root / "pages/00_数据准备与任务解读.py",
        root / "pages/02_资料收集与现场调研.py",
        root / "pages/13_成果表达.py",
    ]

    violations = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for pattern in FIXED_KEY_PLOT_COUNT_PATTERNS:
            if pattern.search(text):
                violations.append(f"{path.relative_to(root)} matches {pattern.pattern}")

    layout_path = root / "src/engines/drawing_prompt_templates.py"
    layout_text = layout_path.read_text(encoding="utf-8")
    for pattern in FIXED_KEY_PLOT_LAYOUT_PATTERNS:
        if pattern.search(layout_text):
            violations.append(f"{layout_path.relative_to(root)} matches {pattern.pattern}")

    assert violations == []


def test_key_plots_summary_falls_back_when_key_plot_data_unavailable(monkeypatch, caplog):
    from src.engines import key_plot_engine, spatial_data_injector

    def fail_to_load_key_plots():
        raise RuntimeError("key plot config failed")

    monkeypatch.setattr(key_plot_engine, "get_configured_key_plots", fail_to_load_key_plots)
    if hasattr(spatial_data_injector.get_key_plots_summary, "clear"):
        spatial_data_injector.get_key_plots_summary.clear()

    try:
        caplog.set_level(logging.WARNING, logger="ultimateDESIGN")

        summary = spatial_data_injector.get_key_plots_summary()

        assert summary == "重点更新单元数据暂不可用。"
        assert any(
            record.message == "Key plot summary unavailable" and record.exc_info
            for record in caplog.records
        )
    finally:
        if hasattr(spatial_data_injector.get_key_plots_summary, "clear"):
            spatial_data_injector.get_key_plots_summary.clear()


def test_batch_exporter_uses_dynamic_chapter_drawings(monkeypatch):
    from src.engines import batch_exporter

    chapter = "06 重点地段更新改造设计"
    dynamic_drawings = ["地块6街道断面图"]
    monkeypatch.setattr(batch_exporter, "get_book_chapters", lambda: {chapter: dynamic_drawings})

    generated = []
    saved = []

    class FakePipeline:
        def generate_single(self, name, mode="auto"):
            generated.append((name, mode))
            return SimpleNamespace(
                success=True,
                image=object(),
                prompt=f"prompt for {name}",
                quality_report=None,
            )

    class FakeStore:
        def get_latest(self, name):
            return None

        def save(self, name, image, metadata):
            saved.append((name, metadata))

    exporter = batch_exporter.BatchExporter(FakePipeline(), FakeStore(), drawing_names=[])

    report = exporter.export_chapter(chapter)

    assert report.total == 1
    assert report.success == 1
    assert generated == [("地块6街道断面图", "auto")]
    assert saved[0][0] == "地块6街道断面图"
    assert saved[0][1]["chapter"] == chapter


def test_batch_exporter_infers_dynamic_chapter(monkeypatch):
    from src.engines import batch_exporter

    chapter = "06 重点地段更新改造设计"
    monkeypatch.setattr(batch_exporter, "get_book_chapters", lambda: {chapter: ["地块6街道断面图"]})

    exporter = batch_exporter.BatchExporter(
        pipeline=SimpleNamespace(),
        store=SimpleNamespace(),
        drawing_names=[],
    )

    assert exporter._infer_chapter("地块6街道断面图") == chapter


def test_batch_exporter_metadata_inference_falls_back_when_dynamic_chapter_map_fails(monkeypatch, caplog):
    from src.engines import batch_exporter

    def broken_get_book_chapters():
        raise RuntimeError("broken plots")

    monkeypatch.setattr(batch_exporter, "get_book_chapters", broken_get_book_chapters)
    saved = []

    class FakePipeline:
        def generate_single(self, name, mode="auto"):
            return SimpleNamespace(
                success=True,
                image=object(),
                prompt=f"prompt for {name}",
                quality_report=None,
            )

    class FakeStore:
        def get_latest(self, name):
            return None

        def save(self, name, image, metadata):
            saved.append((name, metadata))

    caplog.set_level(logging.WARNING, logger="ultimateDESIGN")

    exporter = batch_exporter.BatchExporter(
        FakePipeline(),
        FakeStore(),
        drawing_names=["封面"],
    )
    report = exporter.export_full_atlas()

    assert report.total == 1
    assert report.success == 1
    assert report.failed == 0
    assert saved[0][0] == "封面"
    assert saved[0][1]["chapter"] in ("01 项目认知篇", "未分类")
    assert any(
        record.message == "Dynamic chapter map unavailable for metadata inference" and record.exc_info
        for record in caplog.records
    )


def test_batch_exporter_reuses_chapter_mapping_for_multiple_drawings(monkeypatch):
    from src.engines import batch_exporter

    chapter = "06 重点地段更新改造设计"
    dynamic_drawings = ["地块6街道断面图", "地块7导则索引图"]
    calls = 0

    def counted_get_book_chapters():
        nonlocal calls
        calls += 1
        return {chapter: dynamic_drawings}

    monkeypatch.setattr(batch_exporter, "get_book_chapters", counted_get_book_chapters)

    class FakePipeline:
        def generate_single(self, name, mode="auto"):
            return SimpleNamespace(
                success=True,
                image=object(),
                prompt=f"prompt for {name}",
                quality_report=None,
            )

    class FakeStore:
        def get_latest(self, name):
            return None

        def save(self, name, image, metadata):
            pass

    exporter = batch_exporter.BatchExporter(
        FakePipeline(),
        FakeStore(),
        drawing_names=dynamic_drawings,
    )

    report = exporter.export_full_atlas()

    assert report.total == 2
    assert report.success == 2
    assert calls == 1


def test_batch_exporter_explicit_empty_drawing_names_does_not_load_atlas(monkeypatch):
    from src.engines import batch_exporter

    calls = 0

    def counted_flatten_chapter_drawings():
        nonlocal calls
        calls += 1
        return ["不应加载的图纸"]

    monkeypatch.setattr(batch_exporter, "flatten_chapter_drawings", counted_flatten_chapter_drawings)

    class FakeStore:
        def get_latest(self, name):
            return object()

    exporter = batch_exporter.BatchExporter(
        pipeline=SimpleNamespace(),
        store=FakeStore(),
        drawing_names=[],
    )

    report = exporter.export_full_atlas()

    assert report.total == 0
    assert calls == 0
