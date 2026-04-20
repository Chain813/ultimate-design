"""
GeoJSON 几何量化压缩脚本 (v2 - 容错增强版)
"""
import json
import os

src = "static/buildings.geojson"

print("Reading original file...")
with open(src, "r", encoding="utf-8") as f:
    data = json.load(f)

orig_size = os.path.getsize(src)
num_features = len(data["features"])
print(f"Original: {orig_size / 1024 / 1024:.1f} MB, {num_features} features")

def round_coords(coords, precision=5):
    if not coords:
        return coords
    if isinstance(coords[0], (list, tuple)):
        return [round_coords(c, precision) for c in coords]
    elif isinstance(coords[0], (int, float)):
        return [round(c, precision) for c in coords]
    return coords

cleaned = []
for feature in data["features"]:
    try:
        geom = feature.get("geometry")
        if not geom or not geom.get("coordinates"):
            continue
        geom["coordinates"] = round_coords(geom["coordinates"], 5)
        props = feature.get("properties", {})
        keep = {}
        for k in ("Floor", "Name", "name"):
            if k in props:
                keep[k] = props[k]
        feature["properties"] = keep
        cleaned.append(feature)
    except Exception:
        cleaned.append(feature)

data["features"] = cleaned

print("Writing compressed file...")
with open(src, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

new_size = os.path.getsize(src)
ratio = (1 - new_size / orig_size) * 100
print(f"Compressed: {new_size / 1024 / 1024:.1f} MB")
print(f"Reduction: {ratio:.1f}%")
print(f"Features preserved: {len(cleaned)}")
