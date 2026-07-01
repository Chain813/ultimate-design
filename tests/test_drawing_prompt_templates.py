from src.engines import drawing_prompt_templates as templates
from src.engines.key_plot_engine import KeyPlot


def _stub_dynamic_description(monkeypatch):
    from src.engines import design_description_engine

    monkeypatch.setattr(
        design_description_engine,
        "generate_dynamic_design_description",
        lambda _name, _stage: ("测试制图策略", "测试分析结论"),
    )


def _manifest_for(asset_ids):
    asset_to_channel = {
        "fixed_base_map": "卫星底图",
        "research_scope": "红线边界图",
        "key_plots": "红线边界图",
        "fixed_frame": "固定图框模板",
        "road_network": "道路矢量图",
        "legend_reference": "图例参考图",
        "gis_theme": "GIS专题图",
        "building_texture": "建筑肌理图",
    }
    return {
        "version": 1,
        "assets": {
            asset_id: {
                "asset_id": asset_id,
                "label": asset_id,
                "prompt_channel": asset_to_channel[asset_id],
                "original_name": f"{asset_id}.png",
                "filename": f"{asset_id}.png",
                "size_bytes": 12,
            }
            for asset_id in asset_ids
        },
    }


def _complete_manifest():
    return _manifest_for(
        [
            "fixed_base_map",
            "research_scope",
            "key_plots",
            "fixed_frame",
            "road_network",
            "legend_reference",
            "gis_theme",
            "building_texture",
        ]
    )


def test_build_drawing_prompt_blocks_level_one_when_assets_missing(monkeypatch):
    monkeypatch.setattr(templates, "load_template_asset_manifest", lambda: {"version": 1, "assets": {}})

    prompt, system_prompt = templates.build_drawing_prompt("道路交通系统规划图")

    pass


def test_build_drawing_prompt_uses_locked_asset_compiler(monkeypatch):
    monkeypatch.setattr(
        templates,
        "load_template_asset_manifest",
        lambda: _manifest_for(
            [
                "fixed_base_map",
                "research_scope",
                "key_plots",
                "fixed_frame",
                "road_network",
                "legend_reference",
            ]
        ),
    )

    prompt, _ = templates.build_drawing_prompt("道路交通系统规划图")

    assert "完整提示词" in prompt
    assert "请严格套用上传的固定图框" in prompt
    assert "只生成规划分析覆盖层" in prompt
    assert "最终合成顺序" in prompt
    assert "请为以下城市设计项目生成" not in prompt


def test_dynamic_plot_template_is_generated(monkeypatch):
    _stub_dynamic_description(monkeypatch)
    monkeypatch.setattr(templates, "load_template_asset_manifest", _complete_manifest)

    prompt, system_prompt = templates.build_drawing_prompt("地块7街道断面图")

    assert prompt
    assert "完整提示词" in prompt
    assert "地块7街道断面图" in prompt
    assert system_prompt


def test_dynamic_plot_inference_prefers_plot_detail_over_status_keywords():
    drawing_name = "地块6现状问题图"

    assert templates._infer_chapter_from_name(drawing_name) == "06 重点地段更新改造设计"
    assert templates._infer_stage_from_name(drawing_name) == "10"


def test_dynamic_plot_inference_runs_before_legacy_book_chapters(monkeypatch):
    drawing_name = "地块6现状问题图"
    monkeypatch.setattr(templates, "BOOK_CHAPTERS", {"02 数据诊断篇": [drawing_name]})

    assert templates._infer_chapter_from_name(drawing_name) == "06 重点地段更新改造设计"
    assert templates._infer_stage_from_name(drawing_name) == "10"


def test_dynamic_plot_inference_requires_canonical_plot_detail_name():
    drawing_name = "用地现状图地块6"

    assert templates._infer_chapter_from_name(drawing_name) == "02 数据诊断篇"
    assert templates._infer_stage_from_name(drawing_name) == "01"


def test_build_drawing_prompt_uses_dynamic_key_plot_context(monkeypatch):
    _stub_dynamic_description(monkeypatch)
    monkeypatch.setattr(templates, "load_template_asset_manifest", _complete_manifest)
    monkeypatch.setattr(
        templates,
        "get_configured_key_plots",
        lambda: [
            KeyPlot(index=1, plot_id="1", name="站前门户单元"),
            KeyPlot(index=7, plot_id="7", name="滨水修补单元", role="滨水公共空间修补"),
        ],
    )

    prompt, _ = templates.build_drawing_prompt("道路交通系统规划图")

    assert "共 2 个重点更新单元" in prompt
    assert "地块7：滨水修补单元" in prompt
    assert "五个重点地块" not in prompt


def test_key_plot_prompt_context_does_not_suppress_loader_errors(monkeypatch):
    def raise_corrupt_config():
        raise RuntimeError("corrupted key plot config")

    monkeypatch.setattr(templates, "get_configured_key_plots", raise_corrupt_config)

    try:
        templates._get_key_plot_prompt_context()
    except RuntimeError as exc:
        assert "corrupted key plot config" in str(exc)
    else:
        raise AssertionError("Expected key plot loader errors to propagate")
