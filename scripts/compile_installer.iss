; Inno Setup Script for UltimateDESIGN
; Compile command: ISCC.exe scripts/compile_installer.iss

[Setup]
AppName=UltimateDESIGN
AppVersion=1.0.0
AppPublisher=UltimateDESIGN Team
DefaultDirName={localappdata}\UltimateDESIGN
DefaultGroupName=UltimateDESIGN
DisableProgramGroupPage=yes
OutputBaseFilename=UltimateDESIGN_Setup
OutputDir=..\dist
Compression=lzma2/max
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
DisableWelcomePage=no
DisableDirPage=auto

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Project source files, excluding temp, git, env and dist folders
Source: "..\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs; Excludes: ".git\*,.github\*,.idea\*,.venv\*,.runtime-packages\*,.pytest_cache\*,.ruff_cache\*,.env,.python_path,*.log,dist\*,ultimate_design_skeleton.zip,scripts\install_inno_setup.ps1,scripts\build_portable_env.py,scratch\*,tests\*,logs\*,output\*,tools\*,__pycache__\*,.claude\*,.codegraph\*,.gemini\*,.superpowers\*"

; Portable Python environment files
Source: "..\dist\python_embed\*"; DestDir: "{app}\python_embed"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\UltimateDESIGN"; Filename: "{app}\python_embed\pythonw.exe"; Parameters: "run_desktop.py"; WorkingDir: "{app}"; IconFilename: "{app}\python_embed\pythonw.exe"; IconIndex: 0
Name: "{userdesktop}\UltimateDESIGN"; Filename: "{app}\python_embed\pythonw.exe"; Parameters: "run_desktop.py"; WorkingDir: "{app}"; IconFilename: "{app}\python_embed\pythonw.exe"; IconIndex: 0; Tasks: desktopicon

[Run]
Filename: "{app}\python_embed\pythonw.exe"; Description: "运行 UltimateDESIGN"; Parameters: "run_desktop.py"; WorkingDir: "{app}"; Flags: postinstall nowait skipifsilent
