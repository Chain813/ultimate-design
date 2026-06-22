import base64
import mimetypes
from functools import lru_cache

from src.config import ROOT_DIR, get_static_url


@lru_cache(maxsize=16)
def get_inline_static_image_src(filename: str) -> str:
    """Return a data URI for critical above-the-fold static images."""
    asset_path = ROOT_DIR / "static" / filename
    if not asset_path.exists():
        return get_static_url(filename)

    mime_type = mimetypes.guess_type(asset_path.name)[0] or "image/png"
    encoded = base64.b64encode(asset_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"
