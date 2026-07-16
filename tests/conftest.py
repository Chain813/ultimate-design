"""Shared test fixtures, path setup, and Streamlit mock for ultimateDESIGN."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to sys.path
root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

# ── Streamlit mock (must exist before any src module is imported) ──
_st_mock = MagicMock()
_test_cache = {}

def _make_cached_decorator(func):
    def wrapped(*args, **kwargs):
        key = (func.__name__, str(args), str(sorted(kwargs.items())))
        if key not in _test_cache:
            _test_cache[key] = func(*args, **kwargs)
        return _test_cache[key]
    
    def clear():
        keys_to_remove = [k for k in _test_cache if k[0] == func.__name__]
        for k in keys_to_remove:
            del _test_cache[k]
            
    wrapped.clear = clear
    return wrapped



def _cache_resource(*args, **kwargs):
    def decorator(func):
        return _make_cached_decorator(func)
    if len(args) == 1 and callable(args[0]):
        return _make_cached_decorator(args[0])
    return decorator


def _cache_data(*args, **kwargs):
    def decorator(func):
        return _make_cached_decorator(func)
    if len(args) == 1 and callable(args[0]):
        return _make_cached_decorator(args[0])
    return decorator



_st_mock.cache_resource = _cache_resource
_st_mock.cache_data = _cache_data
_st_mock.session_state = {}
_st_mock.set_page_config = MagicMock()
_st_mock.markdown = MagicMock()
_st_mock.columns = MagicMock(return_value=[MagicMock()])
_st_mock.expander = MagicMock(return_value=MagicMock())
_st_mock.radio = MagicMock(return_value="mock")
_st_mock.checkbox = MagicMock(return_value=True)
_st_mock.info = MagicMock()
_st_mock.warning = MagicMock()
_st_mock.error = MagicMock()
_st_mock.sidebar = MagicMock()
_st_mock.spinner = MagicMock(return_value=MagicMock())

sys.modules["streamlit"] = _st_mock
sys.modules.setdefault("streamlit", _st_mock)
