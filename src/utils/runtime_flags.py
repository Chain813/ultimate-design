"""Global runtime flags consumed across engines and UI.

Usage:
    from src.utils.runtime_flags import is_demo_mode
"""

import streamlit as st


def is_demo_mode() -> bool:
    """Return True when the platform is running with pre-canned demo data or in CLI/bare Python."""
    import os
    if os.getenv("FORCE_REAL_LLM") == "1":
        return False
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx() is None:
            return True
    except Exception:
        return True
    return bool(st.session_state.get("demo_mode", False))


def is_mobile_client() -> bool:
    """Detect if the current request is from a mobile browser using Streamlit context headers.
    
    Returns:
        bool: True if mobile client is detected, False otherwise. Safely degrades to False
              when running outside of an active Streamlit request context.
    """
    import streamlit as st
    try:
        # st.context is available in Streamlit >= 1.35.0/1.55.0
        # Normalize header keys to lowercase to ensure case-insensitive matching
        headers = {k.lower(): v for k, v in st.context.headers.items()}
        user_agent = headers.get("user-agent", "").lower()
        if not user_agent:
            return False
            
        mobile_keywords = ["mobile", "android", "iphone", "ipad", "phone", "mobi", "opera mini", "iemobile"]
        return any(kw in user_agent for kw in mobile_keywords)
    except Exception:
        # Fallback to False outside Streamlit or when context/headers are not accessible
        return False

