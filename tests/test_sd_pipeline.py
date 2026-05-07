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
            pass  # expected
