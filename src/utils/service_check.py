"""Unified local-service availability probing.

Eliminates duplicated probes across app.py, app_shell.py, and daemon_manager.py.

Usage:
    from src.utils.service_check import is_port_alive, check_engine_status, EngineStatus
"""

import socket
import threading
import time
from dataclasses import dataclass

SD_PORT = 7860
OLLAMA_PORT = 11434
DEFAULT_TIMEOUT = 0.2

# Module-level cache for engine status (10-second TTL)
_status_cache = None
_status_cache_ts = 0.0
_STATUS_CACHE_TTL = 10.0
_status_lock = threading.Lock()


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
    """Check both SD and Ollama engine availability (cached for 10s, thread-safe)."""
    global _status_cache, _status_cache_ts
    
    with _status_lock:
        now = time.time()
        if _status_cache is not None and (now - _status_cache_ts) < _STATUS_CACHE_TTL:
            return _status_cache
            
        sd_alive = is_port_alive(SD_PORT)
        ollama_alive = is_port_alive(OLLAMA_PORT)
        result = EngineStatus(
            sd=sd_alive,
            gemma=ollama_alive,
            ollama=ollama_alive,
        )
        _status_cache = result
        _status_cache_ts = time.time()
        return result
