from src.utils.exceptions import (
    UltimateDesignError,
    DataNotFoundError,
    EngineUnavailableError,
    log_and_suppress,
)


def test_ultimate_design_error_is_exception():
    assert issubclass(UltimateDesignError, Exception)


def test_data_not_found_error_hierarchy():
    assert issubclass(DataNotFoundError, UltimateDesignError)


def test_engine_unavailable_error_hierarchy():
    assert issubclass(EngineUnavailableError, UltimateDesignError)


def test_log_and_suppress_returns_fallback():
    @log_and_suppress(fallback=42)
    def boom():
        raise RuntimeError("kaboom")

    assert boom() == 42


def test_log_and_suppress_returns_original_when_no_error():
    @log_and_suppress(fallback="fallback")
    def fine():
        return "success"

    assert fine() == "success"


def test_log_and_suppress_preserves_function_name():
    @log_and_suppress(fallback=None)
    def should_preserve_name():
        raise ValueError

    assert should_preserve_name.__name__ == "should_preserve_name"


def test_log_and_suppress_accepts_any_exception_type():
    @log_and_suppress(fallback=None)
    def raise_type_error():
        raise TypeError("type mismatch")

    assert raise_type_error() is None
