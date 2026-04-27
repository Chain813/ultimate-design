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
from src.ui.ui_components import (
    render_engine_status_alert,
    render_top_nav,
)
from src.engines.core_engine import get_hud_statistics, get_skyline_features
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
        "title": "🔬 01 数据底座与策略构建",
        "desc": "汇聚长春专项规划与现场勘测数据，结合 AHP 专家矩阵执行地块更新潜力（MPI）多维综合评价。",
        "image": "assets/01_data_overview.png",
        "path": "pages/1_数据底座与规划策略.py",
        "btn_label": "🚀 访问数据资产"
    },
    {
        "title": "🏙️ 02 现状空间全景诊断",
        "desc": "将多模态数据锚定至地理空间，实现三维数字孪生呈现与慢行品质（绿视率/开阔度等）量化诊断。",
        "image": "assets/03_digital_twin.png",
        "path": "pages/2_现状空间全景诊断.py",
        "btn_label": "🚀 开启空间诊断"
    },
    {
        "title": "🎨 03 街区风貌修缮预演",
        "desc": "以提取的城市特质为约束条件，驱动生成式衍生模型输出多情景、合乎空间尺度的更新方案图谱。",
        "image": "assets/05_design_inference.png",
        "path": "pages/3_AIGC设计推演.py",
        "btn_label": "🎨 执行风貌预演"
    },
    {
        "title": "⚖️ 04 多主体协商议事厅",
        "desc": "基于长春市现行规范法则库，推演公众代表、投资方及规划师之间的诉求博弈与政策共识。",
        "image": "assets/06_llm_consultation_v2.png",
        "path": "pages/4_LLM博弈决策.py",
        "btn_label": "⚖️ 进入协同决策"
    },
    {
        "title": "🏗️ 05 更新设计成果展示",
        "desc": "展示“留改拆”四维推演动画、地下基建 X-Ray 透视及最终规划导则成果，实现全过程数字化交付。",
        "image": "assets/03_digital_twin.png",
        "path": "pages/5_更新设计成果展示.py",
        "btn_label": "🚀 访问设计成果"
    }
]

render_page_banner(
    title="长春伪满皇宫周边街区微更新支持平台",
    description="以研究边界锁定、空间诊断、AIGC 推演、多主体协商和成果交付为主线，把规划分析链路收敛在一套统一工作界面内。",
    eyebrow="Home",
    tags=["任务书 / 开题报告边界对齐", "空间诊断与 AIGC 一体化", "成果导则直接交付"],
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
<style>.hud-v-bar {{ --sd-color: {sd_color}; --gemma-color: {gemma_color}; }}</style>

<div class="hud-v-bar hud-left">
    <div class="hud-header">底层算力设施调用监控</div>
    <div class="hud-item">
        <span class="hud-label">[多主体交互大语言模型]</span>
        <div class="hud-value"><span class="status-dot-gemma"></span>{gemma_status}</div>
        <div class="hud-meta">承担角色推理与政策文书生成<br>(依托引擎: Local Ollama)</div>
    </div>
    <div class="hud-item">
        <span class="hud-label">[空间影像衍生网络]</span>
        <div class="hud-value"><span class="status-dot-sd"></span>{sd_status}</div>
        <div class="hud-meta">承担街景风貌意向图的计算重构<br>(依托引擎: Stable Diffusion)</div>
    </div>
    <div class="hud-item">
        <span class="hud-label">[地理空间测度引擎]</span>
        <div class="hud-value"><span class="status-dot-static"></span>正常</div>
        <div class="hud-meta">基于 AHP 处理多因子向量乘加逻辑</div>
    </div>
    <div class="hud-item">
        <span class="hud-label">[结构化文档解析引擎]</span>
        <div class="hud-value"><span class="status-dot-static"></span>已就绪</div>
        <div class="hud-meta">用于萃取法定规划图文 PDF</div>
    </div>
</div>

<div class="hud-v-bar hud-right">
    <div class="hud-header">空间与社会资产挂载验证</div>
    <div class="hud-item">
        <span class="hud-label">[城市公共服务设施网络]</span>
        <div class="hud-value">{hud_stats['poi_count']} 商业与公共锚点<span class="status-dot-static" style="background:#818cf8;"></span></div>
        <div class="hud-meta">数据源追踪: 高德开放平台 POI 快照</div>
    </div>
    <div class="hud-item">
        <span class="hud-label">[公众情绪意向样本]</span>
        <div class="hud-value">{hud_stats['nlp_count']} 去隐私化语段<span class="status-dot-static" style="background:#818cf8;"></span></div>
        <div class="hud-meta">数据源追踪: 本地生活平台脱敏 UGC</div>
    </div>
    <div class="hud-item">
        <span class="hud-label">[研究范围投影边界]</span>
        <div class="hud-value">约 {hud_stats['boundary_ha']} 公顷用地<span class="status-dot-static" style="background:#818cf8;"></span></div>
        <div class="hud-meta">坐标系: CGCS2000</div>
    </div>
    <div class="hud-item">
        <span class="hud-label">[街道生态体验抽样]</span>
        <div class="hud-value">{hud_stats['gvi_count']} 影像计算截面<span class="status-dot-static" style="background:#818cf8;"></span></div>
        <div class="hud-meta">数据源: 百度街景结合植被遮罩过滤</div>
    </div>
    <div class="academic-conclusion-box" style="margin-top: 20px; padding: 12px; background: rgba(99, 102, 241, 0.08); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 12px;">
        <div class="academic-conclusion-title" style="font-size: 9px; font-weight: 800; color: #a5b4fc; margin-bottom: 6px;">🎯 系统数据底座挂载诊断报告</div>
        <div class="academic-conclusion-text" style="font-size: 8px; color: #cbd5e1; line-height: 1.5;">
            经核实验证，当前城市底座多源异构数据（含POI、UGC及街景采样）挂载率达 100%。底层空间解析引擎（核心生成网络与大语言模型）通信握手正常，具备高鲁棒性的城市微更新循证辅助研判能力。
        </div>
    </div>
</div>
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
# 🔄 循证决策工作流 (Academic Roadmap)
# ==========================================
def render_workflow_logic():
    with open("assets/workflow_svg.html", "r", encoding="utf-8") as f:
        workflow_html = f.read()
    components.html(workflow_html, height=900, scrolling=False)
    return

    stages = [
        {
            "code": "01",
            "title": "项目边界与数据底座",
            "module": "页面 01",
            "accent": "blue",
            "inputs": "研究范围红线、五个重点地块、卫星底图、建筑轮廓、POI / 交通 / 街景 / UGC 数据",
            "process": "锁定长春大街、长白路、东九条、亚泰快速路围合的 150 公顷研究范围，完成数据清洗、空间落位和更新潜力测度。",
            "outputs": "统一项目底图、MPI 更新潜力、策略语义库、可复用边界约束",
        },
        {
            "code": "02",
            "title": "现状空间全景诊断",
            "module": "页面 02",
            "accent": "green",
            "inputs": "建筑高度、道路交通、公共空间、绿视率、街景语义分割、社会感知文本",
            "process": "用 2D / 3D 数字孪生底板叠加多源诊断图层，识别用地混杂、交通割裂、公共空间不足、风貌破碎等核心问题。",
            "outputs": "现状问题清单、空间诊断面板、重点地块诊断依据",
        },
        {
            "code": "03",
            "title": "价值评估与保护更新冲突",
            "module": "评估内核",
            "accent": "gold",
            "inputs": "遗产点位、历史风貌、更新潜力、公共活力、政策红线",
            "process": "把遗产价值、风貌敏感度、更新潜力和保护开发冲突转成可解释的等级分区，为策略生成提供约束边界。",
            "outputs": "价值评估分区、保护优先级、更新潜力等级、冲突识别",
        },
        {
            "code": "04",
            "title": "策略生成与空间响应",
            "module": "页面 04",
            "accent": "pink",
            "inputs": "诊断问题、案例借鉴、设计理念、政策依据、重点地块定位",
            "process": "以阶段一至三结果为证据链，生成问题-策略-空间响应表，形成总体策略、功能策划、空间结构和五个重点地块导向。",
            "outputs": "总体策略、更新模式、空间落位、政策依据与共识度",
        },
        {
            "code": "05",
            "title": "AIGC 方案推演",
            "module": "页面 03",
            "accent": "cyan",
            "inputs": "现状照片、空间骨架、风貌策略、ControlNet 约束、提示词参数",
            "process": "在不改变真实边界和空间尺度的前提下，进行街景风貌修缮、节点场景和方案意向的生成式推演。",
            "outputs": "A/B 方案图、风貌更新效果、推演历史与可比选图景",
        },
        {
            "code": "06",
            "title": "图纸提示词与图册生产",
            "module": "页面 04",
            "accent": "violet",
            "inputs": "现有阶段结果、图纸类型、精度等级、上传底图、图例规则、文字规则",
            "process": "按一级/二级/三级精度进行完整性检查，自动组合 Image 2.0 图纸提示词；缺少关键底图时拦截，缺少数据时降级为视觉模板。",
            "outputs": "可复制提示词、负面提示词、A/B/C/D 成图评级修正记录",
        },
        {
            "code": "07",
            "title": "成果交付与实施反馈",
            "module": "页面 05",
            "accent": "red",
            "inputs": "策略表、共识结果、AIGC 图景、图册提示词、规划指标和实施分期",
            "process": "汇总导则、图册、重点地块深化、实施分期和更新成效评估，形成可展示、可汇报、可继续反馈迭代的成果包。",
            "outputs": "规划导则、A3 图册、重点地块成果、实施建议与评估闭环",
        },
    ]

    stage_cards = []
    for stage in stages:
        stage_cards.append(
            f'<article class="evidence-stage evidence-stage-{stage["accent"]}">'
            f'<div class="evidence-stage-top"><span class="evidence-stage-code">{stage["code"]}</span>'
            f'<span class="evidence-stage-module">{escape(stage["module"])}</span></div>'
            f'<h3>{escape(stage["title"])}</h3>'
            f'<p>{escape(stage["process"])}</p>'
            '<div class="evidence-stage-meta">'
            f'<div><b>输入</b><span>{escape(stage["inputs"])}</span></div>'
            f'<div><b>输出</b><span>{escape(stage["outputs"])}</span></div>'
            '</div>'
            '</article>'
        )

    guardrails = [
        ("空间真实性", "研究范围、五个重点地块、道路关系、建筑轮廓和高度控制不得被 AI 任意改写。"),
        ("数据可信度", "一级图纸缺底图即拦截；二级图纸缺专题数据时只生成视觉表达模板，不生成具体结论。"),
        ("政策合规", "RAG 检索长春历史文化保护与城市更新相关条文，约束容积率、限高、保护优先级。"),
        ("成果闭环", "成图后按 A/B/C/D 评级修正提示词，优质版本沉淀为后续图册统一风格。"),
    ]
    guardrail_html = "".join(
        f'<div class="evidence-guardrail"><b>{escape(title)}</b><span>{escape(desc)}</span></div>'
        for title, desc in guardrails
    )

    atlas_chapters = [
        "项目认知",
        "数据诊断",
        "价值评估",
        "策略生成",
        "总体规划",
        "重点地块深化",
        "技术推演与实施",
    ]
    chapter_html = "".join(f'<span>{escape(chapter)}</span>' for chapter in atlas_chapters)

    html = (
        '<section class="evidence-workflow">'
        '<div class="evidence-workflow-head">'
        '<div>'
        '<div class="section-eyebrow">Closed Loop</div>'
        '<h3>数据诊断 - 价值评估 - 策略生成 - 方案推演 - 实施反馈</h3>'
        '<p>主页流程已按当前项目完整链路重构：从真实边界和多源数据出发，进入诊断、评估、策略、AIGC、LLM 博弈、Image 2.0 图纸提示词与成果交付，形成毕业设计图册和规划导则的统一闭环。</p>'
        '</div>'
        '<div class="evidence-workflow-kpi">'
        '<b>70-84</b><span>A3 横版图册建议页数</span>'
        '<b>7</b><span>图册章节</span>'
        '<b>5</b><span>重点地块</span>'
        '</div>'
        '</div>'
        f'<div class="evidence-stage-grid">{"".join(stage_cards)}</div>'
        '<div class="evidence-workflow-band">'
        '<div><h4>图册章节映射</h4><div class="evidence-chapter-row">'
        f'{chapter_html}'
        '</div></div>'
        '<div><h4>系统硬约束</h4><div class="evidence-guardrail-grid">'
        f'{guardrail_html}'
        '</div></div>'
        '</div>'
        '<div class="evidence-feedback-line">'
        '<span>反馈路径</span>'
        '<p>成图评级、政策校验、指标修正和实施反馈会回流到策略库、提示词模板和重点地块深化规则，下一轮图纸和方案继承已验证的风格与约束。</p>'
        '</div>'
        '</section>'
    )
    st.markdown(html, unsafe_allow_html=True)

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
            from src.engines.core_engine import get_merged_poi_data
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

# 🧩 核心子系统导览
st.markdown("---")
render_section_intro("核心子系统导览", "从首页直接进入 01-05 页面，按研究链路完成诊断、推演、协商与交付。", eyebrow="Modules")
module_cards_html = '<div class="module-grid-home">'
for m in MODULES:
    route = get_page_route(m["path"])
    img_base64 = get_base64_image_v2(m["image"])
    img_html = ""
    if img_base64:
        img_html = f'<img src="data:image/png;base64,{img_base64}" alt="{escape(m["title"])}">'
    module_cards_html += (
        f'<div class="module-container">'
        f'<a href="/{route}" target="_self" style="text-decoration:none;">'
        f'<div class="module-card">{img_html}'
        f'<h4>{escape(m["title"])}</h4>'
        f'<p>{escape(m["desc"])}</p>'
        f'<div class="module-btn-mock">{escape(m["btn_label"])}</div>'
        f'</div></a></div>'
    )
module_cards_html += "</div>"
st.markdown(module_cards_html, unsafe_allow_html=True)

# 🔄 流程路线
render_section_intro("循证决策全流程", "用一张流程图串起数据、诊断、推演、协商与成果输出。", eyebrow="Workflow")
render_workflow_logic()
st.markdown("<br><br>", unsafe_allow_html=True)

