"""User settings manager for storing keys and API URLs in the user's home directory.

Prevents credentials leakage and persists configurations across installations.
"""

import contextlib
import json
import os
from pathlib import Path

SETTINGS_DIR = Path.home() / ".ultimatedesign"
SETTINGS_FILE = SETTINGS_DIR / "config.json"

DEFAULT_SETTINGS = {
    "DEEPSEEK_API_KEY": "",
    "SD_WEBUI_URL": "http://127.0.0.1:7860",
    "LLM_API_URL": "https://api.deepseek.com/chat/completions",
    "OLLAMA_URL": "http://localhost:11434",
}


def load_user_settings() -> dict:
    """Load settings from the local JSON config file, creating defaults if missing."""
    if not SETTINGS_DIR.exists():
        with contextlib.suppress(Exception):
            SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

    settings = DEFAULT_SETTINGS.copy()
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    settings.update(data)
        except Exception:
            pass

    # Backport DEEPSEEK_API_KEY to environment variables for dotenv/getenv compatibility
    if settings.get("DEEPSEEK_API_KEY"):
        os.environ["DEEPSEEK_API_KEY"] = settings["DEEPSEEK_API_KEY"]

    return settings


def save_user_settings(settings: dict) -> bool:
    """Save user settings to the local JSON config file."""
    if not SETTINGS_DIR.exists():
        try:
            SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            return False

    try:
        # Filter settings to only known keys
        to_save = {}
        for k in DEFAULT_SETTINGS:
            to_save[k] = settings.get(k, DEFAULT_SETTINGS[k])

        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=4, ensure_ascii=False)

        # Update current environment variable
        if to_save.get("DEEPSEEK_API_KEY"):
            os.environ["DEEPSEEK_API_KEY"] = to_save["DEEPSEEK_API_KEY"]
        elif "DEEPSEEK_API_KEY" in os.environ:
            del os.environ["DEEPSEEK_API_KEY"]

        return True
    except Exception:
        return False


def get_effective_setting(key: str, fallback_value: str = "") -> str:
    """Get setting value, prioritizing env variables/user settings, then fallback."""
    # Check env var first
    if key in os.environ:
        return os.environ[key]

    # Load from user settings file
    settings = load_user_settings()
    return settings.get(key, fallback_value)
