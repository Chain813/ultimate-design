"""单元测试：工作台 1 任意地块自由量化诊断、动态痛点画像生成与靶向地块选定。"""

import pytest

from src.stages.stage04_diagnosis.page import select_target_plot_and_diagnose
from src.ui.site_ingestion_panel import (
    get_active_candidate_plots,
    parse_plots_from_geojson,
    parse_site_geometry_from_geojson,
)
from src.workflow.stage_data_bus import load_stage_output, save_stage_output


def test_user_can_select_any_plot_as_target():
    """验证无论传入何种地块（如'市一中北侧'），系统均能自动推导其痛点并存入总线。"""
    plot = select_target_plot_and_diagnose(
        plot_name="市一中北侧",
        land_use="科教文卫用地",
        mpi_score=78.2,
        area_ha=2.78,
    )

    assert plot["name"] == "市一中北侧"
    assert plot["land_use"] == "科教文卫用地"
    assert plot["mpi"] == 78.2
    assert plot["priority"] == "P2 协同更新"
    assert isinstance(plot["issues"], list)
    assert len(plot["issues"]) >= 3
    assert "metrics" in plot

    # 验证 StageDataBus 中正确保存
    saved_04 = load_stage_output("04", "target_plot")
    saved_05 = load_stage_output("05", "target_plot")
    assert saved_04 is not None
    assert saved_04["name"] == "市一中北侧"
    assert saved_04["mpi"] == 78.2
    assert saved_05["name"] == "市一中北侧"


def test_select_industrial_plot_derives_industrial_issues():
    """验证工业用地能精准动态推导出产业转型/厂房闲置与绿化痛点。"""
    plot = select_target_plot_and_diagnose(
        plot_name="老铸造车间",
        land_use="工业用地",
        mpi_score=88.5,
        area_ha=3.5,
        metrics={"gvi": 8.0, "poi": 5, "svf": 0.45},
    )

    assert plot["name"] == "老铸造车间"
    assert plot["priority"] == "P1 优先更新"
    issues = plot["issues"]
    assert any("闲置" in s or "工业" in s or "转型" in s or "厂房" in s for s in issues)
    assert any("绿化" in s or "绿视率" in s for s in issues)


def test_select_residential_plot_derives_aging_and_safety_issues():
    """验证居住用地能动态推断出适老配套、老旧管网设施及停车通道隐患。"""
    plot = select_target_plot_and_diagnose(
        plot_name="朝阳南里新村",
        land_use="二类居住用地",
        mpi_score=72.0,
        area_ha=4.2,
        metrics={"gvi": 12.0, "poi": 7, "svf": 0.50},
    )

    assert plot["name"] == "朝阳南里新村"
    issues = plot["issues"]
    assert any("老龄化" in s or "适老" in s or "住区" in s or "老化" in s or "停车" in s for s in issues)


def test_target_plot_structure_conforms_to_full_spec():
    """验证保存的靶向地块数据结构严格包含 7 项要素。"""
    plot = select_target_plot_and_diagnose(
        plot_name="武汉汉阳铁厂核心区",
        land_use="工业/文创用地",
        mpi_score=91.4,
        area_ha=12.5,
        metrics={"gvi": 16.0, "poi": 12, "svf": 0.55, "clutter": 35.0},
    )

    required_keys = {"name", "land_use", "area_ha", "mpi", "priority", "issues", "metrics"}
    assert required_keys.issubset(set(plot.keys()))
    assert plot["metrics"]["gvi"] == 16.0
    assert plot["metrics"]["poi"] == 12
    assert plot["area_ha"] == 12.5
    assert plot["priority"] == "P1 优先更新"


def test_candidate_plots_loading_from_geojson():
    """验证从任意 GeoJSON 动态解析候选地块，不依赖任何写死模板。"""
    sample_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "自定义创新园A区", "land_use": "商业商办", "Shape_Area": 50000},
                "geometry": {"type": "Polygon", "coordinates": [[[114.3, 30.5], [114.31, 30.5], [114.31, 30.51], [114.3, 30.5]]]}
            },
            {
                "type": "Feature",
                "properties": {"name": "老厂生活区B区", "land_use": "居住用地", "Shape_Area": 80000},
                "geometry": {"type": "Polygon", "coordinates": [[[114.31, 30.5], [114.32, 30.5], [114.32, 30.51], [114.31, 30.5]]]}
            }
        ]
    }

    parsed_plots = parse_plots_from_geojson(sample_geojson)
    assert len(parsed_plots) == 2
    assert parsed_plots[0]["name"] == "自定义创新园A区"
    assert parsed_plots[0]["area_ha"] == 5.0
    assert parsed_plots[1]["name"] == "老厂生活区B区"
    assert parsed_plots[1]["area_ha"] == 8.0

    site_info = parse_site_geometry_from_geojson(sample_geojson, city="武汉", name="汉阳铁厂工程")
    assert site_info["city"] == "武汉"
    assert site_info["name"] == "汉阳铁厂工程"
    assert site_info["feature_count"] == 2
