"""Diagnostic engine: plot-level metrics and policy-matrix generation.

Usage:
    from src.engines.site_diagnostic_engine import get_plot_diagnostics, generate_policy_matrix
"""

import json
import logging

import numpy as np
import pandas as pd
import streamlit as st

from src.config import SHP_FILES, DATA_FILES
from src.config.runtime import resolve_path
from src.engines.spatial_engine import get_merged_poi_data
from src.engines.rag_engine import retrieve_rag_context

logger = logging.getLogger("ultimateDESIGN")


# ═══════════════════════════════════════════
# Cached heavy data loaders
# ═══════════════════════════════════════════

@st.cache_data(ttl=3600)
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


@st.cache_data(ttl=3600)
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

    with plots_path.open("r", encoding="utf-8") as f:
        geo = json.load(f)

    try:
        df_poi = get_merged_poi_data()
    except Exception:
        df_poi = pd.DataFrame()

    # Use cached loaders instead of re-reading files every call
    df_spatial = _load_spatial_merge()
    df_nlp = _load_nlp_data()

    # Pre-extract coordinate arrays for vectorized bbox filtering
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

    global_sentiment = 0.0
    if not df_nlp.empty and "Score" in df_nlp.columns:
        global_sentiment = round(float(df_nlp["Score"].mean()), 3)

    results = []
    for feat in geo.get("features", []):
        props = feat.get("properties", {})
        name = props.get("name", f"地块_{props.get('OBJECTID', '?')}")
        area_sqm = props.get("Shape_Area", 0)
        coords = feat["geometry"]["coordinates"][0]
        bbox = (min(c[0] for c in coords), max(c[0] for c in coords),
                min(c[1] for c in coords), max(c[1] for c in coords))

        # Vectorized bbox filtering
        poi_count = _count_in_bbox_vec(poi_coords, bbox)
        gvi_mean, svf_mean, enc_mean, clu_mean = _spatial_means_in_bbox_vec(sp_coords, sp_cols, bbox)

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

def generate_policy_matrix(proposal: str) -> list:
    """Retrieve relevant policy clauses and annotate compliance.

    Returns list[dict] with: clause, source, relevance_score, compliance_note.
    """
    best_chunks = retrieve_rag_context(proposal, top_k=8)
    top_clauses = []
    for score, content, source in best_chunks:
        top_clauses.append({
            "clause": content[:200],
            "source": source,
            "relevance_score": score,
        })

    for clause in top_clauses:
        text = clause["clause"]
        if any(kw in text for kw in ("禁止", "不得", "严格控制")):
            clause["compliance_note"] = "⚠️ 约束性条款 — 需核查合规"
        elif any(kw in text for kw in ("鼓励", "支持")):
            clause["compliance_note"] = "✅ 支持性条款 — 可引用"
        else:
            clause["compliance_note"] = "📋 参考性条款"

    return top_clauses
