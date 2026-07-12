import json
from importlib import import_module

import numpy as np
import pandas as pd
import pytest


def _engine():
    return import_module("src.engines.site_diagnostic_engine")


def _write_feature_collection(path, features):
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False),
        encoding="utf-8",
    )


def _polygon_feature(name, coordinates, plot_id="plot"):
    return {
        "type": "Feature",
        "properties": {"id": plot_id, "name": name},
        "geometry": {"type": "Polygon", "coordinates": [coordinates]},
    }


def _clear_cache_if_available(func):
    clear = getattr(func, "clear", None)
    if callable(clear):
        clear()


@pytest.fixture(autouse=True)
def _clear_plot_diagnostics_cache():
    engine = _engine()
    _clear_cache_if_available(engine.get_plot_diagnostics)
    yield
    _clear_cache_if_available(engine.get_plot_diagnostics)


def _patch_diagnostic_sources(monkeypatch, engine, plots_path, poi=None, spatial=None, nlp=None):
    from src.engines import spatial_engine

    monkeypatch.setitem(engine.SHP_FILES, "plots", plots_path)
    monkeypatch.setattr(spatial_engine, "get_merged_poi_data", lambda: poi if poi is not None else pd.DataFrame())
    monkeypatch.setattr(engine, "_load_spatial_merge", lambda: spatial if spatial is not None else pd.DataFrame())
    monkeypatch.setattr(engine, "_load_nlp_data", lambda: nlp if nlp is not None else pd.DataFrame())
    _clear_cache_if_available(engine.get_plot_diagnostics)


def test_plot_diagnostics_uses_dynamic_names_and_polygon_area(tmp_path, monkeypatch):
    engine = _engine()
    plots_path = tmp_path / "plots.geojson"
    _write_feature_collection(
        plots_path,
        [
            _polygon_feature(
                "门户更新单元",
                [
                    [0.0, 0.0],
                    [0.01, 0.0],
                    [0.01, 0.01],
                    [0.0, 0.01],
                    [0.0, 0.0],
                ],
                plot_id="portal",
            ),
            _polygon_feature(
                "社区修补单元",
                [
                    [0.02, 0.0],
                    [0.03, 0.0],
                    [0.03, 0.01],
                    [0.02, 0.01],
                    [0.02, 0.0],
                ],
                plot_id="community",
            ),
        ],
    )
    _patch_diagnostic_sources(monkeypatch, engine, plots_path)

    diagnostics = engine.get_plot_diagnostics()

    assert [plot["name"] for plot in diagnostics] == ["门户更新单元", "社区修补单元"]
    assert [plot["area_ha"] > 0 for plot in diagnostics] == [True, True]


def test_plot_diagnostics_filters_points_by_polygon_not_bbox(tmp_path, monkeypatch):
    engine = _engine()
    plots_path = tmp_path / "l-shape.geojson"
    _write_feature_collection(
        plots_path,
        [
            _polygon_feature(
                "L形更新单元",
                [
                    [0.0, 0.0],
                    [0.02, 0.0],
                    [0.02, 0.01],
                    [0.01, 0.01],
                    [0.01, 0.02],
                    [0.0, 0.02],
                    [0.0, 0.0],
                ],
                plot_id="l-shape",
            )
        ],
    )
    poi = pd.DataFrame(
        [
            {"Name": "inside", "Lng": 0.005, "Lat": 0.005},
            {"Name": "bbox-only", "Lng": 0.015, "Lat": 0.015},
        ]
    )
    spatial = pd.DataFrame(
        [
            {"Lng": 0.005, "Lat": 0.005, "GVI": 10, "SVF": 20, "Enclosure": 30, "Clutter": 40},
            {"Lng": 0.015, "Lat": 0.015, "GVI": 90, "SVF": 80, "Enclosure": 70, "Clutter": 60},
        ]
    )
    _patch_diagnostic_sources(monkeypatch, engine, plots_path, poi=poi, spatial=spatial)

    diagnostics = engine.get_plot_diagnostics()

    assert diagnostics[0]["poi_count"] == 1
    assert diagnostics[0]["gvi_mean"] == 10
    assert diagnostics[0]["svf_mean"] == 20
    assert diagnostics[0]["enclosure_mean"] == 30
    assert diagnostics[0]["clutter_mean"] == 40


def test_plot_diagnostics_missing_plots_path_returns_empty_list(tmp_path, monkeypatch):
    engine = _engine()
    _patch_diagnostic_sources(monkeypatch, engine, tmp_path / "missing.geojson")

    assert engine.get_plot_diagnostics() == []


def test_plot_diagnostics_uses_paired_plot_geometry_loader(tmp_path, monkeypatch):
    engine = _engine()
    from shapely.geometry import box
    from src.engines import spatial_engine
    from src.engines.key_plot_engine import KeyPlot, KeyPlotGeometry

    plots_path = tmp_path / "plots.geojson"
    plots_path.write_text("{}", encoding="utf-8")
    monkeypatch.setitem(engine.SHP_FILES, "plots", plots_path)
    monkeypatch.setattr(
        engine,
        "load_key_plot_geometries_from_geojson",
        lambda _: [KeyPlotGeometry(KeyPlot(index=1, plot_id="first", name="first", area_ha=1.0), box(0, 0, 1, 1))],
        raising=False,
    )
    monkeypatch.setattr(
        engine,
        "load_key_plots_from_geojson",
        lambda _: (_ for _ in ()).throw(AssertionError("old metadata loader called")),
        raising=False,
    )
    monkeypatch.setattr(
        engine,
        "_load_plot_geometries_wgs84",
        lambda _: (_ for _ in ()).throw(AssertionError("old geometry loader called")),
        raising=False,
    )
    monkeypatch.setattr(spatial_engine, "get_merged_poi_data", lambda: pd.DataFrame())
    monkeypatch.setattr(engine, "_load_spatial_merge", lambda: pd.DataFrame())
    monkeypatch.setattr(engine, "_load_nlp_data", lambda: pd.DataFrame())

    diagnostics = engine.get_plot_diagnostics()

    assert [plot["name"] for plot in diagnostics] == ["first"]


def test_plot_diagnostics_logs_poi_source_errors(tmp_path, monkeypatch, caplog):
    engine = _engine()
    from src.engines import spatial_engine

    plots_path = tmp_path / "plots.geojson"
    _write_feature_collection(
        plots_path,
        [
            _polygon_feature(
                "first",
                [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]],
                plot_id="first",
            )
        ],
    )
    monkeypatch.setitem(engine.SHP_FILES, "plots", plots_path)

    def raise_poi_error():
        raise RuntimeError("poi offline")

    monkeypatch.setattr(spatial_engine, "get_merged_poi_data", raise_poi_error)
    monkeypatch.setattr(engine, "_load_spatial_merge", lambda: pd.DataFrame())
    monkeypatch.setattr(engine, "_load_nlp_data", lambda: pd.DataFrame())

    with caplog.at_level("WARNING", logger="ultimateDESIGN"):
        diagnostics = engine.get_plot_diagnostics()

    assert diagnostics[0]["poi_count"] == 0
    assert "POI data unavailable for plot diagnostics" in caplog.text


def test_masked_mean_handles_mask_length_mismatch():
    engine = _engine()

    assert engine._masked_mean(np.array([1.0, 2.0]), np.array([True], dtype=bool)) == 0.0


def test_point_mask_handles_coordinate_length_mismatch():
    engine = _engine()
    from shapely.geometry import box

    mask = engine._point_mask_in_geometry((np.array([0.5, 0.75]), np.array([0.5])), box(0, 0, 1, 1))

    assert mask.dtype == bool
    assert not mask.any()
