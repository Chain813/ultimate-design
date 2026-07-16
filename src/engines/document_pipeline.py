"""项目设计报告 — 一键生成管道

提供两条独立的自动化管道：
A. run_light_pipeline()    — 轻量管道：基于已有 stage 数据，快速生成设计报告
B. run_full_pipeline()     — 全流程管道：从空间数据出发，生成所有阶段报告 + 设计报告

Usage:
    from src.engines.document_pipeline import run_light_pipeline, run_full_pipeline

    # 轻量管道
    chapters, docx_buf = run_light_pipeline(
        student=AuthorInfo(...),
        progress_callback=lambda cur, tot, label: print(f"{cur}/{tot}: {label}"),
        log_callback=lambda msg: print(f"  {msg}"),
    )

    # 全流程管道
    chapters, docx_buf = run_full_pipeline(
        student=AuthorInfo(...),
        progress_callback=lambda cur, tot, label: print(f"{cur}/{tot}: {label}"),
        log_callback=lambda msg: print(f"  {msg}"),
    )
"""

from __future__ import annotations

import contextlib
import io
import logging
import traceback
from collections.abc import Callable
from typing import Dict, List, Optional, Tuple

from src.engines.document_composer import (
    REPORT_CHAPTERS,
    AuthorInfo,
    assemble_report_docx,
    build_document_context,
    generate_single_section,
)
from src.engines.llm_engine import call_llm_engine

logger = logging.getLogger("ultimateDESIGN")


# ═══════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════

def _skip_if_exists(stage_code: str, key: str) -> bool:
    """检查 stage_bus 中是否已存在数据"""
    from src.workflow.stage_data_bus import load_stage_output
    val = load_stage_output(stage_code, key, None)
    return val is not None and (isinstance(val, str) and len(val) > 20)


def _save(stage_code: str, key: str, data):
    """保存到 stage_bus"""
    from src.workflow.stage_data_bus import save_stage_output
    save_stage_output(stage_code, key, data)


def _call(model: str, system_prompt: str, prompt: str, timeout: int = 180) -> str:
    """统一的 LLM 调用"""
    return call_llm_engine(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model,
    )


def _spatial(max_chars: int = 3000) -> str:
    """获取空间数据上下文"""
    try:
        from src.engines.spatial_data_injector import get_full_spatial_context
        ctx = get_full_spatial_context()
        return ctx[:max_chars] if len(ctx) > max_chars else ctx
    except Exception:
        return "空间数据暂不可用"


def _landuse() -> str:
    try:
        from src.engines.spatial_data_injector import get_landuse_summary
        return get_landuse_summary()
    except Exception:
        return "用地数据暂不可用"


# ═══════════════════════════════════════════════════════════════
# Stage 05: 问题诊断
# ═══════════════════════════════════════════════════════════════

def _gen_diagnosis_report(pc, lc, model="deepseek-v4-pro"):
    """生成 AI 前期诊断报告"""
    from src.workflow.stage_keys import SK

    if _skip_if_exists("05", SK.DIAGNOSIS_REPORT):
        lc("⏭️ 诊断报告已存在，跳过")
        return

    try:
        from src.engines.site_diagnostic_engine import get_plot_diagnostics
        diags = get_plot_diagnostics()
        if not diags:
            lc("⚠️ 无地块诊断数据，使用默认参数生成")
            diags = [{"name": "重点更新单元", "area_ha": 10, "mpi_score": 65, "poi_count": 150, "gvi_mean": 12}]
    except Exception:
        diags = [{"name": "重点更新单元", "area_ha": 10, "mpi_score": 65, "poi_count": 150, "gvi_mean": 12}]

    selected = diags[0]
    prompt = f"""基于以下项目真实数据，生成一份严格基于数据的前期问题诊断报告。不得编造数据中未出现的具体事实：
- 地块名称：{selected.get('name', '重点更新单元')}
- 面积：{selected.get('area_ha', 10)} 公顷
- 微更新潜力指数（MPI）：{selected.get('mpi_score', 65)}（>70 为高潜力）
- 周边 POI 设施数：{selected.get('poi_count', 150)}
- 绿视率（GVI）：{selected.get('gvi_mean', 12)}%（GB50180-2018 要求≥30%）

请生成【前期问题诊断报告】。要求：
1. 列出 4-6 个具体问题，每个含：【问题名称】【数据依据】【政策依据】【严重程度】
2. 结合四大核心痛点：用地混杂、交通割裂、老龄化率30%、环境品质匮乏
3. 最后给出问题优先级排序"""

    result = _call(model, "你是一个城市规划数据分析和报告生成工具。严格基于提供的数据进行诊断，只输出提供数据中能够支撑的结论。不得编造数据、地名、案例或政策条文编号。", prompt)
    if result and len(result) > 50:
        _save("05", SK.DIAGNOSIS_REPORT, result)
        lc(f"✅ 诊断报告生成完成 ({len(result)} 字)")
    else:
        lc("❌ 诊断报告生成失败")


def _gen_mpi_ranking(pc, lc):
    """计算 MPI 排行榜（非 LLM）"""
    from src.workflow.stage_keys import SK

    if _skip_if_exists("05", SK.MPI_RANKING):
        lc("⏭️ MPI 排行已存在，跳过")
        return

    try:
        from src.engines.site_diagnostic_engine import get_plot_diagnostics
        diags = get_plot_diagnostics()
        if diags:
            ranking = sorted(diags, key=lambda d: d.get("mpi_score", 0), reverse=True)
            ranking_data = [{"rank": i+1, "name": d.get("name", ""), "mpi_score": d.get("mpi_score", 0),
                            "area_ha": d.get("area_ha", 0), "poi_count": d.get("poi_count", 0),
                            "gvi_mean": d.get("gvi_mean", 0)} for i, d in enumerate(ranking)]
            _save("05", SK.MPI_RANKING, ranking_data)
            _save("05", SK.TOP_PLOT, ranking[0].get("name", ""))
            _save("05", SK.TOP_SCORE, ranking[0].get("mpi_score", 0))
            lc(f"✅ MPI 排行榜计算完成 ({len(ranking_data)} 个地块)")
        else:
            lc("⚠️ 无地块数据，跳过 MPI 排行")
    except Exception as e:
        lc(f"❌ MPI 排行计算失败: {e}")


# ═══════════════════════════════════════════════════════════════
# Stage 06: 目标定位
# ═══════════════════════════════════════════════════════════════

def _gen_case_benchmark(pc, lc, model="deepseek-v4-pro"):
    from src.workflow.stage_keys import SK
    if _skip_if_exists("06", SK.CASE_BENCHMARK): lc("⏭️ 案例对标已存在"); return

    diag = ""
    with contextlib.suppress(BaseException): diag = str(_load("05", SK.DIAGNOSIS_REPORT, "") or "")[:2000]

    spatial = _spatial(3000)
    prompt = f"""基于以下信息：
【已有诊断】：{diag if diag else '用地结构失衡、交通割裂、老龄化、环境品质匮乏'}
【空间数据】：{spatial}

生成【案例对标分析报告】：
1. 每个案例含【核心经验】【对标问题】【本地化建议】
2. 最后提炼 3-4 条核心设计原则
3. 每条原则必须明确其所回应的空间短板"""

    result = _call(model, "你是一个城市更新案例分析工具。严格基于提供的项目数据和空间信息进行案例对标分析，只输出数据能支撑的结论。不得编造案例、数据或地名。", prompt)
    if result and len(result) > 50:
        _save("06", SK.CASE_BENCHMARK, result)
        lc(f"✅ 案例对标生成完成 ({len(result)} 字)")


def _gen_design_concept(pc, lc, model="deepseek-v4-pro"):
    from src.workflow.stage_keys import SK
    if _skip_if_exists("06", SK.DESIGN_CONCEPT): lc("⏭️ 设计概念已存在"); return

    s1 = str(_load("05", SK.DIAGNOSIS_REPORT, "") or "")[:1500]
    s2 = str(_load("06", SK.CASE_BENCHMARK, "") or "")[:1500]
    spatial = _spatial(4000)

    prompt = f"""基于：
【前期诊断问题】{s1 if s1 else '用地结构失衡、交通割裂、老龄化率30%、环境品质匮乏'}
【案例借鉴经验】{s2 if s2 else '广州永庆坊微改造、北京白塔寺数字织补、伦敦国王十字站城融合'}
【主题】"数字孪生·古今共振——AI赋能下的伪满皇宫周边街区更新规划设计"
【研究范围全域空间数据】：{spatial}

请生成覆盖**整个研究范围**的【全域设计目标策划报告】：

一、总体设计愿景（1段，50-100字）

二、分层目标体系（4-5条），每条须包含：
  - 目标名称
  - 所回应的具体空间短板（必须引用空间数据中的具体数字）
  - 对应的策略方向
  - 空间落位指引（具体到哪些地块或区域）

三、区域经济策划方向：如何利用伪满皇宫文化IP进行业态重构与空间织补

四、土地利用优化建议：基于当前土地利用结构提出功能调整方向"""

    result = _call(model, "你是一个城市规划设计目标分析工具。严格基于提供的空间量化数据进行分析，每个目标和建议必须落到具体空间要素上。禁止空泛陈述，禁止编造数据中不存在的信息。", prompt)
    if result and len(result) > 50:
        _save("06", SK.DESIGN_CONCEPT, result)
        lc(f"✅ 设计概念生成完成 ({len(result)} 字)")


# ═══════════════════════════════════════════════════════════════
# Stage 07: 设计策略 (简化为单次策略矩阵生成)
# ═══════════════════════════════════════════════════════════════

def _gen_strategy_matrix(pc, lc, model="deepseek-v4-pro"):
    from src.workflow.stage_keys import SK
    if _skip_if_exists("07", SK.STRATEGY_MATRIX): lc("⏭️ 策略矩阵已存在"); return

    concept = str(_load("06", SK.DESIGN_CONCEPT, "") or "")[:2000]
    diagnosis = str(_load("05", SK.DIAGNOSIS_REPORT, "") or "")[:1500]
    spatial = _spatial(3000)

    prompt = f"""基于以下信息，生成设计策略矩阵：

【诊断报告】：{diagnosis if diagnosis else '四大痛点：用地混杂、交通割裂、老龄化、环境品质匮乏'}
【设计概念】：{concept if concept else '数字孪生·古今共振'}
【空间数据】：{spatial}

请生成 Markdown 表格格式的设计策略矩阵：
| 策略方向 | 具体举措 | 政策依据 | 空间落位 | 资金逻辑 | 协同度 |

包含 5-6 个策略方向，覆盖：历史保护修缮、微更新修补、功能置换活化、TOD站城一体、生态绿廊修复等。

同时生成协商结果摘要（模拟三方博弈后的共识）：
- 居民代表关注点与妥协条件
- 开发运营商诉求与让步
- 规划师专业建议与平衡方案"""

    result = _call(model, "你是一个城市设计策略分析工具。严格基于提供的诊断数据和设计概念生成策略矩阵。只输出有数据支撑的策略条目，不得编造任何具体举措或数据。", prompt)
    if result and len(result) > 50:
        _save("07", SK.STRATEGY_MATRIX, result)
        _save("07", SK.NEGOTIATION_RESULT, "（全流程管道自动生成）三方基于空间数据达成共识。")
        lc(f"✅ 策略矩阵生成完成 ({len(result)} 字)")


def _gen_design_brief(pc, lc, model="deepseek-v4-pro"):
    from src.workflow.stage_keys import SK
    if _skip_if_exists("07", SK.DESIGN_BRIEF): lc("⏭️ 设计纲要已存在"); return

    try:
        from src.workflow.design_context import build_design_context, synthesize_design_brief
        ctx = build_design_context()
        if ctx.has_strategy or ctx.has_diagnosis:
            brief = synthesize_design_brief(ctx)
            if brief:
                _save("07", SK.DESIGN_BRIEF, brief)
                lc(f"✅ 设计纲要生成完成 ({len(brief)} 字)")
                return
    except Exception:
        pass

    lc("⚠️ 设计纲要生成失败，但不影响后续流程")


# ═══════════════════════════════════════════════════════════════
# Stage 08: 总体城市设计
# ═══════════════════════════════════════════════════════════════

def _gen_spatial_structure(pc, lc, model="deepseek-v4-pro"):
    from src.workflow.stage_keys import SK
    if _skip_if_exists("08", SK.SPATIAL_STRUCTURE): lc("⏭️ 空间结构已存在"); return

    concept = str(_load("06", SK.DESIGN_CONCEPT, "") or "")[:2000]
    strategy = str(_load("07", SK.STRATEGY_MATRIX, "") or "")[:2000]
    spatial = _spatial(4000)

    prompt = f"""基于以下项目数据，推演总体空间结构。严格基于数据，不得编造数据中未出现的内容：

【前期设计目标】：{concept if concept else '数字孪生·古今共振'}
【策略矩阵】：{strategy if strategy else '政策引导→产业导入→经济盘活→空间更新良性循环'}
【全域空间数据】：{spatial}

请生成【总体空间结构推演报告】（不限字数，务必详实）：

一、总体空间结构概念（如"一核两轴多片多节点"），300字以上阐释

二、核心区域定位（逐片区展开）：范围描述、功能定位、开发强度建议、交通联系

三、轴线与廊道体系：主轴、次轴、绿色廊道、视线通廊

四、节点体系：门户节点、文化节点、商业节点、社区节点

五、开发强度分区图则（表格）：| 分区名称 | 主导功能 | 容积率 | 建筑密度 | 绿地率 | 限高 |

六、与前期策略的对应关系

每一条论述都必须引用具体的空间数据，禁止空泛陈述。"""

    result = _call(model, "你是一个城市空间结构分析工具。推演必须严格基于提供的数据，每个功能分区须落到具体的地块和面积，禁止泛泛而谈。不得编造数据中不存在的地块、指标或规划方案。", prompt)
    if result and len(result) > 50:
        _save("08", SK.SPATIAL_STRUCTURE, result)
        lc(f"✅ 空间结构生成完成 ({len(result)} 字)")


def _gen_landuse_sandbox(pc, lc, model="deepseek-v4-pro"):
    from src.workflow.stage_keys import SK
    if _skip_if_exists("08", SK.LANDUSE_SANDBOX): lc("⏭️ 用地沙盘已存在"); return

    landuse_data = _landuse()
    prompt = f"""评估以下用地结构调整方案。严格基于数据，不得编造未提供的经济指标：

研究范围（伪满皇宫周边约160公顷）现状用地结构：
{landuse_data}

推荐用地结构调整方向（基于规划设计目标）：
- 居住用地占比适度降低 5-8%
- 商业服务业用地提升 3-5%
- 绿地与广场用地刚性提升至 ≥15%
- 公共设施用地提升至 ≥8%

请评估此用地结构调整方案的影响：
一、经济活力影响
二、环境承载力影响
三、社区品质影响
四、风险提示
五、综合评级（百分制打分）"""

    result = _call(model, "你是一个土地利用经济分析工具。严格基于提供的用地数据和规划目标进行评估。不编造数据，直接基于数据输出结论。", prompt)
    if result and len(result) > 50:
        _save("08", SK.LANDUSE_SANDBOX, {
            "scenario": "推荐方案：居住-5%、商业+3%、绿地+5%、公共+3%",
            "evaluation": result,
            "res_pct": 45, "com_pct": 15, "off_pct": 10, "green_pct": 15, "public_pct": 8, "remain": 7,
        })
        lc(f"✅ 用地沙盘评估完成 ({len(result)} 字)")


# ═══════════════════════════════════════════════════════════════
# Stage 09: 专项系统设计
# ═══════════════════════════════════════════════════════════════

def _gen_traffic_system(pc, lc, model="deepseek-v4-pro"):
    from src.workflow.stage_keys import SK
    if _skip_if_exists("09", SK.TRAFFIC_SYSTEM): lc("⏭️ 交通系统已存在"); return

    structure = str(_load("08", SK.SPATIAL_STRUCTURE, "") or "")[:2000]
    spatial = _spatial(3500)

    prompt = f"""基于以下数据设计交通系统。每个建议必须有数据依据，不得编造具体道路名称或投资额：

【上游空间结构】：{structure if structure else '一核两轴多片多节点'}
【全域空间数据】：{spatial}

请生成【交通系统设计方案】：

一、道路分级体系：主干路/次干路/支路的功能定位与断面建议
二、公共交通优化：轨道站点接驳、公交线路优化、TOD 开发策略
三、慢行系统规划：慢行网络贯通、自行车道、步行友好街区
四、停车规划：停车分区策略、公共停车场选址建议
五、断头路打通计划：优先打通路段及投资估算

每一条建议都必须引用空间数据，并指明空间落位。"""

    result = _call(model, "你是一个交通系统设计分析工具。严格基于提供的空间数据设计交通方案，每个建议必须落到空间上，不得编造具体道路名称或投资金额。", prompt)
    if result and len(result) > 50:
        _save("09", SK.TRAFFIC_SYSTEM, result)
        lc(f"✅ 交通系统生成完成 ({len(result)} 字)")


def _gen_public_space(pc, lc, model="deepseek-v4-pro"):
    from src.workflow.stage_keys import SK
    if _skip_if_exists("09", SK.PUBLIC_SPACE): lc("⏭️ 公共空间已存在"); return

    structure = str(_load("08", SK.SPATIAL_STRUCTURE, "") or "")[:2000]
    spatial = _spatial(3500)

    prompt = f"""基于以下数据设计公共空间系统。每个选址建议必须有数据依据，不得编造具体公园名称：

【上游空间结构】：{structure if structure else '一核两轴多片多节点'}
【全域空间数据】：{spatial}

请生成【公共空间设计方案】：
一、三级公共空间体系（城市级/片区级/社区级）
二、15分钟社区生活圈规划
三、口袋公园选址与设计导引（至少 6 处，说明选址依据）
四、广场与街道空间设计导引
五、GVI 提升目标与策略（现状绿视率偏低，需提出具体提升措施）"""

    result = _call(model, "你是一个公共空间设计分析工具。严格基于提供的空间数据设计公共空间方案，每个选址和设计建议必须有数据依据，不得编造具体公园名称或点位。", prompt)
    if result and len(result) > 50:
        _save("09", SK.PUBLIC_SPACE, result)
        lc(f"✅ 公共空间生成完成 ({len(result)} 字)")


def _gen_building_form(pc, lc, model="deepseek-v4-pro"):
    from src.workflow.stage_keys import SK
    if _skip_if_exists("09", SK.BUILDING_FORM): lc("⏭️ 建筑形态已存在"); return

    structure = str(_load("08", SK.SPATIAL_STRUCTURE, "") or "")[:2000]
    spatial = _spatial(3500)

    prompt = f"""基于以下数据设计建筑形态控制方案。高度分区和风貌指引与上游空间结构一致，不得自行发挥：

【上游空间结构】：{structure if structure else '一核两轴多片多节点'}
【全域空间数据】：{spatial}

请生成【建筑形态、风貌与立面控制方案】：
一、高度分区控制（核心区≤9m/一般区≤18m/站前区≤24m）
二、建筑体量控制（街墙连续性、塔楼退线、裙房高度）
三、立面风格导引（历史区/风貌协调区/现代发展区各不同）
四、屋顶形式控制（坡屋顶/平屋顶/退台组合）
五、材料与色彩控制体系"""

    result = _call(model, "你是一个建筑形态控制分析工具。严格基于提供的空间结构数据生成建筑形态控制方案，高度分区和风貌指引必须与上游空间结构一致，不得自行发挥。", prompt)
    if result and len(result) > 50:
        _save("09", SK.BUILDING_FORM, result)
        lc(f"✅ 建筑形态生成完成 ({len(result)} 字)")


def _gen_landscape_style(pc, lc, model="deepseek-v4-pro"):
    from src.workflow.stage_keys import SK
    if _skip_if_exists("09", SK.LANDSCAPE_STYLE): lc("⏭️ 风貌景观已存在"); return

    structure = str(_load("08", SK.SPATIAL_STRUCTURE, "") or "")[:2000]
    spatial = _spatial(3500)

    prompt = f"""基于以下数据设计风貌景观方案。色彩和材质建议与历史建筑特征一致，不编造具体建筑名称或保护等级：

【上游空间结构】：{structure if structure else '一核两轴多片多节点'}
【全域空间数据】：{spatial}
【历史背景】：研究范围以伪满皇宫为核心，周边存在大量日伪时期建筑遗存。

请生成【风貌景观设计方案】：
一、风貌分区（历史保护核心区/风貌协调区/现代发展区）
二、色彩控制体系（基于历史建筑色彩提取的主色调谱系）
三、材料与质感控制（传统材料复兴 + 现代材料融入）
四、历史界面修补策略
五、景观节点设计导引（广场、街角、口袋公园、滨水空间）"""

    result = _call(model, "你是一个风貌景观设计分析工具。严格基于提供的空间结构和历史背景数据生成风貌方案。色彩和材质建议必须与历史建筑特征一致，不得编造具体的历史建筑名称或保护等级。", prompt)
    if result and len(result) > 50:
        _save("09", SK.LANDSCAPE_STYLE, result)
        lc(f"✅ 风貌景观生成完成 ({len(result)} 字)")


# ═══════════════════════════════════════════════════════════════
# Stage 10: 重点地块深化
# ═══════════════════════════════════════════════════════════════

def _get_plot_names() -> list:
    """获取重点地块名称列表"""
    try:
        from src.engines.spatial_data_injector import get_key_plots_summary
        summary = get_key_plots_summary()
        # 从摘要中提取地块名
        import re
        names = re.findall(r'[「【](.+?)[」】]', summary)
        if names:
            return names[:5]
    except Exception:
        pass
    # 默认地块列表
    return ["老水产批发市场", "中车旧厂区", "食品调料市场", "清禾市场", "石油公司地块"]


def _gen_plot_metrics(pc, lc, plot_name, model="deepseek-v4-pro"):
    from src.workflow.stage_keys import SK
    key = f"{SK.PLOT_METRICS}_{plot_name}"
    if _skip_if_exists("10", key): lc(f"⏭️ {plot_name} 控规指标已存在"); return

    spatial = _spatial(2000)
    prompt = f"""为重点地块【{plot_name}】推演控制性详细规划指标。指标值在合理范围内，不编造来源依据：

【地块】：{plot_name}（伪满皇宫周边重点更新单元）
【空间数据】：{spatial}

请基于该地块的区位条件和更新定位，反推以下控规指标（以表格呈现）：
| 指标名称 | 建议值 | 依据说明 |
| 容积率 | | |
| 建筑密度 | | |
| 绿地率 | | |
| 建筑限高 | | |
| 停车位配比 | | |
| 配套设施面积 | | |

注意：历史核心区容积率≤1.4、限高≤9m；一般区限高≤18m；站前区限高≤24m。"""

    result = _call(model, "你是一个控规指标分析工具。严格基于提供的空间数据和地块特征推演控规指标，指标值必须在合理的规范范围内，不得编造具体数值的来源依据。", prompt)
    if result and len(result) > 30:
        _save("10", key, result)
        lc(f"✅ {plot_name} 控规指标生成完成")


def _gen_plot_personas(pc, lc, plot_name, model="deepseek-v4-pro"):
    from src.workflow.stage_keys import SK
    key = f"{SK.PLOT_PERSONAS}_{plot_name}"
    if _skip_if_exists("10", key): lc(f"⏭️ {plot_name} 人群画像已存在"); return

    prompt = f"""分析重点地块【{plot_name}】的可能使用人群特征。分析基于项目定位，不编造具体人物故事：

请分析该地块可能吸引的用户群体，生成 3 组人群画像，每组包含：
- 人群名称/年龄/职业
- 24 小时典型行为轨迹
- 对公共空间的具体需求
- 消费能力和业态偏好

结合伪满皇宫周边的历史街区特征和城市更新定位。"""

    result = _call(model, "你是一个城市社会学分析工具。基于项目定位和地块特征，分析可能的使用人群特征。分析必须基于项目实际情况，不得编造具体人物故事或对话。", prompt)
    if result and len(result) > 30:
        _save("10", key, result)
        lc(f"✅ {plot_name} 人群画像生成完成")


def _gen_plot_design(pc, lc, plot_name, model="deepseek-v4-pro"):
    from src.workflow.stage_keys import SK
    key = f"{SK.PLOT_DESIGN}_{plot_name}"
    if _skip_if_exists("10", key): lc(f"⏭️ {plot_name} 深化设计已存在"); return

    spatial = _spatial(2000)
    prompt = f"""为重点地块【{plot_name}】生成空间深化设计方案。每个方案段落到具体空间要素，不编造建筑类型或空间关系：

【地块】：{plot_name}（伪满皇宫周边重点更新单元）
【空间数据】：{spatial}

请生成详细的【空间深化设计方案】：
1. 总平面设计方案描述（功能布局、建筑排布、流线组织）
2. 建筑设计方案（体量、风格、材质、色彩）
3. 景观设计方案（节点、植被、铺装、家具）
4. 交通组织（出入口、停车、人车分流）
5. 与周边地块的空间关系处理
6. 重点界面（沿街立面、广场边界等）的设计意象

每个方案段必须落到具体的空间要素上。"""

    result = _call(model, "你是一个城市空间设计分析工具。严格基于提供的空间数据生成地块级的空间设计方案，每个方案段必须落到具体空间要素。不编造数据中没有的建筑类型、景观要素或空间关系。", prompt)
    if result and len(result) > 30:
        _save("10", key, result)
        lc(f"✅ {plot_name} 深化设计生成完成")


# ═══════════════════════════════════════════════════════════════
# Stage 11: 实施路径
# ═══════════════════════════════════════════════════════════════

def _gen_region_phasing(pc, lc, model="deepseek-v4-pro"):
    if _skip_if_exists("11", "region_phasing"): lc("⏭️ 实施分期已存在"); return

    strategy = str(_load("07", "strategy_matrix", "") or "")[:2000]
    spatial = _spatial(3000)

    prompt = f"""制定全域实施路径。时序安排与空间数据一致，不编造具体项目名称或投资额：

【策略矩阵】：{strategy if strategy else '政策引导→产业导入→经济盘活→空间更新的良性循环'}
【空间数据】：{spatial}

请生成【全域实施路径报告】：

一、近期行动（1-3年）——触媒激活与环境改善
二、中期建设（3-5年）——产业导入与功能升级
三、远期目标（5-10年）——品牌运营与持续发展
四、政策组合拳时序表
五、资金闭环模型"""

    result = _call(model, "你是一个城市更新实施分析工具。严格基于提供的策略矩阵和空间数据制定实施分期方案。时序安排必须与空间数据的实际情况一致，不得编造具体的项目名称或投资额。", prompt)
    if result and len(result) > 50:
        _save("11", "region_phasing", result)
        lc(f"✅ 实施分期生成完成 ({len(result)} 字)")


# ═══════════════════════════════════════════════════════════════
# Stage 12: 城市设计导则 (精简版)
# ═══════════════════════════════════════════════════════════════

def _gen_design_guideline(pc, lc, model="deepseek-v4-pro"):
    from src.workflow.stage_keys import SK
    if _skip_if_exists("12", SK.DESIGN_GUIDELINE): lc("⏭️ 设计导则已存在"); return

    structure = str(_load("08", SK.SPATIAL_STRUCTURE, "") or "")[:2000]
    traffic = str(_load("09", SK.TRAFFIC_SYSTEM, "") or "")[:1500]
    building = str(_load("09", SK.BUILDING_FORM, "") or "")[:1500]
    landscape = str(_load("09", SK.LANDSCAPE_STYLE, "") or "")[:1500]
    public = str(_load("09", SK.PUBLIC_SPACE, "") or "")[:1500]

    prompt = f"""撰写城市设计导则（精简版）。每条管控条文必须有上游数据支撑，不编造规范编号或数值：

【空间结构】：{structure if structure else '一核两轴多片多节点'}
【交通系统】：{traffic}
【建筑形态】：{building}
【风貌景观】：{landscape}
【公共空间】：{public}

请撰写【城市设计导则】（含以下板块）：
一、总则与基本原则
二、空间结构与功能布局管控
三、建筑风貌控制导则（高度/色彩/材质/立面）
四、道路交通与慢行系统导则
五、公共空间与景观绿化导则
六、历史文化保护与活化导则

每一条管控条文都必须有数据支撑或法规依据。"""

    result = _call(model, "你是一个城市设计导则撰写工具。严格基于提供的上游阶段成果撰写导则。每条管控条文必须有数据支撑或法规依据，不得编造规范编号或具体管控数值。", prompt)
    if result and len(result) > 50:
        _save("12", SK.DESIGN_GUIDELINE, result)
        lc(f"✅ 设计导则生成完成 ({len(result)} 字)")


# ═══════════════════════════════════════════════════════════════
# 补充小节
# ═══════════════════════════════════════════════════════════════

def _gen_supplementary(pc, lc, model="deepseek-v4-pro"):
    """生成全部 8 个补充小节"""
    from src.workflow.stage_keys import SK
    spatial = _spatial(2000)
    strategy = str(_load("07", SK.STRATEGY_MATRIX, "") or "")[:1500]
    concept = str(_load("06", SK.DESIGN_CONCEPT, "") or "")[:1500]
    structure = str(_load("08", SK.SPATIAL_STRUCTURE, "") or "")[:1500]

    supplements = [
        # (stage, key, title, system_prompt, prompt)
        ("04", SK.CULTURAL_ANALYSIS, "2.6 文化资源分析",
         "你是一个城市文化资源分析工具。严格基于提供的空间数据描述文化资源特征。不得编造数据中未出现的具体文物名称、保护级别或历史事件。",
         f"请基于提供的空间数据，描述研究范围内的文化资源特征，撰写约300字。只陈述数据中能确认的内容。\n\n【空间数据】\n{spatial}\n\n只输出分析文本正文。"),

        ("04", SK.INDUSTRY_ANALYSIS, "2.7 产业业态分析",
         "你是一个产业业态分析工具。严格基于提供的POI和空间数据描述产业特征。不得编造具体的商业品牌名或企业名。",
         f"请基于提供的空间数据，描述研究范围内的产业业态特征，撰写约300字。只陈述能确认的内容。\n\n【空间数据】\n{spatial}\n\n只输出分析文本正文。"),

        ("04", SK.POPULATION_ANALYSIS, "2.8 人群需求分析",
         "你是一个社区人群分析工具。严格基于提供的空间数据描述人群特征。不得编造具体的访谈记录、人物故事或没有数据来源的统计数据。",
         f"请基于提供的空间数据，描述研究范围内的社区人群特征，撰写约300字。只陈述数据中能确认的内容。\n\n【空间数据】\n{spatial}\n\n只输出分析文本正文。"),

        ("07", SK.DESIGN_BASIS, "3.1 设计依据",
         "你是一个设计依据整理工具。严格基于提供的数据提炼设计依据。上位规划、法规条文只列出已知的，不得编造文件编号或条文内容。",
         f"请基于以下数据提炼设计依据，撰写约500字。只列出有依据可循的内容。\n\n设计概念：{concept}\n策略矩阵：{strategy}\n空间数据：{spatial[:1500]}\n\n只输出正文。"),

        ("07", SK.DESIGN_PRINCIPLES, "3.2 设计原则",
         "你是一个设计原则整理工具。严格基于提供的数据提炼设计原则。每条原则必须与项目实际关联，不得空泛罗列通用原则。",
         f"请基于以下数据提炼设计原则，撰写约500字。每条原则必须对应项目中的具体问题或目标。\n\n设计概念：{concept}\n策略矩阵：{strategy}\n\n只输出正文。"),

        ("07", SK.DESIGN_POSITIONING, "3.4 设计定位",
         "你是一个设计定位整理工具。严格基于提供的数据提炼设计定位。定位描述必须与项目的实际空间条件一致，不得拔高或泛化。",
         f"请基于以下数据提炼设计定位，撰写约500字。\n\n设计概念：{concept}\n策略矩阵：{strategy}\n\n只输出正文。"),

        ("09", SK.INDUSTRY_PLANNING, "4.6 产业业态规划",
         "你是一个产业规划分析工具。严格基于提供的空间结构和策略数据制定产业业态方案。不得编造具体的企业名称、投资金额或招商政策细节。",
         f"请基于以下数据制定产业业态规划方案。\n\n【空间结构】：{structure}\n【策略矩阵】：{strategy}\n【空间数据】：{spatial}\n\n涵盖：产业定位与愿景、业态分区引导、业态准入与管控、产业导入时序。"),

        ("10", SK.SPECIALIZED_STUDY, "5.1 特色专项研究",
         "你是一个技术方法总结工具。严格基于项目实际使用的技术方法进行总结，不得编造未使用的技术方案或杜撰技术参数。",
         f"请总结本项目的特色专项研究方法。涵盖：1. 数字孪生底座构建；2. AIGC设计推演；3. LLM多方协同推演；4. MPI更新潜力评估模型。\n\n【设计纲要】：{concept}\n【空间结构】：{structure}\n\n只输出与项目实际相关的内容，不展开无关技术介绍。"),
    ]

    for stage, key, title, sys_prompt, prompt in supplements:
        if _skip_if_exists(stage, key):
            lc(f"⏭️ {title} 已存在，跳过")
            continue

        try:
            result = _call(model, sys_prompt, prompt)
            if result and len(result) > 30:
                _save(stage, key, result)
                lc(f"✅ {title} 生成完成 ({len(result)} 字)")
            else:
                lc(f"❌ {title} 生成失败")
        except Exception as e:
            lc(f"❌ {title} 异常: {e}")


# ═══════════════════════════════════════════════════════════════
# 工具：从 stage_bus 加载
# ═══════════════════════════════════════════════════════════════

def _load(stage_code: str, key: str, default=None):
    from src.workflow.stage_data_bus import load_stage_output
    return load_stage_output(stage_code, key, default)


# ═══════════════════════════════════════════════════════════════
# Pipeline A: 轻量管道
# ═══════════════════════════════════════════════════════════════

def run_light_pipeline(
    student: AuthorInfo | None = None,
    progress_callback: Callable[[int, int, str], None] | None = None,
    log_callback: Callable[[str], None] | None = None,
    model: str = "deepseek-v4-pro",
    enable_deai: bool = False,
    deai_intensity: float = 0.7,
) -> tuple[dict[str, str], io.BytesIO]:
    """轻量管道：基于已有 stage 数据，快速生成设计报告。

    步骤: 8个补充小节 → 27个论文章节 → [降AI处理] → docx 组装

    Args:
        enable_deai: 是否启用降 AI 率后处理
        deai_intensity: 降 AI 处理强度 0.0-1.0

    Returns:
        (chapters_dict, docx_bytesio)
    """
    if student is None:
        student = AuthorInfo()

    def pc(cur, total, label):
        if progress_callback:
            progress_callback(cur, total, label)

    def lc(msg):
        if log_callback:
            log_callback(msg)

    total_steps = 8 + 27 + 1  # 补充 + 论文 + 组装
    step = 0

    lc("=" * 50)
    lc("🚀 轻量管道启动 — 基于已有数据生成设计报告")
    lc("=" * 50)

    # Step 1: 补充小节
    lc("\n📋 Phase 1/3: 生成补充小节 (8 个)")
    _gen_supplementary(pc, lc, model=model)
    step += 8
    pc(step, total_steps, "补充小节完成")

    # Step 2: 论文章节
    lc("\n📝 Phase 2/3: 生成论文章节 (27 节)")
    ctx = build_document_context()
    chapters: dict[str, str] = {}
    for i, sec in enumerate(REPORT_CHAPTERS):
        pc(step + i, total_steps, f"论文 {sec.section_id} {sec.title}")
        try:
            text = generate_single_section(sec, ctx, model=model)
            chapters[sec.section_id] = text
            lc(f"  ✅ {sec.section_id} {sec.title} ({len(text)} 字)")
        except Exception as e:
            chapters[sec.section_id] = f"[生成失败] {e}"
            lc(f"  ❌ {sec.section_id} {sec.title}: {e}")
    step += 27
    pc(step, total_steps, "论文章节完成")

    # Step 3 (可选): 降 AI 率后处理
    if enable_deai:
        lc("\n🔧 Phase 3/4: 降 AI 率后处理")
        lc(f"   强度: {deai_intensity:.0%} | 策略: 规则打散 + LLM风格扰动 + 个人观察注入")
        try:
            from src.engines.deai_processor import deai_all_chapters
            chapters = deai_all_chapters(
                chapters,
                intensity=deai_intensity,
                log_callback=lc,
            )
            lc("✅ 降AI处理完成")
        except Exception as e:
            lc(f"⚠️ 降AI处理异常（保留原文）: {e}")
        step += 1
        pc(step, total_steps, "降AI处理完成")

    # Step 4: 组装 docx
    phase_label = "4/4" if enable_deai else "3/3"
    lc(f"\n📦 Phase {phase_label}: 组装 Word 文档")
    step += 1
    pc(step, total_steps, "组装 docx...")
    try:
        buf = assemble_report_docx(chapters=chapters, student=student)
        lc(f"✅ 设计报告生成完毕！({len(buf.getvalue())/1024:.1f} KB)")
    except Exception as e:
        lc(f"❌ 文档组装失败: {e}")
        raise

    pc(total_steps, total_steps, "✅ 完成")
    return chapters, buf


# ═══════════════════════════════════════════════════════════════
# Pipeline B: 全流程管道
# ═══════════════════════════════════════════════════════════════

def run_full_pipeline(
    student: AuthorInfo | None = None,
    progress_callback: Callable[[int, int, str], None] | None = None,
    log_callback: Callable[[str], None] | None = None,
    model: str = "deepseek-v4-pro",
    enable_deai: bool = False,
    deai_intensity: float = 0.7,
) -> tuple[dict[str, str], io.BytesIO]:
    """全流程管道：从空间数据出发，生成所有阶段报告 + 设计报告。

    步骤:
    Stage 05 诊断报告 + MPI 排行
    Stage 06 案例对标 + 设计概念
    Stage 07 策略矩阵 + 设计纲要
    Stage 08 空间结构 + 用地沙盘
    Stage 09 交通 + 公共空间 + 建筑形态 + 风貌景观
    Stage 10 重点地块（N个地块 × 3项）
    Stage 11 实施分期
    Stage 12 设计导则（精简版）
    → 补充小节 (8) → 论文章节 (27) → docx 组装

    Returns:
        (chapters_dict, docx_bytesio)
    """
    if student is None:
        student = AuthorInfo()

    def pc(cur, total, label):
        if progress_callback:
            progress_callback(cur, total, label)

    def lc(msg):
        if log_callback:
            log_callback(msg)

    lc("=" * 60)
    lc("🚀 全流程管道启动 — 从空间数据出发，自动生成所有阶段报告")
    lc("=" * 60)

    # 计算总步数
    plot_names = _get_plot_names()
    n_plots = min(len(plot_names), 5)
    total_steps = (
        2 +     # Stage 05: 诊断报告 + MPI
        2 +     # Stage 06: 案例 + 概念
        2 +     # Stage 07: 策略矩阵 + 纲要
        2 +     # Stage 08: 空间结构 + 用地沙盘
        4 +     # Stage 09: 四系统
        n_plots * 3 +  # Stage 10: 每地块 3 项
        1 +     # Stage 11: 实施分期
        1 +     # Stage 12: 导则
        8 +     # 补充小节
        27 +    # 论文章节
        (1 if enable_deai else 0) +  # 降AI处理
        1       # docx 组装
    )
    step = 0

    # ── Stage 05 ──
    lc("\n📊 Stage 05: 问题诊断")
    _gen_diagnosis_report(pc, lc, model=model); step += 1; pc(step, total_steps, "诊断报告")
    _gen_mpi_ranking(pc, lc); step += 1; pc(step, total_steps, "MPI 排行")

    # ── Stage 06 ──
    lc("\n🎯 Stage 06: 目标定位")
    _gen_case_benchmark(pc, lc, model=model); step += 1; pc(step, total_steps, "案例对标")
    _gen_design_concept(pc, lc, model=model); step += 1; pc(step, total_steps, "设计概念")

    # ── Stage 07 ──
    lc("\n♟️ Stage 07: 设计策略")
    _gen_strategy_matrix(pc, lc, model=model); step += 1; pc(step, total_steps, "策略矩阵")
    _gen_design_brief(pc, lc, model=model); step += 1; pc(step, total_steps, "设计纲要")

    # ── Stage 08 ──
    lc("\n🗺️ Stage 08: 总体城市设计")
    _gen_spatial_structure(pc, lc, model=model); step += 1; pc(step, total_steps, "空间结构")
    _gen_landuse_sandbox(pc, lc, model=model); step += 1; pc(step, total_steps, "用地沙盘")

    # ── Stage 09 ──
    lc("\n🔧 Stage 09: 专项系统设计")
    _gen_traffic_system(pc, lc, model=model); step += 1; pc(step, total_steps, "交通系统")
    _gen_public_space(pc, lc, model=model); step += 1; pc(step, total_steps, "公共空间")
    _gen_building_form(pc, lc, model=model); step += 1; pc(step, total_steps, "建筑形态")
    _gen_landscape_style(pc, lc, model=model); step += 1; pc(step, total_steps, "风貌景观")

    # ── Stage 10 ──
    lc(f"\n🏗️ Stage 10: 重点地块深化 ({n_plots} 个地块)")
    for pname in plot_names[:n_plots]:
        lc(f"   地块: {pname}")
        _gen_plot_metrics(pc, lc, pname, model=model); step += 1; pc(step, total_steps, f"{pname} 指标")
        _gen_plot_personas(pc, lc, pname, model=model); step += 1; pc(step, total_steps, f"{pname} 人群")
        _gen_plot_design(pc, lc, pname, model=model); step += 1; pc(step, total_steps, f"{pname} 设计")

    # ── Stage 11 ──
    lc("\n📅 Stage 11: 实施路径")
    _gen_region_phasing(pc, lc, model=model); step += 1; pc(step, total_steps, "实施分期")

    # ── Stage 12 ──
    lc("\n📜 Stage 12: 城市设计导则")
    _gen_design_guideline(pc, lc, model=model); step += 1; pc(step, total_steps, "设计导则")

    # ── 补充小节 ──
    lc("\n📋 补充小节 (8 个)")
    _gen_supplementary(pc, lc, model=model); step += 8; pc(step, total_steps, "补充小节完成")

    # ── 论文章节 ──
    lc("\n📝 生成论文章节 (27 节)")
    ctx = build_document_context()
    chapters: dict[str, str] = {}
    for i, sec in enumerate(REPORT_CHAPTERS):
        pc(step + i, total_steps, f"论文 {sec.section_id} {sec.title}")
        try:
            text = generate_single_section(sec, ctx, model=model)
            chapters[sec.section_id] = text
            lc(f"  ✅ {sec.section_id} {sec.title} ({len(text)} 字)")
        except Exception as e:
            chapters[sec.section_id] = f"[生成失败] {e}"
            lc(f"  ❌ {sec.section_id} {sec.title}: {e}")
    step += 27
    pc(step, total_steps, "论文章节完成")

    # ── 降 AI 处理 (可选) ──
    if enable_deai:
        lc("\n🔧 降 AI 率后处理")
        lc(f"   强度: {deai_intensity:.0%} | 策略: 规则打散 + LLM风格扰动 + 个人观察注入")
        try:
            from src.engines.deai_processor import deai_all_chapters
            chapters = deai_all_chapters(
                chapters,
                intensity=deai_intensity,
                log_callback=lc,
            )
            lc("✅ 降AI处理完成")
        except Exception as e:
            lc(f"⚠️ 降AI处理异常（保留原文）: {e}")
        step += 1
        pc(step, total_steps, "降AI处理完成")

    # ── 组装 ──
    lc("\n📦 组装 Word 文档")
    step += 1
    pc(step, total_steps, "组装 docx...")
    try:
        buf = assemble_report_docx(chapters=chapters, student=student)
        lc(f"\n{'='*50}")
        lc(f"🎉 全流程管道执行完毕！")
        lc(f"📄 设计报告大小: {len(buf.getvalue())/1024:.1f} KB")
        lc(f"📊 论文章节数: {len(chapters)}")
        lc(f"{'='*50}")
    except Exception as e:
        lc(f"❌ 文档组装失败: {e}")
        lc(traceback.format_exc())
        raise

    pc(total_steps, total_steps, "✅ 全流程完成")
    return chapters, buf
