"""阶段数据总线键名常量

避免在多处硬编码字符串键名，防止拼写错误导致静默数据丢失。

Usage:
    from src.workflow.stage_keys import SK
    save_stage_output("05", SK.DIAGNOSIS_REPORT, result)
    data = load_stage_output("05", SK.DIAGNOSIS_REPORT, "")
"""


class SK:
    """Stage Keys — 阶段数据总线键名常量"""
    # Stage 05 问题诊断
    DIAGNOSIS_REPORT = "diagnosis_report"
    MPI_RANKING = "mpi_ranking"
    TOP_PLOT = "top_plot"
    TOP_SCORE = "top_score"
    RADAR_DATA = "radar_data"

    # Stage 06 目标定位
    CASE_BENCHMARK = "case_benchmark"
    DESIGN_CONCEPT = "design_concept"

    # Stage 07 设计策略
    STRATEGY_MATRIX = "strategy_matrix"
    NEGOTIATION_RESULT = "negotiation_result"
    VOTING_SCORES = "voting_scores"

    # Stage 08 总体设计
    MASTER_PLAN = "master_plan"

    # Stage 12 城市设计导则
    DESIGN_GUIDELINE = "design_guideline"

    # Stage 13 成果表达
    FINAL_REPORT = "final_report"

    # AIGC 管线
    AIGC_IMAGE = "image"
    AIGC_PROMPT = "prompt"
    AIGC_SEED = "seed"
