"""Unified local-service availability probing.

Eliminates duplicated probes across app.py, app_shell.py, and daemon_manager.py.

Usage:
    from src.utils.service_check import is_port_alive, check_engine_status, EngineStatus
"""

import socket
from dataclasses import dataclass

SD_PORT = 7860
OLLAMA_PORT = 11434
DEFAULT_TIMEOUT = 0.2


@dataclass(frozen=True)
class EngineStatus:
    sd: bool
    gemma: bool
    ollama: bool

    @property
    def all_online(self) -> bool:
        return self.sd and self.gemma


def is_port_alive(port: int, host: str = "127.0.0.1", timeout: float = DEFAULT_TIMEOUT) -> bool:
    """Non-raising TCP port probe."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


def check_engine_status() -> EngineStatus:
    """Check both SD and Ollama engine availability."""
    sd_alive = is_port_alive(SD_PORT)
    ollama_alive = is_port_alive(OLLAMA_PORT)
    return EngineStatus(
        sd=sd_alive,
        gemma=ollama_alive,
        ollama=ollama_alive,
    )
