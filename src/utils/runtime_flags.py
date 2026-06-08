"""Global runtime flags consumed across engines and UI.

Usage:
    from src.utils.runtime_flags import is_demo_mode
"""

import streamlit as st


def is_demo_mode() -> bool:
    """Return True when the platform is running with pre-canned demo data or in CLI/bare Python."""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx() is None:
            return True
    except Exception:
        return True
    return bool(st.session_state.get("demo_mode", False))
