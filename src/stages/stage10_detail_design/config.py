from src.stages.common.workspace import StageWorkspaceSpec, SubpageSpec
from src.workflow.stage_keys import SK

STAGE10_WORKSPACE = StageWorkspaceSpec(
    stage_code="10",
    title="重点地段深化",
    description="围绕重点地块展开诊断雷达、控规指标、人群画像、深化方案和专题研究。",
    evidence_stages=("08", "09", "10"),
    subpages=[
        SubpageSpec(
            label="📍 重点地块诊断雷达",
            title="重点地块诊断雷达",
            description="展示重点地块的 MPI、GVI、SVF、POI 等多维诊断指标。",
            output_key=SK.RADAR_DATA,
            artifact_category="analysis",
            aliases=("地块诊断", "诊断雷达"),
        ),
        SubpageSpec(
            label="📊 控制性详细指标推演",
            title="控制性详细指标推演",
            description="按所选地块推导 FAR、建筑密度、绿地率和限高等控规指标。",
            output_key=SK.PLOT_METRICS,
            artifact_category="report",
            aliases=("控规指标", "指标推演"),
        ),
        SubpageSpec(
            label="👥 目标人群与行为画像",
            title="目标人群与行为画像",
            description="生成所选地块的典型人群画像、行为轨迹与空间需求。",
            output_key=SK.PLOT_PERSONAS,
            artifact_category="report",
            aliases=("人群画像", "行为画像"),
        ),
        SubpageSpec(
            label="🏗️ 空间深化设计方案",
            title="空间深化设计方案",
            description="综合上游专项策略和地块指标生成空间深化方案。",
            output_key=SK.PLOT_DESIGN,
            artifact_category="report",
            aliases=("深化方案", "空间深化"),
        ),
        SubpageSpec(
            label="🔄 Before/After 推演",
            title="Before/After 推演",
            description="对比现状与更新后的街景或空间意向。",
            output_key=SK.BEFORE_AFTER,
            artifact_category="image",
            aliases=("before after", "前后对比"),
        ),
        SubpageSpec(
            label="🔬 特色专项研究",
            title="特色专项研究",
            description="针对特色议题生成可纳入成果汇报的专项研究报告。",
            output_key=SK.SPECIALIZED_STUDY,
            artifact_category="report",
            aliases=("特色专项", "专项研究"),
        ),
    ],
)
