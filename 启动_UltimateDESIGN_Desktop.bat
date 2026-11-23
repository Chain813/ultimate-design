@echo off
chcp 65001 >nul
title UltimateDESIGN v7.0 Desktop Studio 启动器
color 0B

echo ===================================================================
echo.
echo      UltimateDESIGN v7.0 城市设计与微更新原生桌面工作站
echo      Electron + React 19 + MapLibre/Deck.GL + DuckDB Spatial
echo      正在初始化便携式运行环境，请稍候...
echo.
echo ===================================================================

set PYTHONNOUSERSITE=1
set PYTHONUTF8=1
set REPO_ROOT=%~dp0
set WINPYTHON_DIR=%REPO_ROOT%WinPython

if not exist "%WINPYTHON_DIR%\python\python.exe" (
    echo [错误] 未找到便携式 WinPython 环境: %WINPYTHON_DIR%\python\python.exe
    echo 请确认已将 WinPython 解压至项目根目录。
    pause
    exit /b 1
)

set PATH=%WINPYTHON_DIR%\python;%WINPYTHON_DIR%\python\Scripts;%PATH%
set UD_PYTHON_PATH=%WINPYTHON_DIR%\python\python.exe

if not exist "%REPO_ROOT%desktop\frontend\dist\index.html" (
    echo [INFO] 首次启动尚未检测到前端构建产物 desktop\frontend\dist\index.html，将自动构建...
)

if exist "%REPO_ROOT%desktop\electron\node_modules\.bin\electron.cmd" (
    echo [INFO] 已就绪 Electron 原生桌面壳层与 WinPython 空间引擎...
) else (
    echo [INFO] 正在通过 WinPython 便携启动器加载 UltimateDESIGN v7.0 Desktop Studio...
)

"%WINPYTHON_DIR%\python\python.exe" "%REPO_ROOT%run_desktop.py" %*
pause
