from src.stages.common.workspace import StageWorkspaceSpec, SubpageSpec
from src.workflow.stage_keys import SK


STAGE04_WORKSPACE = StageWorkspaceSpec(
    stage_code="04",
    title="现状分析与问题诊断",
    description="整合 3D 现状底座、MPI 更新潜力、地块雷达、AI 诊断和专项资源分析。",
    evidence_stages=("01", "02", "03", "04", "05"),
    subpages=[
        SubpageSpec(
            label="🏙️ 3D 现状全息底座",
            title="3D 现状全息底座",
            description="展示建筑体量、用地类型、POI、交通热点和街景品质指标。",
            output_key="digital_twin_metrics",
            artifact_category="scene",
            aliases=("3D现状", "全息底座"),
        ),
        SubpageSpec(
            label="📊 MPI 更新潜力评估",
            title="MPI 更新潜力评估",
            description="基于 AHP 权重实时计算重点更新单元的 MPI 优先级。",
            output_key=SK.MPI_RANKING,
            artifact_category="data",
            aliases=("MPI", "更新潜力"),
        ),
        SubpageSpec(
            label="🎯 地块雷达诊断",
            title="地块雷达诊断",
            description="对重点地块进行 MPI、GVI、POI、SVF 等多维雷达诊断。",
            output_key=SK.RADAR_DATA,
            artifact_category="analysis",
            aliases=("雷达诊断", "地块雷达"),
        ),
        SubpageSpec(
            label="🔬 AI 前期诊断报告",
            title="AI 前期诊断报告",
            description="调用 LLM 汇总现状问题、空间瓶颈和优先更新方向。",
            output_key=SK.DIAGNOSIS_REPORT,
            artifact_category="report",
            aliases=("AI诊断", "前期诊断"),
        ),
        SubpageSpec(
            label="📋 专项资源分析",
            title="专项资源分析",
            description="生成文化、产业和人口三类专题资源分析文本。",
            output_key="resource_analysis",
            artifact_category="report",
            aliases=("资源分析", "专项分析"),
        ),
    ],
)
