"""
Unit tests for API Key validator and background silent check.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from src.ui.api_key_validator import (
    validate_deepseek_api_key,
    save_and_persist_api_key,
    silent_check_api_key
)

def test_validate_deepseek_api_key_empty():
    ok, msg = validate_deepseek_api_key("")
    assert not ok
    assert "不能为空" in msg

@patch("requests.post")
def test_validate_deepseek_api_key_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    ok, msg = validate_deepseek_api_key("sk-valid-key-12345")
    assert ok
    assert "验证成功" in msg

@patch("requests.post")
def test_validate_deepseek_api_key_unauthorized(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_post.return_value = mock_resp

    ok, msg = validate_deepseek_api_key("sk-invalid-key")
    assert not ok
    assert "401" in msg

@patch("requests.post")
def test_validate_deepseek_api_key_insufficient_quota(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 402
    mock_post.return_value = mock_resp

    ok, msg = validate_deepseek_api_key("sk-no-balance")
    assert not ok
    assert "额度受限" in msg or "402" in msg

def test_save_and_persist_api_key():
    test_key = "sk-unittest-persist-key"
    save_and_persist_api_key(test_key)
    assert os.environ.get("DEEPSEEK_API_KEY") == test_key
