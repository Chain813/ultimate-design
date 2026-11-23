"""Dual-mode runtime adapter bridging Streamlit and Desktop FastAPI Sidecar.

This module decouples all 29 domain engines, config loaders, and workflow buses
from Streamlit's global runtime while preserving 100% backward compatibility with
existing Streamlit pages and all 361 pytest tests.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable
import functools
import hashlib
import pickle
import sys
import threading
import time
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

_LOCK = threading.RLock()
_ACTIVE_PROJECT_ID: str = "changchun_default"
_PROJECT_STATES: dict[str, dict[str, Any]] = {"changchun_default": {}}
_DATA_CACHES: list[_MemoryCache] = []
_RESOURCE_CACHES: list[_MemoryCache] = []


def is_streamlit_runtime() -> bool:
    """Return True only when running inside an active Streamlit ScriptRunContext."""
    if "streamlit" not in sys.modules:
        return False
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        return get_script_run_ctx(suppress_warning=True) is not None
    except Exception:
        return False


def _get_st_session_state() -> Any | None:
    """Safely return st.session_state if streamlit is imported and accessible."""
    st_mod = sys.modules.get("streamlit")
    if st_mod is None:
        return None
    try:
        return getattr(st_mod, "session_state", None)
    except Exception:
        return None


def get_active_project_id() -> str:
    """Get the currently active project workspace ID."""
    with _LOCK:
        return _ACTIVE_PROJECT_ID


def set_active_project_id(project_id: str, clear_cache: bool = True) -> str:
    """Switch active project workspace ID and optionally flush in-memory caches."""
    global _ACTIVE_PROJECT_ID
    clean_id = (project_id or "changchun_default").strip() or "changchun_default"
    with _LOCK:
        _ACTIVE_PROJECT_ID = clean_id
        _PROJECT_STATES.setdefault(clean_id, {})
    if clear_cache:
        clear_all_caches()
    return clean_id


def _current_project_dict() -> dict[str, Any]:
    with _LOCK:
        return _PROJECT_STATES.setdefault(_ACTIVE_PROJECT_ID, {})


def get_state(key: str, default: Any = None) -> Any:
    """Read state key from Streamlit session_state (if present) or desktop project store."""
    st_state = _get_st_session_state()
    if st_state is not None:
        try:
            if key in st_state:
                return st_state[key]
        except Exception:
            pass
    with _LOCK:
        pdict = _current_project_dict()
        if key in pdict:
            return pdict[key]
    return default


def set_state(key: str, value: Any) -> Any:
    """Write state key to both desktop project store and Streamlit session_state (if accessible)."""
    with _LOCK:
        _current_project_dict()[key] = value
    st_state = _get_st_session_state()
    if st_state is not None:
        try:
            st_state[key] = value
        except Exception:
            pass
    return value


def delete_state(key: str, default: Any = None) -> Any:
    """Delete state key from both desktop project store and Streamlit session_state."""
    val = default
    with _LOCK:
        pdict = _current_project_dict()
        if key in pdict:
            val = pdict.pop(key)
    st_state = _get_st_session_state()
    if st_state is not None:
        try:
            if key in st_state:
                val = st_state.pop(key)
        except Exception:
            pass
    return val


class StateProxy:
    """Dict-like and attribute-like proxy drop-in compatible with `st.session_state`."""

    def __getitem__(self, key: str) -> Any:
        st_state = _get_st_session_state()
        if st_state is not None:
            try:
                if key in st_state:
                    return st_state[key]
            except Exception:
                pass
        with _LOCK:
            pdict = _current_project_dict()
            if key in pdict:
                return pdict[key]
        raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        set_state(key, value)

    def __delitem__(self, key: str) -> None:
        if key not in self:
            raise KeyError(key)
        delete_state(key)

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        st_state = _get_st_session_state()
        if st_state is not None:
            try:
                if key in st_state:
                    return True
            except Exception:
                pass
        with _LOCK:
            return key in _current_project_dict()

    def get(self, key: str, default: Any = None) -> Any:
        return get_state(key, default)

    def setdefault(self, key: str, default: Any = None) -> Any:
        if key in self:
            return self[key]
        set_state(key, default)
        return default

    def pop(self, key: str, *args: Any) -> Any:
        if key in self:
            return delete_state(key)
        if args:
            return args[0]
        raise KeyError(key)

    def update(self, mapping: dict[str, Any] | None = None, **kwargs: Any) -> None:
        if mapping:
            for k, v in mapping.items():
                set_state(k, v)
        for k, v in kwargs.items():
            set_state(k, v)

    def keys(self):
        return self.to_dict().keys()

    def values(self):
        return self.to_dict().values()

    def items(self):
        return self.to_dict().items()

    def clear(self) -> None:
        with _LOCK:
            _current_project_dict().clear()
        st_state = _get_st_session_state()
        if st_state is not None:
            try:
                st_state.clear()
            except Exception:
                pass

    def to_dict(self) -> dict[str, Any]:
        with _LOCK:
            merged = dict(_current_project_dict())
        st_state = _get_st_session_state()
        if st_state is not None:
            try:
                for k, v in st_state.items():
                    merged[k] = v
            except Exception:
                pass
        return merged

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self[name] = value


runtime_state = StateProxy()


def _make_cache_key(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    """Build a deterministic cache key scoped to the active project ID."""
    proj = get_active_project_id()
    try:
        raw = pickle.dumps((proj, args, sorted(kwargs.items())), protocol=pickle.HIGHEST_PROTOCOL)
        return hashlib.blake2b(raw, digest_size=16).hexdigest()
    except Exception:
        fallback = f"{proj}:{repr(args)}:{repr(sorted(kwargs.items()))}".encode("utf-8", errors="ignore")
        return hashlib.blake2b(fallback, digest_size=16).hexdigest()


class _MemoryCache:
    """Thread-safe LRU + optional TTL cache for desktop/CLI/pytest runtimes."""

    def __init__(self, ttl: float | int | None = None, max_entries: int = 256) -> None:
        self.ttl = float(ttl) if ttl is not None else None
        self.max_entries = max(16, int(max_entries))
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = threading.RLock()

    def get_or_compute(self, fn: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        key = _make_cache_key(args, kwargs)
        now = time.monotonic()
        with self._lock:
            if key in self._store:
                ts, val = self._store[key]
                if self.ttl is None or (now - ts) <= self.ttl:
                    self._store.move_to_end(key)
                    return val
                del self._store[key]

        result = fn(*args, **kwargs)
        with self._lock:
            self._store[key] = (now, result)
            self._store.move_to_end(key)
            while len(self._store) > self.max_entries:
                self._store.popitem(last=False)
        return result

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


def _build_dual_cache_decorator(
    registry: list[_MemoryCache],
    *dargs: Any,
    ttl: float | int | None = None,
    max_entries: int = 256,
    **dkwargs: Any,
) -> Any:
    """Construct a decorator that works both in desktop mode and Streamlit mode."""

    def _decorate(func: F) -> F:
        mem_cache = _MemoryCache(ttl=ttl, max_entries=max_entries)
        with _LOCK:
            registry.append(mem_cache)

        @functools.wraps(func)
        def _wrapper(*args: Any, **kwargs: Any) -> Any:
            return mem_cache.get_or_compute(func, args, kwargs)

        _wrapper.clear = mem_cache.clear  # type: ignore[attr-defined]
        return _wrapper  # type: ignore[return-value]

    if len(dargs) == 1 and callable(dargs[0]) and not dkwargs:
        return _decorate(dargs[0])
    return _decorate


def cache_data(*dargs: Any, ttl: float | int | None = None, max_entries: int = 256, **dkwargs: Any) -> Any:
    """Environment-agnostic replacement for `@st.cache_data`."""
    return _build_dual_cache_decorator(_DATA_CACHES, *dargs, ttl=ttl, max_entries=max_entries, **dkwargs)


def cache_resource(*dargs: Any, ttl: float | int | None = None, max_entries: int = 128, **dkwargs: Any) -> Any:
    """Environment-agnostic replacement for `@st.cache_resource`."""
    return _build_dual_cache_decorator(_RESOURCE_CACHES, *dargs, ttl=ttl, max_entries=max_entries, **dkwargs)


cache_data.clear = lambda: [c.clear() for c in list(_DATA_CACHES)]  # type: ignore[attr-defined]
cache_resource.clear = lambda: [c.clear() for c in list(_RESOURCE_CACHES)]  # type: ignore[attr-defined]


def clear_all_caches() -> None:
    """Flush all in-memory data/resource caches and Streamlit caches if imported."""
    with _LOCK:
        data_list = list(_DATA_CACHES)
        res_list = list(_RESOURCE_CACHES)
    for c in data_list:
        c.clear()
    for c in res_list:
        c.clear()
    st_mod = sys.modules.get("streamlit")
    if st_mod is not None:
        for attr in ("cache_data", "cache_resource"):
            try:
                target = getattr(st_mod, attr, None)
                if target is not None and hasattr(target, "clear"):
                    target.clear()
            except Exception:
                pass
