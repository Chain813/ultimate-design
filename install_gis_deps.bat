@echo off
chcp 65001 >nul
echo ============================================================
echo UltimateDESIGN GIS 依赖安装脚本
echo ============================================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

echo 正在安装 GIS 和城市分析相关依赖...
echo.

REM 核心 GIS 库
echo [1/7] 安装核心 GIS 库...
pip install osmnx geopandas rasterio shapely fiona pyproj -q

REM 城市分析
echo [2/7] 安装城市分析库...
pip install momepy pandana pysal -q

REM 地理编码
echo [3/7] 安装地理编码库...
pip install geocoder overpy -q

REM 可视化
echo [4/7] 安装可视化库...
pip install leafmap pydeck -q

REM 数据处理
echo [5/7] 安装数据处理库...
pip install pandas numpy scipy -q

REM 可选: 遥感分析
echo [6/7] 安装遥感分析库 (可选)...
pip install solaris -q 2>nul

REM 可选: 深度学习遥感
echo [7/7] 安装深度学习遥感库 (可选)...
pip install torchgeo -q 2>nul

echo.
echo ============================================================
echo 安装完成!
echo ============================================================
echo.
echo 已安装的包:
pip list | findstr /i "osmnx geopandas rasterio momepy pandana pysal leafmap pydeck"
echo.
echo 如需使用 OSMnx 获取数据，请运行:
echo   python scripts/fetch_supplementary_data.py --osm
echo.
pause
