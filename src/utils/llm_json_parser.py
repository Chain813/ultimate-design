"""LLM JSON parser: robust extraction of JSON content from text.

Usage:
    from src.utils.llm_json_parser import parse_llm_json
"""

import json
import re
import logging

logger = logging.getLogger("ultimateDESIGN")

def parse_llm_json(text: str, fallback=None):
    """Robustly extracts and parses JSON object/array from LLM text.
    
    Supports:
    - Raw JSON strings
    - JSON enclosed in ```json ... ``` blocks
    - JSON enclosed in ``` ... ``` blocks
    - Any substring starting with { and ending with } or starting with [ and ending with ]
    """
    if fallback is None:
        fallback = {}
        
    if not text or not isinstance(text, str):
        return fallback

    text = text.strip()
    
    # 1. Try direct parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
        
    # 2. Try extracting from markdown code blocks
    markdown_patterns = [
        r"```json\s*([\s\S]*?)\s*```",
        r"```\s*([\s\S]*?)\s*```"
    ]
    for pattern in markdown_patterns:
        match = re.search(pattern, text)
        if match:
            block_content = match.group(1).strip()
            try:
                return json.loads(block_content)
            except json.JSONDecodeError:
                pass

    # 3. Search for first { and last } or first [ and last ]
    # Find matching braces
    obj_match = re.search(r"(\{[\s\S]*\})", text)
    if obj_match:
        try:
            return json.loads(obj_match.group(1))
        except json.JSONDecodeError:
            pass

    arr_match = re.search(r"(\[[\s\S]*\])", text)
    if arr_match:
        try:
            return json.loads(arr_match.group(1))
        except json.JSONDecodeError:
            pass

    logger.warning(f"Failed to parse JSON from LLM output. Raw content: {text[:200]}...")
    return fallback
