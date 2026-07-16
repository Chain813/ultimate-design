"""Copilot Engine —— Core query processor for the global planning copilot.
"""

import logging

import streamlit as st

from src.config import get_site_city, get_site_desc, get_site_district, get_site_name
from src.engines.llm_engine import call_llm_engine
from src.engines.rag_engine import retrieve_rag_context

logger = logging.getLogger("ultimateDESIGN")

def init_copilot_state():
    """Initialize session state variables for the global sidebar Copilot."""
    if "copilot_history" not in st.session_state:
        st.session_state["copilot_history"] = []
    if "copilot_input" not in st.session_state:
        st.session_state["copilot_input"] = ""


def get_copilot_response(user_msg: str) -> str:
    """Invokes DeepSeek with RAG context and full session chat history.

    Saves the QA exchange to the history list in OpenAI format.
    """
    init_copilot_state()
    history = st.session_state["copilot_history"]

    # 1. Retrieve RAG contexts for grounding
    rag_hits = retrieve_rag_context(user_msg, top_k=4)
    rag_context_str = ""
    if rag_hits:
        rag_context_str = "\n".join(
            f"[*法规来源: {source}*]\n{content}" for _, content, source in rag_hits
        )

    # 2. Gather current stage bus data
    bus = st.session_state.get("stage_bus", {})
    bus_summary = []
    for k, v in sorted(bus.items()):
        val_str = str(v)
        if len(val_str) > 200:
            val_str = val_str[:200] + "..."
        bus_summary.append(f"- {k}: {val_str}")
    bus_ctx = "\n".join(bus_summary) if bus_summary else "暂无已完成的规划阶段数据。"

    site_name = get_site_name()
    city_name = get_site_city()
    district_name = get_site_district()
    site_desc = get_site_desc()

    system_prompt = f"""
    你是一个名为 UltimateDESIGN-Copilot 的顶尖 AI 城市规划助手，常驻在用户的规划平台侧边栏。
    你拥有平台的全部知识、当前方案的最新指标、以及本地规划法规数据库。
    
    【项目基础背景】
    - 项目名称：{city_name}市{district_name}{site_name}城市更新规划设计。
    - 范围及特征：{site_desc}
    - 特色：古今共振、数字孪生、多主体协商。
    
    【当前平台运行的指标数据 (Stage Bus)】
    {bus_ctx}
    
    【检索到的关联法规条例与参考资料 (RAG Context)】
    {rag_context_str}
    
    【跨城市防错规则】
    - 当前项目所属城市为：{city_name}市。
    - 检索到的关联法规可能来自其他城市（例如长春或其他省市）。
    - 凡是检索到的法规、案例中城市与“{city_name}市”不一致的，你必须在回答中以“【提示】以下条款参考自[某城市]，非本市法定标准”的形式进行标注，避免将外地政策错配为本市法定要求。
    
    回答要求：
    1. 紧密结合项目实际，强引用上方给出的法规或平台指标数据。
    2. 态度亲切、专业、精炼，避免大篇幅套话。
    3. 如果用户询问某个特定阶段该干什么，给予具体步骤或指导。
    """

    # 3. Call LLM engine with history
    # The history must be in OpenAI format: [{"role": "user", "content": "..."}]
    # We append the user message to history, call the engine, and then append the response.
    # Note: To avoid sending excessive history, we slice the last 6 messages (3 turns).
    recent_history = history[-6:]
    
    try:
        response = call_llm_engine(
            prompt=user_msg,
            system_prompt=system_prompt,
            history=recent_history,
            model="deepseek-v4-pro"  # Use Pro model for higher quality chat guidance
        )
    except Exception as e:
        logger.error(f"Copilot LLM call failed: {e}")
        response = f"⚠️ 对不起，AI 助理连接超时（{e}）。请检查您的网络设置或 DeepSeek API 密钥。"

    # 4. Commit to history (cap at 50 messages = 25 turns)
    st.session_state["copilot_history"].append({"role": "user", "content": user_msg})
    st.session_state["copilot_history"].append({"role": "assistant", "content": response})
    if len(st.session_state["copilot_history"]) > 50:
        st.session_state["copilot_history"] = st.session_state["copilot_history"][-50:]

    return response
