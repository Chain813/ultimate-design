@echo off
chcp 65001 >nul 2>&1
title 环境安装脚本
color 0B

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                          ║
echo ║   🔧 环境安装向导                                        ║
echo ║   Environment Setup Wizard                               ║
echo ║                                                          ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

echo [1/3] 检查 Conda 环境...
echo.

REM Check if gis_ai environment exists
conda env list 2>nul | findstr "gis_ai" >nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ 发现现有环境: gis_ai
    echo.
    set /p UPDATE="是否更新现有环境？(Y/N，默认 Y): "
    if /i "%UPDATE%"=="N" (
        echo.
        echo 跳过环境创建，直接安装依赖...
        goto :install_deps
    )
) else (
    echo ✗ 未找到 gis_ai 环境，正在创建...
    echo.
    
    conda create -n gis_ai python=3.10 -y
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo ✗ 环境创建失败! 请检查 Conda 安装状态。
        pause
        exit /b 1
    )
    echo.
    echo ✓ 环境创建成功: gis_ai (Python 3.10)
)

:install_deps
echo.
echo [2/3] 安装项目依赖...
echo.
echo ⚠️  此过程可能需要 10-30 分钟，请耐心等待...
echo.

REM Install requirements
call conda activate gis_ai 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ✗ 环境激活失败，尝试直接调用 Python...
    
    REM Try direct Python path
    if exist "%CONDA_PREFIX%\envs\gis_ai\python.exe" (
        set PYTHON_PATH=%CONDA_PREFIX%\envs\gis_ai\python.exe
    ) else if exist "%USERPROFILE%\anaconda3\envs\gis_ai\python.exe" (
        set PYTHON_PATH=%USERPROFILE%\anaconda3\envs\gis_ai\python.exe
    ) else if exist "%USERPROFILE%\miniconda3\envs\gis_ai\python.exe" (
        set PYTHON_PATH=%USERPROFILE%\miniconda3\envs\gis_ai\python.exe
    ) else (
        echo ✗ 无法找到 Python 路径!
        pause
        exit /b 1
    )
    
    %PYTHON_PATH% -m pip install -r "%~dp0requirements.txt"
) else (
    pip install -r "%~dp0requirements.txt"
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ✗ 依赖安装失败! 请检查网络连接。
    echo.
    echo 提示: 可以使用清华镜像源加速下载:
    echo   pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo [3/3] 验证安装...
echo.

REM Run environment check
if defined PYTHON_PATH (
    %PYTHON_PATH% "%~dp0check_env.py"
) else (
    python "%~dp0check_env.py"
)

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                          ║
echo ║   ✅ 环境配置完成!                                       ║
echo ║                                                          ║
echo ║   下一步:                                                ║
echo ║   • 双击 run.bat 启动应用程序                            ║
echo ║   • 或运行: streamlit run app.py                         ║
echo ║                                                          ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

pause
