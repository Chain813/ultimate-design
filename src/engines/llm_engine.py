"""LLM engine: local Ollama / DeepSeek API chat with streaming and RAG-augmented prompts.

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
        "【思考过程】作为在片区居住了几十年的老居民代表，我首先关心的是更新改造是否会影响我们日常买菜、接送孩子、邻里交往与生活便利。"
        "其次我担心施工期间的噪声、粉尘与封闭施工，毕竟社区老少群体较多。最后我关心民生基础设施是否真正落地，不能让居民切身利益受损。\n\n"
        "【正式回复】我觉得改造是好事，但必须先把老百姓的生活日常安置妥当。片区原有的生态大树和邻里情感记忆一定要保留。"
        "另外，不能只顾着搞高大上的商业消费，我们最迫切需要的是便民菜市、适老无障碍健身步道、社区口袋公园这些实实在在的配套。"
        "施工方案应当分期分段推进，绝不能搞一刀切全封闭，保障老百姓的正常出行与日照采光。"
    ),
    "赵总": (
        "【思考过程】从商业与产业投资运营的角度分析，该地段具备良好的场景营造与人流集聚潜力。"
        "核心是算清经济账：平衡容积率与资本回报周期、首层商业坪效、业态客群黏性以及长期资产运营的可持续性。"
        "关键是要找到文化赋能、场景创新与商业变现的最佳契合点。\n\n"
        "【正式回复】这个项目的核心价值在于业态重塑与文商旅居多元融合。建议首层优先打造沿街活力商业、特色主理人文创与轻餐饮，"
        "提升综合坪效；二层及以上结合存量空间打造创客工坊、主理人工作室或特色体验空间。"
        "同时需要适度的规划指标弹性与开发强度支撑，缩短投资回收期，通过市场化可持续运营激发片区自生造血能力。"
    ),
    "李工": (
        "【思考过程】根据国土空间规划、城市设计导则及法定控规要求，本区域必须严格统筹历史文脉保护、限高红线与公共利益底线。"
        "需要在保护传承与活力复兴之间寻求科学平衡，确保天际线舒缓、视线走廊通透，同时满足改善民生与公共空间均等化的刚性要求。\n\n"
        "【正式回复】从城乡规划与城市设计专业角度，我建议采取'微介入、精细针灸、存量提质'的更新策略。"
        "第一，严格执行分级建筑限高与关键视线走廊保护，守护城市特色天际线与文脉骨架。"
        "第二，坚持分类施策，对具有风貌与历史价值的建筑原真性修缮活化，对普通建筑实施渐进式立面整治与节能改造。"
        "第三，织补口袋公园与慢行微循环，提升公共空间生态韧性，商业功能开发必须严格服从法定规划控制红线。"
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
    if any(k in system_prompt for k in ("居民代表", "原住居民", "使用者代表")):
        return _DEMO_RESPONSES["老王"]
    if any(k in system_prompt for k in ("投资开发", "文旅运营", "运营商代表", "商业投资")):
        return _DEMO_RESPONSES["赵总"]
    if any(k in system_prompt for k in ("规划师代表", "法定规划监督", "法定义务人", "规划协调方")):
        return _DEMO_RESPONSES["李工"]
    return _DEFAULT_DEMO


def _resolve_api_model(api_url: str, model: str) -> str:
    """Map logical internal model names to official DeepSeek endpoint model IDs when calling api.deepseek.com."""
    if "api.deepseek.com" in str(api_url or "").lower() and model in ("deepseek-v4-pro", "deepseek-v4-flash"):
        return "deepseek-chat"
    return model


# ═══════════════════════════════════════════
# Ollama / DeepSeek API callers
# ═══════════════════════════════════════════

def call_llm_engine(prompt: str, system_prompt: str = "你是一位专业的城市规划专家。",
                    model: str = "deepseek-v4-pro", history: list | None = None) -> str:
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
        "model": _resolve_api_model(url, model),
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
                           model: str = "deepseek-v4-pro", history: list | None = None):
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
        "model": _resolve_api_model(url, model),
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
            err = f"LLM 引擎异常: {e!s}"
            accumulated = err
            yield err

        latency = time.time() - t0
        from src.utils.llm_monitor import log_llm_call
        log_llm_call(model, system_prompt, prompt, accumulated, latency)

    return _stream_gen()


def _augment_with_rag(prompt: str, system_prompt: str) -> str:
    """Append top RAG chunks to system prompt, separating local/national statutes from cross-city precedents."""
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
        from src.config.site import get_site_city
        city = get_site_city() or "属地"
        local_chunks = [c for c in best_chunks if not str(c[2]).startswith("异地参考先例:")]
        ref_chunks = [c for c in best_chunks if str(c[2]).startswith("异地参考先例:")]

        if local_chunks:
            local_ctx = "\n\n".join(f"[{c[2]}]: {c[1]}" for c in local_chunks)
            system_prompt += f"\n\n【国家规范与本地({city})规划条例检索片段（请严格遵守）】：\n{local_ctx}"
        if ref_chunks:
            ref_ctx = "\n\n".join(f"[{c[2]}]: {c[1]}" for c in ref_chunks)
            system_prompt += (
                "\n\n【异地同类历史街区参考范例（仅借鉴导则体例与分析方法，严禁照搬其地名与限高/容积率数值）】：\n"
                f"{ref_ctx}"
            )
    return system_prompt
