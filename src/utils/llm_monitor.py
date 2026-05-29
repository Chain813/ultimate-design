"""LLM Monitor utility: tracks API calls, latency, estimated tokens for dashboard reporting.

Usage:
    from src.utils.llm_monitor import log_llm_call, get_llm_metrics
"""

import os
import json
import time
from pathlib import Path
import streamlit as st

LOG_FILE = Path("logs/llm_usage.json")

def log_llm_call(model: str, system_prompt: str, prompt: str, response: str, latency: float):
    """Logs an LLM call metric."""
    # Token estimation (rough English/Chinese mix: ~1.5 chars per token for mixed, or 1 token per 2 characters of Chinese, etc. Let's make a reasonable guess)
    input_chars = len(system_prompt or "") + len(prompt or "")
    output_chars = len(response or "")
    
    # Chinese characters take slightly more tokens, let's estimate 1 token ≈ 1.2 characters
    est_prompt_tokens = int(input_chars * 0.8) + 10
    est_completion_tokens = int(output_chars * 0.8) + 5
    total_tokens = est_prompt_tokens + est_completion_tokens
    
    record = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model": model,
        "latency_sec": round(latency, 2),
        "prompt_tokens": est_prompt_tokens,
        "completion_tokens": est_completion_tokens,
        "total_tokens": total_tokens,
    }
    
    # Store in Streamlit session state for live update
    if "llm_metrics" not in st.session_state:
        st.session_state["llm_metrics"] = []
    st.session_state["llm_metrics"].append(record)
    
    # Persist to disk
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        records = []
        if LOG_FILE.exists():
            try:
                records = json.loads(LOG_FILE.read_text(encoding="utf-8"))
            except Exception:
                records = []
        records.append(record)
        # Limit local log to last 500 entries to prevent bloat
        if len(records) > 500:
            records = records[-500:]
        LOG_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        # Silently fail if log directory is write-protected
        pass

def get_llm_metrics():
    """Retrieve all LLM metrics from session state and disk."""
    if "llm_metrics" in st.session_state and st.session_state["llm_metrics"]:
        return st.session_state["llm_metrics"]
        
    if LOG_FILE.exists():
        try:
            records = json.loads(LOG_FILE.read_text(encoding="utf-8"))
            st.session_state["llm_metrics"] = records
            return records
        except Exception:
            pass
            
    return []
