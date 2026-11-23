"""LLM Monitor utility: tracks API calls, latency, estimated tokens for dashboard reporting.

Usage:
    from src.utils.llm_monitor import log_llm_call, get_llm_metrics
"""

import json
import logging
import os
import time
from pathlib import Path

import streamlit as st

from src.core.runtime_adapter import delete_state, get_state, runtime_state, set_state

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
    
    # Store in runtime state / Streamlit session state for live update (cap at 100 entries)
    st_state = getattr(st, "session_state", None)
    if isinstance(st_state, dict) and "llm_metrics" not in st_state:
        delete_state("llm_metrics")
    if "llm_metrics" not in runtime_state or not isinstance(get_state("llm_metrics"), list):
        set_state("llm_metrics", [])
    metrics_list = list(get_state("llm_metrics") or [])
    metrics_list.append(record)
    if len(metrics_list) > 100:
        metrics_list = metrics_list[-100:]
    set_state("llm_metrics", metrics_list)
    
    # Persist to disk
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        records = []
        if LOG_FILE.exists():
            try:
                records = json.loads(LOG_FILE.read_text(encoding="utf-8"))
            except Exception:
                logging.debug("LLM 日志文件解析失败，重置为空", exc_info=True)
                records = []
        records.append(record)
        # Limit local log to last 500 entries to prevent bloat
        if len(records) > 500:
            records = records[-500:]
        LOG_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        logging.debug("LLM 日志写入失败", exc_info=True)

def get_llm_metrics():
    """Retrieve all LLM metrics from session state and disk."""
    st_state = getattr(st, "session_state", None)
    if isinstance(st_state, dict) and "llm_metrics" not in st_state:
        delete_state("llm_metrics")
    cached = get_state("llm_metrics")
    if cached:
        return cached
        
    if LOG_FILE.exists():
        try:
            records = json.loads(LOG_FILE.read_text(encoding="utf-8"))
            set_state("llm_metrics", records)
            return records
        except Exception:
            pass
            
    return []
