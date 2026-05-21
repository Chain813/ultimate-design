import argparse
import geopandas as gpd
import os
import sys
from src.config.paths import DATA_DIR, GIS_DIR

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def prepare_landuse(gpkg_path: str = None):
    print("🚀 开始土地利用数据裁剪流程...")

    # 1. 设置路径
    boundary_path = str(GIS_DIR / "Boundary_Scope.geojson")
    input_gpkg = gpkg_path or str(DATA_DIR / "raw" / "EULUC_China_20.gpkg")
    output_path = str(GIS_DIR / "landuse.geojson")

    if not os.path.exists(boundary_path):
        print(f"❌ 错误: 找不到边界文件 {boundary_path}")
        return

    if not os.path.exists(input_gpkg):
        print(f"❌ 错误: 找不到土地利用数据 {input_gpkg}")
        return

    # 2. 读取边界并获取 Bounding Box
    print(f"📂 读取研究范围: {boundary_path}")
    boundary = gpd.read_file(boundary_path)
    if boundary.crs is None:
        boundary.set_crs("EPSG:4326", inplace=True)

    bbox = boundary.total_bounds # [minx, miny, maxx, maxy]
    print(f"📍 研究范围 BBox: {bbox}")

    # 3. 读取 GPKG (仅读取 BBox 范围内的数据)
    print(f"📂 正在从全国数据库裁剪 (路径: {input_gpkg})...")
    try:
        # 使用 bbox 参数可以极大提高读取速度，pyogrio 引擎支持此操作
        landuse = gpd.read_file(
            input_gpkg,
            bbox=tuple(bbox),
            engine="pyogrio"
        )

        if landuse.empty:
            print("⚠️ 警告: 该范围内未发现土地利用数据。")
            return

        print(f"📊 捕获到 {len(landuse)} 个用地地块。")

        # 4. 精确裁剪 (防止 BBox 包含范围外数据)
        print("✂️ 正在进行精确空间裁剪...")
        landuse_clipped = gpd.clip(landuse, boundary)

        # 5. 导出结果
        print(f"💾 正在保存至: {output_path}")
        landuse_clipped.to_file(output_path, driver="GeoJSON")
        print("✅ 土地利用数据准备就绪！")

    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="裁剪全国土地利用数据至研究范围")
    parser.add_argument("--source", type=str, default=None,
                        help="EULUC gpkg 文件路径 (默认: data/raw/EULUC_China_20.gpkg)")
    args = parser.parse_args()
    prepare_landuse(gpkg_path=args.source)
