@echo off
title Multi-modal Micro-renewal Decision Support System
echo ========================================
echo   Starting Application...
echo ========================================
echo.

REM Use existing Conda gis_ai environment
echo [System] Using Conda environment: gis_ai
echo [Python] 自动检测 Python 路径
echo.

REM Start Streamlit using conda run
call conda run -n gis_ai streamlit run "%~dp0app.py"

pause
