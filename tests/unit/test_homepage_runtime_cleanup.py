import ast
from pathlib import Path


APP_PATH = Path("app.py")
APP_SHELL_PATH = Path("src/ui/app_shell.py")


def _app_tree():
    return ast.parse(APP_PATH.read_text(encoding="utf-8"))


def _tree(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _function(tree, name):
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"Function {name!r} not found")


def test_homepage_does_not_precompute_unused_hud_stats():
    assigned_names = {
        target.id
        for node in ast.walk(_app_tree())
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }

    assert "top_stats" not in assigned_names


def test_homepage_uses_shared_skyline_hud_component():
    local_functions = [
        node.name for node in _app_tree().body if isinstance(node, ast.FunctionDef)
    ]

    assert "render_skyline_hud" not in local_functions


def test_ai_monitoring_dashboard_skips_rendering_until_metrics_exist():
    func = _function(_app_tree(), "render_ai_monitoring_dashboard")
    non_import_statements = [
        stmt
        for stmt in func.body
        if not isinstance(stmt, ast.ImportFrom | ast.Import)
        and not (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str)
        )
    ]

    first_stmt = non_import_statements[0]
    assert isinstance(first_stmt, ast.Assign)
    assert any(isinstance(target, ast.Name) and target.id == "metrics" for target in first_stmt.targets)

    second_stmt = non_import_statements[1]
    assert isinstance(second_stmt, ast.If)
    assert isinstance(second_stmt.test, ast.UnaryOp)
    assert isinstance(second_stmt.test.op, ast.Not)
    assert isinstance(second_stmt.test.operand, ast.Name)
    assert second_stmt.test.operand.id == "metrics"
    assert any(isinstance(stmt, ast.Return) for stmt in second_stmt.body)


def test_recording_huds_only_load_in_presentation_mode():
    func = _function(_tree(APP_SHELL_PATH), "render_top_nav")
    gated_calls = set()

    for node in ast.walk(func):
        if isinstance(node, ast.If):
            test_src = ast.unparse(node.test)
            if "presentation_mode" not in test_src:
                continue
            for child in ast.walk(ast.Module(body=node.body, type_ignores=[])):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                    gated_calls.add(child.func.id)

    assert {"render_scrolling_control", "render_auto_tour"} <= gated_calls
