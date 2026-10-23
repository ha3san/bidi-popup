; Inno Setup script — builds BidiPopup-Setup.exe from PyInstaller onedir output.
; Expected layout on the build machine:
;   dist\BidiPopup\BidiPopup.exe  (+ deps)

#define MyAppName "Bidi Popup"
#define MyAppVersion "1.2.1"
#define MyAppPublisher "ha3san"
#define MyAppURL "https://github.com/ha3san/bidi-popup"
#define MyAppExeName "BidiPopup.exe"

[Setup]
AppId={{A7B3C9E1-4D2F-4B8A-9C1E-BidiPopupWin01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\..\LICENSE
OutputDir=..\..\dist
OutputBaseFilename=BidiPopup-Setup
SetupIconFile=..\..\assets\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked
Name: "autostart"; Description: "Start Bidi Popup when Windows starts"; GroupDescription: "Startup:"; Flags: checkedonce

[Files]
Source: "..\..\dist\BidiPopup\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
