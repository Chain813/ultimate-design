"""Clean, clip, and export key plot GIS boundaries."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Sequence
from uuid import uuid4

import geopandas as gpd
import pandas as pd
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.ops import unary_union


DEFAULT_CRS = "EPSG:4326"
OUTPUT_CRS = "EPSG:4326"

logger = logging.getLogger("ultimateDESIGN")


def process_key_plots(input_path: str | Path, boundary_path: str | Path, output_path: str | Path) -> int:
    """Process raw key plot polygons into clipped WGS84 GeoJSON features."""
    plots = _read_layer(input_path)
    boundary = _read_layer(boundary_path)

    plots = _clean_geometries(plots)
    boundary = _clean_geometries(boundary)

    if plots.empty:
        _write_geojson(plots, output_path)
        return 0

    processed = _clip_to_boundary(plots, boundary)
    processed = _add_output_fields(processed)
    processed = processed.to_crs(OUTPUT_CRS)

    _write_geojson(processed, output_path)
    return len(processed)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clean, clip, index, and export key plot polygons.")
    parser.add_argument("--input", required=True, help="Raw key plots GeoJSON/Shapefile path")
    parser.add_argument("--boundary", required=True, help="Research boundary GeoJSON/Shapefile path")
    parser.add_argument("--output", required=True, help="Output WGS84 GeoJSON path")
    args = parser.parse_args(argv)

    count = process_key_plots(args.input, args.boundary, args.output)
    print(f"Processed {count} key plot feature(s) to {args.output}")
    return 0


def _read_layer(path: str | Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs(DEFAULT_CRS, allow_override=True)
    return gdf


def _clean_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.empty:
        return gdf.copy()

    cleaned = gdf[gdf.geometry.apply(lambda geometry: geometry is not None)].copy()
    if cleaned.empty:
        return cleaned

    try:
        if hasattr(cleaned.geometry, "make_valid"):
            cleaned = cleaned.set_geometry(cleaned.geometry.make_valid())
        else:
            from shapely.validation import make_valid

            cleaned = cleaned.set_geometry(cleaned.geometry.apply(make_valid))
    except Exception:
        cleaned = cleaned.set_geometry(cleaned.geometry.buffer(0))

    cleaned = cleaned.set_geometry(cleaned.geometry.apply(_polygonal_geometry))
    cleaned = cleaned[cleaned.geometry.apply(lambda geometry: geometry is not None and not geometry.is_empty)].copy()
    return cleaned.reset_index(drop=True)


def _polygonal_geometry(geometry):
    if geometry is None or geometry.is_empty:
        return GeometryCollection()
    if isinstance(geometry, (Polygon, MultiPolygon)):
        return geometry
    if geometry.geom_type == "GeometryCollection":
        parts = [part for part in geometry.geoms if isinstance(part, (Polygon, MultiPolygon)) and not part.is_empty]
        return unary_union(parts) if parts else GeometryCollection()
    return GeometryCollection()


def _clip_to_boundary(plots: gpd.GeoDataFrame, boundary: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if boundary.empty:
        return plots.iloc[0:0].copy()

    if boundary.crs != plots.crs:
        boundary = boundary.to_crs(plots.crs)

    boundary_union = _union_geometry(boundary)
    clipped = plots.copy()
    clipped = clipped.set_geometry(clipped.geometry.intersection(boundary_union))
    clipped = _clean_geometries(clipped)

    return clipped


def _union_geometry(gdf: gpd.GeoDataFrame):
    if hasattr(gdf.geometry, "union_all"):
        return gdf.geometry.union_all()
    return gdf.geometry.unary_union


def _add_output_fields(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    output = gdf.copy().reset_index(drop=True)
    areas_ha = _calculate_areas_ha(output)

    plot_indexes = []
    names = []
    roles = []
    for index, (_, row) in enumerate(output.iterrows(), start=1):
        plot_indexes.append(index)
        names.append(_first_value(row, ("name", "Name", "plot_name", "PlotName", "地块名称")) or f"地块{index}")
        roles.append(_first_value(row, ("role", "type", "category", "功能")) or "")

    output["plot_index"] = plot_indexes
    output["name"] = names
    output["role"] = roles
    source_ids = [_first_value(row, ("id",)) or index for index, (_, row) in enumerate(output.iterrows(), start=1)]
    source_objectids = [
        _first_value(row, ("OBJECTID",)) or index for index, (_, row) in enumerate(output.iterrows(), start=1)
    ]
    area_values = [round(float(area), 4) for area in areas_ha]
    output["id"] = source_ids
    output["OBJECTID"] = source_objectids
    output["area_ha"] = area_values
    output["Shape_Area"] = [area * 10000.0 for area in area_values]
    return output


def _calculate_areas_ha(gdf: gpd.GeoDataFrame) -> list[float]:
    if gdf.empty:
        return []

    target_crs = _estimated_utm_crs(gdf)
    if target_crs is not None:
        try:
            projected = gdf.to_crs(target_crs)
            return (projected.geometry.area / 10000.0).tolist()
        except Exception:
            logger.warning("Estimated UTM area calculation failed; falling back to geodesic area", exc_info=True)
    else:
        logger.warning("Estimated UTM CRS unavailable; falling back to geodesic area")

    return _calculate_geodesic_areas_ha(gdf)


def _calculate_geodesic_areas_ha(gdf: gpd.GeoDataFrame) -> list[float]:
    from pyproj import Geod

    geod = Geod(ellps="WGS84")
    wgs84 = _to_wgs84(gdf)
    areas_ha = []
    for geometry in wgs84.geometry:
        area_m2, _ = geod.geometry_area_perimeter(geometry)
        areas_ha.append(abs(float(area_m2)) / 10000.0)
    return areas_ha


def _estimated_utm_crs(gdf: gpd.GeoDataFrame):
    try:
        return gdf.estimate_utm_crs()
    except Exception:
        logger.warning("Estimated UTM CRS lookup failed; falling back to geodesic area", exc_info=True)
        return None


def _to_wgs84(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        return gdf.set_crs(DEFAULT_CRS, allow_override=True)

    try:
        epsg = gdf.crs.to_epsg()
    except Exception:
        epsg = None

    if epsg == 4326:
        return gdf
    return gdf.to_crs(OUTPUT_CRS)


def _first_value(row: pd.Series, keys: tuple[str, ...]):
    for key in keys:
        if key in row and _has_value(row[key]):
            return row[key]
    return None


def _has_value(value) -> bool:
    if value is None:
        return False
    if isinstance(value, float) and pd.isna(value):
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def _write_geojson(gdf: gpd.GeoDataFrame, output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(f".{output.stem}.{uuid4().hex}{output.suffix or '.geojson'}")

    try:
        if gdf.empty:
            temp.write_text('{"type": "FeatureCollection", "features": []}\n', encoding="utf-8")
        else:
            gdf.to_file(temp, driver="GeoJSON", index=False)

        temp.replace(output)
    except Exception:
        if temp.exists():
            temp.unlink()
        raise


if __name__ == "__main__":
    raise SystemExit(main())
