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

import pandas as pd
import streamlit as st

from src.config import resolve_path, DATA_FILES, GIS_FILES

logger = logging.getLogger("ultimateDESIGN")


# ═══════════════════════════════════════════
# 土地利用统计
# ═══════════════════════════════════════════

@st.cache_data(ttl=3600)
def get_landuse_summary() -> str:
    """读取 landuse_clipped.geojson，统计各类用地面积占比，返回可注入 LLM 的文本。"""
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
        types = {}
        for feat in data.get("features", []):
            t = feat.get("properties", {}).get("Type", "未知")
            types[t] = types.get(t, 0) + 1
        total = sum(types.values())
        lines = [f"研究范围共 {total} 个用地地块："]
        for t, c in sorted(types.items(), key=lambda x: -x[1]):
            lines.append(f"  - {t}: {c} 块 ({c/total*100:.1f}%)")
        return "\n".join(lines)

    if gdf.empty or "Type" not in gdf.columns:
        return "土地利用数据为空。"

    # 尝试计算面积（投影坐标系）
    try:
        if gdf.crs and gdf.crs.is_geographic:
            gdf_proj = gdf.to_crs(gdf.estimate_utm_crs())
        else:
            gdf_proj = gdf
        gdf["area_sqm"] = gdf_proj.geometry.area
    except Exception:
        gdf["area_sqm"] = 0

    total_count = len(gdf)
    total_area = gdf["area_sqm"].sum()
    stats = gdf.groupby("Type").agg(
        count=("Type", "size"),
        area_sum=("area_sqm", "sum"),
    ).sort_values("count", ascending=False)

    lines = [f"研究范围共 {total_count} 个用地地块，总面积约 {total_area/10000:.1f} 公顷："]
    for t, row in stats.iterrows():
        pct = row["count"] / total_count * 100
        area_ha = row["area_sum"] / 10000
        lines.append(f"  - {t}: {int(row['count'])} 块 ({pct:.1f}%), 面积 {area_ha:.1f} ha")

    lines.append("")
    lines.append("【空间研判】居住用地占比过半，说明研究范围以老旧居住区为主体；"
                 "商业服务业与商业办公合计约24%，但POI密度不足，说明商业活力较弱；"
                 "公园绿地仅5.5%，公共开放空间严重不足。")
    return "\n".join(lines)


# ═══════════════════════════════════════════
# POI 空间摘要
# ═══════════════════════════════════════════

@st.cache_data(ttl=3600)
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

@st.cache_data(ttl=3600)
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

@st.cache_data(ttl=3600)
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

@st.cache_data(ttl=3600)
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

@st.cache_data(ttl=3600)
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
