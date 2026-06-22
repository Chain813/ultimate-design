import ast
from pathlib import Path

from src.ui.critical_images import get_inline_static_image_src


def test_inline_static_image_src_embeds_existing_png():
    src = get_inline_static_image_src("research_scope_2d_cropped.png")

    assert src.startswith("data:image/png;base64,")
    assert "/app/static/" not in src


def test_homepage_uses_inline_src_for_study_area_map():
    tree = ast.parse(Path("app.py").read_text(encoding="utf-8"))

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "get_inline_static_image_src"
    ]

    assert any(
        call.args
        and isinstance(call.args[0], ast.Constant)
        and call.args[0].value == "research_scope_2d_cropped.png"
        for call in calls
    )
