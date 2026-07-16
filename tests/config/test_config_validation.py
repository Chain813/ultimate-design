import pytest
from src.config.loader import load_global_config

def test_config_loader_validation(monkeypatch, tmp_path):
    # Mock resolve_path to point to a temporary test config
    test_yaml = """
engines:
  llm:
    api_url: "invalid-url-no-scheme"
    timeout: 9999
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(test_yaml, encoding="utf-8")

    def mock_resolve(path):
        if "config.yaml" in path:
            return config_file
        return tmp_path / path

    monkeypatch.setattr("src.config.loader.resolve_path", mock_resolve)
    
    # Clear the st.cache_resource cache before testing
    load_global_config.clear()
    
    config = load_global_config()
    
    llm = config.get("engines", {}).get("llm", {})
    assert llm.get("api_url") == "https://api.deepseek.com/chat/completions" # Fell back
    assert llm.get("timeout") == 600 # Clamped from 9999
