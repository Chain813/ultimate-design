import json
import sys

from tools.generate_policy_board_content import (
    FALLBACK_POLICY_CONTENT,
    ROOT,
    build_policy_prompt,
    ensure_repo_root_on_path,
    normalize_policy_content,
    write_policy_content,
)


def test_build_policy_prompt_mentions_required_subjects():
    prompt = build_policy_prompt()

    assert "政府" in prompt
    assert "市场" in prompt
    assert "居民" in prompt
    assert "A3" in prompt


def test_normalize_policy_content_accepts_valid_payload():
    payload = {
        "title": "政经良性循环与实施政策策划",
        "subtitle": "政府定规则、市场做运营、居民得收益",
        "loop_nodes": [
            {"role": "政府", "title": "规则与财政引导", "body": "控规弹性与公共投入。"},
            {"role": "市场", "title": "投资与运营导入", "body": "业态更新与收益分成。"},
            {"role": "居民", "title": "参与与收益反馈", "body": "就业增收与社区基金。"},
        ],
        "policy_tools": [
            {"name": "财政奖补", "body": "首期公共空间改造补助。"},
            {"name": "租金分成", "body": "平台公司与运营方共享增量收益。"},
        ],
        "a3_sheets": [
            {
                "file": "a3_policy_01_loop",
                "title": "三方良性循环机制图",
                "caption": "三方权责与收益流向。",
                "prompt": "urban planning policy loop infographic",
            },
            {
                "file": "a3_policy_02_tools",
                "title": "政策工具矩阵图",
                "caption": "政策工具与主体矩阵。",
                "prompt": "policy tools matrix",
            },
            {
                "file": "a3_policy_03_market",
                "title": "市场运营与收益回流图",
                "caption": "运营收益回流。",
                "prompt": "market operation loop",
            },
            {
                "file": "a3_policy_04_residents",
                "title": "居民收益与治理反馈图",
                "caption": "居民收益反馈。",
                "prompt": "resident benefits governance loop",
            },
        ],
    }

    normalized = normalize_policy_content(payload)

    assert normalized["title"] == payload["title"]
    assert len(normalized["loop_nodes"]) == 3
    assert len(normalized["a3_sheets"]) == 4


def test_normalize_policy_content_falls_back_on_missing_keys():
    normalized = normalize_policy_content({"title": "incomplete"})

    assert normalized == FALLBACK_POLICY_CONTENT


def test_write_policy_content_writes_utf8_json(tmp_path):
    output = tmp_path / "policy_board_content.json"

    result = write_policy_content(output, llm_func=lambda *_args, **_kwargs: "not json")

    assert result == FALLBACK_POLICY_CONTENT
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["title"] == FALLBACK_POLICY_CONTENT["title"]


def test_ensure_repo_root_on_path_prepends_root(monkeypatch):
    root = str(ROOT)
    monkeypatch.setattr(sys, "path", [item for item in sys.path if item != root])

    ensure_repo_root_on_path()

    assert sys.path[0] == root
