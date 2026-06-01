
"""Domain engine modules for planning analysis and generation.

Uses lazy imports via engine_registry to avoid loading heavy dependencies
(pandas, numpy, PIL, jieba, requests, torch) at module import time.
"""

from src.engines.engine_registry import __all__ as _registry_all

__all__ = list(_registry_all)


def __getattr__(name):
    if name in _registry_all:
        from src.engines import engine_registry
        return getattr(engine_registry, name)
    raise AttributeError(f"module 'src.engines' has no attribute {name!r}")
