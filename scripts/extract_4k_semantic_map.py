#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
4K Semantic Segmentation Map Extractor
======================================
Reads GIS vector data from project static/ and data/gis/ directories,
composites them into a high-resolution color-coded semantic map suitable
for upload to cloud-based AI image generation tools (Nano Banana 2 / GPT-4o).

Output:
  - output/semantic_map_A3.png   (4961×3508 px, A3 landscape @300dpi)
  - output/prompt_nanobana2.txt  (Prompt for Google AI Studio / Gemini)
  - output/prompt_gpt4o.txt      (Prompt for ChatGPT / GPT-4o)

Usage:
  python scripts/extract_4k_semantic_map.py [--dpi 300] [--style blocks|lines]
"""

import os
import sys
import argparse
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server/headless rendering
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection
from shapely.geometry import box

warnings.filterwarnings("ignore", category=UserWarning)

# ──────────────────────────────────────────────────────────────────────
# Project paths
# ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"
GIS_DIR = PROJECT_ROOT / "data" / "gis"
OUTPUT_DIR = PROJECT_ROOT / "output"

# ──────────────────────────────────────────────────────────────────────
# A3 Landscape @ 300 DPI  →  4961 × 3508 px
# ──────────────────────────────────────────────────────────────────────
A3_WIDTH_INCH = 16.54   # 420mm
A3_HEIGHT_INCH = 11.69  # 297mm
DEFAULT_DPI = 300

# ──────────────────────────────────────────────────────────────────────
# Layer definitions: (file_path, color, style, zorder, label, optional)
# ──────────────────────────────────────────────────────────────────────
LAYER_DEFS = {
    "boundary": {
        "file": GIS_DIR / "Boundary_Scope.geojson",
        "color": "#FF0000",
        "fill": False,
        "linewidth": 3.0,
        "linestyle": "-",
        "zorder": 100,
        "label": "研究范围红线",
        "optional": False,
    },
    "water": {
        "file": STATIC_DIR / "water.geojson",
        "color": "#4169E1",
        "fill": True,
        "edgecolor": "#2850B0",
        "linewidth": 0.3,
        "zorder": 30,
        "label": "水体",
        "optional": False,
    },
    "road": {
        "file": STATIC_DIR / "road_clipped.geojson",
        "color": "#000000",
        "fill": False,
        "linewidth": 0.8,
        "zorder": 50,
        "label": "道路网络",
        "optional": False,
    },
    "rail": {
        "file": STATIC_DIR / "rail_clipped.geojson",
        "color": "#000080",
        "fill": False,
        "linewidth": 1.2,
        "linestyle": "--",
        "zorder": 55,
        "label": "轨道交通",
        "optional": True,
    },
    "buildings": {
        "file": STATIC_DIR / "buildings.geojson",
        "color": "#C0C0C0",
        "fill": True,
        "edgecolor": "#A0A0A0",
        "linewidth": 0.1,
        "zorder": 40,
        "label": "建筑轮廓",
        "optional": False,
    },
    "landuse": {
        "file": GIS_DIR / "landuse_clipped.geojson",
        "color": None,  # Uses per-feature color from properties
        "fill": True,
        "linewidth": 0.2,
        "zorder": 20,
        "label": "土地利用",
        "optional": True,
        "color_field": "Color",
    },
    "key_plots": {
        "file": GIS_DIR / "Key_Plots_District.json",
        "color": "#FFA500",
        "fill": False,
        "linewidth": 2.0,
        "linestyle": "--",
        "zorder": 90,
        "label": "重点地块",
        "optional": True,
        "label_field": "name",
    },
    "protected_buildings": {
        "file": STATIC_DIR / "protected_buildings.geojson",
        "color": "#8B008B",
        "fill": True,
        "edgecolor": "#4B0082",
        "linewidth": 1.5,
        "zorder": 95,
        "label": "保护建筑(不可拆改)",
        "optional": False,
    },
}


def load_layer(layer_name: str, layer_def: dict, clip_bounds=None):
    """Load a GeoJSON layer, optionally clipping to bounds."""
    filepath = layer_def["file"]
    if not filepath.exists():
        if layer_def.get("optional", False):
            print(f"  [SKIP] {layer_name}: {filepath.name} not found (optional)")
            return None
        else:
            print(f"  [ERROR] {layer_name}: {filepath.name} NOT FOUND!")
            return None

    print(f"  [LOAD] {layer_name}: {filepath.name} ...", end=" ")
    try:
        gdf = gpd.read_file(filepath)
        # Ensure CRS is WGS84
        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4326")
        elif gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs("EPSG:4326")

        # Clip to boundary if provided
        if clip_bounds is not None and layer_name != "boundary":
            gdf = gpd.clip(gdf, clip_bounds)

        print(f"{len(gdf)} features")
        return gdf
    except Exception as e:
        print(f"ERROR: {e}")
        return None


def render_layer(ax, layer_name: str, layer_def: dict, gdf):
    """Render a single layer onto the matplotlib axis."""
    if gdf is None or gdf.empty:
        return

    color = layer_def.get("color")
    fill = layer_def.get("fill", False)
    lw = layer_def.get("linewidth", 0.5)
    ls = layer_def.get("linestyle", "-")
    zorder = layer_def.get("zorder", 10)
    ec = layer_def.get("edgecolor", color)
    color_field = layer_def.get("color_field")

    if fill:
        if color_field and color_field in gdf.columns:
            # Per-feature coloring (e.g., landuse)
            for _, row in gdf.iterrows():
                fc = row.get(color_field, "#CCCCCC")
                if fc is None or (isinstance(fc, float)):
                    fc = "#CCCCCC"
                try:
                    gpd.GeoSeries([row.geometry]).plot(
                        ax=ax, facecolor=fc, edgecolor=fc,
                        linewidth=lw, zorder=zorder, alpha=0.85
                    )
                except Exception:
                    pass
        else:
            gdf.plot(
                ax=ax, facecolor=color, edgecolor=ec,
                linewidth=lw, zorder=zorder, alpha=0.9
            )
    else:
        gdf.plot(
            ax=ax, facecolor="none", edgecolor=color,
            linewidth=lw, linestyle=ls, zorder=zorder
        )

    # Annotate key_plots with name labels
    label_field = layer_def.get("label_field")
    if label_field and label_field in gdf.columns:
        for _, row in gdf.iterrows():
            name = row.get(label_field, "")
            if name and row.geometry:
                centroid = row.geometry.centroid
                ax.annotate(
                    name,
                    xy=(centroid.x, centroid.y),
                    fontsize=4, fontweight="bold",
                    color="#FF6600",
                    ha="center", va="center",
                    zorder=zorder + 5,
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="#FFA500",
                              lw=0.5, alpha=0.8),
                )


def build_legend_patches(loaded_layers: dict):
    """Create legend patches for all loaded layers."""
    patches = []
    for name, (layer_def, gdf) in loaded_layers.items():
        if gdf is None:
            continue
        color = layer_def.get("color", "#999999")
        fill = layer_def.get("fill", False)
        label = layer_def.get("label", name)

        if name == "landuse":
            color = "#AABB55"  # Generic green for legend
        if fill:
            p = mpatches.Patch(facecolor=color, edgecolor="black",
                               linewidth=0.5, label=label)
        else:
            p = mpatches.Patch(facecolor="none", edgecolor=color,
                               linewidth=1.5, label=label,
                               linestyle=layer_def.get("linestyle", "-"))
        patches.append(p)
    return patches


def generate_prompts(output_dir: Path):
    """Generate optimized prompts for cloud AI tools."""

    nanobana_prompt = """You are a professional urban planning renderer. I am uploading a semantic segmentation map of an urban renewal area in Changchun, China.

Color coding:
- RED outlines (#FF0000) = Study area boundary (红线)
- BLACK lines (#000000) = Road network
- DARK BLUE dashed lines (#000080) = Rail/Metro lines
- BLUE filled areas (#4169E1) = Water bodies (rivers, lakes)
- GRAY filled areas (#C0C0C0) = Buildings footprints
- PURPLE filled areas (#8B008B) with thick indigo edge (#4B0082) = Protected heritage buildings (MUST NOT be demolished or altered)
- ORANGE dashed outlines (#FFA500) = Key renovation plots
- Colored blocks = Land use categories (yellow=residential, red=commercial, pink=education, green=parks)

Please generate a photorealistic bird's-eye view urban planning illustration based on this spatial layout. Requirements:
1. Strictly follow the spatial structure and boundaries in the uploaded map
2. Replace color blocks with realistic textures: green trees for parks, glass buildings for commercial, tile roofs for residential
3. The water bodies should have realistic blue reflections
4. Roads should have proper lane markings and sidewalks
5. Add subtle atmospheric haze and golden-hour lighting
6. Output at the highest possible resolution
7. Style: Professional planning competition rendering (规划竞赛效果图)
8. Do NOT change any spatial boundaries or road alignments
9. CRITICAL: Purple buildings are protected heritage architecture - they MUST remain exactly as shown, preserving their original form and position"""

    gpt4o_prompt = """请根据我上传的城乡规划语义色块图，生成一张专业的鸟瞰效果图。

图中颜色含义：
- 红色粗线 = 规划研究范围红线
- 黑色线条 = 道路网络
- 深蓝色虚线 = 轨道交通
- 蓝色色块 = 水体（河流、湖泊）
- 灰色色块 = 建筑轮廓
- 紫色色块(#8B008B)+靛蓝粗边(#4B0082) = 保护建筑(严禁拆改，必须原样保留)
- 橙色虚线 = 重点改造地块
- 其他彩色色块 = 用地性质（黄色=居住、红色=商业、粉色=教育、绿色=公园绿地）

要求：
1. 严格遵循色块图中的空间结构，不改变任何边界和道路走向
2. 将色块替换为写实材质：公园用绿树，商业用玻璃幕墙，居住用瓦屋顶
3. 水体要有真实的蓝色倒影
4. 道路要有车道线和人行道
5. 加入柔和的大气透视和黄金时段光照
6. 风格：城乡规划竞赛效果图
7. 输出最高画质
8. 重要：紫色建筑为保护建筑，必须严格保留其原始形态和位置，不得做任何修改"""

    prompt_path_1 = output_dir / "prompt_nanobana2.txt"
    prompt_path_1.write_text(nanobana_prompt.strip(), encoding="utf-8")
    prompt_path_2 = output_dir / "prompt_gpt4o.txt"
    prompt_path_2.write_text(gpt4o_prompt.strip(), encoding="utf-8")
    print(f"\n  Prompts saved to: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Extract 4K Semantic Map for Cloud AI Rendering")
    parser.add_argument("--dpi", type=int, default=DEFAULT_DPI, help="Output DPI (default: 300)")
    parser.add_argument("--no-landuse", action="store_true", help="Skip landuse layer")
    parser.add_argument("--no-buildings", action="store_true", help="Skip buildings layer (for faster testing)")
    parser.add_argument("--bg", default="white", help="Background color (default: white)")
    args = parser.parse_args()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  4K Semantic Map Extractor — A3 Landscape Edition")
    print("=" * 60)
    print(f"  Output: {OUTPUT_DIR}")
    print(f"  Size:   A3 Landscape ({A3_WIDTH_INCH}\" × {A3_HEIGHT_INCH}\")")
    print(f"  DPI:    {args.dpi}  →  {int(A3_WIDTH_INCH * args.dpi)} × {int(A3_HEIGHT_INCH * args.dpi)} px")
    print()

    # ── Step 1: Load boundary first to get clip extent ──────────────
    print("[1/4] Loading boundary...")
    boundary_def = LAYER_DEFS["boundary"]
    boundary_gdf = load_layer("boundary", boundary_def)
    if boundary_gdf is None or boundary_gdf.empty:
        print("FATAL: Boundary file is required!")
        sys.exit(1)

    # Compute bounding box with padding
    bounds = boundary_gdf.total_bounds  # (minx, miny, maxx, maxy)
    dx = (bounds[2] - bounds[0]) * 0.08  # 8% padding
    dy = (bounds[3] - bounds[1]) * 0.08
    padded_bounds = box(bounds[0] - dx, bounds[1] - dy,
                        bounds[2] + dx, bounds[3] + dy)

    print(f"  Extent: [{bounds[0]:.4f}, {bounds[1]:.4f}] → [{bounds[2]:.4f}, {bounds[3]:.4f}]")
    print()

    # ── Step 2: Load all layers ─────────────────────────────────────
    print("[2/4] Loading layers...")
    loaded_layers = {}
    loaded_layers["boundary"] = (boundary_def, boundary_gdf)

    for name, layer_def in LAYER_DEFS.items():
        if name == "boundary":
            continue
        if args.no_landuse and name == "landuse":
            print(f"  [SKIP] {name}: --no-landuse flag")
            continue
        if args.no_buildings and name == "buildings":
            print(f"  [SKIP] {name}: --no-buildings flag")
            continue

        gdf = load_layer(name, layer_def, clip_bounds=padded_bounds)
        loaded_layers[name] = (layer_def, gdf)

    print()

    # ── Step 3: Render the composite map ────────────────────────────
    print("[3/4] Rendering composite map...")
    fig, ax = plt.subplots(
        1, 1,
        figsize=(A3_WIDTH_INCH, A3_HEIGHT_INCH),
        dpi=args.dpi,
        facecolor=args.bg,
    )
    ax.set_facecolor(args.bg)

    # Render layers in zorder sequence
    sorted_layers = sorted(loaded_layers.items(),
                           key=lambda x: x[1][0].get("zorder", 10))
    for name, (layer_def, gdf) in sorted_layers:
        if gdf is not None:
            print(f"  Rendering: {name} (z={layer_def.get('zorder', 10)})...")
            render_layer(ax, name, layer_def, gdf)

    # Set extent to padded boundary
    ax.set_xlim(bounds[0] - dx, bounds[2] + dx)
    ax.set_ylim(bounds[1] - dy, bounds[3] + dy)

    # Remove axes decorations for clean output
    ax.set_axis_off()
    ax.set_aspect("equal")

    # Add legend
    legend_patches = build_legend_patches(loaded_layers)
    if legend_patches:
        legend = ax.legend(
            handles=legend_patches,
            loc="lower right",
            fontsize=6,
            frameon=True,
            fancybox=True,
            framealpha=0.9,
            edgecolor="#333333",
            title="图例 Legend",
            title_fontsize=7,
        )
        legend.get_frame().set_linewidth(0.8)

    # Add title
    ax.set_title(
        "长春市某片区城市更新 — 语义色块图\nUrban Renewal Semantic Segmentation Map",
        fontsize=10, fontweight="bold", pad=10,
        fontfamily="sans-serif",
    )

    # Save
    output_path = OUTPUT_DIR / "semantic_map_A3.png"
    plt.savefig(
        output_path,
        dpi=args.dpi,
        bbox_inches="tight",
        pad_inches=0.3,
        facecolor=args.bg,
        edgecolor="none",
    )
    plt.close(fig)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\n  [OK] Saved: {output_path}")
    print(f"  [SIZE] {int(A3_WIDTH_INCH * args.dpi)} x {int(A3_HEIGHT_INCH * args.dpi)} px")
    print(f"  [FILE] {file_size_mb:.1f} MB")
    print()

    # ── Step 4: Generate prompts ────────────────────────────────────
    print("[4/4] Generating cloud AI prompts...")
    generate_prompts(OUTPUT_DIR)
    print("  [OK] Prompts generated.")

    print()
    print("=" * 60)
    print("  ALL DONE!")
    print("=" * 60)
    print()
    print("  Next steps:")
    print("  1. Open output/semantic_map_A3.png and verify quality")
    print("  2. Go to https://aistudio.google.com or ChatGPT")
    print("  3. Upload the semantic map PNG")
    print("  4. Paste the prompt from output/prompt_nanobana2.txt or prompt_gpt4o.txt")
    print("  5. Generate and iterate!")
    print()


if __name__ == "__main__":
    main()
