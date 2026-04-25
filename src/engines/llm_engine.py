"""LLM engine: local Ollama chat with streaming and RAG-augmented prompts.

Usage:
    from src.engines.llm_engine import call_llm_engine, call_llm_engine_stream
"""

import json as _json
import logging
import time

import requests

from src.config.loader import load_global_config
from src.engines.rag_engine import retrieve_rag_context
from src.utils.runtime_flags import is_demo_mode

logger = logging.getLogger("ultimateDESIGN")

# ═══════════════════════════════════════════
# Demo-mode canned responses
# ═══════════════════════════════════════════

_DEMO_RESPONSES = {
    "老王": (
        "【思考过程】作为在铁北住了三十年的老居民，我首先想到的是这个方案会不会影响我们日常买菜、接孩子。"
        "其次我担心施工期间噪音和粉尘问题，毕竟这里老人孩子多。最后我关心拆迁补偿是否合理，不能让老百姓吃亏。\n\n"
        "【正式回复】我觉得改造是好事，但你们得先把老百姓的生活安排好。我家门口那棵老榆树可不能砍，那是我们几代人的记忆。"
        "还有，别光想着搞商业，我们需要的是菜市场、社区医院这些实实在在的东西。"
        "施工的时候能不能分期搞，别一下子把路全封了，我们出门都成问题。"
    ),
    "赵总": (
        "【思考过程】从商业角度分析，这个地段紧邻伪满皇宫景区，日均客流量可观。"
        "我需要评估容积率能否支撑投资回报，首层商业租金预期，以及周边竞品项目的定价策略。"
        "关键是要找到文化IP与商业变现的平衡点。\n\n"
        "【正式回复】这个项目的核心价值在于文旅融合。我建议首层全部做沿街商业，引入文创品牌和特色餐饮，"
        "租金可以比周边高出30%。二层以上做精品民宿或联合办公，提升坪效。"
        "但前提是容积率不能低于2.0，否则投资回收期太长，资本不会进来。我们可以用历史建筑的外壳包装现代商业内核。"
    ),
    "李工": (
        "【思考过程】根据《历史文化名城保护条例》和长春市总体规划，这个区域属于风貌协调区，"
        "建筑高度和风格都有严格管控。我需要平衡保护与发展的关系，确保中轴线视廊不被遮挡，"
        "同时满足居民改善生活条件的合理诉求。\n\n"
        "【正式回复】从规划专业角度，我建议采用'微介入、轻改造'策略。"
        "第一，严格控制新建建筑高度在12米以下，保护伪满皇宫的天际线视廊。"
        "第二，采用'修旧如旧'原则修缮历史建筑，保留红砖灰瓦的满洲风貌特征。"
        "第三，通过口袋公园和街角绿地的植入，提升公共空间品质。"
        "商业开发可以有，但必须服从上位规划的风貌管控要求。"
    ),
}

_DEFAULT_DEMO = (
    "【思考过程】综合分析各方诉求，需要在历史保护、商业可行性和民生改善之间寻找平衡。\n\n"
    "【正式回复】建议采取渐进式更新策略，优先改善基础设施和公共空间，"
    "在保护历史风貌的前提下适度引入商业功能，确保居民利益不受损害。"
)


def _select_demo_response(system_prompt: str) -> str:
    for key, resp in _DEMO_RESPONSES.items():
        if key in system_prompt:
            return resp
    return _DEFAULT_DEMO


# ═══════════════════════════════════════════
# Ollama API callers
# ═══════════════════════════════════════════

def call_llm_engine(prompt: str, system_prompt: str = "你是一位专业的城市规划专家。",
                    model: str = "gemma4:e2b-it-q4_K_M") -> str:
    """Call local Ollama engine (non-streaming). Falls back to demo responses."""
    if is_demo_mode():
        return _select_demo_response(system_prompt)

    system_prompt = _augment_with_rag(prompt, system_prompt)
    config = load_global_config()
    url = config.get("engines", {}).get("llm", {}).get("ollama_url", "http://127.0.0.1:11434/api/chat")
    model = config.get("engines", {}).get("llm", {}).get("default_model", model)
    timeout_val = config.get("engines", {}).get("llm", {}).get("timeout", 120)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "options": {"num_ctx": 8192},
        "stream": False,
    }

    for attempt in range(2):
        try:
            response = requests.post(url, json=payload, timeout=timeout_val)
            if response.status_code == 200:
                return response.json().get("message", {}).get("content", "")
            return f"Ollama 报错: {response.status_code} - {response.text}"
        except requests.exceptions.ConnectionError:
            if attempt == 0:
                time.sleep(3)
        except Exception as e:
            logger.warning("Ollama call failed", exc_info=True)
            return f"无法连接到 Ollama 服务，请确认已在终端运行: ollama run {model}"

    return f"无法连接到 Ollama 服务，请确认已在终端运行: ollama run {model}"


def call_llm_engine_stream(prompt: str, system_prompt: str = "你是一位专业的城市规划专家。",
                           model: str = "gemma4:e2b-it-q4_K_M"):
    """Call local Ollama engine (streaming generator). Falls back to character-by-character demo."""
    if is_demo_mode():
        text = _select_demo_response(system_prompt)

        def _demo_gen():
            for char in text:
                yield char
                time.sleep(0.02)

        return _demo_gen()

    system_prompt = _augment_with_rag(prompt, system_prompt)
    config = load_global_config()
    url = config.get("engines", {}).get("llm", {}).get("ollama_url", "http://127.0.0.1:11434/api/chat")
    model = config.get("engines", {}).get("llm", {}).get("default_model", model)
    timeout_val = config.get("engines", {}).get("llm", {}).get("timeout", 120)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "options": {"num_ctx": 8192},
        "stream": True,
    }

    def _stream_gen():
        try:
            response = requests.post(url, json=payload, timeout=(5, timeout_val), stream=True)
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        chunk = _json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            yield token
            else:
                yield f"Ollama 报错: {response.status_code} - {response.text}"
        except requests.exceptions.ConnectionError:
            yield f"无法连接到 Ollama 服务，请确认已在终端运行: ollama run {model}"
        except Exception as e:
            logger.warning("Ollama stream call failed", exc_info=True)
            yield f"LLM 引擎异常: {str(e)}"

    return _stream_gen()


def _augment_with_rag(prompt: str, system_prompt: str) -> str:
    """Append top RAG chunks to system prompt."""
    best_chunks = retrieve_rag_context(prompt, top_k=3)
    if best_chunks:
        top_context = "\n\n".join(f"[{c[2]}]: {c[1]}" for c in best_chunks)
        system_prompt += f"\n\n【本地长春市法规与条例检索库片段，请严格以此时空限定背景作答】：\n{top_context}"
    return system_prompt
