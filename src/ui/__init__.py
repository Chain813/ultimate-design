
from src.ui.chart_theme import (
    CHART_PALETTE,
    apply_plotly_polar_theme,
    apply_plotly_theme,
    get_chart_palette,
    rgba_from_hex,
)
from src.ui.design_system import (
    load_design_css,
    render_page_banner,
    render_section_intro,
    render_summary_cards,
)

__all__ = [
    "CHART_PALETTE",
    "apply_plotly_polar_theme",
    "apply_plotly_theme",
    "get_chart_palette",
    "load_design_css",
    "render_engine_status_alert",
    "render_page_banner",
    "render_section_intro",
    "render_summary_cards",
    "render_top_nav",
    "rgba_from_hex",
]


def __getattr__(name):
    if name in {"render_engine_status_alert", "render_top_nav"}:
        from src.ui import app_shell

        return getattr(app_shell, name)
    raise AttributeError(f"module 'src.ui' has no attribute {name!r}")
