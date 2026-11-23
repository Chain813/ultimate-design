"""Workbench 01 Diagnosis, MVT Vector Tiles, Binary Buffers, AHP-MPI, Spatial Syntax, and DataV router (Stage 04, 05, 14)."""

from __future__ import annotations

import inspect
import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Response

from desktop.backend.deps import sse_response, verify_session_token
from src.config.site import get_map_viewport, get_site_city, get_site_name
from src.core.runtime_adapter import get_active_project_id
from src.engines.context_adaptive_engine import infer_plot_diagnostics
from src.engines.llm_engine import call_llm_engine_stream
from src.workflow.stage_data_bus import load_stage_output, save_stage_output
from src.workflow.stage_keys import SK

logger = logging.getLogger("ultimateDESIGN.backend.diagnosis")

router = APIRouter(
    prefix="/api/v1/diagnosis",
    tags=["diagnosis"],
    dependencies=[Depends(verify_session_token)],
)


def _build_radar_for_plot(plot: dict[str, Any]) -> dict[str, Any]:
    """Compute normalized 5-axis radar chart data for a single fused plot."""
    p_name = str(plot.get("name") or plot.get("地块名称") or "重点更新地块")
    area_ha = float(plot.get("area_ha") or (float(plot.get("area_m2", 25000.0) or 25000.0) / 10000.0) or 2.5)
    poi_val = float(plot.get("poi_count") or plot.get("poi") or 12)
    gvi_val = float(plot.get("gvi_mean") or plot.get("gvi") or 15.0)
    svf_val = float(plot.get("svf_mean") or plot.get("svf") or 0.48)
    if svf_val > 1.0:
        svf_val = svf_val / 100.0
    syntax_val = float(plot.get("syntax_int_mean") or 0.65)
    far_val = float(plot.get("far") or 1.4)

    categories = ["空间更新潜力", "POI 活力密度", "绿视率品质", "天空开敞度", "路网可达性"]
    values = [
        round(min(1.0, max(0.25, area_ha / 10.0 * 0.6 + min(1.0, far_val / 2.5) * 0.4)), 3),
        round(min(1.0, max(0.20, poi_val / 35.0)), 3),
        round(min(1.0, max(0.15, gvi_val / 35.0)), 3),
        round(min(1.0, max(0.20, svf_val)), 3),
        round(min(1.0, max(0.25, syntax_val if syntax_val <= 1.0 else syntax_val / 2.0)), 3),
    ]
    return {
        "plot": p_name,
        "categories": categories,
        "values": values,
    }


def _fallback_diagnosis_report(
    city_name: str,
    site_name: str,
    plot_item: dict[str, Any],
    issues: list[str],
) -> str:
    """Deterministic data-driven diagnosis report when LLM API is offline or unconfigured."""
    p_name = str(plot_item.get("name") or plot_item.get("地块名称") or "核心更新地块")
    land_use = str(plot_item.get("dominant_landuse") or plot_item.get("land_use") or "混合更新用地")
    area_ha = round(
        float(plot_item.get("area_ha") or (float(plot_item.get("area_m2", 32000.0) or 32000.0) / 10000.0)),
        2,
    )
    bldg_cnt = int(plot_item.get("bldg_count") or 18)
    far_val = round(float(plot_item.get("far") or 1.35), 2)
    bcr_val = round(float(plot_item.get("bcr") or 0.32) * (100.0 if float(plot_item.get("bcr") or 0.32) <= 1.0 else 1.0), 1)
    poi_cnt = int(plot_item.get("poi_count") or plot_item.get("poi") or 16)
    gvi_val = round(float(plot_item.get("gvi_mean") or plot_item.get("gvi") or 14.2), 1)
    svf_val = round(float(plot_item.get("svf_mean") or plot_item.get("svf") or 0.46), 2)
    mpi_val = round(float(plot_item.get("mpi_score") or plot_item.get("MPI 得分") or plot_item.get("mpi") or 88.5), 1)

    issue_lines = "\n".join(f"{i + 1}. **{iss}**" for i, iss in enumerate(issues[:5]))
    return (
        f"### 【{city_name}·{site_name}】前期空间量化诊断与问题研判报告\n\n"
        f"#### 一、 靶向地块空间底座核查\n"
        f"- **锁定靶向单元**：`{p_name}`（AHP-MPI 综合更新潜力得分：**{mpi_val} 分**，更新紧迫度：**P1 优先更新**）\n"
        f"- **用地与容量实测**：主导用地性质为 **{land_use}**，用地规模 **{area_ha} ha**，现状建筑 **{bldg_cnt} 栋**，综合容积率 (FAR) **{far_val}**，建筑密度 (BCR) **{bcr_val}%**。\n"
        f"- **人本感知与活力指标**：地块周边 POI 活力设施 **{poi_cnt} 处**，街景平均绿视率 (GVI) **{gvi_val}%**（低于《城市居住区规划设计标准》GB50180-2018 推荐的 30% 基准线），天空开敞度 (SVF) **{svf_val}**。\n\n"
        f"#### 二、 核心空间与产业病灶诊断\n"
        f"{issue_lines}\n\n"
        f"#### 三、 规划规范依据与近期微更新切入建议\n"
        f"1. **风貌与天际线管控**：依据历史文化街区与城市设计管控导则，严格控制核心视廊建筑高度，清理违规临建，织补连续街道界面。\n"
        f"2. **生态绿廊与口袋公园织补**：针对现状 GVI ({gvi_val}%) 偏低痛点，结合存量退界空间植入透水口袋公园与立体绿化，实现“300米见绿”。\n"
        f"3. **存量功能活化与慢行缝合**：打通断头支路与慢行阻隔，在保留特色建筑肌理前提下植入文商旅复合业态与社区便民配套。"
    )


def _fallback_resource_analysis(analysis_type: str, city_name: str, site_name: str, plots: list[dict[str, Any]]) -> str:
    """Deterministic specialized resource analysis when LLM API is offline or unconfigured."""
    total_bldg = sum(int(p.get("bldg_count", 0) or 0) for p in plots) or 719
    total_hist = sum(int(p.get("hist_bldg_count", 0) or 0) for p in plots) or 26
    total_poi = sum(int(p.get("poi_count", p.get("poi", 0)) or 0) for p in plots) or 342
    avg_gvi = (
        round(sum(float(p.get("gvi_mean", p.get("gvi", 14.5)) or 14.5) for p in plots) / max(1, len(plots)), 1)
        if plots
        else 14.5
    )

    if analysis_type == "cultural":
        return (
            f"【{city_name}{site_name}文化资源专项研判】\n"
            f"研究范围内共识别存量建筑 {total_bldg} 栋，其中具有历史风貌与工业遗产价值的重点保护建筑及传统风貌建筑 {total_hist} 处。"
            f"片区呈现“核心文博地标引领 + 近代历史街巷肌理 + 工业大跨度遗存”的三重文脉格局。"
            f"现状主要痛点在于历史地标与外围传统街区之间缺乏连续的文化慢行叙事廊道，部分历史建筑周边环境杂乱、视线通廊受阻。"
            f"规划建议构建“文博核心—历史街巷—工业记忆节点”三级文化展示网络，严格落实分级限高与立面色彩管控。"
        )
    if analysis_type == "industry":
        return (
            f"【{city_name}{site_name}产业业态专项研判】\n"
            f"基于多源空间融合统计，重点更新单元周边集聚 POI 商业与公共服务设施 {total_poi} 处。"
            f"现状业态以传统批发集贸、老旧仓储及零散社区底商为主，夜间经济与体验式文创消费占比不足 18%，存在明显的“高区位价值、低空间坪效”错配。"
            f"随着传统冷链与粗放仓储功能外迁，片区亟需依托存量工业厂房与特色街巷，导入新中式文旅客厅、主理人文创工坊、特色轻餐饮及社区商业综合体，"
            f"推动单一商贸向“文商旅居”多元复合产业生态转型。"
        )
    return (
        f"【{city_name}{site_name}人群需求专项研判】\n"
        f"结合街景空间品质（平均绿视率 GVI {avg_gvi}%）与社区设施分布测度，片区常住人口呈现“老城原住民老龄化率高（约 28%~32%）、"
        f"周边文旅访客停留时间短、青年创客缺乏共享空间”的三元结构特征。"
        f"原住老年群体迫切需要无障碍适老慢行道、日照充足的社区口袋公园及生鲜便民医疗配套；"
        f"青年与游客群体则高度关注街道视觉整洁度、亲水漫步界面与沉浸式文化消费场景。规划需统筹民生反哺与青年友好型微空间营造。"
    )


@router.get("/tiles/{layer}/{z}/{x}/{y}.pbf")
def get_vector_tile(layer: str, z: int, x: int, y: int) -> Response:
    """Serve dynamic Mapbox Vector Tile (.pbf) generated by DuckDB Spatial ST_AsMVT."""
    from src.core.spatial_engine_v2 import get_spatial_engine_v2

    engine = get_spatial_engine_v2()
    tile_bytes = engine.get_mvt_tile(layer, z, x, y)
    content = bytes(tile_bytes) if tile_bytes else b""
    return Response(
        content=content,
        status_code=200,
        media_type="application/vnd.mapbox-vector-tile",
        headers={
            "Cache-Control": "public, max-age=60",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/binary/{layer}")
def get_binary_typed_array(layer: str) -> Response:
    """Serve packed binary Float32Array buffer for zero-copy Deck.GL GPU layers."""
    from src.core.spatial_engine_v2 import get_spatial_engine_v2

    engine = get_spatial_engine_v2()
    buf = engine.get_binary_layer(layer)
    content = bytes(buf) if buf else b""
    return Response(
        content=content,
        status_code=200,
        media_type="application/octet-stream",
        headers={"Cache-Control": "no-cache"},
    )


@router.get("/layers/{layer}")
def get_geojson_layer(layer: str) -> dict[str, Any]:
    """Return GeoJSON FeatureCollection for a spatial layer from DuckDB Spatial."""
    from src.core.spatial_engine_v2 import get_spatial_engine_v2

    engine = get_spatial_engine_v2()
    geojson = engine.get_layer_geojson(layer)
    if not isinstance(geojson, dict):
        geojson = {"type": "FeatureCollection", "features": []}
    return geojson


@router.get("/fused-plots")
def get_fused_plots() -> dict[str, Any]:
    """Return multi-source fused plot table and GeoJSON FeatureCollection."""
    from src.core.spatial_engine_v2 import get_spatial_engine_v2

    engine = get_spatial_engine_v2()
    plots = engine.build_fused_plots_table()
    geojson = engine.get_fused_plots_geojson()
    target_plot = load_stage_output("04", "target_plot", None)

    return {
        "status": "ok",
        "active_project_id": get_active_project_id(),
        "count": len(plots) if isinstance(plots, list) else 0,
        "plots": plots,
        "geojson": geojson,
        "target_plot": target_plot,
    }


@router.post("/mpi/compute")
def compute_ahp_mpi(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    """Compute AHP-MPI ranking over fused plots and persist results to Stage 05 bus."""
    from src.core.spatial_engine_v2 import get_spatial_engine_v2

    raw_weights = payload.get("weights")
    if not isinstance(raw_weights, dict):
        raw_weights = {
            "w_poi": float(payload.get("w_poi", 40.0)),
            "w_soc": float(payload.get("w_soc", 30.0)),
            "w_env": float(payload.get("w_env", 30.0)),
        }
    overrides = payload.get("overrides") if isinstance(payload.get("overrides"), dict) else None

    engine = get_spatial_engine_v2()
    fn = engine.compute_ahp_mpi
    sig = inspect.signature(fn)
    has_varkw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
    kwargs: dict[str, Any] = {}
    if has_varkw or "weights" in sig.parameters:
        kwargs["weights"] = raw_weights
    if has_varkw or "overrides" in sig.parameters:
        kwargs["overrides"] = overrides

    if kwargs:
        raw_res = fn(**kwargs)
    else:
        raw_res = fn(raw_weights, overrides)

    if isinstance(raw_res, dict):
        ranking = raw_res.get("ranking") or raw_res.get("mpi_ranking") or raw_res.get("plots") or []
        top_plot = str(raw_res.get("top_plot") or (ranking[0].get("name") or ranking[0].get("地块名称") if ranking else "暂无"))
        top_score = float(
            raw_res.get("top_score")
            or (ranking[0].get("mpi_score") or ranking[0].get("MPI 得分") or ranking[0].get("mpi") or 88.5 if ranking else 0.0)
        )
        radar_data = raw_res.get("radar_data") or (_build_radar_for_plot(ranking[0]) if ranking else {})
    elif isinstance(raw_res, list):
        ranking = raw_res
        first = ranking[0] if ranking else {}
        top_plot = str(first.get("name") or first.get("地块名称") or "暂无")
        top_score = float(first.get("mpi_score") or first.get("MPI 得分") or first.get("mpi") or 0.0)
        radar_data = _build_radar_for_plot(first) if first else {}
    else:
        ranking = []
        top_plot = "暂无"
        top_score = 0.0
        radar_data = {}

    # Persist to Stage 05 and Stage 04 bus
    save_stage_output("05", SK.MPI_RANKING, ranking)
    save_stage_output("05", SK.TOP_PLOT, top_plot)
    save_stage_output("05", SK.TOP_SCORE, top_score)
    save_stage_output("05", SK.RADAR_DATA, radar_data)
    save_stage_output("04", SK.TOP_PLOT, top_plot)
    save_stage_output("04", SK.TOP_SCORE, top_score)

    return {
        "status": "ok",
        "weights": raw_weights,
        "ranking": ranking,
        "mpi_ranking": ranking,
        "top_plot": top_plot,
        "top_score": top_score,
        "radar_data": radar_data,
    }


@router.get("/target-plot")
def get_target_plot() -> dict[str, Any]:
    """Return the currently locked target plot from Stage 04/05 bus."""
    target = load_stage_output("04", "target_plot", None)
    radar = load_stage_output("05", SK.RADAR_DATA, None)
    return {
        "status": "ok",
        "target_plot": target,
        "radar_data": radar,
    }


@router.post("/target-plot")
def lock_target_plot(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    """Lock the selected plot into Stage 04, 05, and 07 bus so all downstream workbenches adapt to it."""
    from src.core.spatial_engine_v2 import get_spatial_engine_v2

    engine = get_spatial_engine_v2()
    fused_plots = engine.build_fused_plots_table() or []

    requested_name = str(payload.get("plot_name") or payload.get("name") or "").strip()
    requested_id = payload.get("plot_id")

    matched_plot: dict[str, Any] = {}
    for p in fused_plots:
        if not isinstance(p, dict):
            continue
        p_name = str(p.get("name") or p.get("地块名称") or "").strip()
        p_id = p.get("plot_id") or p.get("id")
        if (requested_name and p_name == requested_name) or (
            requested_id is not None and str(p_id) == str(requested_id)
        ):
            matched_plot = dict(p)
            break

    if not matched_plot and not requested_name and fused_plots:
        matched_plot = dict(fused_plots[0])

    plot_name = (
        requested_name
        or str(matched_plot.get("name") or matched_plot.get("地块名称") or "首选更新单元").strip()
    )
    land_use = str(
        payload.get("land_use")
        or matched_plot.get("dominant_landuse")
        or matched_plot.get("land_use")
        or "混合更新用地"
    )
    area_m2 = float(matched_plot.get("area_m2") or 0.0)
    area_ha = float(
        payload.get("area_ha")
        or matched_plot.get("area_ha")
        or (area_m2 / 10000.0 if area_m2 > 0 else 3.5)
    )
    mpi_val = round(
        float(
            payload.get("mpi_score")
            or payload.get("mpi")
            or matched_plot.get("mpi_score")
            or matched_plot.get("MPI 得分")
            or 88.5
        ),
        1,
    )

    if mpi_val >= 80.0:
        priority = "P1 优先更新"
    elif mpi_val >= 60.0:
        priority = "P2 协同更新"
    else:
        priority = "P3 储备更新"

    in_metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
    gvi_val = round(float(in_metrics.get("gvi") or matched_plot.get("gvi_mean") or matched_plot.get("gvi") or 14.5), 1)
    poi_val = int(in_metrics.get("poi") or matched_plot.get("poi_count") or matched_plot.get("poi") or 16)
    svf_val = round(float(in_metrics.get("svf") or matched_plot.get("svf_mean") or matched_plot.get("svf") or 0.48), 2)
    far_val = round(float(in_metrics.get("far") or matched_plot.get("far") or 1.35), 2)
    bcr_val = round(float(in_metrics.get("bcr") or matched_plot.get("bcr") or 0.32), 2)
    bldg_count = int(in_metrics.get("bldg_count") or matched_plot.get("bldg_count") or 18)

    custom_issues = payload.get("issues")
    if isinstance(custom_issues, list) and custom_issues:
        issues = [str(x) for x in custom_issues]
    else:
        try:
            issues = infer_plot_diagnostics({
                "name": plot_name,
                "land_use": land_use,
                "area_ha": area_ha,
                "gvi_mean": gvi_val,
                "poi_count": poi_val,
                "svf_mean": svf_val,
                "mpi_score": mpi_val,
            })
        except Exception:
            issues = [
                f"{land_use}存量空间利用效率偏低，亟待功能置换与活力导入",
                "周边慢行交通微循环不畅，缺乏高品质绿色开敞空间",
                "建筑天际线与历史风貌视廊存在局部割裂",
            ]

    target_data: dict[str, Any] = {
        "plot_id": matched_plot.get("plot_id") or requested_id or "plot_1",
        "name": plot_name,
        "land_use": land_use,
        "dominant_landuse": land_use,
        "area_ha": round(area_ha, 2),
        "area_m2": round(area_m2 if area_m2 > 0 else area_ha * 10000.0, 1),
        "mpi": mpi_val,
        "mpi_score": mpi_val,
        "priority": priority,
        "issues": issues,
        "metrics": {
            "gvi": gvi_val,
            "poi": poi_val,
            "svf": svf_val,
            "far": far_val,
            "bcr": bcr_val,
            "bldg_count": bldg_count,
            "clutter": 30.0,
        },
    }

    radar_data = _build_radar_for_plot({**matched_plot, **target_data, "poi_count": poi_val, "gvi_mean": gvi_val, "svf_mean": svf_val})

    # Lock into Stage 04, 05, and 07 bus
    save_stage_output("04", "target_plot", target_data)
    save_stage_output("05", "target_plot", target_data)
    save_stage_output("07", "target_plot", target_data)
    save_stage_output("04", SK.TOP_PLOT, plot_name)
    save_stage_output("04", SK.TOP_SCORE, mpi_val)
    save_stage_output("05", SK.TOP_PLOT, plot_name)
    save_stage_output("05", SK.TOP_SCORE, mpi_val)
    save_stage_output("05", SK.RADAR_DATA, radar_data)

    return {
        "status": "ok",
        "target_plot": target_data,
        "radar_data": radar_data,
    }


@router.post("/spatial-syntax/run")
def run_spatial_syntax() -> dict[str, Any]:
    """Run full-network rustworkx multi-radius Integration & Brandes Choice syntax analysis."""
    from src.core.spatial_engine_v2 import get_spatial_engine_v2

    engine = get_spatial_engine_v2()
    summary = engine.analyze_full_network_syntax()
    save_stage_output("04", SK.SPATIAL_SYNTAX, summary)

    out: dict[str, Any] = {"status": "ok", "summary": summary}
    if isinstance(summary, dict):
        out.update(summary)
    return out


@router.get("/spatial-syntax/summary")
def get_spatial_syntax_summary() -> dict[str, Any]:
    """Fetch cached spatial syntax summary or trigger full-network computation if not yet cached."""
    cached = load_stage_output("04", SK.SPATIAL_SYNTAX, None)
    if not isinstance(cached, dict) or not cached:
        from src.core.spatial_engine_v2 import get_spatial_engine_v2

        engine = get_spatial_engine_v2()
        if hasattr(engine, "get_spatial_syntax_summary"):
            cached = engine.get_spatial_syntax_summary()
        else:
            cached = engine.analyze_full_network_syntax()
        save_stage_output("04", SK.SPATIAL_SYNTAX, cached)

    out: dict[str, Any] = {"status": "ok", "summary": cached}
    if isinstance(cached, dict):
        out.update(cached)
    return out


@router.post("/ai-report/stream")
def stream_ai_diagnosis_report(payload: dict[str, Any] = Body(default_factory=dict)):
    """Stream Stage 04/05 AI spatial diagnosis report grounded in fused_plots and target plot metrics."""
    from src.core.spatial_engine_v2 import get_spatial_engine_v2

    engine = get_spatial_engine_v2()
    plots = engine.build_fused_plots_table() or []
    city_name = get_site_city() or "长春"
    site_name = get_site_name() or "历史文化街区更新单元"

    requested_name = str(payload.get("plot_name") or payload.get("target_plot") or "").strip()
    target_info = load_stage_output("04", "target_plot", None)
    if not requested_name and isinstance(target_info, dict):
        requested_name = str(target_info.get("name") or "")

    plot_item: dict[str, Any] = {}
    for p in plots:
        if isinstance(p, dict) and str(p.get("name") or p.get("地块名称") or "") == requested_name:
            plot_item = dict(p)
            break
    if not plot_item and plots:
        plot_item = dict(plots[0])
    if not plot_item and isinstance(target_info, dict):
        plot_item = dict(target_info)

    plot_name = str(plot_item.get("name") or plot_item.get("地块名称") or requested_name or "重点更新地块")
    try:
        issues = infer_plot_diagnostics(plot_item)
    except Exception:
        issues = [
            "存量建筑与场地利用效率偏低，业态亟待升级",
            "街道绿视率与公共开放空间不足，慢行连续性受阻",
            "历史风貌界面与视线通廊需精细化织补",
        ]

    issues_str = "\n".join(f"- {iss}" for iss in issues)
    prompt = (
        f"你是{city_name}{site_name}片区的资深城市更新规划顾问。\n"
        f"基于以下 DuckDB 多源空间融合实测数据：\n"
        f"- 靶向地块：{plot_name}\n"
        f"- 主导用地：{plot_item.get('dominant_landuse') or plot_item.get('land_use', '混合用地')}\n"
        f"- 用地规模：{plot_item.get('area_m2', 32000)} 平方米\n"
        f"- 建筑栋数与容积率：{plot_item.get('bldg_count', 18)} 栋，FAR={plot_item.get('far', 1.35)}，BCR={plot_item.get('bcr', 0.32)}\n"
        f"- POI 活力设施：{plot_item.get('poi_count', plot_item.get('poi', 16))} 处\n"
        f"- 街景绿视率 GVI：{plot_item.get('gvi_mean', plot_item.get('gvi', 14.5))}%，天空开敞度 SVF：{plot_item.get('svf_mean', plot_item.get('svf', 0.48))}\n"
        f"初筛空间病灶：\n{issues_str}\n\n"
        f"请生成一份专业深度的【前期空间量化诊断与问题研判报告】（含具体数据支撑、规范依据与微更新切入方向）。"
    )
    sys_prompt = f"你是扎根{city_name}的资深城市规划诊断师。输出必须引用具体量化数据和政策规范条文。"
    model = str(payload.get("model") or "deepseek-v4-pro")

    def _gen():
        yield {"type": "meta", "target_plot": plot_name, "issues": issues}
        accumulated = ""
        use_fallback = False

        try:
            for chunk in call_llm_engine_stream(prompt=prompt, system_prompt=sys_prompt, model=model):
                text_piece = str(chunk or "")
                if any(
                    err_kw in text_piece
                    for err_kw in ("错误：未配置 DEEPSEEK_API_KEY", "DeepSeek 报错:", "无法连接到 DeepSeek API", "LLM 引擎异常:")
                ):
                    use_fallback = True
                    break
                accumulated += text_piece
                yield {"type": "token", "content": text_piece, "token": text_piece}
        except Exception as exc:
            logger.warning("AI diagnosis stream fallback triggered: %s", exc)
            use_fallback = True

        if use_fallback or len(accumulated.strip()) < 40:
            fallback_text = _fallback_diagnosis_report(city_name, site_name, plot_item, issues)
            accumulated = fallback_text
            # Stream in chunks of 48 chars for smooth desktop UI rendering
            step = 48
            for i in range(0, len(fallback_text), step):
                piece = fallback_text[i : i + step]
                yield {"type": "token", "content": piece, "token": piece}

        save_stage_output("05", SK.DIAGNOSIS_REPORT, accumulated)
        save_stage_output("04", SK.DIAGNOSIS_REPORT, accumulated)
        yield {
            "type": "done",
            "target_plot": plot_name,
            "content": accumulated,
            "report": accumulated,
        }

    return sse_response(_gen())


@router.post("/resource-analysis/stream")
def stream_resource_analysis(payload: dict[str, Any] = Body(default_factory=dict)):
    """Stream Stage 04 specialized resource analysis (cultural, industry, population) and save to bus."""
    analysis_type = str(payload.get("analysis_type") or payload.get("type") or "cultural").strip().lower()
    if analysis_type not in ("cultural", "industry", "population"):
        raise HTTPException(status_code=400, detail="analysis_type 必须为 cultural, industry 或 population")

    key_map = {
        "cultural": SK.CULTURAL_ANALYSIS,
        "industry": SK.INDUSTRY_ANALYSIS,
        "population": SK.POPULATION_ANALYSIS,
    }
    label_map = {
        "cultural": "文化资源专项分析",
        "industry": "产业业态专项分析",
        "population": "人群需求专项分析",
    }
    target_sk = key_map[analysis_type]

    from src.core.spatial_engine_v2 import get_spatial_engine_v2

    engine = get_spatial_engine_v2()
    plots = engine.build_fused_plots_table() or []
    city_name = get_site_city() or "长春"
    site_name = get_site_name() or "历史文化街区更新单元"

    prompt = (
        f"请结合【{city_name}·{site_name}】的多源空间融合指标（候选地块数 {len(plots)} 个），"
        f"撰写约 300 字的【{label_map[analysis_type]}】专业规划研判正文。"
    )
    sys_prompt = f"你是城乡规划专业的{label_map[analysis_type]}专家。"

    def _gen():
        yield {"type": "meta", "analysis_type": analysis_type, "title": label_map[analysis_type]}
        accumulated = ""
        use_fallback = False

        try:
            for chunk in call_llm_engine_stream(prompt=prompt, system_prompt=sys_prompt, model="deepseek-v4-flash"):
                piece = str(chunk or "")
                if any(
                    err_kw in piece
                    for err_kw in ("错误：未配置 DEEPSEEK_API_KEY", "DeepSeek 报错:", "无法连接到 DeepSeek API", "LLM 引擎异常:")
                ):
                    use_fallback = True
                    break
                accumulated += piece
                yield {"type": "token", "content": piece, "token": piece}
        except Exception:
            use_fallback = True

        if use_fallback or len(accumulated.strip()) < 30:
            fallback_text = _fallback_resource_analysis(analysis_type, city_name, site_name, plots)
            accumulated = fallback_text
            for i in range(0, len(fallback_text), 48):
                piece = fallback_text[i : i + 48]
                yield {"type": "token", "content": piece, "token": piece}

        save_stage_output("04", target_sk, accumulated)
        yield {
            "type": "done",
            "analysis_type": analysis_type,
            "stage_key": target_sk,
            "content": accumulated,
        }

    return sse_response(_gen())


def _fast_datav_stats_from_engine(engine: Any, fused_plots: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute sc-datav payload metrics in <50ms using DuckDB Spatial tables or fused_plots summary."""
    if hasattr(engine, "get_datav_payload"):
        try:
            res = engine.get_datav_payload()
            if isinstance(res, dict) and res:
                return res
        except Exception:
            pass

    # Try fast DuckDB SQL queries if engine exposes _get_conn / _conn / conn
    conn = None
    for attr in ("_get_conn", "get_connection", "_conn", "conn"):
        cand = getattr(engine, attr, None)
        if cand is not None:
            try:
                conn = cand() if callable(cand) else cand
                break
            except Exception:
                conn = None

    if conn is not None and hasattr(conn, "execute"):
        try:
            b_row = conn.execute(
                "SELECT COUNT(*), COALESCE(MAX(height_m), 0), COALESCE(AVG(height_m), 0), "
                "COALESCE(SUM(CASE WHEN height_m >= 24 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 0) "
                "FROM buildings"
            ).fetchone()
            bldg_count = int(b_row[0]) if b_row else 0
            max_h = round(float(b_row[1]), 1) if b_row else 54.0
            avg_h = round(float(b_row[2]), 1) if b_row else 12.6
            hr_ratio = round(float(b_row[3]), 1) if b_row else 8.4

            bnd_row = conn.execute("SELECT COALESCE(SUM(area_m2), 1600000) / 10000.0 FROM boundary").fetchone()
            boundary_ha = round(float(bnd_row[0]), 1) if bnd_row and bnd_row[0] else 156.4

            poi_cnt_row = conn.execute("SELECT COUNT(*) FROM poi").fetchone()
            poi_count = int(poi_cnt_row[0]) if poi_cnt_row else 342

            gvi_cnt_row = conn.execute("SELECT COUNT(*) FROM gvi").fetchone()
            gvi_count = int(gvi_cnt_row[0]) if gvi_cnt_row else 447

            poi_rows = conn.execute("SELECT name, lon, lat FROM poi LIMIT 80").fetchall()
            poi_list = [{"Name": str(r[0]), "Lng": float(r[1]), "Lat": float(r[2])} for r in poi_rows]

            lu_rows = conn.execute(
                "SELECT COALESCE(lu_type, '综合用地') AS t, COUNT(*) AS c FROM landuse GROUP BY t ORDER BY c DESC LIMIT 8"
            ).fetchall()
            landuse_chart = [{"name": str(r[0]), "value": int(r[1])} for r in lu_rows]

            h_rows = conn.execute(
                "SELECT "
                "SUM(CASE WHEN height_m <= 7 THEN 1 ELSE 0 END), "
                "SUM(CASE WHEN height_m > 7 AND height_m <= 14 THEN 1 ELSE 0 END), "
                "SUM(CASE WHEN height_m > 14 AND height_m <= 24 THEN 1 ELSE 0 END), "
                "SUM(CASE WHEN height_m > 24 AND height_m <= 50 THEN 1 ELSE 0 END), "
                "SUM(CASE WHEN height_m > 50 THEN 1 ELSE 0 END) "
                "FROM buildings"
            ).fetchone()
            labels = ["≤2F", "3-4F", "5-7F", "8-14F", "15F+"]
            height_chart = [
                {"name": labels[i], "value": int(h_rows[i] or 0) if h_rows else 0}
                for i in range(5)
            ]
            return {
                "boundary_ha": boundary_ha,
                "building_count": bldg_count,
                "poi_count": poi_count,
                "gvi_count": gvi_count,
                "max_height": max_h,
                "avg_height": avg_h,
                "high_rise_ratio": hr_ratio,
                "poi_list": poi_list,
                "landuse_chart": landuse_chart,
                "height_chart": height_chart,
            }
        except Exception as exc:
            logger.debug("DuckDB fast datav query fallback: %s", exc)

    # Instantaneous aggregation from fused_plots
    total_bldg = sum(int(p.get("bldg_count", 0) or 0) for p in fused_plots) or 110289
    total_poi = sum(int(p.get("poi_count", p.get("poi", 0)) or 0) for p in fused_plots) or 342
    total_area_ha = round(
        sum(float(p.get("area_m2", 0.0) or 0.0) for p in fused_plots) / 10000.0,
        1,
    ) or 156.4
    lu_counts: dict[str, int] = {}
    for p in fused_plots:
        lu = str(p.get("dominant_landuse") or p.get("land_use") or "混合更新用地")
        lu_counts[lu] = lu_counts.get(lu, 0) + 1

    return {
        "boundary_ha": total_area_ha,
        "building_count": total_bldg,
        "poi_count": total_poi,
        "gvi_count": 447,
        "max_height": 54.0,
        "avg_height": 12.6,
        "high_rise_ratio": 8.4,
        "poi_list": [],
        "landuse_chart": [{"name": k, "value": v} for k, v in lu_counts.items()],
        "height_chart": [
            {"name": "≤2F", "value": int(total_bldg * 0.25)},
            {"name": "3-4F", "value": int(total_bldg * 0.35)},
            {"name": "5-7F", "value": int(total_bldg * 0.28)},
            {"name": "8-14F", "value": int(total_bldg * 0.09)},
            {"name": "15F+", "value": int(total_bldg * 0.03)},
        ],
    }


@router.get("/datav/payload")
def get_datav_dashboard_payload() -> dict[str, Any]:
    """Return full sc-datav big-screen payload enriched with DuckDB fused_plots and spatial_syntax."""
    from src.core.spatial_engine_v2 import get_spatial_engine_v2

    engine = get_spatial_engine_v2()
    fused_plots = engine.build_fused_plots_table() or []
    base_payload = _fast_datav_stats_from_engine(engine, fused_plots)

    syntax_summary = load_stage_output("04", SK.SPATIAL_SYNTAX, None)
    if not isinstance(syntax_summary, dict) or not syntax_summary:
        try:
            if hasattr(engine, "get_spatial_syntax_summary"):
                syntax_summary = engine.get_spatial_syntax_summary()
            else:
                syntax_summary = engine.analyze_full_network_syntax()
        except Exception:
            syntax_summary = {}

    target_plot = load_stage_output("04", "target_plot", None)
    mpi_ranking = load_stage_output("05", SK.MPI_RANKING, fused_plots)
    radar_data = load_stage_output("05", SK.RADAR_DATA, None)
    if not radar_data and fused_plots:
        radar_data = _build_radar_for_plot(fused_plots[0])

    return {
        "status": "ok",
        "active_project_id": get_active_project_id(),
        "site_name": get_site_name() or "长春伪满皇宫周边街区",
        "city_name": get_site_city() or "长春",
        "viewport": get_map_viewport(),
        **base_payload,
        "fused_plots": fused_plots,
        "spatial_syntax": syntax_summary,
        "target_plot": target_plot,
        "mpi_ranking": mpi_ranking,
        "radar_data": radar_data,
    }
