"""
🛠️ 一键式地块数据裁剪、清洗与空间关联处理管线 (Data Process Pipeline)
------------------------------------------------------------------
本脚本提供新地块数据的全自动管线式处理：
1. 提取 Boundary_Scope 边界多边形及配置的缓冲范围进行数据裁剪。
2. 表格数据集（POI、交通、精确点位等）列名大小写及中英文模糊匹配归一化。
3. 空间数据加载、CRS 对齐，并运行建筑与用地的 Centroid 空间关联分析。
4. 内置 .buffer(0) 解决 GeoPandas 拓扑多边形无效性错误防御。
5. 自动对 GeoJSON 进行坐标 6 位精度截断、无关字段属性清洗过滤，并输出到 static 压缩缓存。
6. 自动联动执行数据质量体检脚本 (tools/data_quality_check.py)。
"""
import sys
import json
import subprocess
from pathlib import Path

# Windows 终端 UTF-8 编码修复
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 确保可以引用项目模块
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import geopandas as gpd
from shapely.geometry import shape

from src.config import DATA_FILES, GIS_FILES, resolve_path


def get_boundary_geometry():
    """读取边界 GeoJSON 并提取合并后的 Shapely 多边形"""
    boundary_path = resolve_path(GIS_FILES["boundary"])
    if not boundary_path.exists():
        print(f"❌ 错误: 边界文件不存在 {boundary_path}")
        return None
    try:
        gdf = gpd.read_file(boundary_path)
        # 用 buffer(0) 防御拓扑问题，然后合并为一个几何对象
        geom = gdf.geometry.buffer(0).union_all()
        return geom
    except Exception as e:
        print(f"❌ 读取边界几何失败: {e}")
        return None


def normalize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """归一化 DataFrame 列名：将中英文、大小写不同变体统一映射为标准列名"""
    col_mapping = {
        'lng': 'Lng', 'longitude': 'Lng', '经度': 'Lng', 'lng_wgs': 'Lng',
        'lat': 'Lat', 'latitude': 'Lat', '纬度': 'Lat', 'lat_wgs': 'Lat',
        'name': 'Name', '名称': 'Name', 'poi名称': 'Name',
        'type': 'Type', '类型': 'Type', '分类': 'Type',
        'flow': 'Flow', '流量': 'Flow', 'traffic': 'Flow', 'volume': 'Flow'
    }
    df.rename(columns=lambda c: col_mapping.get(str(c).strip().lower(), c), inplace=True)
    return df


def process_tabular_data(boundary_geom, buffer_deg=0.01):
    """裁剪并归一化表格数据集"""
    print("\n--- 1. 表格数据清洗与坐标过滤 ---")
    if boundary_geom is None:
        print("⚠️ 无法获取边界几何，跳过坐标过滤裁剪。")
        return

    min_x, min_y, max_x, max_y = boundary_geom.bounds
    bbox_min_x = min_x - buffer_deg
    bbox_min_y = min_y - buffer_deg
    bbox_max_x = max_x + buffer_deg
    bbox_max_y = max_y + buffer_deg

    print(f"  边界范围: Lng [{min_x:.6f}, {max_x:.6f}], Lat [{min_y:.6f}, {max_y:.6f}]")
    print(f"  裁剪范围 (缓冲 {buffer_deg} 度): Lng [{bbox_min_x:.6f}, {bbox_max_x:.6f}], Lat [{bbox_min_y:.6f}, {bbox_max_y:.6f}]")

    for name, file_path_str in DATA_FILES.items():
        file_path = resolve_path(file_path_str)
        if not file_path.exists():
            print(f"  [跳过] 文件不存在: {name} -> {file_path}")
            continue

        is_xlsx = file_path.suffix.lower() == '.xlsx'
        try:
            if is_xlsx:
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path, encoding="utf-8-sig")
        except Exception as e:
            print(f"  ❌ 读取 {name} 失败: {e}")
            continue

        orig_len = len(df)
        df = normalize_dataframe_columns(df)

        if "Lng" in df.columns and "Lat" in df.columns:
            df["Lng"] = pd.to_numeric(df["Lng"], errors='coerce')
            df["Lat"] = pd.to_numeric(df["Lat"], errors='coerce')
            df.dropna(subset=["Lng", "Lat"], inplace=True)

            # Bounding Box 过滤
            df = df[
                (df["Lng"] >= bbox_min_x) & (df["Lng"] <= bbox_max_x) &
                (df["Lat"] >= bbox_min_y) & (df["Lat"] <= bbox_max_y)
            ]
            print(f"  ✅ 过滤并归一化 {name}: 行数 {orig_len} -> {len(df)}")
        else:
            print(f"  ✅ 归一化 {name} (无经纬度字段): 行数 {orig_len}")

        try:
            if is_xlsx:
                df.to_excel(file_path, index=False)
            else:
                df.to_csv(file_path, index=False, encoding="utf-8-sig")
        except Exception as e:
            print(f"  ❌ 保存 {name} 失败: {e}")


def run_spatial_join():
    """进行建筑和用地 Centroid 空间关联关联及 prop_style 标签自动化分配"""
    print("\n--- 2. 建筑与用地空间关联 (Spatial Join) ---")
    buildings_path = resolve_path(GIS_FILES["buildings"])
    landuse_path = resolve_path(GIS_FILES["landuse"])

    if not buildings_path.exists() or not landuse_path.exists():
        print(f"  ⚠️ 缺失建筑或用地文件，跳过空间关联。")
        return

    try:
        buildings = gpd.read_file(buildings_path)
        landuse = gpd.read_file(landuse_path)

        # 拓扑修复防错
        buildings['geometry'] = buildings.geometry.buffer(0)
        landuse['geometry'] = landuse.geometry.buffer(0)

        if 'building_id' not in buildings.columns:
            buildings.insert(0, 'building_id', [f"B{idx + 1:06d}" for idx in range(len(buildings))])

        if buildings.crs != landuse.crs:
            landuse = landuse.to_crs(buildings.crs)

        print("  计算建筑质心...")
        bld_centroids = buildings.copy()
        bld_centroids['geometry'] = bld_centroids.geometry.centroid

        print("  执行空间相交关联...")
        joined = gpd.sjoin(bld_centroids, landuse[['Class', 'geometry']], how='left', predicate='within')

        buildings['landuse_class'] = joined['Class'].values

        # 匹配规则
        if 'is_historical' not in buildings.columns:
            buildings['is_historical'] = False
        if 'prop_style' not in buildings.columns:
            buildings['prop_style'] = 'normal'

        existing_hist = buildings['prop_style'] == 'historical'

        park_mask = buildings['landuse_class'] == 10
        hist_mask = buildings['landuse_class'] == 9

        # 公园绿地建筑
        buildings.loc[park_mask, 'is_historical'] = False
        buildings.loc[park_mask, 'prop_style'] = 'park'
        buildings.loc[park_mask, 'hist_name'] = '公园绿地区域'
        buildings.loc[park_mask, 'hist_batch'] = 'G-绿地'

        # 历史保护区域建筑
        new_hist = hist_mask & ~existing_hist
        buildings.loc[new_hist, 'is_historical'] = True
        buildings.loc[new_hist, 'prop_style'] = 'historical'
        buildings.loc[new_hist, 'hist_name'] = '行政办公/历史保护区域'
        buildings.loc[new_hist, 'hist_batch'] = 'A-保护'

        buildings.drop(columns=['landuse_class'], inplace=True, errors='ignore')

        # 保存更新
        buildings.to_file(buildings_path, driver='GeoJSON')
        
        # 复制到 static 下
        static_bld = ROOT / "static" / "buildings.geojson"
        static_bld.parent.mkdir(parents=True, exist_ok=True)
        buildings.to_file(static_bld, driver='GeoJSON')

        n_park = (buildings['prop_style'] == 'park').sum()
        n_hist = (buildings['prop_style'] == 'historical').sum()
        n_normal = (buildings['prop_style'] == 'normal').sum()
        print(f"  ✅ 关联成功! 公园绿地: {n_park}, 历史保护: {n_hist}, 普通建筑: {n_normal}")
    except Exception as e:
        print(f"  ❌ 空间关联关联失败: {e}")


def compress_geojson_files(precision=6):
    """压缩所有的 GeoJSON 文件：截断坐标精度并过滤冗余属性"""
    print("\n--- 3. 空间数据坐标截断与压缩 ---")
    keep_fields = ['Class', 'is_historical', 'prop_style', 'hist_name', 'hist_batch', 'Floor', 'Name', 'name']

    def round_coords(obj):
        if isinstance(obj, list):
            if len(obj) == 2 and isinstance(obj[0], (int, float)):
                return [round(obj[0], precision), round(obj[1], precision)]
            return [round_coords(x) for x in obj]
        return obj

    # 压缩列表，包括 static 目录下的文件
    files_to_compress = [
        (resolve_path(GIS_FILES["buildings"]), ROOT / "static" / "buildings.geojson"),
        (resolve_path(GIS_FILES["landuse"]), ROOT / "static" / "landuse.geojson"),
        (resolve_path(GIS_FILES["boundary"]), ROOT / "static" / "boundary.geojson"),
        (resolve_path(GIS_FILES["roads"]), ROOT / "static" / "roads.geojson"),
    ]

    for source_path, target_path in files_to_compress:
        if not source_path.exists():
            continue

        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            compressed_features = []
            for feature in data.get('features', []):
                props = feature.get('properties', {})
                new_props = {}
                for field in keep_fields:
                    if field in props:
                        new_props[field] = props[field]

                feature['properties'] = new_props
                if 'geometry' in feature and feature['geometry']:
                    feature['geometry']['coordinates'] = round_coords(feature['geometry'].get('coordinates', []))
                compressed_features.append(feature)

            data['features'] = compressed_features

            # 导出紧凑 JSON (去掉多余空格)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, separators=(',', ':'))

            # 同时回写原文件，保持数据一致
            with open(source_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, separators=(',', ':'))

            orig_size = source_path.stat().st_size / (1024 * 1024)
            new_size = target_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ 压缩 {source_path.name} -> {target_path.name}: {orig_size:.2f}MB -> {new_size:.2f}MB (压缩率: {((orig_size - new_size)/orig_size)*100:.1f}%)")
        except Exception as e:
            print(f"  ❌ 压缩 {source_path.name} 失败: {e}")


def run_data_quality_check():
    """联动执行数据质量体检脚本"""
    print("\n--- 4. 执行数据质量体检 ---")
    script_path = ROOT / "tools" / "data_quality_check.py"
    if not script_path.exists():
        print(f"❌ 质量体检脚本不存在: {script_path}")
        return

    try:
        res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, encoding='utf-8')
        print(res.stdout)
        if res.stderr:
            print("错误输出:")
            print(res.stderr)
        print(f"体检脚本返回状态码: {res.returncode}")
    except Exception as e:
        print(f"❌ 执行体检脚本失败: {e}")


def main():
    print("==================================================")
    print("🌅 开始地块数据全自动清洗与关联处理管线")
    print("==================================================")

    geom = get_boundary_geometry()
    
    # 1. 裁剪表格数据
    process_tabular_data(geom, buffer_deg=0.01)

    # 2. 建筑和用地关联
    run_spatial_join()

    # 3. 精度截断与缓存压缩
    compress_geojson_files(precision=6)

    # 4. 执行质量体检
    run_data_quality_check()

    print("\n🎉 数据管线处理完成！")
    print("==================================================")


if __name__ == "__main__":
    main()
