"""Tests for deliverables, graduation report pipeline, white model camera, and Stage 13 A3 framing."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image


# ═══════════════════════════════════════════════════════════════════════════
# 1. Document Pipeline: _gen_plot_metrics, _gen_plot_personas, _get_plot_names
# ═══════════════════════════════════════════════════════════════════════════

def test_gen_plot_metrics_no_nameerror_and_dynamic_redlines(monkeypatch):
    """_gen_plot_metrics must define spatial without NameError and use dynamic redlines on custom sites."""
    from src.engines import document_pipeline

    captured_prompts: list[str] = []
    saved_outputs: list[tuple[str, str, str]] = []

    monkeypatch.setattr(document_pipeline, "_skip_if_exists", lambda stage, key: False)
    monkeypatch.setattr(document_pipeline, "_spatial", lambda max_chars=1500: "实测空间上下文：容积率1.8，绿地率18%")
    monkeypatch.setattr(
        document_pipeline,
        "_call",
        lambda model, sys_p, prompt, timeout=180: (captured_prompts.append(prompt) or "指标表格结果" * 10),
    )
    monkeypatch.setattr(
        document_pipeline,
        "_save",
        lambda stage, key, data: saved_outputs.append((stage, key, data)),
    )

    # Mock site config to a custom Shanghai site
    monkeypatch.setattr("src.config.site.get_site_name", lambda: "杨浦滨江工业遗存片区")
    monkeypatch.setattr("src.config.site.get_site_city", lambda: "上海市")
    monkeypatch.setattr(
        "src.config.site.get_site_config",
        lambda: {
            "name": "杨浦滨江工业遗存片区",
            "city": "上海市",
            "regulatory_limits": {
                "far": 2.8,
                "height_limit": 45,
                "building_density_max": 0.40,
                "greenery_ratio_min": 0.32,
            },
        },
    )

    document_pipeline._gen_plot_metrics(lambda *a: None, lambda *a: None, "船厂核心更新地块")

    assert len(captured_prompts) == 1
    prompt = captured_prompts[0]
    assert "实测空间上下文：容积率1.8，绿地率18%" in prompt
    assert "杨浦滨江工业遗存片区" in prompt
    assert "2.8" in prompt
    assert "45m" in prompt
    assert "历史核心区容积率≤1.4、限高≤9m" not in prompt
    assert len(saved_outputs) == 1


def test_gen_plot_personas_no_nameerror_and_uses_site_name(monkeypatch):
    """_gen_plot_personas must define s_name without NameError and inject dynamic site name."""
    from src.engines import document_pipeline

    captured_prompts: list[str] = []
    saved_outputs: list[tuple[str, str, str]] = []

    monkeypatch.setattr(document_pipeline, "_skip_if_exists", lambda stage, key: False)
    monkeypatch.setattr(
        document_pipeline,
        "_call",
        lambda model, sys_p, prompt, timeout=180: (captured_prompts.append(prompt) or "三组人群画像详细分析结果" * 5),
    )
    monkeypatch.setattr(
        document_pipeline,
        "_save",
        lambda stage, key, data: saved_outputs.append((stage, key, data)),
    )
    monkeypatch.setattr("src.config.site.get_site_name", lambda: "深圳南头古城更新单元")

    document_pipeline._gen_plot_personas(lambda *a: None, lambda *a: None, "南城门入口商业地块")

    assert len(captured_prompts) == 1
    assert "深圳南头古城更新单元" in captured_prompts[0]
    assert "南城门入口商业地块" in captured_prompts[0]
    assert len(saved_outputs) == 1


def test_get_plot_names_candidate_plots_and_regex(monkeypatch):
    """_get_plot_names should extract from get_active_candidate_plots, bullet list regex, and bracket regex."""
    from src.engines import document_pipeline

    # Case 1: get_active_candidate_plots mocked with custom plots
    monkeypatch.setattr(
        "src.ui.site_ingestion_panel.get_active_candidate_plots",
        lambda: [{"name": "自定义地块A"}, {"Name": "自定义地块B"}],
    )
    assert document_pipeline._get_plot_names() == ["自定义地块A", "自定义地块B"]

    # Case 2: Bullet list format from spatial_data_injector.get_key_plots_summary()
    monkeypatch.setattr("src.ui.site_ingestion_panel.get_active_candidate_plots", lambda: [])
    monkeypatch.setattr(
        "src.engines.spatial_data_injector.get_key_plots_summary",
        lambda: (
            "研究范围共 3 个重点更新单元：\n"
            "  - 农贸水产市场: 面积 3.71 ha\n"
            "  - 滨水文创工坊：面积 5.12 ha\n"
            "  - 轨道交通TOD地块: 面积 4.05 ha"
        ),
    )
    assert document_pipeline._get_plot_names() == ["农贸水产市场", "滨水文创工坊", "轨道交通TOD地块"]

    # Case 3: Bracketed format
    monkeypatch.setattr(
        "src.engines.spatial_data_injector.get_key_plots_summary",
        lambda: "重点更新范围包括【南头文创街区】与「科技园配套社区」两个核心单元。",
    )
    assert document_pipeline._get_plot_names() == ["南头文创街区", "科技园配套社区"]

    # Case 4: Fallback when nothing found
    monkeypatch.setattr("src.engines.spatial_data_injector.get_key_plots_summary", lambda: "暂无地块数据")
    assert document_pipeline._get_plot_names() == [
        "老水产批发市场",
        "中车旧厂区",
        "食品调料市场",
        "清禾市场",
        "石油公司地块",
    ]


def test_dehardcoded_diagnosis_and_building_form(monkeypatch):
    """_gen_diagnosis_report and _gen_building_form must not hardcode Changchun 30% aging / 9m-18m-24m on custom sites."""
    from src.engines import document_pipeline

    captured: list[str] = []
    monkeypatch.setattr(document_pipeline, "_skip_if_exists", lambda stage, key: False)
    monkeypatch.setattr(document_pipeline, "_load", lambda stage, key, default=None: "上游空间结构数据")
    monkeypatch.setattr(document_pipeline, "_spatial", lambda max_chars=3500: "空间统计上下文")
    monkeypatch.setattr(
        document_pipeline,
        "_call",
        lambda model, sys_p, prompt, timeout=180: (captured.append(prompt) or "生成结果内容" * 12),
    )
    monkeypatch.setattr(document_pipeline, "_save", lambda stage, key, data: None)
    monkeypatch.setattr("src.config.site.get_site_name", lambda: "广州永庆坊西片区")
    monkeypatch.setattr("src.config.site.get_site_city", lambda: "广州市")
    monkeypatch.setattr(
        "src.config.site.get_site_config",
        lambda: {"name": "广州永庆坊西片区", "city": "广州市", "regulatory_limits": {"height_limit": 30}},
    )

    document_pipeline._gen_diagnosis_report(lambda *a: None, lambda *a: None)
    document_pipeline._gen_building_form(lambda *a: None, lambda *a: None)

    assert len(captured) == 2
    assert "老龄化率30%" not in captured[0]
    assert "广州市广州永庆坊西片区" in captured[0]
    assert "核心区≤9m/一般区≤18m/站前区≤24m" not in captured[1]
    assert "30m" in captured[1]


# ═══════════════════════════════════════════════════════════════════════════
# 2. Document Composer: _generate_english_abstract
# ═══════════════════════════════════════════════════════════════════════════

def test_generate_english_abstract_custom_site(monkeypatch):
    """_generate_english_abstract must dynamically use the custom site's city, name, and area instead of Changchun."""
    from src.engines import document_composer

    captured_prompts: list[str] = []

    monkeypatch.setattr(document_composer, "_generate_abstract_from_chapters", lambda chapters: "中文摘要测试文本。")
    monkeypatch.setattr("src.config.site.get_site_city", lambda: "成都市")
    monkeypatch.setattr("src.config.site.get_site_district", lambda: "锦江区")
    monkeypatch.setattr("src.config.site.get_site_name", lambda: "东门码头历史更新片区")
    monkeypatch.setattr(
        "src.config.site.get_site_config",
        lambda: {"city": "成都市", "district": "锦江区", "name": "东门码头历史更新片区", "area_ha": 78.5},
    )
    monkeypatch.setattr(
        "src.config.site.get_project_info",
        lambda: {"name": "成都东门码头片区数智更新设计"},
    )
    monkeypatch.setattr(
        "src.engines.llm_engine.call_llm_engine",
        lambda prompt, system_prompt="", model="": (captured_prompts.append(prompt) or "English abstract output."),
    )

    res = document_composer._generate_english_abstract({"1.1": "正文内容"})
    assert res == "English abstract output."
    assert len(captured_prompts) == 1
    prompt = captured_prompts[0]
    assert "成都市" in prompt
    assert "东门码头历史更新片区" in prompt
    assert "78.5" in prompt
    assert "Puppet Emperor's Palace" not in prompt
    assert "Weimanhuang Palace" not in prompt


# ═══════════════════════════════════════════════════════════════════════════
# 3. WhiteModelRenderer: Dynamic Camera & Context-Adaptive AIGC Prompt
# ═══════════════════════════════════════════════════════════════════════════

def test_white_model_renderer_dynamic_camera_non_changchun(tmp_path):
    """WhiteModelRenderer.render_birdseye must dynamically compute camera target and eye for non-Changchun sites."""
    from src.engines.white_model_renderer import WhiteModelRenderer

    gis_dir = tmp_path / "gis"
    gis_dir.mkdir(parents=True)

    # Create Shanghai Lujiazui-area building footprints (~121.50, 31.24)
    buildings_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"building_id": "b1", "Floor": 6, "is_historical": False},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [121.500, 31.240],
                        [121.502, 31.240],
                        [121.502, 31.242],
                        [121.500, 31.242],
                        [121.500, 31.240],
                    ]],
                },
            },
            {
                "type": "Feature",
                "properties": {"building_id": "b2", "Floor": 10, "is_historical": True},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [121.504, 31.243],
                        [121.506, 31.243],
                        [121.506, 31.245],
                        [121.504, 31.245],
                        [121.504, 31.243],
                    ]],
                },
            },
        ],
    }
    (gis_dir / "Building_Footprints.geojson").write_text(
        json.dumps(buildings_geojson, ensure_ascii=False), encoding="utf-8"
    )

    renderer = WhiteModelRenderer(data_dir=tmp_path)
    out_sw = tmp_path / "birdseye_sw.png"
    renderer.render_birdseye(str(out_sw), direction="sw")

    assert out_sw.exists()
    view_sw = renderer.last_camera_view
    assert view_sw is not None
    assert 121.500 <= view_sw.target_lng <= 121.506
    assert 31.240 <= view_sw.target_lat <= 31.245
    assert view_sw.eye_lng < view_sw.target_lng
    assert view_sw.eye_lat < view_sw.target_lat

    # Verify overview_south, overview_southeast, overview_aerial
    view_south = renderer._resolve_camera_view("overview_south")
    assert view_south.eye_lng == pytest.approx(view_sw.target_lng, abs=1e-5)
    assert view_south.eye_lat < view_south.target_lat

    view_se = renderer._resolve_camera_view("overview_southeast")
    assert view_se.eye_lng > view_se.target_lng
    assert view_se.eye_lat < view_se.target_lat

    view_aerial = renderer._resolve_camera_view("overview_aerial")
    assert view_aerial.eye_alt == 1200.0


def test_build_consistent_aigc_prompt_non_changchun(monkeypatch):
    """build_consistent_aigc_prompt must avoid Changchun-specific tokens when active site is another city."""
    from src.engines.white_model_renderer import build_consistent_aigc_prompt

    monkeypatch.setattr("src.config.site.get_site_city", lambda: "广州市")
    monkeypatch.setattr("src.config.site.get_site_name", lambda: "恩宁路骑楼历史街区")
    monkeypatch.setattr("src.config.site.get_site_center", lambda: [113.245, 23.115])
    monkeypatch.setattr(
        "src.config.site.get_site_config",
        lambda: {"city": "广州市", "name": "恩宁路骑楼历史街区", "center": [113.245, 23.115]},
    )

    pos, neg = build_consistent_aigc_prompt("birdseye")
    assert "neo-classical mansard roofs" not in pos
    assert "riverfront on east side, railway corridor on north" not in pos
    assert "subtropical" in pos or "colonnades" in pos or "aerial bird's eye view" in pos


# ═══════════════════════════════════════════════════════════════════════════
# 4. Stage 13 Framing & Universal GIS Renderer
# ═══════════════════════════════════════════════════════════════════════════

def test_apply_custom_a3_overlay_repaints_header_and_card(tmp_path):
    """apply_custom_a3_overlay must paint over the header and right card with custom student metadata."""
    from src.engines.frame_generator import apply_custom_a3_overlay

    # Create a solid mid-gray base image simulating a raw NO_FRAME sheet
    raw_path = tmp_path / "raw_sheet.png"
    out_path = tmp_path / "framed_sheet.png"
    base_img = Image.new("RGB", (2240, 1584), (120, 130, 140))
    base_img.save(str(raw_path))

    res_path = apply_custom_a3_overlay(
        image_path=raw_path,
        output_path=out_path,
        title="自定义空间结构规划图",
        subtitle="展示深圳市南头古城核心更新单元的空间结构体系",
        desc_list=[
            "1. 核心结构：构建一核两轴三片区的空间发展骨架。",
            "2. 慢行织补：打通东西向历史文化漫游步道。",
            "3. 指标管控：核心区限高15米，容积率控制在1.8以内。",
        ],
        author="张三",
        author_id="20260101",
        organization="深圳大学建筑与城市规划学院\n城乡规划21级",
        site_name="南头古城更新片区",
        city_name="深圳市",
        drawing_number="DR-036",
    )

    assert res_path.exists()
    out_img = Image.open(str(res_path))
    assert out_img.size == (2240, 1584)

    arr = np.array(out_img)
    # Header area (top ~5-10% height) should have been painted with white card + text (not uniform (120,130,140))
    header_crop = arr[70:160, 50:2100]
    assert not np.all(header_crop == [120, 130, 140])
    assert header_crop.max() == 255

    # Right explanation & title-block card area should also be painted
    right_card_crop = arr[600:1500, 1620:2180]
    assert not np.all(right_card_crop == [120, 130, 140])
    assert right_card_crop.max() == 255

    # Central map area should remain untouched
    map_center_crop = arr[500:900, 400:1200]
    assert np.all(map_center_crop == [120, 130, 140])


def test_draw_spatial_map_non_changchun_universal_fallback(tmp_path, monkeypatch):
    """draw_spatial_map must use the universal GIS renderer when the active site is outside Changchun."""
    from tools import draw_scope_map

    monkeypatch.setattr("src.config.site.get_site_city", lambda: "杭州市")
    monkeypatch.setattr("src.config.site.get_site_name", lambda: "大运河拱宸桥遗产更新片区")
    monkeypatch.setattr("src.config.site.get_site_center", lambda: [120.145, 30.318])
    monkeypatch.setattr(
        "src.config.site.get_site_config",
        lambda: {
            "city": "杭州市",
            "name": "大运河拱宸桥遗产更新片区",
            "center": [120.145, 30.318],
            "bbox": [120.140, 30.314, 120.150, 30.322],
            "area_ha": 92.0,
            "regulatory_limits": {"far": 2.2, "height_limit": 24},
        },
    )

    out_png = tmp_path / "hangzhou_scope.png"
    view_w = draw_scope_map.draw_spatial_map(str(out_png), drawing_type="现状区位图")

    assert out_png.exists()
    assert view_w > 0
    img = Image.open(str(out_png))
    assert img.width > 1000 and img.height > 700
