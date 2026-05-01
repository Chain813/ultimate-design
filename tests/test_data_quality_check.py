import pandas as pd

from tools.data_quality_check import _count_poi_for_geometry


def test_count_poi_for_geometry_uses_polygon_not_bbox():
    geometry = {
        "type": "Polygon",
        "coordinates": [[(0, 0), (1, 0), (0, 1), (0, 0)]],
    }
    bbox = {"min_lng": 0, "max_lng": 1, "min_lat": 0, "max_lat": 1}
    df_poi = pd.DataFrame(
        [
            {"Lng": 0.1, "Lat": 0.1},
            {"Lng": 0.9, "Lat": 0.9},
        ]
    )

    count, method = _count_poi_for_geometry(df_poi, geometry, bbox)

    assert count == 1
    assert method == "polygon"
