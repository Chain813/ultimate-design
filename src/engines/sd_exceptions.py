"""Custom exceptions for the SD Pipeline engine."""


class SDEngineError(Exception):
    """Base exception for all SD engine errors."""


class SDConnectionError(SDEngineError):
    """Cannot connect to SD WebUI."""


class SDTimeoutError(SDEngineError):
    """SD processing timed out."""


class SDAPIError(SDEngineError):
    """SD API returned a non-200 status code."""


class SDVRAMError(SDEngineError):
    """Insufficient GPU VRAM."""
