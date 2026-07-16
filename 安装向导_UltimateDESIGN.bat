@echo off
chcp 65001 >nul
title UltimateDESIGN 安装向导

:: 检查是否以管理员权限运行（部分目录和开始菜单可能需要管理员权限）
net session >nul 2>&1
if %errorLevel% == 0 (
    goto run_installer
) else (
    echo =======================================================
    echo 请右键点击此文件，选择 "以管理员身份运行" 
    echo =======================================================
    pause
    exit /b
)

:run_installer
echo 正在启动图形化安装向导...

set "PS_SCRIPT=%TEMP%\UD_Installer.ps1"

:: 动态生成 PowerShell GUI 脚本
> "%PS_SCRIPT%" (
echo Add-Type -AssemblyName System.Windows.Forms
echo Add-Type -AssemblyName System.Drawing
echo.
echo $form = New-Object System.Windows.Forms.Form
echo $form.Text = "UltimateDESIGN 安装程序"
echo $form.Size = New-Object System.Drawing.Size^(420,260^)
echo $form.StartPosition = "CenterScreen"
echo $form.FormBorderStyle = "FixedDialog"
echo $form.MaximizeBox = $false
echo.
echo $label = New-Object System.Windows.Forms.Label
echo $label.Location = New-Object System.Drawing.Point^(20,20^)
echo $label.Size = New-Object System.Drawing.Size^(300,20^)
echo $label.Text = "请选择安装路径 (目标文件夹将被创建):"
echo $form.Controls.Add^($label^)
echo.
echo $pathBox = New-Object System.Windows.Forms.TextBox
echo $pathBox.Location = New-Object System.Drawing.Point^(20,40^)
echo $pathBox.Size = New-Object System.Drawing.Size^(280,20^)
echo $pathBox.Text = "C:\UltimateDESIGN"
echo $form.Controls.Add^($pathBox^)
echo.
echo $browseBtn = New-Object System.Windows.Forms.Button
echo $browseBtn.Location = New-Object System.Drawing.Point^(310,38^)
echo $browseBtn.Size = New-Object System.Drawing.Size^(70,23^)
echo $browseBtn.Text = "浏览..."
echo $browseBtn.Add_Click^{
echo     $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
echo     if^($dialog.ShowDialog^(^) -eq 'OK'^) ^{
echo         $pathBox.Text = $dialog.SelectedPath + "\UltimateDESIGN"
echo     ^}
echo ^}
echo $form.Controls.Add^($browseBtn^)
echo.
echo $checkDesktop = New-Object System.Windows.Forms.CheckBox
echo $checkDesktop.Location = New-Object System.Drawing.Point^(20,80^)
echo $checkDesktop.Size = New-Object System.Drawing.Size^(200,20^)
echo $checkDesktop.Text = "创建桌面快捷方式"
echo $checkDesktop.Checked = $true
echo $form.Controls.Add^($checkDesktop^)
echo.
echo $checkStartMenu = New-Object System.Windows.Forms.CheckBox
echo $checkStartMenu.Location = New-Object System.Drawing.Point^(20,110^)
echo $checkStartMenu.Size = New-Object System.Drawing.Size^(200,20^)
echo $checkStartMenu.Text = "添加到开始菜单"
echo $checkStartMenu.Checked = $true
echo $form.Controls.Add^($checkStartMenu^)
echo.
echo $installBtn = New-Object System.Windows.Forms.Button
echo $installBtn.Location = New-Object System.Drawing.Point^(150,170^)
echo $installBtn.Size = New-Object System.Drawing.Size^(100,30^)
echo $installBtn.Text = "开始安装"
echo $installBtn.Add_Click^{
echo     $installPath = $pathBox.Text
echo     $form.DialogResult = [System.Windows.Forms.DialogResult]::OK
echo     $form.Close^(^)
echo     
echo     # 传参回 BAT
echo     [System.IO.File]::WriteAllText^("$TEMP\UD_InstallParams.txt", "$installPath`n$($checkDesktop.Checked)`n$($checkStartMenu.Checked)"^)
echo ^}
echo $form.Controls.Add^($installBtn^)
echo.
echo $form.ShowDialog^(^) ^| Out-Null
)

:: 执行 PowerShell 脚本
powershell -ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File "%PS_SCRIPT%"

:: 读取用户选择
if not exist "%TEMP%\UD_InstallParams.txt" (
    echo 用户取消了安装。
    exit /b
)

setlocal EnableDelayedExpansion
set /a line=1
for /f "usebackq delims=" %%A in ("%TEMP%\UD_InstallParams.txt") do (
    if !line!==1 set "INSTALL_PATH=%%A"
    if !line!==2 set "MAKE_DESKTOP=%%A"
    if !line!==3 set "MAKE_START=%%A"
    set /a line+=1
)
del "%TEMP%\UD_InstallParams.txt"
del "%PS_SCRIPT%"

if "%INSTALL_PATH%"=="" exit /b

echo =======================================================
echo 开始部署文件到: %INSTALL_PATH%
echo 正在复制文件 (此过程可能需要几分钟，请耐心等待...)
echo =======================================================

:: 创建目录
mkdir "%INSTALL_PATH%" 2>nul

:: 使用 robocopy 复制文件，排除缓存和无用文件
robocopy "%~dp0." "%INSTALL_PATH%" /E /R:1 /W:1 /NFL /NDL /XD .git __pycache__ .pytest_cache /XF .gitignore *.pyc
echo 文件复制完成！

:: 使用 PowerShell 生成快捷方式
set "SHORTCUT_PS=%TEMP%\UD_Shortcut.ps1"
> "%SHORTCUT_PS%" (
echo $WshShell = New-Object -comObject WScript.Shell
echo if ('%MAKE_DESKTOP%' -eq 'True') {
echo     $DesktopPath = [Environment]::GetFolderPath('Desktop')
echo     $Shortcut = $WshShell.CreateShortcut("$DesktopPath\UltimateDESIGN.lnk")
echo     $Shortcut.TargetPath = "%INSTALL_PATH%\启动_UltimateDESIGN.bat"
echo     $Shortcut.WorkingDirectory = "%INSTALL_PATH%"
echo     $Shortcut.Description = "Urban Platform Decision Support"
echo     $Shortcut.IconLocation = "%INSTALL_PATH%\assets\favicon.ico"
echo     $Shortcut.Save()
echo }
echo if ('%MAKE_START%' -eq 'True') {
echo     $StartMenuPath = [Environment]::GetFolderPath('CommonStartMenu')
echo     $ShortcutDir = "$StartMenuPath\Programs\UltimateDESIGN"
echo     New-Item -ItemType Directory -Force -Path $ShortcutDir ^| Out-Null
echo     $Shortcut = $WshShell.CreateShortcut("$ShortcutDir\UltimateDESIGN.lnk")
echo     $Shortcut.TargetPath = "%INSTALL_PATH%\启动_UltimateDESIGN.bat"
echo     $Shortcut.WorkingDirectory = "%INSTALL_PATH%"
echo     $Shortcut.Description = "Urban Platform Decision Support"
echo     $Shortcut.IconLocation = "%INSTALL_PATH%\assets\favicon.ico"
echo     $Shortcut.Save()
echo }
)
powershell -ExecutionPolicy Bypass -NoProfile -File "%SHORTCUT_PS%"
del "%SHORTCUT_PS%"

echo.
echo =======================================================
echo 安装成功！
echo 快捷方式已创建，您现在可以通过桌面或开始菜单启动平台。
echo =======================================================
pause
