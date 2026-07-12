from tools.generate_policy_a3_diagrams import (
    FORBIDDEN_REAL_MAP_TERMS,
    build_sheet_specs,
    load_policy_content,
    spec_uses_real_map_terms,
)


def test_load_policy_content_reads_utf8_chinese():
    content = load_policy_content()

    assert content["title"] == "政经良性循环与实施政策策划"
    assert content["loop_nodes"][0]["role"] == "政府"


def test_build_sheet_specs_use_chinese_strategy_content():
    content = load_policy_content()

    specs = build_sheet_specs(content)

    assert len(specs) == 4
    assert specs[0]["title"] == "三方良性循环机制图"
    assert "政府" in specs[0]["nodes"][0]["label"]
    assert "财政奖补" in specs[1]["rows"][0]
    assert all(len(spec["modules"]) >= 4 for spec in specs)


def test_sheet_specs_do_not_use_real_map_terms():
    specs = build_sheet_specs(load_policy_content())

    assert FORBIDDEN_REAL_MAP_TERMS
    assert all(not spec_uses_real_map_terms(spec) for spec in specs)
