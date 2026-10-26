"""空间数据注入器 —— 将 GIS/CSV 空间数据聚合为结构化文本，供 LLM 提示词注入。

这是整个管线"数据→文本"的核心桥梁。
每一个下游阶段在生成 AI 文本时，都必须通过本模块获取真实的空间统计数据，
确保所有结论都落到空间上、有理有据。

Usage:
    from src.engines.spatial_data_injector import (
        get_landuse_summary,
        get_full_spatial_context,
        get_plot_context,
    )
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st

from src.config import DATA_FILES, GIS_FILES, get_site_city, get_site_district, get_site_name, resolve_path

logger = logging.getLogger("ultimateDESIGN")


def _build_dynamic_landuse_judgment(
    type_items: List[Tuple[str, int, float]],
    total_count: int,
    total_area_sqm: float,
) -> str:
    """根据实际统计出的用地类型列表 [(type_name, count, area_sqm), ...] 动态生成空间研判结论。"""
    if not type_items or total_count <= 0:
        return "【空间研判】暂无足够用地分类数据进行结构研判。"

    use_area = total_area_sqm > 0
    denom = total_area_sqm if use_area else float(total_count)

    scored: List[Tuple[str, float, int, float]] = []
    for t_name, cnt, area_sqm in type_items:
        val = area_sqm if use_area else float(cnt)
        pct = (val / denom * 100.0) if denom > 0 else 0.0
        scored.append((str(t_name), pct, int(cnt), float(area_sqm)))

    scored.sort(key=lambda x: x[1], reverse=True)
    top1_name, top1_pct, _, _ = scored[0]

    parts = [f"场地主导用地类型为「{top1_name}」（占比 {top1_pct:.1f}%）"]
    if len(scored) >= 2:
        top2_name, top2_pct, _, _ = scored[1]
        parts.append(f"次主导类型为「{top2_name}」（占比 {top2_pct:.1f}%）")

    # 识别绿地/开放空间占比
    green_pct = sum(
        pct
        for name, pct, _, _ in scored
        if any(k in name.lower() for k in ("绿地", "公园", "广场", "green", "park", "grass", "meadow"))
    )
    comm_pct = sum(
        pct
        for name, pct, _, _ in scored
        if any(k in name.lower() for k in ("商业", "商务", "办公", "服务", "commercial", "retail", "office"))
    )
    ind_pct = sum(
        pct
        for name, pct, _, _ in scored
        if any(k in name.lower() for k in ("工业", "仓储", "厂", "industrial", "warehouse"))
    )

    if comm_pct > 0:
        parts.append(f"商业与公共服务类用地合计约 {comm_pct:.1f}%")
    if ind_pct >= 10.0:
        parts.append(f"存量工业/仓储用地占 {ind_pct:.1f}%，具备功能置换与产业升级潜力")

    if green_pct < 10.0:
        parts.append(f"公园绿地与开放空间占比仅 {green_pct:.1f}%，公共生态开敞空间存在短板，建议通过微更新植入口袋公园")
    else:
        parts.append(f"生态绿地及开敞空间占比约 {green_pct:.1f}%，具备良好的景观廊道串联基础")

    return "【空间研判】" + "；".join(parts) + "。"


# ═══════════════════════════════════════════
# 土地利用统计
# ═══════════════════════════════════════════

@st.cache_data(ttl=3600, max_entries=20)
def get_landuse_summary() -> str:
    """读取土地利用矢量或自定义场地地块数据，统计各类用地面积占比，返回动态计算的可注入 LLM 文本。"""
    # 若激活了非长春的自定义场地且存在自定义 OSM 土地利用或 plots，优先使用自定义场地数据
    try:
        from src.config.site import get_site_config
        site_cfg = get_site_config()
        s_city = str(site_cfg.get("city") or site_cfg.get("city_name") or "")
        s_name = str(site_cfg.get("name") or site_cfg.get("site_name") or "")
        is_custom_non_cc = bool(s_city or s_name) and ("长春" not in s_city) and ("伪满" not in s_name)
    except Exception:
        site_cfg = {}
        is_custom_non_cc = False

    custom_landuse_path = resolve_path("data/custom_site/osm_landuse.geojson")
    if is_custom_non_cc and custom_landuse_path.exists():
        path = custom_landuse_path
    elif is_custom_non_cc and site_cfg.get("plots"):
        plots = site_cfg.get("plots", [])
        type_areas: Dict[str, List[float]] = {}
        for p in plots:
            lu = str(p.get("land_use") or p.get("type") or "混合用地")
            area_sqm = float(p.get("area_m2") or (float(p.get("area_ha", 1.0)) * 10000.0))
            if lu not in type_areas:
                type_areas[lu] = [0, 0.0]
            type_areas[lu][0] += 1
            type_areas[lu][1] += area_sqm
        total_count = sum(int(v[0]) for v in type_areas.values())
        total_area = sum(float(v[1]) for v in type_areas.values())
        lines = [f"研究范围共 {total_count} 个用地地块，总面积约 {total_area / 10000.0:.1f} 公顷："]
        type_items: List[Tuple[str, int, float]] = []
        for t, (cnt, area_val) in sorted(type_areas.items(), key=lambda x: -x[1][1]):
            pct = (area_val / total_area * 100.0) if total_area > 0 else (cnt / max(total_count, 1) * 100.0)
            lines.append(f"  - {t}: {int(cnt)} 块 ({pct:.1f}%), 面积 {area_val / 10000.0:.1f} ha")
            type_items.append((t, int(cnt), float(area_val)))
        lines.append("")
        lines.append(_build_dynamic_landuse_judgment(type_items, total_count, total_area))
        return "\n".join(lines)
    else:
        path = resolve_path(str(GIS_FILES["landuse"]))

    if not path.exists():
        return "土地利用数据暂不可用。"

    try:
        import geopandas as gpd
        gdf = gpd.read_file(str(path))
    except Exception:
        # 回退到纯 JSON 解析
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        types: Dict[str, Tuple[int, float]] = {}
        for feat in data.get("features", []):
            props = feat.get("properties", {}) or {}
            t = props.get("Type") or props.get("type") or props.get("landuse") or "未知"
            area_sqm = float(props.get("Shape_Area") or props.get("area_m2") or props.get("area_sqm") or 0.0)
            prev_cnt, prev_area = types.get(t, (0, 0.0))
            types[t] = (prev_cnt + 1, prev_area + area_sqm)
        total = sum(v[0] for v in types.values())
        total_area_json = sum(v[1] for v in types.values())
        lines = [f"研究范围共 {total} 个用地地块："]
        type_items_json: List[Tuple[str, int, float]] = []
        for t, (c, a_sqm) in sorted(types.items(), key=lambda x: -x[1][0]):
            lines.append(f"  - {t}: {c} 块 ({c / max(total, 1) * 100:.1f}%)")
            type_items_json.append((t, c, a_sqm))
        lines.append("")
        lines.append(_build_dynamic_landuse_judgment(type_items_json, total, total_area_json))
        return "\n".join(lines)

    type_col = "Type" if "Type" in gdf.columns else ("type" if "type" in gdf.columns else ("landuse" if "landuse" in gdf.columns else None))
    if gdf.empty or not type_col:
        return "土地利用数据为空。"

    # 尝试计算面积（投影坐标系）
    try:
        gdf_proj = gdf.to_crs(gdf.estimate_utm_crs()) if gdf.crs and gdf.crs.is_geographic else gdf
        gdf["area_sqm"] = gdf_proj.geometry.area
    except Exception:
        gdf["area_sqm"] = 0

    total_count = len(gdf)
    total_area = float(gdf["area_sqm"].sum())
    stats = gdf.groupby(type_col).agg(
        count=(type_col, "size"),
        area_sum=("area_sqm", "sum"),
    ).sort_values("count", ascending=False)

    lines = [f"研究范围共 {total_count} 个用地地块，总面积约 {total_area/10000:.1f} 公顷："]
    type_items_gdf: List[Tuple[str, int, float]] = []
    for t, row in stats.iterrows():
        cnt = int(row["count"])
        area_sqm = float(row["area_sum"])
        pct = (area_sqm / total_area * 100.0) if total_area > 0 else (cnt / max(total_count, 1) * 100.0)
        area_ha = area_sqm / 10000.0
        lines.append(f"  - {t}: {cnt} 块 ({row['count'] / total_count * 100:.1f}%), 面积 {area_ha:.1f} ha")
        type_items_gdf.append((str(t), cnt, area_sqm))

    lines.append("")
    lines.append(_build_dynamic_landuse_judgment(type_items_gdf, total_count, total_area))
    return "\n".join(lines)


# ═══════════════════════════════════════════
# POI 空间摘要
# ═══════════════════════════════════════════

@st.cache_data(ttl=3600, max_entries=20)
def get_poi_summary() -> str:
    """汇总 POI 类型分布，返回可注入文本。"""
    try:
        df = pd.read_csv(str(DATA_FILES["poi"]), encoding="utf-8-sig")
    except Exception:
        return "POI 数据暂不可用。"

    if df.empty:
        return "POI 数据为空。"

    total = len(df)
    lines = [f"研究范围共采集 {total} 条 POI 兴趣点："]

    if "Type" in df.columns:
        type_counts = df["Type"].value_counts().head(10)
        for t, c in type_counts.items():
            lines.append(f"  - {t}: {c} 条 ({c/total*100:.1f}%)")
    elif "Category" in df.columns:
        type_counts = df["Category"].value_counts().head(10)
        for t, c in type_counts.items():
            lines.append(f"  - {t}: {c} 条 ({c/total*100:.1f}%)")

    return "\n".join(lines)


# ═══════════════════════════════════════════
# GVI / 街景品质摘要
# ═══════════════════════════════════════════

@st.cache_data(ttl=3600, max_entries=20)
def get_gvi_summary() -> str:
    """汇总 GVI 绿视率分析结果，返回可注入文本。"""
    try:
        df = pd.read_csv(str(DATA_FILES["gvi"]), encoding="utf-8-sig")
    except Exception:
        return "GVI 数据暂不可用。"

    if df.empty or "GVI" not in df.columns:
        return "GVI 数据为空。"

    gvi_mean = df["GVI"].mean()
    gvi_std = df["GVI"].std()
    gvi_min = df["GVI"].min()
    gvi_max = df["GVI"].max()
    low_gvi_pct = (df["GVI"] < 15).sum() / len(df) * 100

    lines = [
        f"街景绿视率 (GVI) 分析（共 {len(df)} 个采样点）：",
        f"  - 平均绿视率: {gvi_mean:.1f}%",
        f"  - 标准差: {gvi_std:.1f}%",
        f"  - 最低 / 最高: {gvi_min:.1f}% / {gvi_max:.1f}%",
        f"  - 绿视率低于15%的采样点占比: {low_gvi_pct:.1f}%",
    ]

    if "SVF" in df.columns:
        lines.append(f"  - 天空可视因子 (SVF) 均值: {df['SVF'].mean():.2f}")
    if "Enclosure" in df.columns:
        lines.append(f"  - 围合度 (Enclosure) 均值: {df['Enclosure'].mean():.2f}")

    if low_gvi_pct > 50:
        lines.append("【空间研判】超过半数采样点绿视率低于15%，街道绿化严重不足，需大规模补绿。")
    elif gvi_mean < 20:
        lines.append("【空间研判】整体绿视率偏低，需在沿街界面和社区节点进行针对性增绿。")

    return "\n".join(lines)


# ═══════════════════════════════════════════
# 重点地块摘要
# ═══════════════════════════════════════════

@st.cache_data(ttl=3600, max_entries=20)
def get_key_plots_summary() -> str:
    """读取 Key_Plots_District.json，返回地块名称和面积列表。"""
    path = resolve_path(str(GIS_FILES["plots"]))
    if not path.exists():
        return "重点地块数据暂不可用。"

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    if not features:
        return "重点地块数据为空。"

    lines = [f"研究范围共 {len(features)} 个重点更新单元："]
    for feat in features:
        props = feat.get("properties", {})
        name = props.get("name", f"地块_{props.get('OBJECTID', '?')}")
        area = props.get("Shape_Area", 0)
        lines.append(f"  - {name}: 面积 {area/10000:.2f} ha")

    return "\n".join(lines)


# ═══════════════════════════════════════════
# 建筑形态摘要
# ═══════════════════════════════════════════

@st.cache_data(ttl=3600, max_entries=20)
def get_building_summary() -> str:
    """汇总建筑形态统计。"""
    try:
        from src.engines.spatial_engine import get_skyline_features
        sky = get_skyline_features()
    except Exception:
        return "建筑形态数据暂不可用。"

    lines = [
        "建筑形态统计：",
        f"  - 建筑总量: {sky.get('building_count', 0)} 栋",
        f"  - 平均高度: {sky.get('avg_height', 0)} m",
        f"  - 最高建筑: {sky.get('max_height', 0)} m",
        f"  - 高层建筑占比: {sky.get('high_rise_ratio', 0)}%",
    ]
    return "\n".join(lines)


# ═══════════════════════════════════════════
# 交通流量摘要
# ═══════════════════════════════════════════

@st.cache_data(ttl=3600, max_entries=20)
def get_traffic_summary() -> str:
    """汇总交通流量数据。"""
    try:
        df = pd.read_csv(str(DATA_FILES["traffic"]), encoding="utf-8-sig")
    except Exception:
        return "交通数据暂不可用。"

    if df.empty:
        return "交通数据为空。"

    lines = [f"交通流量数据（共 {len(df)} 条记录）："]
    # 尝试识别列名
    for col in df.columns:
        if "flow" in col.lower() or "volume" in col.lower() or "count" in col.lower():
            lines.append(f"  - {col} 均值: {df[col].mean():.1f}")
    return "\n".join(lines)


# ═══════════════════════════════════════════
# 全域空间上下文 —— 一键获取所有数据
# ═══════════════════════════════════════════

def get_full_spatial_context() -> str:
    """整合所有空间数据为一个完整的上下文字符串，可直接注入 LLM 提示词。

    这是下游阶段 (Stage 06-12) 的标准数据入口。
    """
    sections = [
        "═══ 研究范围土地利用统计 ═══",
        get_landuse_summary(),
        "",
        "═══ POI 兴趣点分布 ═══",
        get_poi_summary(),
        "",
        "═══ 街景环境品质 (GVI/SVF) ═══",
        get_gvi_summary(),
        "",
        "═══ 建筑形态 ═══",
        get_building_summary(),
        "",
        "═══ 重点更新单元 ═══",
        get_key_plots_summary(),
        "",
        "═══ 交通流量 ═══",
        get_traffic_summary(),
    ]
    return "\n".join(sections)


def get_plot_context(plot_name: str) -> str:
    """获取单个重点地块的详细空间数据上下文。"""
    try:
        from src.engines.site_diagnostic_engine import get_plot_diagnostics
        diags = get_plot_diagnostics()
        match = [d for d in diags if d["name"] == plot_name]
        if match:
            d = match[0]
            return (
                f"地块【{d['name']}】空间诊断：\n"
                f"  - 面积: {d['area_ha']} ha\n"
                f"  - MPI 更新潜力得分: {d['mpi_score']}\n"
                f"  - 绿视率 (GVI): {d['gvi_mean']}%\n"
                f"  - 天空可视因子 (SVF): {d['svf_mean']}\n"
                f"  - 围合度: {d['enclosure_mean']}\n"
                f"  - 杂乱度: {d['clutter_mean']}\n"
                f"  - POI 密度: {d['poi_count']} 个\n"
                f"  - 情感指数: {d['sentiment_mean']}"
            )
    except Exception:
        pass
    return f"地块 {plot_name} 的详细数据暂不可用。"


def generate_spatial_insights() -> str:
    """基于当前所有空间数据汇总，调用 LLM 生成深度空间数据洞察报告。"""
    from src.engines.llm_engine import call_llm_engine
    
    spatial_ctx = get_full_spatial_context()
    city = get_site_city()
    district = get_site_district()
    site_name = get_site_name()
    prompt = f"""
    你是一位资深城市空间数据分析专家。以下是{city}市{district}{site_name}的各项现状空间统计数据：
    
    {spatial_ctx}
    
    请结合上述具体数值，输出一份【空间现状深度洞察报告】：
    1. 🔍 空间供需矛盾：例如，高层高密度居住地块与极低的绿地占比之间的空间矛盾，指出具体地块和矛盾程度。
    2. 🚦 环境品质预警：指出绿视率 GVI 偏低的重灾地段或 POI 活力极低、情感指数消极的老旧地带，引用具体数据。
    3. 💡 更新潜力与机会点：结合 POI、建筑高度、更新潜力 MPI 指数，找出最值得优先进行 TOD 综合开发或微更新的重点街区，并说明定量依据。
    
    必须强引用上述数据包里的实测数值（面积、百分比、个数、均值等），不要做空泛总结。
    """
    return call_llm_engine(
        prompt=prompt,
        system_prompt="你是一位精通空间量化分析和城市更新决策的规划师，善于发现数据之间的深层矛盾。",
        model="deepseek-v4-pro"
    )
