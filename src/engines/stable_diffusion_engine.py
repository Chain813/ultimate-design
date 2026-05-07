"""AIGC engine: Stable Diffusion multi-modal rendering pipeline.

Supports txt2img, img2img, inpainting, upscale, and multi-ControlNet via local SD WebUI API.

Usage:
    from src.engines.stable_diffusion_engine import SDPipeline, run_realtime_sd
"""

import base64
import json
import logging
import time
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests
from PIL import Image, ImageDraw

from src.config.loader import load_global_config
from src.engines.sd_exceptions import (
    SDAPIError,
    SDConnectionError,
    SDTimeoutError,
)
from src.utils.runtime_flags import is_demo_mode

logger = logging.getLogger("ultimateDESIGN")


# ============================================================
# Data classes
# ============================================================


@dataclass
class PipelineStep:
    """A single step in the SD rendering pipeline."""
    mode: str  # "txt2img" | "img2img" | "inpaint" | "upscale"
    params: Dict[str, Any] = field(default_factory=dict)
    controlnet_units: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SDResult:
    """Result from an SD pipeline execution."""
    images: List[Any]  # list of PIL.Image.Image
    seed: int
    info: Dict[str, Any]
    elapsed_seconds: float


# ============================================================
# Utilities
# ============================================================


def encode_image(pil_image, max_dim: int = 1024) -> str:
    """Encode a PIL Image to base64 JPEG string, thumbnailing if needed."""
    img_copy = pil_image.copy()
    img_copy.thumbnail((max_dim, max_dim))
    buffered = BytesIO()
    img_copy.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def _decode_image(b64_str: str) -> Image.Image:
    """Decode a base64 string to a PIL Image."""
    return Image.open(BytesIO(base64.b64decode(b64_str)))


def _load_config_aigc() -> dict:
    """Load the aigc section from global config."""
    config = load_global_config()
    return config.get("engines", {}).get("aigc", {})


def _parse_sd_response(data: dict) -> Tuple[Any, int, dict]:
    """Parse SD API response into (image, seed, info)."""
    image = _decode_image(data["images"][0])
    seed = data.get("seed", -1)
    info = data.get("info", {})
    if isinstance(info, str):
        try:
            info = json.loads(info)
        except Exception:
            info = {}
    return image, seed, info


def _build_common_payload(step: PipelineStep) -> dict:
    """Build common payload fields shared by txt2img/img2img/inpaint."""
    p = step.params
    payload = {
        "steps": p.get("steps", 20),
        "sampler_name": p.get("sampler_name", "DPM++ 2M Karras"),
        "cfg_scale": p.get("cfg_scale", 7.0),
        "seed": p.get("seed", -1),
    }
    if step.controlnet_units:
        payload["alwayson_scripts"] = {
            "ControlNet": {"args": step.controlnet_units}
        }
    return payload


# ============================================================
# SDPipeline
# ============================================================


class SDPipeline:
    """Unified rendering pipeline: txt2img -> img2img -> inpaint -> upscale.

    Builder pattern -- chain mode calls, then call .run() to execute.

    Example:
        result = (
            SDPipeline("http://127.0.0.1:7860")
            .img2img(init_image, prompt, negative_prompt, denoising=0.4)
            .add_controlnet(canny_image, module="canny", model="control_canny")
            .upscale(scale=2)
            .run()
        )
    """

    def __init__(self, base_url: str = "", timeout: int = 0):
        aigc = _load_config_aigc()
        self._aigc = aigc
        self.base_url = base_url or aigc.get("sd_webui_url", "http://127.0.0.1:7860")
        self.timeout = timeout or aigc.get("timeout", 180)
        self._steps: List[PipelineStep] = []
        self._current_step: Optional[PipelineStep] = None

    # ---- 4 rendering modes ----

    def txt2img(self, prompt: str, negative_prompt: str,
                width: int = 512, height: int = 512, **kwargs) -> "SDPipeline":
        step = PipelineStep(mode="txt2img", params={
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            **kwargs,
        })
        self._steps.append(step)
        self._current_step = step
        return self

    def img2img(self, init_image, prompt: str, negative_prompt: str,
                denoising: float = 0.55, **kwargs) -> "SDPipeline":
        step = PipelineStep(mode="img2img", params={
            "init_image": init_image,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "denoising": denoising,
            **kwargs,
        })
        self._steps.append(step)
        self._current_step = step
        return self

    def inpaint(self, init_image, mask_image, prompt: str, negative_prompt: str,
                denoising: float = 0.55, **kwargs) -> "SDPipeline":
        step = PipelineStep(mode="inpaint", params={
            "init_image": init_image,
            "mask_image": mask_image,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "denoising": denoising,
            "mask_blur": kwargs.pop("mask_blur", 4),
            "inpainting_fill": kwargs.pop("inpainting_fill", 1),
            "inpainting_mask_invert": kwargs.pop("inpainting_mask_invert", 0),
            **kwargs,
        })
        self._steps.append(step)
        self._current_step = step
        return self

    def upscale(self, image=None, scale: int = 2, **kwargs) -> "SDPipeline":
        upscale_cfg = self._aigc.get("upscale", {})
        step = PipelineStep(mode="upscale", params={
            "image": image,
            "scale": scale,
            "tile_size": kwargs.pop("tile_size", upscale_cfg.get("tile_size", 512)),
            "tile_overlap": kwargs.pop("tile_overlap", upscale_cfg.get("tile_overlap", 32)),
            "target_max_dim": kwargs.pop("target_max_dim", upscale_cfg.get("target_max_dim", 2048)),
            **kwargs,
        })
        self._steps.append(step)
        self._current_step = step
        return self

    # ---- ControlNet ----

    def add_controlnet(self, image, module: str, model: str,
                       weight: float = 1.0) -> "SDPipeline":
        if self._current_step is None:
            raise ValueError("No active step -- call txt2img/img2img/inpaint first")
        max_units = self._aigc.get("controlnet", {}).get("max_units", 3)
        if len(self._current_step.controlnet_units) >= max_units:
            raise ValueError(f"Maximum {max_units} ControlNet units per step")
        self._current_step.controlnet_units.append({
            "input_image": encode_image(image),
            "module": module,
            "model": model,
            "weight": weight,
            "resize_mode": "Just Resize",
            "lowvram": False,
            "processor_res": 512,
            "control_mode": "Balanced",
        })
        return self

    # ---- Execution ----

    def run(self, on_progress: Optional[Callable] = None) -> SDResult:
        """Execute all pipeline steps sequentially."""
        if not self._steps:
            raise ValueError("Pipeline has no steps -- call txt2img/img2img/inpaint/upscale first")

        if is_demo_mode():
            return self.run_demo()

        start_time = time.time()
        current_image = None
        last_seed = -1
        last_info = {}

        for i, step in enumerate(self._steps):
            if on_progress:
                on_progress(step_index=i, total_steps=len(self._steps), mode=step.mode)
            if step.mode == "txt2img":
                current_image, last_seed, last_info = self._exec_txt2img(step, on_progress)
            elif step.mode == "img2img":
                current_image, last_seed, last_info = self._exec_img2img(step, current_image, on_progress)
            elif step.mode == "inpaint":
                current_image, last_seed, last_info = self._exec_inpaint(step, current_image, on_progress)
            elif step.mode == "upscale":
                current_image = self._exec_upscale(step, current_image, on_progress)

        elapsed = time.time() - start_time
        return SDResult(
            images=[current_image],
            seed=last_seed,
            info=last_info,
            elapsed_seconds=round(elapsed, 2),
        )

    def run_demo(self) -> SDResult:
        """Return a placeholder result in demo mode."""
        img = Image.new("RGB", (512, 512), "#1e293b")
        draw = ImageDraw.Draw(img)
        draw.text((128, 240), "AIGC Demo Placeholder", fill="#818cf8")
        draw.text((128, 270), "SD WebUI not connected", fill="#64748b")
        return SDResult(images=[img], seed=-1, info={}, elapsed_seconds=0.0)

    # ---- Internal execution methods ----

    def _exec_txt2img(self, step: PipelineStep, on_progress) -> tuple:
        p = step.params
        payload = _build_common_payload(step)
        payload.update({
            "prompt": p["prompt"],
            "negative_prompt": p["negative_prompt"],
            "width": p["width"],
            "height": p["height"],
        })
        url = f"{self.base_url.rstrip('/')}/sdapi/v1/txt2img"
        data = self._execute_with_retry(url, payload, on_progress)
        return _parse_sd_response(data)

    def _exec_img2img(self, step: PipelineStep, current_image, on_progress) -> tuple:
        p = step.params
        init_img = p.get("init_image") or current_image
        payload = _build_common_payload(step)
        payload.update({
            "init_images": [encode_image(init_img)],
            "prompt": p["prompt"],
            "negative_prompt": p["negative_prompt"],
            "denoising_strength": p["denoising"],
            "width": p.get("width", init_img.width if hasattr(init_img, 'width') else 512),
            "height": p.get("height", init_img.height if hasattr(init_img, 'height') else 512),
        })
        url = f"{self.base_url.rstrip('/')}/sdapi/v1/img2img"
        data = self._execute_with_retry(url, payload, on_progress)
        return _parse_sd_response(data)

    def _exec_inpaint(self, step: PipelineStep, current_image, on_progress) -> tuple:
        p = step.params
        init_img = p.get("init_image") or current_image
        mask_img = p["mask_image"]
        payload = _build_common_payload(step)
        payload.update({
            "init_images": [encode_image(init_img)],
            "mask": encode_image(mask_img),
            "prompt": p["prompt"],
            "negative_prompt": p["negative_prompt"],
            "denoising_strength": p["denoising"],
            "mask_blur": p.get("mask_blur", 4),
            "inpainting_fill": p.get("inpainting_fill", 1),
            "inpainting_mask_invert": p.get("inpainting_mask_invert", 0),
            "resize_mode": "Just Resize",
        })
        url = f"{self.base_url.rstrip('/')}/sdapi/v1/img2img"
        data = self._execute_with_retry(url, payload, on_progress)
        return _parse_sd_response(data)

    def _exec_upscale(self, step: PipelineStep, current_image, on_progress) -> Any:
        p = step.params
        img = p.get("image") or current_image
        if img is None:
            raise ValueError("No image to upscale -- provide image or chain after a generation step")

        tile_size = p.get("tile_size", 512)
        _tile_overlap = p.get("tile_overlap", 32)
        scale = p.get("scale", 2)
        target_w = img.width * scale
        target_h = img.height * scale
        target_max = p.get("target_max_dim", 2048)
        if max(target_w, target_h) > target_max:
            ratio = target_max / max(target_w, target_h)
            target_w = int(target_w * ratio)
            target_h = int(target_h * ratio)

        payload = {
            "init_images": [encode_image(img, max_dim=4096)],
            "prompt": "",
            "negative_prompt": "",
            "denoising_strength": 0.35,
            "steps": 8,
            "width": target_w,
            "height": target_h,
            "script_name": "Ultimate SD upscale",
            "script_args": [
                "", tile_size, tile_size, 8, 32, 64, 0.35, tile_size,
                0, True, 0, False, 8, 0, 2, target_w, target_h, 2,
            ],
        }
        url = f"{self.base_url.rstrip('/')}/sdapi/v1/img2img"
        data = self._execute_with_retry(url, payload, on_progress)
        return _decode_image(data["images"][0])

    # ---- Network layer ----

    def _execute_with_retry(self, url: str, payload: dict,
                            on_progress=None, max_retries: int = 2) -> dict:
        """POST to SD API with retry logic."""
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(url, json=payload, timeout=self.timeout)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 503:
                    logger.warning("SD WebUI busy (503), retrying in 5s...")
                    time.sleep(5)
                    continue
                else:
                    raise SDAPIError(f"SD API returned {response.status_code}: {response.text[:200]}")
            except requests.exceptions.ConnectionError as err:
                if attempt < max_retries:
                    logger.warning("SD connection failed, retry %d/%d...", attempt + 1, max_retries)
                    time.sleep(3)
                    continue
                raise SDConnectionError(
                    "Cannot connect to SD WebUI. Check that it is running with --api flag."
                ) from err
            except requests.exceptions.Timeout as err:
                raise SDTimeoutError(
                    f"SD processing timed out ({self.timeout}s). "
                    "Try lowering resolution or increasing timeout in config.yaml."
                ) from err
        raise SDConnectionError("SD WebUI unreachable after retries.")

    def poll_progress(self) -> dict:
        """Poll /sdapi/v1/progress for current generation status."""
        try:
            url = f"{self.base_url.rstrip('/')}/sdapi/v1/progress"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return {"progress": 0, "eta_relative": 0, "textinfo": ""}


# ============================================================
# Legacy compatibility wrapper
# ============================================================


def run_realtime_sd(pil_image, prompt, negative_prompt, steps=20, cfg_scale=7.0, denoising=0.55,
                    cn_module="none", cn_model="none", cn_weight=1.0,
                    sampler_name="DPM++ 2M Karras", seed=-1, upscale_mode=""):
    """Legacy interface -- delegates to SDPipeline.

    Preserved for backward compatibility with existing page code.
    """
    if is_demo_mode():
        return _demo_placeholder(pil_image)

    pipe = SDPipeline()
    pipe.img2img(
        init_image=pil_image,
        prompt=prompt,
        negative_prompt=negative_prompt,
        denoising=denoising,
        steps=steps,
        sampler_name=sampler_name,
        cfg_scale=cfg_scale,
        seed=seed,
    )
    if cn_module != "none" and cn_model != "none":
        pipe.add_controlnet(pil_image, module=cn_module, model=cn_model, weight=cn_weight)
    if upscale_mode and "Ultimate" in upscale_mode:
        pipe.upscale(scale=2)

    result = pipe.run()
    return result.images[0] if result.images else None


def _demo_placeholder(pil_image):
    w, h = pil_image.size
    img = Image.new("RGB", (min(w, 1024), min(h, 1024)), "#1e293b")
    draw = ImageDraw.Draw(img)
    draw.text((img.width // 6, img.height // 2 - 20), "AIGC Demo Placeholder", fill="#818cf8")
    draw.text((img.width // 6, img.height // 2 + 10), "请替换 assets/demo_aigc_result.png", fill="#64748b")
    return img
