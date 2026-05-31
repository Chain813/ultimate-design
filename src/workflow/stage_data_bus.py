"""跨阶段数据总线 —— 统一管理 13 阶段之间的数据传递。

所有阶段产出均存放在 ``st.session_state["stage_bus"]`` 字典中，
键名格式为 ``"{stage_code}_{key}"``。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import streamlit as st
from src.config.runtime import resolve_path

logger = logging.getLogger("ultimateDESIGN")


def _get_cache_path() -> Path:
    cache_path = resolve_path("output/stage_bus_cache.json")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    return cache_path


def _save_cache_to_disk(bus_dict: dict):
    try:
        cache_path = _get_cache_path()
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(bus_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to write stage data bus cache: {e}")


def _load_cache_from_disk() -> dict:
    try:
        cache_path = _get_cache_path()
        if cache_path.exists():
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception as e:
        logger.warning(f"Failed to load stage data bus cache from disk: {e}")
    return {}


def _bus() -> dict:
    if "stage_bus" not in st.session_state:
        st.session_state["stage_bus"] = _load_cache_from_disk()
    return st.session_state["stage_bus"]


def save_stage_output(stage_code: str, key: str, data):
    """将本阶段的产出存入总线，供下游阶段读取。"""
    bus_dict = _bus()
    bus_dict[f"{stage_code}_{key}"] = data
    _save_cache_to_disk(bus_dict)


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

    # ═══════════════════════════════════════════
    # AI 规划管线交接说明 (Stage Transition Agent)
    # ═══════════════════════════════════════════
    # 排除数据准备阶段 00
    if current_stage != "00":
        with st.expander("📋 AI 规划管线交接说明", expanded=False):
            cache_key = f"transition_summary_{current_stage}"
            if cache_key not in st.session_state:
                st.session_state[cache_key] = ""
                
            if st.session_state[cache_key] == "":
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.caption("✨ AI 正在自动分析上游所有阶段的产出数据，提炼核心结论与本阶段的设计任务红线。")
                with c2:
                    if st.button("🧠 提取并生成行动指南", key=f"btn_transition_{current_stage}", use_container_width=True):
                        with st.spinner("AI 正在深度解析上游决策链条..."):
                            summary = generate_stage_transition_summary(current_stage)
                            st.session_state[cache_key] = summary
                            st.rerun()
            else:
                st.markdown(st.session_state[cache_key])
                if st.button("🔄 重新提取生成", key=f"btn_re_transition_{current_stage}"):
                    st.session_state[cache_key] = ""
                    st.rerun()


def generate_stage_transition_summary(current_stage: str) -> str:
    """LLM 自动汇总前序阶段产出，为当前阶段生成工作交接行动指南。"""
    from src.engines.llm_engine import call_llm_engine
    
    bus_data = _bus()
    upstream_text = []
    
    # 提取所有小于当前阶段的产出
    for key, val in sorted(bus_data.items()):
        parts = key.split("_", 1)
        stage_prefix = parts[0]
        if stage_prefix.isdigit() and current_stage.isdigit():
            if int(stage_prefix) < int(current_stage):
                val_str = str(val)
                if len(val_str) > 1000:
                    val_str = val_str[:1000] + "...(已截断)"
                key_name = parts[1] if len(parts) > 1 else key
                upstream_text.append(f"【Stage {stage_prefix} - {key_name}】:\n{val_str}")
                
    if not upstream_text:
        return "💡 **前序数据未就绪**：暂无充足的上游阶段数据产出。请先按顺序完成前序页面的量化分析以解锁智能工作衔接。"
        
    upstream_ctx = "\n\n".join(upstream_text)
    current_name = STAGE_MAP.get(current_stage, f"Stage {current_stage}")
    
    prompt = f"""
    你是一位资深的城市设计项目经理。目前项目已进行到【Stage {current_stage}: {current_name}】。
    
    以下是前序阶段的全部关键产出：
    {upstream_ctx}
    
    请根据这些上游数据，为即将开始的【Stage {current_stage}】生成一份 300 字左右的精炼工作交接及行动指南。
    
    要求：
    1. 💡 核心交接结论：从上游成果中提炼出最核心的 2-3 个对本阶段有直接指导意义的量化结论或策略决策。
    2. 🎯 本阶段核心目标：明确说明在本阶段需要达成什么空间设计或诊断指标。
    3. ⚠️ 关键约束：指出本阶段需要死守的红线（如限高、容积率或历史保护要素）。
    
    输出请使用简洁专业的规划行业术语。
    """
    
    return call_llm_engine(
        prompt=prompt, 
        system_prompt="你是一位资深的城市设计项目经理，善于跨阶段整合规划策略。", 
        model="deepseek-v4-flash"
    )


def save_stage_summary_to_file(
    stage_code: str,
    title: str,
    methodology: str,
    findings: list[dict],
    implication: str,
    ai_summary: str = ""
):
    """将当前阶段的方法论、核心发现及 AI 小结写入本地的汇总报告文档中，支持增量更新并按阶段编号排序。"""
    import os
    import re
    from pathlib import Path
    from src.config.runtime import resolve_path
    
    # 确定输出文件路径
    report_path = resolve_path("output/stage_generation_report.md")
    
    # 确保 output 目录存在
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 构建当前阶段的 Markdown 文本块
    findings_lines = []
    for idx, item in enumerate(findings):
        point = item.get("point", "").strip()
        evidence = item.get("evidence", "").strip()
        if point:
            line = f"{idx + 1}. **{point}**"
            if evidence:
                line += f" *(依据: {evidence})*"
            findings_lines.append(line)
    
    findings_str = "\n".join(findings_lines) if findings_lines else "*暂无核心发现*"
    
    ai_summary_section = ""
    if ai_summary:
        ai_summary_section = f"\n\n### 🧠 AI 答辩小结\n{ai_summary.strip()}"
        
    stage_section = f"""## 📌 Stage {stage_code}: {title}
- **方法/方法论**: {methodology or '无'}
- **后续影响**: {implication or '无'}

### 🔍 核心发现
{findings_str}{ai_summary_section}"""

    # 读取已有文档内容，解析已有的阶段数据
    sections = {}
    header_text = (
        "# UltimateDESIGN 城市设计大屏 - 阶段生成汇总报告\n\n"
        "本报告自动记录了在本次运行进程中，各个规划设计阶段所完成的完整生成内容、总结与方法论。\n\n"
        "*(注：本文件由系统自动维护，按阶段顺序增量更新)*\n"
    )
    
    if report_path.exists():
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 使用正则拆分已有的阶段块
            parts = re.split(r"\n*(?=## 📌 Stage \d+:)", content)
            
            # 保留头部
            if parts and not parts[0].startswith("## 📌 Stage"):
                header_text = parts[0].strip() + "\n\n"
                parts = parts[1:]
                
            for part in parts:
                match = re.match(r"## 📌 Stage (\d+):", part)
                if match:
                    code = match.group(1)
                    sections[code] = part.strip()
        except Exception as e:
            import logging
            logger = logging.getLogger("ultimateDESIGN")
            logger.warning("Failed to parse existing stage summaries report: %s", e)

    # 用当前阶段的最新内容覆盖或写入
    sections[stage_code] = stage_section.strip()
    
    # 按阶段编号排序重新拼接
    sorted_codes = sorted(sections.keys(), key=lambda x: int(x) if x.isdigit() else 99)
    
    full_report = header_text
    for code in sorted_codes:
        full_report += sections[code] + "\n\n"
        
    # 写入文件
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(full_report.strip() + "\n")
    except Exception as e:
        import logging
        logger = logging.getLogger("ultimateDESIGN")
        logger.error("Failed to write stage summaries report to file: %s", e)
