import streamlit as st
import pandas as pd
import json
import streamlit.components.v1 as components
from src.ui.ui_components import render_top_nav
from src.config import ASSETS_DIR, DATA_FILES, SHP_FILES, STATIC_DIR, get_static_url

st.set_page_config(page_title="更新设计成果展示 | 05 实验室", layout="wide", initial_sidebar_state="collapsed")
render_top_nav()

@st.cache_data
def load_base_map_data():
    def load_json(fp):
        with open(fp, 'r', encoding='utf-8') as f: return f.read()
    
    b_data = f"'{get_static_url('buildings.geojson')}'" if (STATIC_DIR / "buildings.geojson").exists() else "null"
    bound_path = SHP_FILES["boundary"]
    plots_path = SHP_FILES["plots"]
    bound_data = load_json(str(bound_path)) if bound_path.exists() else "null"
    plots_data = load_json(str(plots_path)) if plots_path.exists() else "null"
    return b_data, bound_data, plots_data

@st.cache_data
def _load_3d_data():
    df_pts = pd.read_excel(DATA_FILES["points"])
    df_ana = pd.read_csv(DATA_FILES["gvi"])
    if 'Folder' in df_ana.columns:
        df_ana['ID'] = df_ana['Folder'].str.replace('Point_', '').astype(int)
        df_ana = df_ana.groupby('ID').mean(numeric_only=True).reset_index()
    return pd.merge(df_pts, df_ana, on='ID', how='inner')

def render_future_deckgl(is_3d=True, view_pitch=60, is_demo=True, is_xray=False):
    b_data, bound_data, plots_data = load_base_map_data()
    
    with (ASSETS_DIR / "map3d_standalone.html").open("r", encoding="utf-8") as f:
        html = f.read()
    
    html = html.replace("/*__BUILDING_DATA__*/null/*__END_BUILDING__*/", b_data)
    html = html.replace("/*__BOUNDARY_DATA__*/null/*__END_BOUNDARY__*/", bound_data)
    html = html.replace("/*__PLOTS_DATA__*/null/*__END_PLOTS__*/", plots_data)
    
    # Hide baseline layers
    html = html.replace("/*__POI_DATA__*/null/*__END_POI__*/", "null")
    html = html.replace("/*__TRAFFIC_DATA__*/null/*__END_TRAFFIC__*/", "null")
    html = html.replace("/*__LANDUSE_DATA__*/null/*__END_LANDUSE__*/", "null")
    html = html.replace("/*__HEX_PAYLOAD__*/null/*__END_HEX_PAY__*/", "null")
    html = html.replace("/*__COL_PAYLOAD__*/null/*__END_COL_PAY__*/", "null")
    html = html.replace("/*__HEAT_PAYLOAD__*/null/*__END_HEAT_PAY__*/", "null")
    
    html = html.replace("/*__IS_3D__*/true/*__END_IS_3D__*/", "true" if is_3d else "false")
    html = html.replace("/*__SHOW_LIGHTING__*/true/*__END_LIGHTING__*/", "true")
    html = html.replace("/*__SUN_TIME__*/10/*__END_SUN_TIME__*/", "14")
    
    # 4D Morphing & X-Ray
    html = html.replace("/*__IS_XRAY__*/false/*__END_IS_XRAY__*/", "true" if is_xray else "false")
    html = html.replace("/*__IS_DEMO__*/false/*__END_IS_DEMO__*/", "true" if is_demo else "false")
    
    pipe_payload = "null"
    if is_xray:
        try:
            df_3d = _load_3d_data().copy()
            pipes = []
            for _, row in df_3d.iterrows():
                lng, lat = row['Lng'], row['Lat']
                pipes.append({"path": [[lng, lat], [lng + 0.001, lat + 0.001]], "type": "water"})
                pipes.append({"path": [[lng, lat], [lng - 0.001, lat + 0.0005]], "type": "power"})
            pipe_payload = json.dumps(pipes)
        except: pass
        
    html = html.replace("/*__PIPE_PAYLOAD__*/null/*__END_PIPE__*/", pipe_payload)
    html = html.replace("pitch: is_3d ? 45 : 0", f"pitch: {view_pitch}")
    
    st.markdown("""<style>
        iframe[title="st.iframe"] { border-radius: 12px !important; overflow: hidden !important; border: 1px solid rgba(99, 102, 241, 0.4); box-shadow: 0 10px 40px rgba(0,0,0,0.5); margin-bottom: 20px !important; }
    </style>""", unsafe_allow_html=True)
    components.html(html, height=850, scrolling=False)


# ==========================================
# 🌌 逻辑切换架构
# ==========================================
if 'lab05_active_sub' not in st.session_state:
    st.session_state.lab05_active_sub = "🏙️ 更新设计大地图"

TAB_OPTIONS = ["🏙️ 更新设计大地图", "📑 规划文本成果", "🖼️ 重点地块效果图"]

selected_sub = st.radio("功能选择", TAB_OPTIONS, index=TAB_OPTIONS.index(st.session_state.lab05_active_sub) if st.session_state.lab05_active_sub in TAB_OPTIONS else 0, horizontal=True, label_visibility="collapsed", key="lab05_switcher")
st.session_state.lab05_active_sub = selected_sub
st.markdown("---")


if selected_sub == "🏙️ 更新设计大地图":
    st.markdown("<p style='color: #818cf8; font-size: 14px; font-weight: 700; margin-bottom: 5px;'>🚀 未来图景推演引擎 (Future Scenario Engine)</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,2])
    with col1:
        enable_demo = st.checkbox("🔥 启动违建塌缩拆除 (4D Morphing)", value=True)
    with col2:
        enable_xray = st.checkbox("🔬 地下微循环管网透视 (X-Ray)", value=False)
    with col3:
        st.info("💡 紫色：修缮保护 | 黄色：功能改造 | 红色/塌缩：拆除腾退 | 绿色：公园绿地")
        
    pitch_3d = 65 if enable_xray else 45
    
    render_future_deckgl(
        is_3d=True,
        view_pitch=pitch_3d,
        is_demo=enable_demo,
        is_xray=enable_xray
    )

elif selected_sub == "📑 规划文本成果":
    st.markdown("### 📑 宽城区历史文化街区微更新规划导则 (最终汇编版)")
    st.info("基于 01-04 实验室的诊断分析与 LLM 博弈共识，自动输出规范化行政导则。")
    
    with st.expander("第一章 总则", expanded=True):
        st.markdown("""
        **1.1 规划目的**
        为贯彻落实长春市城市更新总体战略，科学指导宽城区伪满皇宫周边历史文化街区的保护与复兴工作，制定本导则。
        
        **1.2 规划原则**
        - **修旧如旧，存量提质**：严格保护历史街区真实性。
        - **针灸更新，活力激发**：以微小尺度的介入带动全局活力。
        - **设施完善，韧性提升**：全面升级地下水电管网系统（见 X-Ray 管线规划图）。
        """)
        
    with st.expander("第二章 空间留改拆策略分布", expanded=True):
        st.markdown("""
        **2.1 历史风貌保护区 (紫色区域)**
        涉及伪满皇宫及周边 15 处挂牌历史建筑。严格禁止改变外立面材质，允许内部进行符合现代安全标准的修缮。
        
        **2.2 功能活化改造区 (黄色区域)**
        对 80 年代建成的低效厂房及废弃商业裙楼进行“腾笼换鸟”，植入文创零售与青创办公空间。
        
        **2.3 拆除腾退区 (动态塌缩区域)**
        针对 MPI 评分极高且建筑老化严重、存在安全隐患的 3 层以下违章建筑实施拆除，释放的用地优先作为绿地口袋公园（提升 GVI）及公共停车场。
        """)
        
    # 🚀 动态生成官方 Word 公文并提供下载 (替代原本的 Mock Markdown)
    from src.utils.document_generator import generate_official_word_doc
    
    full_text = """
# 第一章 总则
## 1.1 规划目的
为贯彻落实长春市城市更新总体战略，科学指导宽城区伪满皇宫周边历史文化街区的保护与复兴工作，制定本导则。本导则汲取了多主体（公众、开发商、规划师）的大模型博弈共识。

## 1.2 规划原则
- 修旧如旧，存量提质：严格保护历史街区真实性。
- 针灸更新，活力激发：以微小尺度的介入带动全局活力。
- 设施完善，韧性提升：全面升级地下水电管网系统（见 X-Ray 管线规划图）。

# 第二章 空间留改拆策略分布
## 2.1 历史风貌保护区 (紫色区域)
涉及伪满皇宫及周边 15 处挂牌历史建筑。严格禁止改变外立面材质，允许内部进行符合现代安全标准的修缮。

## 2.2 功能活化改造区 (黄色区域)
对 80 年代建成的低效厂房及废弃商业裙楼进行“腾笼换鸟”，植入文创零售与青创办公空间。

## 2.3 拆除腾退区 (动态塌缩区域)
针对 MPI 评分极高且建筑老化严重、存在安全隐患的违章建筑实施拆除，释放的用地优先作为绿地口袋公园及公共停车场。
    """
    
    # 读取跨页面 Session 中的 AIGC 成果图
    aigc_history = st.session_state.get('aigc_history', [])
    
    docx_io = generate_official_word_doc(
        title="宽城区历史文化街区微更新规划导则", 
        text_content=full_text,
        aigc_history=aigc_history
    )
    
    st.download_button(
        label="📥 一键导出带红头公文 (Word 格式，含 AIGC 图集)",
        data=docx_io,
        file_name="宽城区历史文化街区微更新规划导则(AI自动生成版).docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
        type="primary"
    )

elif selected_sub == "🖼️ 重点地块效果图":
    st.markdown("### 🖼️ AIGC 意向方案图集")
    st.caption("展示基于 03 实验室 ControlNet 稳定约束生成的最终街景修缮效果。")
    
    # Placeholder images using dicebear or unspash or solid colors
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 节点 A：历史建筑沿街立面修缮")
        st.image("https://images.unsplash.com/photo-1513694203232-719a280e022f?q=80&w=800&auto=format&fit=crop", caption="修缮后意向 (保留历史砖墙，移除杂乱店招)")
    with col2:
        st.markdown("#### 节点 B：废弃厂房微更新活化")
        st.image("https://images.unsplash.com/photo-1541888056262-127993afedcb?q=80&w=800&auto=format&fit=crop", caption="改造后意向 (植入玻璃幕墙与文创商业街)")
