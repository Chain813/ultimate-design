from src.utils.geo_transform import bd09_to_gcj02, bd09_to_wgs84


def test_bd09_to_gcj02_returns_float_pair():
    lng, lat = bd09_to_gcj02(125.3517, 43.9116)
    assert isinstance(lng, float)
    assert isinstance(lat, float)


def test_bd09_to_wgs84_value_range():
    lng, lat = bd09_to_wgs84(125.3517, 43.9116)
    assert 120.0 < lng < 130.0
    assert 40.0 < lat < 50.0
