from html import escape
from pathlib import Path

import streamlit as st


@st.cache_data
def _read_css_content(css_path: str, mtime: float):
    return Path(css_path).read_text(encoding="utf-8")


def _get_css_content():
    css_path = Path(__file__).resolve().parents[2] / "assets" / "style.css"
    if css_path.exists():
        return _read_css_content(str(css_path), css_path.stat().st_mtime)
    return ""


def load_design_css():
    """Load the shared UI stylesheet used by layout primitives."""
    css_content = _get_css_content()
    if css_content:
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def render_page_banner(title, description, eyebrow=None, tags=None, metrics=None, image_url=None, graphic_html=None):
    """Render the standard page header with tags, metrics, and an optional decorative image."""
    load_design_css()
    tags = tags or []
    metrics = metrics or []

    tags_html = "".join(f'<span class="page-chip">{escape(str(tag))}</span>' for tag in tags)
    metrics_html = "".join(
        (
            '<div class="page-banner-metric">'
            f'<div class="page-banner-value">{escape(str(item.get("value", "")))}</div>'
            f'<div class="page-banner-label">{escape(str(item.get("label", "")))}</div>'
            f'<div class="page-banner-meta">{escape(str(item.get("meta", "")))}</div>'
            "</div>"
        )
        for item in metrics
    )
    eyebrow_html = f'<div class="page-eyebrow">{escape(str(eyebrow))}</div>' if eyebrow else ""
    image_html = f'<div class="page-banner-map-preview"><img src="{image_url}" alt="Study Area Map"></div>' if image_url else ""
    
    # If we have a graphic, wrap it in a container
    if graphic_html:
        image_html = f'<div class="page-banner-graphic">{graphic_html}</div>'

    html = (
        '<section class="page-banner">'
        '<div class="page-banner-content">'
        '<div class="page-banner-copy">'
        f"{eyebrow_html}"
        f"<h1>{escape(str(title))}</h1>"
        f"<p>{escape(str(description))}</p>"
        f'<div class="page-chip-row">{tags_html}</div>'
        "</div>"
        f'<div class="page-banner-grid">{metrics_html}</div>'
        "</div>"
        f"{image_html}"
        "</section>"
    )
    # 强制压缩 HTML，移除换行和多余空格，防止 Streamlit 将其解析为代码块
    compressed_html = "".join(line.strip() for line in html.split("\n"))
    st.markdown(compressed_html, unsafe_allow_html=True)


def render_section_intro(title, description="", eyebrow=None):
    """Render the standard section heading block."""
    load_design_css()
    eyebrow_html = f'<div class="section-eyebrow">{escape(str(eyebrow))}</div>' if eyebrow else ""
    desc_html = f"<p>{escape(str(description))}</p>" if description else ""

    html = (
        '<div class="section-intro">'
        f"{eyebrow_html}"
        f"<h2>{escape(str(title))}</h2>"
        f"{desc_html}"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_summary_cards(cards):
    """Render compact metric cards used across pages."""
    load_design_css()
    parts = ['<div class="summary-grid">']
    for card in cards:
        icon_html = f'<div class="summary-icon">{card["icon"]}</div>' if "icon" in card else ""
        parts.append(
            '<div class="summary-card">'
            f"{icon_html}"
            f'<span class="summary-value">{escape(str(card.get("value", "")))}</span>'
            f'<h4>{escape(str(card.get("title", "")))}</h4>'
            f'<p>{escape(str(card.get("desc", "")))}</p>'
            "</div>"
        )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


import textwrap

def render_data_pipeline(as_html=False):
    """渲染专业的数据处理管线图 (Premium Serpentine Flow)"""
    html_content = textwrap.dedent('''
    <div class="pipeline-hud">
        <div class="content-panel-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-trending-up"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>
            <h3 style="margin:0; font-size: 0.9rem;">全链路数据处理管线与决策逻辑</h3>
        </div>
        <div class="pipeline-svg-wrapper-hud">
            <svg viewBox="0 0 1000 350" preserveAspectRatio="xMidYMid meet" class="pipeline-svg-serpentine">
                <defs>
                    <linearGradient id="grad-node-1" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#1e293b;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#0f172a;stop-opacity:1" />
                    </linearGradient>
                </defs>

                <!-- 路径导向 -->
                <path d="M50,200 C200,100 500,300 950,200" fill="none" stroke="rgba(148, 163, 184, 0.1)" stroke-width="10" stroke-linecap="round" />

                <!-- 节点 1: 数据准备 -->
                <g transform="translate(10, 140)">
                    <rect width="230" height="150" rx="12" fill="url(#grad-node-1)" stroke="#818cf8" stroke-width="3" />
                    <rect width="230" height="40" rx="12" fill="#818cf8" />
                    <text x="115" y="27" text-anchor="middle" fill="#0f172a" font-size="20" font-weight="900">01 数据采集</text>
                    <text x="30" y="75" fill="#f8fafc" font-size="15" font-weight="bold">● GeoJSON 空间矢量</text>
                    <text x="30" y="105" fill="#f8fafc" font-size="15" font-weight="bold">● CSV 属性数据表</text>
                    <text x="30" y="135" fill="#f8fafc" font-size="15" font-weight="bold">● 街景图像资源</text>
                </g>

                <!-- 节点 2: 处理引擎 -->
                <g transform="translate(260, 20)">
                    <rect width="240" height="170" rx="12" fill="url(#grad-node-1)" stroke="#818cf8" stroke-width="3" />
                    <rect width="240" height="40" rx="12" fill="#818cf8" />
                    <text x="120" y="27" text-anchor="middle" fill="#0f172a" font-size="20" font-weight="900">02 AI 处理引擎</text>
                    <text x="30" y="75" fill="#f8fafc" font-size="14">■ 空间拓扑关联分析</text>
                    <text x="30" y="105" fill="#f8fafc" font-size="14">■ 视觉语义深度识别</text>
                    <text x="30" y="135" fill="#f8fafc" font-size="14">■ 大模型逻辑链推演</text>
                </g>

                <!-- 节点 3: 数字化评价 -->
                <g transform="translate(520, 140)">
                    <rect width="230" height="150" rx="12" fill="url(#grad-node-1)" stroke="#94a3b8" stroke-width="3" />
                    <rect width="230" height="40" rx="12" fill="#94a3b8" />
                    <text x="115" y="27" text-anchor="middle" fill="#0f172a" font-size="20" font-weight="900">03 数字化评价</text>
                    <text x="30" y="75" fill="#f8fafc" font-size="15" font-weight="bold">● 更新潜力多维评分</text>
                    <text x="30" y="105" fill="#f8fafc" font-size="15" font-weight="bold">● 风貌协调性诊断</text>
                    <text x="30" y="135" fill="#f8fafc" font-size="15" font-weight="bold">● 效益平衡预测曲线</text>
                </g>

                <!-- 节点 4: 更新决策 -->
                <g transform="translate(760, 40)">
                    <rect width="230" height="170" rx="12" fill="url(#grad-node-1)" stroke="#22c55e" stroke-width="3" />
                    <rect width="230" height="40" rx="12" fill="#22c55e" />
                    <text x="115" y="27" text-anchor="middle" fill="#0f172a" font-size="20" font-weight="900">04 决策输出</text>
                    <text x="30" y="75" fill="#4ade80" font-size="16" font-weight="900">✔ 更新序位图谱</text>
                    <text x="30" y="110" fill="#4ade80" font-size="16" font-weight="900">✔ 生成式方案集</text>
                    <text x="30" y="145" fill="#4ade80" font-size="16" font-weight="900">✔ 行动计划共识</text>
                </g>

                <!-- 连接箭头 -->
                <path d="M240,215 L260,105" stroke="rgba(129, 140, 248, 0.4)" stroke-width="2" stroke-dasharray="5,5" />
                <path d="M500,105 L520,215" stroke="rgba(129, 140, 248, 0.4)" stroke-width="2" stroke-dasharray="5,5" />
                <path d="M750,215 L760,125" stroke="rgba(129, 140, 248, 0.4)" stroke-width="2" stroke-dasharray="5,5" />
            </svg>
        </div>
    </div>
    ''')
def render_mission_decoding_hud(as_html=False):
    """渲染任务解读专用的‘任务解码 HUD’ (Mission Decoding Star)"""
    html_content = textwrap.dedent('''
    <div class="pipeline-hud">
        <div class="content-panel-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-fingerprint"><path d="M12 10a2 2 0 0 0-2 2c0 1.02-.1 2.02-.3 3"/><path d="M7 22c-.35-.66-.64-1.4-.87-2.16"/><path d="M10 22c.7-.5 1.2-1.35 1.52-2.15"/><path d="M12 2a10 10 0 0 1 8 10c0 .62-.05 1.22-.15 1.81"/><path d="M15.1 22c.19-.51.3-1.05.35-1.6"/><path d="M18 22c.44-.47.76-1.04.95-1.65"/><path d="M18.8 17.91A10 10 0 0 0 12 2"/><path d="M2 12c0-1.1.15-2.17.43-3.19"/><path d="M20 12c0 .28-.01.56-.03.84"/><path d="M22 12c0-5.52-4.48-10-10-10"/><path d="M4.65 19.34A10 10 0 0 1 2 12"/><path d="M5.07 14.54A6 6 0 0 1 12 6a6 6 0 0 1 6 6c0 .19-.01.38-.03.56"/><path d="M8 22c-.5-1.1-.73-2.28-.73-3.5"/><path d="M9 12c0-.55.45-1 1-1s1 .45 1 1"/><path d="M9 18c0-.55.45-1 1-1s1 .45 1 1"/></svg>
            <h3 style="margin:0; font-size: 0.9rem;">任务书深度解析与核心目标解码</h3>
        </div>
        <div class="pipeline-svg-wrapper-hud">
            <svg viewBox="0 0 800 400" preserveAspectRatio="xMidYMid meet" class="pipeline-svg-serpentine">
                <defs>
                    <linearGradient id="grad-mission" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#38bdf8;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#0ea5e9;stop-opacity:1" />
                    </linearGradient>
                    <filter id="glow-hud">
                        <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                        <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
                    </filter>
                </defs>

                <!-- 放射六边形背景网格 -->
                <polygon points="400,40 540,120 540,280 400,360 260,280 260,120" fill="none" stroke="rgba(56, 189, 248, 0.05)" stroke-width="1" />
                <polygon points="400,80 500,140 500,260 400,320 300,260 300,140" fill="none" stroke="rgba(56, 189, 248, 0.08)" stroke-width="1" />
                <polygon points="400,120 460,160 460,240 400,280 340,240 340,160" fill="none" stroke="rgba(56, 189, 248, 0.1)" stroke-width="1" />
                
                <!-- 放射轴 (六轴) -->
                <line x1="400" y1="200" x2="400" y2="40" stroke="rgba(148, 163, 184, 0.15)" stroke-width="1" stroke-dasharray="4,4" />
                <line x1="400" y1="200" x2="540" y2="120" stroke="rgba(148, 163, 184, 0.15)" stroke-width="1" stroke-dasharray="4,4" />
                <line x1="400" y1="200" x2="540" y2="280" stroke="rgba(148, 163, 184, 0.15)" stroke-width="1" stroke-dasharray="4,4" />
                <line x1="400" y1="200" x2="400" y2="360" stroke="rgba(148, 163, 184, 0.15)" stroke-width="1" stroke-dasharray="4,4" />
                <line x1="400" y1="200" x2="260" y2="280" stroke="rgba(148, 163, 184, 0.15)" stroke-width="1" stroke-dasharray="4,4" />
                <line x1="400" y1="200" x2="260" y2="120" stroke="rgba(148, 163, 184, 0.15)" stroke-width="1" stroke-dasharray="4,4" />

                <!-- 六边形雷达覆盖面 -->
                <polygon points="400,60 520,130 510,290 400,340 280,270 270,140" fill="rgba(56, 189, 248, 0.1)" stroke="#38bdf8" stroke-width="2" filter="url(#glow-hud)" />

                <!-- 中心核心 -->
                <circle cx="400" cy="200" r="45" fill="rgba(15, 23, 42, 0.95)" stroke="#38bdf8" stroke-width="2" />
                <text x="400" y="198" text-anchor="middle" fill="#f8fafc" font-size="12" font-weight="900">MISSION</text>
                <text x="400" y="213" text-anchor="middle" fill="#38bdf8" font-size="10" font-weight="bold">DECODE</text>

                <!-- 维度标签卡片 -->
                <!-- 1. 空间尺度 (Top) -->
                <g transform="translate(310, 10)">
                    <rect width="180" height="45" rx="12" fill="rgba(15, 23, 42, 0.95)" stroke="#38bdf8" stroke-width="2" />
                    <text x="90" y="28" text-anchor="middle" fill="#f8fafc" font-size="12" font-weight="bold">空间尺度: 150ha</text>
                </g>

                <!-- 2. 核心驱动 (Right Top) -->
                <g transform="translate(580, 60)">
                    <rect width="190" height="75" rx="12" fill="rgba(15, 23, 42, 0.95)" stroke="#38bdf8" stroke-width="2" />
                    <text x="95" y="25" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="bold">核心驱动: 价值重构</text>
                    <text x="95" y="45" text-anchor="middle" fill="#94a3b8" font-size="9">AI 赋能 / 文脉延续 / 空间激活</text>
                    <text x="95" y="60" text-anchor="middle" fill="#38bdf8" font-size="8">多源数据驱动的范式重构</text>
                </g>

                <!-- 3. AI 介入度 (Right Bottom) -->
                <g transform="translate(580, 240)">
                    <rect width="190" height="75" rx="12" fill="rgba(15, 23, 42, 0.95)" stroke="#38bdf8" stroke-width="2" />
                    <text x="95" y="25" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="bold">AI 介入度: 全流程赋能</text>
                    <text x="95" y="45" text-anchor="middle" fill="#94a3b8" font-size="9">Gemini/Claude/DeepSeek/GPT/SD</text>
                    <text x="95" y="60" text-anchor="middle" fill="#38bdf8" font-size="8">多模态语义解析集群</text>
                </g>

                <!-- 4. 文脉共振 (Bottom) -->
                <g transform="translate(305, 315)">
                    <rect width="190" height="75" rx="12" fill="rgba(15, 23, 42, 0.95)" stroke="#38bdf8" stroke-width="2" />
                    <text x="95" y="25" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="bold">文脉共振: 语义提取</text>
                    <text x="95" y="45" text-anchor="middle" fill="#94a3b8" font-size="9">历史基因修复 / 建筑语义识别</text>
                    <text x="95" y="60" text-anchor="middle" fill="#38bdf8" font-size="8">历史风貌数字资产映射</text>
                </g>

                <!-- 5. 交付形态 (Left Bottom) -->
                <g transform="translate(30, 240)">
                    <rect width="190" height="75" rx="12" fill="rgba(15, 23, 42, 0.95)" stroke="#38bdf8" stroke-width="2" />
                    <text x="95" y="25" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="bold">交付形态: 数字孪生</text>
                    <text x="95" y="45" text-anchor="middle" fill="#94a3b8" font-size="9">孪生底座 / 规划图册 / 交互全景</text>
                    <text x="95" y="60" text-anchor="middle" fill="#94a3b8" font-size="8">A3 (≥60P) + A1 (≥3P)</text>
                </g>

                <!-- 6. 核心任务 (Left Top) -->
                <g transform="translate(30, 60)">
                    <rect width="190" height="75" rx="12" fill="rgba(15, 23, 42, 0.95)" stroke="#38bdf8" stroke-width="2" />
                    <text x="95" y="25" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="bold">核心任务: 城市更新</text>
                    <text x="95" y="45" text-anchor="middle" fill="#94a3b8" font-size="9">历史遗产保护 / 智慧平台构建</text>
                    <text x="95" y="60" text-anchor="middle" fill="#94a3b8" font-size="8">多维价值协同目标解锁</text>
                </g>

                <!-- 动态光点 -->
                <circle cx="400" cy="60" r="4" fill="#38bdf8" filter="blur(2px)" />
                <circle cx="540" cy="120" r="4" fill="#38bdf8" filter="blur(2px)" />
                <circle cx="400" cy="340" r="4" fill="#38bdf8" filter="blur(2px)" />
            </svg>
        </div>
    </div>
    ''')
    # 预先压缩 HTML
    html_content = "".join(line.strip() for line in html_content.split("\n"))
    
    if as_html:
        return html_content
    st.markdown(html_content, unsafe_allow_html=True)

def render_rag_pipeline_hud(as_html=False):
    """渲染资料收集专用的‘RAG 语义资产工厂’ HUD"""
    html_content = textwrap.dedent('''
    <div class="pipeline-hud">
        <div class="content-panel-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/><path d="M8 7h6"/><path d="M8 11h8"/><path d="M8 15h6"/></svg>
            <h3 style="margin:0; font-size: 0.9rem;">RAG 语义知识库构建流程：从非结构化文档到向量索引</h3>
        </div>
        <div class="pipeline-svg-wrapper-hud">
            <svg viewBox="0 0 800 400" preserveAspectRatio="xMidYMid meet" class="pipeline-svg-serpentine">
                <defs>
                    <marker id="arrow-rag" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(56, 189, 248, 0.4)" />
                    </marker>
                    <filter id="glow-rag-core">
                        <feGaussianBlur stdDeviation="3" result="blur"/>
                        <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
                    </filter>
                </defs>

                <!-- 背景脉络 -->
                <path d="M50,150 Q400,150 750,150" fill="none" stroke="rgba(56, 189, 248, 0.1)" stroke-width="1" stroke-dasharray="5,5" />

                <!-- 1. Ingestion -->
                <g transform="translate(30, 100)">
                    <rect width="130" height="100" rx="12" fill="rgba(15, 23, 42, 0.95)" stroke="#38bdf8" stroke-width="2" />
                    <!-- Icon: Upload -->
                    <g transform="translate(53, 15) scale(0.6)" stroke="#38bdf8" stroke-width="2" fill="none">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                    </g>
                    <text x="65" y="65" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="bold">多模态采集</text>
                    <text x="65" y="82" text-anchor="middle" fill="#94a3b8" font-size="9">Ingestion</text>
                </g>
                <line x1="160" y1="150" x2="185" y2="150" stroke="#38bdf8" stroke-width="1.5" marker-end="url(#arrow-rag)" />

                <!-- 2. MarkItDown ETL -->
                <g transform="translate(185, 100)">
                    <rect width="130" height="100" rx="12" fill="rgba(15, 23, 42, 0.95)" stroke="#38bdf8" stroke-width="2" />
                    <!-- Icon: Magic -->
                    <g transform="translate(53, 15) scale(0.6)" stroke="#38bdf8" stroke-width="2" fill="none">
                        <path d="m21.64 3.64-1.28-1.28a1.21 1.21 0 0 0-1.72 0L2.36 18.64a1.21 1.21 0 0 0 0 1.72l1.28 1.28a1.21 1.21 0 0 0 1.72 0L21.64 5.36a1.21 1.21 0 0 0 0-1.72Z"/><path d="m14 7 3 3"/>
                    </g>
                    <text x="65" y="65" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="bold">语义提取</text>
                    <text x="65" y="82" text-anchor="middle" fill="#94a3b8" font-size="9">MarkItDown ETL</text>
                </g>
                <line x1="315" y1="150" x2="340" y2="150" stroke="#38bdf8" stroke-width="1.5" marker-end="url(#arrow-rag)" />

                <!-- 3. Chunking -->
                <g transform="translate(340, 100)">
                    <rect width="130" height="100" rx="12" fill="rgba(15, 23, 42, 0.95)" stroke="#38bdf8" stroke-width="2" />
                    <!-- Icon: Layers -->
                    <g transform="translate(53, 15) scale(0.6)" stroke="#38bdf8" stroke-width="2" fill="none">
                        <polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>
                    </g>
                    <text x="65" y="65" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="bold">上下文分块</text>
                    <text x="65" y="82" text-anchor="middle" fill="#94a3b8" font-size="9">Recursive Split</text>
                </g>
                <line x1="470" y1="150" x2="495" y2="150" stroke="#38bdf8" stroke-width="1.5" marker-end="url(#arrow-rag)" />

                <!-- 4. Embedding -->
                <g transform="translate(495, 100)">
                    <rect width="130" height="100" rx="12" fill="rgba(15, 23, 42, 0.95)" stroke="#38bdf8" stroke-width="2" />
                    <!-- Icon: Share2 (Network) -->
                    <g transform="translate(53, 15) scale(0.6)" stroke="#38bdf8" stroke-width="2" fill="none">
                        <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
                    </g>
                    <text x="65" y="65" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="bold">向量嵌入</text>
                    <text x="65" y="82" text-anchor="middle" fill="#94a3b8" font-size="9">Embedding Model</text>
                </g>
                <line x1="625" y1="150" x2="650" y2="150" stroke="#38bdf8" stroke-width="1.5" marker-end="url(#arrow-rag)" />

                <!-- 5. Vector Store -->
                <g transform="translate(650, 100)">
                    <rect width="135" height="100" rx="12" fill="rgba(30, 41, 59, 0.95)" stroke="#38bdf8" stroke-width="2.5" filter="url(#glow-rag-core)" />
                    <!-- Icon: Database -->
                    <g transform="translate(55, 15) scale(0.6)" stroke="#38bdf8" stroke-width="2" fill="none">
                        <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/>
                    </g>
                    <text x="67" y="65" text-anchor="middle" fill="#f8fafc" font-size="12" font-weight="bold">语义索引库</text>
                    <text x="67" y="82" text-anchor="middle" fill="#38bdf8" font-size="9" font-weight="bold">Chroma / Faiss Index</text>
                </g>

                <!-- 底部资产矩阵 -->
                <g transform="translate(30, 260)">
                    <rect width="755" height="100" rx="16" fill="rgba(56, 189, 248, 0.03)" stroke="rgba(56, 189, 248, 0.1)" stroke-width="1" />
                    <text x="20" y="30" fill="#38bdf8" font-size="11" font-weight="bold">语义原料矩阵 / Knowledge Assets Matrix</text>
                    
                    <g transform="translate(20, 50)">
                        <rect width="170" height="35" rx="8" fill="rgba(15, 23, 42, 0.6)" stroke="#38bdf8" stroke-width="1" />
                        <text x="85" y="22" text-anchor="middle" fill="#cbd5e1" font-size="10">PDF 规划文本</text>
                    </g>
                    <g transform="translate(205, 50)">
                        <rect width="170" height="35" rx="8" fill="rgba(15, 23, 42, 0.6)" stroke="#38bdf8" stroke-width="1" />
                        <text x="85" y="22" text-anchor="middle" fill="#cbd5e1" font-size="10">DOCX 任务书</text>
                    </g>
                    <g transform="translate(390, 50)">
                        <rect width="170" height="35" rx="8" fill="rgba(15, 23, 42, 0.6)" stroke="#38bdf8" stroke-width="1" />
                        <text x="85" y="22" text-anchor="middle" fill="#cbd5e1" font-size="10">PPT 设计提案</text>
                    </g>
                    <g transform="translate(575, 50)">
                        <rect width="160" height="35" rx="8" fill="rgba(15, 23, 42, 0.6)" stroke="#38bdf8" stroke-width="1" />
                        <text x="80" y="22" text-anchor="middle" fill="#cbd5e1" font-size="10">TXT 调研记录</text>
                    </g>
                </g>
            </svg>
        </div>
    </div>
    ''')
    html_content = "".join(line.strip() for line in html_content.split("\n"))
    if as_html:
        return html_content
    st.markdown(html_content, unsafe_allow_html=True)

def render_analysis_pipeline_hud(as_html=False):
    """渲染现状分析专属的数据处理与诊断全流程 HUD (SVG版)"""
    html_content = textwrap.dedent('''
    <div class="pipeline-hud">
        <div class="content-panel-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
            <h3 style="margin:0; font-size: 0.9rem;">全息现状分析引擎：数据源 ➔ 空间处理 ➔ 诊断结论</h3>
        </div>
        <div class="pipeline-svg-wrapper-hud">
            <svg viewBox="0 0 950 300" preserveAspectRatio="xMidYMid meet" class="pipeline-svg-serpentine">
                <defs>
                    <linearGradient id="grad-src" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#0f172a;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#1e293b;stop-opacity:1" />
                    </linearGradient>
                    <marker id="arrow-line" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(56, 189, 248, 0.6)" />
                    </marker>
                    <filter id="glow-light">
                        <feGaussianBlur stdDeviation="3" result="blur"/>
                        <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
                    </filter>
                </defs>

                <!-- Columns Backgrounds -->
                <rect x="10" y="10" width="250" height="280" rx="16" fill="rgba(56, 189, 248, 0.03)" stroke="rgba(56, 189, 248, 0.15)" stroke-width="1" stroke-dasharray="4,4" />
                <rect x="350" y="10" width="250" height="280" rx="16" fill="rgba(168, 85, 247, 0.03)" stroke="rgba(168, 85, 247, 0.15)" stroke-width="1" stroke-dasharray="4,4" />
                <rect x="690" y="10" width="250" height="280" rx="16" fill="rgba(34, 197, 94, 0.03)" stroke="rgba(34, 197, 94, 0.15)" stroke-width="1" stroke-dasharray="4,4" />

                <!-- Column Titles -->
                <text x="135" y="35" text-anchor="middle" fill="#38bdf8" font-size="12" font-weight="900" letter-spacing="1">01 多源数据接入 (DATA)</text>
                <text x="475" y="35" text-anchor="middle" fill="#a855f7" font-size="12" font-weight="900" letter-spacing="1">02 空间引擎 (PROCESSING)</text>
                <text x="815" y="35" text-anchor="middle" fill="#22c55e" font-size="12" font-weight="900" letter-spacing="1">03 诊断结论 (CONCLUSIONS)</text>

                <!-- Connection Lines (Data -> Process) -->
                <path d="M235,90 C 290,90 300,90 345,90" fill="none" stroke="rgba(56, 189, 248, 0.4)" stroke-width="1.5" marker-end="url(#arrow-line)" />
                <path d="M235,90 C 290,90 300,160 345,160" fill="none" stroke="rgba(56, 189, 248, 0.2)" stroke-width="1.5" marker-end="url(#arrow-line)" />
                <path d="M235,160 C 290,160 300,160 345,160" fill="none" stroke="rgba(56, 189, 248, 0.4)" stroke-width="1.5" marker-end="url(#arrow-line)" />
                <path d="M235,160 C 290,160 300,230 345,230" fill="none" stroke="rgba(56, 189, 248, 0.2)" stroke-width="1.5" marker-end="url(#arrow-line)" />
                <path d="M235,230 C 290,230 300,230 345,230" fill="none" stroke="rgba(56, 189, 248, 0.4)" stroke-width="1.5" marker-end="url(#arrow-line)" />

                <!-- Connection Lines (Process -> Conclusion) -->
                <path d="M575,90 C 630,90 640,90 685,90" fill="none" stroke="rgba(168, 85, 247, 0.4)" stroke-width="1.5" marker-end="url(#arrow-line)" />
                <path d="M575,160 C 630,160 640,90 685,90" fill="none" stroke="rgba(168, 85, 247, 0.2)" stroke-width="1.5" marker-end="url(#arrow-line)" />
                <path d="M575,160 C 630,160 640,160 685,160" fill="none" stroke="rgba(168, 85, 247, 0.4)" stroke-width="1.5" marker-end="url(#arrow-line)" />
                <path d="M575,160 C 630,160 640,230 685,230" fill="none" stroke="rgba(168, 85, 247, 0.2)" stroke-width="1.5" marker-end="url(#arrow-line)" />
                <path d="M575,230 C 630,230 640,230 685,230" fill="none" stroke="rgba(168, 85, 247, 0.4)" stroke-width="1.5" marker-end="url(#arrow-line)" />
                <path d="M575,230 C 630,230 640,160 685,160" fill="none" stroke="rgba(168, 85, 247, 0.2)" stroke-width="1.5" marker-end="url(#arrow-line)" />

                <!-- DATA SOURCE NODES -->
                <g transform="translate(35, 65)">
                    <rect width="200" height="50" rx="8" fill="url(#grad-src)" stroke="#38bdf8" stroke-width="1.5" />
                    <text x="15" y="32" font-size="20">📍</text>
                    <text x="45" y="25" fill="#f8fafc" font-size="12" font-weight="bold">POI 与交通设施</text>
                    <text x="45" y="42" fill="#94a3b8" font-size="10">Baidu Map API / OSM</text>
                </g>
                <g transform="translate(35, 135)">
                    <rect width="200" height="50" rx="8" fill="url(#grad-src)" stroke="#38bdf8" stroke-width="1.5" />
                    <text x="15" y="32" font-size="20">🏢</text>
                    <text x="45" y="25" fill="#f8fafc" font-size="12" font-weight="bold">建筑轮廓与边界</text>
                    <text x="45" y="42" fill="#94a3b8" font-size="10">GIS Vector / GeoJSON</text>
                </g>
                <g transform="translate(35, 205)">
                    <rect width="200" height="50" rx="8" fill="url(#grad-src)" stroke="#38bdf8" stroke-width="1.5" />
                    <text x="15" y="32" font-size="20">📸</text>
                    <text x="45" y="25" fill="#f8fafc" font-size="12" font-weight="bold">实景图像与采样</text>
                    <text x="45" y="42" fill="#94a3b8" font-size="10">Field Survey (Stage 03)</text>
                </g>

                <!-- PROCESSING ENGINE NODES -->
                <g transform="translate(375, 65)">
                    <rect width="200" height="50" rx="8" fill="url(#grad-src)" stroke="#a855f7" stroke-width="1.5" />
                    <text x="15" y="32" font-size="20">📊</text>
                    <text x="45" y="25" fill="#f8fafc" font-size="12" font-weight="bold">密度聚类分析</text>
                    <text x="45" y="42" fill="#d8b4fe" font-size="10">KDE Heatmap / DBSCAN</text>
                </g>
                <g transform="translate(375, 135)">
                    <rect width="200" height="50" rx="8" fill="url(#grad-src)" stroke="#a855f7" stroke-width="1.5" />
                    <text x="15" y="32" font-size="20">🧬</text>
                    <text x="45" y="25" fill="#f8fafc" font-size="12" font-weight="bold">空间拓扑挂接</text>
                    <text x="45" y="42" fill="#d8b4fe" font-size="10">Spatial Join & Overlap</text>
                </g>
                <g transform="translate(375, 205)">
                    <rect width="200" height="50" rx="8" fill="url(#grad-src)" stroke="#a855f7" stroke-width="1.5" />
                    <text x="15" y="32" font-size="20">⚖️</text>
                    <text x="45" y="25" fill="#f8fafc" font-size="12" font-weight="bold">形态与综合评价</text>
                    <text x="45" y="42" fill="#d8b4fe" font-size="10">AHP / Skyline Morphing</text>
                </g>

                <!-- CONCLUSIONS NODES -->
                <g transform="translate(715, 65)">
                    <rect width="200" height="50" rx="8" fill="rgba(34, 197, 94, 0.15)" stroke="#22c55e" stroke-width="2" filter="url(#glow-light)" />
                    <text x="15" y="32" font-size="20">🔥</text>
                    <text x="45" y="25" fill="#f8fafc" font-size="12" font-weight="bold">功能活力状态</text>
                    <text x="45" y="42" fill="#86efac" font-size="10">业态分布 / 交通热点群</text>
                </g>
                <g transform="translate(715, 135)">
                    <rect width="200" height="50" rx="8" fill="rgba(34, 197, 94, 0.15)" stroke="#22c55e" stroke-width="2" filter="url(#glow-light)" />
                    <text x="15" y="32" font-size="20">🌳</text>
                    <text x="45" y="25" fill="#f8fafc" font-size="12" font-weight="bold">空间风貌品质</text>
                    <text x="45" y="42" fill="#86efac" font-size="10">CV 绿视率 / 场所感指标</text>
                </g>
                <g transform="translate(715, 205)">
                    <rect width="200" height="50" rx="8" fill="rgba(34, 197, 94, 0.15)" stroke="#22c55e" stroke-width="2" filter="url(#glow-light)" />
                    <text x="15" y="32" font-size="20">📐</text>
                    <text x="45" y="25" fill="#f8fafc" font-size="12" font-weight="bold">形态规控指引</text>
                    <text x="45" y="42" fill="#86efac" font-size="10">天际线特征 / 容积潜力</text>
                </g>
            </svg>
        </div>
        
        <!-- 🆕 技术栈与数据来源标注区 -->
        <div class="hud-footer-meta" style="padding: 12px 24px; background: rgba(56, 189, 248, 0.05); border-top: 1px solid rgba(56, 189, 248, 0.1); display: flex; justify-content: space-between; align-items: center;">
            <div class="data-source-info" style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 0.65rem; color: #64748b; font-weight: 800; letter-spacing: 1px;">DATA PROVENANCE / 数据来源:</span>
                <span style="font-size: 0.65rem; color: #94a3b8; font-weight: 600;">Baidu Map API, OSM, Field Survey Assets</span>
            </div>
            <div class="tech-stack-info" style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 0.65rem; color: #64748b; font-weight: 800; letter-spacing: 1px;">TECH STACK:</span>
                <div style="display: flex; gap: 6px;">
                    <span class="tech-tag">GeoPandas</span>
                    <span class="tech-tag">Scikit-learn</span>
                    <span class="tech-tag">AHP-Engine</span>
                    <span class="tech-tag">Deck.GL</span>
                </div>
            </div>
        </div>

        <div class="hud-footer-scan"></div>
    </div>
    ''')
    html_content = "".join(line.strip() for line in html_content.split("\n"))
    if as_html:
        return html_content
    st.markdown(html_content, unsafe_allow_html=True)

def render_diagnosis_pipeline_hud(as_html=False):
    """渲染问题诊断专属的数据处理与 AHP-MPI 诊断管线 HUD (SVG版)"""
    html_content = textwrap.dedent('''
    <div class="pipeline-hud" style="max-width: 950px;">
        <div class="content-panel-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/></svg>
            <h3 style="margin:0; font-size: 0.9rem;">AHP-MPI 多维潜力诊断引擎：量化评估 ➔ 智能生成</h3>
        </div>
        <div class="pipeline-svg-wrapper-hud">
            <svg viewBox="0 0 950 240" preserveAspectRatio="xMidYMid meet" class="pipeline-svg-serpentine">
                <defs>
                    <linearGradient id="grad-diag-src" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#0f172a;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#1e293b;stop-opacity:1" />
                    </linearGradient>
                    <marker id="arrow-diag" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(129, 140, 248, 0.6)" />
                    </marker>
                    <filter id="glow-diag">
                        <feGaussianBlur stdDeviation="3" result="blur"/>
                        <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
                    </filter>
                </defs>

                <!-- Columns Backgrounds -->
                <rect x="10" y="10" width="250" height="220" rx="16" fill="rgba(99, 102, 241, 0.03)" stroke="rgba(99, 102, 241, 0.15)" stroke-width="1" stroke-dasharray="4,4" />
                <rect x="350" y="10" width="250" height="220" rx="16" fill="rgba(244, 63, 94, 0.03)" stroke="rgba(244, 63, 94, 0.15)" stroke-width="1" stroke-dasharray="4,4" />
                <rect x="690" y="10" width="250" height="220" rx="16" fill="rgba(168, 85, 247, 0.03)" stroke="rgba(168, 85, 247, 0.15)" stroke-width="1" stroke-dasharray="4,4" />

                <!-- Column Titles -->
                <text x="135" y="35" text-anchor="middle" fill="#818cf8" font-size="12" font-weight="900" letter-spacing="1">01 核心量化指标 (METRICS)</text>
                <text x="475" y="35" text-anchor="middle" fill="#fb7185" font-size="12" font-weight="900" letter-spacing="1">02 AHP-MPI 建模 (MODELING)</text>
                <text x="815" y="35" text-anchor="middle" fill="#c084fc" font-size="12" font-weight="900" letter-spacing="1">03 智能诊断报告 (DIAGNOSIS)</text>

                <!-- Connection Lines (Data -> Process) -->
                <path d="M235,80 C 290,80 300,120 345,120" fill="none" stroke="rgba(99, 102, 241, 0.4)" stroke-width="1.5" marker-end="url(#arrow-diag)" />
                <path d="M235,140 C 290,140 300,120 345,120" fill="none" stroke="rgba(99, 102, 241, 0.4)" stroke-width="1.5" marker-end="url(#arrow-diag)" />
                <path d="M235,200 C 290,200 300,120 345,120" fill="none" stroke="rgba(99, 102, 241, 0.4)" stroke-width="1.5" marker-end="url(#arrow-diag)" />

                <!-- Connection Lines (Process -> Conclusion) -->
                <path d="M575,120 C 630,120 640,80 685,80" fill="none" stroke="rgba(244, 63, 94, 0.4)" stroke-width="1.5" marker-end="url(#arrow-diag)" />
                <path d="M575,120 C 630,120 640,140 685,140" fill="none" stroke="rgba(244, 63, 94, 0.4)" stroke-width="1.5" marker-end="url(#arrow-diag)" />
                <path d="M575,120 C 630,120 640,200 685,200" fill="none" stroke="rgba(244, 63, 94, 0.4)" stroke-width="1.5" marker-end="url(#arrow-diag)" />

                <!-- METRICS NODES -->
                <g transform="translate(35, 55)">
                    <rect width="200" height="45" rx="8" fill="url(#grad-diag-src)" stroke="#818cf8" stroke-width="1.5" />
                    <text x="15" y="28" font-size="18">🏢</text>
                    <text x="45" y="22" fill="#f8fafc" font-size="11" font-weight="bold">空间潜力 (S)</text>
                    <text x="45" y="38" fill="#94a3b8" font-size="9">源自: 地块面积/形态容积率</text>
                </g>
                <g transform="translate(35, 115)">
                    <rect width="200" height="45" rx="8" fill="url(#grad-diag-src)" stroke="#818cf8" stroke-width="1.5" />
                    <text x="15" y="28" font-size="18">👥</text>
                    <text x="45" y="22" fill="#f8fafc" font-size="11" font-weight="bold">社会需求 (D)</text>
                    <text x="45" y="38" fill="#94a3b8" font-size="9">源自: POI 密度/调研诉求</text>
                </g>
                <g transform="translate(35, 175)">
                    <rect width="200" height="45" rx="8" fill="url(#grad-diag-src)" stroke="#818cf8" stroke-width="1.5" />
                    <text x="15" y="28" font-size="18">🌿</text>
                    <text x="45" y="22" fill="#f8fafc" font-size="11" font-weight="bold">环境现状 (E)</text>
                    <text x="45" y="38" fill="#94a3b8" font-size="9">源自: 街景 GVI/SVF 评估</text>
                </g>

                <!-- PROCESSING ENGINE NODES -->
                <g transform="translate(375, 80)">
                    <rect width="200" height="80" rx="12" fill="rgba(244, 63, 94, 0.1)" stroke="#fb7185" stroke-width="2" filter="url(#glow-diag)" />
                    <text x="15" y="35" font-size="24">🧮</text>
                    <text x="55" y="30" fill="#f8fafc" font-size="14" font-weight="bold">AHP-MPI 指数计算</text>
                    <text x="55" y="50" fill="#fda4af" font-size="10">专家权重矩阵加权融合</text>
                    <text x="55" y="65" fill="#fda4af" font-size="10">Min-Max 归一化处理</text>
                </g>

                <!-- CONCLUSIONS NODES -->
                <g transform="translate(715, 55)">
                    <rect width="200" height="45" rx="8" fill="rgba(168, 85, 247, 0.15)" stroke="#c084fc" stroke-width="2" />
                    <text x="15" y="28" font-size="18">🏆</text>
                    <text x="45" y="22" fill="#f8fafc" font-size="11" font-weight="bold">优先更新时序图谱</text>
                    <text x="45" y="38" fill="#d8b4fe" font-size="9">明确地块改造先后次序</text>
                </g>
                <g transform="translate(715, 115)">
                    <rect width="200" height="45" rx="8" fill="rgba(168, 85, 247, 0.15)" stroke="#c084fc" stroke-width="2" />
                    <text x="15" y="28" font-size="18">🎯</text>
                    <text x="45" y="22" fill="#f8fafc" font-size="11" font-weight="bold">多维诊断雷达分析</text>
                    <text x="45" y="38" fill="#d8b4fe" font-size="9">精准定位单地块短板</text>
                </g>
                <g transform="translate(715, 175)">
                    <rect width="200" height="45" rx="8" fill="rgba(168, 85, 247, 0.15)" stroke="#c084fc" stroke-width="2" filter="url(#glow-diag)" />
                    <text x="15" y="28" font-size="18">🤖</text>
                    <text x="45" y="22" fill="#f8fafc" font-size="11" font-weight="bold">LLM 智能诊断报告</text>
                    <text x="45" y="38" fill="#d8b4fe" font-size="9">DeepSeek 自动生成解读</text>
                </g>
            </svg>
        </div>

        <!-- 🆕 公式解析区域：优化为单行显示公式，下方注明解释 -->
        <div class="hud-footer-meta" style="padding: 16px 24px; background: rgba(99, 102, 241, 0.05); border-top: 1px solid rgba(99, 102, 241, 0.1); border-bottom-left-radius: 20px; border-bottom-right-radius: 20px;">
            <div style="font-family: 'Inter', sans-serif; display: flex; flex-direction: column; gap: 14px;">
                <!-- Formula Line -->
                <div style="width: 100%;">
                    <div style="color: #818cf8; font-weight: 800; font-size: 0.65rem; margin-bottom: 6px; letter-spacing: 1px; text-transform: uppercase;">AHP-MPI 核心评估公式 (Diagnostic Model)</div>
                    <div style="background: rgba(15, 23, 42, 0.85); padding: 10px 16px; border-radius: 8px; border: 1px solid rgba(99, 102, 241, 0.3); font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; color: #c084fc; text-align: center; box-shadow: inset 0 0 15px rgba(192, 132, 252, 0.05);">
                        MPI = (W<sub style="font-size: 0.6rem">s</sub>·S + W<sub style="font-size: 0.6rem">d</sub>·D + W<sub style="font-size: 0.6rem">e</sub>·(1-E)) / ΣW × 100
                    </div>
                </div>
                
                <!-- Explanation Grid -->
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; padding: 0 4px; border-bottom: 1px solid rgba(99, 102, 241, 0.1); padding-bottom: 14px;">
                    <div>
                        <b style="color: #f8fafc; font-size: 0.8rem;">S = 空间潜力</b><br>
                        <i style="color: #64748b; font-size: 0.65rem;">源自: GIS地块形态测度</i>
                    </div>
                    <div>
                        <b style="color: #f8fafc; font-size: 0.8rem;">D = 社会需求</b><br>
                        <i style="color: #64748b; font-size: 0.65rem;">源自: POI/UCG情感叠加</i>
                    </div>
                    <div>
                        <b style="color: #f8fafc; font-size: 0.8rem;">E = 环境现状</b><br>
                        <i style="color: #64748b; font-size: 0.65rem;">源自: 街景 CV 视觉评估</i>
                    </div>
                    <div>
                        <b style="color: #f8fafc; font-size: 0.8rem;">W = AHP分配权重</b><br>
                        <i style="color: #64748b; font-size: 0.65rem;">*(1-E) 指环境干预紧迫度</i>
                    </div>
                </div>

                <!-- 🆕 Tech Stack & LLM Row -->
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 4px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 0.65rem; color: #64748b; font-weight: 800; letter-spacing: 1px;">DIAGNOSTIC ENGINE / 诊断引擎:</span>
                        <span style="font-size: 0.68rem; color: #c084fc; font-weight: 700; background: rgba(168, 85, 247, 0.1); padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(168, 85, 247, 0.2);">DeepSeek-V4 Pro (Local LLM)</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 0.65rem; color: #64748b; font-weight: 800; letter-spacing: 1px;">CORE LIBRARIES:</span>
                        <div style="display: flex; gap: 6px;">
                            <span class="tech-tag">NumPy</span>
                            <span class="tech-tag">Pandas</span>
                            <span class="tech-tag">SciPy (AHP)</span>
                            <span class="tech-tag">Plotly</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    ''')
    html_content = "".join(line.strip() for line in html_content.split("\n"))
    if as_html:
        return html_content
    st.markdown(html_content, unsafe_allow_html=True)

def render_survey_pipeline_hud(as_html=False):
    """渲染现场调研点位处理与 CV 精度 HUD (综合精简版)"""
    html_content = f"""
        <div class="hud-container">
            <!-- 头部装饰线 -->
            <div class="hud-top-bar">
                <span class="hud-tag">GEOSPATIAL & CV PIPELINE / 空间与视觉双引擎</span>
                <span class="hud-version">v2.4.0-STABLE</span>
            </div>
            
            <div class="hud-main-content">
                <!-- 流程区: 空间数据处理流 -->
                <div class="hud-pipeline-section" style="flex: 2;">
                    <div class="hud-label" style="font-size: 0.65rem; color: #64748b; margin-bottom: 15px;">
                        DATA PIPELINE / 数据处理流
                    </div>
                    <div class="hud-steps-row">
                        {_tech_step_v3("原始 GPS", "RTK 修正", "M21 3v5m0 4v1m0 4v5M3 12h5m4 0h1m4 0h5")}
                        {_tech_arrow_v3()}
                        {_tech_step_v3("无效清洗", "噪声过滤", "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2")}
                        {_tech_arrow_v3()}
                        {_tech_step_v3("格网抽稀", "均匀分布", "M9 20l3-3 3 3m-3-3V4")}
                        {_tech_arrow_v3()}
                        {_tech_step_v3("影像对齐", "航向校准", "M12 2v10m0 0l-3-3m3 3l3-3M3 12h18")}
                        {_tech_arrow_v3()}
                        {_tech_step_v3("成果索引", "GIS 导出", "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z")}
                    </div>
                </div>
                
                <!-- 分隔线 -->
                <div class="hud-divider" style="margin: 0 15px;"></div>
                
                <!-- CV 核心指标与库 -->
                <div class="hud-metrics-section" style="flex: 1; min-width: 180px;">
                    <div class="hud-main-metric" style="margin-bottom: 15px;">
                        <div class="metric-value" style="font-size: 2rem;">94.2<span class="unit">%</span></div>
                        <div class="metric-label">CV RECOGNITION mIoU</div>
                    </div>
                    
                    <div class="hud-tech-stack">
                        <div class="hud-label" style="font-size: 0.6rem; color: #64748b; margin-bottom: 8px;">CV 算法栈 / LIBRARIES</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                            <span class="tech-tag">PyTorch 2.1</span>
                            <span class="tech-tag">SegFormer</span>
                            <span class="tech-tag">SAM (Meta)</span>
                            <span class="tech-tag">OpenCV</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 底部装饰效果 -->
            <div class="hud-footer-scan"></div>
        </div>
    """
    if as_html:
        return html_content
    st.markdown(html_content, unsafe_allow_html=True)

def _tech_step_v3(label, subtext, icon_path):
    return f'''
        <div class="hud-step-item">
            <div class="hud-step-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="{icon_path}"></path>
                </svg>
            </div>
            <span class="hud-step-label">{label}</span>
            <span class="hud-step-subtext">{subtext}</span>
        </div>
    '''

def _tech_arrow_v3():
    return '''
        <div class="hud-step-arrow">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14m-7-7l7 7-7 7"></path>
            </svg>
        </div>
    '''
