import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

import geopandas as gpd
from tools.drawings.dr_parcel_detail import parse_drawing_type, PARCEL_INFO, ANALYSIS_INFO

# Test parser
test_cases = [
    "老水产市场-现状卫星图",
    "老水产市场-现状土地利用",
    "老水产市场-现状肌理",
    "老水产市场-现状建筑高度",
    "老水产市场-现状业态分区",
    "食品调料市场-现状卫星图",
    "食品调料市场-现状土地利用",
    "食品调料市场-现状肌理",
    "食品调料市场-现状建筑高度",
    "食品调料市场-现状业态分区",
    "市一中北侧-现状卫星图",
    "市一中北侧-现状土地利用",
    "市一中北侧-现状肌理",
    "市一中北侧-现状建筑高度",
    "市一中北侧-现状业态分区",
    "清禾集贸市场-现状卫星图",
    "清禾集贸市场-现状土地利用",
    "清禾集贸市场-现状肌理",
    "清禾集贸市场-现状建筑高度",
    "清禾集贸市场-现状业态分区",
    "中国石油-现状卫星图",
    "中国石油-现状土地利用",
    "中国石油-现状肌理",
    "中国石油-现状建筑高度",
    "中国石油-现状业态分区",
]

key_plots = gpd.read_file(ROOT / 'data/gis/Key_Plots_District.json').to_crs(epsg=3857)

print("Parsed parameters:")
for tc in test_cases:
    p_idx, a_type = parse_drawing_type(tc)
    p_info = PARCEL_INFO[p_idx]
    a_info = ANALYSIS_INFO[a_type]
    
    # Recalculate local view bounds
    curr_row = key_plots.iloc[p_idx]
    p_minx, p_miny, p_maxx, p_maxy = curr_row.geometry.bounds
    cx = (p_minx + p_maxx) / 2
    cy = (p_miny + p_maxy) / 2
    local_w = p_maxx - p_minx
    local_h = p_maxy - p_miny
    
    padding_factor = 2.2
    view_h = local_h * padding_factor
    view_w = view_h * 1.2454
    if view_w < local_w * 1.3:
        view_w = local_w * 1.3
        view_h = view_w / 1.2454
        
    print(f"Drawing: {tc}")
    print(f"  Parsed p_idx: {p_idx} ({p_info['name']}), a_type: {a_type}")
    print(f"  Recalculated: cx={cx:.2f}, cy={cy:.2f}, w={view_w:.2f}, h={view_h:.2f}")
