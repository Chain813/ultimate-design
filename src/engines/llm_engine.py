"""LLM engine: local Ollama chat with streaming and RAG-augmented prompts.

Usage:
    from src.engines.llm_engine import call_llm_engine, call_llm_engine_stream
"""

import json as _json
import logging
import os
import time

import requests
from dotenv import load_dotenv

from src.config.loader import load_global_config

load_dotenv()
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
                    model: str = "deepseek-v4-pro", history: list = None) -> str:
    """Call DeepSeek API (non-streaming). Falls back to demo responses."""
    import sys
    if is_demo_mode() or "pytest" in sys.modules:
        return _select_demo_response(system_prompt)

    t0 = time.time()
    # RAG augmentation -- graceful degradation on failure
    try:
        system_prompt = _augment_with_rag(prompt, system_prompt)
    except Exception:
        logger.warning("RAG augmentation failed, proceeding without policy context", exc_info=True)
    config = load_global_config()

    from src.config.user_settings import get_effective_setting
    llm_cfg = config.get("engines", {}).get("llm", {})
    url = get_effective_setting("LLM_API_URL", llm_cfg.get("api_url", "https://api.deepseek.com/chat/completions"))
    timeout_val = llm_cfg.get("timeout", 120)
    api_key = (get_effective_setting("DEEPSEEK_API_KEY"))

    if not api_key:
        return "错误：未配置 DEEPSEEK_API_KEY，请在“系统设置”页面或环境变量中配置。"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }

    max_attempts = 3
    res_text = ""
    for attempt in range(max_attempts):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout_val)
            if response.status_code == 200:
                res_text = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                break
            res_text = f"DeepSeek \u62a5\u9519: {response.status_code} - {response.text}"
            if response.status_code >= 500:
                backoff = min(2 ** attempt, 16)
                logger.warning("DeepSeek server error %d, retry %d/%d in %ds",
                               response.status_code, attempt + 1, max_attempts, backoff)
                time.sleep(backoff)
                continue
            break  # Client errors (4xx) are not retryable
        except requests.exceptions.ConnectionError:
            backoff = min(2 ** attempt, 16)
            logger.warning("DeepSeek connection failed, retry %d/%d in %ds",
                           attempt + 1, max_attempts, backoff)
            time.sleep(backoff)
        except requests.exceptions.Timeout:
            logger.warning("DeepSeek request timed out after %ds", timeout_val)
            res_text = f"DeepSeek API \u8bf7\u6c42\u8d85\u65f6\uff08{timeout_val}s\uff09\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u6216\u589e\u5927 config.yaml \u4e2d\u7684 timeout\u3002"
            break
        except Exception as e:
            logger.warning("DeepSeek call failed", exc_info=True)
            res_text = f"\u65e0\u6cd5\u8fde\u63a5\u5230 DeepSeek API: {e}"
            break

    if not res_text:
        res_text = "\u65e0\u6cd5\u8fde\u63a5\u5230 DeepSeek API\uff0c\u8bf7\u68c0\u67e5\u7f51\u7edc\u6216\u4ee3\u7406\u8bbe\u7f6e\u3002"

    latency = time.time() - t0
    logger.info("LLM call completed: model=%s latency=%.1fs response_len=%d", model, latency, len(res_text))
    from src.utils.llm_monitor import log_llm_call
    log_llm_call(model, system_prompt, prompt, res_text, latency)
    return res_text



def call_llm_engine_stream(prompt: str, system_prompt: str = "你是一位专业的城市规划专家。",
                           model: str = "deepseek-v4-pro", history: list = None):
    """Call DeepSeek API (streaming generator). Falls back to character-by-character demo."""
    import sys
    if is_demo_mode() or "pytest" in sys.modules:
        text = _select_demo_response(system_prompt)

        def _demo_gen():
            accumulated = ""
            for char in text:
                accumulated += char
                yield char
                time.sleep(0.003)
            from src.utils.llm_monitor import log_llm_call
            log_llm_call(model, system_prompt, prompt, accumulated, len(text) * 0.02)

        return _demo_gen()

    t0 = time.time()
    # RAG augmentation -- graceful degradation on failure
    try:
        system_prompt = _augment_with_rag(prompt, system_prompt)
    except Exception:
        logger.warning("RAG augmentation failed in stream mode, proceeding without policy context", exc_info=True)
    config = load_global_config()

    from src.config.user_settings import get_effective_setting
    llm_cfg = config.get("engines", {}).get("llm", {})
    url = get_effective_setting("LLM_API_URL", llm_cfg.get("api_url", "https://api.deepseek.com/chat/completions"))
    timeout_val = llm_cfg.get("timeout", 120)
    api_key = (get_effective_setting("DEEPSEEK_API_KEY"))

    if not api_key:
        def _err_gen():
            yield "错误：未配置 DEEPSEEK_API_KEY，请在“系统设置”页面或环境变量中配置。"
        return _err_gen()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
    }

    def _stream_gen():
        accumulated = ""
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=(5, timeout_val), stream=True)
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            data_str = decoded_line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = _json.loads(data_str)
                                token = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if token:
                                    accumulated += token
                                    yield token
                            except _json.JSONDecodeError:
                                continue
            else:
                err = f"DeepSeek 报错: {response.status_code} - {response.text}"
                accumulated = err
                yield err
        except requests.exceptions.ConnectionError:
            err = "无法连接到 DeepSeek API，请检查网络或代理设置。"
            accumulated = err
            yield err
        except Exception as e:
            logger.warning("DeepSeek stream call failed", exc_info=True)
            err = f"LLM 引擎异常: {str(e)}"
            accumulated = err
            yield err

        latency = time.time() - t0
        from src.utils.llm_monitor import log_llm_call
        log_llm_call(model, system_prompt, prompt, accumulated, latency)

    return _stream_gen()


def _augment_with_rag(prompt: str, system_prompt: str) -> str:
    """Append top RAG chunks to system prompt."""
    from src.engines.rag_engine import retrieve_rag_context
    # Extract proposal if present to keep the RAG search query clean and cacheable
    search_query = prompt
    if "策划议题：" in prompt:
        parts = prompt.split("策划议题：", 1)
        search_query = parts[1].split("\n", 1)[0].strip()
        if not search_query:
            search_query = parts[1][:200].strip()

    best_chunks = retrieve_rag_context(search_query, top_k=3)
    if best_chunks:
        top_context = "\n\n".join(f"[{c[2]}]: {c[1]}" for c in best_chunks)
        system_prompt += f"\n\n【本地长春市法规与条例检索库片段，请严格以此时空限定背景作答】：\n{top_context}"
    return system_prompt
