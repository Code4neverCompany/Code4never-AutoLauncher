#define MyAppName "Code4never-AutoLauncher"
#define MyAppVersion "1.8.5"
#define MyAppPublisher "4never Company"
#define MyAppURL "https://github.com/Code4neverCompany/Code4never-AutoLauncher"
#define MyAppExeName "Autolauncher.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{D416E986-5383-49BD-9214-411358914041}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={userpf}\Autolauncher
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
OutputBaseFilename=c4n-AutoLauncher_Setup_v1.8.5
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\Autolauncher\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{app}\unins000.exe"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
