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
        svg_html = f'<div class="summary-svg-chart" style="margin-top: 15px; opacity: 0.9;">{card["svg_chart"]}</div>' if "svg_chart" in card else ""
        parts.append(
            '<div class="summary-card">'
            f"{icon_html}"
            f'<span class="summary-value">{escape(str(card.get("value", "")))}</span>'
            f'<h4>{escape(str(card.get("title", "")))}</h4>'
            f'<p>{escape(str(card.get("desc", "")))}</p>'
            f"{svg_html}"
            "</div>"
        )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


import textwrap

def _load_svg_template(template_name: str) -> str:
    path = Path(__file__).resolve().parents[2] / "assets" / "svg_templates" / f"{template_name}.html"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""

def render_data_pipeline(as_html=False):
    """渲染专业的数据处理管线图"""
    html_content = _load_svg_template("data_pipeline")
    if html_content:
        if as_html:
            return html_content
        import streamlit as st
        st.markdown(html_content, unsafe_allow_html=True)

def render_mission_decoding_hud(as_html=False):
    """渲染任务解码 HUD"""
    html_content = _load_svg_template("mission_decoding")
    if html_content:
        if as_html:
            return html_content
        import streamlit as st
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
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="#0071e3" />
                    </marker>
                </defs>

                <!-- 背景脉络 -->
                <path d="M50,150 Q400,150 750,150" fill="none" stroke="rgba(0, 0, 0, 0.08)" stroke-width="1" stroke-dasharray="5,5" />

                <!-- 1. Ingestion -->
                <g transform="translate(30, 100)">
                    <rect width="130" height="100" rx="14" ry="14" fill="#ffffff" stroke="#e5e5ea" stroke-width="1" />
                    <!-- Icon: Upload -->
                    <g transform="translate(53, 15) scale(0.6)" stroke="#0071e3" stroke-width="1.5" fill="none">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                    </g>
                    <text x="65" y="65" text-anchor="middle" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="11" font-weight="bold">多模态采集</text>
                    <text x="65" y="82" text-anchor="middle" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="9">Ingestion</text>
                </g>
                <line x1="160" y1="150" x2="185" y2="150" stroke="#0071e3" stroke-width="1.2" marker-end="url(#arrow-rag)" />

                <!-- 2. MarkItDown ETL -->
                <g transform="translate(185, 100)">
                    <rect width="130" height="100" rx="14" ry="14" fill="#ffffff" stroke="#e5e5ea" stroke-width="1" />
                    <!-- Icon: Magic -->
                    <g transform="translate(53, 15) scale(0.6)" stroke="#0071e3" stroke-width="1.5" fill="none">
                        <path d="m21.64 3.64-1.28-1.28a1.21 1.21 0 0 0-1.72 0L2.36 18.64a1.21 1.21 0 0 0 0 1.72l1.28 1.28a1.21 1.21 0 0 0 1.72 0L21.64 5.36a1.21 1.21 0 0 0 0-1.72Z"/><path d="m14 7 3 3"/>
                    </g>
                    <text x="65" y="65" text-anchor="middle" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="11" font-weight="bold">语义提取</text>
                    <text x="65" y="82" text-anchor="middle" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="9">MarkItDown ETL</text>
                </g>
                <line x1="315" y1="150" x2="340" y2="150" stroke="#0071e3" stroke-width="1.2" marker-end="url(#arrow-rag)" />

                <!-- 3. Chunking -->
                <g transform="translate(340, 100)">
                    <rect width="130" height="100" rx="14" ry="14" fill="#ffffff" stroke="#e5e5ea" stroke-width="1" />
                    <!-- Icon: Layers -->
                    <g transform="translate(53, 15) scale(0.6)" stroke="#0071e3" stroke-width="1.5" fill="none">
                        <polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>
                    </g>
                    <text x="65" y="65" text-anchor="middle" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="11" font-weight="bold">上下文分块</text>
                    <text x="65" y="82" text-anchor="middle" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="9">Recursive Split</text>
                </g>
                <line x1="470" y1="150" x2="495" y2="150" stroke="#0071e3" stroke-width="1.2" marker-end="url(#arrow-rag)" />

                <!-- 4. Embedding -->
                <g transform="translate(495, 100)">
                    <rect width="130" height="100" rx="14" ry="14" fill="#ffffff" stroke="#e5e5ea" stroke-width="1" />
                    <!-- Icon: Share2 (Network) -->
                    <g transform="translate(53, 15) scale(0.6)" stroke="#0071e3" stroke-width="1.5" fill="none">
                        <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
                    </g>
                    <text x="65" y="65" text-anchor="middle" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="11" font-weight="bold">向量嵌入</text>
                    <text x="65" y="82" text-anchor="middle" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="9">Embedding Model</text>
                </g>
                <line x1="625" y1="150" x2="650" y2="150" stroke="#0071e3" stroke-width="1.2" marker-end="url(#arrow-rag)" />

                <!-- 5. Vector Store -->
                <g transform="translate(650, 100)">
                    <rect width="135" height="100" rx="14" ry="14" fill="#ffffff" stroke="#0071e3" stroke-width="1.5" />
                    <!-- Icon: Database -->
                    <g transform="translate(55, 15) scale(0.6)" stroke="#0071e3" stroke-width="1.5" fill="none">
                        <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/>
                    </g>
                    <text x="67" y="65" text-anchor="middle" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="bold">语义索引库</text>
                    <text x="67" y="82" text-anchor="middle" fill="#0071e3" font-family="system-ui, -apple-system, sans-serif" font-size="9" font-weight="bold">Chroma / Faiss Index</text>
                </g>

                <!-- 底部资产矩阵 -->
                <g transform="translate(30, 260)">
                    <rect width="755" height="100" rx="16" fill="rgba(0, 113, 227, 0.02)" stroke="rgba(0, 113, 227, 0.08)" stroke-width="1" />
                    <text x="20" y="30" fill="#0071e3" font-family="system-ui, -apple-system, sans-serif" font-size="11" font-weight="bold">语义原料矩阵 / Knowledge Assets Matrix</text>
                    
                    <g transform="translate(20, 50)">
                        <rect width="170" height="35" rx="10" ry="10" fill="#ffffff" stroke="#e5e5ea" stroke-width="1" />
                        <text x="85" y="22" text-anchor="middle" fill="#48484a" font-family="system-ui, -apple-system, sans-serif" font-size="10">PDF 规划文本</text>
                    </g>
                    <g transform="translate(205, 50)">
                        <rect width="170" height="35" rx="10" ry="10" fill="#ffffff" stroke="#e5e5ea" stroke-width="1" />
                        <text x="85" y="22" text-anchor="middle" fill="#48484a" font-family="system-ui, -apple-system, sans-serif" font-size="10">DOCX 任务书</text>
                    </g>
                    <g transform="translate(390, 50)">
                        <rect width="170" height="35" rx="10" ry="10" fill="#ffffff" stroke="#e5e5ea" stroke-width="1" />
                        <text x="85" y="22" text-anchor="middle" fill="#48484a" font-family="system-ui, -apple-system, sans-serif" font-size="10">PPT 设计提案</text>
                    </g>
                    <g transform="translate(575, 50)">
                        <rect width="160" height="35" rx="10" ry="10" fill="#ffffff" stroke="#e5e5ea" stroke-width="1" />
                        <text x="80" y="22" text-anchor="middle" fill="#48484a" font-family="system-ui, -apple-system, sans-serif" font-size="10">TXT 调研记录</text>
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
                    <marker id="arrow-line" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="#0071e3" />
                    </marker>
                </defs>

                <!-- Columns Backgrounds -->
                <rect x="10" y="10" width="250" height="280" rx="16" fill="rgba(0, 113, 227, 0.01)" stroke="rgba(0, 113, 227, 0.04)" stroke-width="1" />
                <rect x="350" y="10" width="250" height="280" rx="16" fill="rgba(175, 82, 222, 0.01)" stroke="rgba(175, 82, 222, 0.04)" stroke-width="1" />
                <rect x="690" y="10" width="250" height="280" rx="16" fill="rgba(52, 199, 89, 0.01)" stroke="rgba(52, 199, 89, 0.04)" stroke-width="1" />

                <!-- Column Titles -->
                <text x="135" y="35" text-anchor="middle" fill="#0071e3" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="800" letter-spacing="1">01 多源数据接入 (DATA)</text>
                <text x="475" y="35" text-anchor="middle" fill="#af52de" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="800" letter-spacing="1">02 空间引擎 (PROCESSING)</text>
                <text x="815" y="35" text-anchor="middle" fill="#34c759" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="800" letter-spacing="1">03 诊断结论 (CONCLUSIONS)</text>

                <!-- Connection Lines (Data -> Process) -->
                <path d="M235,90 C 290,90 300,90 345,90" fill="none" stroke="rgba(0, 113, 227, 0.15)" stroke-width="1.2" marker-end="url(#arrow-line)" />
                <path d="M235,90 C 290,90 300,160 345,160" fill="none" stroke="rgba(0, 113, 227, 0.08)" stroke-width="1.2" marker-end="url(#arrow-line)" />
                <path d="M235,160 C 290,160 300,160 345,160" fill="none" stroke="rgba(0, 113, 227, 0.15)" stroke-width="1.2" marker-end="url(#arrow-line)" />
                <path d="M235,160 C 290,160 300,230 345,230" fill="none" stroke="rgba(0, 113, 227, 0.08)" stroke-width="1.2" marker-end="url(#arrow-line)" />
                <path d="M235,230 C 290,230 300,230 345,230" fill="none" stroke="rgba(0, 113, 227, 0.15)" stroke-width="1.2" marker-end="url(#arrow-line)" />

                <!-- Connection Lines (Process -> Conclusion) -->
                <path d="M575,90 C 630,90 640,90 685,90" fill="none" stroke="rgba(175, 82, 222, 0.15)" stroke-width="1.2" marker-end="url(#arrow-line)" />
                <path d="M575,160 C 630,160 640,90 685,90" fill="none" stroke="rgba(175, 82, 222, 0.08)" stroke-width="1.2" marker-end="url(#arrow-line)" />
                <path d="M575,160 C 630,160 640,160 685,160" fill="none" stroke="rgba(175, 82, 222, 0.15)" stroke-width="1.2" marker-end="url(#arrow-line)" />
                <path d="M575,160 C 630,160 640,230 685,230" fill="none" stroke="rgba(175, 82, 222, 0.08)" stroke-width="1.2" marker-end="url(#arrow-line)" />
                <path d="M575,230 C 630,230 640,230 685,230" fill="none" stroke="rgba(175, 82, 222, 0.15)" stroke-width="1.2" marker-end="url(#arrow-line)" />
                <path d="M575,230 C 630,230 640,160 685,160" fill="none" stroke="rgba(175, 82, 222, 0.08)" stroke-width="1.2" marker-end="url(#arrow-line)" />

                <!-- DATA SOURCE NODES -->
                <g transform="translate(35, 65)">
                    <rect width="200" height="50" rx="12" ry="12" fill="#ffffff" stroke="#e5e5ea" stroke-width="1" />
                    <text x="15" y="32" font-size="20">📍</text>
                    <text x="45" y="25" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="bold">POI 与交通设施</text>
                    <text x="45" y="42" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="10">Baidu Map API / OSM</text>
                </g>
                <g transform="translate(35, 135)">
                    <rect width="200" height="50" rx="12" ry="12" fill="#ffffff" stroke="#e5e5ea" stroke-width="1" />
                    <text x="15" y="32" font-size="20">🏢</text>
                    <text x="45" y="25" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="bold">建筑轮廓与边界</text>
                    <text x="45" y="42" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="10">GIS Vector / GeoJSON</text>
                </g>
                <g transform="translate(35, 205)">
                    <rect width="200" height="50" rx="12" ry="12" fill="#ffffff" stroke="#e5e5ea" stroke-width="1" />
                    <text x="15" y="32" font-size="20">📸</text>
                    <text x="45" y="25" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="bold">实景图像与采样</text>
                    <text x="45" y="42" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="10">Field Survey (Stage 03)</text>
                </g>

                <!-- PROCESSING ENGINE NODES -->
                <g transform="translate(375, 65)">
                    <rect width="200" height="50" rx="12" ry="12" fill="#ffffff" stroke="#e5e5ea" stroke-width="1" />
                    <text x="15" y="32" font-size="20">📊</text>
                    <text x="45" y="25" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="bold">密度聚类分析</text>
                    <text x="45" y="42" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="10">KDE Heatmap / DBSCAN</text>
                </g>
                <g transform="translate(375, 135)">
                    <rect width="200" height="50" rx="12" ry="12" fill="#ffffff" stroke="#e5e5ea" stroke-width="1" />
                    <text x="15" y="32" font-size="20">🧬</text>
                    <text x="45" y="25" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="bold">空间拓扑挂接</text>
                    <text x="45" y="42" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="10">Spatial Join & Overlap</text>
                </g>
                <g transform="translate(375, 205)">
                    <rect width="200" height="50" rx="12" ry="12" fill="#ffffff" stroke="#e5e5ea" stroke-width="1" />
                    <text x="15" y="32" font-size="20">⚖️</text>
                    <text x="45" y="25" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="bold">形态与综合评价</text>
                    <text x="45" y="42" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="10">AHP / Skyline Morphing</text>
                </g>

                <!-- CONCLUSIONS NODES -->
                <g transform="translate(715, 65)">
                    <rect width="200" height="50" rx="12" ry="12" fill="#ffffff" stroke="#34c759" stroke-width="1" />
                    <text x="15" y="32" font-size="20">🔥</text>
                    <text x="45" y="25" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="bold">功能活力状态</text>
                    <text x="45" y="42" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="10">业态分布 / 交通热点群</text>
                </g>
                <g transform="translate(715, 135)">
                    <rect width="200" height="50" rx="12" ry="12" fill="#ffffff" stroke="#34c759" stroke-width="1" />
                    <text x="15" y="32" font-size="20">🌳</text>
                    <text x="45" y="25" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="bold">空间风貌品质</text>
                    <text x="45" y="42" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="10">CV 绿视率 / 场所感指标</text>
                </g>
                <g transform="translate(715, 205)">
                    <rect width="200" height="50" rx="12" ry="12" fill="#ffffff" stroke="#34c759" stroke-width="1" />
                    <text x="15" y="32" font-size="20">📐</text>
                    <text x="45" y="25" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="bold">形态规控指引</text>
                    <text x="45" y="42" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="10">天际线特征 / 容积潜力</text>
                </g>
            </svg>
        </div>
        
        <!-- 🆕 技术栈与数据来源标注区 -->
        <div class="hud-footer-meta" style="padding: 12px 24px; background: rgba(0, 113, 227, 0.03); border-top: 1px solid rgba(0, 113, 227, 0.08); display: flex; justify-content: space-between; align-items: center;">
            <div class="data-source-info" style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 0.65rem; color: #86868b; font-weight: 800; letter-spacing: 1px;">DATA PROVENANCE / 数据来源:</span>
                <span style="font-size: 0.65rem; color: #48484a; font-weight: 600;">Baidu Map API, OSM, Field Survey Assets</span>
            </div>
            <div class="tech-stack-info" style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 0.65rem; color: #86868b; font-weight: 800; letter-spacing: 1px;">TECH STACK:</span>
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
                    <marker id="arrow-diag" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="#0071e3" />
                    </marker>
                </defs>

                <!-- Columns Backgrounds -->
                <rect x="10" y="10" width="250" height="220" rx="16" fill="rgba(0, 113, 227, 0.01)" stroke="rgba(0, 113, 227, 0.04)" stroke-width="1" />
                <rect x="350" y="10" width="250" height="220" rx="16" fill="rgba(255, 59, 48, 0.01)" stroke="rgba(255, 59, 48, 0.04)" stroke-width="1" />
                <rect x="690" y="10" width="250" height="220" rx="16" fill="rgba(175, 82, 222, 0.01)" stroke="rgba(175, 82, 222, 0.04)" stroke-width="1" />

                <!-- Column Titles -->
                <text x="135" y="35" text-anchor="middle" fill="#0071e3" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="800" letter-spacing="1">01 核心量化指标 (METRICS)</text>
                <text x="475" y="35" text-anchor="middle" fill="#ff3b30" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="800" letter-spacing="1">02 AHP-MPI 建模 (MODELING)</text>
                <text x="815" y="35" text-anchor="middle" fill="#af52de" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="800" letter-spacing="1">03 智能诊断报告 (DIAGNOSIS)</text>

                <!-- Connection Lines (Data -> Process) -->
                <path d="M235,80 C 290,80 300,120 345,120" fill="none" stroke="rgba(0, 113, 227, 0.15)" stroke-width="1.2" marker-end="url(#arrow-diag)" />
                <path d="M235,140 C 290,140 300,120 345,120" fill="none" stroke="rgba(0, 113, 227, 0.15)" stroke-width="1.2" marker-end="url(#arrow-diag)" />
                <path d="M235,200 C 290,200 300,120 345,120" fill="none" stroke="rgba(0, 113, 227, 0.15)" stroke-width="1.2" marker-end="url(#arrow-diag)" />

                <!-- Connection Lines (Process -> Conclusion) -->
                <path d="M575,120 C 630,120 640,80 685,80" fill="none" stroke="rgba(255, 59, 48, 0.15)" stroke-width="1.2" marker-end="url(#arrow-diag)" />
                <path d="M575,120 C 630,120 640,140 685,140" fill="none" stroke="rgba(255, 59, 48, 0.15)" stroke-width="1.2" marker-end="url(#arrow-diag)" />
                <path d="M575,120 C 630,120 640,200 685,200" fill="none" stroke="rgba(255, 59, 48, 0.15)" stroke-width="1.2" marker-end="url(#arrow-diag)" />

                <!-- METRICS NODES -->
                <g transform="translate(35, 55)">
                    <rect width="200" height="45" rx="12" ry="12" fill="#ffffff" stroke="#e5e5ea" stroke-width="1" />
                    <text x="15" y="28" font-size="18">🏢</text>
                    <text x="45" y="22" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="11" font-weight="bold">空间潜力 (S)</text>
                    <text x="45" y="38" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="9">源自: 地块面积/形态容积率</text>
                </g>
                <g transform="translate(35, 115)">
                    <rect width="200" height="45" rx="12" ry="12" fill="#ffffff" stroke="#e5e5ea" stroke-width="1" />
                    <text x="15" y="28" font-size="18">👥</text>
                    <text x="45" y="22" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="11" font-weight="bold">社会需求 (D)</text>
                    <text x="45" y="38" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="9">源自: POI 密度/调研诉求</text>
                </g>
                <g transform="translate(35, 175)">
                    <rect width="200" height="45" rx="12" ry="12" fill="#ffffff" stroke="#e5e5ea" stroke-width="1" />
                    <text x="15" y="28" font-size="18">🌿</text>
                    <text x="45" y="22" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="11" font-weight="bold">环境现状 (E)</text>
                    <text x="45" y="38" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="9">源自: 街景 GVI/SVF 评估</text>
                </g>

                <!-- PROCESSING ENGINE NODES -->
                <g transform="translate(375, 80)">
                    <rect width="200" height="80" rx="14" ry="14" fill="#ffffff" stroke="#ff3b30" stroke-width="1" />
                    <text x="15" y="35" font-size="24">🧮</text>
                    <text x="55" y="30" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="14" font-weight="bold">AHP-MPI 指数计算</text>
                    <text x="55" y="50" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="10">专家权重矩阵加权融合</text>
                    <text x="55" y="65" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="10">Min-Max 归一化处理</text>
                </g>

                <!-- CONCLUSIONS NODES -->
                <g transform="translate(715, 55)">
                    <rect width="200" height="45" rx="12" ry="12" fill="#ffffff" stroke="#af52de" stroke-width="1" />
                    <text x="15" y="28" font-size="18">🏆</text>
                    <text x="45" y="22" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="11" font-weight="bold">优先更新时序图谱</text>
                    <text x="45" y="38" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="9">明确地块改造先后次序</text>
                </g>
                <g transform="translate(715, 115)">
                    <rect width="200" height="45" rx="12" ry="12" fill="#ffffff" stroke="#af52de" stroke-width="1" />
                    <text x="15" y="28" font-size="18">🎯</text>
                    <text x="45" y="22" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="11" font-weight="bold">多维诊断雷达分析</text>
                    <text x="45" y="38" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="9">精准定位单地块短板</text>
                </g>
                <g transform="translate(715, 175)">
                    <rect width="200" height="45" rx="12" ry="12" fill="#ffffff" stroke="#af52de" stroke-width="1" />
                    <text x="15" y="28" font-size="18">🤖</text>
                    <text x="45" y="22" fill="#1d1d1f" font-family="system-ui, -apple-system, sans-serif" font-size="11" font-weight="bold">LLM 智能诊断报告</text>
                    <text x="45" y="38" fill="#86868b" font-family="system-ui, -apple-system, sans-serif" font-size="9">DeepSeek 自动生成解读</text>
                </g>
            </svg>
        </div>

        <!-- 🆕 公式解析区域：优化为单行显示公式，下方注明解释 -->
        <div class="hud-footer-meta" style="padding: 16px 24px; background: rgba(0, 113, 227, 0.03); border-top: 1px solid rgba(0, 113, 227, 0.08); border-bottom-left-radius: 20px; border-bottom-right-radius: 20px;">
            <div style="font-family: 'Inter', sans-serif; display: flex; flex-direction: column; gap: 14px;">
                <!-- Formula Line -->
                <div style="width: 100%;">
                    <div style="color: #0071e3; font-weight: 800; font-size: 0.65rem; margin-bottom: 6px; letter-spacing: 1px; text-transform: uppercase;">AHP-MPI 核心评估公式 (Diagnostic Model)</div>
                    <div style="background: #ffffff; padding: 10px 16px; border-radius: 8px; border: 1px solid rgba(0, 113, 227, 0.15); font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; color: #0071e3; text-align: center; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);">
                        MPI = (W<sub style="font-size: 0.6rem">s</sub>·S + W<sub style="font-size: 0.6rem">d</sub>·D + W<sub style="font-size: 0.6rem">e</sub>·(1-E)) / ΣW × 100
                    </div>
                </div>
                
                <!-- Explanation Grid -->
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; padding: 0 4px; border-bottom: 1px solid rgba(0, 113, 227, 0.08); padding-bottom: 14px;">
                    <div>
                        <b style="color: #1d1d1f; font-size: 0.8rem;">S = 空间潜力</b><br>
                        <i style="color: #86868b; font-size: 0.65rem;">源自: GIS地块形态测度</i>
                    </div>
                    <div>
                        <b style="color: #1d1d1f; font-size: 0.8rem;">D = 社会需求</b><br>
                        <i style="color: #86868b; font-size: 0.65rem;">源自: POI/UCG情感叠加</i>
                    </div>
                    <div>
                        <b style="color: #1d1d1f; font-size: 0.8rem;">E = 环境现状</b><br>
                        <i style="color: #86868b; font-size: 0.65rem;">源自: 街景 CV 视觉评估</i>
                    </div>
                    <div>
                        <b style="color: #1d1d1f; font-size: 0.8rem;">W = AHP分配权重</b><br>
                        <i style="color: #86868b; font-size: 0.65rem;">*(1-E) 指环境干预紧迫度</i>
                    </div>
                </div>

                <!-- 🆕 Tech Stack & LLM Row -->
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 4px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 0.65rem; color: #86868b; font-weight: 800; letter-spacing: 1px;">DIAGNOSTIC ENGINE / 诊断引擎:</span>
                        <span style="font-size: 0.68rem; color: #af52de; font-weight: 700; background: rgba(175, 82, 222, 0.05); padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(175, 82, 222, 0.1);">DeepSeek-V4 Pro (Local LLM)</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 0.65rem; color: #86868b; font-weight: 800; letter-spacing: 1px;">CORE LIBRARIES:</span>
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
