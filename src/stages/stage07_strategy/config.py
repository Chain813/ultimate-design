from src.stages.common.workspace import StageWorkspaceSpec, SubpageSpec
from src.workflow.stage_keys import SK


STAGE07_WORKSPACE = StageWorkspaceSpec(
    stage_code="07",
    title="设计策略",
    description="通过多主体协同推演形成可审查、可下传的策略矩阵。",
    evidence_stages=("05", "06", "07"),
    subpages=[
        SubpageSpec(
            label="⚖️ 多主体协同推演",
            title="多主体协同推演",
            description="组织居民、开发商和规划师进行策略协商，形成共识矩阵。",
            output_key=SK.STRATEGY_MATRIX,
            artifact_category="report",
            aliases=("多主体协同", "协同推演"),
        ),
        SubpageSpec(
            label="📊 共识雷达",
            title="共识雷达",
            description="查看三方协同推演后的共识度分布。",
            aliases=("动态共识雷达", "共识度"),
        ),
        SubpageSpec(
            label="📐 设计纲领提炼",
            title="设计纲领提炼",
            description="将策略矩阵提炼为总体设计和专项设计的纲领。",
            output_key=SK.DESIGN_BASIS,
            artifact_category="report",
            aliases=("设计纲领", "纲领提炼"),
        ),
    ],
)
