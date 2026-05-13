; Inno Setup script para JORGE - Books to Woocommerce
; Requiere que exista dist\JORGE-Books-to-Woocommerce\

#define MyAppName "JORGE - Books to Woocommerce"
#define MyAppVersion "1.0.2 Beta"
#define MyAppPublisher "JORGE Team"
#define MyAppURL "https://agency.wham-vintage.com"
#define MyAppExeName "JORGE-Books-to-Woocommerce.exe"

[Setup]
AppId={{8DAA79CA-4E96-4F63-B3F2-2EB0C2FE37FB}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\JORGE Books to Woocommerce
DisableProgramGroupPage=yes
OutputDir=..\..\..\dist-installer\windows
OutputBaseFilename=JORGE-Books-to-Woocommerce-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
; SetupIconFile=..\..\assets\app-icon-win.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear icono en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Files]
Source: "..\..\..\dist\JORGE-Books-to-Woocommerce\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\JORGE - Books to Woocommerce"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\JORGE - Books to Woocommerce"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Ejecutar JORGE - Books to Woocommerce"; Flags: nowait postinstall skipifsilent
