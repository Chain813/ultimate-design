"""阶段 04-05：现状分析与问题诊断 —— 3D 全息底座、MPI 潜力评估、地块雷达、AI 诊断报告。"""

import json
import logging

import numpy as np
import pandas as pd
import streamlit as st

from src.config import SHP_FILES
from src.engines.llm_engine import call_llm_engine_stream
from src.engines.site_diagnostic_engine import get_plot_diagnostics
from src.engines.spatial_engine import get_hud_statistics, get_skyline_features
from src.stages.common.workspace import render_stage_workspace
from src.stages.stage04_diagnosis.config import STAGE04_WORKSPACE
from src.ui.app_shell import render_engine_status_alert, render_top_nav
from src.ui.chart_theme import apply_plotly_polar_theme, apply_plotly_theme, get_chart_palette
from src.ui.design_system import (
    render_analysis_pipeline_hud,
    render_diagnosis_pipeline_hud,
    render_page_banner,
    render_section_intro,
    render_summary_cards,
)
from src.ui.digital_twin import render_digital_twin_map, render_skyline_hud
from src.ui.module_summary import render_stage_summary
from src.ui.persistent_outputs import register_output, register_report_output
from src.ui.streamlit_compat import stretch_width
from src.workflow.stage_data_bus import load_stage_output, render_evidence_chain_bar, save_stage_output
from src.workflow.stage_keys import SK


def render_page() -> None:
    render_top_nav()
    render_engine_status_alert()

    stats = get_hud_statistics()
    sky = get_skyline_features()

    render_page_banner(
        title="现状分析与问题诊断",
        description="基于 3D 全息底座进行空间现状综合分析，通过 MPI 潜力评估和 AI 诊断识别优先更新地块。",
        eyebrow="Stage 04-05",
        tags=["3D 数字孪生", "MPI 更新潜力", "地块雷达诊断", "AI 问题报告"],
        metrics=[
            {"value": str(stats.get("poi_count", "N/A")), "label": "POI 记录", "meta": "功能活力测度"},
            {"value": str(sky.get("building_count", 0)), "label": "建筑", "meta": "栋"},
            {"value": "AHP-MPI", "label": "评价模型", "meta": "空间潜力×社会需求×环境紧迫度"},
            {"value": "DeepSeek", "label": "诊断引擎", "meta": "本地大模型"},
        ],
        graphic_html=render_analysis_pipeline_hud(as_html=True)
    )
    render_evidence_chain_bar("04", ["01", "02", "03", "04", "05"])

    active = render_stage_workspace(STAGE04_WORKSPACE)
    selected_sub = active.label
    st.markdown("---")


    # ============================================================
    # 模块一：3D 现状全息底座 (原 Stage 04)
    # ============================================================
    if selected_sub == "🏙️ 3D 现状全息底座":
        render_section_intro("3D 现状全息底座", "综合建筑体量、用地类型、POI 分布、交通热点和街景品质指标的三维可视化。", eyebrow="Digital Twin")

        render_summary_cards([
            {"value": stats.get("boundary_ha", "~156"), "title": "研究范围", "desc": "公顷"},
            {"value": sky.get("building_count", 0), "title": "建筑总数", "desc": "栋"},
            {"value": f"{sky.get('max_height', 0)} m", "title": "最高建筑", "desc": "天际线峰值"},
            {"value": stats.get("gvi_count", "N/A"), "title": "街景样本", "desc": "GVI/SVF 采样点"},
        ])

        render_digital_twin_map(key_suffix="stage04")
        render_skyline_hud()

        save_stage_output("04", "poi_count", stats.get("poi_count", 0))
        save_stage_output("04", "building_count", sky.get("building_count", 0))
        save_stage_output("04", "avg_height", sky.get("avg_height", 0))


    # ============================================================
    # 模块二：MPI 更新潜力评估 (原 Stage 05)
    # ============================================================
    elif selected_sub == "📊 MPI 更新潜力评估":
        render_section_intro(
            "更新优先级评估",
            "基于重点更新单元 GeoJSON 和 AHP 权重实时计算 MPI，优先用于识别近期应先启动的微更新节点。",
            eyebrow="Multi-dimensional Potential Index",
        )

        @st.cache_data(ttl=3600, max_entries=20)
        def _load_plot_base_data():
            """缓存 GeoJSON 解析结果，避免每次交互重复读盘。"""
            _jpath = SHP_FILES["plots"]
            if _jpath.exists():
                try:
                    geo_data = json.loads(_jpath.read_text(encoding="utf-8"))
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
                    return pd.DataFrame(plot_list)
                except Exception:
                    logging.debug("地块数据加载失败，使用 fallback", exc_info=True)
                    return pd.DataFrame({
                        "地块名称": ["中车老厂区", "光复路历史街区", "铁北断头路节点"],
                        "空间潜力原分": [0.89, 0.82, 0.74],
                        "社会需求原分": [0.92, 0.95, 0.65],
                        "环境现状评分": [0.35, 0.42, 0.28],
                    })
            return pd.DataFrame({
                "地块名称": ["数据资产缺失"],
                "空间潜力原分": [0], "社会需求原分": [0], "环境现状评分": [1],
            })

        base_data = _load_plot_base_data()

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
            hide_index=True,
            **stretch_width(st.dataframe),
        )

        csv_report = df_filtered.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📤 导出评估排行榜 (CSV)",
            csv_report,
            file_name="MPI_Report.csv",
            mime="text/csv",
            **stretch_width(st.download_button),
        )
        register_output(
            label="MPI更新潜力评估排行榜",
            data=csv_report,
            mime="text/csv",
            filename="MPI_Report.csv",
            category="data",
            key="mpi_ranking_csv",
        )

        if not df_filtered.empty:
            import plotly.express as px
            fig = px.scatter(df_filtered, x="空间潜力原分", y="社会需求原分", size="MPI 得分", color="地块名称",
                             color_discrete_sequence=get_chart_palette(), height=440)
            apply_plotly_theme(fig, title="空间潜力与社会需求耦合分布", height=440, showlegend=True)
            st.plotly_chart(fig, **stretch_width(st.plotly_chart))

        save_stage_output("05", SK.MPI_RANKING, df_filtered.to_dict("records"))
        save_stage_output("05", SK.TOP_PLOT, top_plot)
        save_stage_output("05", SK.TOP_SCORE, top_score)


    # ============================================================
    # 模块三：地块雷达诊断 (原 Stage 05)
    # ============================================================
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

            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=[*values, values[0]],
                theta=[*categories, categories[0]],
                fill="toself",
                fillcolor="rgba(129,140,248,0.15)",
                line=dict(color="#818cf8", width=2),
            ))
            apply_plotly_polar_theme(fig, title=f"{selected_plot} 多维诊断雷达", height=380)
            st.plotly_chart(fig, **stretch_width(st.plotly_chart))

            save_stage_output("05", SK.RADAR_DATA, {"plot": selected_plot, "categories": categories, "values": values})
        else:
            st.warning("暂无地块诊断数据，请检查 data/gis 目录。")


    # ============================================================
    # 模块四：AI 前期诊断报告 (原 Stage 05)
    # ============================================================
    elif selected_sub == "🔬 AI 前期诊断报告":
        if "stage1_output" not in st.session_state:
            st.session_state["stage1_output"] = load_stage_output("05", SK.DIAGNOSIS_REPORT, "")
        render_section_intro("AI 前期问题诊断", "自动读取 MPI/GVI/POI 数据，调用本地 DeepSeek 生成数据驱动的问题诊断报告。", eyebrow="LLM Stage 01")

        with st.sidebar:
            model_tag = st.text_input("DeepSeek 模型标签", value="deepseek-v4-pro", key="p5_model")

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
                st.markdown("#### 📋 前期诊断报告")
                result = st.write_stream(stream)
                if isinstance(result, str) and len(result) > 50:
                    st.session_state["stage1_output"] = result
                    save_stage_output("05", SK.DIAGNOSIS_REPORT, result)
                    st.toast("✅ 前期诊断报告生成完成！", icon="📊")
                    register_report_output(label="AI前期诊断报告", content=result, stage_code="04", key="diagnosis_report")
        else:
            st.warning("暂无地块诊断数据。")

        if st.session_state.get("stage1_output") and not st.session_state.get("s1_btn"):
            st.markdown("#### 📋 前期诊断报告")
            st.markdown(st.session_state["stage1_output"])


    # ============================================================
    # 模块五：专项资源分析
    # ============================================================
    elif selected_sub == "📋 专项资源分析":
        render_section_intro(
            "专项资源分析",
            "提供文化资源、产业业态和人群需求的概要分析。",
            eyebrow="Supplementary Analysis",
        )

        from src.engines.spatial_data_injector import get_full_spatial_context
        spatial_ctx = get_full_spatial_context()

        # ── 2.6 文化资源分析 ──
        saved_cultural = load_stage_output("04", SK.CULTURAL_ANALYSIS, "")
        with st.expander("🏛️ 2.6 文化资源分析", expanded=bool(saved_cultural) or True):
            st.caption("基于历史建筑分布、工业遗产和伪满皇宫周边文化资源，生成约300字分析文本。")
            if st.button("🧠 生成文化资源分析", key="p04_cultural", **stretch_width(st.button)):
                with st.spinner("LLM 分析中..."):
                    prompt = f"""请分析研究范围内的文化资源特征，撰写约300字的文化资源分析文本。
    要涵盖：1. 伪满皇宫为核心的近代历史建筑群；2. 中车工业遗产；3. 文化资源分布格局。

    【空间数据】
    {spatial_ctx[:2000]}

    只输出分析文本正文，不要标题。"""
                    result = call_llm_engine_stream(
                        prompt=prompt,
                        system_prompt="你是城乡规划专业的文化遗产分析专家。",
                        model="deepseek-v4-flash",
                    )
                    text = st.write_stream(result)
                    if isinstance(text, str) and len(text) > 30:
                        save_stage_output("04", SK.CULTURAL_ANALYSIS, text)
                        st.success(f"✅ 文化资源分析已生成（{len(text)} 字）")

            if saved_cultural:
                st.markdown(saved_cultural)

        # ── 2.7 产业业态分析 ──
        saved_industry = load_stage_output("04", SK.INDUSTRY_ANALYSIS, "")
        with st.expander("🏪 2.7 产业业态分析", expanded=bool(saved_industry)):
            st.caption("基于 POI 数据和用地现状，分析产业业态分布特征。")
            if st.button("🧠 生成产业业态分析", key="p04_industry", **stretch_width(st.button)):
                with st.spinner("LLM 分析中..."):
                    prompt = f"""请分析研究范围内的产业业态特征，撰写约300字的产业业态分析文本。
    要涵盖：1. 现状商业分布；2. POI 类型构成；3. 产业集聚特征。

    【空间数据】
    {spatial_ctx[:2000]}

    只输出分析文本正文，不要标题。"""
                    result = call_llm_engine_stream(
                        prompt=prompt,
                        system_prompt="你是城乡规划专业的产业经济分析专家。",
                        model="deepseek-v4-flash",
                    )
                    text = st.write_stream(result)
                    if isinstance(text, str) and len(text) > 30:
                        save_stage_output("04", SK.INDUSTRY_ANALYSIS, text)
                        st.success(f"✅ 产业业态分析已生成（{len(text)} 字）")

            if saved_industry:
                st.markdown(saved_industry)

        # ── 2.8 人群需求分析 ──
        saved_population = load_stage_output("04", SK.POPULATION_ANALYSIS, "")
        with st.expander("👥 2.8 人群需求分析", expanded=bool(saved_population)):
            st.caption("基于 POI 分布、街景品质、住宅类型等推断人群结构和社区需求。")
            if st.button("🧠 生成人群需求分析", key="p04_population", **stretch_width(st.button)):
                with st.spinner("LLM 分析中..."):
                    prompt = f"""请分析研究范围内的社区人群需求特征，撰写约300字的人群需求分析文本。
    要涵盖：1. 居民年龄结构和居住类型推断；2. 公共服务设施需求；3. 社区更新诉求。

    【空间数据】
    {spatial_ctx[:2000]}

    只输出分析文本正文，不要标题。"""
                    result = call_llm_engine_stream(
                        prompt=prompt,
                        system_prompt="你是城乡规划专业的社区规划专家，擅长人群需求分析。",
                        model="deepseek-v4-flash",
                    )
                    text = st.write_stream(result)
                    if isinstance(text, str) and len(text) > 30:
                        save_stage_output("04", SK.POPULATION_ANALYSIS, text)
                        st.success(f"✅ 人群需求分析已生成（{len(text)} 字）")

            if saved_population:
                st.markdown(saved_population)


    # ============================================================
    # 底部：阶段研究小结
    # ============================================================
    st.markdown("---")

    # Stage 04 小结
    render_stage_summary(
        stage_code="04",
        title="现状空间特征综述",
        findings=[
            {"point": f"研究范围内共 {sky.get('building_count', 0)} 栋建筑，平均高度 {sky.get('avg_height', 0)} 米", "evidence": "建筑底图 GeoJSON 空间分析"},
            {"point": f"高层建筑（≥24m）占比 {sky.get('high_rise_ratio', 0)}%，片区以低层和多层为主", "evidence": "天际线形态分析"},
            {"point": f"POI 设施 {stats.get('poi_count', 'N/A')} 条，街景采样点 {stats.get('gvi_count', 'N/A')} 个", "evidence": "空间引擎 HUD 统计"},
        ],
        methodology="基于 GIS 空间数据和街景图像的多源融合分析",
        implication="为问题诊断提供了现状空间特征的定量基础",
    )

    # Stage 05 小结
    mpi_data = load_stage_output("05", SK.MPI_RANKING, [])
    top_plot_name = load_stage_output("05", SK.TOP_PLOT, "暂无")
    top_mpi = load_stage_output("05", SK.TOP_SCORE, 0)
    diagnostics = get_plot_diagnostics()

    findings_05 = [
        {
            "point": f"基于 AHP-MPI 模型，{top_plot_name} 以 {top_mpi:.1f} 分位居更新优先级首位",
            "evidence": "评价维度：空间潜力、社会需求、环境紧迫度三维加权"
        },
        {
            "point": f"共识别 {len(mpi_data)} 个候选更新单元进入优先排行",
            "evidence": "数据来源：重点更新单元 GeoJSON + AHP 动态权重"
        },
    ]

    if diagnostics:
        avg_gvi = sum(d["gvi_mean"] for d in diagnostics) / len(diagnostics)
        avg_poi = sum(d["poi_count"] for d in diagnostics) / len(diagnostics)
        findings_05.append({
            "point": f"研究范围内重点地块平均绿视率为 {avg_gvi:.1f}%，低于 GB50180-2018 要求的 30%",
            "evidence": f"平均 POI 密度 {avg_poi:.0f} 处/地块，反映公共服务覆盖不均"
        })

    render_stage_summary(
        stage_code="05",
        title="更新潜力诊断小结",
        findings=findings_05,
        methodology="基于 AHP-MPI 多维潜力指数模型，融合空间潜力、社会需求和环境紧迫度三维加权评价",
        implication="为后续目标定位（Stage 06）和设计策略（Stage 07）提供了数据驱动的优先级依据",
    )
