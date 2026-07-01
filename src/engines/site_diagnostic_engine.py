"""Diagnostic engine: plot-level metrics and policy-matrix generation.

Usage:
    from src.engines.site_diagnostic_engine import get_plot_diagnostics, generate_policy_matrix
"""

import logging

import numpy as np
import pandas as pd
import streamlit as st

from src.config import SHP_FILES, DATA_FILES
from src.config.runtime import resolve_path
from src.engines.key_plot_engine import load_key_plot_geometries_from_geojson

logger = logging.getLogger("ultimateDESIGN")


# ═══════════════════════════════════════════
# Cached heavy data loaders
# ═══════════════════════════════════════════

@st.cache_data(ttl=3600, max_entries=20)
def _load_spatial_merge() -> pd.DataFrame:
    """Cache the expensive Excel + CSV merge used for GVI/SVF metrics."""
    try:
        df_pts = pd.read_excel(str(DATA_FILES["points"]))
        df_gvi = pd.read_csv(str(DATA_FILES["gvi"]))
        if "Folder" in df_gvi.columns:
            df_gvi["ID"] = df_gvi["Folder"].str.replace("Point_", "").astype(int)
            df_gvi = df_gvi.groupby("ID").mean(numeric_only=True).reset_index()
        return pd.merge(df_pts, df_gvi, on="ID", how="inner")
    except Exception:
        logger.warning("Spatial data unavailable for plot diagnostics", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=3600, max_entries=20)
def _load_nlp_data() -> pd.DataFrame:
    """Cache NLP sentiment CSV."""
    try:
        return pd.read_csv(str(DATA_FILES["nlp"]), encoding="utf-8-sig")
    except Exception:
        logger.warning("NLP data unavailable for plot diagnostics", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_plot_diagnostics() -> list:
    """Multi-dimensional diagnosis for each key plot.

    Returns list[dict] with fields: name, area_ha, gvi_mean, svf_mean,
    enclosure_mean, clutter_mean, poi_count, sentiment_mean, mpi_score.
    """
    plots_path = resolve_path(str(SHP_FILES["plots"]))
    if not plots_path.exists():
        return []

    plot_geometries = load_key_plot_geometries_from_geojson(plots_path)
    if not plot_geometries:
        return []

    try:
        from src.engines.spatial_engine import get_merged_poi_data
        df_poi = get_merged_poi_data()
    except Exception:
        logger.warning("POI data unavailable for plot diagnostics", exc_info=True)
        df_poi = pd.DataFrame()

    # Use cached loaders instead of re-reading files every call
    df_spatial = _load_spatial_merge()
    df_nlp = _load_nlp_data()

    # Pre-extract coordinate arrays for vectorized polygon filtering
    poi_coords = _coordinate_arrays(df_poi)

    sp_coords = None
    sp_cols = {}
    if not df_spatial.empty and "Lng" in df_spatial.columns and "Lat" in df_spatial.columns:
        sp_coords = _coordinate_arrays(df_spatial)
        for col in ("GVI", "SVF", "Enclosure", "Clutter"):
            if col in df_spatial.columns:
                sp_cols[col] = pd.to_numeric(df_spatial[col], errors="coerce").to_numpy(dtype=float)

    global_sentiment = 0.0
    if not df_nlp.empty and "Score" in df_nlp.columns:
        global_sentiment = round(float(df_nlp["Score"].mean()), 3)

    results = []
    for plot_geometry in plot_geometries:
        plot = plot_geometry.plot
        geometry = plot_geometry.geometry
        props = {"name": plot.name}
        name = props.get("name", f"地块_{props.get('OBJECTID', '?')}")
        area_sqm = float(plot.area_ha) * 10000.0
        poi_count = _count_in_geometry_vec(poi_coords, geometry)
        gvi_mean, svf_mean, enc_mean, clu_mean = _spatial_means_in_geometry_vec(sp_coords, sp_cols, geometry)

        s_i = min(1.0, area_sqm / 150000)
        d_i = min(1.0, poi_count / 20) if poi_count > 0 else 0.3
        e_i = gvi_mean / 100.0 if gvi_mean > 0 else 0.3
        mpi = (0.4 * s_i + 0.3 * d_i + 0.3 * (1 - e_i)) * 100

        results.append({
            "name": name,
            "area_ha": round(area_sqm / 10000, 2),
            "gvi_mean": gvi_mean,
            "svf_mean": svf_mean,
            "enclosure_mean": enc_mean,
            "clutter_mean": clu_mean,
            "poi_count": poi_count,
            "sentiment_mean": global_sentiment,
            "mpi_score": round(mpi, 1),
        })

    return results


def _coordinate_arrays(df):
    """Return numeric longitude/latitude arrays, or None when unavailable."""
    if df.empty or "Lng" not in df.columns or "Lat" not in df.columns:
        return None
    lngs = pd.to_numeric(df["Lng"], errors="coerce").to_numpy(dtype=float)
    lats = pd.to_numeric(df["Lat"], errors="coerce").to_numpy(dtype=float)
    return lngs, lats


def _count_in_geometry_vec(coords_tuple, geometry):
    """Count coordinate pairs covered by a polygon geometry."""
    mask = _point_mask_in_geometry(coords_tuple, geometry)
    return int(np.count_nonzero(mask))


def _spatial_means_in_geometry_vec(coords_tuple, col_arrays, geometry):
    """Mean spatial metrics for coordinate pairs covered by a polygon geometry."""
    mask = _point_mask_in_geometry(coords_tuple, geometry)
    if not np.any(mask):
        return 0.0, 0.0, 0.0, 0.0
    gvi = _masked_mean(col_arrays.get("GVI"), mask)
    svf = _masked_mean(col_arrays.get("SVF"), mask)
    enc = _masked_mean(col_arrays.get("Enclosure"), mask)
    clu = _masked_mean(col_arrays.get("Clutter"), mask)
    return gvi, svf, enc, clu


def _point_mask_in_geometry(coords_tuple, geometry):
    """Return a bool mask for points covered by geometry, with bbox prefiltering."""
    if coords_tuple is None or geometry is None or geometry.is_empty:
        return np.array([], dtype=bool)

    from shapely.geometry import Point

    lngs, lats = coords_tuple
    if len(lngs) != len(lats):
        return np.array([], dtype=bool)

    minx, miny, maxx, maxy = geometry.bounds
    finite = np.isfinite(lngs) & np.isfinite(lats)
    bbox_mask = finite & (lngs >= minx) & (lngs <= maxx) & (lats >= miny) & (lats <= maxy)
    mask = np.zeros(len(lngs), dtype=bool)
    for idx in np.nonzero(bbox_mask)[0]:
        mask[idx] = bool(geometry.covers(Point(float(lngs[idx]), float(lats[idx]))))
    return mask


def _masked_mean(values, mask):
    """Return a rounded mean for masked numeric values, or 0 for missing data."""
    if values is None:
        return 0.0
    values = np.asarray(values, dtype=float)
    mask = np.asarray(mask, dtype=bool)
    if len(values) != len(mask):
        return 0.0
    selected = values[mask]
    selected = selected[np.isfinite(selected)]
    if selected.size == 0:
        return 0.0
    return round(float(selected.mean()), 2)


# ═══════════════════════════════════════════
# Policy compliance matrix
# ═══════════════════════════════════════════

@st.cache_data(ttl=1800, show_spinner=False)
def generate_policy_matrix(proposal: str) -> list:
    """Retrieve relevant policy clauses and annotate compliance.

    Returns list[dict] with: clause, source, relevance_score, compliance_note.
    """
    from src.engines.rag_engine import retrieve_rag_context
    best_chunks = retrieve_rag_context(proposal, top_k=8)
    top_clauses = []
    for score, content, source in best_chunks:
        top_clauses.append({
            "clause": content[:300],  # 保留较长文本供 LLM 理解
            "source": source,
            "relevance_score": score,
        })

    # 尝试使用 LLM 进行合规研判
    try:
        from src.engines.llm_engine import call_llm_engine
        from src.utils.llm_json_parser import parse_llm_json

        clauses_input = []
        for i, c in enumerate(top_clauses):
            clauses_input.append(f"[{i}] 条款内容: {c['clause']}")
        clauses_text = "\n".join(clauses_input)

        prompt = f"""
        你是一位专业的城市规划法规审计师。请评估以下“规划设计方案”对“法规条例”的合规性。
        
        规划设计方案：
        {proposal}
        
        法规条例列表：
        {clauses_text}
        
        请对每个法规条文进行合规研判，判断方案是否合规，并给出具体理由和改进建议。
        请严格仅返回 JSON 数组格式，不要包含任何 markdown 块或多余文字：
        [
            {{
                "id": 0,
                "status": "合规 / 存在风险 / 违规 / 不适用",
                "note": "对合规情况的详细解读，如果是违规或风险，提出针对性建议"
            }},
            ...
        ]
        """
        resp = call_llm_engine(prompt=prompt, system_prompt="你是一位客观的城市规划法规审计师。", model="deepseek-v4-pro")
        parsed = parse_llm_json(resp, fallback=None)
        if parsed and isinstance(parsed, list) and len(parsed) == len(top_clauses):
            for item in parsed:
                idx = item.get("id")
                if idx is not None and 0 <= idx < len(top_clauses):
                    status = item.get("status", "📋 参考")
                    note = item.get("note", "")
                    # 如果有具体说明，组合输出
                    top_clauses[idx]["compliance_note"] = f"{status} — {note}"
            return top_clauses
    except Exception:
        pass

    # 降级退回到关键词匹配
    for clause in top_clauses:
        text = clause["clause"]
        if any(kw in text for kw in ("禁止", "不得", "严格控制")):
            clause["compliance_note"] = "⚠️ 约束性条款 — 需核查合规"
        elif any(kw in text for kw in ("鼓励", "支持")):
            clause["compliance_note"] = "✅ 支持性条款 — 可引用"
        else:
            clause["compliance_note"] = "📋 参考性条款"

    return top_clauses
