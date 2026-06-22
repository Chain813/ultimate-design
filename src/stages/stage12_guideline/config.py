from src.stages.common.workspace import StageWorkspaceSpec, SubpageSpec
from src.workflow.stage_keys import SK


STAGE12_WORKSPACE = StageWorkspaceSpec(
    stage_code="12",
    title="城市设计导则",
    description="分板块生成导则、汇总管控指标，并导出完整成果。",
    evidence_stages=("05", "06", "07", "12"),
    subpages=[
        SubpageSpec(
            label="📜 分板块导则生成",
            title="分板块导则生成",
            description="逐章生成城市设计导则正文，并汇总为完整导则。",
            output_key=SK.DESIGN_GUIDELINE,
            artifact_category="guideline",
            aliases=("分板块导则", "导则生成"),
        ),
        SubpageSpec(
            label="📊 管控指标汇总",
            title="管控指标汇总",
            description="查看容积率、高度、绿地率和街道界面等管控指标。",
            aliases=("指标汇总", "管控指标体系"),
        ),
        SubpageSpec(
            label="📄 一键导出",
            title="一键导出",
            description="导出已生成的完整城市设计导则。",
            output_key=SK.DESIGN_GUIDELINE,
            artifact_category="guideline",
            aliases=("导则导出", "导出"),
        ),
    ],
)
