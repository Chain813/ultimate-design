import json
import os
import sys

def compress_geojson(input_path, output_path, precision=6):
    print(f"Compressing {input_path}...")
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. Coordinate Rounding
    def round_coords(obj):
        if isinstance(obj, list):
            if len(obj) == 2 and isinstance(obj[0], (int, float)):
                return [round(obj[0], precision), round(obj[1], precision)]
            return [round_coords(x) for x in obj]
        return obj

    # 2. Feature Filtering
    compressed_features = []
    for feature in data.get('features', []):
        # Keep only essential attributes
        props = feature.get('properties', {})
        new_props = {}
        
        # Whitelist of essential fields
        keep_fields = ['Class', 'is_historical', 'prop_style', 'hist_name', 'hist_batch', 'Floor', 'Name', 'name']
        for field in keep_fields:
            if field in props:
                new_props[field] = props[field]
        
        feature['properties'] = new_props
        feature['geometry']['coordinates'] = round_coords(feature['geometry'].get('coordinates', []))
        compressed_features.append(feature)

    data['features'] = compressed_features

    # 3. Save with minimal whitespace
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'))

    orig_size = os.path.getsize(input_path) / (1024 * 1024)
    new_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Compression Complete!")
    print(f"   Original: {orig_size:.2f} MB")
    print(f"   Now: {new_size:.2f} MB")
    print(f"   Reduction: {((orig_size - new_size) / orig_size) * 100:.1f}%")

if __name__ == "__main__":
    # Compress both main data files
    compress_geojson("static/landuse.geojson", "static/landuse.geojson")
    compress_geojson("static/buildings.geojson", "static/buildings.geojson")
