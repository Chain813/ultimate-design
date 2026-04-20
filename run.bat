@echo off
setlocal enabledelayedexpansion
title Micro-Renewal Decision Platform
color 0A

echo.
echo ================================================================
echo   Multi-modal Micro-renewal Decision Support System
echo   Changchun Pseudo-Manchu Palace District
echo ================================================================
echo.

REM ==========================================
REM Step 1: Check Python Environment
REM ==========================================
echo [1/4] Checking Python environment...
echo.

set PYTHON_FOUND=0

REM Check for Anaconda in common root locations (E:, F:, D:, etc.)
for %%d in (E F D G H I J K L) do (
    if exist "%%d:\anaconda3\envs\gis_ai\python.exe" (
        echo [OK] Found Python: %%d:\anaconda3\envs\gis_ai\python.exe
        set "PYTHON_PATH=%%d:\anaconda3\envs\gis_ai\python.exe"
        set PYTHON_FOUND=1
        goto :check_deps
    )
    if exist "%%d:\anaconda\envs\gis_ai\python.exe" (
        echo [OK] Found Python: %%d:\anaconda\envs\gis_ai\python.exe
        set "PYTHON_PATH=%%d:\anaconda\envs\gis_ai\python.exe"
        set PYTHON_FOUND=1
        goto :check_deps
    )
)

REM Check user profile paths
if exist "%USERPROFILE%\anaconda3\envs\gis_ai\python.exe" (
    echo [OK] Found Python: %USERPROFILE%\anaconda3\envs\gis_ai\python.exe
    set PYTHON_PATH=%USERPROFILE%\anaconda3\envs\gis_ai\python.exe
    set PYTHON_FOUND=1
    goto :check_deps
)

if exist "%USERPROFILE%\miniconda3\envs\gis_ai\python.exe" (
    echo [OK] Found Python: %USERPROFILE%\miniconda3\envs\gis_ai\python.exe
    set PYTHON_PATH=%USERPROFILE%\miniconda3\envs\gis_ai\python.exe
    set PYTHON_FOUND=1
    goto :check_deps
)

REM Check system paths
if exist "C:\ProgramData\Anaconda3\envs\gis_ai\python.exe" (
    echo [OK] Found Python: C:\ProgramData\Anaconda3\envs\gis_ai\python.exe
    set PYTHON_PATH=C:\ProgramData\Anaconda3\envs\gis_ai\python.exe
    set PYTHON_FOUND=1
    goto :check_deps
)

REM Try conda command (only works in Anaconda Prompt)
call conda env list 2>nul | findstr "gis_ai" >nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Found conda environment: gis_ai
    echo [INFO] Activating environment...
    call conda activate gis_ai 2>nul
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_FOUND=1
        goto :check_deps
    )
)

if %PYTHON_FOUND% EQU 0 (
    echo [ERROR] gis_ai Python environment not found!
    echo.
    echo Please run setup_env.bat first, or create manually:
    echo   conda create -n gis_ai python=3.10
    echo   conda activate gis_ai
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

:check_deps
echo.
echo [2/4] Checking core dependencies...
echo.

REM Check if streamlit is installed
if defined PYTHON_PATH (
    %PYTHON_PATH% -c "import streamlit" 2>nul
) else (
    python -c "import streamlit" 2>nul
)

if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Missing dependencies, installing...
    echo.
    if defined PYTHON_PATH (
        %PYTHON_PATH% -m pip install -r "%~dp0requirements.txt"
    ) else (
        pip install -r "%~dp0requirements.txt"
    )
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [ERROR] Dependency installation failed!
        echo Please check network connection or install manually.
        pause
        exit /b 1
    )
    echo.
    echo [OK] Dependencies installed
) else (
    echo [OK] Core dependencies ready (streamlit, pandas, torch, ...)
)

:launch
echo.
echo [3/4] Starting application...
echo.

REM Check for available port (start from 8501)
set SERVER_PORT=8501
set MAX_RETRIES=10
set RETRY_COUNT=0

:check_port
netstat -ano | findstr ":%SERVER_PORT% " | findstr "LISTENING" >nul
if %ERRORLEVEL% EQU 0 (
    set /a RETRY_COUNT+=1
    if !RETRY_COUNT! GEQ !MAX_RETRIES! (
        echo [ERROR] No available port found after !MAX_RETRIES! attempts!
        pause
        exit /b 1
    )
    set /a SERVER_PORT+=1
    echo [WARN] Port !SERVER_PORT! in use, trying next...
    goto :check_port
)

if %RETRY_COUNT% GTR 0 (
    echo [OK] Auto-switched to port: !SERVER_PORT!
) else (
    echo [OK] Using default port: !SERVER_PORT!
)

echo.
echo ----------------------------------------------------------------
echo   Browser will open: http://localhost:!SERVER_PORT!
echo   Modules: Data ^| Twin ^| AIGC ^| LLM
echo   Port: !SERVER_PORT!
echo ----------------------------------------------------------------
echo.

REM Start Streamlit with detected port
if defined PYTHON_PATH (
    %PYTHON_PATH% -m streamlit run "%~dp0app.py" --server.headless true --server.port !SERVER_PORT!
) else (
    streamlit run "%~dp0app.py" --server.headless true --server.port !SERVER_PORT!
)

echo.
echo ================================================================
echo   Application exited
echo ================================================================
echo.
pause
