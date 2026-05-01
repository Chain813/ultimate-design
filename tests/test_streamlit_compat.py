from src.ui.streamlit_compat import stretch_width


def test_stretch_width_prefers_new_width_parameter():
    def component(width="content", use_container_width=None):
        return width, use_container_width

    assert stretch_width(component) == {"width": "stretch"}


def test_stretch_width_falls_back_to_legacy_parameter():
    def component(use_container_width=False):
        return use_container_width

    assert stretch_width(component) == {"use_container_width": True}
