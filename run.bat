@echo off
title Multi-modal Micro-renewal Decision Support System
echo ========================================
echo   Multi-modal Micro-renewal Decision Support System
echo ========================================
echo.

echo [System] Activating Conda environment: gis_ai ...

call conda activate gis_ai >nul 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [System] Conda not in PATH, searching for activate.bat...
    if exist "E:\anaconda\Scripts\activate.bat" (
        call "E:\anaconda\Scripts\activate.bat" gis_ai
    ) else if exist "%USERPROFILE%\anaconda3\Scripts\activate.bat" (
        call "%USERPROFILE%\anaconda3\Scripts\activate.bat" gis_ai
    ) else if exist "%USERPROFILE%\miniconda3\Scripts\activate.bat" (
        call "%USERPROFILE%\miniconda3\Scripts\activate.bat" gis_ai
    ) else if exist "C:\ProgramData\Anaconda3\Scripts\activate.bat" (
        call "C:\ProgramData\Anaconda3\Scripts\activate.bat" gis_ai
    ) else if exist "D:\anaconda3\Scripts\activate.bat" (
        call "D:\anaconda3\Scripts\activate.bat" gis_ai
    ) else if exist "C:\ProgramData\miniconda3\Scripts\activate.bat" (
        call "C:\ProgramData\miniconda3\Scripts\activate.bat" gis_ai
    ) else if exist "%USERPROFILE%\.ai-navigator\micromamba\envs\condabin\activate.bat" (
        call "%USERPROFILE%\.ai-navigator\micromamba\envs\condabin\activate.bat" gis_ai
    ) else (
        echo [Error] Could not find Conda installation path. Please run this in Anaconda Prompt or add Conda to PATH.
    )
)

echo.
echo [System] Environment is ready. Starting Streamlit...
echo.

cd /d "%~dp0"
streamlit run app.py

pause
