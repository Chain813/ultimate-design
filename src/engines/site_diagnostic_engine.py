"""Diagnostic engine: plot-level metrics and policy-matrix generation.

Usage:
    from src.engines.site_diagnostic_engine import get_plot_diagnostics, generate_policy_matrix
"""

import json
import logging
from typing import Any

import numpy as np
import pandas as pd
import pyproj
import streamlit as st
from shapely.geometry import shape

from src.config import DATA_FILES, SHP_FILES
from src.config.runtime import resolve_path

logger = logging.getLogger("ultimateDESIGN")


def _load_custom_site_fallback() -> dict[str, Any]:
    """Load custom_site.json or session_state['custom_site_context'] if active."""
    try:
        cs = st.session_state.get("custom_site_context")
        if cs and isinstance(cs, dict):
            return cs
    except Exception:
        pass
    try:
        p = resolve_path("config/custom_site.json")
        if p.exists():
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception:
        pass
    return {}


def _compute_geodesic_area_m2(geom_dict: dict[str, Any]) -> float:
    """Dynamically compute geodesic polygon area in m2 using pyproj.Geod(ellps='WGS84')."""
    try:
        geom = shape(geom_dict)
        if geom.is_empty:
            return 0.0
        geod = pyproj.Geod(ellps="WGS84")
        area_val, _ = geod.geometry_area_perimeter(geom)
        return abs(float(area_val))
    except Exception:
        return 0.0


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


def _diagnostics_from_candidate_plots(candidate_plots: list[dict[str, Any]], global_sentiment: float) -> list[dict[str, Any]]:
    """Build plot diagnostics list from custom_site candidate_plots/plots when Key_Plots_District.json is not updated."""
    results = []
    for idx, p in enumerate(candidate_plots):
        if not isinstance(p, dict):
            continue
        name = str(p.get("name") or p.get("Name") or f"地块_{idx + 1}")
        area_sqm = float(p.get("Shape_Area") or p.get("area_m2") or (float(p.get("area_ha", 0.0)) * 10000.0))
        if area_sqm <= 0 and p.get("geometry"):
            area_sqm = _compute_geodesic_area_m2(p["geometry"])
        if area_sqm <= 0:
            area_sqm = 35000.0

        poi_count = int(p.get("poi") or p.get("poi_count") or 18)
        gvi_mean = round(float(p.get("gvi") or p.get("gvi_mean") or 16.0), 2)
        svf_mean = round(float(p.get("svf") or p.get("svf_mean") or 0.55), 2)
        enc_mean = round(float(p.get("enclosure_mean") or 0.42), 2)
        clu_mean = round(float(p.get("clutter_mean") or 0.25), 2)

        s_i = min(1.0, area_sqm / 150000.0)
        d_i = min(1.0, poi_count / 20.0) if poi_count > 0 else 0.3
        e_i = gvi_mean / 100.0 if gvi_mean > 0 else 0.3
        mpi = (0.4 * s_i + 0.3 * d_i + 0.3 * (1.0 - e_i)) * 100.0

        results.append({
            "name": name,
            "area_ha": round(area_sqm / 10000.0, 2),
            "gvi_mean": gvi_mean,
            "svf_mean": svf_mean,
            "enclosure_mean": enc_mean,
            "clutter_mean": clu_mean,
            "poi_count": poi_count,
            "sentiment_mean": global_sentiment,
            "mpi_score": round(mpi, 1),
        })
    return results


@st.cache_data(ttl=600)
def get_plot_diagnostics() -> list:
    """Multi-dimensional diagnosis for each key plot.

    Returns list[dict] with fields: name, area_ha, gvi_mean, svf_mean,
    enclosure_mean, clutter_mean, poi_count, sentiment_mean, mpi_score.
    """
    plots_path = resolve_path(str(SHP_FILES["plots"]))
    custom_site = _load_custom_site_fallback()
    candidate_plots = custom_site.get("candidate_plots") or custom_site.get("plots") or []

    df_nlp = _load_nlp_data()
    global_sentiment = 0.0
    if not df_nlp.empty and "Score" in df_nlp.columns:
        global_sentiment = round(float(df_nlp["Score"].mean()), 3)

    if not plots_path.exists():
        if candidate_plots:
            return _diagnostics_from_candidate_plots(candidate_plots, global_sentiment)
        return []

    try:
        with plots_path.open("r", encoding="utf-8") as f:
            geo = json.load(f)
    except Exception:
        if candidate_plots:
            return _diagnostics_from_candidate_plots(candidate_plots, global_sentiment)
        return []

    features = geo.get("features", [])
    if not features and candidate_plots:
        return _diagnostics_from_candidate_plots(candidate_plots, global_sentiment)

    # Check if custom_site has candidate_plots for a non-Changchun site while Key_Plots_District.json wasn't updated yet
    if candidate_plots and features:
        first_feat_name = str(features[0].get("properties", {}).get("name") or features[0].get("properties", {}).get("Name") or "")
        cs_city = str(custom_site.get("city", ""))
        cs_name = str(custom_site.get("name", ""))
        cand_names = {str(p.get("name") or p.get("Name") or "") for p in candidate_plots if isinstance(p, dict)}
        if (
            first_feat_name == "农贸水产市场"
            and "农贸水产市场" not in cand_names
            and "长春" not in cs_city
            and "伪满" not in cs_name
        ):
            return _diagnostics_from_candidate_plots(candidate_plots, global_sentiment)

    try:
        from src.engines.spatial_engine import get_merged_poi_data
        df_poi = get_merged_poi_data()
    except Exception:
        df_poi = pd.DataFrame()

    df_spatial = _load_spatial_merge()

    poi_coords = None
    if not df_poi.empty and "Lng" in df_poi.columns:
        poi_coords = (df_poi["Lng"].values, df_poi["Lat"].values)

    sp_coords = None
    sp_cols = {}
    if not df_spatial.empty and "Lng" in df_spatial.columns:
        sp_coords = (df_spatial["Lng"].values, df_spatial["Lat"].values)
        for col in ("GVI", "SVF", "Enclosure", "Clutter"):
            if col in df_spatial.columns:
                sp_cols[col] = df_spatial[col].values

    results = []
    for idx, feat in enumerate(features):
        props = feat.get("properties") or {}
        name = props.get("name") or props.get("Name") or props.get("NAME") or f"地块_{props.get('OBJECTID', idx + 1)}"

        raw_area = props.get("Shape_Area") or props.get("area_sqm") or props.get("area_m2") or 0
        try:
            area_sqm = float(raw_area)
        except (ValueError, TypeError):
            area_sqm = 0.0

        geom_dict = feat.get("geometry")
        if area_sqm <= 0 and geom_dict:
            area_sqm = _compute_geodesic_area_m2(geom_dict)
        if area_sqm <= 0 and props.get("area_ha"):
            try:
                area_sqm = float(props["area_ha"]) * 10000.0
            except (ValueError, TypeError):
                pass

        # Safely extract bounding box (min_lon, max_lon, min_lat, max_lat) for both Polygon and MultiPolygon
        bbox = (0.0, 0.0, 0.0, 0.0)
        if geom_dict:
            try:
                geom_obj = shape(geom_dict)
                minx, miny, maxx, maxy = geom_obj.bounds
                bbox = (float(minx), float(maxx), float(miny), float(maxy))
            except Exception:
                pass

        poi_count = _count_in_bbox_vec(poi_coords, bbox)
        gvi_mean, svf_mean, enc_mean, clu_mean = _spatial_means_in_bbox_vec(sp_coords, sp_cols, bbox)

        # Fallback to feature-level properties if no Changchun CSV points fall inside this plot's bbox
        if poi_count == 0 and (props.get("poi") or props.get("poi_count")):
            try:
                poi_count = int(props.get("poi") or props.get("poi_count"))
            except (ValueError, TypeError):
                pass
        if gvi_mean == 0.0 and (props.get("gvi") or props.get("gvi_mean")):
            try:
                gvi_mean = round(float(props.get("gvi") or props.get("gvi_mean")), 2)
            except (ValueError, TypeError):
                pass
        if svf_mean == 0.0 and (props.get("svf") or props.get("svf_mean")):
            try:
                svf_mean = round(float(props.get("svf") or props.get("svf_mean")), 2)
            except (ValueError, TypeError):
                pass

        s_i = min(1.0, area_sqm / 150000.0)
        d_i = min(1.0, poi_count / 20.0) if poi_count > 0 else 0.3
        e_i = gvi_mean / 100.0 if gvi_mean > 0 else 0.3
        mpi = (0.4 * s_i + 0.3 * d_i + 0.3 * (1.0 - e_i)) * 100.0

        results.append({
            "name": str(name),
            "area_ha": round(area_sqm / 10000.0, 2),
            "gvi_mean": gvi_mean,
            "svf_mean": svf_mean,
            "enclosure_mean": enc_mean,
            "clutter_mean": clu_mean,
            "poi_count": poi_count,
            "sentiment_mean": global_sentiment,
            "mpi_score": round(mpi, 1),
        })

    return results


def _count_in_bbox_vec(coords_tuple, bbox):
    """Vectorized point-in-bbox count using pre-extracted numpy arrays."""
    if coords_tuple is None:
        return 0
    lngs, lats = coords_tuple
    mask = (lngs >= bbox[0]) & (lngs <= bbox[1]) & (lats >= bbox[2]) & (lats <= bbox[3])
    return int(np.count_nonzero(mask))


def _spatial_means_in_bbox_vec(coords_tuple, col_arrays, bbox):
    """Vectorized spatial metric means using pre-extracted numpy arrays."""
    if coords_tuple is None:
        return 0.0, 0.0, 0.0, 0.0
    lngs, lats = coords_tuple
    mask = (lngs >= bbox[0]) & (lngs <= bbox[1]) & (lats >= bbox[2]) & (lats <= bbox[3])
    if not np.any(mask):
        return 0.0, 0.0, 0.0, 0.0
    gvi = round(float(col_arrays["GVI"][mask].mean()), 2) if "GVI" in col_arrays else 0.0
    svf = round(float(col_arrays["SVF"][mask].mean()), 2) if "SVF" in col_arrays else 0.0
    enc = round(float(col_arrays["Enclosure"][mask].mean()), 2) if "Enclosure" in col_arrays else 0.0
    clu = round(float(col_arrays["Clutter"][mask].mean()), 2) if "Clutter" in col_arrays else 0.0
    return gvi, svf, enc, clu


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
            "clause": content[:300],
            "source": source,
            "relevance_score": score,
        })

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
                    top_clauses[idx]["compliance_note"] = f"{status} — {note}"
            return top_clauses
    except Exception:
        pass

    for clause in top_clauses:
        text = clause["clause"]
        if any(kw in text for kw in ("禁止", "不得", "严格控制")):
            clause["compliance_note"] = "⚠️ 约束性条款 — 需核查合规"
        elif any(kw in text for kw in ("鼓励", "支持")):
            clause["compliance_note"] = "✅ 支持性条款 — 可引用"
        else:
            clause["compliance_note"] = "📋 参考性条款"

    return top_clauses
