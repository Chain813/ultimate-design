import streamlit as st
import json
import os
from pathlib import Path
import base64
from html import escape
from src.ui.design_system import (
    render_page_banner,
    render_section_intro,
    render_summary_cards,
)
from src.ui.app_shell import (
    render_engine_status_alert,
    render_top_nav,
)
from src.engines.spatial_engine import get_hud_statistics, get_skyline_features
from src.config import get_static_url
from src.utils.service_check import check_engine_status
import pandas as pd
import streamlit.components.v1 as components

# 🌟 强制隐藏侧边栏，设定宽屏模式
st.set_page_config(page_title="系统主页", layout="wide", initial_sidebar_state="collapsed")

def get_page_route(page_path):
    """将文件路径转换为 Streamlit 路由 URL"""
    name = os.path.basename(page_path)
    if "_" in name and name.split("_")[0].isdigit():
        name = name.split("_", 1)[1]
    name = name.replace(".py", "")
    return name

@st.cache_data(ttl=3600)
def get_base64_image_v2(image_path):
    """将本地图片转换为 Base64 编码"""
    try:
        abs_path = os.path.abspath(image_path)
        if not os.path.exists(abs_path):
            return ""
        with open(abs_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception as e:
        return ""

# 加载顶部导航与系统状态警报
render_top_nav()
render_engine_status_alert()
top_stats = get_hud_statistics()

# 🎬 演示模式：最大化显示区域
if st.session_state.get("presentation_mode", False):
    st.markdown("""<style>
        .block-container { max-width: 100% !important; padding: 0.5rem 2rem !important; }
    </style>""", unsafe_allow_html=True)

# 🧪 隐藏主页原生的侧边栏组件
st.markdown("""
<style>
    [data-testid="collapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 📊 模块配置数据 (研究模块 01-04)
# ==========================================
MODULES = [
    {
        "title": "01 前期数据获取与现状分析",
        "desc": "任务解读、资料收集、现场调研、现状分析、问题诊断。",
        "image": "assets/01_data_overview.png",
        "path": "pages/01_前期数据获取与现状分析.py",
        "btn_label": "进入前期板块"
    },
    {
        "title": "02 中期概念生成与应对策略",
        "desc": "目标定位、设计策略、案例借鉴、协商共识。",
        "image": "assets/02_strategy_library.png",
        "path": "pages/02_中期概念生成与应对策略.py",
        "btn_label": "进入中期板块"
    },
    {
        "title": "03 后期设计生成与成果表达",
        "desc": "总体设计、专项系统、重点深化、实施路径、导则和成果表达。",
        "image": "assets/05_design_inference.png",
        "path": "pages/03_后期设计生成与成果表达.py",
        "btn_label": "进入后期板块"
    }
]

render_page_banner(
    title="长春伪满皇宫周边街区微更新支持平台",
    description="按城乡规划专业 13 阶段组织为前期、中期、后期三大板块，统一调度已有功能页与占位深化页。",
    eyebrow="Home",
    tags=["前期数据获取与现状分析", "中期概念生成与应对策略", "后期设计生成与成果表达"],
    metrics=[
        {"value": "150 公顷", "label": "研究范围", "meta": "围绕历史街区与周边复合片区"},
        {"value": len(MODULES), "label": "核心页面", "meta": "覆盖 01-05 全链路实验室"},
        {"value": top_stats["poi_count"], "label": "POI 资产", "meta": "挂载到空间活力诊断的数据点"},
        {"value": top_stats["gvi_count"], "label": "街景样本", "meta": "支撑环境品质与风貌分析"},
    ],
)
render_summary_cards(
    [
        {"value": "动态空间评价", "title": "Spatial Assessment", "desc": "以地块、建筑、街景和设施数据为基础诊断更新潜力。"},
        {"value": "生成式视觉推演", "title": "Generative Pre-rendering", "desc": "将保护要求与设计策略转成可比选的空间图景。"},
        {"value": "多主体协同测算", "title": "Multi-agent Decision", "desc": "模拟居民、开发商与规划师之间的协商与约束平衡。"},
    ]
)
st.markdown(
    """
    <div class="content-panel">
        <h3>研究范围声明与系统口径</h3>
        <p><strong>当前基址合规性：</strong>系统所呈现的建筑三维模型、基础表格和街景照片等核心数据，
        均严格落在《任务书》与《开题报告》限定的研究区域内。</p>
        <p><strong>未来跨城拓展性：</strong>系统采用界面与数据分离的方式，只需替换地图与数据表即可迁移到新的研究片区，而不必重写核心逻辑。</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 📖 云端访客指南与本地部署教程 (Cloud Visitor Guide)
# ==========================================
engine_status_home = check_engine_status()
if not engine_status_home.sd or not engine_status_home.gemma:
    with st.expander("🚀 获取完整算力：本地化部署与完美体验教程 (Cloud Visitor Guide)", expanded=False):
        st.markdown("""
        ### ☁️ 云端演示模式说明 (Cloud Limitations)
        您当前访问的是部署在公有云服务器上的**在线演示版本**。
        由于标准云端环境缺乏 GPU 算力支持，本系统的两大核心 AI 引擎已自动切换为**预置演示模式 (Demo Mode)**：
        - 🎨 **视觉渲染引擎 (Stable Diffusion)**：生成式风貌推演功能将返回预先渲染好的高质量参考图。
        - 🧠 **决策博弈引擎 (Ollama/Gemma)**：多主体协商对话将返回结构化的预置专家推演剧本。
        
        *注：地图测度引擎 (Deck.GL)、AHP 评估算法、资产管理等核心逻辑不受影响，均可正常交互体验。*

        ---

        ### 💻 如何完美体验本项目 (Local Deployment Tutorial)
        若您希望解锁真实、实时的 AIGC 图像生成与 LLM 智能对话推演能力，请按照以下步骤将本项目部署至您拥有独立显卡（建议 8GB+ 显存）的本地计算机：

        #### 1. 获取项目源码与核心数据
        前往本项目的 GitHub 仓库 Clone 最新代码，并安装项目所需的全部 Python 依赖。
        ```bash
        git clone https://github.com/YourUsername/ultimateDESIGN.git
        cd ultimateDESIGN
        pip install -r requirements.txt
        ```

        #### 2. 挂载本地大模型引擎 (Ollama)
        前往 [Ollama 官网](https://ollama.com/) 下载并安装引擎。打开终端并运行以下命令，系统将在后台自动下载并运行经过量化压缩的 Gemma 模型：
        ```bash
        ollama run gemma4:e2b-it-q4_K_M
        ```
        *(引擎默认将在 `http://127.0.0.1:11434` 端口保持监听，本系统会自动捕捉该端口)*

        #### 3. 挂载视觉渲染引擎 (Stable Diffusion WebUI)
        启动您本地的 SD WebUI（如秋叶一键包），**最关键的一步**是在启动参数中添加 API 开放指令：
        ```bash
        # 在您的 webui-user.bat (Windows) 或 webui-user.sh (Mac/Linux) 中添加：
        set COMMANDLINE_ARGS=--api --listen
        ```
        *(确保 SD WebUI 在 `http://127.0.0.1:7860` 运行。系统将通过此接口发送 ControlNet 骨架约束与 Prompt)*

        #### 4. 启动最终极的数字孪生总台
        当上述两大底层算力引擎均启动并处于监听状态后，回到本项目的根目录，运行以下命令：
        ```bash
        streamlit run app.py
        ```
        此时，主页的 **「底层算力设施调用监控」HUD** 将全面亮起🟢绿灯。恭喜您，已成功解锁 100% 算力全开的循证微更新平台！
        """)

# ==========================================
# 🛡️ 技术监测 HUD (实时探测)
# ==========================================
def render_status_hud():
    """渲染深度客制化、带技术背书的监测 HUD (已同步全局探测逻辑)"""
    engine_status = check_engine_status()
    sd_online = engine_status.sd
    gemma_online = engine_status.gemma
    hud_stats = get_hud_statistics()

    sd_status = "已联机" if sd_online else "未挂载"
    gemma_status = "已联机" if gemma_online else "未挂载"
    sd_color = "#4ADE80" if sd_online else "#EF4444"
    gemma_color = "#4ADE80" if gemma_online else "#EF4444"

    st.markdown(f"""
<section class="platform-hud" style="--sd-color:{sd_color}; --gemma-color:{gemma_color};">
    <article class="platform-hud-card">
        <div class="platform-hud-title">底层算力设施</div>
        <div class="platform-hud-row"><span class="status-dot-gemma"></span><b>多主体交互大语言模型</b><em>{gemma_status}</em></div>
        <p>承担角色推理与政策文书生成，依托 Local Ollama。</p>
    </article>
    <article class="platform-hud-card">
        <div class="platform-hud-title">视觉渲染引擎</div>
        <div class="platform-hud-row"><span class="status-dot-sd"></span><b>空间影像衍生网络</b><em>{sd_status}</em></div>
        <p>承担街景风貌意向图计算，依托 Stable Diffusion。</p>
    </article>
    <article class="platform-hud-card">
        <div class="platform-hud-title">空间与资料引擎</div>
        <div class="platform-hud-row"><span class="status-dot-static"></span><b>测度 / 文档解析</b><em>正常</em></div>
        <p>AHP 测度与法定规划图文 PDF 萃取已就绪。</p>
    </article>
    <article class="platform-hud-card">
        <div class="platform-hud-title">数据资产挂载</div>
        <div class="platform-hud-row"><span class="status-dot-static"></span><b>{hud_stats['poi_count']} POI / {hud_stats['gvi_count']} 街景</b><em>已挂载</em></div>
        <p>研究边界约 {hud_stats['boundary_ha']} 公顷，含 POI、UGC 与街景采样。</p>
    </article>
</section>
""", unsafe_allow_html=True)

def render_skyline_hud():
    """在地图下方渲染横向天际线指标面板"""
    skyline_stats = get_skyline_features()
    st.markdown(f"""
    <div class="skyline-panel">
        <div class="row">
            <div class="metric">
                <div class="metric-label" style="color: #818cf8;">🏙️ 区域天际线地标高度</div>
                <div class="metric-value">{skyline_stats['max_height']}<span class="metric-unit">m</span></div>
            </div>
            <div class="metric">
                <div class="metric-label" style="color: #10b981;">🏢 平均建筑高度</div>
                <div class="metric-value">{skyline_stats['avg_height']}<span class="metric-unit">m</span></div>
            </div>
            <div class="metric">
                <div class="metric-label" style="color: #f59e0b;">📈 高层建筑占比</div>
                <div class="metric-value">{skyline_stats['high_rise_ratio']}<span class="metric-unit">%</span></div>
            </div>
            <div class="metric" style="border-right: none;">
                <div class="metric-label" style="color: #ec4899;">🏗️ 测区建筑总数</div>
                <div class="metric-value">{skyline_stats['building_count']}<span class="metric-unit">栋</span></div>
            </div>
        </div>
        <div class="footnote">
            * 注：天际线高度数据基于建筑基底 Floor 字段按标准层高 3.5m 换算所得
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# 🚀 渲染执行
# ==========================================
render_section_intro("平台状态", "先确认底层引擎和资产挂载情况，再进入地图与模块工作流。", eyebrow="Runtime")
render_status_hud()

# 🗺️ 街区范围及改造红线 (Project Boundary)
render_section_intro("街区范围及改造红线", "统一查看研究边界、重点更新单元、建筑底图和辅助图层。", eyebrow="Project Boundary")
@st.cache_data(ttl=300)
def load_map_data(file_path):
    path = Path(file_path)
    if not path.exists(): return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def render_project_map():
    # 🎨 视图模式选择器 (置于显眼位置)
    view_mode = st.radio(
        "🗺️ 视图模式", 
        ["🦅 3D 仿真视角", "🗺️ 2D 空间肌理"], 
        index=0, 
        horizontal=True, 
        key="global_map_view_mode"
    )

    # 🚀 --- 统一高性能渲染链路 (Deck.GL 分离组件加速版) ---
    is_3d_mode = "3D" in view_mode
    import streamlit.components.v1 as components

    layer_cols = st.columns(6)
    with layer_cols[0]:
        show_boundary = st.checkbox("🔲 规划红线", value=True, key="map_boundary")
    with layer_cols[1]:
        show_plots = st.checkbox("✴️ 重点更新单元", value=True, key="map_plots")
    with layer_cols[2]:
        show_buildings = st.checkbox("🏢 建筑轮廓", value=True, key="map_buildings")
    with layer_cols[3]:
        show_poi = st.checkbox("📍 POI 设施分布", value=False, key="map_poi")
    with layer_cols[4]:
        show_traffic = st.checkbox("🚦 交通拥堵热点", value=False, key="map_traffic")
    with layer_cols[5]:
        show_landuse = st.checkbox("🧬 规划用地底色", value=False, key="map_landuse")

    # ☀️ 光照控制 (单独一行)
    show_lighting = st.checkbox("☀️ 开启仿真光照", value=is_3d_mode, key="map_lighting")

    # 🛠️ 仿真时间控制
    sun_time = st.slider("🕐 日照推演 (00:00 - 23:00)", 0, 23, 10, key="map_sun_time")

    # 1. 独立获取并 JSON 序列化数据（建筑大模型使用流媒体路由，规避渲染引擎强行注入导致的假死）
    b_data_json = f"'{get_static_url('buildings.geojson')}'" if show_buildings else "null"
    bound_data_json = json.dumps(load_map_data("data/shp/Boundary_Scope.geojson")) if show_boundary else "null"
    plots_data_json = json.dumps(load_map_data("data/shp/Key_Plots_District.json")) if show_plots else "null"
    
    poi_data_json = "null"
    if show_poi:
        try:
            from src.engines.spatial_engine import get_merged_poi_data
            df_poi = get_merged_poi_data().fillna("")
            if not df_poi.empty:
                poi_data_json = json.dumps(df_poi[['Lng', 'Lat', 'Name']].to_dict(orient="records"))
        except Exception:
            pass  # POI is optional for map overlay
        
    traffic_data_json = "null"
    if show_traffic:
        try:
            df_tr = pd.read_csv("data/Changchun_Traffic_Real.csv", encoding='utf-8-sig').fillna("")
            traffic_data_json = json.dumps(df_tr[['Lng', 'Lat', 'Name']].to_dict(orient="records"))
        except Exception:
            pass  # Traffic data is optional for map overlay

    # 🧬 用地数据层 (采用 URL 异步流模式加载，规避大文件注入导致的假死)
    landuse_data_json = f"'{get_static_url('landuse.geojson')}'" if show_landuse else "null"

    # 2. 读取纯粹的高性能 WebGL HTML 骨架
    try:
        with open("assets/map3d_standalone.html", "r", encoding="utf-8") as f:
            html_template = f.read()
            
        # 3. 外科手术式闪电替换，将百万级节点数据直接输送入前端内存
        html_template = html_template.replace("/*__BUILDING_DATA__*/null/*__END_BUILDING__*/", b_data_json)
        html_template = html_template.replace("/*__BOUNDARY_DATA__*/null/*__END_BOUNDARY__*/", bound_data_json)
        html_template = html_template.replace("/*__PLOTS_DATA__*/null/*__END_PLOTS__*/", plots_data_json)
        html_template = html_template.replace("/*__POI_DATA__*/null/*__END_POI__*/", poi_data_json)
        html_template = html_template.replace("/*__TRAFFIC_DATA__*/null/*__END_TRAFFIC__*/", traffic_data_json)
        html_template = html_template.replace("/*__LANDUSE_DATA__*/null/*__END_LANDUSE__*/", landuse_data_json)
        # 注入模式切换标志
        html_template = html_template.replace("/*__IS_3D__*/true/*__END_IS_3D__*/", "true" if is_3d_mode else "false")
        # 注入光照显示与时间标志
        html_template = html_template.replace("/*__SHOW_LIGHTING__*/true/*__END_LIGHTING__*/", "true" if show_lighting else "false")
        html_template = html_template.replace("/*__SUN_TIME__*/10/*__END_SUN_TIME__*/", str(sun_time))
        
        # 4. 定制化组件外观，保持科技感一致性，防范滚动渗透
        st.markdown("""<style>
            iframe[title="st.iframe"] { border-radius: 18px !important; overflow: hidden !important; border: 1px solid rgba(99, 102, 241, 0.4); box-shadow: 0 10px 40px rgba(0,0,0,0.5); }
        </style>""", unsafe_allow_html=True)
        
        # 以非滚动组件形式释放
        components.html(html_template, height=650, scrolling=False)
    except Exception as e:
        st.error(f"地图组件核心加载失败: {str(e)}")

render_project_map()
render_skyline_hud()

st.markdown("<br><br>", unsafe_allow_html=True)

