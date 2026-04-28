"""AIGC engine: Stable Diffusion img2img pipeline via local WebUI API.

Usage:
    from src.engines.stable_diffusion_engine import run_realtime_sd
"""

import base64
import logging
import time
from io import BytesIO

import requests
from PIL import Image, ImageDraw

from src.config.loader import load_global_config
from src.utils.runtime_flags import is_demo_mode

logger = logging.getLogger("ultimateDESIGN")


def run_realtime_sd(pil_image, prompt, negative_prompt, steps=20, cfg_scale=7.0, denoising=0.55,
                    cn_module="none", cn_model="none", cn_weight=1.0,
                    sampler_name="DPM++ 2M Karras", seed=-1, upscale_mode=""):
    """Call local Stable Diffusion WebUI img2img endpoint.

    Falls back to a placeholder image in demo mode.
    """
    if is_demo_mode():
        return _demo_placeholder(pil_image)

    img_copy = pil_image.copy()
    img_copy.thumbnail((1024, 1024))
    buffered = BytesIO()
    img_copy.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    payload = _build_payload(
        img_base64=img_base64, prompt=prompt, negative_prompt=negative_prompt,
        steps=steps, cfg_scale=cfg_scale, denoising=denoising,
        cn_module=cn_module, cn_model=cn_model, cn_weight=cn_weight,
        sampler_name=sampler_name, seed=seed, upscale_mode=upscale_mode,
        width=img_copy.width, height=img_copy.height,
    )

    config = load_global_config()
    url = config.get("engines", {}).get("aigc", {}).get("sd_webui_url",
                                                         "http://127.0.0.1:7860/sdapi/v1/img2img")
    timeout_val = config.get("engines", {}).get("aigc", {}).get("timeout", 120)

    for attempt in range(2):
        try:
            response = requests.post(url, json=payload, timeout=timeout_val)
            if response.status_code == 200:
                r_data = response.json()
                return Image.open(BytesIO(base64.b64decode(r_data["images"][0])))
        except requests.exceptions.ConnectionError:
            if attempt == 0:
                time.sleep(3)
        except Exception:
            logger.warning("SD img2img call failed", exc_info=True)
            return None
    return None


def _demo_placeholder(pil_image):
    w, h = pil_image.size
    img = Image.new("RGB", (min(w, 1024), min(h, 1024)), "#1e293b")
    draw = ImageDraw.Draw(img)
    draw.text((img.width // 6, img.height // 2 - 20), "AIGC Demo Placeholder", fill="#818cf8")
    draw.text((img.width // 6, img.height // 2 + 10), "请替换 assets/demo_aigc_result.png", fill="#64748b")
    return img


def _build_payload(img_base64, prompt, negative_prompt, steps, cfg_scale, denoising,
                   cn_module, cn_model, cn_weight, sampler_name, seed, upscale_mode,
                   width, height):
    controlnet_unit = {
        "input_image": img_base64,
        "module": cn_module,
        "model": cn_model,
        "weight": cn_weight,
        "resize_mode": "Just Resize",
        "lowvram": False,
        "processor_res": 512,
        "control_mode": "Balanced",
    }

    payload = {
        "init_images": [img_base64],
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "denoising_strength": denoising,
        "steps": steps,
        "sampler_name": sampler_name,
        "cfg_scale": cfg_scale,
        "seed": seed,
        "width": width,
        "height": height,
        "alwayson_scripts": {"ControlNet": {"args": [controlnet_unit]}},
    }

    if upscale_mode and "Ultimate" in upscale_mode:
        payload["script_name"] = "Ultimate SD upscale"
        payload["script_args"] = [
            "", 512, 512, 8, 32, 64, 0.35, 32,
            0, True, 0, False, 8, 0, 2, 2048, 2048, 2,
        ]
    elif upscale_mode and "Inpainting" in upscale_mode:
        payload["mask_blur"] = 4
        payload["inpainting_fill"] = 1

    return payload
