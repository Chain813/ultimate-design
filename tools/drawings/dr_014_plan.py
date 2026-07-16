from pathlib import Path

import numpy as np
import pandas as pd
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"
GIS_DIR = ROOT / "data/gis"
ASSETS_DIR = ROOT / "assets"

import geopandas as gpd
import matplotlib.font_manager as fm
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
from PIL import Image


def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    if landuse is not None and not landuse.empty:
        # 1. Load sandbox settings from Stage 08
        try:
            from src.workflow.stage_data_bus import load_stage_output
            from src.workflow.stage_keys import SK
            sandbox = load_stage_output("08", SK.LANDUSE_SANDBOX, {})
        except Exception:
            sandbox = {}

        res_pct = sandbox.get("res_pct", 48.0)
        com_pct = sandbox.get("com_pct", 16.0)
        off_pct = sandbox.get("off_pct", 8.0)
        green_pct = sandbox.get("green_pct", 10.0)
        public_pct = sandbox.get("public_pct", 6.0)

        # 2. Run Greedy Spatial Allocation
        gdf_proj = landuse.copy()
        gdf_proj["area_sqm"] = gdf_proj.geometry.area
        centroids = gdf_proj.geometry.centroid
        cx_s = centroids.x
        cy_s = centroids.y

        # Centers in EPSG:3857
        centers = {
            "居住用地": get_xy(125.3350, 43.9030),
            "商业服务业": get_xy(125.3475, 43.9017),
            "商业办公": get_xy(125.3250, 43.9080),
            "公园与绿地": get_xy(125.3590, 43.9010),
            "公共设施": get_xy(125.3422, 43.9036)
        }

        # Precompute distance decay
        for cat, (c_x, c_y) in centers.items():
            dists = np.sqrt((cx_s - c_x)**2 + (cy_s - c_y)**2)
            max_d = dists.max() if dists.max() > 0 else 1.0
            gdf_proj[f"decay_{cat}"] = 1.0 - (dists / max_d)

        # Target areas (restrict to study area)
        if boundary is not None and not boundary.empty:
            boundary_proj = boundary.to_crs(epsg=3857)
            boundary_geom = boundary_proj.geometry.unary_union
            gdf_proj["in_study_area"] = gdf_proj.geometry.centroid.within(boundary_geom)
        else:
            gdf_proj["in_study_area"] = True

        gdf_in = gdf_proj[gdf_proj["in_study_area"]]
        total_area_in = gdf_in["area_sqm"].sum() if not gdf_in.empty else 0.0

        target_pcts = {
            "居住用地": res_pct,
            "商业服务业": com_pct,
            "商业办公": off_pct,
            "公园与绿地": green_pct,
            "公共设施": public_pct
        }
        target_areas = {k: total_area_in * (v / 100.0) for k, v in target_pcts.items()}

        # Scores
        scores = {}
        for cat in target_pcts:
            decay = gdf_proj[f"decay_{cat}"]
            if cat == "公共设施":
                is_orig = gdf_proj["Type"].isin(['医疗卫生', '教育科研', '体育文化', '行政办公'])
            else:
                is_orig = gdf_proj["Type"] == cat
            scores[cat] = is_orig.astype(float) * 2.0 + decay * 1.0

        # Allocation
        allocated = pd.Series(True, index=gdf_proj.index)
        allocated[gdf_proj["in_study_area"]] = False
        allocated_types = gdf_proj["Type"].copy()

        priority = ["商业服务业", "商业办公", "公园与绿地", "公共设施", "居住用地"]
        for cat in priority:
            target_a = target_areas[cat]
            cat_scores = scores[cat].copy()
            cat_scores[allocated] = -999.0
            sorted_idx = cat_scores.sort_values(ascending=False).index

            current_a = 0.0
            for idx in sorted_idx:
                if allocated[idx]:
                    continue
                p_area = gdf_proj.loc[idx, "area_sqm"]
                allocated_types.loc[idx] = cat
                allocated[idx] = True
                current_a += p_area
                if current_a >= target_a:
                    break

        # Set all remaining unallocated features inside the study area to "交通场站"
        unallocated_in = (~allocated) & gdf_proj["in_study_area"]
        allocated_types[unallocated_in] = "交通场站"

        # 3. Plot allocated landuse
        color_map = {
            "居住用地": "#FDE047",       # Yellow
            "商业服务业": "#EF4444",     # Red
            "商业办公": "#C084FC",       # Purple
            "公园与绿地": "#22C55E",     # Green
            "公共设施": "#F87171",       # Light Red
            "医疗卫生": "#F87171",
            "教育科研": "#F87171",
            "体育文化": "#F87171",
            "行政办公": "#F87171",
            "交通场站": "#94A3B8",       # Grey
            "工业用地": "#64748B"        # Dark Grey
        }

        gdf_proj["allocated_color"] = allocated_types.map(color_map).fillna("#CBD5E1")
        
        # Plot study area and context separately for consistent visual contrast
        gdf_out = gdf_proj[~gdf_proj["in_study_area"]]
        if not gdf_out.empty:
            for color_hex, sub_df in gdf_out.groupby('allocated_color'):
                sub_df.plot(ax=ax, facecolor=color_hex, edgecolor="#E2E8F0", linewidth=0.15, alpha=0.35, zorder=1)

        if not gdf_in.empty:
            gdf_in_proj = gdf_proj[gdf_proj["in_study_area"]]
            for color_hex, sub_df in gdf_in_proj.groupby('allocated_color'):
                sub_df.plot(ax=ax, facecolor=color_hex, edgecolor="#CBD5E1", linewidth=0.25, alpha=1.0, zorder=1)

    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax, facecolor="none", edgecolor="#475569", linewidth=0.15, alpha=0.3, zorder=2)
    if water is not None and not water.empty:
        water.plot(ax=ax, facecolor="#D0E6F7", edgecolor="none", zorder=2.5)
    if roads is not None and not roads.empty:
        roads.plot(ax=ax, color="#E2E8F0", linewidth=0.8, alpha=0.8, zorder=3)
    if rails is not None and not rails.empty:
        rails.plot(ax=ax, color="#64748B", linewidth=1.0, linestyle=(0, (5, 5)), zorder=4)

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("规划居住用地 (R)", "rect_plan_yellow"),
    ("规划商业办公 (B)", "rect_purple_fill"),
    ("规划商业服务 (B)", "rect_plan_red"),
    ("现状工业遗存 (M)", "rect_style_blue"),
    ("交通场站 (S)", "rect_euluc_4"),
    ("规划公共设施 (A)", "rect_plan_green"),
    ("规划公园绿地 (G)", "rect_green_planned")
]

description_lines = [
    "1. 策略优化：贯彻“降密度、补绿地、提功能”的城市更新宏观目标，通过用地结构调整，将原占比过高的老旧居住用地（56.6%）调减约5%，释放存量空间活力。",
    "2. 结构重构：调增商业及商服商务用地约3%，重点布局在光复路轴线及青年双创社区；强制增加公园与绿地至15.5%以上，打通蓝绿渗透网络。",
    "3. 混合平衡：提倡混合用地开发（R/B/A），补足日间照料与幼托等公共设施（A），织补城市“功能赤字”，重塑全龄友好与可持续的社区活力基底。"
]
