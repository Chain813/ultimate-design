"""阶段研究小结组件 —— 每个阶段页面底部的专业结论面板。

面向答辩委员会，用城乡规划专业术语输出当前阶段的核心发现。
"""

from __future__ import annotations

from html import escape

import streamlit as st
from src.ui.design_system import load_design_css


def render_stage_summary(
    stage_code: str,
    title: str,
    findings: list[dict],
    methodology: str = "",
    implication: str = "",
):
    """渲染阶段研究小结面板。

    Parameters
    ----------
    stage_code : str
        阶段编号，如 "01"。
    title : str
        小结标题，如 "前期问题诊断小结"。
    findings : list[dict]
        核心发现列表。每项包含:
        - ``point``  (str): 结论要点
        - ``evidence`` (str): 数据依据
        - ``chart`` (fig | None): 可选 Plotly 图表
    methodology : str
        方法论说明，如 "基于 AHP-MPI 多维潜力指数模型"。
    implication : str
        后续影响说明，如 "为后续设计策略提供了定量依据"。
    """
    load_design_css()

    findings_html = ""
    chart_figures = []
    for idx, item in enumerate(findings):
        findings_html += (
            '<div class="summary-finding">'
            f'<div class="finding-badge">{idx + 1}</div>'
            f'<div class="finding-body">'
            f'<div class="finding-point">{escape(str(item.get("point", "")))}</div>'
            f'<div class="finding-evidence">{escape(str(item.get("evidence", "")))}</div>'
            f'</div></div>'
        )
        if item.get("chart"):
            chart_figures.append(item["chart"])

    method_html = ""
    if methodology:
        method_html = f'<div class="summary-method">方法：{escape(methodology)}</div>'

    impl_html = ""
    if implication:
        impl_html = f'<div class="summary-implication">→ {escape(implication)}</div>'

    st.markdown(
        f"""
        <section class="stage-summary-panel">
            <div class="stage-summary-head">
                <span class="stage-summary-code">{escape(stage_code)}</span>
                <h3>{escape(title)}</h3>
            </div>
            {method_html}
            <div class="stage-summary-findings">{findings_html}</div>
            {impl_html}
        </section>
        <style>
        .stage-summary-panel {{
            background: linear-gradient(135deg, rgba(99,102,241,0.06), rgba(52,211,153,0.04));
            border: 1px solid rgba(99,102,241,0.2);
            border-radius: 16px;
            padding: 24px 28px;
            margin: 32px 0 16px 0;
        }}
        .stage-summary-head {{
            display: flex; align-items: center; gap: 12px; margin-bottom: 16px;
        }}
        .stage-summary-head h3 {{
            margin: 0; font-size: 18px; font-weight: 800; color: #e2e8f0;
        }}
        .stage-summary-code {{
            background: rgba(129,140,248,0.2);
            color: #a5b4fc;
            padding: 4px 12px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 800;
            letter-spacing: 0.05em;
        }}
        .stage-summary-method {{
            color: #94a3b8; font-size: 13px; margin-bottom: 14px;
            padding-left: 4px; border-left: 3px solid rgba(129,140,248,0.3);
            padding: 2px 0 2px 12px;
        }}
        .stage-summary-findings {{
            display: flex; flex-direction: column; gap: 12px;
        }}
        .summary-finding {{
            display: flex; gap: 12px; align-items: flex-start;
        }}
        .finding-badge {{
            min-width: 28px; height: 28px;
            background: rgba(129,140,248,0.15);
            color: #a5b4fc;
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 13px; font-weight: 800;
        }}
        .finding-point {{
            color: #e2e8f0; font-size: 14px; font-weight: 600; line-height: 1.5;
        }}
        .finding-evidence {{
            color: #94a3b8; font-size: 12px; margin-top: 2px; line-height: 1.5;
        }}
        .stage-summary-implication {{
            color: #34d399; font-size: 13px; font-weight: 600;
            margin-top: 16px; padding-top: 12px;
            border-top: 1px solid rgba(52,211,153,0.15);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 渲染附带的图表
    for fig in chart_figures:
        st.plotly_chart(fig, use_container_width=True)


def generate_stage_summary_text(
    stage_code: str,
    stage_name: str,
    data_context: str,
    model: str = "gemma4:e2b-it-q4_K_M",
) -> str:
    """调用本地 Gemma 4 生成阶段小结文字。

    Parameters
    ----------
    stage_code : str
        阶段编号。
    stage_name : str
        阶段名称。
    data_context : str
        本阶段的数据上下文（如 MPI 结果、POI 统计等）。
    model : str
        Gemma 模型标签。

    Returns
    -------
    str
        生成的小结文字。
    """
    from src.engines.llm_engine import call_llm_engine

    prompt = f"""你是城乡规划专业毕业设计的答辩评审专家。
请根据以下"{stage_name}"阶段的数据分析结果，撰写一段精炼的阶段研究小结。

要求：
1. 使用城乡规划专业术语，语言简洁精炼
2. 列出 3-5 条核心发现，每条必须引用具体数据
3. 最后一句说明本阶段结论对后续设计的支撑作用
4. 总字数控制在 200-300 字

数据上下文：
{data_context[:3000]}
"""
    sys_prompt = "你是城乡规划专业答辩委员会成员，擅长用专业术语撰写精炼的研究小结。禁止使用技术代码术语。"

    try:
        result = call_llm_engine(prompt=prompt, system_prompt=sys_prompt, model=model)
        return result if isinstance(result, str) and len(result) > 30 else ""
    except Exception:
        return ""
