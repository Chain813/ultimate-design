@echo off
title UltimateDESIGN 启动器
color 0A

echo ===================================================
echo.
echo      UltimateDESIGN 城市设计与微更新辅助平台
echo      正在初始化便携式运行环境，请稍候...
echo.
echo ===================================================

set PYTHONNOUSERSITE=1
set WINPYTHON_DIR=%~dp0WinPython

if not exist "%WINPYTHON_DIR%\python\python.exe" (
    echo [错误] 未找到便携式 Python 环境！
    echo 是否已将 WinPython 解压至此目录？
    pause
    exit /b 1
)

set PATH=%WINPYTHON_DIR%\python;%WINPYTHON_DIR%\python\Scripts;%PATH%

echo [INFO] 环境加载成功！正在启动核心引擎...
"%WINPYTHON_DIR%\python\python.exe" -m streamlit run app.py
pause
