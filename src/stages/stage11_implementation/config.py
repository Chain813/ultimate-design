from src.stages.common.workspace import StageWorkspaceSpec, SubpageSpec

STAGE11_WORKSPACE = StageWorkspaceSpec(
    stage_code="11",
    title="实施路径",
    description="组织全域实施路径、重点地块实施路径和更新方式分类，形成可落地的推进框架。",
    evidence_stages=("10", "11", "12"),
    subpages=[
        SubpageSpec(
            label="🌐 第一层：全域实施路径",
            title="第一层：全域实施路径",
            description="生成覆盖整个研究范围的基础设施、政策投放和文旅路线实施框架。",
            output_key="region_phasing",
            artifact_category="report",
            aliases=("全域实施", "全域路径"),
        ),
        SubpageSpec(
            label="📍 第二层：重点地块实施路径",
            title="第二层：重点地块实施路径",
            description="按所选重点地块生成资金、业态、节点和时序实施方案。",
            output_key="plot_phasing",
            artifact_category="report",
            aliases=("地块实施", "重点地块路径"),
        ),
        SubpageSpec(
            label="🏗️ 更新方式分类",
            title="更新方式分类",
            description="按保护、修缮、改造、置换、拆建和微更新组织分类说明。",
            output_key="renewal_classification",
            artifact_category="reference",
            aliases=("更新分类", "更新方式"),
        ),
    ],
)
