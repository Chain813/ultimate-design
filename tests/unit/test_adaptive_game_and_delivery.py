"""单元测试：因地制宜场景自生式多主体博弈决策、自适应 AIGC 生形与全球 UTM 投影 CAD 交付。"""

import os
import tempfile
import pytest
import geopandas as gpd
from shapely.geometry import Polygon

from src.engines.context_adaptive_engine import (
    generate_adaptive_aigc_prompt,
    generate_adaptive_personas,
    get_utm_epsg_for_coordinates,
    infer_plot_diagnostics,
)
from src.workflow.design_context import DesignContext, synthesize_design_brief
from src.utils.vector_exporter import export_multi_layer_dxf, project_gdf_to_metric


def test_adaptive_personas_industrial_heritage():
    """测试工业遗存地块自生衍生工业职工、创客运营与环保监管角色，无写死台词。"""
    site = {"city": "武汉市", "name": "汉阳铁厂工业遗存"}
    plot = {
        "name": "一号高炉车间",
        "land_use": "工业/仓储用地",
        "area_ha": 6.8,
        "issues": ["大跨度厂房闲置低效", "工业废弃地环境待修复"],
    }
    personas = generate_adaptive_personas(site, plot)
    assert len(personas) == 3

    p_titles = [p["role_title"] for p in personas]
    assert any("工人" in t or "职工" in t or "使用者" in t for t in p_titles)
    assert any("运营" in t or "企业" in t or "创客" in t for t in p_titles)
    assert any("规划" in t or "监管" in t or "保护" in t for t in p_titles)

    # 验证提示词与诉求绑定在工业地块上，绝不出现长春水产市场
    all_text = " ".join(p["system_prompt"] + p["core_demands"] for p in personas)
    assert "水产大市场" not in all_text
    assert "一号高炉车间" in all_text


def test_adaptive_personas_residential_aging():
    """测试老旧小区地块自生衍生银发老龄居民、物业服务与基层规划治理主体。"""
    site = {"city": "北京市", "name": "朝阳南里老旧小区"}
    plot = {
        "name": "朝阳南里三区",
        "land_use": "居住用地",
        "area_ha": 4.5,
        "issues": ["适老化设施严重匮乏", "微循环道路人车混行", "室外口袋绿地不足"],
    }
    personas = generate_adaptive_personas(site, plot)
    assert len(personas) == 3

    all_text = " ".join(p["system_prompt"] + p["core_demands"] for p in personas)
    assert "朝阳南里三区" in all_text
    assert any(w in all_text for w in ["老龄", "适老", "居民", "无障碍"])


def test_synthesize_design_brief_is_dynamic():
    """测试设计纲要合成根据靶向地块动态生成，不退回静态长春水产模板。"""
    ctx = DesignContext()
    ctx.target_plot = {
        "name": "成都锦江滨水文创街区",
        "land_use": "商业与公共服务用地",
        "mpi": 89.2,
        "priority": "P1 优先更新",
        "far_max": 1.8,
        "height_max": 24.0,
        "density_max": 40.0,
        "green_min": 30.0,
        "issues": ["夜间活力不足", "沿河慢行绿道断点", "缺乏公共休憩口袋公园"],
    }
    ctx.diagnosis_report = "锦江东岸公共开敞空间断链，缺少适老适幼活动设施。"
    ctx.negotiation_result = "居民要求贯通滨江绿道并增设茶座；运营商同意配建文创步道以换取首层轻餐饮经营权；规划师要求限高24m确保锦江生态廊道开敞度。"

    brief = synthesize_design_brief(ctx)
    assert "成都锦江滨水文创街区" in brief
    assert "水产大市场" not in brief
    assert "89.2" in brief
    assert "## 靶向地块定位与更新指引" in brief
    assert "## 核心问题与博弈共识" in brief


def test_adaptive_aigc_prompt_regional_climate():
    """测试根据南方广州经纬度自适应提取岭南湿热气候与遮阳通风特征。"""
    site_gz = {"city": "广州市", "center": [113.26, 23.13]}
    plot_gz = {"name": "荔湾骑楼历史街区", "land_use": "商业用地"}
    aigc_res = generate_adaptive_aigc_prompt(site_gz, plot_gz, consensus={"keywords": ["岭南特色骑楼", "立体通风冷巷"]})

    prompt_text = aigc_res["prompt"]
    assert "荔湾骑楼历史街区" in prompt_text
    # 南方湿热气候特征自动注入
    assert any(w in prompt_text for w in ["通风", "遮阳", "骑楼", "绿化"])
    assert "华南" in aigc_res["climate_zone"] or "岭南" in aigc_res["climate_zone"]


def test_universal_utm_projection_cad_export():
    """测试任意地理坐标经纬度计算 UTM 代号，并成功生成 1:1 米制 AutoCAD 2000 DXF。"""
    # 广州坐标 Lon: 113.3, Lat: 23.1 -> UTM Zone 49N (EPSG: 32649)
    epsg_gz = get_utm_epsg_for_coordinates(113.3, 23.1)
    assert epsg_gz == 32649

    # 长春坐标 Lon: 125.3, Lat: 43.9 -> UTM Zone 51N (EPSG: 32651)
    epsg_cc = get_utm_epsg_for_coordinates(125.3, 43.9)
    assert epsg_cc == 32651

    # 创建一个模拟多边形并执行多图层 DXF 导出
    poly = Polygon([[113.30, 23.10], [113.31, 23.10], [113.31, 23.11], [113.30, 23.11], [113.30, 23.10]])
    gdf = gpd.GeoDataFrame([{"geometry": poly, "name": "广州测试单元"}], crs="EPSG:4326")

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_dxf = os.path.join(tmp_dir, "test_output.dxf")
        layers = {
            "01_BOUNDARY": gdf,
            "02_EXISTING_BLDG": gdf,
        }
        res_path = export_multi_layer_dxf(layers, out_dxf, to_metric=True, target_crs=f"EPSG:{epsg_gz}")
        assert os.path.exists(res_path)

        with open(res_path, "r", encoding="ascii", errors="ignore") as f:
            content = f.read()
        assert "AC1015" in content  # 标准 AutoCAD 2000 头部
        assert "01_BOUNDARY" in content
        assert "LWPOLYLINE" in content
