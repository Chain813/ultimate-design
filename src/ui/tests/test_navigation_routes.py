from pathlib import Path
import re
import urllib.parse


def _streamlit_page_slugs():
    slugs = {""}
    for page in Path("pages").glob("*.py"):
        slugs.add(re.sub(r"^\d+_", "", page.stem))
    return slugs


def _href_slug(href):
    return urllib.parse.urlparse(href).path.lstrip("/")


def test_city_design_workflow_imports_without_ui_cycle():
    import src.workflow.city_design_workflow as workflow

    assert workflow.STAGE_LOOKUP["12"]["title"] == "城市设计导则"


def test_workflow_navigation_routes_exist():
    import src.workflow.city_design_workflow as workflow

    known_pages = _streamlit_page_slugs()
    hrefs = [(f"stage {code}", workflow.stage_primary_href(code)) for code in workflow.STAGE_LOOKUP]
    hrefs.extend(
        (f"stage {stage_code} module {module['title']}", module["href"])
        for stage_code, modules in workflow.STAGE_MODULE_MAP.items()
        for module in modules
    )

    missing = {
        label: href
        for label, href in hrefs
        if (slug := _href_slug(href)) and slug not in known_pages
    }

    assert missing == {}


def test_stage_12_modules_route_to_design_guideline_page():
    import src.workflow.city_design_workflow as workflow

    stage_12_hrefs = [module["href"] for module in workflow.STAGE_MODULE_MAP["12"]]

    assert stage_12_hrefs
    assert {_href_slug(href) for href in stage_12_hrefs} == {"城市设计导则"}
