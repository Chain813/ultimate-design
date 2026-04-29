from src.ui.output_flow_panel import build_output_flow_prompt


def _manifest(asset_ids):
    channel_map = {
        "fixed_base_map": "卫星底图",
        "research_scope": "红线边界图",
        "key_plots": "红线边界图",
        "fixed_frame": "固定图框模板",
    }
    return {
        "version": 1,
        "assets": {
            asset_id: {
                "asset_id": asset_id,
                "prompt_channel": channel_map[asset_id],
                "original_name": f"{asset_id}.png",
                "filename": f"{asset_id}.png",
            }
            for asset_id in asset_ids
        },
    }


def test_output_flow_prompt_blocks_when_required_assets_missing():
    prompt = build_output_flow_prompt({"version": 1, "assets": {}})

    assert "必备固定资产：0/4" in prompt
    assert "一级精度图纸缺少任一必备资产时，停止生成最终 Image 2.0 提示词" in prompt
    assert "不允许 AI 缩放、旋转、裁切、重绘或改写固定底图" in prompt


def test_output_flow_prompt_includes_synthesis_order_when_ready():
    prompt = build_output_flow_prompt(_manifest(["fixed_base_map", "research_scope", "key_plots", "fixed_frame"]))

    assert "必备固定资产：4/4" in prompt
    assert "固定底图 -> AI 覆盖层 -> 研究范围红线 -> 重点地块边界 -> 固定图框" in prompt
    assert "AI 图像模型只承担覆盖层和表现风格" in prompt
