from src.stages.common.workspace import StageWorkspaceSpec, SubpageSpec
from src.workflow.stage_keys import SK

STAGE13_WORKSPACE = StageWorkspaceSpec(
    stage_code="13",
    title="成果表达",
    description="汇总规划图纸、图册、文档和项目设计报告，形成最终展示成果。",
    evidence_stages=("10", "11", "12", "13"),
    subpages=[
        SubpageSpec(
            label="🗺️ 规划图纸代码生成",
            title="规划图纸代码生成",
            description="调用高精度 GIS 绘图脚本生成规划图纸底图。",
            output_key="planning_drawings",
            artifact_category="drawing",
            aliases=("规划图纸", "图纸生成"),
        ),
        SubpageSpec(
            label="🖼️ 图册自动组装",
            title="图册自动组装",
            description="自动组合 A3 图框、图例、指标卡和规划说明。",
            output_key="atlas_package",
            artifact_category="atlas",
            aliases=("图册组装", "图册"),
        ),
        SubpageSpec(
            label="📤 文档导出",
            title="文档导出",
            description="将导则、诊断、策略和阶段成果注册为可下载文档。",
            output_key=SK.FINAL_REPORT,
            artifact_category="document",
            aliases=("文档", "导出"),
        ),
        SubpageSpec(
            label="📝 项目设计报告",
            title="项目设计报告",
            description="生成项目设计报告，自动汇编各阶段成果为结构化文档。",
            output_key="project_report",
            artifact_category="presentation",
            aliases=("设计报告", "项目报告"),
        ),
    ],
)
