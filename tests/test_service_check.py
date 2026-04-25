from src.utils.service_check import (
    is_port_alive,
    check_engine_status,
    EngineStatus,
    SD_PORT,
    OLLAMA_PORT,
    DEFAULT_TIMEOUT,
)


def test_is_port_alive_returns_bool():
    result = is_port_alive(9999, timeout=0.01)  # unlikely to be open
    assert isinstance(result, bool)


def test_is_port_alive_closed_port_false():
    """A high ephemeral port should almost certainly be closed."""
    result = is_port_alive(49152, "127.0.0.1", timeout=0.01)
    assert result is False


def test_engine_status_dataclass_fields():
    s = EngineStatus(sd=True, gemma=False, ollama=False)
    assert s.sd is True
    assert s.gemma is False
    assert s.ollama is False


def test_engine_status_all_online_true():
    s = EngineStatus(sd=True, gemma=True, ollama=True)
    assert s.all_online is True


def test_engine_status_all_online_false_when_sd_offline():
    s = EngineStatus(sd=False, gemma=True, ollama=True)
    assert s.all_online is False


def test_engine_status_all_online_false_when_gemma_offline():
    s = EngineStatus(sd=True, gemma=False, ollama=True)
    assert s.all_online is False


def test_check_engine_status_returns_dataclass():
    result = check_engine_status()
    assert isinstance(result, EngineStatus)
    assert isinstance(result.sd, bool)
    assert isinstance(result.gemma, bool)
    assert isinstance(result.ollama, bool)


def test_port_constants_are_correct():
    assert SD_PORT == 7860
    assert OLLAMA_PORT == 11434
    assert 0 < DEFAULT_TIMEOUT <= 1.0
