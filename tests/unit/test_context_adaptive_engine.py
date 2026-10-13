"""Unit tests for the pure data-driven Context-Adaptive Engine.

Verifies:
1. UTM EPSG dynamic calculation across global coordinates.
2. Objective plot diagnostics inference across industrial, residential, commercial, and waterfront plots.
3. Dynamic generation of realistic tripartite personas without hardcoded mock templates.
4. Coordinate-based climate adaptation and consensus-driven AIGC prompt generation.
"""

import pytest

from src.engines.context_adaptive_engine import (
    get_utm_epsg_for_coordinates,
    infer_plot_diagnostics,
    generate_adaptive_personas,
    generate_adaptive_aigc_prompt,
)


def test_get_utm_epsg_for_coordinates():
    # Changchun / Northeast China (Lon 125.32, Lat 43.85) -> Zone 51 -> 32651
    epsg_changchun = get_utm_epsg_for_coordinates(125.32, 43.85)
    assert epsg_changchun == 32651
    assert isinstance(epsg_changchun, int)

    # Shenzhen / South China (Lon 114.05, Lat 22.54) -> Zone 50 -> 32650
    epsg_shenzhen = get_utm_epsg_for_coordinates(114.05, 22.54)
    assert epsg_shenzhen == 32650
    assert isinstance(epsg_shenzhen, int)

    # Sydney / Southern Hemisphere (Lon 151.20, Lat -33.86) -> Zone 56 -> 32756
    epsg_sydney = get_utm_epsg_for_coordinates(151.20, -33.86)
    assert epsg_sydney == 32756
    assert isinstance(epsg_sydney, int)

    # London / Greenwich (Lon -0.12, Lat 51.50) -> Zone 30 -> 32630
    epsg_london = get_utm_epsg_for_coordinates(-0.12, 51.50)
    assert epsg_london == 32630


def test_infer_plot_diagnostics_industrial():
    plot = {
        "name": "旧机械制造厂地块",
        "land_use": "industrial",
        "area_ha": 18.5,
        "gvi_mean": 0.08,
        "poi_count": 6,
        "building_density": 0.52,
        "svf": 0.65,
    }
    diagnostics = infer_plot_diagnostics(plot)
    diag_str = " ".join(diagnostics)

    # Typology: Industrial reuse & steel truss / brownfield
    assert "大跨度" in diag_str or "厂房" in diag_str
    assert "棕地" in diag_str or "环境风险" in diag_str

    # Quantitative: GVI < 0.15, Area > 15 ha, POI < 15, Building Density > 45%
    assert "绿视率严重匮乏" in diag_str
    assert "口袋公园" in diag_str
    assert "地块超尺度" in diag_str
    assert "建筑基底密度偏高" in diag_str
    assert "POI便民设施匮乏" in diag_str


def test_infer_plot_diagnostics_residential():
    plot = {
        "name": "老旧工人新村居住区",
        "land_use": "residential",
        "area_ha": 6.2,
        "gvi_mean": 0.11,
        "poi_count": 28,
        "building_density": 0.46,
        "svf": 0.22,
    }
    diagnostics = infer_plot_diagnostics(plot)
    diag_str = " ".join(diagnostics)

    # Typology: Aging facilities & pipeline
    assert "适老" in diag_str
    assert "管网" in diag_str or "老化" in diag_str
    assert "人车" in diag_str or "停车" in diag_str

    # Quantitative: GVI < 0.15, SVF < 0.25, Building Density > 0.45
    assert "绿视率严重匮乏" in diag_str
    assert "天空开敞度极低" in diag_str
    assert "建筑基底密度偏高" in diag_str


def test_infer_plot_diagnostics_commercial():
    plot = {
        "name": "核心商圈商业街区",
        "land_use": "commercial",
        "area_ha": 3.8,
        "gvi_mean": 0.18,
        "poi_count": 165,
        "building_density": 0.58,
        "svf": 0.38,
        "clutter_mean": 0.42,
    }
    diagnostics = infer_plot_diagnostics(plot)
    diag_str = " ".join(diagnostics)

    # Typology: Homogeneous commerce & night economy
    assert "商业业态同质化" in diag_str
    assert "夜间经济" in diag_str

    # Quantitative: POI > 120, Clutter > 0.35
    assert "POI设施过度密集" in diag_str
    assert "视觉杂乱度偏高" in diag_str


def test_infer_plot_diagnostics_waterfront():
    plot = {
        "name": "南河滨水生态走廊",
        "land_use": "waterfront",
        "area_ha": 12.0,
        "gvi_mean": 0.38,
        "poi_count": 8,
        "building_density": 0.14,
        "svf": 0.76,
    }
    diagnostics = infer_plot_diagnostics(plot)
    diag_str = " ".join(diagnostics)

    # Typology: Riverbank & resilience
    assert "滨水驳岸硬质化" in diag_str or "亲水" in diag_str
    assert "防汛排涝" in diag_str or "海绵" in diag_str

    # Quantitative: GVI >= 0.35, Building Density < 0.20, SVF > 0.70
    assert "绿化本底指标良好" in diag_str
    assert "建筑密度较低" in diag_str
    assert "天空开敞度过大" in diag_str


def test_infer_plot_diagnostics_empty_or_none():
    res1 = infer_plot_diagnostics(None)
    assert isinstance(res1, list)
    assert len(res1) > 0

    res2 = infer_plot_diagnostics({})
    assert isinstance(res2, list)
    assert len(res2) > 0


def test_generate_adaptive_personas():
    site_context = {"city": "广州市", "district": "荔湾区", "name": "珠江老粮仓码头更新"}
    target_plot = {
        "name": "旧码头筒仓改造区",
        "land_use": "industrial",
        "area_ha": 8.4,
        "building_density": 0.38,
    }
    regulatory_limits = {
        "far": 2.2,
        "height_limit": 30.0,
        "building_density_max": 0.35,
        "greenery_ratio_min": 0.35,
    }

    personas = generate_adaptive_personas(site_context, target_plot, regulatory_limits)

    # Check the 3 stakeholder groups exist
    assert "resident_or_user" in personas
    assert "investor_or_operator" in personas
    assert "planner_or_regulator" in personas

    for role_key, p in personas.items():
        assert "name" in p and len(p["name"]) > 0
        assert "stance" in p and len(p["stance"]) > 0
        assert "core_interests" in p and len(p["core_interests"]) >= 3
        assert "system_prompt" in p and len(p["system_prompt"]) > 50

        # Rigorous check: ABSOLUTELY NO hardcoded legacy templates!
        assert "老王" not in p["name"]
        assert "老王" not in p["system_prompt"]
        assert "赵总" not in p["name"]
        assert "赵总" not in p["system_prompt"]
        assert "李工" not in p["name"]
        assert "李工" not in p["system_prompt"]
        assert "长春水产市场" not in p["system_prompt"]

    # Verify site-specific dynamic injection
    assert "广州市" in personas["resident_or_user"]["name"]
    assert "旧码头筒仓改造区" in personas["resident_or_user"]["system_prompt"]
    assert "2.2" in personas["planner_or_regulator"]["system_prompt"]
    assert "30.0米" in personas["planner_or_regulator"]["system_prompt"] or "30" in personas["planner_or_regulator"]["system_prompt"]


def test_generate_adaptive_aigc_prompt_regional_climates():
    # 1. Northern Cold Climate (Changchun / Harbin ~ Lat 43.85, Lon 125.32)
    north_site = {"city": "长春市", "lat": 43.85, "lon": 125.32}
    north_plot = {"name": "长影厂周边街区", "land_use": "industrial"}
    prompt_north = generate_adaptive_aigc_prompt(north_site, north_plot)
    assert "北方" in prompt_north["climate_zone"]
    assert "防寒" in prompt_north["climate_features"] or "采暖" in prompt_north["climate_features"]
    assert "snow" in prompt_north["prompt"].lower() or "cold" in prompt_north["prompt"].lower()

    # 2. Southern Humid Subtropical Climate (Guangzhou ~ Lat 23.13, Lon 113.26)
    south_site = {"city": "广州市", "lat": 23.13, "lon": 113.26}
    south_plot = {"name": "西关骑楼街区", "land_use": "commercial"}
    prompt_south = generate_adaptive_aigc_prompt(south_site, south_plot)
    assert "华南" in prompt_south["climate_zone"]
    assert "遮阳" in prompt_south["climate_features"] or "骑楼" in prompt_south["climate_features"]
    assert "arcade" in prompt_south["prompt"].lower() or "shading" in prompt_south["prompt"].lower() or "colonnade" in prompt_south["prompt"].lower()

    # 3. Southwestern Mountainous Climate (Chengdu / Chongqing ~ Lat 29.56, Lon 106.55)
    sw_site = {"city": "重庆市", "lat": 29.56, "lon": 106.55}
    sw_plot = {"name": "半山崖线聚落", "land_use": "residential"}
    prompt_sw = generate_adaptive_aigc_prompt(sw_site, sw_plot)
    assert "西南山地" in prompt_sw["climate_zone"]
    assert "退台" in prompt_sw["climate_features"] or "随坡就势" in prompt_sw["climate_features"]
    assert "terraced" in prompt_sw["prompt"].lower() or "hillside" in prompt_sw["prompt"].lower()

    # 4. Jiangnan Water Network Climate (Suzhou ~ Lat 31.30, Lon 120.62)
    jn_site = {"city": "苏州市", "lat": 31.30, "lon": 120.62}
    jn_plot = {"name": "平江路滨水街区", "land_use": "waterfront"}
    prompt_jn = generate_adaptive_aigc_prompt(jn_site, jn_plot)
    assert "江南水网" in prompt_jn["climate_zone"]
    assert "亲水驳岸" in prompt_jn["climate_features"] or "驳岸" in prompt_jn["climate_features"]
    assert "waterfront" in prompt_jn["prompt"].lower() or "revetment" in prompt_jn["prompt"].lower()


def test_generate_adaptive_aigc_prompt_consensus_injection():
    site = {"city": "成都市", "lat": 30.65, "lon": 104.06}
    plot = {"name": "东郊记忆文创地块", "land_use": "industrial"}
    consensus = {
        "历史建筑保护": "完整保留红砖厂房大跨度钢架",
        "公共绿地率": "提升至35%并增设立体连廊",
        "容积率上限": "严格限制在1.8以内",
    }
    res = generate_adaptive_aigc_prompt(site, plot, consensus)

    prompt = res["prompt"]
    assert "完整保留红砖厂房大跨度钢架" in prompt
    assert "提升至35%并增设立体连廊" in prompt
    assert "1.8" in prompt
    assert "negative_prompt" in res
    assert len(res["negative_prompt"]) > 20
