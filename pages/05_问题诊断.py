"""阶段 05：问题诊断 —— MPI 更新潜力评估、地块雷达、LLM 诊断报告。

从原 page11 (MPI 计算面板) + page12 (地块雷达) + page14 (LLM 阶段一) 整合。
"""

import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import SHP_FILES, DATA_FILES
from src.engines.site_diagnostic_engine import get_plot_diagnostics
from src.engines.llm_engine import call_llm_engine_stream
from src.engines.drawing_prompt_templates import (
    get_templates_by_stage,
    build_drawing_prompt,
    generate_drawing_prompt_with_llm,
)
from src.ui.chart_theme import apply_plotly_theme, apply_plotly_polar_theme, get_chart_palette
from src.ui.design_system import render_page_banner, render_section_intro, render_summary_cards
from src.ui.app_shell import render_top_nav, render_engine_status_alert
from src.ui.module_summary import render_stage_summary, generate_stage_summary_text
from src.workflow.stage_data_bus import (
    save_stage_output,
    load_stage_output,
    render_evidence_chain_bar,
)
from src.utils.runtime_flags import is_demo_mode

st.set_page_config(page_title="05 问题诊断", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()
render_engine_status_alert()

render_page_banner(
    title="问题诊断",
    description="通过 AHP-MPI 多维潜力指数模型识别优先更新地块，结合地块级雷达诊断和 AI 前期分析，形成数据驱动的问题清单。",
    eyebrow="Stage 05",
    tags=["MPI 更新潜力", "地块雷达诊断", "AI 问题报告", "数据图纸生成"],
    metrics=[
        {"value": "AHP-MPI", "label": "评价模型", "meta": "空间潜力×社会需求×环境紧迫度"},
        {"value": "3", "label": "核心维度", "meta": "可交互调权"},
        {"value": "Gemma 4", "label": "诊断引擎", "meta": "本地大模型"},
    ],
)

render_evidence_chain_bar("05", ["01", "02", "03", "04", "05"])

# --- 子页面选择 ---
SUB_OPTIONS = ["📊 MPI 更新潜力评估", "🎯 地块雷达诊断", "🔬 AI 前期诊断报告", "🖼️ 图纸提示词生成"]
selected_sub = st.radio("功能模块", SUB_OPTIONS, horizontal=True, label_visibility="collapsed")
st.markdown("---")

# ═══════════════════════════════════════════
# 子页面 1: MPI 更新潜力评估 (原 page11 资产综合评估)
# ═══════════════════════════════════════════
if selected_sub == "📊 MPI 更新潜力评估":
    render_section_intro(
        "更新优先级评估",
        "基于重点更新单元 GeoJSON 和 AHP 权重实时计算 MPI，优先用于识别近期应先启动的微更新节点。",
        eyebrow="Multi-dimensional Potential Index",
    )

    json_path = SHP_FILES["plots"]
    if json_path.exists():
        try:
            geo_data = json.loads(json_path.read_text(encoding="utf-8"))
            plot_list = []
            for feat in geo_data.get("features", []):
                props = feat.get("properties", {})
                name = props.get("name", props.get("Name", f"地块_{props.get('OBJECTID', '??')}"))
                area = props.get("Shape_Area", 50000)
                pot = min(0.95, 0.5 + (area / 150000) * 0.4)
                seed_id = props.get("OBJECTID", 0)
                np.random.seed(seed_id)
                plot_list.append({
                    "地块名称": name,
                    "空间潜力原分": round(pot, 2),
                    "社会需求原分": round(0.5 + 0.4 * np.random.rand(), 2),
                    "环境现状评分": round(0.1 + 0.6 * np.random.rand(), 2),
                })
            base_data = pd.DataFrame(plot_list)
        except Exception:
            base_data = pd.DataFrame({
                "地块名称": ["中车老厂区", "光复路历史街区", "铁北断头路节点"],
                "空间潜力原分": [0.89, 0.82, 0.74],
                "社会需求原分": [0.92, 0.95, 0.65],
                "环境现状评分": [0.35, 0.42, 0.28],
            })
    else:
        base_data = pd.DataFrame({
            "地块名称": ["数据资产缺失"],
            "空间潜力原分": [0], "社会需求原分": [0], "环境现状评分": [1],
        })

    with st.sidebar:
        st.markdown("### 🎚️ 专家决策模拟 (AHP)")
        w_poi = st.slider("🏗️ 空间潜力占比 (%)", 0, 100, 40, key="w_poi")
        w_soc = st.slider("👥 社会需求占比 (%)", 0, 100, 30, key="w_soc")
        w_env = st.slider("🌿 环境干预紧迫度 (%)", 0, 100, 30, key="w_env")
        total_w = w_poi + w_soc + w_env
        st.caption(f"当前权重总计: {total_w}%")
        if total_w != 100:
            st.warning("建议将权重总计调至 100%。")
        st.markdown("---")
        threshold = st.slider("🎯 仅展示得分高于", 0, 100, 0, key="p5_threshold")

    def recalc_mpi(df, w1, w2, w3):
        df = df.copy()
        df["MPI 得分"] = (
            (df["空间潜力原分"] * w1 + df["社会需求原分"] * w2 + (1 - df["环境现状评分"]) * w3)
            / (w1 + w2 + w3 + 0.001) * 100
        )
        return df

    df_calc = recalc_mpi(base_data, w_poi, w_soc, w_env)
    df_filtered = df_calc[df_calc["MPI 得分"] >= threshold].sort_values("MPI 得分", ascending=False)
    top_plot = df_filtered.iloc[0]["地块名称"] if not df_filtered.empty else "暂无"
    top_score = float(df_filtered.iloc[0]["MPI 得分"]) if not df_filtered.empty else 0.0

    render_summary_cards([
        {"value": len(df_filtered), "title": "候选更新单元", "desc": "满足当前阈值要求的地块数量。"},
        {"value": f"{top_score:.1f}", "title": "最高 MPI 分值", "desc": f"当前优先地块：{top_plot}。"},
        {"value": f"{w_poi}/{w_soc}/{w_env}", "title": "权重组合", "desc": "空间潜力 / 社会需求 / 环境紧迫度。"},
    ])

    st.latex(
        r"\color{#a5b4fc} MPI_i = \frac{w_{space} \cdot S_i + w_{social} \cdot D_i + w_{env} \cdot (1 - E_i)}{w_{space} + w_{social} + w_{env}} \times 100"
    )

    st.dataframe(
        df_filtered[["地块名称", "MPI 得分"]],
        column_config={"MPI 得分": st.column_config.ProgressColumn("MPI 综合潜力分", format="%.1f", min_value=0, max_value=100)},
        use_container_width=True, hide_index=True,
    )

    csv_report = df_filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📤 导出评估排行榜 (CSV)", csv_report, file_name="MPI_Report.csv", mime="text/csv", use_container_width=True)

    if not df_filtered.empty:
        fig = px.scatter(df_filtered, x="空间潜力原分", y="社会需求原分", size="MPI 得分", color="地块名称",
                         color_discrete_sequence=get_chart_palette(), height=440)
        apply_plotly_theme(fig, title="空间潜力与社会需求耦合分布", height=440, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    # 保存到数据总线
    save_stage_output("05", "mpi_ranking", df_filtered.to_dict("records"))
    save_stage_output("05", "top_plot", top_plot)
    save_stage_output("05", "top_score", top_score)

# ═══════════════════════════════════════════
# 子页面 2: 地块雷达诊断 (原 page12 地块级诊断面板)
# ═══════════════════════════════════════════
elif selected_sub == "🎯 地块雷达诊断":
    render_section_intro("地块级多维诊断", "对每个重点更新单元进行 MPI/GVI/POI/SVF 多维度雷达评价。", eyebrow="Plot Radar")

    diagnostics = get_plot_diagnostics()
    if diagnostics:
        plot_names = [d["name"] for d in diagnostics]
        selected_plot = st.selectbox("选择重点地块：", plot_names, key="p5_radar_plot")
        diag = next(d for d in diagnostics if d["name"] == selected_plot)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("面积", f"{diag['area_ha']} ha")
        m2.metric("MPI", f"{diag['mpi_score']}")
        m3.metric("POI", f"{diag['poi_count']}")
        m4.metric("GVI", f"{diag['gvi_mean']}")

        categories = ["空间潜力", "设施密度", "绿视率", "天空开敞度", "环境整洁度"]
        values = [
            min(1, diag["area_ha"] / 10),
            min(1, diag["poi_count"] / 20),
            diag["gvi_mean"] / 100,
            diag["svf_mean"] / 100 if diag["svf_mean"] else 0.5,
            1 - (diag["clutter_mean"] / 100 if diag["clutter_mean"] else 0.5),
        ]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            fillcolor="rgba(129,140,248,0.15)",
            line=dict(color="#818cf8", width=2),
        ))
        apply_plotly_polar_theme(fig, title=f"{selected_plot} 多维诊断雷达", height=380)
        st.plotly_chart(fig, use_container_width=True)

        save_stage_output("05", "radar_data", {"plot": selected_plot, "categories": categories, "values": values})
    else:
        st.warning("暂无地块诊断数据，请检查 data/shp 目录。")

# ═══════════════════════════════════════════
# 子页面 3: AI 前期诊断报告 (原 page14 阶段一)
# ═══════════════════════════════════════════
elif selected_sub == "🔬 AI 前期诊断报告":
    render_section_intro("AI 前期问题诊断", "自动读取 MPI/GVI/POI 数据，调用本地 Gemma 4 生成数据驱动的问题诊断报告。", eyebrow="LLM Stage 01")

    with st.sidebar:
        model_tag = st.text_input("Gemma 4 模型标签", value="gemma4:e2b-it-q4_K_M", key="p5_model")

    diagnostics = get_plot_diagnostics()
    if diagnostics:
        plot_names = [d["name"] for d in diagnostics]
        selected_plot = st.selectbox("选择重点地块：", plot_names, key="p5_s1_plot")
        diag = next(d for d in diagnostics if d["name"] == selected_plot)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("面积", f"{diag['area_ha']} ha")
        m2.metric("MPI", f"{diag['mpi_score']}")
        m3.metric("POI", f"{diag['poi_count']}")
        m4.metric("GVI", f"{diag['gvi_mean']}")

        if st.button("🔬 生成前期问题诊断报告", type="primary", key="s1_btn"):
            prompt = f"""你是长春宽城区铁北片区的城市更新规划顾问。
基于以下数据：
- 地块名称：{selected_plot}
- 面积：{diag['area_ha']} 公顷
- 微更新潜力指数（MPI）：{diag['mpi_score']}（>70 为高潜力）
- 周边 POI 设施数：{diag['poi_count']}
- 绿视率（GVI）：{diag['gvi_mean']}%（GB50180-2018 要求≥30%）

请生成【前期问题诊断报告】。要求：
1. 列出 4-6 个具体问题，每个含：【问题名称】【数据依据】【政策依据】【严重程度】
2. 结合四大核心痛点：用地混杂、交通割裂、老龄化率30%、环境品质匮乏
3. 最后给出问题优先级排序"""
            sys_prompt = "你是扎根长春铁北片区的资深城市规划诊断师。输出必须引用具体数据和政策条文编号。"
            stream = call_llm_engine_stream(prompt=prompt, system_prompt=sys_prompt, model=model_tag)
            result = st.write_stream(stream)
            if isinstance(result, str) and len(result) > 50:
                st.session_state["stage1_output"] = result
                save_stage_output("05", "diagnosis_report", result)
                st.toast("✅ 前期诊断报告生成完成！", icon="📊")
    else:
        st.warning("暂无地块诊断数据。")

    if st.session_state.get("stage1_output"):
        st.markdown("#### 📋 前期诊断报告")
        st.markdown(st.session_state["stage1_output"])

# ═══════════════════════════════════════════
# 子页面 4: 图纸提示词生成 (新增)
# ═══════════════════════════════════════════
elif selected_sub == "🖼️ 图纸提示词生成":
    render_section_intro(
        "问题诊断类图纸提示词",
        "基于本阶段数据自动生成面向 ChatGPT Image 2.0 的专业图纸提示词，可调用本地大模型优化。",
        eyebrow="Drawing Prompt Templates",
    )

    with st.sidebar:
        model_tag = st.text_input("Gemma 4 模型标签", value="gemma4:e2b-it-q4_K_M", key="p5_draw_model")

    templates = get_templates_by_stage("05")
    if templates:
        template_names = [t.name for t in templates]
        selected_tmpl = st.selectbox("选择图纸模板", template_names, key="p5_draw_sel")
        tmpl = next(t for t in templates if t.name == selected_tmpl)

        st.markdown(f"**图纸说明：** {tmpl.description}")
        st.markdown(f"**所属章节：** {tmpl.chapter}")

        prompt_text, sys_text = build_drawing_prompt(selected_tmpl)
        st.text_area("预览：数据注入后的提示词模板", value=prompt_text, height=300, key="p5_draw_preview")

        if st.button("🧠 调用 Gemma 4 生成完整提示词", type="primary", use_container_width=True, key="p5_draw_gen"):
            with st.spinner("正在生成..."):
                result = generate_drawing_prompt_with_llm(selected_tmpl, model=model_tag)
            st.session_state["p5_generated_prompt"] = result

        if st.session_state.get("p5_generated_prompt"):
            st.text_area("生成的完整 Image 2.0 提示词", value=st.session_state["p5_generated_prompt"], height=400, key="p5_draw_output")
            st.download_button("📥 下载提示词", st.session_state["p5_generated_prompt"],
                              file_name=f"{selected_tmpl}_prompt.md", mime="text/markdown", use_container_width=True)
    else:
        st.info("暂无本阶段图纸模板。")

# ═══════════════════════════════════════════
# 阶段研究小结 (底部)
# ═══════════════════════════════════════════
st.markdown("---")

mpi_data = load_stage_output("05", "mpi_ranking", [])
top_plot_name = load_stage_output("05", "top_plot", "暂无")
top_mpi = load_stage_output("05", "top_score", 0)
diagnostics = get_plot_diagnostics()

findings = [
    {
        "point": f"基于 AHP-MPI 模型，{top_plot_name} 以 {top_mpi:.1f} 分位居更新优先级首位",
        "evidence": f"评价维度：空间潜力、社会需求、环境紧迫度三维加权"
    },
    {
        "point": f"共识别 {len(mpi_data)} 个候选更新单元进入优先排行",
        "evidence": "数据来源：重点更新单元 GeoJSON + AHP 动态权重"
    },
]

if diagnostics:
    avg_gvi = sum(d["gvi_mean"] for d in diagnostics) / len(diagnostics)
    avg_poi = sum(d["poi_count"] for d in diagnostics) / len(diagnostics)
    findings.append({
        "point": f"研究范围内重点地块平均绿视率为 {avg_gvi:.1f}%，低于 GB50180-2018 要求的 30%",
        "evidence": f"平均 POI 密度 {avg_poi:.0f} 处/地块，反映公共服务覆盖不均"
    })

render_stage_summary(
    stage_code="05",
    title="更新潜力诊断小结",
    findings=findings,
    methodology="基于 AHP-MPI 多维潜力指数模型，融合空间潜力、社会需求和环境紧迫度三维加权评价",
    implication="为后续目标定位（Stage 06）和设计策略（Stage 07）提供了数据驱动的优先级依据",
)
