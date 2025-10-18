; Inno Setup Script for Multi-Drive Cloud Manager
; Requires Inno Setup 6.x (http://www.jrsoftware.org/isinfo.php)

#define MyAppName "Multi-Drive Cloud Manager"
#define MyAppVersion "3.0.4"
#define MyAppPublisher "Jagyaa"
#define MyAppURL "https://example.com"
#define MyAppExeName "MultiDriveCloudManager.exe"

[Setup]
AppId={{A1F8D2E0-76E1-4E2E-9E2A-0A9A8B6E7C11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={localappdata}\{#MyAppName}
DisableDirPage=no
PrivilegesRequired=lowest
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no
Compression=lzma
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=MultiDriveCloudManager_Setup_{#MyAppVersion}
ArchitecturesInstallIn64BitMode=x64
; SetupIconFile=..\assets\app.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; Main application files (PyInstaller creates a folder with EXE and _internal subfolder)
; Copy the entire dist\MultiDriveCloudManager folder contents (EXE + _internal folder with DLLs)
Source: "..\dist\MultiDriveCloudManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Rclone binary if you bundle it (optional). Place rclone.exe into build\bin before compiling installer
Source: "..\build\bin\rclone.exe"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; Resource folders (NOT config - users should have their own clean config)
Source: "..\docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs

; Optional: License file
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
// Ensure user config dirs exist on first run
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then begin
    if not DirExists(ExpandConstant('{app}\\manifests')) then
      CreateDir(ExpandConstant('{app}\\manifests'));
    if not DirExists(ExpandConstant('{app}\\chunks')) then
      CreateDir(ExpandConstant('{app}\\chunks'));
    if not DirExists(ExpandConstant('{app}\\downloads')) then
      CreateDir(ExpandConstant('{app}\\downloads'));
  end;
end;
