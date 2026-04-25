"""Standardized exception hierarchy and error-handling utilities."""

import functools
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger("ultimateDESIGN")

F = TypeVar("F", bound=Callable[..., Any])


class UltimateDesignError(Exception):
    """Base exception for all platform errors."""


class DataNotFoundError(UltimateDesignError):
    """A required data file or resource is missing."""


class EngineUnavailableError(UltimateDesignError):
    """An external engine (SD, Ollama) is not reachable."""


def log_and_suppress(fallback: Any = None):
    """Decorator: log the exception and return *fallback*.

    Replaces bare ``except: pass`` with observable degradation.
    Use only on non-critical rendering / data-loading paths.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception:
                logger.warning(
                    "%s.%s suppressed  (fallback=%r)",
                    func.__module__,
                    func.__qualname__,
                    fallback,
                    exc_info=True,
                )
                return fallback
        return wrapper  # type: ignore[return-value]
    return decorator
