import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.append(str(root))
sys.modules.setdefault("streamlit", type(sys)("streamlit_mock"))

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
