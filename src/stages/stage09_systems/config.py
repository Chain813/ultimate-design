from src.stages.common.workspace import StageWorkspaceSpec, SubpageSpec
from src.workflow.stage_keys import SK


STAGE09_WORKSPACE = StageWorkspaceSpec(
    stage_code="09",
    title="专项系统设计",
    description="将总体空间结构拆解为交通、公共空间、建筑形态、风貌景观和产业业态专项。",
    evidence_stages=("08", "09"),
    subpages=[
        SubpageSpec(
            label="🚗 交通网络与TOD",
            title="交通网络与TOD",
            description="生成慢行、公交、停车和TOD节点组织建议。",
            output_key=SK.TRAFFIC_SYSTEM,
            artifact_category="report",
            aliases=("交通网络", "TOD"),
        ),
        SubpageSpec(
            label="🌳 公共空间与15分钟圈",
            title="公共空间与15分钟圈",
            description="组织绿地、公服和步行服务圈的专项系统。",
            output_key=SK.PUBLIC_SPACE,
            artifact_category="report",
            aliases=("公共空间", "15分钟圈"),
        ),
        SubpageSpec(
            label="🏛️ 建筑形态、风貌与立面",
            title="建筑形态、风貌与立面",
            description="控制高度、界面、肌理和立面更新策略。",
            output_key=SK.BUILDING_FORM,
            artifact_category="report",
            aliases=("建筑形态", "立面"),
        ),
        SubpageSpec(
            label="🎨 风貌景观与文保",
            title="风貌景观与文保",
            description="整合历史保护、景观视廊和风貌分区策略。",
            output_key=SK.LANDSCAPE_STYLE,
            artifact_category="report",
            aliases=("风貌景观", "文保"),
        ),
        SubpageSpec(
            label="🏭 产业业态规划",
            title="产业业态规划",
            description="承接空间结构和策略矩阵，提出产业导入与业态组合。",
            output_key=SK.INDUSTRY_PLANNING,
            artifact_category="report",
            aliases=("产业业态", "产业规划"),
        ),
    ],
)
