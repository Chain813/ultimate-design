import streamlit as st


def setup_function():
    st.session_state.clear()
    st.query_params.clear()


def test_resolve_active_subpage_uses_query_param_alias():
    from src.stages.common.workspace import StageWorkspaceSpec, SubpageSpec, resolve_active_subpage

    spec = StageWorkspaceSpec(
        stage_code="12",
        title="城市设计导则",
        description="导则生成与导出",
        subpages=[
            SubpageSpec(label="📜 分板块导则生成", title="分板块导则生成"),
            SubpageSpec(label="📄 一键导出", title="一键导出", aliases=("导则导出",)),
        ],
    )
    active = resolve_active_subpage(spec, requested_subpage="导则导出")

    assert active.label == "📄 一键导出"
    assert active.title == "一键导出"


def test_build_stage_workspace_html_contains_subpage_links_and_output_key():
    from src.stages.common.workspace import StageWorkspaceSpec, SubpageSpec, build_stage_workspace_html

    spec = StageWorkspaceSpec(
        stage_code="07",
        title="设计策略",
        description="多主体协同策略推演",
        subpages=[
            SubpageSpec(
                label="⚖️ 多主体协同推演",
                title="多主体协同推演",
                description="组织居民、开发商和规划师协同推演。",
                output_key="strategy_matrix",
                artifact_category="report",
            ),
            SubpageSpec(label="📊 共识雷达", title="共识雷达"),
        ],
    )

    html = build_stage_workspace_html(spec, spec.subpages[0])

    assert "Stage 07" in html
    assert "设计策略" in html
    assert "多主体协同推演" in html
    assert "共识雷达" in html
    assert "stage_bus: 07_strategy_matrix" in html
    assert "artifact: report" in html
