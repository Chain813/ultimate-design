"""
Vector Exporter for UltimateDESIGN (Inspired by ezdxf & AutoCAD 2000 AC1015 standard).
Exports GeoDataFrames to AutoCAD DXF format (.dxf) with:
- Standard AutoCAD 2000 (AC1015) header with ANSI_936 code page (anti-mojibake)
- National standard GB/T urban planning CAD layer conventions:
    01_BOUNDARY       (规划红线, Red, RGB 255,0,0, ACI 1)
    02_EXISTING_BLDG   (保留建筑, Light Gray, RGB 200,200,200, ACI 8)
    03_PROPOSED_BLDG   (更新建筑, Yellow/Gold, RGB 255,215,0, ACI 2)
    04_ROAD_CENTER     (道路拓扑中心线, Blue, RGB 30,144,255, ACI 5)
    05_GREEN_SPACE     (公园绿地, Green, RGB 34,139,34, ACI 3)
- TABLES section with layer definitions, ACI colors, and 24-bit TrueColor (Group Code 420)
- Recursive geometry expansion supporting MultiPolygon and MultiLineString
- Strict sanitization of TEXT/MTEXT strings (stripping \\r and \\n) to preserve group-code pairing
"""

import logging
import os
import zipfile
from typing import Any, Dict, List, Optional, Tuple, Union

import geopandas as gpd
from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)

logger = logging.getLogger(__name__)

# Standard National Urban Planning CAD Layers (GB/T 城乡规划制图标准规范图层)
STANDARD_GB_LAYERS: Dict[str, Dict[str, Any]] = {
    "01_BOUNDARY": {
        "name": "01_BOUNDARY",
        "desc": "规划红线",
        "rgb": (255, 0, 0),         # Red
        "aci": 1,                   # AutoCAD Color Index 1 = Red
    },
    "02_EXISTING_BLDG": {
        "name": "02_EXISTING_BLDG",
        "desc": "保留建筑",
        "rgb": (200, 200, 200),     # Light Gray
        "aci": 8,                   # AutoCAD Color Index 8 = Dark Gray / 7 = White
    },
    "03_PROPOSED_BLDG": {
        "name": "03_PROPOSED_BLDG",
        "desc": "更新建筑",
        "rgb": (255, 215, 0),       # Yellow / Gold
        "aci": 2,                   # AutoCAD Color Index 2 = Yellow
    },
    "04_ROAD_CENTER": {
        "name": "04_ROAD_CENTER",
        "desc": "道路拓扑中心线",
        "rgb": (30, 144, 255),       # Dodger Blue
        "aci": 5,                   # AutoCAD Color Index 5 = Blue
    },
    "05_GREEN_SPACE": {
        "name": "05_GREEN_SPACE",
        "desc": "公园绿地",
        "rgb": (34, 139, 34),       # Forest Green
        "aci": 3,                   # AutoCAD Color Index 3 = Green
    },
}

# Mapping common layer keys / keywords to standard GB layers
LAYER_KEYWORD_MAPPING: List[Tuple[List[str], str]] = [
    (["01", "BOUNDARY", "REDLINE", "SCOPE", "红线", "范围", "边界"], "01_BOUNDARY"),
    (["03", "PROPOSED", "NEW_BLDG", "UPDATE_BLDG", "RENEWAL", "更新建筑", "新建建筑", "改造建筑"], "03_PROPOSED_BLDG"),
    (["02", "EXISTING", "RETAINED", "BUILDING", "BLDG", "FOOTPRINT", "保留建筑", "现状建筑", "建筑"], "02_EXISTING_BLDG"),
    (["04", "ROAD", "HIGHWAY", "STREET", "TRAFFIC", "RAIL", "道路", "路网", "车行", "慢行", "中心线"], "04_ROAD_CENTER"),
    (["05", "GREEN", "PARK", "LANDUSE_GREEN", "VEGETATION", "ECOLOGY", "绿地", "公园", "景观", "生态"], "05_GREEN_SPACE"),
]

# Legacy RGB fallback for landuse types
LANDUSE_RGB: Dict[str, Tuple[int, int, int]] = {
    "01_BOUNDARY": (255, 0, 0),
    "02_EXISTING_BLDG": (200, 200, 200),
    "03_PROPOSED_BLDG": (255, 215, 0),
    "04_ROAD_CENTER": (30, 144, 255),
    "05_GREEN_SPACE": (34, 139, 34),
    "R": (255, 215, 0),         # Residential - Yellow
    "RESIDENTIAL": (255, 215, 0),
    "C": (255, 69, 0),          # Commercial - Red
    "COMMERCIAL": (255, 69, 0),
    "M": (160, 82, 45),         # Industrial - Brown
    "G": (34, 139, 34),         # Park / Green - Green
    "PARK": (34, 139, 34),
    "U": (70, 130, 180),        # Utility - Blue
    "BUILDING": (200, 200, 200),
    "ROAD": (30, 144, 255),
}


def rgb_to_truecolor(r: int, g: int, b: int) -> int:
    """Converts RGB tuple to 24-bit DXF TrueColor integer (420 Group Code)."""
    return ((r & 0xFF) << 16) | ((g & 0xFF) << 8) | (b & 0xFF)


def normalize_layer_name(raw_name: str) -> str:
    """Normalize input layer name to standard GB layer if matched, or return uppercase clean string."""
    name_str = str(raw_name).strip()
    upper_name = name_str.upper()
    if upper_name in STANDARD_GB_LAYERS:
        return upper_name
    for keywords, target in LAYER_KEYWORD_MAPPING:
        if any(kw in upper_name for kw in keywords):
            return target
    return upper_name


def clean_dxf_string(val: Any) -> str:
    """Strictly cleans string for DXF to avoid newline injection that corrupts paired group codes."""
    if val is None:
        return ""
    s = str(val).replace("\r\n", " ").replace("\n", " ").replace("\r", " ").replace("\t", " ")
    return s.strip()


def flatten_geometries(geom: Any) -> List[Tuple[str, Any]]:
    """
    Recursively expands complex geometries (MultiPolygon, MultiLineString,
    GeometryCollection, MultiPoint) into atomic elementary geometries.
    Returns list of ('polygon'|'line'|'point', elementary_geom).
    """
    if geom is None or geom.is_empty:
        return []

    geom_type = getattr(geom, "geom_type", "")
    items: List[Tuple[str, Any]] = []

    if geom_type == "Polygon":
        items.append(("polygon", geom))
    elif geom_type == "MultiPolygon":
        for part in geom.geoms:
            items.extend(flatten_geometries(part))
    elif geom_type == "LineString":
        items.append(("line", geom))
    elif geom_type == "MultiLineString":
        for part in geom.geoms:
            items.extend(flatten_geometries(part))
    elif geom_type == "Point":
        items.append(("point", geom))
    elif geom_type == "MultiPoint":
        for part in geom.geoms:
            items.extend(flatten_geometries(part))
    elif geom_type == "GeometryCollection":
        for part in geom.geoms:
            items.extend(flatten_geometries(part))
    else:
        if hasattr(geom, "geoms"):
            for part in geom.geoms:
                items.extend(flatten_geometries(part))
    return items


def project_gdf_to_metric(gdf: gpd.GeoDataFrame, target_crs: Optional[str] = None) -> gpd.GeoDataFrame:
    """
    Safely projects a GeoDataFrame from geographic coordinate system (e.g. EPSG:4326)
    to a projected metric coordinate system (UTM or CGCS2000) to ensure 1:1 isometric CAD scaling in meters.
    """
    if gdf is None or gdf.empty:
        return gdf

    is_geo = False
    if gdf.crs is not None:
        try:
            is_geo = gdf.crs.is_geographic
        except Exception:
            is_geo = False
    else:
        bounds = gdf.total_bounds
        if len(bounds) == 4:
            minx, miny, maxx, maxy = bounds
            if -180 <= minx <= 180 and -90 <= miny <= 90 and -180 <= maxx <= 180 and -90 <= maxy <= 90:
                is_geo = True

    if is_geo:
        if target_crs:
            return gdf.to_crs(target_crs)
        try:
            centroid = gdf.geometry.union_all().centroid
            lon, lat = centroid.x, centroid.y
        except AttributeError:
            centroid = gdf.unary_union.centroid
            lon, lat = centroid.x, centroid.y
        from src.engines.context_adaptive_engine import get_utm_epsg_for_coordinates
        epsg_code = get_utm_epsg_for_coordinates(lon, lat)
        return gdf.to_crs(epsg=epsg_code)

    return gdf


class VectorExporter:
    """Utility class to convert spatial GeoDataFrames into AutoCAD 2000 (AC1015) DXF files and Shapefile bundles."""

    def export_to_dxf(
        self,
        gdfs: Dict[str, gpd.GeoDataFrame],
        output_dxf_path: str,
        to_metric: bool = False,
        target_crs: Optional[str] = None
    ) -> str:
        """
        Exports GeoDataFrames to a standard AutoCAD 2000 (AC1015) ASCII DXF file
        with TABLES section, 24-bit TrueColor 420 codes, sanitized TEXT labels,
        modern LWPOLYLINE entities, and recursive MultiPolygon/MultiLineString geometry decomposition.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_dxf_path)), exist_ok=True)

        if to_metric:
            processed_gdfs = {
                k: project_gdf_to_metric(v, target_crs) if v is not None and not v.empty else v
                for k, v in gdfs.items()
            }
        else:
            processed_gdfs = gdfs

        # Determine appropriate text height
        is_metric_scale = False
        for gdf in processed_gdfs.values():
            if gdf is not None and not gdf.empty:
                b = gdf.total_bounds
                if len(b) == 4 and (b[2] - b[0] > 10.0 or b[3] - b[1] > 10.0):
                    is_metric_scale = True
                    break
        default_text_height = 3.0 if is_metric_scale else 0.0005

        dxf_lines: List[str] = []
        dxf_lines.extend(self._dxf_header())
        dxf_lines.extend(self._dxf_tables(processed_gdfs))
        dxf_lines.extend(self._dxf_entities_start())

        for layer_key, gdf in processed_gdfs.items():
            if gdf.empty:
                continue

            cad_layer = normalize_layer_name(layer_key)

            for _idx, row in gdf.iterrows():
                geom = row.geometry
                if geom is None or geom.is_empty:
                    continue

                # Determine RGB color
                lu_type = str(row.get("type", row.get("building_type", cad_layer))).upper()
                if cad_layer in STANDARD_GB_LAYERS:
                    rgb = STANDARD_GB_LAYERS[cad_layer]["rgb"]
                else:
                    rgb = LANDUSE_RGB.get(lu_type, LANDUSE_RGB.get(cad_layer, (180, 180, 180)))
                tc = rgb_to_truecolor(*rgb)

                # Recursively flatten all geometries (MultiPolygon, MultiLineString, etc.)
                atomic_geoms = flatten_geometries(geom)

                for gtype, gpart in atomic_geoms:
                    if gtype == "polygon":
                        # Exterior boundary
                        coords = list(gpart.exterior.coords)
                        dxf_lines.extend(self._polygon_to_dxf_polyline(coords, cad_layer, tc))

                        # Interior rings (holes/courtyards)
                        for interior in gpart.interiors:
                            int_coords = list(interior.coords)
                            dxf_lines.extend(self._polygon_to_dxf_polyline(int_coords, cad_layer, tc))

                        # TEXT label
                        centroid = gpart.centroid
                        label = str(row.get("name") or row.get("Floor") or "")
                        if label and label != "nan":
                            if "Floor" in row and not str(row["Floor"]).endswith("F"):
                                label += f" ({row['Floor']}F)"
                            dxf_lines.extend(self._text_to_dxf(centroid.x, centroid.y, label, cad_layer, default_text_height))

                    elif gtype == "line":
                        coords = list(gpart.coords)
                        dxf_lines.extend(self._line_to_dxf_polyline(coords, cad_layer, tc))

                        label = str(row.get("name") or "")
                        if label and label != "nan":
                            mid_idx = len(coords) // 2
                            mx, my = coords[mid_idx]
                            dxf_lines.extend(self._text_to_dxf(mx, my, label, cad_layer, default_text_height))

                    elif gtype == "point":
                        dxf_lines.extend(self._point_to_dxf(gpart.x, gpart.y, cad_layer, tc))
                        label = str(row.get("name") or "")
                        if label and label != "nan":
                            delta = 1.0 if is_metric_scale else 0.0001
                            dxf_lines.extend(self._text_to_dxf(gpart.x + delta, gpart.y + delta, label, cad_layer, default_text_height))

        dxf_lines.extend(self._dxf_entities_end())

        with open(output_dxf_path, "w", encoding="utf-8") as f:
            f.write("\n".join(dxf_lines))

        logger.info(f"Successfully generated AC1015 DXF file: {output_dxf_path}")
        return output_dxf_path

    def export_bundle(
        self,
        gdfs: Dict[str, gpd.GeoDataFrame],
        output_zip_path: str
    ) -> str:
        """
        Exports DXF and GeoJSON files bundled into a single ZIP archive.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_zip_path)), exist_ok=True)
        base_dir = os.path.dirname(output_zip_path)
        dxf_temp = os.path.join(base_dir, "temp_statutory_plan.dxf")

        self.export_to_dxf(gdfs, dxf_temp)

        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(dxf_temp, arcname="statutory_plan.dxf")
            for name, gdf in gdfs.items():
                if not gdf.empty:
                    zf.writestr(f"{name}.geojson", gdf.to_json())

        if os.path.exists(dxf_temp):
            os.remove(dxf_temp)

        return output_zip_path

    def _dxf_header(self) -> List[str]:
        """AutoCAD 2000 (AC1015) header with ANSI_936 codepage to guarantee Chinese characters rendering without mojibake."""
        return [
            "0", "SECTION",
            "2", "HEADER",
            "9", "$ACADVER",
            "1", "AC1015",
            "9", "$DWGCODEPAGE",
            "3", "ANSI_936",
            "0", "ENDSEC",
        ]

    def _dxf_tables(self, gdfs: Dict[str, gpd.GeoDataFrame]) -> List[str]:
        """Generates DXF TABLES section with standard GB LAYER definitions, handles, and subclass markers."""
        active_layers = set(STANDARD_GB_LAYERS.keys())
        for k in gdfs.keys():
            norm_k = normalize_layer_name(k)
            active_layers.add(norm_k)

        lines = [
            "0", "SECTION",
            "2", "TABLES",
            "0", "TABLE",
            "2", "LAYER",
            "5", "2",
            "100", "AcDbSymbolTable",
            "70", str(len(active_layers)),
        ]

        h = 0x20
        for lname in sorted(active_layers):
            if lname in STANDARD_GB_LAYERS:
                info = STANDARD_GB_LAYERS[lname]
                rgb = info["rgb"]
                aci = info["aci"]
            else:
                rgb = LANDUSE_RGB.get(lname, (180, 180, 180))
                aci = 7

            tc = rgb_to_truecolor(*rgb)
            lines.extend([
                "0", "LAYER",
                "5", hex(h)[2:].upper(),
                "100", "AcDbSymbolTableRecord",
                "100", "AcDbLayerTableRecord",
                "2", lname,
                "70", "0",
                "62", str(aci),
                "420", str(tc),
                "6", "CONTINUOUS",
            ])
            h += 1

        lines.extend(["0", "ENDTAB", "0", "ENDSEC"])
        return lines

    def _dxf_entities_start(self) -> List[str]:
        return ["0", "SECTION", "2", "ENTITIES"]

    def _dxf_entities_end(self) -> List[str]:
        return ["0", "ENDSEC", "0", "EOF"]

    def _polygon_to_dxf_polyline(self, coords: List[tuple], layer: str, truecolor: int) -> List[str]:
        """Exports polygon boundary as modern AutoCAD 2000 LWPOLYLINE entity."""
        pts = list(coords)
        if len(pts) > 1 and pts[0] == pts[-1]:
            pts = pts[:-1]
        if not pts:
            return []
        lines = [
            "0", "LWPOLYLINE",
            "8", layer,
            "420", str(truecolor),
            "100", "AcDbEntity",
            "100", "AcDbPolyline",
            "90", str(len(pts)),
            "70", "1",  # 1 = Closed polyline
            "43", "0.0",
        ]
        for pt in pts:
            lines.extend([
                "10", str(round(float(pt[0]), 6)),
                "20", str(round(float(pt[1]), 6)),
            ])
        return lines

    def _line_to_dxf_polyline(self, coords: List[tuple], layer: str, truecolor: int) -> List[str]:
        """Exports linestring as modern AutoCAD 2000 LWPOLYLINE entity."""
        pts = list(coords)
        if not pts:
            return []
        lines = [
            "0", "LWPOLYLINE",
            "8", layer,
            "420", str(truecolor),
            "100", "AcDbEntity",
            "100", "AcDbPolyline",
            "90", str(len(pts)),
            "70", "0",  # 0 = Open polyline
            "43", "0.0",
        ]
        for pt in pts:
            lines.extend([
                "10", str(round(float(pt[0]), 6)),
                "20", str(round(float(pt[1]), 6)),
            ])
        return lines

    def _point_to_dxf(self, x: float, y: float, layer: str, truecolor: int) -> List[str]:
        return [
            "0", "POINT",
            "8", layer,
            "420", str(truecolor),
            "10", str(round(float(x), 6)),
            "20", str(round(float(y), 6)),
            "30", "0.0",
        ]

    def _text_to_dxf(self, x: float, y: float, text_str: str, layer: str, text_height: float = 3.0) -> List[str]:
        clean_text = clean_dxf_string(text_str)
        if not clean_text:
            return []
        return [
            "0", "TEXT",
            "8", layer,
            "10", str(round(float(x), 6)),
            "20", str(round(float(y), 6)),
            "30", "0.0",
            "40", str(round(float(text_height), 4)),
            "1", clean_text,
        ]


def export_dxf_from_gdf(
    gdf: gpd.GeoDataFrame,
    output_dxf_path: str,
    layer_name: str = "01_BOUNDARY",
    to_metric: bool = True,
    target_crs: Optional[str] = None,
) -> str:
    """
    Exports a single GeoDataFrame to AutoCAD 2000 AC1015 DXF.
    Auto-projects to metric coordinate system (UTM or CGCS2000) by default to prevent micro-scale distortion in CAD.
    """
    exporter = VectorExporter()
    norm_layer = normalize_layer_name(layer_name)
    return exporter.export_to_dxf(
        {norm_layer: gdf},
        output_dxf_path,
        to_metric=to_metric,
        target_crs=target_crs,
    )


def export_multi_layer_dxf(
    gdfs: Dict[str, gpd.GeoDataFrame],
    output_dxf_path: str,
    to_metric: bool = True,
    target_crs: Optional[str] = None,
) -> str:
    """
    Exports multiple GeoDataFrames to a layered AutoCAD 2000 AC1015 DXF.
    Auto-projects to metric coordinate system (UTM or CGCS2000) by default.
    """
    exporter = VectorExporter()
    return exporter.export_to_dxf(
        gdfs,
        output_dxf_path,
        to_metric=to_metric,
        target_crs=target_crs,
    )


def export_universal_dxf(
    gdf_or_gdfs: Union[gpd.GeoDataFrame, Dict[str, gpd.GeoDataFrame]],
    output_path: str,
    target_crs: Optional[str] = None,
) -> str:
    """通用自适应 DXF 导出接口：自动识别坐标并映射至自适应 UTM 投影带，生成标准 AC1015 DXF。"""
    exporter = VectorExporter()
    if isinstance(gdf_or_gdfs, gpd.GeoDataFrame):
        gdfs = {"01_BOUNDARY": gdf_or_gdfs}
    else:
        gdfs = gdf_or_gdfs
    return exporter.export_to_dxf(
        gdfs,
        output_path,
        to_metric=True,
        target_crs=target_crs,
    )


