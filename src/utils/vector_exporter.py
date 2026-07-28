"""
Vector Exporter for UltimateDESIGN (Inspired by ezdxf).
Exports GeoDataFrames to AutoCAD DXF format (.dxf) with TABLES layer definitions,
24-bit TrueColor (Group Code 420) support, and TEXT/MTEXT annotations.
"""

import os
import zipfile
import logging
from typing import Dict, Any, Optional, List, Tuple
import geopandas as gpd
from shapely.geometry import Polygon, LineString, Point, MultiPolygon

logger = logging.getLogger(__name__)

# Standard National Urban Planning Landuse RGB Mapping
LANDUSE_RGB = {
    "R": (255, 215, 0),         # Residential - Yellow (0xFFD700)
    "RESIDENTIAL": (255, 215, 0),
    "C": (255, 69, 0),          # Commercial - Red (0xFF4500)
    "COMMERCIAL": (255, 69, 0),
    "M": (160, 82, 45),         # Industrial - Brown (0xA0522D)
    "G": (50, 205, 50),         # Park / Green - Green (0x32CD32)
    "PARK": (50, 205, 50),
    "U": (70, 130, 180),        # Utility - Blue (0x4682B4)
    "BUILDING": (220, 220, 220),# Building Footprint - Light Gray
    "ROAD": (100, 100, 100)     # Road Axis - Gray
}

def rgb_to_truecolor(r: int, g: int, b: int) -> int:
    """Converts RGB tuple to 24-bit DXF TrueColor integer (420 Group Code code pattern in ezdxf)."""
    return ((r & 0xFF) << 16) | ((g & 0xFF) << 8) | (b & 0xFF)


class VectorExporter:
    """Utility class to convert spatial GeoDataFrames into CAD DXF files and Shapefile bundles."""

    def export_to_dxf(
        self,
        gdfs: Dict[str, gpd.GeoDataFrame],
        output_dxf_path: str
    ) -> str:
        """
        Exports GeoDataFrames to an ASCII DXF file with TABLES section, TrueColor 420 group codes, and TEXT labels.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_dxf_path)), exist_ok=True)

        dxf_lines = []
        dxf_lines.extend(self._dxf_header())
        dxf_lines.extend(self._dxf_tables(gdfs))
        dxf_lines.extend(self._dxf_entities_start())

        for layer_name, gdf in gdfs.items():
            if gdf.empty:
                continue
            cad_layer = layer_name.upper()
            
            for idx, row in gdf.iterrows():
                geom = row.geometry
                if geom is None or geom.is_empty:
                    continue
                
                # Check for RGB color mapping
                lu_type = str(row.get("type", row.get("building_type", cad_layer))).upper()
                rgb = LANDUSE_RGB.get(lu_type, LANDUSE_RGB.get(cad_layer, (180, 180, 180)))
                tc = rgb_to_truecolor(*rgb)

                # Export Polygons / MultiPolygons
                if isinstance(geom, (Polygon, MultiPolygon)):
                    polys = [geom] if isinstance(geom, Polygon) else geom.geoms
                    for p in polys:
                        coords = list(p.exterior.coords)
                        dxf_lines.extend(self._polygon_to_dxf_polyline(coords, cad_layer, tc))
                        
                        # Add TEXT annotation for building floors / names
                        centroid = p.centroid
                        label = str(row.get("name") or row.get("Floor") or "")
                        if label:
                            if "Floor" in row:
                                label += f" ({row['Floor']}F)"
                            dxf_lines.extend(self._text_to_dxf(centroid.x, centroid.y, label, cad_layer))

                # Export LineStrings
                elif isinstance(geom, LineString):
                    coords = list(geom.coords)
                    dxf_lines.extend(self._line_to_dxf_polyline(coords, cad_layer, tc))
                    
                    label = str(row.get("name") or "")
                    if label:
                        mid_idx = len(coords) // 2
                        mx, my = coords[mid_idx]
                        dxf_lines.extend(self._text_to_dxf(mx, my, label, cad_layer))

                # Export Points
                elif isinstance(geom, Point):
                    dxf_lines.extend(self._point_to_dxf(geom.x, geom.y, cad_layer, tc))
                    label = str(row.get("name") or "")
                    if label:
                        dxf_lines.extend(self._text_to_dxf(geom.x + 0.0001, geom.y + 0.0001, label, cad_layer))

        dxf_lines.extend(self._dxf_entities_end())

        with open(output_dxf_path, "w", encoding="utf-8") as f:
            f.write("\n".join(dxf_lines))

        logger.info(f"Successfully generated DXF file: {output_dxf_path}")
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
        return [
            "0", "SECTION",
            "2", "HEADER",
            "9", "$ACADVER",
            "1", "AC1009",
            "0", "ENDSEC"
        ]

    def _dxf_tables(self, gdfs: Dict[str, gpd.GeoDataFrame]) -> List[str]:
        """Generates DXF TABLES section with LAYER definitions (ezdxf pattern)."""
        lines = [
            "0", "SECTION",
            "2", "TABLES",
            "0", "TABLE",
            "2", "LAYER",
            "70", str(len(gdfs) + 1)
        ]
        
        layers = set([k.upper() for k in gdfs.keys()] + ["BUILDINGS", "ROADS", "LANDUSE", "ANNOTATIONS"])
        for lname in layers:
            rgb = LANDUSE_RGB.get(lname, (180, 180, 180))
            tc = rgb_to_truecolor(*rgb)
            lines.extend([
                "0", "LAYER",
                "2", lname,
                "70", "0",
                "62", "7",  # Default index color fallback
                "420", str(tc),
                "6", "CONTINUOUS"
            ])
        lines.extend(["0", "ENDTAB", "0", "ENDSEC"])
        return lines

    def _dxf_entities_start(self) -> List[str]:
        return ["0", "SECTION", "2", "ENTITIES"]

    def _dxf_entities_end(self) -> List[str]:
        return ["0", "ENDSEC", "0", "EOF"]

    def _polygon_to_dxf_polyline(self, coords: List[tuple], layer: str, truecolor: int) -> List[str]:
        lines = [
            "0", "POLYLINE",
            "8", layer,
            "420", str(truecolor),
            "66", "1",
            "70", "1"
        ]
        for x, y in coords[:]:
            lines.extend([
                "0", "VERTEX",
                "8", layer,
                "10", str(round(float(x), 6)),
                "20", str(round(float(y), 6)),
                "30", "0.0"
            ])
        lines.extend(["0", "SEQEND", "8", layer])
        return lines

    def _line_to_dxf_polyline(self, coords: List[tuple], layer: str, truecolor: int) -> List[str]:
        lines = [
            "0", "POLYLINE",
            "8", layer,
            "420", str(truecolor),
            "66", "1",
            "70", "0"
        ]
        for x, y in coords:
            lines.extend([
                "0", "VERTEX",
                "8", layer,
                "10", str(round(float(x), 6)),
                "20", str(round(float(y), 6)),
                "30", "0.0"
            ])
        lines.extend(["0", "SEQEND", "8", layer])
        return lines

    def _point_to_dxf(self, x: float, y: float, layer: str, truecolor: int) -> List[str]:
        return [
            "0", "POINT",
            "8", layer,
            "420", str(truecolor),
            "10", str(round(float(x), 6)),
            "20", str(round(float(y), 6)),
            "30", "0.0"
        ]

    def _text_to_dxf(self, x: float, y: float, text_str: str, layer: str) -> List[str]:
        return [
            "0", "TEXT",
            "8", layer,
            "10", str(round(float(x), 6)),
            "20", str(round(float(y), 6)),
            "30", "0.0",
            "40", "0.0005",  # Text height in geographic coordinates
            "1", text_str
        ]
