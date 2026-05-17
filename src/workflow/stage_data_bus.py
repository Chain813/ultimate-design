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


def require_upstream(current_stage: str, upstream_stage: str, key: str,
                     friendly_name: str = "") -> bool:
    """检查上游阶段数据是否就绪，未就绪时显示阻断提示。

    Returns True if data is available, False if missing (error shown).
    """
    if stage_ready(upstream_stage, key):
        return True

    stage_name = STAGE_MAP.get(upstream_stage, f"Stage {upstream_stage}")
    data_label = friendly_name or key
    st.error(
        f"⛔ **管线前置依赖缺失**\n\n"
        f"当前阶段 (Stage {current_stage}) 需要来自 **{stage_name}** (Stage {upstream_stage}) "
        f"的 **{data_label}** 数据。\n\n"
        f"请先完成 Stage {upstream_stage} 的量化分析，确保数据总线中存在对应产出后再返回本页面。"
    )
    return False


STAGE_MAP = {
    "00": "数据准备",
    "01": "任务解读",
    "02": "资料收集",
    "03": "现场调研",
    "04": "现状分析",
    "05": "问题诊断",
    "06": "目标定位",
    "07": "设计策略",
    "08": "总体城市设计",
    "09": "专项系统设计",
    "10": "重点地段深化",
    "11": "实施路径",
    "12": "城市设计导则",
    "13": "成果表达",
    "14": "视频生成",
    "15": "AIGC设计推演"
}

def render_evidence_chain_bar(current_stage: str, required_stages: list[str]):
    """渲染增强型功能胶囊进度条，支持点击跳转页面。"""
    completed = list_completed_stages()
    pills = []
    for code in required_stages:
        done = code in completed
        is_current = code == current_stage
        name = STAGE_MAP.get(code, "未知阶段")
        
        # 修正：Streamlit 默认会自动剥离 "01_" 这种数字前缀
        # 所以跳转路径应直接使用阶段名称
        import urllib.parse
        page_slug = urllib.parse.quote(name)
        
        cls = "ec-current" if is_current else ("ec-done" if done else "ec-pending")
        
        # 构造 HTML
        label_html = f'<span class="ec-num">{code}</span><span class="ec-divider"></span><span class="ec-name">{name}</span>'
        
        pill_html = f'<a href="/{page_slug}" target="_self" style="text-decoration:none;"><div class="ec-pill {cls}">{label_html}</div></a>'
        pills.append(pill_html)

    # 构造完整的 HTML 并压缩
    html_container = f'<div class="evidence-chain">{"".join(pills)}</div>'
    style_html = """
        <style>
        .evidence-chain { 
            display: flex; 
            align-items: center; 
            gap: 12px; 
            margin: 16px 0 24px 0; 
            flex-wrap: wrap; 
        }
        .ec-pill { 
            display: flex;
            align-items: center;
            padding: 4px 12px; 
            border-radius: 100px; 
            font-size: 13px; 
            transition: all 0.2s ease;
            cursor: pointer;
            border: 1px solid transparent;
            white-space: nowrap;
        }
        .ec-num { 
            font-weight: 800; 
            opacity: 0.9;
        }
        .ec-divider {
            width: 1px;
            height: 12px;
            background: currentColor;
            margin: 0 8px;
            opacity: 0.3;
        }
        .ec-name { 
            font-weight: 500;
        }
        
        .ec-done { 
            background: rgba(34, 197, 94, 0.12); 
            color: #4ade80; 
            border-color: rgba(34, 197, 94, 0.3); 
        }
        .ec-done:hover {
            background: rgba(34, 197, 94, 0.2); 
            transform: translateY(-1px);
        }
        
        .ec-current { 
            background: rgba(129, 140, 248, 0.2); 
            color: #a5b4fc; 
            border-color: rgba(129, 140, 248, 0.6); 
            box-shadow: 0 4px 12px rgba(129, 140, 248, 0.25);
        }
        
        .ec-pending { 
            background: rgba(148, 163, 184, 0.08); 
            color: #94a3b8; 
            border-color: rgba(148, 163, 184, 0.15); 
        }
        .ec-pending:hover {
            background: rgba(148, 163, 184, 0.15); 
            transform: translateY(-1px);
        }
        </style>
    """
    # 强制单行化，防止 Markdown 误解析
    full_html = "".join(line.strip() for line in (html_container + style_html).split("\n"))
    st.markdown(full_html, unsafe_allow_html=True)
