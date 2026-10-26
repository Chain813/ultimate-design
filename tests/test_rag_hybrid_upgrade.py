"""Unit tests for the upgraded Hybrid RAG Engine, Contextual Chunker, and De-hardcoded Prompts."""

import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.engines.contextual_chunker import (
    AcademicContextualChunker,
    clean_pdf_noise,
    recursive_character_chunking,
)
from src.engines.rag_engine import (
    FastDenseEmbeddingFunction,
    add_custom_document,
    classify_chunk_scope,
    clear_custom_documents,
    expand_query_terms,
    retrieve_rag_context,
    tokenize_text,
)
from src.engines.llm_engine import _augment_with_rag, _resolve_api_model
from src.engines.spatial_data_injector import _build_dynamic_landuse_judgment, get_landuse_summary
from src.engines.guideline_prompt import build_expansion_prompt, build_guideline_prompt
from tools.rebuild_rag import chunk_text


def test_clean_pdf_noise_and_sentence_protection():
    """Verify PDF noise stripping, float protection (1.4, 25.05), legal clauses, and landuse codes."""
    raw = (
        "伪满皇宫是清朝末代皇帝宫廷旧址。\n"
        "_乴Ba\x0f壛z?\n"
        "2\n"
        "第十三条第一款规定：核心保护区容积率不超过 1.4，规划总用地面积约为 25.05 公顷。"
        "其中 R2 二类居住用地与 B1 商业服务业设施用地混合比例不少于 30%，严格执行 GB/T 50137 标准。\n"
        "实施城市更新\n行动是重要举措。"
    )
    cleaned = clean_pdf_noise(raw)
    assert "_乴Ba" not in cleaned
    assert "\x0f" not in cleaned

    chunker = AcademicContextualChunker()
    sentences = chunker._protect_and_split_sentences(raw)
    joined = " | ".join(sentences)
    # Floats and codes must not be split at the decimal point
    assert "1.4" in joined
    assert "25.05" in joined
    assert "第十三条第一款" in joined
    assert "R2" in joined and "B1" in joined
    # PDF de-wrapping should join "实施城市更新\n行动"
    assert "实施城市更新行动" in joined


def test_split_table_with_header_preserves_header():
    """Verify Markdown planning indicator tables preserve header on every split chunk."""
    table_md = "\n".join([
        "表1 地块控制指标一览表",
        "| 地块编号 | 用地代码 | 容积率上限 | 建筑限高(m) | 绿地率下限 |",
        "| --- | --- | --- | --- | --- |",
        "| A-01 | R2 | 1.4 | 12 | 30% |",
        "| A-02 | B1 | 2.2 | 24 | 20% |",
        "| A-03 | G1 | 0.2 | 9 | 75% |",
        "| A-04 | M1 | 1.8 | 18 | 25% |",
        "| A-05 | R2/B1 | 2.0 | 18 | 28% |",
        "| A-06 | A33 | 1.2 | 15 | 35% |",
    ])
    chunker = AcademicContextualChunker()
    sub_tables = chunker.split_table_with_header(table_md, max_table_len=160)
    assert len(sub_tables) >= 2
    for st_chunk in sub_tables:
        assert "| 地块编号 | 用地代码 | 容积率上限 | 建筑限高(m) | 绿地率下限 |" in st_chunk
        assert "| --- | --- | --- | --- | --- |" in st_chunk


def test_parent_child_chunking_and_recursive_chunker():
    """Verify build_parent_child_index_from_section and recursive_character_chunking."""
    chunker = AcademicContextualChunker(parent_size=400, child_size=150, parent_overlap=40)
    sec_text = (
        "第一章 总则\n\n"
        "第一条 为加强历史文化街区保护与城市更新管理，依据《城乡规划法》制定本导则。"
        "本街区总面积 25.05 公顷，核心保护范围容积率控制在 1.4 以内。\n\n"
        "第二条 街区改造应当遵循留改拆并举、以保留利用提升为主的原则，"
        "严格保护历史建筑风貌与传统街巷肌理，禁止大拆大建。"
    )
    parents, children = chunker.build_parent_child_index_from_section(
        book_meta={"major_code": "national", "subject": "城市更新导则", "book_name": "历史街区导则.pdf"},
        chapter_title="第一章 总则",
        sec_text=sec_text,
        page_start=1,
        page_end=2,
    )
    assert len(parents) >= 1
    assert len(children) >= 1
    assert "【规划精要:" in children[0]["contextual_prefix"]
    assert "25.05" in children[0]["content"] or any("25.05" in c["content"] for c in children)

    rec_chunks = recursive_character_chunking(sec_text, chunk_size=120, chunk_overlap=20)
    assert len(rec_chunks) >= 2


def test_classify_chunk_scope_and_query_expansion():
    """Verify scope classification for national, city_statute, case_thesis, and project_custom."""
    assert classify_chunk_scope("用地用海规范202311.pdf", "")["scope"] == "national"
    assert classify_chunk_scope("中共中央办公厅国务院办公厅关于持续推进城市更新行动的意见.pdf", "")["scope"] == "national"
    assert classify_chunk_scope("控规用地颜色分类.pdf", "")["scope"] == "national"
    assert classify_chunk_scope("伪满皇宫保护规划.pdf", "") == {"scope": "city_statute", "city": "长春"}
    assert classify_chunk_scope("长春市历史文化名城保护条例.pdf", "") == {"scope": "city_statute", "city": "长春"}
    assert classify_chunk_scope("毕业设计任务书.pdf", "")["scope"] == "case_thesis"
    assert classify_chunk_scope("毕业设计开题报告.pdf", "")["scope"] == "case_thesis"
    assert classify_chunk_scope("苏州市平江片区控规.pdf", "", explicit_scope="project_custom")["scope"] == "project_custom"

    expanded = expand_query_terms("FAR 与 TOD 控规指标")
    assert "容积率" in expanded
    assert "公共交通导向开发" in expanded

    tokens = tokenize_text("控制性详细规划容积率不得超过1.4", filter_stopwords=True)
    assert "容积率" in tokens
    assert "的" not in tokens

    fast_ef = FastDenseEmbeddingFunction(dimension=384)
    vecs = fast_ef(["测试容积率与建筑限高向量投影"])
    assert len(vecs) == 1
    assert vecs[0].shape == (384,)


def test_retrieve_rag_context_cross_city_isolation(monkeypatch):
    """Verify that in non-Changchun mode, case_thesis is excluded and Changchun statutes are marked as cross-city precedent."""
    fake_db = {
        "c_thesis": {
            "source": "毕业设计任务书.pdf",
            "content": "长春市宽城区伪满皇宫周边更新毕业设计任务书，容积率1.4。",
        },
        "c_cc_statute": {
            "source": "伪满皇宫保护规划.pdf",
            "content": "伪满皇宫历史文化街区核心保护区限高9米，建设控制地带限高18米。\n_乴Ba\x0f壛z?",
        },
        "c_national": {
            "source": "中共中央办公厅国务院办公厅关于持续推进城市更新行动的意见.pdf",
            "content": "推进老旧街区更新改造，严禁违法违规拆除改造历史文化街区与历史建筑，完善容积率转移或奖励政策。",
        },
    }
    monkeypatch.setattr("src.engines.rag_engine.load_rag_knowledge", lambda: fake_db)
    monkeypatch.setattr("src.engines.rag_engine.load_custom_rag_knowledge", lambda: {})
    monkeypatch.setattr("src.engines.rag_engine.get_cached_db_embeddings", lambda: ({}, fake_db))
    monkeypatch.setattr("src.config.site.get_site_city", lambda: "苏州市")
    monkeypatch.setattr("src.config.site.get_site_name", lambda: "平江历史文化街区")

    try:
        retrieve_rag_context.clear()
    except Exception:
        pass

    results = retrieve_rag_context("历史文化街区 容积率 限高", top_k=3)
    assert len(results) >= 2
    sources = [r[2] for r in results]
    # Graduation thesis must be completely excluded in non-Changchun mode
    assert not any("毕业设计" in s for s in sources)
    # National policy must be ranked #1 (higher than down-weighted cross-city statute)
    assert results[0][2] == "中共中央办公厅国务院办公厅关于持续推进城市更新行动的意见.pdf"
    # Cross-city statute must be prefixed with "异地参考先例:" and have PDF garbage cleaned
    cc_items = [r for r in results if "伪满皇宫保护规划.pdf" in r[2]]
    assert len(cc_items) == 1
    assert cc_items[0][2].startswith("异地参考先例:")
    assert "_乴Ba" not in cc_items[0][1]


def test_add_custom_document_and_retrieval_boost(monkeypatch, tmp_path):
    """Verify add_custom_document chunks, persists, and boosts custom project documents."""
    custom_file = tmp_path / "custom_rag_knowledge.json"
    monkeypatch.setattr("src.engines.rag_engine.resolve_path", lambda p: custom_file if "custom_rag" in str(p) else (ROOT_DIR / p))
    monkeypatch.setattr("src.config.site.get_site_city", lambda: "成都市")
    monkeypatch.setattr("src.config.site.get_site_name", lambda: "祠堂街城市更新单元")

    count = add_custom_document(
        "成都市祠堂街更新控规导则.md",
        "第一条 成都市祠堂街更新单元核心区容积率上限为 2.2，建筑限高 24 米，绿地率不低于 32%。\n"
        "第二条 鼓励首层植入文创商业与策展空间，保护川西传统街巷肌理。",
    )
    assert count >= 1
    assert custom_file.exists()

    results = retrieve_rag_context("祠堂街 容积率 建筑限高", top_k=3)
    assert len(results) >= 1
    assert any("成都市祠堂街更新控规导则.md" in r[2] for r in results)
    assert any("2.2" in r[1] for r in results)

    clear_custom_documents()
    assert not custom_file.exists()


def test_llm_engine_model_mapping_and_rag_prompt_separation(monkeypatch):
    """Verify DeepSeek API model name mapping and _augment_with_rag separation of local vs cross-city chunks."""
    assert _resolve_api_model("https://api.deepseek.com/chat/completions", "deepseek-v4-pro") == "deepseek-chat"
    assert _resolve_api_model("https://api.deepseek.com/chat/completions", "deepseek-v4-flash") == "deepseek-chat"
    assert _resolve_api_model("https://api.deepseek.com/chat/completions", "deepseek-reasoner") == "deepseek-reasoner"
    assert _resolve_api_model("http://localhost:11434/v1/chat/completions", "deepseek-v4-pro") == "deepseek-v4-pro"

    mock_chunks = [
        (0.032, "国家城市更新行动意见：严禁大拆大建。", "中共中央办公厅国务院办公厅关于持续推进城市更新行动的意见.pdf"),
        (0.011, "参考先例导则体例：分三级管控建筑高度。", "异地参考先例:伪满皇宫保护规划.pdf"),
    ]
    monkeypatch.setattr("src.engines.rag_engine.retrieve_rag_context", lambda q, top_k=3: mock_chunks)
    monkeypatch.setattr("src.config.site.get_site_city", lambda: "杭州市")

    aug_sys = _augment_with_rag("历史街区更新策略", "你是规划专家。")
    assert "【国家规范与本地(杭州市)规划条例检索片段（请严格遵守）】" in aug_sys
    assert "【异地同类历史街区参考范例（仅借鉴导则体例与分析方法，严禁照搬其地名与限高/容积率数值）】" in aug_sys


def test_spatial_data_injector_and_guideline_prompt_dehardcoded(monkeypatch):
    """Verify dynamic landuse summary judgment and custom redline injection in guideline prompts."""
    judgment = _build_dynamic_landuse_judgment(
        [("工业仓储用地", 6, 60000.0), ("商业服务业设施用地", 3, 30000.0), ("公园绿地", 1, 5000.0)],
        total_count=10,
        total_area_sqm=95000.0,
    )
    assert "工业仓储用地" in judgment
    assert "居住用地占比过半" not in judgment

    landuse_txt = get_landuse_summary()
    assert "【空间研判】" in landuse_txt
    assert "居住用地占比过半，说明研究范围以老旧居住区为主体；商业服务业与商业办公合计约24%" not in landuse_txt

    # Mock custom non-Changchun site with custom redlines
    monkeypatch.setattr("src.engines.guideline_prompt.get_site_city", lambda: "成都市")
    monkeypatch.setattr("src.engines.guideline_prompt.get_site_district", lambda: "锦江区")
    monkeypatch.setattr("src.engines.guideline_prompt.get_site_name", lambda: "滨水工业遗存更新区")
    monkeypatch.setattr(
        "src.engines.guideline_prompt.get_site_config",
        lambda: {
            "city": "成都市",
            "name": "滨水工业遗存更新区",
            "regulatory_limits": {
                "far": 2.6,
                "height_limit": 36.0,
                "building_density_max": 0.32,
                "greenery_ratio_min": 0.35,
            },
        },
    )

    g_prompt = build_guideline_prompt()
    assert "≤2.6" in g_prompt
    assert "≤36m" in g_prompt
    assert "≤32%" in g_prompt
    assert "≥35%" in g_prompt
    assert "≤1.4" not in g_prompt

    e_prompt = build_expansion_prompt(outline="## 第1章 总则")
    assert "容积率≤2.6" in e_prompt
    assert "≤1.4" not in e_prompt

    # Verify rebuild_rag chunk_text helper
    rebuilt_chunks = chunk_text("第一条 城市更新单元容积率控制在 2.0 以内。\n_乴Ba\x0f壛z?", "测试控规.pdf")
    assert len(rebuilt_chunks) >= 1
    first_chunk = next(iter(rebuilt_chunks.values()))
    assert "_乴Ba" not in first_chunk["content"]
    assert "scope" in first_chunk
