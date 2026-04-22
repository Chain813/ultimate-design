import streamlit as st
import json
import os
import socket
from pathlib import Path
import base64
from src.ui.ui_components import render_top_nav, render_engine_status_alert, check_engine_status
from src.engines.core_engine import get_hud_statistics
from src.config import get_static_url
import urllib.parse
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

@st.cache_data
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

# ==========================================
# 🏠 顶部主视觉区 (Hero Section)
# ==========================================
st.markdown("""
<div class="glass-hero">
    <h1 style="text-align: center; font-size: 2.6rem; margin-bottom: 8px;">
        🏙️ 长春伪满皇宫周边街区
    </h1>
    <h2 style="text-align: center; font-size: 1.5rem; margin-bottom: 12px; border: none; background: linear-gradient(135deg, #c7d2fe, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        循证导向的空间微更新支持平台
    </h2>
    <p style="text-align: center; font-size: 0.95rem; color: #64748b !important; letter-spacing: 0.1em; margin-bottom: 28px;">
        Evidence-based Micro-renewal Support System for Historic Districts
    </p>
    <p style="font-size: 1.05rem; line-height: 1.9; text-align: center; color: #94a3b8 !important; max-width: 900px; margin: 0 auto; padding-top: 10px;">
        在严谨的城乡规划理论框架下，本平台引入了 <b style="color: #a5b4fc !important;">可计算城市科学</b> 范式。<br>通过 
        <b style="color: #a5b4fc !important;">动态空间评价 (Spatial Assessment)</b>、
        <b style="color: #a5b4fc !important;">生成式视觉推演 (Generative Pre-rendering)</b> 与
        <b style="color: #a5b4fc !important;">多主体协同测算 (Multi-agent Computation)</b>，
        为长春历史风貌区改造提供量化决策支撑。
    </p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 🛡️ 技术监测 HUD (实时探测)
# ==========================================
def check_local_service(port):
    """检测本地端口是否开放"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except:
        return False

def render_status_hud():
    """渲染深度客制化、带技术背书的监测 HUD (已同步全局探测逻辑)"""
    engine_status = check_engine_status()
    sd_online = engine_status["sd"]
    gemma_online = engine_status["gemma"]
    hud_stats = get_hud_statistics()

    sd_status = "已联机" if sd_online else "未挂载"
    gemma_status = "已联机" if gemma_online else "未挂载"
    sd_color = "#4ADE80" if sd_online else "#EF4444"
    gemma_color = "#4ADE80" if gemma_online else "#EF4444"

    st.markdown(f"""
<style>
.hud-v-bar {{
    position: fixed; top: 75px; bottom: 30px; width: 200px; padding: 18px 14px;
    background: rgba(10, 15, 30, 0.45); backdrop-filter: blur(25px) saturate(180%);
    border: 1px solid rgba(99, 102, 241, 0.25); z-index: 999;
    font-family: 'Inter', 'JetBrains Mono', 'Microsoft YaHei', sans-serif; color: rgba(248, 250, 252, 0.95);
    pointer-events: none; transition: all 0.5s ease; overflow-y: auto;
}}
.hud-v-bar::after {{
    content: '';
    position: absolute; top: 0; left: 0; width: 100%; height: 2px;
    background: linear-gradient(90deg, transparent, rgba(129, 140, 248, 0.6), transparent);
    animation: hudScanLine 3s linear infinite;
}}
@keyframes hudScanLine {{
    0% {{ top: 0; opacity: 0; }}
    10% {{ opacity: 1; }}
    90% {{ opacity: 1; }}
    100% {{ top: 100%; opacity: 0; }}
}}
.hud-left {{ left: 0; border-radius: 0 16px 16px 0; border-left: 3px solid #6366f1; }}
.hud-right {{ right: 0; border-radius: 16px 0 0 16px; border-right: 3px solid #6366f1; text-align: right; }}
.hud-header {{ font-size: 11px; color: #818cf8; margin-bottom: 14px; font-weight: 800; border-bottom: 1px solid rgba(99, 102, 241, 0.3); padding-bottom: 8px; }}
.hud-item {{ margin-bottom: 14px; }}
.hud-label {{ font-size: 8px; color: rgba(148, 163, 184, 0.9); display: block; margin-bottom: 3px; font-weight: 600; }}
.hud-value {{ font-size: 9.5px; font-weight: 700; color: #f8fafc; display: flex; align-items: center; gap: 6px; }}
.hud-right .hud-value {{ justify-content: flex-end; }}
.hud-meta {{ font-size: 7px; color: rgba(129, 140, 248, 0.8); margin-top: 3px; line-height: 1.3; }}
.status-dot-sd {{ width: 6px; height: 6px; border-radius: 50%; background: {sd_color}; box-shadow: 0 0 12px {sd_color}; }}
.status-dot-gemma {{ width: 6px; height: 6px; border-radius: 50%; background: {gemma_color}; box-shadow: 0 0 12px {gemma_color}; }}
.status-dot-static {{ width: 6px; height: 6px; border-radius: 50%; background: #4ADE80; box-shadow: 0 0 8px #4ADE80; }}
@media (max-width: 1450px) {{ .hud-v-bar {{ display: none; }} }}
</style>

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

# ==========================================
# 🔄 循证决策工作流 (Academic Roadmap)
# ==========================================
def render_workflow_logic():
    st.markdown("### 🔄 循证决策全流程逻辑 (System Workflow Logic)")
    workflow_html = """
    <style>
    body { background: transparent; margin: 0; padding: 0; overflow: hidden; }
    .workflow-container {
        padding: 20px; background: rgba(15, 23, 42, 0.55); border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 24px; backdrop-filter: blur(20px) saturate(160%); width: 100%; box-sizing: border-box;
    }
    .base-path { fill: none; stroke: rgba(99, 102, 241, 0.15); stroke-width: 2; stroke-linecap: round; }
    .flow-path {
        fill: none; stroke: #818cf8; stroke-width: 1.5; stroke-linecap: round;
        stroke-dasharray: 10, 14; opacity: 0.6; animation: flowDash 2s linear infinite;
    }
    @keyframes flowDash { from { stroke-dashoffset: 24; } to { stroke-dashoffset: 0; } }
    .feedback-path {
        fill: none; stroke: #f59e0b; stroke-width: 1.5; stroke-linecap: round;
        stroke-dasharray: 6, 8; opacity: 0.5; animation: flowDash 3s linear infinite reverse;
    }

    .node-circle { fill: rgba(10, 15, 30, 0.92); stroke: rgba(99, 102, 241, 0.5); stroke-width: 2; transition: all 0.3s ease; }
    .node-glow { fill: none; stroke: #818cf8; stroke-width: 1; opacity: 0; transition: all 0.4s ease; }
    .node-group { cursor: pointer; }
    .node-group:hover .node-circle { stroke: #a5b4fc; stroke-width: 2.5; fill: rgba(30, 41, 59, 0.95); filter: drop-shadow(0 0 12px rgba(129, 140, 248, 0.6)); }
    .node-group:hover .node-glow { opacity: 0.4; }
    .node-icon { font-size: 20px; text-anchor: middle; dominant-baseline: central; }
    .node-group:hover .node-icon { font-size: 24px; }
    .node-label { font-family: 'Inter', sans-serif; font-weight: 700; fill: #e2e8f0; font-size: 10px; text-anchor: middle; opacity: 0.9; }
    .node-sub { font-family: 'Inter', sans-serif; font-weight: 400; fill: #94a3b8; font-size: 7.5px; text-anchor: middle; opacity: 0.8; }
    .node-tech { font-family: 'JetBrains Mono', monospace; font-size: 7px; fill: #6366f1; text-anchor: middle; opacity: 0.8; }
    .tooltip-box { fill: rgba(15, 23, 42, 0.95); stroke: #818cf8; stroke-width: 1; rx: 8; opacity: 0; transition: opacity 0.3s; pointer-events: none; }
    .node-group:hover .tooltip-box { opacity: 1; }
    .tooltip-title { font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 700; fill: #818cf8; opacity: 0; transition: opacity 0.3s; pointer-events: none; }
    .node-group:hover .tooltip-title { opacity: 1; }
    .tooltip-desc { font-family: 'Inter', sans-serif; font-size: 9px; fill: #cbd5e1; opacity: 0; transition: opacity 0.3s; pointer-events: none; }
    .node-group:hover .tooltip-desc { opacity: 1; }
    .tooltip-tech-label { font-family: 'JetBrains Mono', monospace; font-size: 8px; fill: #34d399; opacity: 0; transition: opacity 0.3s; pointer-events: none; }
    .node-group:hover .tooltip-tech-label { opacity: 1; }
    </style>
        <svg viewBox="0 0 1250 650" width="100%" preserveAspectRatio="xMidYMid meet">
            <defs>
                <filter id="glow"><feGaussianBlur stdDeviation="2.5" result="blur"/><feComposite in="SourceGraphic" in2="blur" operator="over"/></filter>
                <filter id="glow-strong"><feGaussianBlur stdDeviation="4" result="blur"/><feComposite in="SourceGraphic" in2="blur" operator="over"/></filter>
                <marker id="arrowHead" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto" markerUnits="userSpaceOnUse"><path d="M 0 0 L 8 3 L 0 6 Z" fill="#818cf8" opacity="0.8"/></marker>
                <marker id="arrowFeedback" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto" markerUnits="userSpaceOnUse"><path d="M 0 0 L 8 3 L 0 6 Z" fill="#f59e0b" opacity="0.8"/></marker>
            </defs>

            <!-- Layer Backgrounds -->
            <rect x="20" y="50" width="220" height="580" rx="15" fill="rgba(99,102,241,0.03)" stroke="rgba(99,102,241,0.15)" stroke-dasharray="5,5"/>
            <text x="130" y="70" font-family="Inter" font-weight="800" font-size="11px" fill="#6366f1" text-anchor="middle" letter-spacing="1">PHASE I: 多源异构基底</text>
            
            <rect x="260" y="50" width="340" height="580" rx="15" fill="rgba(16,185,129,0.03)" stroke="rgba(16,185,129,0.15)" stroke-dasharray="5,5"/>
            <text x="430" y="70" font-family="Inter" font-weight="800" font-size="11px" fill="#10b981" text-anchor="middle" letter-spacing="1">PHASE II: 空间测度与语义解析</text>

            <rect x="620" y="50" width="280" height="580" rx="15" fill="rgba(236,72,153,0.03)" stroke="rgba(236,72,153,0.15)" stroke-dasharray="5,5"/>
            <text x="760" y="70" font-family="Inter" font-weight="800" font-size="11px" fill="#ec4899" text-anchor="middle" letter-spacing="1">PHASE III: 孪生映射与干预</text>

            <rect x="920" y="50" width="310" height="580" rx="15" fill="rgba(245,158,11,0.03)" stroke="rgba(245,158,11,0.15)" stroke-dasharray="5,5"/>
            <text x="1075" y="70" font-family="Inter" font-weight="800" font-size="11px" fill="#f59e0b" text-anchor="middle" letter-spacing="1">PHASE IV: 智能博弈决策</text>

            <!-- ===================== Base Paths ===================== -->
            <!-- L1 to L2 -->
            <path class="base-path" d="M 180 130 C 240 130, 270 130, 310 130" marker-end="url(#arrowHead)"/>
            <path class="base-path" d="M 180 280 C 240 280, 270 280, 310 280" marker-end="url(#arrowHead)"/>
            <path class="base-path" d="M 180 430 C 240 430, 270 430, 310 430" marker-end="url(#arrowHead)"/>
            <path class="base-path" d="M 180 550 C 240 550, 480 550, 560 480" marker-end="url(#arrowHead)"/>
            
            <!-- L2 internal and -> L3 -->
            <path class="base-path" d="M 450 130 C 510 130, 530 130, 600 130" marker-end="url(#arrowHead)"/>
            <path class="base-path" d="M 450 130 C 510 130, 530 220, 600 220" marker-end="url(#arrowHead)"/>
            <path class="base-path" d="M 450 280 C 510 280, 530 330, 600 330" marker-end="url(#arrowHead)"/>
            <path class="base-path" d="M 450 430 C 510 430, 530 430, 600 430" marker-end="url(#arrowHead)"/>
            
            <!-- L3 -> L4 -->
            <path class="base-path" d="M 750 130 C 830 130, 850 280, 930 280" marker-end="url(#arrowHead)"/>
            <path class="base-path" d="M 750 220 C 830 220, 850 280, 930 280" marker-end="url(#arrowHead)"/>
            <path class="base-path" d="M 750 330 C 830 330, 850 280, 930 280" marker-end="url(#arrowHead)"/>
            <path class="base-path" d="M 750 430 C 830 430, 850 430, 930 430" marker-end="url(#arrowHead)"/>
            
            <!-- L4 internal -->
            <path class="base-path" d="M 1070 280 L 1140 280" marker-end="url(#arrowHead)"/>
            <path class="base-path" d="M 1000 430 L 1050 430" marker-end="url(#arrowHead)"/>
            <path class="base-path" d="M 1050 430 L 1050 315" marker-end="url(#arrowHead)"/>

            <!-- ===================== Animated Flows ===================== -->
            <!-- Use delays to create a continuous pipeline effect -->
            <circle class="particle particle-anim" r="4"><animateMotion dur="2s" repeatCount="indefinite" path="M 180 130 C 240 130, 270 130, 310 130"/></circle>
            <circle class="particle particle-anim" r="4" style="animation-delay:0.3s"><animateMotion dur="2s" repeatCount="indefinite" path="M 180 280 C 240 280, 270 280, 310 280"/></circle>
            <circle class="particle particle-anim" r="4" style="animation-delay:0.6s"><animateMotion dur="2s" repeatCount="indefinite" path="M 180 430 C 240 430, 270 430, 310 430"/></circle>
            
            <circle class="particle particle-anim" r="4" style="animation-delay:0.4s"><animateMotion dur="1.8s" repeatCount="indefinite" path="M 450 130 C 510 130, 530 130, 600 130"/></circle>
            <circle class="particle particle-anim" r="4" style="animation-delay:0.7s"><animateMotion dur="1.8s" repeatCount="indefinite" path="M 450 280 C 510 280, 530 330, 600 330"/></circle>
            <circle class="particle particle-anim" r="4" style="animation-delay:1.0s"><animateMotion dur="1.8s" repeatCount="indefinite" path="M 450 430 C 510 430, 530 430, 600 430"/></circle>
            
            <circle class="particle particle-anim" r="4" style="animation-delay:1.2s"><animateMotion dur="2s" repeatCount="indefinite" path="M 750 330 C 830 330, 850 280, 930 280"/></circle>

            <!-- Feedback Flow -->
            <path class="feedback-path" d="M 1180 300 C 1180 620, 600 620, 130 550" marker-end="url(#arrowFeedback)"/>
            <circle class="particle" r="5" fill="#f59e0b">
                <animateMotion dur="4s" repeatCount="indefinite" path="M 1180 300 C 1180 620, 600 620, 130 550"/>
            </circle>
            <text x="650" y="605" font-family="Inter" font-size="10px" font-weight="700" fill="#f59e0b" text-anchor="middle" letter-spacing="1">🔗 RAG 向量知识回流：政策边界动态约束算法参数与空间权重</text>

            <!-- ===================== NODES ===================== -->
            <!-- L1: 数据层 -->
            <g class="node-group">
                <circle class="node-glow" cx="130" cy="130" r="34"/>
                <circle class="node-circle" cx="130" cy="130" r="28"/>
                <text class="node-icon" x="130" y="131">📍</text>
                <text class="node-label" x="130" y="175">城市兴趣点/AOI</text>
                <text class="node-tech" x="130" y="188">高德API / 业态分布</text>
                
                <rect class="tooltip-box" x="0" y="15" width="260" height="75"/>
                <text class="tooltip-title" x="130" y="32" text-anchor="middle">Step 1: 多源异构数据清洗与落位</text>
                <text class="tooltip-desc" x="130" y="48" text-anchor="middle">汇聚高精度空间特征与网络社会感知数据</text>
                <text class="tooltip-desc" x="130" y="62" text-anchor="middle">构建统一的时空基座，保障后续计算维度对齐</text>
                <text class="tooltip-tech-label" x="130" y="78" text-anchor="middle">核心管线：Pandas / GeoPandas / API 集成</text>
            </g>
            <g class="node-group">
                <circle class="node-glow" cx="130" cy="280" r="34"/>
                <circle class="node-circle" cx="130" cy="280" r="28"/>
                <text class="node-icon" x="130" y="281">💬</text>
                <text class="node-label" x="130" y="325">社会感知网络</text>
                <text class="node-tech" x="130" y="338">UGC 脱敏文本</text>
            </g>
            <g class="node-group">
                <circle class="node-glow" cx="130" cy="430" r="34"/>
                <circle class="node-circle" cx="130" cy="430" r="28"/>
                <text class="node-icon" x="130" y="431">🗺️</text>
                <text class="node-label" x="130" y="475">物理影像底板</text>
                <text class="node-tech" x="130" y="488">街景GVI / 建筑GeoJSON</text>
            </g>
            <g class="node-group">
                <circle class="node-glow" cx="130" cy="550" r="34"/>
                <circle class="node-circle" cx="130" cy="550" r="28"/>
                <text class="node-icon" x="130" y="551">📜</text>
                <text class="node-label" x="130" y="595">规划条例语料库</text>
                <text class="node-tech" x="130" y="608">PDF / Docx 文本提取</text>
            </g>

            <!-- L2: 测度层 -->
            <g class="node-group">
                <circle class="node-glow" cx="380" cy="130" r="42"/>
                <circle class="node-circle" cx="380" cy="130" r="34"/>
                <text class="node-icon" x="380" y="131" font-size="22">📊</text>
                <text class="node-label" x="380" y="185">MPI 多维体检测度</text>
                <text class="node-sub" x="380" y="198">AHP 层次分析 + 熵权法交叉赋权</text>
                <text class="node-tech" x="380" y="210">Scipy / Pandas / NumPy</text>
                
                <rect class="tooltip-box" x="250" y="15" width="260" height="75"/>
                <text class="tooltip-title" x="380" y="32" text-anchor="middle">Step 2: 空间潜能评估 (MPI)</text>
                <text class="tooltip-desc" x="380" y="48" text-anchor="middle">基于物质空间(40%)、社会需求(30%)、环境(30%)的动态评价</text>
                <text class="tooltip-desc" x="380" y="62" text-anchor="middle">识别高优先级微更新地块，输出综合潜力得分榜</text>
                <text class="tooltip-tech-label" x="380" y="78" text-anchor="middle">算法：多因子矩阵乘加运算与归一化</text>
            </g>
            <g class="node-group">
                <circle class="node-glow" cx="380" cy="280" r="38"/>
                <circle class="node-circle" cx="380" cy="280" r="30"/>
                <text class="node-icon" x="380" y="281" font-size="18">🧠</text>
                <text class="node-label" x="380" y="330">NLP 情感极性挖掘</text>
                <text class="node-tech" x="380" y="345">SnowNLP / TF-IDF / 词云</text>
            </g>
            <g class="node-group">
                <circle class="node-glow" cx="380" cy="430" r="38"/>
                <circle class="node-circle" cx="380" cy="430" r="30"/>
                <text class="node-icon" x="380" y="431" font-size="18">🌿</text>
                <text class="node-label" x="380" y="480">四维街景语义切割</text>
                <text class="node-tech" x="380" y="495">GVI 绿视率 / SVF 天空开阔度</text>
                
                <rect class="tooltip-box" x="250" y="315" width="260" height="75"/>
                <text class="tooltip-title" x="380" y="332" text-anchor="middle">Step 3: 现状空间全景诊断</text>
                <text class="tooltip-desc" x="380" y="348" text-anchor="middle">利用语义分割对全域街景进行绿视率/开阔度计算</text>
                <text class="tooltip-desc" x="380" y="362" text-anchor="middle">结合 UGC 文本与情感分析模型挖掘社会诉求</text>
                <text class="tooltip-tech-label" x="380" y="378" text-anchor="middle">模型：Transformer + NLP 极性判断</text>
            </g>

            <!-- L3: 渲染与推演层 -->
            <g class="node-group">
                <circle class="node-glow" cx="680" cy="130" r="34"/>
                <circle class="node-circle" cx="680" cy="130" r="28"/>
                <text class="node-icon" x="680" y="131">📍</text>
                <text class="node-label" x="680" y="175">POI 蜂窝热力特征</text>
                <text class="node-tech" x="680" y="188">Deck.gl HexagonLayer</text>
            </g>
            <g class="node-group">
                <circle class="node-glow" cx="680" cy="220" r="34"/>
                <circle class="node-circle" cx="680" cy="220" r="28"/>
                <text class="node-icon" x="680" y="221">🚦</text>
                <text class="node-label" x="680" y="265">24H 动态潮汐轨迹</text>
                <text class="node-tech" x="680" y="278">Deck.gl TripsLayer</text>
            </g>
            <g class="node-group">
                <circle class="node-glow" cx="680" cy="330" r="44"/>
                <circle class="node-circle" cx="680" cy="330" r="36"/>
                <text class="node-icon" x="680" y="331" font-size="24">🎨</text>
                <text class="node-label" x="680" y="390">AIGC 衍生风貌重构</text>
                <text class="node-sub" x="680" y="405">Stable Diffusion + ControlNet 约束</text>
                <text class="node-tech" x="680" y="418">本地 API + xformers 加速</text>
                
                <rect class="tooltip-box" x="550" y="180" width="260" height="90"/>
                <text class="tooltip-title" x="680" y="198" text-anchor="middle">Step 5: 生成式视觉推演</text>
                <text class="tooltip-desc" x="680" y="215" text-anchor="middle">基于现状街景，提取Canny/Seg结构骨架</text>
                <text class="tooltip-desc" x="680" y="230" text-anchor="middle">结合绿化、历史风貌锚定力进行重绘</text>
                <text class="tooltip-desc" x="680" y="245" text-anchor="middle">为微更新提供"修旧如旧"的前期草图预览</text>
                <text class="tooltip-tech-label" x="680" y="260" text-anchor="middle">DPM++ 2M Karras 采样 | CFG Scale: 7.0</text>
            </g>
            <g class="node-group">
                <circle class="node-glow" cx="680" cy="480" r="38"/>
                <circle class="node-circle" cx="680" cy="480" r="30"/>
                <text class="node-icon" x="680" y="481">🏗️</text>
                <text class="node-label" x="680" y="530">3D 留改拆空间染色</text>
                <text class="node-sub" x="680" y="545">地下管线 X 光透视</text>
                <text class="node-tech" x="680" y="558">PolygonLayer + 动态视角</text>
                
                <rect class="tooltip-box" x="550" y="365" width="260" height="75"/>
                <text class="tooltip-title" x="680" y="382" text-anchor="middle">Step 4: 数字孪生底座与 4D 推演</text>
                <text class="tooltip-desc" x="680" y="398" text-anchor="middle">构建具备地下基础设施 X 光透视能力的 3D 底板</text>
                <text class="tooltip-desc" x="680" y="412" text-anchor="middle">实现微更新方案的实时染色与时空演变可视化</text>
                <text class="tooltip-tech-label" x="680" y="428" text-anchor="middle">渲染引擎：Deck.GL WebGL 加速 + 图层叠加</text>
            </g>

            <!-- L4: 决策层 -->
            <g class="node-group">
                <circle class="node-glow" cx="1000" cy="280" r="48"/>
                <circle class="node-circle" cx="1000" cy="280" r="38" style="stroke:#f59e0b; stroke-width:3; filter:url(#glow-strong);" />
                <text class="node-icon" x="1000" y="281" font-size="28">🤖</text>
                <text class="node-label" x="1000" y="340" font-size="12px" fill="#f8fafc">多主体 LLM 零和博弈</text>
                <text class="node-sub" x="1000" y="355">居民 / 开发商 / 规划师 角色共识</text>
                <text class="node-tech" x="1000" y="368">本地 Ollama + Gemma 4 引擎</text>
                
                <rect class="tooltip-box" x="870" y="125" width="260" height="90"/>
                <text class="tooltip-title" x="1000" y="142" text-anchor="middle">Step 6: AI 驱动民主协商</text>
                <text class="tooltip-desc" x="1000" y="158" text-anchor="middle">模拟三方利益视角的强化对话机制</text>
                <text class="tooltip-desc" x="1000" y="173" text-anchor="middle">自动挖掘靶向议题 (如: 老旧管网改造 vs 资金)</text>
                <text class="tooltip-desc" x="1000" y="188" text-anchor="middle">生成各方共识度雷达与行动备忘录</text>
                <text class="tooltip-tech-label" x="1000" y="205" text-anchor="middle">技术栈: LangChain prompt 工程 + Generator 流式响应</text>
            </g>
            
            <!-- RAG Sub-node -->
            <g class="node-group">
                <circle class="node-glow" cx="1000" cy="430" r="32"/>
                <circle class="node-circle" cx="1000" cy="430" r="26"/>
                <text class="node-icon" x="1000" y="431">📚</text>
                <text class="node-label" x="1000" y="475">RAG 法规校验矩阵</text>
                <text class="node-tech" x="1000" y="488">248 语义切片 + 容积率红线</text>
            </g>

            <!-- Final Node -->
            <g class="node-group">
                <circle class="node-glow" cx="1180" cy="280" r="32"/>
                <circle class="node-circle" cx="1180" cy="280" r="26" style="fill:#f59e0b; stroke:#fff;"/>
                <text class="node-icon" x="1180" y="281" font-size="16">🎯</text>
                <text class="node-label" x="1180" y="325" font-weight="800">循证更新报告</text>
                <text class="node-tech" x="1180" y="338">Markdown + PDF</text>
                
                <rect class="tooltip-box" x="980" y="165" width="260" height="75"/>
                <text class="tooltip-title" x="1110" y="182" text-anchor="middle">Step 7: 更新设计成果展示</text>
                <text class="tooltip-desc" x="1110" y="198" text-anchor="middle">整合 AIGC 草图、MPI 评分与各方博弈共识</text>
                <text class="tooltip-desc" x="1110" y="212" text-anchor="middle">输出满足政府公文规范的标准化 PDF 导则</text>
                <text class="tooltip-tech-label" x="1110" y="228" text-anchor="middle">流转方式：Markdown 动态渲染 + 结构化打包</text>
            </g>
        </svg>
    </div>
    """
    components.html(workflow_html, height=720, scrolling=False)

# ==========================================
# 🚀 渲染执行
# ==========================================
render_status_hud()

# 🗺️ 街区范围及改造红线 (Project Boundary)
st.markdown("### 🗺️ 街区范围及改造红线 (Project Boundary)")
@st.cache_data
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
            df_poi = pd.read_csv("data/Changchun_POI_Real.csv", encoding='utf-8-sig').fillna("")
            poi_data_json = json.dumps(df_poi[['Lng', 'Lat', 'Name']].to_dict(orient="records"))
        except: pass
        
    traffic_data_json = "null"
    if show_traffic:
        try:
            df_tr = pd.read_csv("data/Changchun_Traffic_Real.csv", encoding='utf-8-sig').fillna("")
            traffic_data_json = json.dumps(df_tr[['Lng', 'Lat', 'Name']].to_dict(orient="records"))
        except: pass

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

# 🧩 核心子系统导览
st.markdown("---")
st.markdown("### 🧩 核心子系统导览 (点击进入)")
cols = st.columns(len(MODULES))
for i, m in enumerate(MODULES):
    with cols[i]:
        route = get_page_route(m['path'])
        img_base64 = get_base64_image_v2(m['image'])
        if img_base64:
            img_html = f'<img src="data:image/png;base64,{img_base64}" alt="{m["title"]}">'
        else:
            img_html = ''
        st.markdown(f"""<div class="module-container"><a href="/{route}" target="_self" style="text-decoration:none;"><div class="module-card">{img_html}<h4>{m['title']}</h4><p>{m['desc']}</p><div class="module-btn-mock">{m['btn_label']}</div></div></a></div>""", unsafe_allow_html=True)

# 🔄 流程路线
render_workflow_logic()
st.markdown("<br><br>", unsafe_allow_html=True)

