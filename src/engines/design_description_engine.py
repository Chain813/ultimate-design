"""Design Description Engine —— Dynamically generate layout strategies and analysis conclusions for drawing prompts.
"""

import logging
import streamlit as st
from src.engines.llm_engine import call_llm_engine

logger = logging.getLogger("ultimateDESIGN")

def generate_dynamic_design_description(tmpl_name: str, stage_code: str) -> tuple[str, str]:
    """Generates (design_strategy, analysis_conclusion) dynamically via LLM using context from the stage bus.

    Falls back to high-quality default statements if LLM fails or context is missing.
    """
    # Default high-quality fallbacks
    default_strategy = (
        "只生成规划分析覆盖层、符号、箭头、半透明色块和必要标注；底图、红线、重点地块和图框由固定资产锁定。"
        "最终合成顺序固定为：固定底图 -> AI 覆盖层 -> 研究范围红线 -> 重点地块边界 -> 固定图框。"
    )
    default_conclusion = "引用前序阶段数据与上传专题图；信息不完整处使用占位符，不得虚构评价等级、面积或统计数值。"

    try:
        # Collect relevant stage bus info
        bus = st.session_state.get("stage_bus", {})
        context_snippets = []
        for k, v in sorted(bus.items()):
            # Gather up to 3 relevant upstream variables
            if len(context_snippets) >= 3:
                break
            parts = k.split("_", 1)
            if parts[0].isdigit() and int(parts[0]) <= int(stage_code):
                val_str = str(v)
                if len(val_str) > 500:
                    val_str = val_str[:500] + "..."
                context_snippets.append(f"【上游 {k}】: {val_str}")

        upstream_context = "\n".join(context_snippets) if context_snippets else "无上游关联数据"

        prompt = f"""
        基于当前城市设计阶段，为图纸《{tmpl_name}》（阶段 {stage_code}）生成制图渲染策略和数据分析结论描述。
        
        当前上游可用数据上下文：
        {upstream_context}
        
        请生成以下两部分内容：
        1. design_strategy: 用于指导 SD/Image 2.0 渲染的图纸布局与视觉覆盖层逻辑说明（必须规定底图锁定、仅允许 AI 重绘特定规划要素）。
        2. analysis_conclusion: 该图纸所应体现的数据分析结论（如果上游有量化数据如 POI 数、高度、MPI 等，必须将具体数据融入结论中；如果无数据，必须规定引用真实数据，严禁虚构数据）。
        
        请仅返回 JSON 格式结果，不要包含任何 markdown 块或多余文字：
        {{
            "design_strategy": "渲染覆盖层说明...",
            "analysis_conclusion": "数据分析与结论引述..."
        }}
        """

        resp = call_llm_engine(
            prompt=prompt,
            system_prompt="你是一位专业的城市规划制图专家，擅长将数据指标与 AI 制图约束有机结合。",
            model="deepseek-v4-flash"
        )
        
        from src.utils.llm_json_parser import parse_llm_json
        parsed = parse_llm_json(resp, fallback=None)
        if parsed and isinstance(parsed, dict):
            ds = parsed.get("design_strategy", default_strategy)
            ac = parsed.get("analysis_conclusion", default_conclusion)
            return ds, ac
    except Exception as e:
        logger.warning(f"Failed to generate dynamic design description: {e}")

    return default_strategy, default_conclusion
