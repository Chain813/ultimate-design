"""Render bird's eye white model: study area centered, natural scale."""
import json
import math
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
os.chdir(str(project_root))
sys.path.insert(0, str(project_root))

import matplotlib

matplotlib.use('Agg')
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

# Find available CJK font on this system
cjk_font = None
for f in fm.fontManager.ttflist:
    if any(k in f.name for k in ['SimHei', 'YaHei', 'Heiti', 'SimSun', 'Songti', 'CJK', 'Noto Sans']):
        cjk_font = f.name
        break
if cjk_font:
    matplotlib.rcParams['font.sans-serif'] = [cjk_font, 'DejaVu Sans']
    matplotlib.rcParams['axes.unicode_minus'] = False
    print(f'CJK font: {cjk_font}')
else:
    print('WARNING: No CJK font found, Chinese text may render as boxes')
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
from shapely.geometry import Polygon as SPoly

# Load .env
env_path = project_root / '.env'
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

print('Loading data...')
with open('data/gis/Building_Footprints.geojson', 'r', encoding='utf-8') as f:
    bld_data = json.load(f)
with open('data/gis/Key_Plots_District.json', 'r', encoding='utf-8') as f:
    kp_data = json.load(f)
with open('data/gis/Boundary_Scope.geojson', 'r', encoding='utf-8') as f:
    bnd_data = json.load(f)

def extract_polygon(geom):
    try:
        if geom['type'] == 'Polygon':
            rings = geom.get('coordinates', [])
            if rings and rings[0]:
                return [(p[0], p[1]) for p in rings[0] if len(p) >= 2]
        elif geom['type'] == 'MultiPolygon':
            best = []
            for ring in geom.get('coordinates', []):
                if ring and ring[0]:
                    pts = [(p[0], p[1]) for p in ring[0] if len(p) >= 2]
                    if len(pts) > len(best):
                        best = pts
            return best
    except:
        pass
    return []

# Study area boundary
bnd_poly = extract_polygon(bnd_data['features'][0]['geometry'])
bnd_polygon = SPoly(bnd_poly)

# Coordinate center = boundary centroid
bnd_lngs = [p[0] for p in bnd_poly]
bnd_lats = [p[1] for p in bnd_poly]
cx, cy = np.mean(bnd_lngs), np.mean(bnd_lats)
cos_lat = math.cos(math.radians(cy))

def to_xy(lng, lat):
    return ((lng - cx) * 111320 * cos_lat, (lat - cy) * 111320)

# Compute frame bounds first (study area + 35% padding in projected coords)
bnd_xy = [to_xy(lng, lat) for lng, lat in bnd_poly]
bx_all = [p[0] for p in bnd_xy]
by_all = [p[1] for p in bnd_xy]
w, h = max(bx_all) - min(bx_all), max(by_all) - min(by_all)
pad = max(w, h) * 0.35
frame_xmin = min(bx_all) - pad
frame_xmax = max(bx_all) + pad
frame_ymin = min(by_all) - pad
frame_ymax = max(by_all) + pad

# Filter: inside boundary vs within frame (for context)
# Also build a shapely polygon for the frame for intersects check
frame_poly = SPoly([
    (frame_xmin, frame_ymin), (frame_xmax, frame_ymin),
    (frame_xmax, frame_ymax), (frame_xmin, frame_ymax),
])

print('Filtering buildings...')
buildings_inside = []
buildings_context = []
for feat in bld_data['features']:
    props = feat['properties']
    coords = extract_polygon(feat['geometry'])
    if not coords or len(coords) < 3:
        continue
    # Quick centroid check first
    cx_b = sum(p[0] for p in coords) / len(coords)
    cy_b = sum(p[1] for p in coords) / len(coords)
    in_frame = (frame_xmin <= to_xy(cx_b, cy_b)[0] <= frame_xmax and
                frame_ymin <= to_xy(cx_b, cy_b)[1] <= frame_ymax)
    if not in_frame:
        continue

    bld_spoly = SPoly(coords)
    if bld_spoly.intersects(bnd_polygon):
        buildings_inside.append((coords, max(1, int(props.get('Floor', 1))), props.get('is_historical', False)))
    else:
        buildings_context.append((coords, max(1, int(props.get('Floor', 1))), props.get('is_historical', False)))

print(f'Inside: {len(buildings_inside)}, Context: {len(buildings_context)}')

# Build patches — inside buildings bright, context dim
patches_inside, colors_inside = [], []
patches_ctx, colors_ctx = [], []

for coords, floors, is_hist in buildings_inside:
    xy = [to_xy(lng, lat) for lng, lat in coords]
    patches_inside.append(Polygon(xy, closed=True))
    if is_hist:         colors_inside.append('#FFE4C4')
    elif floors <= 1:   colors_inside.append('#F0ECE6')
    elif floors <= 2:   colors_inside.append('#E8E4DC')
    elif floors <= 3:   colors_inside.append('#DCD6CC')
    elif floors <= 5:   colors_inside.append('#CCC4B6')
    elif floors <= 8:   colors_inside.append('#B0A590')
    else:               colors_inside.append('#9B8E76')

for coords, floors, is_hist in buildings_context:
    xy = [to_xy(lng, lat) for lng, lat in coords]
    patches_ctx.append(Polygon(xy, closed=True))
    # Dim, uniform color for context
    colors_ctx.append('#5A5550')

# Key plots
plot_colors = ['#FF4444', '#FF8800', '#44AAFF', '#44FF44', '#FF44FF']
plots = []
for i, feat in enumerate(kp_data['features']):
    poly = extract_polygon(feat['geometry'])
    if poly:
        name = feat['properties'].get('name', '')
        xy = [to_xy(lng, lat) for lng, lat in poly]
        plots.append((xy, name, plot_colors[i % 5]))

# --- RENDER ---
print('Rendering...')
fig, ax = plt.subplots(figsize=(20, 16), dpi=120)
ax.set_aspect('equal')
ax.set_facecolor('#1A1D20')

# Context buildings (dim, below)
if patches_ctx:
    pc_ctx = PatchCollection(patches_ctx, facecolors=colors_ctx,
                             edgecolors='none', alpha=0.5)
    ax.add_collection(pc_ctx)

# Study area buildings (bright, on top)
pc_inside = PatchCollection(patches_inside, facecolors=colors_inside,
                            edgecolors='#333333', linewidths=0.15)
ax.add_collection(pc_inside)

# Boundary (bold red)
bnd_xy = [to_xy(lng, lat) for lng, lat in bnd_poly]
ax.add_patch(Polygon(bnd_xy, closed=True, fill=False, edgecolor='#FF3333', linewidth=3, zorder=10))

# Key plots
for xy, name, color in plots:
    ax.add_patch(Polygon(xy, closed=True, fill=False, edgecolor=color, linewidth=4, zorder=11))
    cx_p = np.mean([p[0] for p in xy])
    cy_p = np.mean([p[1] for p in xy])
    ax.annotate(name, (cx_p, cy_p), fontsize=10, color='white', ha='center', va='bottom',
                fontweight='bold', zorder=12,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#222222', alpha=0.85, edgecolor=color))

# Bounds: use pre-computed frame from filtering step
ax.set_xlim(frame_xmin, frame_xmax)
ax.set_ylim(frame_ymin, frame_ymax)

ax.set_title('White Model — Study Area Bird\'s Eye View\nBuilding Footprints Colored by Floor Count', fontsize=16, color='white', pad=20)
ax.set_xticks([])
ax.set_yticks([])

# Legend
legend_elements = [
    mpatches.Patch(color='#F0ECE6', label='1F'), mpatches.Patch(color='#E8E4DC', label='2F'),
    mpatches.Patch(color='#DCD6CC', label='3F'), mpatches.Patch(color='#CCC4B6', label='4-5F'),
    mpatches.Patch(color='#B0A590', label='6-8F'), mpatches.Patch(color='#9B8E76', label='9-12F'),
    mpatches.Patch(color='#887860', label='13+F'), mpatches.Patch(color='#FFE4C4', label='Historical'),
]
ax.legend(handles=legend_elements, loc='upper right', fontsize=8, ncol=2,
          facecolor='#222', edgecolor='#555', labelcolor='white')

# Stats
ax.text(0.02, 0.98,
        f'Study area: {len(buildings_inside):,} buildings\n'
        f'Context: {len(buildings_context):,} buildings',
        transform=ax.transAxes, fontsize=9, verticalalignment='top', fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='#1A1D20', edgecolor='#555', alpha=0.9), color='#AAA')

# Save
out_dir = Path('output/white_models')
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / 'birdseye_complete.png'
fig.savefig(str(out_path), dpi=150, bbox_inches='tight', facecolor='#1A1D20', edgecolor='none')
plt.close()
print(f'Saved: {out_path} ({out_path.stat().st_size/1024:.0f} KB)')
print('Done!')
