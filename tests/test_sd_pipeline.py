import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.append(str(root))
sys.modules.setdefault("streamlit", type(sys)("streamlit_mock"))

import requests
from unittest.mock import patch, MagicMock

from src.engines.sd_exceptions import (
    SDEngineError,
    SDConnectionError,
    SDTimeoutError,
    SDAPIError,
    SDVRAMError,
)


def test_sd_exceptions_hierarchy():
    """All SD exceptions inherit from SDEngineError."""
    assert issubclass(SDConnectionError, SDEngineError)
    assert issubclass(SDTimeoutError, SDEngineError)
    assert issubclass(SDAPIError, SDEngineError)
    assert issubclass(SDVRAMError, SDEngineError)


def test_sd_exceptions_are_catchable():
    """All SD exceptions can be caught as SDEngineError."""
    for cls in (SDConnectionError, SDTimeoutError, SDAPIError, SDVRAMError):
        try:
            raise cls("test")
        except SDEngineError:
            pass
        else:
            assert False, f"{cls.__name__} was not raised"


from PIL import Image
import base64
from io import BytesIO


def test_pipeline_step_defaults():
    """PipelineStep initializes with empty controlnet_units."""
    from src.engines.stable_diffusion_engine import PipelineStep

    step = PipelineStep(mode="txt2img", params={"prompt": "test"})
    assert step.mode == "txt2img"
    assert step.controlnet_units == []


def test_pipeline_step_supports_all_modes():
    """PipelineStep accepts all 4 rendering modes."""
    from src.engines.stable_diffusion_engine import PipelineStep

    for mode in ("txt2img", "img2img", "inpaint", "upscale"):
        step = PipelineStep(mode=mode, params={})
        assert step.mode == mode


def test_sd_result_fields():
    """SDResult holds images, seed, info, and elapsed time."""
    from src.engines.stable_diffusion_engine import SDResult

    img = Image.new("RGB", (64, 64))
    result = SDResult(images=[img], seed=42, info={"test": True}, elapsed_seconds=1.5)
    assert len(result.images) == 1
    assert result.seed == 42
    assert result.elapsed_seconds == 1.5


def test_encode_image_to_base64():
    """encode_image converts a PIL Image to a JPEG base64 string."""
    from src.engines.stable_diffusion_engine import encode_image

    img = Image.new("RGB", (100, 100), color="red")
    result = encode_image(img)
    assert isinstance(result, str)
    assert len(result) > 0
    decoded = base64.b64decode(result)
    restored = Image.open(BytesIO(decoded))
    assert restored.size == (100, 100)


def test_encode_image_thumbnails_large_images():
    """encode_image downsizes images larger than max_dim."""
    from src.engines.stable_diffusion_engine import encode_image

    img = Image.new("RGB", (2048, 2048))
    result = encode_image(img, max_dim=1024)
    decoded = base64.b64decode(result)
    restored = Image.open(BytesIO(decoded))
    assert max(restored.size) <= 1024


def test_encode_image_preserves_small_images():
    """encode_image does not upscale small images."""
    from src.engines.stable_diffusion_engine import encode_image

    img = Image.new("RGB", (256, 256))
    result = encode_image(img, max_dim=1024)
    decoded = base64.b64decode(result)
    restored = Image.open(BytesIO(decoded))
    assert restored.size == (256, 256)


# ============================================================
# SDPipeline tests
# ============================================================


def _make_mock_response(width=64, height=64):
    """Create a mock SD API response with a valid image."""
    img = Image.new("RGB", (width, height), color="blue")
    buf = BytesIO()
    img.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "images": [img_b64],
        "seed": 12345,
        "info": '{"seed": 12345}',
    }
    return mock_resp


def test_sd_pipeline_init():
    from src.engines.stable_diffusion_engine import SDPipeline
    pipe = SDPipeline(base_url="http://test:7860")
    assert pipe._steps == []
    assert pipe._current_step is None
    assert pipe.base_url == "http://test:7860"


def test_sd_pipeline_txt2img_creates_step():
    from src.engines.stable_diffusion_engine import SDPipeline
    pipe = SDPipeline()
    result = pipe.txt2img(prompt="test", negative_prompt="bad", width=512, height=512)
    assert result is pipe
    assert len(pipe._steps) == 1
    assert pipe._steps[0].mode == "txt2img"
    assert pipe._current_step is pipe._steps[0]


@patch("src.engines.stable_diffusion_engine.requests.post")
def test_sd_pipeline_txt2img_run(mock_post):
    from src.engines.stable_diffusion_engine import SDPipeline
    mock_post.return_value = _make_mock_response()
    pipe = SDPipeline(base_url="http://test:7860")
    result = pipe.txt2img(prompt="a city", negative_prompt="blurry", width=64, height=64).run()
    assert len(result.images) == 1
    assert isinstance(result.images[0], Image.Image)
    assert result.seed == 12345
    mock_post.assert_called_once()
    call_url = mock_post.call_args[0][0]
    assert "/sdapi/v1/txt2img" in call_url


@patch("src.engines.stable_diffusion_engine.requests.post")
def test_sd_pipeline_img2img_run(mock_post):
    from src.engines.stable_diffusion_engine import SDPipeline
    mock_post.return_value = _make_mock_response()
    pipe = SDPipeline(base_url="http://test:7860")
    img = Image.new("RGB", (64, 64))
    result = pipe.img2img(img, prompt="city", negative_prompt="blurry", denoising=0.4).run()
    assert len(result.images) == 1
    assert isinstance(result.images[0], Image.Image)
    call_url = mock_post.call_args[0][0]
    assert "/sdapi/v1/img2img" in call_url


def test_add_controlnet_without_step_raises():
    from src.engines.stable_diffusion_engine import SDPipeline
    pipe = SDPipeline()
    img = Image.new("RGB", (64, 64))
    try:
        pipe.add_controlnet(img, module="canny", model="control_canny")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "No active step" in str(e)


def test_add_controlnet_chains_to_current_step():
    from src.engines.stable_diffusion_engine import SDPipeline
    pipe = SDPipeline()
    img = Image.new("RGB", (64, 64))
    pipe.img2img(img, prompt="test", negative_prompt="bad")
    pipe.add_controlnet(img, module="canny", model="control_canny", weight=0.8)
    pipe.add_controlnet(img, module="depth", model="control_depth", weight=0.6)
    assert len(pipe._current_step.controlnet_units) == 2
    assert pipe._current_step.controlnet_units[0]["module"] == "canny"
    assert pipe._current_step.controlnet_units[1]["module"] == "depth"


@patch("src.engines.stable_diffusion_engine._load_config_aigc")
def test_add_controlnet_respects_max_units(mock_config):
    mock_config.return_value = {"controlnet": {"max_units": 2}}
    from src.engines.stable_diffusion_engine import SDPipeline
    pipe = SDPipeline()
    img = Image.new("RGB", (64, 64))
    pipe.img2img(img, prompt="test", negative_prompt="bad")
    pipe.add_controlnet(img, module="canny", model="m1")
    pipe.add_controlnet(img, module="depth", model="m2")
    try:
        pipe.add_controlnet(img, module="lineart", model="m3")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Maximum" in str(e)


@patch("src.engines.stable_diffusion_engine.requests.post")
def test_controlnet_units_appear_in_payload(mock_post):
    from src.engines.stable_diffusion_engine import SDPipeline
    mock_post.return_value = _make_mock_response()
    pipe = SDPipeline(base_url="http://test:7860")
    img = Image.new("RGB", (64, 64))
    (
        pipe.img2img(img, prompt="city", negative_prompt="blurry")
        .add_controlnet(img, module="canny", model="control_canny")
        .add_controlnet(img, module="depth", model="control_depth")
        .run()
    )
    payload = mock_post.call_args[1]["json"]
    cn_args = payload["alwayson_scripts"]["ControlNet"]["args"]
    assert len(cn_args) == 2
    assert cn_args[0]["module"] == "canny"
    assert cn_args[1]["module"] == "depth"


def test_inpaint_creates_step_with_mask():
    from src.engines.stable_diffusion_engine import SDPipeline
    pipe = SDPipeline()
    img = Image.new("RGB", (64, 64))
    mask = Image.new("L", (64, 64), 255)
    pipe.inpaint(img, mask, prompt="fix this", negative_prompt="bad")
    step = pipe._steps[0]
    assert step.mode == "inpaint"
    assert step.params["mask_image"] is mask
    assert step.params["mask_blur"] == 4
    assert step.params["inpainting_fill"] == 1


@patch("src.engines.stable_diffusion_engine.requests.post")
def test_inpaint_payload_has_mask(mock_post):
    from src.engines.stable_diffusion_engine import SDPipeline
    mock_post.return_value = _make_mock_response()
    pipe = SDPipeline(base_url="http://test:7860")
    img = Image.new("RGB", (64, 64))
    mask = Image.new("L", (64, 64), 255)
    pipe.inpaint(img, mask, prompt="fix", negative_prompt="bad").run()
    payload = mock_post.call_args[1]["json"]
    assert "mask" in payload
    assert payload["mask_blur"] == 4


def test_upscale_creates_step():
    from src.engines.stable_diffusion_engine import SDPipeline
    pipe = SDPipeline()
    pipe.upscale(scale=2, tile_size=256)
    step = pipe._steps[0]
    assert step.mode == "upscale"
    assert step.params["scale"] == 2
    assert step.params["tile_size"] == 256


def test_upscale_without_image_raises():
    from src.engines.stable_diffusion_engine import SDPipeline
    pipe = SDPipeline()
    pipe.upscale(scale=2)
    try:
        pipe.run()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "No image" in str(e)


@patch("src.engines.stable_diffusion_engine.requests.post")
def test_retry_on_connection_error(mock_post):
    from src.engines.stable_diffusion_engine import SDPipeline, SDConnectionError
    mock_post.side_effect = requests.exceptions.ConnectionError("refused")
    pipe = SDPipeline(base_url="http://test:7860")
    pipe.txt2img(prompt="t", negative_prompt="b", width=64, height=64)
    try:
        pipe.run()
        assert False, "Should have raised SDConnectionError"
    except SDConnectionError:
        pass
    assert mock_post.call_count == 3


@patch("src.engines.stable_diffusion_engine.requests.post")
def test_retry_on_503_then_succeed(mock_post):
    from src.engines.stable_diffusion_engine import SDPipeline
    fail_resp = MagicMock()
    fail_resp.status_code = 503
    ok_resp = _make_mock_response()
    mock_post.side_effect = [fail_resp, ok_resp]
    pipe = SDPipeline(base_url="http://test:7860")
    result = pipe.txt2img(prompt="t", negative_prompt="b", width=64, height=64).run()
    assert len(result.images) == 1
    assert mock_post.call_count == 2


@patch("src.engines.stable_diffusion_engine.requests.post")
def test_timeout_raises_sdtimeouterror(mock_post):
    from src.engines.stable_diffusion_engine import SDPipeline, SDTimeoutError
    mock_post.side_effect = requests.exceptions.Timeout("timed out")
    pipe = SDPipeline(base_url="http://test:7860")
    pipe.txt2img(prompt="t", negative_prompt="b", width=64, height=64)
    try:
        pipe.run()
        assert False, "Should have raised SDTimeoutError"
    except SDTimeoutError:
        pass
    assert mock_post.call_count == 1


@patch("src.engines.stable_diffusion_engine.requests.post")
def test_api_error_raises_sdapierror(mock_post):
    from src.engines.stable_diffusion_engine import SDPipeline, SDAPIError
    fail_resp = MagicMock()
    fail_resp.status_code = 500
    fail_resp.text = "Internal Server Error"
    mock_post.return_value = fail_resp
    pipe = SDPipeline(base_url="http://test:7860")
    pipe.txt2img(prompt="t", negative_prompt="b", width=64, height=64)
    try:
        pipe.run()
        assert False, "Should have raised SDAPIError"
    except SDAPIError:
        pass


def test_empty_pipeline_raises():
    from src.engines.stable_diffusion_engine import SDPipeline
    pipe = SDPipeline()
    try:
        pipe.run()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "no steps" in str(e)


@patch("src.engines.stable_diffusion_engine.requests.get")
def test_poll_progress(mock_get):
    from src.engines.stable_diffusion_engine import SDPipeline
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {"progress": 0.5, "eta_relative": 10.0, "textinfo": "Step 10/20"},
    )
    pipe = SDPipeline(base_url="http://test:7860")
    data = pipe.poll_progress()
    assert data["progress"] == 0.5


@patch("src.engines.stable_diffusion_engine.requests.get")
def test_poll_progress_handles_failure(mock_get):
    from src.engines.stable_diffusion_engine import SDPipeline
    mock_get.side_effect = Exception("network error")
    pipe = SDPipeline(base_url="http://test:7860")
    data = pipe.poll_progress()
    assert data == {"progress": 0, "eta_relative": 0, "textinfo": ""}


@patch("src.engines.stable_diffusion_engine.is_demo_mode", return_value=True)
def test_run_returns_demo_placeholder(mock_demo):
    from src.engines.stable_diffusion_engine import SDPipeline
    pipe = SDPipeline()
    result = pipe.txt2img(prompt="t", negative_prompt="b", width=64, height=64).run()
    assert len(result.images) == 1
    assert result.images[0].size == (512, 512)
    assert result.seed == -1


@patch("src.engines.stable_diffusion_engine.is_demo_mode", return_value=False)
@patch("src.engines.stable_diffusion_engine.requests.post")
def test_run_realtime_sd_delegates_to_pipeline(mock_post, mock_demo):
    from src.engines.stable_diffusion_engine import run_realtime_sd
    mock_post.return_value = _make_mock_response()
    img = Image.new("RGB", (64, 64))
    result = run_realtime_sd(img, prompt="test", negative_prompt="bad")
    assert isinstance(result, Image.Image)
    mock_post.assert_called_once()


@patch("src.engines.stable_diffusion_engine.is_demo_mode", return_value=True)
def test_run_realtime_sd_demo_returns_placeholder(mock_demo):
    from src.engines.stable_diffusion_engine import run_realtime_sd
    img = Image.new("RGB", (256, 256))
    result = run_realtime_sd(img, prompt="test", negative_prompt="bad")
    assert isinstance(result, Image.Image)
    assert result.size == (256, 256)


def test_engine_registry_exports_run_realtime_sd():
    from src.engines import engine_registry
    assert hasattr(engine_registry, "run_realtime_sd")
    assert callable(engine_registry.run_realtime_sd)


def test_engine_registry_exports_sdpipeline():
    from src.engines import engine_registry
    assert hasattr(engine_registry, "SDPipeline")
    assert hasattr(engine_registry, "SDResult")
