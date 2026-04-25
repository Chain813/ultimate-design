import streamlit as st
import pandas as pd
import json
import plotly.express as px
import streamlit.components.v1 as components
from src.ui.ui_components import render_top_nav
from src.config import ASSETS_DIR, DATA_FILES, SHP_FILES, STATIC_DIR, get_static_url

# ==========================================
# 💎 页面配置
# ==========================================
st.set_page_config(page_title="现状空间全景诊断 | 02 实验室", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

@st.cache_data(ttl=1800)
def load_base_map_data():
    def load_json(fp):
        with open(fp, 'r', encoding='utf-8') as f: return f.read()
    
    b_data = f"'{get_static_url('buildings.geojson')}'" if (STATIC_DIR / "buildings.geojson").exists() else "null"
    landuse_data = f"'{get_static_url('landuse.geojson')}'" if (STATIC_DIR / "landuse.geojson").exists() else "null"
    
    bound_path = SHP_FILES["boundary"]
    plots_path = SHP_FILES["plots"]
    bound_data = load_json(str(bound_path)) if bound_path.exists() else "null"
    plots_data = load_json(str(plots_path)) if plots_path.exists() else "null"
    return b_data, bound_data, plots_data, landuse_data

@st.cache_data(ttl=600)
def _load_3d_data():
    df_pts = pd.read_excel(DATA_FILES["points"])
    df_ana = pd.read_csv(DATA_FILES["gvi"])
    if 'Folder' in df_ana.columns:
        df_ana['ID'] = df_ana['Folder'].str.replace('Point_', '').astype(int)
        df_ana = df_ana.groupby('ID').mean(numeric_only=True).reset_index()
    return pd.merge(df_pts, df_ana, on='ID', how='inner')

def render_advanced_deckgl(is_3d=True, view_pitch=45, show_build=True, show_poi=False, show_traffic=False, show_landuse=False, show_lighting=True, sun_time=10, hex_payload="null", col_payload="null", heat_payload="null", is_xray=False, is_demo=False, pipe_payload="null"):
    b_data, bound_data, plots_data, landuse_data = load_base_map_data()
    if not show_build: b_data = "null"
    if not show_landuse: landuse_data = "null"
    
    poi_data_json = "null"
    if show_poi:
        try:
            df_poi = pd.read_csv(DATA_FILES["poi"], encoding='utf-8-sig').fillna("")
            poi_data_json = json.dumps(df_poi[['Lng', 'Lat', 'Name']].to_dict(orient="records"))
        except Exception:
            pass
        
    traffic_data_json = "null"
    if show_traffic:
        try:
            df_tr = pd.read_csv(DATA_FILES["traffic"], encoding='utf-8-sig').fillna("")
            traffic_data_json = json.dumps(df_tr[['Lng', 'Lat', 'Name']].to_dict(orient="records"))
        except Exception:
            pass

    with (ASSETS_DIR / "map3d_standalone.html").open("r", encoding="utf-8") as f:
        html = f.read()
    
    html = html.replace("/*__BUILDING_DATA__*/null/*__END_BUILDING__*/", b_data)
    html = html.replace("/*__BOUNDARY_DATA__*/null/*__END_BOUNDARY__*/", bound_data)
    html = html.replace("/*__PLOTS_DATA__*/null/*__END_PLOTS__*/", plots_data)
    html = html.replace("/*__POI_DATA__*/null/*__END_POI__*/", poi_data_json)
    html = html.replace("/*__TRAFFIC_DATA__*/null/*__END_TRAFFIC__*/", traffic_data_json)
    html = html.replace("/*__LANDUSE_DATA__*/null/*__END_LANDUSE__*/", landuse_data)
    html = html.replace("/*__IS_3D__*/true/*__END_IS_3D__*/", "true" if is_3d else "false")
    html = html.replace("/*__SHOW_LIGHTING__*/true/*__END_LIGHTING__*/", "true" if show_lighting else "false")
    html = html.replace("/*__SUN_TIME__*/10/*__END_SUN_TIME__*/", str(sun_time))
    
    html = html.replace("/*__HEX_PAYLOAD__*/null/*__END_HEX_PAY__*/", hex_payload)
    html = html.replace("/*__COL_PAYLOAD__*/null/*__END_COL_PAY__*/", col_payload)
    html = html.replace("/*__HEAT_PAYLOAD__*/null/*__END_HEAT_PAY__*/", heat_payload)
    html = html.replace("/*__PIPE_PAYLOAD__*/null/*__END_PIPE__*/", pipe_payload)
    
    html = html.replace("/*__IS_XRAY__*/false/*__END_IS_XRAY__*/", "true" if is_xray else "false")
    html = html.replace("/*__IS_DEMO__*/false/*__END_IS_DEMO__*/", "true" if is_demo else "false")
    html = html.replace("pitch: is_3d ? 45 : 0", f"pitch: {view_pitch}")
    
    st.markdown("""<style>
        iframe[title="st.iframe"] { border-radius: 12px !important; overflow: hidden !important; border: 1px solid rgba(99, 102, 241, 0.4); box-shadow: 0 10px 40px rgba(0,0,0,0.5); margin-bottom: 20px !important; }
    </style>""", unsafe_allow_html=True)
    components.html(html, height=800, scrolling=False)

# ==========================================
# 🌌 逻辑切换架构
# ==========================================
if 'lab02_active_sub' not in st.session_state:
    st.session_state.lab02_active_sub = "🏙️ 3D现状全息底座"

TAB_OPTIONS = ["🏙️ 3D现状全息底座", "📍 地块级诊断面板"]

selected_sub = st.radio("功能选择", TAB_OPTIONS, index=TAB_OPTIONS.index(st.session_state.lab02_active_sub) if st.session_state.lab02_active_sub in TAB_OPTIONS else 0, horizontal=True, label_visibility="collapsed", key="lab02_switcher")
st.session_state.lab02_active_sub = selected_sub
st.markdown("---")

# ==========================================
# 🌌 模块 A: 3D 现状空间全景诊断
# ==========================================
if selected_sub == "🏙️ 3D现状全息底座":
    
    # 顶部横向图层控制
    st.markdown("<p style='color: #818cf8; font-size: 14px; font-weight: 700; margin-bottom: 5px;'>🎛️ 多源异构诊断图层控制 (Layer Toggles)</p>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("**物理基底 (Physical Base)**")
        show_build = st.checkbox("🏙️ 基础建筑底座", value=True)
        show_landuse = st.checkbox("🧬 规划用地分类 (GB/T)", value=False)
    with col2:
        st.markdown("**社会活力 (Social Vitality)**")
        show_poi = st.checkbox("📍 城市公共服务 POI", value=False)
        show_traffic = st.checkbox("🚦 动态交通拥堵热力", value=False)
    with col3:
        st.markdown("**空间测度 (Spatial Quality)**")
        show_col = st.checkbox("🧪 街景品质 3D 柱体", value=True)
        col_metric = st.selectbox("核心指标渲染", ["GVI 绿视率", "SVF 开阔度", "Enclosure 围合感", "Clutter 杂乱度"], label_visibility="collapsed") if show_col else "GVI 绿视率"
    with col4:
        st.markdown("**渲染模式 (Render Engine)**")
        v_mode = st.radio("视角", ["🦅 3D 鸟瞰", "🗺️ 2D 平面", "🚶 漫游视角"], horizontal=True, label_visibility="collapsed")
        show_light = st.checkbox("☀️ 仿真光照与日影", value=True)

    # 数据准备
    col_payload = "null"
    heat_payload = "null"
    
    if show_traffic:
        try:
            df_poi = pd.read_csv(DATA_FILES["poi"], encoding='utf-8-sig')
            heat_data = df_poi[['Lng', 'Lat']].assign(Vitality=1.0).to_dict(orient='records')
            heat_payload = json.dumps({"data": heat_data, "metric": "Vitality", "radius": 80})
        except Exception:
            pass
        
    if show_col:
        try:
            df_3d = _load_3d_data().copy()
            cur_m = col_metric.split(" ")[0]
            if not df_3d.empty and cur_m in df_3d.columns:
                min_v, max_v = df_3d[cur_m].min(), df_3d[cur_m].max()
                if min_v == max_v: max_v = min_v + 1
                def get_col_color(val, v_min, v_max):
                    t = (val - v_min) / (v_max - v_min) if v_max > v_min else 0
                    if t < 0.5:
                        st_ = t * 2
                        return [int(6 + 133 * st_), int(182 - 90 * st_), int(212 + 34 * st_), 235]
                    else:
                        st_ = (t - 0.5) * 2
                        return [int(139 + 105 * st_), int(92 - 29 * st_), int(246 - 152 * st_), 235]
                df_3d["Dynamic_Color"] = df_3d[cur_m].apply(lambda v: get_col_color(v, min_v, max_v))
                col_payload = json.dumps({
                    "data": df_3d[['Lng', 'Lat', cur_m, 'Dynamic_Color', 'ID']].to_dict(orient='records'),
                    "metric": cur_m,
                    "elevationScale": 10,
                    "radius": 25
                })
        except Exception:
            pass
        
    pitch_3d = 45 if v_mode == "🦅 3D 鸟瞰" else (60 if "漫游" in v_mode else 0)
    
    st.markdown("---")
    
    render_advanced_deckgl(
        is_3d=(v_mode != "🗺️ 2D 平面"),
        view_pitch=pitch_3d,
        show_build=show_build, 
        show_poi=show_poi, 
        show_traffic=False, # We use heatmap for traffic in this view
        show_landuse=show_landuse,
        show_lighting=show_light,
        sun_time=10,
        col_payload=col_payload,
        heat_payload=heat_payload,
        is_xray=False,
        is_demo=False
    )

# ==========================================
# 🌌 模块 B: 地块级诊断面板
# ==========================================
elif selected_sub == "📍 地块级诊断面板":
    import plotly.graph_objects as go
    from src.engines.core_engine import get_plot_diagnostics

    st.markdown("### 📍 重点地块多维诊断面板")
    st.info("此面板基于重点更新单元，自动计算多维指标并生成诊断雷达图。")
    
    diagnostics = get_plot_diagnostics()

    if not diagnostics:
        st.warning("无法加载地块诊断数据。")
    else:
        df_diag = pd.DataFrame(diagnostics)
        df_diag_sorted = df_diag.sort_values("mpi_score", ascending=False)
        
        st.markdown("#### 更新潜力排行榜 (MPI)")
        st.dataframe(
            df_diag_sorted[["name", "area_ha", "poi_count", "gvi_mean", "mpi_score"]].rename(columns={
                "name": "地块名称", "area_ha": "面积(ha)", "poi_count": "POI数",
                "gvi_mean": "GVI均值", "mpi_score": "MPI得分"
            }),
            column_config={
                "MPI得分": st.column_config.ProgressColumn("MPI得分", format="%.1f", min_value=0, max_value=100)
            },
            use_container_width=True, hide_index=True
        )

        st.markdown("---")
        st.markdown("#### 逐地块多维指标雷达")
        
        all_gvi = [d["gvi_mean"] for d in diagnostics]
        all_svf = [d["svf_mean"] for d in diagnostics]
        all_enc = [d["enclosure_mean"] for d in diagnostics]
        all_clu = [d["clutter_mean"] for d in diagnostics]
        all_poi = [d["poi_count"] for d in diagnostics]
        all_mpi = [d["mpi_score"] for d in diagnostics]
        
        def relative_norm(val, arr, invert=False):
            mn, mx = min(arr), max(arr)
            if mx == mn: return 0.5
            ratio = (val - mn) / (mx - mn)
            if invert: ratio = 1.0 - ratio
            return 0.15 + ratio * 0.8

        plot_colors = ['#f59e0b', '#10b981', '#6366f1', '#ec4899', '#06b6d4']
        
        cols = st.columns(min(len(diagnostics), 3))
        for i, diag in enumerate(diagnostics):
            with cols[i % len(cols)]:
                categories = ['绿视率', '开阔度', '围合感', '整洁度', 'POI密度', 'MPI潜力']
                values = [
                    relative_norm(diag["gvi_mean"], all_gvi),
                    relative_norm(diag["svf_mean"], all_svf),
                    relative_norm(diag["enclosure_mean"], all_enc),
                    relative_norm(diag["clutter_mean"], all_clu, invert=True),
                    relative_norm(diag["poi_count"], all_poi),
                    relative_norm(diag["mpi_score"], all_mpi),
                ]
                c = plot_colors[i % len(plot_colors)]

                fig_radar = go.Figure(data=go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    fill='toself',
                    fillcolor=f'rgba({int(c[1:3],16)},{int(c[3:5],16)},{int(c[5:7],16)},0.15)',
                    line=dict(color=c, width=2.5),
                    name=diag["name"]
                ))
                fig_radar.update_layout(
                    polar=dict(
                        bgcolor='rgba(0,0,0,0)',
                        radialaxis=dict(visible=True, range=[0, 1], showticklabels=False, gridcolor='rgba(99,102,241,0.15)'),
                        angularaxis=dict(gridcolor='rgba(99,102,241,0.15)', color='#cbd5e1', tickfont=dict(size=10)),
                    ),
                    showlegend=False,
                    title=dict(text=f"{diag['name']}", font=dict(size=13, color=c)),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=45, r=45, t=45, b=25),
                    height=280,
                    font=dict(color='#94a3b8')
                )
                st.plotly_chart(fig_radar, use_container_width=True)
                
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("MPI", f"{diag['mpi_score']}", help="微更新潜力指数")
                mc2.metric("POI", f"{diag['poi_count']}", help="兴趣点数量")
                mc3.metric("GVI", f"{diag['gvi_mean']}%", help="绿视率")
                
                weak_points = []
                strategies = []
                if diag["gvi_mean"] < 15:
                    weak_points.append("绿视率严重不足")
                    strategies.append("建议在沿街界面植入垂直绿化墙体与口袋公园，参照 GB50180-2018 绿地率不低于 30%")
                elif diag["gvi_mean"] < 25:
                    weak_points.append("绿视率偏低")
                    strategies.append("可在人行道两侧补植行道树，结合微型雨水花园提升绿量感知")
                    
                if diag["clutter_mean"] > 30:
                    weak_points.append("街道视觉杂乱度偏高")
                    strategies.append("需整治架空线缆入地、统一店招尺度与色彩")
                    
                if diag["poi_count"] < 3:
                    weak_points.append("商业活力匮乏")
                    strategies.append("建议植入社区商业触媒如便利店、社区食堂，激活街区日间人流")
                elif diag["poi_count"] > 8:
                    strategies.append("商业密度充足，应优化业态结构，淘汰低端批发，引入文创零售")
                
                if diag["mpi_score"] > 75:
                    weak_points.insert(0, "高优先级更新单元")
                    strategies.insert(0, "该地块综合评分位于第一梯队，建议作为片区首批启动示范项目")
                
                conclusion_text = "该地块各项指标相对均衡，建议实施渐进式织补更新。"
                if weak_points:
                    wp_str = " | ".join(weak_points)
                    st_str = "<br>".join(strategies)
                    conclusion_text = f"<b>诊断结果：{wp_str}</b><br>{st_str}"
                
                st.markdown(f"""
                <div style="background: rgba(99,102,241,0.06); border: 1px solid rgba(99,102,241,0.2); border-radius: 10px; padding: 12px 14px; margin-top: 6px;">
                    <span style="font-size: 12px; font-weight: 700; color: {c};">靶向干预建议</span>
                    <div style="font-size: 11px; color: #e2e8f0; margin-top: 6px; line-height: 1.7;">{conclusion_text}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        csv_export = df_diag.to_csv(index=False).encode("utf-8-sig")
        st.download_button("导出地块诊断报告 (CSV)", csv_export, "Plot_Diagnostics_Report.csv", "text/csv", use_container_width=True)

st.markdown('<div style="height: 150px;"></div>', unsafe_allow_html=True)
