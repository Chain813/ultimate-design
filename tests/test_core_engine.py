import src.engines.core_engine as core_engine


def test_load_global_config_has_engine_section():
    config = core_engine.load_global_config()
    assert "engines" in config
    assert "llm" in config["engines"]


def test_load_rag_knowledge_fallback_when_file_missing(monkeypatch):
    def _fake_load_global_config():
        return {"data": {"rag_knowledge_path": "data/does_not_exist.json"}}

    monkeypatch.setattr(core_engine, "load_global_config", _fake_load_global_config)
    data = core_engine.load_rag_knowledge()
    assert data == {}
