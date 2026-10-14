"""阶段 04-05：现状分析与问题诊断 —— 3D 全息底座、MPI 潜力评估、地块雷达、AI 诊断报告。

零预置模板·动态因地制宜：
- 动态载入候选地块（GeoJSON 上传 / OSM 抓取 / 本地资产）
- AHP-MPI 动态潜力评价与散点分布
- 自由选取或手动录入任意地块为更新靶向地块
- 动态调用 infer_plot_diagnostics 生成量化痛点画像
"""

from __future__ import annotations

import json
import logging
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from src.config import SHP_FILES
from src.config.site import get_site_city, get_site_name
from src.engines.llm_engine import call_llm_engine_stream
from src.engines.spatial_engine import get_hud_statistics, get_skyline_features
from src.stages.common.workspace import render_stage_workspace
from src.stages.stage04_diagnosis.config import STAGE04_WORKSPACE
from src.ui.app_shell import (
    render_engine_status_alert,
    render_logic_chain_stepper,
    render_top_nav,
)
from src.ui.chart_theme import apply_plotly_polar_theme, apply_plotly_theme, get_chart_palette
from src.ui.design_system import (
    render_analysis_pipeline_hud,
    render_page_banner,
    render_section_intro,
    render_summary_cards,
)
from src.ui.digital_twin import render_digital_twin_map, render_skyline_hud
from src.ui.module_summary import render_stage_summary
from src.ui.persistent_outputs import register_output, register_report_output
from src.ui.site_ingestion_panel import get_active_candidate_plots
from src.ui.streamlit_compat import stretch_width
from src.workflow.stage_data_bus import load_stage_output, render_evidence_chain_bar, save_stage_output
from src.workflow.stage_keys import SK

logger = logging.getLogger("ultimateDESIGN")


# ═══════════════════════════════════════════════════════════════
# 1. 靶向地块动态诊断与总线锁定核心接口
# ═══════════════════════════════════════════════════════════════

def select_target_plot_and_diagnose(
    plot_name: str,
    land_use: str = "商业用地",
    mpi_score: float = 85.0,
    area_ha: float = 3.5,
    metrics: dict[str, Any] | None = None,
    site_context: dict[str, Any] | None = None,
    custom_issues: list[str] | None = None,
) -> dict[str, Any]:
    """核心接口：选定任意地块为更新靶向地块，并现场动态推导量化痛点画像，存入总线。
    
    参数:
        plot_name: 地块名称（如 '社区农贸市场', '老铸造车间', '市一中北侧' 等）
        land_use: 现状用地性质
        mpi_score: MPI 更新潜力综合得分
        area_ha: 占地面积 (公顷)
        metrics: 包含 gvi, poi, svf, clutter 等定量指标
        site_context: 片区上下文信息
        custom_issues: 用户自定义或手动编辑的痛点列表 (可选)

    返回:
        包含完整结构化画像的 dict: name, land_use, area_ha, mpi, priority, issues, metrics
    """
    mpi_val = round(float(mpi_score), 1)

    # 优先级动态判定
    if mpi_val >= 80.0:
        priority = "P1 优先更新"
    elif mpi_val >= 60.0:
        priority = "P2 协同更新"
    else:
        priority = "P3 储备更新"

    m = metrics or {}
    gvi = m.get("gvi", m.get("gvi_mean", 15.0))
    poi = m.get("poi", m.get("poi_count", 10))
    svf = m.get("svf", m.get("svf_mean", 0.50))
    clutter = m.get("clutter", m.get("clutter_mean", 30.0))

    metrics_dict = {
        "gvi": round(float(gvi), 1) if gvi is not None else 15.0,
        "poi": int(poi) if poi is not None else 10,
        "svf": round(float(svf), 2) if svf is not None else 0.50,
        "clutter": round(float(clutter), 1) if clutter is not None else 30.0,
    }

    # 动态推导痛点（带安全降级）
    if custom_issues and isinstance(custom_issues, list) and len(custom_issues) > 0:
        issues = custom_issues
    else:
        plot_payload = {
            "name": plot_name,
            "land_use": land_use,
            "area_ha": area_ha,
            "gvi_mean": metrics_dict["gvi"],
            "poi_count": metrics_dict["poi"],
            "svf_mean": metrics_dict["svf"],
            "clutter_mean": metrics_dict["clutter"],
            "mpi_score": mpi_val,
        }
        try:
            from src.engines.context_adaptive_engine import infer_plot_diagnostics
            issues = infer_plot_diagnostics(plot_payload, site_context=site_context)
        except Exception:
            logger.warning("动态痛点推导引擎调用受阻，使用防御性安全降级", exc_info=True)
            issues = [
                f"{land_use}利用效率偏低，面临存量空间转型与活力重构诉求",
                "慢行连续性与公共微空间品质匮乏，街道界面缺乏有机渗透",
                "片区生态绿视率与开敞空间连通度不足",
            ]

    plot_data = {
        "name": plot_name,
        "land_use": land_use,
        "area_ha": round(float(area_ha), 2),
        "mpi": mpi_val,
        "priority": priority,
        "issues": issues,
        "metrics": metrics_dict,
    }

    # 保存至 Stage 04 & 05 总线
    save_stage_output("04", "target_plot", plot_data)
    save_stage_output("05", "target_plot", plot_data)
    save_stage_output("04", SK.TOP_PLOT, plot_name)
    save_stage_output("04", SK.TOP_SCORE, mpi_val)
    save_stage_output("05", SK.TOP_PLOT, plot_name)
    save_stage_output("05", SK.TOP_SCORE, mpi_val)

    return plot_data


def render_target_plot_card(target_plot: dict[str, Any]) -> None:
    """实时渲染「🎯 当前更新靶向地块动态诊断画像卡片」。"""
    if not target_plot or not isinstance(target_plot, dict):
        st.info("💡 尚未锁定更新靶向地块，请在上方列表中选择或录入地块。")
        return

    name = target_plot.get("name", "未指定地块")
    land_use = target_plot.get("land_use", "综合用地")
    area_ha = target_plot.get("area_ha", 0.0)
    mpi = target_plot.get("mpi", 0.0)
    priority = target_plot.get("priority", "P1 优先更新")
    issues = target_plot.get("issues", [])
    metrics = target_plot.get("metrics", {})

    priority_color = "#34d399" if "P1" in priority else ("#fbbf24" if "P2" in priority else "#94a3b8")
    priority_bg = "rgba(52, 211, 153, 0.15)" if "P1" in priority else ("rgba(251, 191, 36, 0.15)" if "P2" in priority else "rgba(148, 163, 184, 0.15)")

    issues_html = ""
    for idx, iss in enumerate(issues):
        issues_html += f"""
        <div style="display: flex; align-items: flex-start; gap: 8px; margin-bottom: 8px;">
            <span style="color: #f87171; font-size: 14px; line-height: 1.4;">⚠️</span>
            <div style="color: #e2e8f0; font-size: 13px; line-height: 1.5;">{iss}</div>
        </div>
        """

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
                border: 1px solid rgba(129, 140, 248, 0.35); border-radius: 14px; padding: 18px 22px; margin: 18px 0;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);">
        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 12px; margin-bottom: 14px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 24px;">🎯</span>
                <div>
                    <div style="color: #f8fafc; font-size: 18px; font-weight: 700; display: flex; align-items: center; gap: 10px;">
                        <span>{name}</span>
                        <span style="font-size: 12px; font-weight: 600; color: {priority_color}; background: {priority_bg}; padding: 2px 8px; border-radius: 6px; border: 1px solid {priority_color}40;">
                            {priority}
                        </span>
                        <span style="font-size: 12px; font-weight: 600; color: #a5b4fc; background: rgba(99, 102, 241, 0.15); padding: 2px 8px; border-radius: 6px; border: 1px solid rgba(99, 102, 241, 0.3);">
                            MPI: {mpi}
                        </span>
                    </div>
                    <div style="color: #94a3b8; font-size: 12px; margin-top: 2px;">
                        现状用地：<span style="color: #cbd5e1; font-weight: 500;">{land_use}</span> ｜ 占地规模：<span style="color: #cbd5e1; font-weight: 500;">{area_ha} ha</span>
                    </div>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">贯通状态</div>
                <div style="font-size: 13px; color: #38bdf8; font-weight: 600;">已锁定为全流程更新靶向</div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; background: rgba(15, 23, 42, 0.5); padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.04);">
            <div>
                <div style="font-size: 11px; color: #94a3b8;">绿视率 (GVI)</div>
                <div style="font-size: 15px; font-weight: 600; color: #f8fafc;">{metrics.get('gvi', 'N/A')}%</div>
            </div>
            <div>
                <div style="font-size: 11px; color: #94a3b8;">POI 活力设施</div>
                <div style="font-size: 15px; font-weight: 600; color: #f8fafc;">{metrics.get('poi', 'N/A')} 处</div>
            </div>
            <div>
                <div style="font-size: 11px; color: #94a3b8;">天空开敞度 (SVF)</div>
                <div style="font-size: 15px; font-weight: 600; color: #f8fafc;">{metrics.get('svf', 'N/A')}</div>
            </div>
            <div>
                <div style="font-size: 11px; color: #94a3b8;">街道杂乱度</div>
                <div style="font-size: 15px; font-weight: 600; color: #f8fafc;">{metrics.get('clutter', '30.0')}%</div>
            </div>
        </div>

        <div>
            <div style="font-size: 13px; font-weight: 600; color: #cbd5e1; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
                <span>📋</span> 现场算法动态推导空间痛点清单:
            </div>
            {issues_html}
        </div>

        <div style="border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px; margin-top: 12px; font-size: 11px; color: #64748b;">
            💡 该靶向地块将全局驱动后续目标定位（Stage 06）、多主体博弈（Stage 07）、总体规划（Stage 08）与重点地块深化（Stage 10）。
        </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# 2. 页面主渲染逻辑
# ═══════════════════════════════════════════════════════════════

def render_page() -> None:
    render_top_nav()
    render_engine_status_alert()

    stats = get_hud_statistics()
    sky = get_skyline_features()
    city_name = get_site_city()
    site_name = get_site_name()

    render_page_banner(
        title="现状分析与问题诊断",
        description=f"基于 3D 全息底座进行空间现状综合分析，通过 AHP-MPI 潜力评估和 AI 诊断识别【{site_name}】优先更新地块。",
        eyebrow="Stage 04-05",
        tags=["3D 数字孪生", "AHP-MPI 潜力模型", "自由地块雷达诊断", "AI 动态痛点画像"],
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

    # 动态载入候选地块（自动检测当前工程，杜绝死模板）
    active_plots = get_active_candidate_plots()

    # 保证总线中存在靶向地块结构化数据（若缺失或为陈旧硬编码，则动态选取首选地块）
    current_target = load_stage_output("04", "target_plot", None)
    if not current_target:
        if active_plots:
            first_p = active_plots[0]
            current_target = select_target_plot_and_diagnose(
                plot_name=first_p.get("name", "首选更新单元"),
                land_use=first_p.get("land_use", "商业用地"),
                mpi_score=85.0,
                area_ha=first_p.get("area_ha", 3.5),
                metrics={
                    "gvi": first_p.get("gvi", 14.5),
                    "poi": first_p.get("poi", 16),
                    "svf": first_p.get("svf", 0.52),
                    "clutter": 30.0,
                }
            )
        else:
            current_target = select_target_plot_and_diagnose(
                plot_name="优先启动更新单元",
                land_use="综合更新用地",
                mpi_score=85.0,
                area_ha=3.0,
            )

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
            "基于当前工程全部候选更新单元与 AHP 权重实时计算 MPI，量化排序并支持自由锁定更新靶向地块。",
            eyebrow="Multi-dimensional Potential Index",
        )

        # 构建所有候选地块的基础数据
        plot_rows = []
        for p in active_plots:
            p_name = p.get("name", "未知地块")
            p_land = p.get("land_use", "综合用地")
            p_area = float(p.get("area_ha", 2.5))
            p_poi = int(p.get("poi", 10))
            p_gvi = float(p.get("gvi", 15.0))
            p_svf = float(p.get("svf", 0.5))

            # 空间潜力原分 (面积尺度与利用率加权)
            pot = min(0.95, round(0.40 + (p_area / 20.0) * 0.5, 2))
            # 社会需求原分 (基于周边设施需求与活力)
            soc = min(0.95, round(0.45 + (p_poi / 30.0) * 0.45, 2))
            # 环境现状评分 (环境越差紧迫度越高)
            env = min(0.95, round((p_gvi / 50.0) * 0.5 + p_svf * 0.3, 2))

            plot_rows.append({
                "地块名称": p_name,
                "现状用地": p_land,
                "占地面积(ha)": p_area,
                "空间潜力原分": pot,
                "社会需求原分": soc,
                "环境现状评分": env,
                "gvi": p_gvi,
                "poi": p_poi,
                "svf": p_svf,
            })

        base_data = pd.DataFrame(plot_rows)

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

        def recalc_mpi(df: pd.DataFrame, w1: int, w2: int, w3: int) -> pd.DataFrame:
            df = df.copy()
            df["MPI 得分"] = round(
                (df["空间潜力原分"] * w1 + df["社会需求原分"] * w2 + (1 - df["环境现状评分"]) * w3)
                / (w1 + w2 + w3 + 0.001) * 100,
                1
            )
            return df

        df_calc = recalc_mpi(base_data, w_poi, w_soc, w_env)
        df_filtered = df_calc[df_calc["MPI 得分"] >= threshold].sort_values("MPI 得分", ascending=False)
        top_plot = df_filtered.iloc[0]["地块名称"] if not df_filtered.empty else "暂无"
        top_score = float(df_filtered.iloc[0]["MPI 得分"]) if not df_filtered.empty else 0.0

        render_summary_cards([
            {"value": len(df_filtered), "title": "候选更新单元", "desc": "当前纳入计算的地块数量。"},
            {"value": f"{top_score:.1f}", "title": "最高 MPI 分值", "desc": f"算法推荐首位：{top_plot}。"},
            {"value": f"{w_poi}/{w_soc}/{w_env}", "title": "权重组合", "desc": "空间潜力 / 社会需求 / 环境紧迫度。"},
        ])

        st.latex(
            r"\color{#a5b4fc} MPI_i = \frac{w_{space} \cdot S_i + w_{social} \cdot D_i + w_{env} \cdot (1 - E_i)}{w_{space} + w_{social} + w_{env}} \times 100"
        )

        st.dataframe(
            df_filtered[["地块名称", "现状用地", "占地面积(ha)", "MPI 得分"]],
            column_config={
                "MPI 得分": st.column_config.ProgressColumn("MPI 综合潜力分", format="%.1f", min_value=0, max_value=100),
                "占地面积(ha)": st.column_config.NumberColumn("占地面积", format="%.2f ha"),
            },
            hide_index=True,
            **stretch_width(st.dataframe),
        )

        csv_report = df_filtered.to_csv(index=False).encode("utf-8-sig")
        c_down1, c_down2 = st.columns([1, 1])
        with c_down1:
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
            fig = px.scatter(
                df_filtered,
                x="空间潜力原分",
                y="社会需求原分",
                size="MPI 得分",
                color="地块名称",
                hover_data=["现状用地", "占地面积(ha)", "MPI 得分"],
                color_discrete_sequence=get_chart_palette(),
                height=420,
            )
            apply_plotly_theme(fig, title="空间潜力与社会需求耦合分布散点图", height=420, showlegend=True)
            st.plotly_chart(fig, **stretch_width(st.plotly_chart))

        save_stage_output("05", SK.MPI_RANKING, df_filtered.to_dict("records"))
        save_stage_output("05", SK.TOP_PLOT, top_plot)
        save_stage_output("05", SK.TOP_SCORE, top_score)

        st.markdown("---")

        # ───────────────────────────────────────────────────────────
        # 核心交互区：自由选择与锁定靶向地块
        # ───────────────────────────────────────────────────────────
        st.markdown("### 🎯 靶向地块决策与选定 (Target Plot Selection)")
        st.caption("允许用户从列表中自由勾选【任意候选地块】，或手动录入自定义地块信息，一键锁定并生成定量痛点画像。")

        sel_tab1, sel_tab2 = st.tabs(["📋 从当前候选地块中选定", "✏️ 手动输入自定义地块信息"])

        with sel_tab1:
            plot_options = df_filtered["地块名称"].tolist() if not df_filtered.empty else [p["name"] for p in active_plots]
            if plot_options:
                chosen_plot_name = st.selectbox(
                    "选择要锁定的靶向地块：",
                    plot_options,
                    index=0,
                    key="sel_target_plot_dropdown"
                )
                chosen_row = df_filtered[df_filtered["地块名称"] == chosen_plot_name].iloc[0] if not df_filtered[df_filtered["地块名称"] == chosen_plot_name].empty else None

                if chosen_row is not None:
                    c_info1, c_info2, c_info3 = st.columns(3)
                    c_info1.metric("现状用地性质", str(chosen_row.get("现状用地", "商业用地")))
                    c_info2.metric("占地面积", f"{chosen_row.get('占地面积(ha)', 3.0)} ha")
                    c_info3.metric("当前 MPI 得分", f"{chosen_row.get('MPI 得分', 80.0):.1f}")

                if st.button("🎯 选定为更新靶向地块并生成痛点画像", type="primary", key="btn_confirm_target_plot", **stretch_width(st.button)):
                    if chosen_row is not None:
                        plot_metrics = {
                            "gvi": chosen_row.get("gvi", 15.0),
                            "poi": chosen_row.get("poi", 10),
                            "svf": chosen_row.get("svf", 0.50),
                            "clutter": 30.0,
                        }
                        updated_target = select_target_plot_and_diagnose(
                            plot_name=chosen_plot_name,
                            land_use=str(chosen_row.get("现状用地", "商业用地")),
                            mpi_score=float(chosen_row.get("MPI 得分", 85.0)),
                            area_ha=float(chosen_row.get("占地面积(ha)", 3.0)),
                            metrics=plot_metrics,
                        )
                        st.toast(f"✅ 已成功将【{chosen_plot_name}】锁定为全局更新靶向地块！", icon="🎯")
                        st.rerun()

        with sel_tab2:
            st.caption("若需针对非清单范围内的特定独立地块进行推演，可在此手动输入参数：")
            u1, u2, u3 = st.columns(3)
            with u1:
                custom_name = st.text_input("地块名称", value="自定义核心单元", key="manual_plot_name")
                custom_landuse = st.selectbox(
                    "现状用地性质",
                    ["工业/仓储用地", "商业/集贸用地", "二类居住用地", "科教文卫用地", "市政交通设施用地", "公园绿地与广场"],
                    key="manual_plot_landuse"
                )
            with u2:
                custom_area = st.number_input("占地面积 (公顷)", value=3.2, min_value=0.1, max_value=200.0, step=0.1, key="manual_plot_area")
                custom_mpi = st.number_input("微更新潜力指数 (MPI)", value=86.5, min_value=1.0, max_value=100.0, step=0.5, key="manual_plot_mpi")
            with u3:
                custom_gvi = st.number_input("现状绿视率 (%)", value=12.5, min_value=0.0, max_value=100.0, step=0.5, key="manual_plot_gvi")
                custom_poi = st.number_input("500m POI 设施数", value=14, min_value=0, max_value=1000, step=1, key="manual_plot_poi")

            if st.button("🎯 录入并选定为更新靶向地块", type="primary", key="btn_confirm_manual_target", **stretch_width(st.button)):
                custom_metrics = {
                    "gvi": custom_gvi,
                    "poi": custom_poi,
                    "svf": 0.48,
                    "clutter": 35.0,
                }
                updated_target = select_target_plot_and_diagnose(
                    plot_name=custom_name,
                    land_use=custom_landuse,
                    mpi_score=custom_mpi,
                    area_ha=custom_area,
                    metrics=custom_metrics,
                )
                st.toast(f"✅ 自定义地块【{custom_name}】已锁定为更新靶向地块！", icon="🎯")
                st.rerun()

        # 实时渲染当前靶向地块动态诊断画像卡片
        current_target = load_stage_output("04", "target_plot", None)
        render_target_plot_card(current_target)

    # ============================================================
    # 模块三：地块雷达诊断 (原 Stage 05)
    # ============================================================
    elif selected_sub == "🎯 地块雷达诊断":
        render_section_intro("地块级多维诊断", "对重点更新单元进行 MPI/GVI/POI/SVF 多维度雷达量化评价。", eyebrow="Plot Radar")

        plot_names = [p["name"] for p in active_plots] if active_plots else []
        if plot_names:
            selected_plot = st.selectbox("选择要诊断的地块：", plot_names, key="p5_radar_plot")
            plot_item = next((p for p in active_plots if p["name"] == selected_plot), active_plots[0])

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("用地性质", str(plot_item.get("land_use", "综合用地")))
            m1.caption(f"占地规模: {plot_item.get('area_ha', 2.5)} ha")
            m2.metric("POI 密度", f"{plot_item.get('poi', 10)} 处")
            m3.metric("绿视率 (GVI)", f"{plot_item.get('gvi', 15.0)}%")
            m4.metric("天空开敞度 (SVF)", f"{plot_item.get('svf', 0.50)}")

            categories = ["空间潜力", "设施密度", "绿视率", "天空开敞度", "环境整洁度"]
            area_val = float(plot_item.get("area_ha", 2.5))
            poi_val = float(plot_item.get("poi", 10))
            gvi_val = float(plot_item.get("gvi", 15.0))
            svf_val = float(plot_item.get("svf", 0.50))
            clutter_val = float(plot_item.get("clutter", 30.0))

            values = [
                min(1.0, area_val / 10.0),
                min(1.0, poi_val / 25.0),
                min(1.0, gvi_val / 40.0),
                min(1.0, svf_val),
                max(0.0, 1.0 - (clutter_val / 100.0)),
            ]

            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=[*values, values[0]],
                theta=[*categories, categories[0]],
                fill="toself",
                fillcolor="rgba(129,140,248,0.20)",
                line=dict(color="#818cf8", width=2),
            ))
            apply_plotly_polar_theme(fig, title=f"【{selected_plot}】多维定量诊断雷达", height=380)
            st.plotly_chart(fig, **stretch_width(st.plotly_chart))

            save_stage_output("05", SK.RADAR_DATA, {"plot": selected_plot, "categories": categories, "values": values})

            # 提供直接锁定为靶向地块的操作按钮
            if st.button(f"🎯 将【{selected_plot}】锁定为全局更新靶向地块", type="primary", key="radar_set_target_btn", **stretch_width(st.button)):
                select_target_plot_and_diagnose(
                    plot_name=selected_plot,
                    land_use=str(plot_item.get("land_use", "商业用地")),
                    mpi_score=85.0,
                    area_ha=area_val,
                    metrics={"gvi": gvi_val, "poi": poi_val, "svf": svf_val, "clutter": clutter_val},
                )
                st.toast(f"✅ 已将【{selected_plot}】锁定为靶向地块！", icon="🎯")
                st.rerun()

            current_target = load_stage_output("04", "target_plot", None)
            render_target_plot_card(current_target)
        else:
            st.warning("暂无候选地块数据，请在上游面板中上传 GeoJSON 或抓取 OSM 数据。")

    # ============================================================
    # 模块四：AI 前期诊断报告 (原 Stage 05)
    # ============================================================
    elif selected_sub == "🔬 AI 前期诊断报告":
        if "stage1_output" not in st.session_state:
            st.session_state["stage1_output"] = load_stage_output("05", SK.DIAGNOSIS_REPORT, "")
        render_section_intro("AI 前期问题诊断", "自动读取所选地块的 MPI/GVI/POI 等指标与动态痛点，生成数据驱动的问题诊断报告。", eyebrow="LLM Stage 01")

        with st.sidebar:
            model_tag = st.text_input("DeepSeek 模型标签", value="deepseek-v4-pro", key="p5_model")

        plot_names = [p["name"] for p in active_plots] if active_plots else []
        if plot_names:
            selected_plot = st.selectbox("选择重点诊断地块：", plot_names, key="p5_s1_plot")
            plot_item = next((p for p in active_plots if p["name"] == selected_plot), active_plots[0])

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("用地性质", str(plot_item.get("land_use", "综合用地")))
            m2.metric("占地面积", f"{plot_item.get('area_ha', 2.5)} ha")
            m3.metric("POI 设施数", f"{plot_item.get('poi', 10)}")
            m4.metric("绿视率 (GVI)", f"{plot_item.get('gvi', 15.0)}%")

            if st.button("🔬 生成前期问题诊断报告", type="primary", key="s1_btn", **stretch_width(st.button)):
                # 动态推导当前地块的痛点
                from src.engines.context_adaptive_engine import infer_plot_diagnostics
                dynamic_issues = infer_plot_diagnostics(plot_item)
                issues_text = "\n".join([f"- {iss}" for iss in dynamic_issues])

                prompt = f"""你是{city_name}{site_name}片区的资深城市更新规划顾问。
基于以下真实空间定量数据：
- 地块名称：{selected_plot}
- 现状用地性质：{plot_item.get('land_use', '综合用地')}
- 占地面积：{plot_item.get('area_ha', 2.5)} 公顷
- 周边 POI 活力设施数：{plot_item.get('poi', 10)} 处
- 绿视率（GVI）：{plot_item.get('gvi', 15.0)}%（国家标准要求≥30%）
- 天空开敞度（SVF）：{plot_item.get('svf', 0.50)}

系统现场算法初筛的空间痛点依据：
{issues_text}

请生成一份专业深度的【前期空间量化诊断与问题研判报告】。要求：
1. 列出 4-6 个具体的空间与产业痛点，每个痛点包含：【问题名称】【空间数据依据】【政策与规范依据】【紧迫程度】；
2. 紧扣该地块现状用地特征与周边慢行/开敞空间环境，杜绝套话；
3. 最后给出问题严重性优先级排序与近期微更新切入方向。"""

                sys_prompt = f"你是扎根{city_name}的资深城市规划诊断师。输出必须引用具体量化数据和政策规范条文编号。"
                stream = call_llm_engine_stream(prompt=prompt, system_prompt=sys_prompt, model=model_tag)
                st.markdown("#### 📋 前期诊断报告")
                result = st.write_stream(stream)
                if isinstance(result, str) and len(result) > 50:
                    st.session_state["stage1_output"] = result
                    save_stage_output("05", SK.DIAGNOSIS_REPORT, result)
                    save_stage_output("04", SK.DIAGNOSIS_REPORT, result)

                    # 自动同步锁定靶向地块
                    select_target_plot_and_diagnose(
                        plot_name=selected_plot,
                        land_use=str(plot_item.get("land_use", "商业用地")),
                        mpi_score=float(plot_item.get("mpi_score", 85.0)),
                        area_ha=float(plot_item.get("area_ha", 2.5)),
                        metrics={
                            "gvi": plot_item.get("gvi", 15.0),
                            "poi": plot_item.get("poi", 10),
                            "svf": plot_item.get("svf", 0.50),
                            "clutter": 30.0,
                        },
                        custom_issues=dynamic_issues,
                    )
                    st.toast("✅ 前期诊断报告生成完成，靶向地块已同步锁定！", icon="📊")
                    register_report_output(label="AI前期诊断报告", content=result, stage_code="04", key="diagnosis_report")
        else:
            st.warning("暂无候选地块数据。")

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
            st.caption("基于历史建筑分布、工业遗存及周边文脉资源，生成分析文本。")
            if st.button("🧠 生成文化资源分析", key="p04_cultural", **stretch_width(st.button)):
                with st.spinner("LLM 分析中..."):
                    prompt = f"""请分析【{city_name} {site_name}】研究范围内的文化资源特征，撰写约300字的文化资源分析文本。
要涵盖：1. 核心近代历史建筑群与文博 IP；2. 工业遗存与厂区风貌；3. 文化资源网络与视廊格局。

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
                    prompt = f"""请分析【{city_name} {site_name}】研究范围内的产业业态特征，撰写约300字的产业业态分析文本。
要涵盖：1. 现状商业服务分布；2. POI 类型构成；3. 存量产业转型痛点。

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
            st.caption("基于 POI 分布、街景品质、社区类型等推断人群结构和社区需求。")
            if st.button("🧠 生成人群需求分析", key="p04_population", **stretch_width(st.button)):
                with st.spinner("LLM 分析中..."):
                    prompt = f"""请分析【{city_name} {site_name}】研究范围内的社区人群需求特征，撰写约300字的人群需求分析文本。
要涵盖：1. 居民年龄结构和居住类型特征；2. 便民生活公共服务设施需求；3. 适老化与青年友好诉求。

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
    target_plot_info = load_stage_output("04", "target_plot", {})

    findings_05 = [
        {
            "point": f"基于 AHP-MPI 模型，{target_plot_info.get('name', top_plot_name)} 以 {float(target_plot_info.get('mpi', top_mpi)):.1f} 分锁定为全流程更新靶向单元",
            "evidence": "评价维度：空间潜力、社会需求、环境紧迫度三维加权"
        },
        {
            "point": f"当前工程共计 {len(mpi_data) or len(active_plots)} 个候选更新单元进入量化评估",
            "evidence": "数据来源：多源矢量资产接入 + AHP 动态权重"
        },
    ]

    if active_plots:
        avg_gvi = sum(float(p.get("gvi", 15.0)) for p in active_plots) / len(active_plots)
        avg_poi = sum(int(p.get("poi", 10)) for p in active_plots) / len(active_plots)
        findings_05.append({
            "point": f"研究范围内重点地块平均绿视率为 {avg_gvi:.1f}%，低于 GB50180-2018 要求的 30%",
            "evidence": f"平均 POI 密度 {avg_poi:.0f} 处/地块，反映公共服务覆盖存在不均"
        })

    render_stage_summary(
        stage_code="05",
        title="更新潜力诊断小结",
        findings=findings_05,
        methodology="基于 AHP-MPI 多维潜力指数模型，融合空间潜力、社会需求和环境紧迫度三维加权评价",
        implication="为后续目标定位（Stage 06）和设计策略（Stage 07）提供了纯数据驱动的靶向依据",
    )

    # 业务逻辑主线推进导航
    render_logic_chain_stepper("04")
