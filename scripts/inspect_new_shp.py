import json
import sys
from pathlib import Path

def get_first(c):
    if isinstance(c[0], (int, float)):
        return c
    return get_first(c[0])

for fpath in ['data/gis/raw/road_network.json', 'data/gis/raw/rail_network.json']:
    print(f'--- {fpath} ---')
    if not Path(fpath).exists():
        print("FILE NOT FOUND")
        continue
    with open(fpath, encoding='utf-8') as f:
        data = json.load(f)
    features = data.get("features", [])
    print(f'Feature count: {len(features)}')
    if features:
        feat = features[0]
        print(f'Sample Geometry: {feat["geometry"]["type"]}')
        coords = feat["geometry"]["coordinates"]
        print(f'Sample Coord: {get_first(coords)}')
        print(f'Properties: {list(feat["properties"].keys())}')
        print(f'First properties: {feat["properties"]}')
