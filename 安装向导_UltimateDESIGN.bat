@echo off
title UltimateDESIGN 安装向导

:: 检查是否以管理员权限运行
net session >nul 2>&1
if %errorLevel% == 0 (
    goto run_installer
) else (
    echo =======================================================
    echo [提示] 正在请求管理员权限以创建桌面快捷方式...
    echo =======================================================
    powershell -Command "Start-Process -FilePath '%0' -Verb RunAs"
    exit /b
)

:run_installer
color 0B
echo.
echo ========================================================
echo   欢迎使用 UltimateDESIGN 便携版安装向导
echo ========================================================
echo.
echo 本程序将帮助您：
echo 1. 验证便携式 Python 运行环境
echo 2. 在桌面生成一键启动快捷方式
echo.
pause

set TARGET_DIR=%~dp0
set WINPYTHON_DIR=%TARGET_DIR%WinPython

echo.
echo [1/3] 正在验证环境完整性...
if not exist "%WINPYTHON_DIR%\python\python.exe" (
    color 0C
    echo [错误] 未找到便携式环境：WinPython
    echo 请确认您已经执行了重装脚本。
    pause
    exit /b 1
)
echo [OK] 便携版环境验证通过！

echo.
echo [2/3] 正在配置系统路径...
set LAUNCHER_PATH=%TARGET_DIR%启动_UltimateDESIGN.bat
if not exist "%LAUNCHER_PATH%" (
    color 0C
    echo [错误] 未找到启动脚本！
    pause
    exit /b 1
)
echo [OK] 启动脚本路径已定位。

echo.
echo [3/3] 正在生成桌面快捷方式...
set SHORTCUT_NAME=UltimateDESIGN.lnk
set SHORTCUT_PATH=%USERPROFILE%\Desktop\%SHORTCUT_NAME%

powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%LAUNCHER_PATH%'; $Shortcut.WorkingDirectory = '%TARGET_DIR%'; $Shortcut.IconLocation = '%WINPYTHON_DIR%\python\python.exe,0'; $Shortcut.Save()"

if exist "%SHORTCUT_PATH%" (
    echo [OK] 桌面快捷方式创建成功！
) else (
    color 0E
    echo [警告] 桌面快捷方式创建失败，请尝试手动创建。
)

echo.
echo ========================================================
echo   安装完成！
echo   现在您可以直接双击桌面上的 [UltimateDESIGN] 图标来运行软件了！
echo ========================================================
echo.
pause
