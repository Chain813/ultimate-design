import streamlit as st
import json
import os
import socket
from pathlib import Path
import base64
from src.ui.ui_components import render_top_nav, render_engine_status_alert, check_engine_status
from src.engines.core_engine import get_hud_statistics
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
    return urllib.parse.quote(name)

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
        "title": "🔬 01 数据底座与策略实验室",
        "desc": "整合指标总览、MPI 潜力评估、MarkItDown 文档萃取与原始数据管理，构建全生命周期证据底座。",
        "image": "assets/01_data_overview.png",
        "path": "pages/1_数据底座与规划策略.py",
        "btn_label": "🚀 进入研究中心"
    },
    {
        "title": "🏙️ 02 全息感知与诊断实验室",
        "desc": "集数字孪生沙盘可视化、24H 交通潮汐洞察与社会情感能量场监测为一体，实现多维全息感知。",
        "image": "assets/03_digital_twin.png",
        "path": "pages/2_数字孪生与全息诊断.py",
        "btn_label": "🚀 开启全息诊断"
    },
    {
        "title": "🎨 03 创意生成推演实验室",
        "desc": "基于视觉大模型 AIGC 引擎，针对历史街区病灶区域进行风貌修复、空间织补与多方案生成推演。",
        "image": "assets/05_design_inference.png",
        "path": "pages/3_AIGC设计推演.py",
        "btn_label": "🎨 启动推演引擎"
    },
    {
        "title": "⚖️ 04 智慧决策博弈实验室",
        "desc": "基于 Gemma 4 离线大模型的利益相关者协商平台，推演多元主体下的更新政策共识与社会评价。",
        "image": "assets/06_llm_consultation_v2.png",
        "path": "pages/4_LLM博弈决策.py",
        "btn_label": "⚖️ 进入决策中心"
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
        多模态微更新决策支持平台
    </h2>
    <p style="text-align: center; font-size: 0.95rem; color: #64748b !important; letter-spacing: 0.1em; margin-bottom: 28px;">
        Multi-modal Micro-renewal Decision Support System for Historic Districts
    </p>
    <p style="font-size: 1.05rem; line-height: 1.9; text-align: center; color: #94a3b8 !important; max-width: 900px; margin: 0 auto; padding-top: 10px;">
        整合了 <b style="color: #a5b4fc !important;">空间数字孪生 (Digital Twin)</b>、
        <b style="color: #a5b4fc !important;">计算机视觉 (CV)</b> 与
        <b style="color: #a5b4fc !important;">生成式大模型 (AIGC)</b> 技术，
        为历史工业街区的城市设计与微更新提供数据支撑。
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

    sd_status = "ONLINE" if sd_online else "OFFLINE"
    gemma_status = "ONLINE" if gemma_online else "NOT DETECTED"
    sd_color = "#4ADE80" if sd_online else "#EF4444"
    gemma_color = "#4ADE80" if gemma_online else "#EF4444"

    st.markdown(f"""
<style>
.hud-v-bar {{
    position: fixed; top: 75px; bottom: 30px; width: 235px; padding: 25px 20px;
    background: rgba(10, 15, 30, 0.45); backdrop-filter: blur(25px) saturate(180%);
    border: 1px solid rgba(99, 102, 241, 0.25); z-index: 999;
    font-family: 'Inter', 'JetBrains Mono', monospace; color: rgba(248, 250, 252, 0.95);
    pointer-events: none; transition: all 0.5s ease;
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
.hud-left {{ left: 0; border-radius: 0 20px 20px 0; border-left: 4px solid #6366f1; }}
.hud-right {{ right: 0; border-radius: 20px 0 0 20px; border-right: 4px solid #6366f1; text-align: right; }}
.hud-header {{ font-size: 14px; color: #818cf8; margin-bottom: 22px; font-weight: 800; border-bottom: 1px solid rgba(99, 102, 241, 0.3); padding-bottom: 10px; }}
.hud-item {{ margin-bottom: 20px; }}
.hud-label {{ font-size: 10px; color: rgba(148, 163, 184, 0.8); display: block; margin-bottom: 4px; }}
.hud-value {{ font-size: 12px; font-weight: 700; color: #f8fafc; display: flex; align-items: center; gap: 8px; }}
.hud-right .hud-value {{ justify-content: flex-end; }}
.hud-meta {{ font-size: 9px; color: rgba(99, 102, 241, 0.7); margin-top: 5px; font-style: italic; }}
.status-dot-sd {{ width: 8px; height: 8px; border-radius: 50%; background: {sd_color}; box-shadow: 0 0 15px {sd_color}; }}
.status-dot-gemma {{ width: 8px; height: 8px; border-radius: 50%; background: {gemma_color}; box-shadow: 0 0 15px {gemma_color}; }}
.status-dot-static {{ width: 8px; height: 8px; border-radius: 50%; background: #4ADE80; box-shadow: 0 0 10px #4ADE80; }}
@media (max-width: 1450px) {{ .hud-v-bar {{ display: none; }} }}
</style>

<div class="hud-v-bar hud-left">
    <div class="hud-header">系统内核基础设施</div>
    <div class="hud-item">
        <span class="hud-label">[决策推理模型]</span>
        <div class="hud-value"><span class="status-dot-gemma"></span>{gemma_status}</div>
        <div class="hud-meta">环境依托: Ollama / gemma4</div>
    </div>
    <div class="hud-item">
        <span class="hud-label">[视觉特征修复]</span>
        <div class="hud-value"><span class="status-dot-sd"></span>{sd_status}</div>
        <div class="hud-meta">后端引擎: Stable Diffusion WebUI</div>
    </div>
    <div class="hud-item">
        <span class="hud-label">[多源数据蜘蛛]</span>
        <div class="hud-value"><span class="status-dot-static"></span>CONNECTED</div>
        <div class="hud-meta">代码框架: Selenium / Requests</div>
    </div>
    <div class="hud-item">
        <span class="hud-label">[空间计算内核]</span>
        <div class="hud-value"><span class="status-dot-static"></span>READY</div>
        <div class="hud-meta">物理逻辑: AHP-MPI Engine</div>
    </div>
</div>

<div class="hud-v-bar hud-right">
    <div class="hud-header">循证科研数据底座</div>
    <div class="hud-item">
        <span class="hud-label">[POI 真实点位]</span>
        <div class="hud-value">{hud_stats['poi_count']} AUTHENTICATED<span class="status-dot-static" style="background:#818cf8;"></span></div>
        <div class="hud-meta">本地数据库: Changchun_POI_Real.csv</div>
    </div>
    <div class="hud-item">
        <span class="hud-label">[社会感知识别]</span>
        <div class="hud-value">{hud_stats['nlp_count']} NLP SAMPLES<span class="status-dot-static" style="background:#818cf8;"></span></div>
        <div class="hud-meta">核心算法: NLP Sentiment Logic</div>
    </div>
    <div class="hud-item">
        <span class="hud-label">[空间界限规模]</span>
        <div class="hud-value">~{hud_stats['boundary_ha']} HA BOUNDARY<span class="status-dot-static" style="background:#818cf8;"></span></div>
        <div class="hud-meta">地理坐标: WGS84 / EPSG:4326</div>
    </div>
    <div class="hud-item">
        <span class="hud-label">[街景风貌指数]</span>
        <div class="hud-value">{hud_stats['gvi_count']} GVI ANALYZED<span class="status-dot-static" style="background:#818cf8;"></span></div>
        <div class="hud-meta">数据来源: GVI_Results_Analysis.csv</div>
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
        padding: 30px; background: rgba(15, 23, 42, 0.55); border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 24px; backdrop-filter: blur(20px) saturate(160%); width: 100%; box-sizing: border-box;
    }

    /* 连线样式 */
    .base-path {
        fill: none; stroke: rgba(99, 102, 241, 0.2); stroke-width: 3; stroke-linecap: round;
    }
    .flow-path {
        fill: none; stroke: #818cf8; stroke-width: 2; stroke-linecap: round;
        stroke-dasharray: 12, 18; opacity: 0.7;
        animation: flowDash 1.8s linear infinite;
    }
    @keyframes flowDash {
        from { stroke-dashoffset: 30; }
        to { stroke-dashoffset: 0; }
    }

    /* 节点样式 */
    .node-circle {
        fill: rgba(10, 15, 30, 0.9); stroke: rgba(99, 102, 241, 0.5); stroke-width: 2.5;
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .node-glow {
        fill: none; stroke: #818cf8; stroke-width: 1; opacity: 0;
        transition: all 0.4s ease;
    }
    .node-group { cursor: pointer; }
    .node-group:hover .node-circle {
        stroke: #a5b4fc; stroke-width: 3; fill: rgba(30, 41, 59, 0.95);
        filter: drop-shadow(0 0 12px rgba(129, 140, 248, 0.6));
    }
    .node-group:hover .node-glow { opacity: 0.4; }
    .node-icon { font-size: 24px; text-anchor: middle; dominant-baseline: central; transition: font-size 0.35s ease; }
    .node-group:hover .node-icon { font-size: 28px; }
    .node-label {
        font-family: 'Inter', sans-serif; font-weight: 700; fill: #e2e8f0; font-size: 12px;
        text-anchor: middle; opacity: 0.85; transition: all 0.35s ease;
    }
    .node-group:hover .node-label { fill: #f8fafc; opacity: 1; font-weight: 800; }

    /* 悬停详细信息提示框 */
    .tooltip-box {
        fill: rgba(10, 15, 30, 0.96); stroke: rgba(99, 102, 241, 0.5); stroke-width: 1.5;
        rx: 12; ry: 12; opacity: 0; pointer-events: none;
        transition: opacity 0.3s ease, transform 0.3s ease;
        filter: drop-shadow(0 8px 20px rgba(0, 0, 0, 0.4));
    }
    .tooltip-title {
        font-family: 'Inter', sans-serif; font-weight: 800; fill: #a5b4fc; font-size: 13px;
        opacity: 0; transition: opacity 0.3s ease 0.05s; pointer-events: none;
    }
    .tooltip-desc {
        font-family: 'Inter', sans-serif; font-weight: 400; fill: #cbd5e1; font-size: 10.5px;
        opacity: 0; transition: opacity 0.3s ease 0.1s; pointer-events: none;
    }
    .tooltip-tech {
        font-family: 'Inter', sans-serif; font-weight: 600; fill: #818cf8; font-size: 9.5px; font-style: italic;
        opacity: 0; transition: opacity 0.3s ease 0.15s; pointer-events: none;
    }

    /* 悬停时显示所有提示元素 */
    .node-group:hover .tooltip-box,
    .node-group:hover .tooltip-title,
    .node-group:hover .tooltip-desc,
    .node-group:hover .tooltip-tech {
        opacity: 1 !important;
    }

    /* 流动粒子动画 */
    .particle {
        fill: #a5b4fc; opacity: 0;
    }
    .particle-anim {
        animation: particleMove 3s ease-in-out infinite;
    }
    @keyframes particleMove {
        0% { opacity: 0; }
        20% { opacity: 0.8; }
        80% { opacity: 0.8; }
        100% { opacity: 0; }
    }
    </style>

    <div class="workflow-container">
        <svg viewBox="0 0 1050 460" width="100%">
            <!-- 定义发光滤镜 -->
            <defs>
                <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
                <linearGradient id="lineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:#6366f1;stop-opacity:0.2" />
                    <stop offset="100%" style="stop-color:#818cf8;stop-opacity:0.6" />
                </linearGradient>
            </defs>

            <!-- ===== 背景连线 (静态) ===== -->
            <path class="base-path" d="M 152 200 C 230 200, 250 110, 348 110" />
            <path class="base-path" d="M 152 200 C 230 200, 250 310, 348 310" />
            <path class="base-path" d="M 412 110 L 588 110" />
            <path class="base-path" d="M 412 310 L 588 310" />
            <path class="base-path" d="M 652 110 C 730 110, 750 200, 848 200" />
            <path class="base-path" d="M 652 310 C 730 310, 750 200, 848 200" />

            <!-- ===== 流动连线 (动画) ===== -->
            <path class="flow-path" d="M 152 200 C 230 200, 250 110, 348 110" />
            <path class="flow-path" d="M 152 200 C 230 200, 250 310, 348 310" />
            <path class="flow-path" d="M 412 110 L 588 110" style="animation-delay: 0.3s" />
            <path class="flow-path" d="M 412 310 L 588 310" style="animation-delay: 0.6s" />
            <path class="flow-path" d="M 652 110 C 730 110, 750 200, 848 200" style="animation-delay: 0.9s" />
            <path class="flow-path" d="M 652 310 C 730 310, 750 200, 848 200" style="animation-delay: 1.2s" />

            <!-- ===== 流动粒子 ===== -->
            <circle class="particle particle-anim" r="4" cx="152" cy="200">
                <animateMotion dur="2s" repeatCount="indefinite" path="M 152 200 C 230 200, 250 110, 348 110" />
            </circle>
            <circle class="particle particle-anim" r="4" cx="152" cy="200" style="animation-delay: 0.5s">
                <animateMotion dur="2s" repeatCount="indefinite" path="M 152 200 C 230 200, 250 310, 348 310" begin="0.5s" />
            </circle>
            <circle class="particle particle-anim" r="4" cx="412" cy="110" style="animation-delay: 0.3s">
                <animateMotion dur="1.5s" repeatCount="indefinite" path="M 412 110 L 588 110" begin="0.3s" />
            </circle>
            <circle class="particle particle-anim" r="4" cx="412" cy="310" style="animation-delay: 0.8s">
                <animateMotion dur="1.5s" repeatCount="indefinite" path="M 412 310 L 588 310" begin="0.8s" />
            </circle>
            <circle class="particle particle-anim" r="4" cx="652" cy="110" style="animation-delay: 0.6s">
                <animateMotion dur="2s" repeatCount="indefinite" path="M 652 110 C 730 110, 750 200, 848 200" begin="0.6s" />
            </circle>
            <circle class="particle particle-anim" r="4" cx="652" cy="310" style="animation-delay: 1.1s">
                <animateMotion dur="2s" repeatCount="indefinite" path="M 652 310 C 730 310, 750 200, 848 200" begin="1.1s" />
            </circle>

            <!-- ===== 节点 1: 多源感知 (左) ===== -->
            <g class="node-group">
                <circle class="node-glow" cx="120" cy="200" r="40" />
                <circle class="node-circle" cx="120" cy="200" r="32" />
                <text class="node-icon" x="120" y="201" style="fill: #818cf8;">🔬</text>
                <text class="node-label" x="120" y="258">多源物质/社会感知</text>
                <!-- 悬停提示框 -->
                <rect class="tooltip-box" x="10" y="95" width="220" height="100" />
                <text class="tooltip-title" x="120" y="115" text-anchor="middle">Step 1: 数据采集</text>
                <text class="tooltip-desc" x="120" y="132" text-anchor="middle">整合多源异构城市数据</text>
                <text class="tooltip-desc" x="120" y="148" text-anchor="middle">POI设施分布 + 街景影像 + 社交媒体</text>
                <text class="tooltip-desc" x="120" y="164" text-anchor="middle">构建物质空间与社会感知</text>
                <text class="tooltip-desc" x="120" y="180" text-anchor="middle">双维度基础数据库</text>
            </g>

            <!-- ===== 节点 2: MPI 测度 (上中左) ===== -->
            <g class="node-group">
                <circle class="node-glow" cx="380" cy="110" r="40" />
                <circle class="node-circle" cx="380" cy="110" r="32" />
                <text class="node-icon" x="380" y="111" style="fill: #818cf8;">🏙️</text>
                <text class="node-label" x="380" y="55">MPI 更新潜力测度</text>
                <!-- 悬停提示框 -->
                <rect class="tooltip-box" x="270" y="5" width="220" height="100" />
                <text class="tooltip-title" x="380" y="25" text-anchor="middle">Step 2: 空间评估</text>
                <text class="tooltip-desc" x="380" y="42" text-anchor="middle">构建多维度更新潜力指标体系</text>
                <text class="tooltip-desc" x="380" y="58" text-anchor="middle">建筑质量 · 容积效率 · 设施配套</text>
                <text class="tooltip-desc" x="380" y="74" text-anchor="middle">运用AHP层次分析法量化</text>
                <text class="tooltip-desc" x="380" y="90" text-anchor="middle">街区空间更新需求等级</text>
            </g>

            <!-- ===== 节点 3: 情感诊断 (下中左) ===== -->
            <g class="node-group">
                <circle class="node-glow" cx="380" cy="310" r="40" />
                <circle class="node-circle" cx="380" cy="310" r="32" />
                <text class="node-icon" x="380" y="311" style="fill: #818cf8;">👤</text>
                <text class="node-label" x="380" y="368">公众情感能量诊断</text>
                <!-- 悬停提示框 -->
                <rect class="tooltip-box" x="270" y="355" width="220" height="100" />
                <text class="tooltip-title" x="380" y="375" text-anchor="middle">Step 3: 社会感知</text>
                <text class="tooltip-desc" x="380" y="392" text-anchor="middle">基于NLP的公众情感分析</text>
                <text class="tooltip-desc" x="380" y="408" text-anchor="middle">情感极性判断 · 核心诉求提取</text>
                <text class="tooltip-desc" x="380" y="424" text-anchor="middle">识别居民关注焦点与</text>
                <text class="tooltip-desc" x="380" y="440" text-anchor="middle">空间使用痛点</text>
            </g>

            <!-- ===== 节点 4: 风貌修复 (上中右) ===== -->
            <g class="node-group">
                <circle class="node-glow" cx="620" cy="110" r="40" />
                <circle class="node-circle" cx="620" cy="110" r="32" />
                <text class="node-icon" x="620" y="111" style="fill: #818cf8;">🎨</text>
                <text class="node-label" x="620" y="55">历史风貌特征修复</text>
                <!-- 悬停提示框 -->
                <rect class="tooltip-box" x="510" y="5" width="220" height="100" />
                <text class="tooltip-title" x="620" y="25" text-anchor="middle">Step 4: AIGC影像生成</text>
                <text class="tooltip-desc" x="620" y="42" text-anchor="middle">基于ControlNet的生成式影像推演</text>
                <text class="tooltip-desc" x="620" y="58" text-anchor="middle">历史风貌特征提取与约束重建</text>
                <text class="tooltip-desc" x="620" y="74" text-anchor="middle">Stable Diffusion + 本地LoRA</text>
                <text class="tooltip-desc" x="620" y="90" text-anchor="middle">实现风格可控的改造预演</text>
            </g>

            <!-- ===== 节点 5: 功能织补 (下中右) ===== -->
            <g class="node-group">
                <circle class="node-glow" cx="620" cy="310" r="40" />
                <circle class="node-circle" cx="620" cy="310" r="32" />
                <text class="node-icon" x="620" y="311" style="fill: #818cf8;">🏗️</text>
                <text class="node-label" x="620" y="368">空间病灶功能织补</text>
                <!-- 悬停提示框 -->
                <rect class="tooltip-box" x="510" y="355" width="220" height="100" />
                <text class="tooltip-title" x="620" y="375" text-anchor="middle">Step 5: 空间织补策略</text>
                <text class="tooltip-desc" x="620" y="392" text-anchor="middle">基于GVI/SVF测度的空间诊断</text>
                <text class="tooltip-desc" x="620" y="408" text-anchor="middle">精准识别功能缺失与空间低效区</text>
                <text class="tooltip-desc" x="620" y="424" text-anchor="middle">微介入策略：口袋公园 / 业态置换</text>
                <text class="tooltip-desc" x="620" y="440" text-anchor="middle">渐进式有机更新模式</text>
            </g>

            <!-- ===== 节点 6: 更新导则 (右) ===== -->
            <g class="node-group">
                <circle class="node-glow" cx="880" cy="200" r="40" />
                <circle class="node-circle" cx="880" cy="200" r="32" />
                <text class="node-icon" x="880" y="201" style="fill: #818cf8;">⚖️</text>
                <text class="node-label" x="880" y="258">多主体协同更新导则</text>
                <!-- 悬停提示框 -->
                <rect class="tooltip-box" x="770" y="100" width="220" height="100" />
                <text class="tooltip-title" x="880" y="120" text-anchor="middle">Step 6: 协同决策</text>
                <text class="tooltip-desc" x="880" y="137" text-anchor="middle">多利益相关者博弈模拟平台</text>
                <text class="tooltip-desc" x="880" y="153" text-anchor="middle">基于大语言模型的多轮协商推演</text>
                <text class="tooltip-desc" x="880" y="169" text-anchor="middle">生成兼顾公平与效率的</text>
                <text class="tooltip-desc" x="880" y="185" text-anchor="middle">可持续更新导则</text>
            </g>
        </svg>
    </div>
    """
    components.html(workflow_html, height=580, scrolling=False)

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
        show_lighting = st.checkbox("☀️ 开启光照", value=is_3d_mode, key="map_lighting")

    # 🛠️ 仿真时间控制
    sun_time = st.slider("🕐 日照推演 (00:00 - 23:00)", 0, 23, 10, key="map_sun_time")

    # 1. 独立获取并 JSON 序列化数据（建筑大模型使用流媒体路由，规避渲染引擎强行注入导致的假死）
    b_data_json = "'/app/static/buildings.geojson'" if show_buildings else "null"
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
cols = st.columns(4)
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

