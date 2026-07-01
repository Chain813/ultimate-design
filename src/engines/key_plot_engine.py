"""Canonical key-plot metadata and GIS loading helpers."""

from __future__ import annotations

import json
import logging
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from src.config import GIS_FILES, resolve_path

logger = logging.getLogger("ultimateDESIGN")


class KeyPlotLoadError(Exception):
    """Raised when a configured key-plot GIS file exists but cannot be loaded."""


KEY_PLOT_DRAWING_SUFFIXES = [
    "现状问题图",
    "更新定位图",
    "平面深化图",
    "AIGC推演效果图",
    "人视效果图",
    "建筑更新图",
    "街道断面图",
    "改造前后对比图",
    "运营场景图",
]


@dataclass(frozen=True)
class KeyPlot:
    index: int
    plot_id: str
    name: str
    role: str = ""
    area_ha: float = 0.0
    centroid: tuple[float, float] | None = None


def normalize_key_plot_name(name: str) -> str:
    """Normalize numbered plot drawing names to the canonical key-plot label."""
    return re.sub(r"地块\d+", "重点地块", name)


def build_key_plot_drawing_names(plots: Iterable[KeyPlot]) -> list[str]:
    """Expand configured key plots into the canonical per-plot drawing names."""
    return [f"地块{plot.index}{suffix}" for plot in plots for suffix in KEY_PLOT_DRAWING_SUFFIXES]


def format_key_plot_context(plots: Iterable[KeyPlot]) -> str:
    """Format key-plot metadata for prompt/context injection."""
    plot_list = list(plots)
    if not plot_list:
        return "重点更新单元尚未配置；生成地块深化图纸前，请先上传或配置地块边界。"

    lines = [f"共 {len(plot_list)} 个重点更新单元："]
    for plot in plot_list:
        details = []
        if plot.role:
            details.append(f"功能角色：{plot.role}")
        if plot.area_ha:
            details.append(f"面积：{plot.area_ha:.2f} ha")

        line = f"地块{plot.index}：{plot.name}"
        if details:
            line = f"{line}（{'，'.join(details)}）"
        lines.append(f"- {line}")
    return "\n".join(lines)


def load_key_plots_from_geojson(path: str | Path) -> list[KeyPlot]:
    """Load configured key plots from a GeoJSON-compatible file."""
    resolved = resolve_path(str(path))
    if not resolved.exists():
        return []

    try:
        gdf = _read_geojson(resolved)
        original_feature_count = int(gdf.attrs.get("key_plot_feature_count", len(gdf)))
        if gdf.empty:
            if original_feature_count == 0:
                return []
            raise KeyPlotLoadError(
                f"Key plot GeoJSON has {original_feature_count} features but 0 usable geometries"
            )

        gdf = _prepare_geometries(gdf)
        if original_feature_count > 0 and len(gdf) != original_feature_count:
            raise KeyPlotLoadError(
                "Key plot GeoJSON geometry cleanup changed feature count: "
                f"original={original_feature_count}, valid={len(gdf)}"
            )
        if gdf.empty:
            return []

        areas_ha = _calculate_areas_ha(gdf)
        centroids = _centroids_wgs84(gdf)

        plots = []
        for position, (_, row) in enumerate(gdf.iterrows(), start=1):
            plot_id = _first_value(row, ("id", "OBJECTID", "index")) or str(position)
            name = _first_value(row, ("name", "Name", "plot_name", "PlotName", "地块名称")) or f"地块{position}"
            role = _first_value(row, ("role", "type", "category")) or ""
            centroid = centroids[position - 1]

            plots.append(
                KeyPlot(
                    index=position,
                    plot_id=str(plot_id),
                    name=str(name),
                    role=str(role),
                    area_ha=round(float(areas_ha[position - 1]), 2),
                    centroid=centroid,
                )
            )
        return plots
    except KeyPlotLoadError:
        raise
    except Exception as exc:
        raise KeyPlotLoadError(f"Failed to load key plots from {resolved}") from exc


def get_configured_key_plots() -> list[KeyPlot]:
    """Load key plots from the configured GIS plot file."""
    return load_key_plots_from_geojson(resolve_path(str(GIS_FILES["plots"])))


def plot_names(plots: Iterable[KeyPlot]) -> list[str]:
    return [plot.name for plot in plots]


def _read_geojson(path: Path):
    try:
        import geopandas as gpd
    except ImportError as exc:
        raise KeyPlotLoadError("GeoPandas is required to load key plot GIS files") from exc

    data = _load_geojson_document(path)
    original_feature_count = len(data["features"])

    try:
        gdf = gpd.read_file(str(path))
        feature_ids = _feature_ids(data)
        if "id" not in gdf.columns and len(feature_ids) == len(gdf) and any(_has_value(value) for value in feature_ids):
            gdf.insert(0, "id", feature_ids)
        gdf.attrs["key_plot_feature_count"] = original_feature_count
        return gdf
    except Exception:
        try:
            gdf = _read_geojson_fallback(data, gpd)
            gdf.attrs["key_plot_feature_count"] = original_feature_count
            return gdf
        except Exception as exc:
            raise KeyPlotLoadError(f"Could not parse key plot GeoJSON at {path}") from exc


def _load_geojson_document(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception as exc:
        raise KeyPlotLoadError(f"Could not read key plot GeoJSON at {path}") from exc

    if not isinstance(data, dict):
        raise KeyPlotLoadError(f"Key plot GeoJSON at {path} must be a FeatureCollection object")
    if data.get("type") != "FeatureCollection":
        raise KeyPlotLoadError(f"Key plot GeoJSON at {path} must be a FeatureCollection")
    if "features" not in data:
        raise KeyPlotLoadError(f"Key plot GeoJSON at {path} is missing features")
    if not isinstance(data["features"], list):
        raise KeyPlotLoadError(f"Key plot GeoJSON at {path} features must be a list")
    _validate_feature_geometries(data["features"], str(path))
    return data


def _validate_feature_geometries(features: list, source: str) -> None:
    from shapely.geometry import shape

    for position, feature in enumerate(features, start=1):
        if not isinstance(feature, dict):
            raise KeyPlotLoadError(f"Key plot GeoJSON feature {position} in {source} must be an object")
        if "geometry" not in feature or feature["geometry"] is None:
            raise KeyPlotLoadError(f"Key plot GeoJSON feature {position} in {source} has missing geometry")

        try:
            geometry = shape(feature["geometry"])
        except Exception as exc:
            raise KeyPlotLoadError(f"Key plot GeoJSON feature {position} in {source} has invalid geometry") from exc

        if geometry.is_empty:
            raise KeyPlotLoadError(f"Key plot GeoJSON feature {position} in {source} has empty geometry")


def _read_geojson_fallback(data: dict, gpd):
    from shapely.geometry import shape

    records = []
    geometries = []
    for feature in data.get("features", []):
        if not isinstance(feature, dict):
            raise KeyPlotLoadError("Key plot GeoJSON features must be objects")

        geometry_data = feature.get("geometry")
        if geometry_data is None:
            raise KeyPlotLoadError("Key plot GeoJSON feature has missing geometry")

        properties = dict(feature.get("properties") or {})
        if "id" not in properties and _has_value(feature.get("id")):
            properties["id"] = feature.get("id")
        geometry = shape(geometry_data)
        if geometry.is_empty:
            raise KeyPlotLoadError("Key plot GeoJSON feature has empty geometry")
        records.append(properties)
        geometries.append(geometry)

    crs = _geojson_crs(data)
    return gpd.GeoDataFrame(records, geometry=geometries, crs=crs)


def _feature_ids(data: dict) -> list:
    return [feature.get("id") if isinstance(feature, dict) else None for feature in data["features"]]


def _geojson_crs(data: dict) -> str | None:
    crs = data.get("crs")
    if not isinstance(crs, dict):
        return None
    properties = crs.get("properties") or {}
    name = properties.get("name")
    return name if isinstance(name, str) else None


def _prepare_geometries(gdf):
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326", allow_override=True)

    gdf = gdf[gdf.geometry.notna()].copy()
    if gdf.empty:
        return gdf

    try:
        if hasattr(gdf.geometry, "make_valid"):
            gdf = gdf.set_geometry(gdf.geometry.make_valid())
        else:
            from shapely.validation import make_valid

            gdf = gdf.set_geometry(gdf.geometry.apply(make_valid))
    except Exception:
        gdf = gdf.set_geometry(gdf.geometry.buffer(0))

    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    return gdf.reset_index(drop=True)


def _calculate_areas_ha(gdf) -> list[float]:
    target_crs = _estimated_utm_crs(gdf)
    if target_crs is not None:
        try:
            projected = gdf.to_crs(target_crs)
            return (projected.geometry.area / 10000.0).tolist()
        except Exception:
            logger.warning("Estimated UTM area calculation failed; falling back to geodesic area", exc_info=True)

    return _calculate_geodesic_areas_ha(gdf)


def _calculate_geodesic_areas_ha(gdf) -> list[float]:
    from pyproj import Geod

    geod = Geod(ellps="WGS84")
    wgs84 = _to_wgs84(gdf)
    areas_ha = []
    for geometry in wgs84.geometry:
        area_m2, _ = geod.geometry_area_perimeter(geometry)
        areas_ha.append(abs(float(area_m2)) / 10000.0)
    return areas_ha


def _estimated_utm_crs(gdf):
    try:
        return gdf.estimate_utm_crs()
    except Exception:
        return None


def _to_wgs84(gdf):
    if gdf.crs is None:
        return gdf.set_crs("EPSG:4326", allow_override=True)

    try:
        epsg = gdf.crs.to_epsg()
    except Exception:
        epsg = None

    if epsg == 4326:
        return gdf
    return gdf.to_crs("EPSG:4326")


def _centroids_wgs84(gdf) -> list[tuple[float, float]]:
    target_crs = _estimated_utm_crs(gdf)
    if target_crs is not None:
        try:
            projected = gdf.to_crs(target_crs)
            centroid_series = projected.geometry.centroid
            centroids = projected.set_geometry(centroid_series).to_crs("EPSG:4326").geometry
            return [(round(point.x, 6), round(point.y, 6)) for point in centroids]
        except Exception:
            logger.warning("Projected centroid calculation failed; falling back to WGS84 centroid", exc_info=True)

    wgs84 = _to_wgs84(gdf)
    centroids = [geometry.centroid for geometry in wgs84.geometry]
    return [(round(point.x, 6), round(point.y, 6)) for point in centroids]


def _first_value(row, keys: tuple[str, ...]):
    for key in keys:
        if key in row and _has_value(row[key]):
            return row[key]
    return None


def _has_value(value) -> bool:
    if value is None:
        return False
    if isinstance(value, float) and math.isnan(value):
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True
