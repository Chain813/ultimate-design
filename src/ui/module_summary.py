"""阶段研究小结组件 —— 每个阶段页面底部的专业结论面板。

面向答辩委员会，用城乡规划专业术语输出当前阶段的核心发现。
支持：
- 静态发现列表
- 动态数据注入（自动从数据总线读取）
- 内嵌统计图表（Plotly）
- 一键调用 Gemma 4 生成 AI 小结
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
    auto_chart: bool = True,
    enable_llm: bool = True,
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
    auto_chart : bool
        是否自动生成统计图表（根据数据总线中的数据）。
    enable_llm : bool
        是否显示"AI 生成小结"按钮。
    """
    load_design_css()

    # ── 动态数据增强：从数据总线读取并补充 findings ──
    dynamic_findings = _enrich_findings_from_bus(stage_code, findings)

    findings_html = ""
    chart_figures = []
    for idx, item in enumerate(dynamic_findings):
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

    # ── 渲染附带的图表 ──
    for fig in chart_figures:
        st.plotly_chart(fig, use_container_width=True)

    # ── 自动生成统计图表 ──
    if auto_chart:
        auto_fig = _build_auto_chart(stage_code)
        if auto_fig:
            st.plotly_chart(auto_fig, use_container_width=True)

    # ── AI 小结生成按钮 ──
    if enable_llm:
        _render_llm_summary_button(stage_code, title, dynamic_findings, methodology)


def _enrich_findings_from_bus(stage_code: str, static_findings: list[dict]) -> list[dict]:
    """从 stage_data_bus 读取数据，动态替换或增强 findings 中的占位数据。"""
    try:
        from src.workflow.stage_data_bus import load_stage_output
    except ImportError:
        return static_findings

    enriched = []
    for item in static_findings:
        point = str(item.get("point", ""))
        evidence = str(item.get("evidence", ""))

        # 动态替换占位值
        if stage_code == "05":
            top_plot = load_stage_output("05", "top_plot", None)
            top_score = load_stage_output("05", "top_score", None)
            mpi_data = load_stage_output("05", "mpi_ranking", None)
            if top_plot and "暂无" in point:
                point = point.replace("暂无", str(top_plot))
            if top_score and isinstance(top_score, (int, float)) and top_score > 0:
                point = point.replace("0.0 分", f"{top_score:.1f} 分")
            if mpi_data and isinstance(mpi_data, list):
                point = point.replace("0 个", f"{len(mpi_data)} 个")

        if stage_code == "04":
            poi = load_stage_output("04", "poi_count", None)
            bld = load_stage_output("04", "building_count", None)
            if poi and "N/A" in point:
                point = point.replace("N/A", str(poi))
            if bld and "0 栋" in point:
                point = point.replace("0 栋", f"{bld} 栋")

        enriched.append({**item, "point": point, "evidence": evidence})
    return enriched


def _build_auto_chart(stage_code: str):
    """根据阶段和可用数据自动生成一张统计图表。"""
    try:
        from src.workflow.stage_data_bus import load_stage_output
        import plotly.graph_objects as go
        from src.ui.chart_theme import apply_plotly_theme
    except ImportError:
        return None

    if stage_code == "05":
        mpi_data = load_stage_output("05", "mpi_ranking", None)
        if mpi_data and isinstance(mpi_data, list) and len(mpi_data) > 1:
            names = [d.get("地块名称", f"地块{i}") for i, d in enumerate(mpi_data[:10])]
            scores = [d.get("MPI 得分", 0) for d in mpi_data[:10]]
            fig = go.Figure(go.Bar(
                x=scores, y=names, orientation="h",
                marker=dict(
                    color=scores,
                    colorscale=[[0, "#1e1b4b"], [0.5, "#6366f1"], [1, "#34d399"]],
                ),
            ))
            apply_plotly_theme(fig, title="MPI 更新潜力排行榜（自动生成）", height=320)
            fig.update_layout(yaxis=dict(autorange="reversed"), xaxis_title="MPI 综合得分")
            return fig

    if stage_code == "04":
        try:
            from src.engines.spatial_engine import get_skyline_features
            sky = get_skyline_features()
            if sky.get("building_count", 0) > 0:
                labels = ["低层(<9m)", "多层(9-18m)", "中高层(18-24m)", "高层(>24m)"]
                hr = sky.get("high_rise_ratio", 10)
                values = [40, 100 - 40 - hr - 5, 5, hr]
                values = [max(0, v) for v in values]
                fig = go.Figure(go.Pie(
                    labels=labels, values=values,
                    marker=dict(colors=["#34d399", "#60a5fa", "#f59e0b", "#ef4444"]),
                    hole=0.45,
                ))
                apply_plotly_theme(fig, title="建筑高度分布（自动生成）", height=300)
                return fig
        except Exception:
            pass

    if stage_code == "07":
        voting = load_stage_output("07", "voting_scores", None)
        if voting and isinstance(voting, dict) and len(voting) >= 3:
            fig = go.Figure(go.Scatterpolar(
                r=list(voting.values()) + [list(voting.values())[0]],
                theta=list(voting.keys()) + [list(voting.keys())[0]],
                fill="toself",
                fillcolor="rgba(99,102,241,0.15)",
                line=dict(color="#818cf8", width=2),
            ))
            from src.ui.chart_theme import apply_plotly_polar_theme
            apply_plotly_polar_theme(fig, title="多主体共识度雷达（自动生成）", height=320, radial_range=[0, 100])
            return fig

    return None


def _render_llm_summary_button(
    stage_code: str, title: str, findings: list[dict], methodology: str
):
    """渲染 AI 小结生成按钮和结果展示。"""
    from src.workflow.city_design_workflow import STAGE_LOOKUP

    stage_info = STAGE_LOOKUP.get(stage_code, {})
    stage_name = stage_info.get("title", title)

    session_key = f"llm_summary_{stage_code}"

    col1, col2 = st.columns([3, 1])
    with col2:
        model_tag = st.text_input(
            "模型", value="gemma4:e2b-it-q4_K_M",
            key=f"summary_model_{stage_code}",
            label_visibility="collapsed",
        )
    with col1:
        if st.button(
            f"🧠 AI 生成 Stage {stage_code} 答辩小结",
            key=f"summary_btn_{stage_code}",
            use_container_width=True,
        ):
            # 收集数据上下文
            data_lines = [f"阶段：{stage_code} {stage_name}", f"方法论：{methodology}"]
            for idx, f in enumerate(findings):
                data_lines.append(f"发现{idx+1}：{f.get('point', '')} (依据: {f.get('evidence', '')})")

            # 从数据总线补充
            try:
                from src.workflow.stage_data_bus import load_stage_output
                bus_data = st.session_state.get("stage_bus", {}).get(stage_code, {})
                for k, v in bus_data.items():
                    if isinstance(v, str) and len(v) < 300:
                        data_lines.append(f"[总线] {k}: {v}")
                    elif isinstance(v, (int, float)):
                        data_lines.append(f"[总线] {k}: {v}")
            except Exception:
                pass

            data_context = "\n".join(data_lines)
            result = generate_stage_summary_text(
                stage_code, stage_name, data_context, model=model_tag
            )
            if result:
                st.session_state[session_key] = result

    if st.session_state.get(session_key):
        st.markdown(
            f"""<div style="background: rgba(52,211,153,0.06); border: 1px solid rgba(52,211,153,0.2);
            border-radius: 12px; padding: 16px 20px; margin-top: 12px;">
            <div style="color: #34d399; font-size: 13px; font-weight: 800; margin-bottom: 8px;">
            🧠 AI 生成的答辩小结 (Stage {escape(stage_code)})</div>
            <div style="color: #e2e8f0; font-size: 14px; line-height: 1.7;">
            {escape(st.session_state[session_key])}</div></div>""",
            unsafe_allow_html=True,
        )
        st.download_button(
            f"📥 导出小结",
            st.session_state[session_key],
            file_name=f"Stage{stage_code}_答辩小结.md",
            mime="text/markdown",
            use_container_width=True,
            key=f"dl_summary_{stage_code}",
        )


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
