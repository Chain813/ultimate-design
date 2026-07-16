from src.stages.common.workspace import StageWorkspaceSpec, SubpageSpec
from src.workflow.stage_keys import SK

STAGE08_WORKSPACE = StageWorkspaceSpec(
    stage_code="08",
    title="总体城市设计",
    description="承接策略共识矩阵，形成空间结构推演与用地结构优化沙盘。",
    evidence_stages=("06", "07", "08"),
    subpages=[
        SubpageSpec(
            label="🗺️ 空间结构推演",
            title="空间结构推演",
            description="基于设计概念和策略矩阵生成总体空间结构方案。",
            output_key=SK.SPATIAL_STRUCTURE,
            artifact_category="report",
            aliases=("空间结构", "结构推演"),
        ),
        SubpageSpec(
            label="🎛️ 用地结构优化沙盘",
            title="用地结构优化沙盘",
            description="调整用地配比、地块强度和功能组合，沉淀可复用的沙盘数据。",
            output_key=SK.LANDUSE_SANDBOX,
            artifact_category="data",
            aliases=("用地沙盘", "用地结构"),
        ),
    ],
)
