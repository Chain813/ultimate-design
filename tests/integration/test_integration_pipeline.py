from unittest.mock import MagicMock

import pytest


def test_pipeline_end_to_end(monkeypatch):
    # Mock LLM Engine
    mock_llm = MagicMock(return_value="Mocked LLM Response for Drawing Prompt")
    monkeypatch.setattr("src.engines.llm_engine.call_llm_engine", mock_llm)

    # Mock Spatial Engine
    monkeypatch.setattr("src.engines.spatial_engine.get_hud_statistics", lambda: {"poi_count": 10})
    monkeypatch.setattr("src.engines.spatial_engine.get_skyline_features", lambda: {"max_height": 100})

    # Mock SD Engine
    from PIL import Image

    from src.engines.stable_diffusion_engine import SDResult
    dummy_img = Image.new("RGB", (100, 100), color="blue")
    mock_sd = MagicMock()
    mock_sd.txt2img.return_value = None
    mock_sd.upscale.return_value = None
    mock_sd.run.return_value = SDResult(images=[dummy_img], seed=42, info="mock", elapsed_seconds=1.0)
    monkeypatch.setattr("src.engines.drawing_pipeline.SDPipeline", lambda **kwargs: mock_sd)

    mock_profile = MagicMock()
    mock_profile.name = "masterplan"
    mock_profile.drawing_type = "Masterplan"
    mock_profile.precision = "三级精度"
    mock_profile.required_uploads = []
    mock_profile.style = "standard"
    mock_profile.allows_ai_expression = True
    mock_profile.needs_real_data = False
    mock_profile.requires_standard_frame = True
    monkeypatch.setattr("src.engines.drawing_pipeline.get_drawing_profile", lambda name: mock_profile)
    monkeypatch.setattr("src.engines.drawing_pipeline.build_drawing_prompt", lambda name: ("Mock prompt", "Mock sys prompt"))

    # Mock the prompt engine LLM method inside drawing_pipeline
    monkeypatch.setattr("src.engines.drawing_pipeline.generate_drawing_prompt_with_llm", lambda x: "Mock prompt")

    # Execute the pipeline
    from src.engines.drawing_pipeline import DrawingPipeline
    
    pipeline = DrawingPipeline(sd_pipeline=mock_sd)
    result = pipeline.generate_single("masterplan")
    assert result.success is True
    assert result.image is not None
