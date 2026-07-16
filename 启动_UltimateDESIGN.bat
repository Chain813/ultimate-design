@echo off
title UltimateDESIGN 启动器
color 0A

echo ===================================================
echo.
echo      UltimateDESIGN 城市设计与微更新辅助平台
echo      正在初始化便携式运行环境，请稍候...
echo.
echo ===================================================

:: 获取当前批处理文件所在目录
set "CURRENT_DIR=%~dp0"

:: 假设 WinPython 解压在当前目录下的 WinPython 文件夹内
:: 请根据实际解压的文件夹名称修改下面这行
set "WINPYTHON_DIR=%CURRENT_DIR%WinPython"

:: 检查 Python 环境是否存在
if not exist "%WINPYTHON_DIR%\python-3.*\python.exe" (
    color 0C
    echo [错误] 未找到便携式 Python 环境！
    echo 请确认是否已将 WinPython 解压至: %WINPYTHON_DIR%
    pause
    exit /b 1
)

:: 获取实际的 Python 路径 (WinPython 的结构通常是 python-3.x.x.amd64)
for /d %%I in ("%WINPYTHON_DIR%\python-*") do set "PYTHON_EXE=%%I\python.exe"

echo [信息] 找到 Python 环境: %PYTHON_EXE%
echo [信息] 正在启动 Streamlit 服务...
echo.

:: 启动 app.py
"%PYTHON_EXE%" -m streamlit run "%CURRENT_DIR%src\app.py"

pause
