@echo off
:: Portable launcher for ultimateDESIGN using embedded python environment.
:: Runs the application via run_desktop.py silently.

cd /d "%~dp0"
if exist "python_embed\pythonw.exe" (
    start "" "python_embed\pythonw.exe" "run_desktop.py"
) else (
    echo [ERROR] Portable python environment not found at python_embed.
    echo Please make sure you are in the application root directory.
    pause
)
