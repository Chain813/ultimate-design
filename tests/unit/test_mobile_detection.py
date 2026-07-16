from unittest.mock import MagicMock, patch
from src.utils.runtime_flags import is_mobile_client


def test_is_mobile_client_outside_streamlit():
    # Outside Streamlit context (or when st.context raises AttributeError/RuntimeError)
    # is_mobile_client should handle exceptions and return False
    assert is_mobile_client() is False


def test_is_mobile_client_various_user_agents():
    # Test mobile user agents
    mobile_uas = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/605.1.15",
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/605.1.15",
        "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
    ]
    
    # Test desktop user agents
    desktop_uas = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    ]

    for ua in mobile_uas:
        mock_context = MagicMock()
        mock_context.headers = {"User-Agent": ua}
        with patch("streamlit.context", mock_context):
            assert is_mobile_client() is True, f"Failed for mobile UA: {ua}"

    for ua in desktop_uas:
        mock_context = MagicMock()
        mock_context.headers = {"User-Agent": ua}
        with patch("streamlit.context", mock_context):
            assert is_mobile_client() is False, f"Failed for desktop UA: {ua}"


def test_is_mobile_client_missing_or_empty_headers():
    mock_context = MagicMock()
    mock_context.headers = {}
    with patch("streamlit.context", mock_context):
        assert is_mobile_client() is False

    mock_context_none = MagicMock()
    mock_context_none.headers = {"user-agent": None}
    with patch("streamlit.context", mock_context_none):
        assert is_mobile_client() is False
