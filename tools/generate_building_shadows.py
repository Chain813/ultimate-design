import os
import json
import math
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.affinity import translate
from pathlib import Path

def compute_shadow_geometry(geom, height):
    """
    计算单个 3D 棱镜建筑在地面投影生成的精确矢量阴影多边形。
    """
    if not geom or geom.is_empty:
        return geom
        
    # 上午 10:00 左右太阳夹角下的阴影位移系数
    # dx < 0, dy > 0 指向西北偏北方向
    # 比例系数约 0.55 倍高度
    # 结合长春当地纬度 (43.90095) 进行投影单位换算：
    # 1m 纬度 (Y) ≈ 9.0e-6 度
    # 1m 经度 (X) ≈ 1.25e-5 度
    dx = -4.86e-6 * height
    dy = 3.5e-6 * height
    
    # 获取原始图形的外边界（仅对外边界进行侧壁投影，忽略内空洞阴影以极大提升性能并防错）
    if isinstance(geom, Polygon):
        polygons = [geom]
    elif isinstance(geom, MultiPolygon):
        polygons = list(geom.geoms)
    else:
        return geom
        
    shadow_parts = []
    for poly in polygons:
        if poly.is_empty or not poly.exterior:
            continue
            
        # 顶面投影
        poly_translated = translate(poly, xoff=dx, yoff=dy)
        shadow_parts.append(poly)
        shadow_parts.append(poly_translated)
        
        # 侧面投影：连接原始顶点和投影顶点
        coords = list(poly.exterior.coords)
        for i in range(len(coords) - 1):
            p1 = coords[i]
            p2 = coords[i+1]
            p1_t = (p1[0] + dx, p1[1] + dy)
            p2_t = (p2[0] + dx, p2[1] + dy)
            
            # 创建侧墙阴影四边形
            wall = Polygon([p1, p2, p2_t, p1_t])
            if wall.is_valid:
                shadow_parts.append(wall)
                
    if not shadow_parts:
        return geom
        
    # 拓扑并集，融合成单一的阴影面
    try:
        merged_shadow = unary_union(shadow_parts)
        return merged_shadow
    except Exception as e:
        # 容错：如果拓扑并集失败，回退到凸包或原多边形
        return geom

def main():
    print("[System] Start calculating vector shadows...")
    
    # 定位静态文件路径
    buildings_path = Path("static/buildings.geojson")
    output_path = Path("static/building_shadows.geojson")
    
    if not buildings_path.exists():
        # 回退至 data/gis 目录
        buildings_path = Path("data/gis/Building_Footprints.geojson")
        
    if not buildings_path.exists():
        print("[Error] Building footprint GeoJSON not found!")
        return
        
    print(f"[Info] Reading source file: {buildings_path.resolve()}")
    gdf = gpd.read_file(buildings_path)
    print(f"[Info] Loaded {len(gdf)} buildings. Generating shadows...")
    
    # 预估建筑高度
    heights = []
    for idx, row in gdf.iterrows():
        props = row
        # 匹配 JavaScript 侧的高度提取逻辑
        floor = props.get('floor') or props.get('Floor') or props.get('levels') or props.get('building:levels')
        height = 1.0
        if floor is not None:
            try:
                height = float(floor) * 3.5
            except (ValueError, TypeError):
                pass
        else:
            h_val = props.get('height') or props.get('Height')
            if h_val is not None:
                try:
                    height = float(h_val)
                except (ValueError, TypeError):
                    pass
        heights.append(height)
        
    # 应用矢量阴影投影
    shadow_geometries = []
    for idx, (geom, h) in enumerate(zip(gdf.geometry, heights)):
        if idx % 1000 == 0:
            print(f"   Processed {idx}/{len(gdf)} buildings...")
        shadow_geom = compute_shadow_geometry(geom, h)
        shadow_geometries.append(shadow_geom)
        
    # 创建阴影 GeoDataFrame
    shadow_gdf = gpd.GeoDataFrame(
        geometry=shadow_geometries,
        crs=gdf.crs
    )
    
    # 保留必要属性或只保留几何图形以减小文件体积
    shadow_gdf['id'] = shadow_gdf.index
    
    print(f"[Info] Writing shadow file to: {output_path.resolve()}")
    shadow_gdf.to_file(output_path, driver="GeoJSON")
    print(f"[Info] Shadow file generated successfully! Size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    main()
