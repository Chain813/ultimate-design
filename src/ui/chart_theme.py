CHART_PALETTE = [
    "#818cf8",
    "#34d399",
    "#f59e0b",
    "#f472b6",
    "#22d3ee",
    "#fb7185",
]


def get_chart_palette():
    """Return the shared chart palette."""
    return list(CHART_PALETTE)


def rgba_from_hex(hex_color, alpha):
    """Convert a hex color to Plotly-compatible rgba."""
    color = hex_color.lstrip("#")
    if len(color) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    return f"rgba({red}, {green}, {blue}, {alpha})"


def apply_plotly_theme(fig, title=None, height=360, showlegend=True, legend_orientation="h"):
    """Apply the shared two-dimensional Plotly theme."""
    title_block = None
    if title:
        title_block = dict(text=title, x=0.0, xanchor="left", font=dict(size=15, color="#f8fafc"))

    fig.update_layout(
        title=title_block,
        height=height,
        showlegend=showlegend,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1"),
        margin=dict(l=20, r=20, t=58 if title else 24, b=20),
        legend=dict(
            orientation=legend_orientation,
            x=0,
            xanchor="left",
            y=1.02 if legend_orientation == "h" else 1,
            yanchor="bottom" if legend_orientation == "h" else "top",
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11, color="#94a3b8"),
        ),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(99,102,241,0.12)",
        linecolor="rgba(148,163,184,0.18)",
        zeroline=False,
        tickfont=dict(size=11, color="#cbd5e1"),
        title_font=dict(size=12, color="#94a3b8"),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(99,102,241,0.12)",
        linecolor="rgba(148,163,184,0.18)",
        zeroline=False,
        tickfont=dict(size=11, color="#cbd5e1"),
        title_font=dict(size=12, color="#94a3b8"),
    )
    return fig


def apply_plotly_polar_theme(fig, title=None, height=320, radial_range=None, accent_color="#818cf8"):
    """Apply the shared polar/radar Plotly theme."""
    title_block = None
    if title:
        title_block = dict(text=title, font=dict(size=13, color=accent_color))

    fig.update_layout(
        title=title_block,
        height=height,
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"),
        margin=dict(l=34, r=34, t=44 if title else 20, b=20),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=radial_range or [0, 1],
                showticklabels=False,
                gridcolor="rgba(99,102,241,0.15)",
                linecolor="rgba(99,102,241,0.15)",
            ),
            angularaxis=dict(
                gridcolor="rgba(99,102,241,0.15)",
                linecolor="rgba(99,102,241,0.15)",
                color="#cbd5e1",
                tickfont=dict(size=10),
            ),
        ),
    )
    return fig
