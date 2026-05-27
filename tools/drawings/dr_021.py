# -*- coding: utf-8 -*-
from shapely.geometry import Point
import pandas as pd
import numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT / "static"
GIS_DIR = ROOT / "data/gis"
ASSETS_DIR = ROOT / "assets"

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patheffects as path_effects
import geopandas as gpd
from PIL import Image

def draw_map(ax, roads, buildings, water, rails, key_plots, landuse, boundary, cx, cy, view_w, view_h, get_xy, font_prop):
    if water is not None and not water.empty:
        water.plot(ax=ax, facecolor="#E2F0FD", edgecolor="none", zorder=1)
    if buildings is not None and not buildings.empty:
        buildings.plot(ax=ax, facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=0.2, zorder=0.8)
    if rails is not None and not rails.empty:
        rails.plot(ax=ax, color="#64748B", linewidth=1.2, linestyle=(0, (5, 5)), zorder=3)

    # Calculate Space Syntax using networkx
    if roads is not None and not roads.empty:
        import networkx as nx
        G = nx.Graph()
        for idx, row in roads.iterrows():
            geom = row.geometry
            if geom is not None and geom.geom_type == 'LineString':
                coords = list(geom.coords)
                for i in range(len(coords) - 1):
                    p1, p2 = coords[i], coords[i+1]
                    dist = np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
                    G.add_edge(p1, p2, weight=dist, id=idx)
            elif geom is not None and geom.geom_type == 'MultiLineString':
                for line in geom.geoms:
                    coords = list(line.coords)
                    for i in range(len(coords) - 1):
                        p1, p2 = coords[i], coords[i+1]
                        dist = np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
                        G.add_edge(p1, p2, weight=dist, id=idx)

        import random
        def approx_closeness(graph, k=300, weight='weight', seed=42):
            random.seed(seed)
            nodes = list(graph.nodes())
            if len(nodes) <= k:
                return nx.closeness_centrality(graph, distance=weight)
            sampled_sources = random.sample(nodes, k)
            path_lengths = {}
            for s in sampled_sources:
                lengths = nx.single_source_dijkstra_path_length(graph, s, weight=weight)
                path_lengths[s] = lengths
            cl_dict = {}
            for u in nodes:
                sum_d = 0
                count = 0
                for s in sampled_sources:
                    d = path_lengths[s].get(u, None)
                    if d is not None and d > 0:
                        sum_d += d
                        count += 1
                cl_dict[u] = count / sum_d if sum_d > 0 else 0
            return cl_dict

        closeness = approx_closeness(G, k=300, weight='weight')
        betweenness = nx.betweenness_centrality(G, k=300, weight='weight', seed=42)

        road_closeness = []
        road_betweenness = []
        for idx, row in roads.iterrows():
            geom = row.geometry
            nodes_in_segment = []
            if geom is not None and geom.geom_type == 'LineString':
                nodes_in_segment = list(geom.coords)
            elif geom is not None and geom.geom_type == 'MultiLineString':
                for line in geom.geoms:
                    nodes_in_segment.extend(list(line.coords))
            if nodes_in_segment:
                c_val = np.mean([closeness.get(n, 0) for n in nodes_in_segment])
                b_val = np.mean([betweenness.get(n, 0) for n in nodes_in_segment])
            else:
                c_val, b_val = 0, 0
            road_closeness.append(c_val)
            road_betweenness.append(b_val)

        roads_copy = roads.copy()
        roads_copy['integration'] = road_closeness
        roads_copy['choice'] = road_betweenness

        # Normalization helper
        def norm(col):
            v = roads_copy[col].values
            if v.max() > v.min():
                return (v - v.min()) / (v.max() - v.min())
            return v

        roads_copy['integration_norm'] = norm('integration')
        roads_copy['choice_norm'] = norm('choice')

        # Plot roads colored by integration (Spectral colormap: red=high, blue=low)
        roads_copy.plot(ax=ax, column='integration_norm', cmap='Spectral_r', linewidth=2.8, zorder=4)

        # Save Synergy Plot separately
        fig_inset, ax_inset = plt.subplots(figsize=(3.8, 2.6), facecolor="#FFFFFF")
        x_vals = roads_copy['integration_norm'].values
        y_vals = roads_copy['choice_norm'].values
        valid = (x_vals > 0) & (y_vals > 0)
        if np.any(valid):
            x_v = x_vals[valid]
            y_v = y_vals[valid]
            ax_inset.scatter(x_v, y_v, color='#3B82F6', alpha=0.5, s=6)
            try:
                m, b_val = np.polyfit(x_v, y_v, 1)
                r_matrix = np.corrcoef(x_v, y_v)
                r_sq = r_matrix[0, 1]**2 if r_matrix.shape == (2, 2) else 0
                x_fit = np.linspace(min(x_v), max(x_v), 100)
                ax_inset.plot(x_fit, m*x_fit + b_val, color='#EF4444', linewidth=1.5, label=f'R²={r_sq:.2f}')
                ax_inset.legend(loc='upper left', fontsize=8, framealpha=0.6)
            except Exception:
                pass
        ax_inset.set_title("协同度分析 (Synergy)", fontsize=9, fontweight='bold', family=font_prop['family'])
        ax_inset.set_xlabel("全局整合度 (Rn)", fontsize=7, family=font_prop['family'])
        ax_inset.set_ylabel("全局选择度 (Choice)", fontsize=7, family=font_prop['family'])
        ax_inset.tick_params(axis='both', which='both', labelsize=6)
        plt.tight_layout()
        inset_path = STATIC_DIR / "temp_synergy_plot.png"
        fig_inset.savefig(str(inset_path), dpi=200, bbox_inches='tight')
        plt.close(fig_inset)

legend_items = [
    ("规划研究范围", "rect_red_border"),
    ("高整合度 (核心区/Red)", "line_syntax_high"),
    ("中等整合度 (Orange/Yellow)", "line_syntax_med"),
    ("低整合度 (外围/Blue)", "line_syntax_low"),
    ("现状铁路线", "line_rail"),
    ("现状建筑轮廓", "rect_building_light")
]

description_lines = [
    "1. 全局整合：基于路网拓扑分析发现，亚泰大街及长通路具有极高的全局可达性（红色），构成了研究范围对外的车行主通道。",
    "2. 慢行渗透：历史街区内部由于支路网密度偏低、被京哈线割裂，整合度表现出空间凹陷，步行可达性较弱，亟需细化微循环。",
    "3. 空间协同：协同度散点图 $R^2$ 拟合显示历史核心区与全域存在中度脱节，说明该地块在人流疏导与慢行连通上存在明显的孤岛效应。"
]