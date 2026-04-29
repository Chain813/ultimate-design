from src.engines import drawing_prompt_templates as templates


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


def test_build_drawing_prompt_blocks_level_one_when_assets_missing(monkeypatch):
    monkeypatch.setattr(templates, "load_template_asset_manifest", lambda: {"version": 1, "assets": {}})

    prompt, system_prompt = templates.build_drawing_prompt("道路交通系统规划图")

    assert "暂不生成最终 Image 2.0 提示词" in prompt
    assert "缺失项" in prompt
    assert "固定底图" in prompt
    assert "固定资产制图提示词审校器" in system_prompt


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
