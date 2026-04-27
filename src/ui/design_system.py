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


def render_page_banner(title, description, eyebrow=None, tags=None, metrics=None):
    """Render the standard page header with tags and metrics."""
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

    html = (
        '<section class="page-banner">'
        '<div class="page-banner-copy">'
        f"{eyebrow_html}"
        f"<h1>{escape(str(title))}</h1>"
        f"<p>{escape(str(description))}</p>"
        f'<div class="page-chip-row">{tags_html}</div>'
        "</div>"
        f'<div class="page-banner-grid">{metrics_html}</div>'
        "</section>"
    )
    st.markdown(html, unsafe_allow_html=True)


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
        parts.append(
            '<div class="summary-card">'
            f'<span class="summary-value">{escape(str(card.get("value", "")))}</span>'
            f'<h4>{escape(str(card.get("title", "")))}</h4>'
            f'<p>{escape(str(card.get("desc", "")))}</p>'
            "</div>"
        )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)
