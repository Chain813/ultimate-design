import sys
from pathlib import Path
from unittest.mock import MagicMock

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.append(str(root))
sys.modules.setdefault("streamlit", type(sys)("streamlit_mock"))

from PIL import Image
from src.engines.version_store import VersionStore
from src.engines.batch_exporter import BatchExporter, ExportReport


def test_save_creates_files(tmp_path):
    store = VersionStore(tmp_path)
    img = Image.new("RGB", (64, 64))
    version_id = store.save("区位分析图", img, {"prompt": "test", "seed": 42})
    assert version_id is not None
    assert (tmp_path / "区位分析图" / f"{version_id}.png").exists()
    assert (tmp_path / "区位分析图" / f"{version_id}.json").exists()


def test_load_returns_image_and_metadata(tmp_path):
    store = VersionStore(tmp_path)
    img = Image.new("RGB", (64, 64), color="red")
    store.save("测试图", img, {"prompt": "p"})
    loaded_img, loaded_meta = store.load("测试图")
    assert loaded_img.size == (64, 64)
    assert loaded_meta["prompt"] == "p"


def test_list_versions(tmp_path):
    store = VersionStore(tmp_path)
    img = Image.new("RGB", (64, 64))
    store.save("测试图", img, {"v": 1})
    store.save("测试图", img, {"v": 2})
    store.save("测试图", img, {"v": 3})
    versions = store.list_versions("测试图")
    assert len(versions) == 3


def test_get_latest(tmp_path):
    store = VersionStore(tmp_path)
    img = Image.new("RGB", (64, 64))
    store.save("测试图", img, {"v": 1})
    store.save("测试图", img, {"v": 2})
    _, meta = store.get_latest("测试图")
    assert meta["v"] == 2


def test_save_version_increments(tmp_path):
    store = VersionStore(tmp_path)
    img = Image.new("RGB", (64, 64))
    v1 = store.save("测试图", img, {})
    v2 = store.save("测试图", img, {})
    assert v2 > v1


def test_export_chapter(tmp_path):
    store = VersionStore(tmp_path)
    img = Image.new("RGB", (64, 64))
    store.save("区位分析图", img, {"chapter": "01 项目认知篇"})
    store.save("周边关系图", img, {"chapter": "01 项目认知篇"})
    export_dir = tmp_path / "export"
    count = store.export_chapter("01 项目认知篇", export_dir)
    assert count == 2


def test_empty_drawing_returns_none(tmp_path):
    store = VersionStore(tmp_path)
    assert store.load("不存在的图") is None


def test_export_report_fields():
    report = ExportReport(total=10, success=8, skipped=1, failed=1, errors=["t1: error"])
    assert report.total == 10
    assert report.success == 8


def test_export_full_atlas_skips_existing(tmp_path):
    store = VersionStore(tmp_path)
    img = Image.new("RGB", (64, 64))
    store.save("已有图", img, {"prompt": "p"})

    mock_pipeline = MagicMock()
    mock_pipeline.generate_with_quality_loop.return_value = MagicMock(
        success=True, prompt="p", image=img, quality_report=None
    )

    exporter = BatchExporter(mock_pipeline, store, drawing_names=["已有图", "新图"])
    report = exporter.export_full_atlas(skip_existing=True)
    assert report.skipped == 1
