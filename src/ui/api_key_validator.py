"""
API Key Validation & Silent Check Manager for UltimateDESIGN.
Provides online HTTP verification, local persistence, and background silent checks.
"""

import os
import logging
from typing import Tuple, Optional
import requests
import streamlit as st

from src.config.user_settings import get_effective_setting, save_user_settings, load_user_settings
from src.ui.project_config_banner import _write_env, ENV_FILE

logger = logging.getLogger(__name__)

DEEPSEEK_DEFAULT_URL = "https://api.deepseek.com/chat/completions"


def validate_deepseek_api_key(
    api_key: str,
    api_url: str = DEEPSEEK_DEFAULT_URL,
    timeout: int = 6
) -> Tuple[bool, str]:
    """
    Sends a lightweight online validation HTTP request to verify if the API Key is active and working.
    """
    cleaned_key = api_key.strip()
    if not cleaned_key:
        return False, "❌ API Key 不能为空！"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cleaned_key}"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
        if response.status_code == 200:
            return True, "✅ API Key 验证成功！密钥有效且余额充沛。"
        elif response.status_code == 401:
            return False, "❌ 验证失败 (401 密钥错误)：API Key 无效，请检查填写的字符是否正确。"
        elif response.status_code in (402, 429):
            return False, f"❌ 验证失败 ({response.status_code} 额度受限)：API 账户余额不足或配额已达上限。"
        else:
            return False, f"❌ 验证失败 (HTTP {response.status_code})：{response.text[:120]}"
    except requests.exceptions.Timeout:
        return False, "❌ 网络超时：无法连接至 DeepSeek 服务器，请检查网络或代理配置。"
    except requests.exceptions.ConnectionError:
        return False, "❌ 网络连接失败：无法到达 API 端点，请检查 Internet 连接。"
    except Exception as e:
        return False, f"❌ 验证过程发生异常：{e!s}"


@st.cache_data(ttl=300)
def silent_check_api_key() -> Tuple[bool, str]:
    """
    Runs a fast background silent check on the currently saved DEEPSEEK_API_KEY.
    Cached for 5 minutes (ttl=300) to prevent redundant HTTP requests during UI navigation.
    """
    current_key = get_effective_setting("DEEPSEEK_API_KEY")
    if not current_key or not current_key.strip():
        return False, "未配置 DEEPSEEK_API_KEY"

    return validate_deepseek_api_key(current_key, timeout=4)


def save_and_persist_api_key(api_key: str) -> bool:
    """
    Saves validated API Key into user settings (~/.ultimatedesign/config.json), .env, and os.environ.
    """
    cleaned = api_key.strip()
    # Save to user settings
    settings = load_user_settings()
    settings["DEEPSEEK_API_KEY"] = cleaned
    save_user_settings(settings)

    # Save to .env
    _write_env({"DEEPSEEK_API_KEY": cleaned})
    os.environ["DEEPSEEK_API_KEY"] = cleaned
    return True


def render_api_key_banner_if_needed() -> bool:
    """
    Checks saved API key status.
    If valid and passes silent check, returns True.
    If missing or invalid, renders the homepage API key entry modal and returns False.
    """
    current_key = get_effective_setting("DEEPSEEK_API_KEY")
    
    # 1. Quick check: If key exists and session_state confirms validity
    if current_key and st.session_state.get("api_key_validated", False):
        return True

    # 2. Run silent background check if key is saved
    if current_key:
        is_valid, msg = silent_check_api_key()
        if is_valid:
            st.session_state["api_key_validated"] = True
            return True
        else:
            logger.warning(f"Background silent check for API key failed: {msg}")

    # 3. If missing or silent check failed, render input card
    st.markdown("---")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
                border: 1px solid #6366f1; border-radius: 16px; padding: 24px 28px; margin-bottom: 16px;">
        <h3 style="color: #818cf8; margin: 0 0 8px 0; font-size: 20px;">
            🔐 DeepSeek AI 智算引擎 — 密钥联机配置与验证
        </h3>
        <p style="color: #94a3b8; margin: 0; font-size: 14px;">
            系统需使用有效的大模型 API 密钥以驱动多主体博弈推演与智能导则生成。首次填写并验证通过后，将加密保存在本地环境，以后无需重复输入，每次启动自动后台静默自检。
        </p>
    </div>
    """, unsafe_allow_html=True)

    input_key = st.text_input(
        "输入 DEEPSEEK_API_KEY",
        value=current_key,
        type="password",
        placeholder="sk-...",
        help="请从 platform.deepseek.com 获取您的 API 密钥",
        key="homepage_api_key_input"
    )

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        if st.button("⚡ 联机验证并保存", type="primary", use_container_width=True):
            if not input_key.strip():
                st.error("请先输入 API 密钥！")
                return False

            with st.spinner("正在向 DeepSeek 云端服务器发起极简联机验证..."):
                ok, message = validate_deepseek_api_key(input_key.strip())

            if ok:
                save_and_persist_api_key(input_key.strip())
                st.session_state["api_key_validated"] = True
                st.success(message)
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error(message)
                return False

    with col_info:
        st.caption("🔒 提示：密钥保存在本地 `~/.ultimatedesign/config.json` 与 `.env`，不会上传至任何第三方服务器。")

    st.warning("⚠️ 请先完成 API 密钥验证，系统后步模块才能正常调用智算推演引擎。")
    return False
