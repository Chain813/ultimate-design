"""跨阶段数据总线 —— 统一管理 13 阶段之间的数据传递。

所有阶段产出均存放在 ``st.session_state["stage_bus"]`` 字典中，
键名格式为 ``"{stage_code}_{key}"``。
"""

from __future__ import annotations

import streamlit as st


def _bus() -> dict:
    if "stage_bus" not in st.session_state:
        st.session_state["stage_bus"] = {}
    return st.session_state["stage_bus"]


def save_stage_output(stage_code: str, key: str, data):
    """将本阶段的产出存入总线，供下游阶段读取。"""
    _bus()[f"{stage_code}_{key}"] = data


def load_stage_output(stage_code: str, key: str, default=None):
    """从总线读取上游阶段的产出。"""
    return _bus().get(f"{stage_code}_{key}", default)


def stage_ready(stage_code: str, key: str) -> bool:
    """判断指定阶段是否已产出某项数据。"""
    return f"{stage_code}_{key}" in _bus()


def list_completed_stages() -> list[str]:
    """返回当前已有产出的阶段编号列表（去重排序）。"""
    codes = {k.split("_", 1)[0] for k in _bus()}
    return sorted(codes)


def render_evidence_chain_bar(current_stage: str, required_stages: list[str]):
    """渲染五阶段证据链进度条，标记哪些上游已就绪。"""
    completed = list_completed_stages()
    pills = []
    for code in required_stages:
        done = code in completed
        is_current = code == current_stage
        cls = "ec-current" if is_current else ("ec-done" if done else "ec-pending")
        label = f"{code}"
        pills.append(f'<span class="ec-pill {cls}">{label}</span>')

    st.markdown(
        '<div class="evidence-chain">' + "→".join(pills) + "</div>"
        + """<style>
        .evidence-chain { display:flex; align-items:center; gap:6px; margin:12px 0 18px 0; flex-wrap:wrap; }
        .ec-pill { padding:5px 14px; border-radius:20px; font-size:13px; font-weight:700; }
        .ec-done { background:rgba(52,211,153,0.18); color:#34d399; border:1px solid rgba(52,211,153,0.35); }
        .ec-current { background:rgba(129,140,248,0.22); color:#a5b4fc; border:1px solid rgba(129,140,248,0.5); box-shadow:0 0 12px rgba(129,140,248,0.3); }
        .ec-pending { background:rgba(148,163,184,0.08); color:#64748b; border:1px solid rgba(148,163,184,0.2); }
        </style>""",
        unsafe_allow_html=True,
    )
