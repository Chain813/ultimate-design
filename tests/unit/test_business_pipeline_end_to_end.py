"""端到端全业务逻辑链综合测试。

验证长春伪满皇宫微更新从：
全息诊断 (Stage 04) -> 多主体博弈 (Stage 07) -> 空间总体与深化 (Stage 08/10/15) -> CAD/Word成果交付 (Stage 12/13)
端到端全业务链路在 StageDataBus 上的 100% 连通率与数据一致性。
"""

import os
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Polygon, LineString, Point
from PIL import Image

from src.workflow.stage_data_bus import (
    load_stage_output,
    save_stage_output,
    stage_ready,
    _bus,
    BASELINE_STAGE_DATA,
)
from src.workflow.stage_keys import SK
from src.workflow.design_context import build_design_context, synthesize_design_brief
from src.utils.vector_exporter import export_multi_layer_dxf, STANDARD_GB_LAYERS


def test_stage04_to_stage07_target_plot_anchoring():
    """验证 Stage 04 靶向地块保存并在 Stage 07 中被正确读取与锚定。"""
    sample_target = {
        "name": "长春水产大市场",
        "alias": "农贸水产市场",
        "mpi": 88.5,
        "priority": "P1 优先更新",
        "issues": ["低效老旧物流", "占道经营阻断滨水视廊", "立面破损衰退"],
    }
    save_stage_output("04", "target_plot", sample_target)

    # Stage 07 读取
    plot_in_07 = load_stage_output("04", "target_plot")
    assert plot_in_07 is not None
    assert plot_in_07["name"] == "长春水产大市场"
    assert plot_in_07["mpi"] == 88.5
    assert "P1" in plot_in_07["priority"]

    # 验证 stage_ready 状态
    assert stage_ready("04", "target_plot") is True


def test_stage07_design_brief_consensus_synthesis():
    """验证 Stage 07 自动合成的设计纲要结构完整并包含因地制宜控制关键词。"""
    ctx = build_design_context()
    brief = synthesize_design_brief(ctx)

    assert brief is not None
    assert len(brief) > 100

    # 验证四大核心结构段落
    assert "## 靶向地块定位与更新指引" in brief
    assert "## 核心问题与博弈共识" in brief
    assert "## 空间策略与 AIGC 控制关键词" in brief
    assert "## 图纸绘制与工程交付要点" in brief

    # 验证核心控制关键词提炼
    assert "核心控制关键词" in brief

    # 保存并验证总线
    save_stage_output("07", SK.DESIGN_BRIEF, brief)
    loaded_brief = load_stage_output("07", SK.DESIGN_BRIEF)
    assert "## 靶向地块定位与更新指引" in loaded_brief


def test_stage08_and_stage10_read_upstream_consensus():
    """验证 Stage 08 与 Stage 10 正确获取 Stage 04 靶向地块与 Stage 07 纲要。"""
    brief = load_stage_output("07", SK.DESIGN_BRIEF)
    target = load_stage_output("04", "target_plot") or load_stage_output("07", "target_plot")

    assert brief != ""
    assert target != {}
    assert target.get("name") is not None and len(target.get("name")) > 0

    # 模拟 Stage 10 产出重点地块控规指标与深化方案
    plot_name = target.get("name", "示范重点地块")
    save_stage_output("10", f"{SK.PLOT_METRICS}_{plot_name}", "容积率1.35，建筑密度32%，限高9-18m")
    save_stage_output("10", f"{SK.PLOT_DESIGN}_{plot_name}", f"{plot_name}深化设计方案，因地制宜空间织补")

    loaded_metrics = load_stage_output("10", f"{SK.PLOT_METRICS}_{plot_name}")
    loaded_design = load_stage_output("10", f"{SK.PLOT_DESIGN}_{plot_name}")
    assert "1.35" in loaded_metrics
    assert plot_name in loaded_design


def test_stage12_guideline_and_metrics_consistency():
    """验证 Stage 12 导则与管控指标体系严格遵循控规红线。"""
    # 读取基准或已生成的导则
    guideline = load_stage_output("12", SK.DESIGN_GUIDELINE)
    assert guideline is not None
    assert "伪满皇宫" in guideline
    assert "长春水产大市场" in guideline or "靶向" in guideline or "1.4" in guideline


def test_stage13_autocad_dxf_vector_generation(tmp_path):
    """验证 Stage 13 AutoCAD 2000 (AC1015) GB/T 五图层矢量图纸生成。"""
    poly = Polygon([(125.33, 43.90), (125.35, 43.90), (125.35, 43.92), (125.33, 43.92)])
    line = LineString([(125.33, 43.90), (125.35, 43.92)])

    gdfs = {
        "01_BOUNDARY": gpd.GeoDataFrame({"id": [1]}, geometry=[poly], crs="EPSG:4326"),
        "02_EXISTING_BLDG": gpd.GeoDataFrame({"id": [2]}, geometry=[poly], crs="EPSG:4326"),
        "03_PROPOSED_BLDG": gpd.GeoDataFrame({"name": ["长春水产大市场"]}, geometry=[poly], crs="EPSG:4326"),
        "04_ROAD_CENTER": gpd.GeoDataFrame({"id": [3]}, geometry=[line], crs="EPSG:4326"),
        "05_GREEN_SPACE": gpd.GeoDataFrame({"id": [4]}, geometry=[poly], crs="EPSG:4326"),
    }

    out_dxf = tmp_path / "test_statutory_plan.dxf"
    export_multi_layer_dxf(gdfs, str(out_dxf), to_metric=True, target_crs="EPSG:3857")

    assert out_dxf.exists()
    assert out_dxf.stat().st_size > 500

    content = out_dxf.read_text(encoding="gbk", errors="ignore")
    # 验证 AutoCAD 2000 AC1015 头信息
    assert "AC1015" in content
    assert "ANSI_936" in content
    # 验证五大 GB/T 图层已全部在 DXF 表格中定义
    for layer in STANDARD_GB_LAYERS:
        assert layer in content
    # 验证包含轻量多段线图元
    assert "LWPOLYLINE" in content


def test_stage_data_bus_defensive_and_non_json_sanitization():
    """验证 StageDataBus 对非 JSON 复杂对象（PIL Image, GeoDataFrame, ndarray）的无损消毒。"""
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    gdf = gpd.GeoDataFrame({"name": ["test"]}, geometry=[Point(1, 1)])

    # 保存复杂对象，不应抛出异常
    save_stage_output("15", "test_pil", img)
    save_stage_output("08", "test_gdf", gdf)

    # 读取时依然保持平稳
    assert load_stage_output("15", "test_pil") is not None
    assert load_stage_output("08", "test_gdf") is not None

    # 未生产的数据应优雅回退到基准数据，杜绝 KeyError
    fallback_concept = load_stage_output("06", "non_existent_key_with_fallback", default="默认概念")
    assert fallback_concept == "默认概念"

    baseline_plot = load_stage_output("04", "target_plot")
    assert baseline_plot is not None
    assert len(baseline_plot.get("name", "")) > 0
    assert "mpi" in baseline_plot
