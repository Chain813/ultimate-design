@echo off
setlocal enabledelayedexpansion
title Micro-Renewal Decision Platform (Desktop App)
color 0B

echo.
echo ================================================================
echo   Multi-modal Micro-renewal Decision Support System
echo   Changchun Pseudo-Manchu Palace District (Desktop Mode)
echo ================================================================
echo.

REM ==========================================
REM Step 1: Check Python Environment (with caching)
REM ==========================================
echo [1/3] Checking Python environment...
echo.

set PYTHON_FOUND=0
set CACHE_FILE=%~dp0.python_path

REM Check cache first
if exist "%CACHE_FILE%" (
    set /p PYTHON_PATH=<"%CACHE_FILE%"
    if exist "!PYTHON_PATH!" (
        echo [OK] Found cached Python: !PYTHON_PATH!
        set PYTHON_FOUND=1
        goto :check_deps
    ) else (
        echo [INFO] Cached path invalid, rescanning...
        del "%CACHE_FILE%" 2>nul
    )
)

REM Check for Anaconda in common locations
for %%d in (E F D G H I J K L) do (
    if exist "%%d:\anaconda3\envs\gis_ai\python.exe" (
        echo [OK] Found Python: %%d:\anaconda3\envs\gis_ai\python.exe
        set "PYTHON_PATH=%%d:\anaconda3\envs\gis_ai\python.exe"
        set PYTHON_FOUND=1
        echo !PYTHON_PATH!>"%CACHE_FILE%"
        goto :check_deps
    )
    if exist "%%d:\anaconda\envs\gis_ai\python.exe" (
        echo [OK] Found Python: %%d:\anaconda\envs\gis_ai\python.exe
        set "PYTHON_PATH=%%d:\anaconda\envs\gis_ai\python.exe"
        set PYTHON_FOUND=1
        echo !PYTHON_PATH!>"%CACHE_FILE%"
        goto :check_deps
    )
)

REM Check user profile paths
if exist "%USERPROFILE%\anaconda3\envs\gis_ai\python.exe" (
    echo [OK] Found Python: %USERPROFILE%\anaconda3\envs\gis_ai\python.exe
    set PYTHON_PATH=%USERPROFILE%\anaconda3\envs\gis_ai\python.exe
    set PYTHON_FOUND=1
    echo !PYTHON_PATH!>"%CACHE_FILE%"
    goto :check_deps
)

if exist "%USERPROFILE%\miniconda3\envs\gis_ai\python.exe" (
    echo [OK] Found Python: %USERPROFILE%\miniconda3\envs\gis_ai\python.exe
    set PYTHON_PATH=%USERPROFILE%\miniconda3\envs\gis_ai\python.exe
    set PYTHON_FOUND=1
    echo !PYTHON_PATH!>"%CACHE_FILE%"
    goto :check_deps
)

REM Try conda command
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
    echo Please run scripts\setup_env.bat first, or create manually.
    echo.
    pause
    exit /b 1
)

:check_deps
echo.
echo [2/3] Checking core dependencies...
echo.

if defined PYTHON_PATH (
    %PYTHON_PATH% -c "import webview" 2>nul
) else (
    python -c "import webview" 2>nul
)

if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Missing pywebview dependency, installing...
    echo.
    if defined PYTHON_PATH (
        %PYTHON_PATH% -m pip install pywebview
    ) else (
        pip install pywebview
    )
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [ERROR] pywebview installation failed!
        pause
        exit /b 1
    )
) else (
    echo [OK] Desktop wrapper dependencies ready (pywebview)
)

:launch
echo.
echo [3/3] Starting Desktop Application...
echo ----------------------------------------------------------------
echo   Launching client window...
echo   Close the window to stop the server automatically.
echo ----------------------------------------------------------------
echo.

if defined PYTHON_PATH (
    %PYTHON_PATH% "%~dp0run_desktop.py"
) else (
    python "%~dp0run_desktop.py"
)

echo.
echo ================================================================
echo   Application exited
echo ================================================================
echo.
pause
