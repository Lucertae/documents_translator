; LAC TRANSLATE - InnoSetup Installer Script
; Crea installer Windows professionale

#define MyAppName "LAC TRANSLATE"
#define MyAppVersion "2.0"
#define MyAppPublisher "LAC Software"
#define MyAppURL "https://www.lactranslate.com"
#define MyAppExeName "LAC_Translate.exe"
#define MyAppId "{{12345678-1234-1234-1234-123456789ABC}"

[Setup]
; NOTE: Il valore di AppId identifica in modo univoco questa applicazione
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/support
AppUpdatesURL={#MyAppURL}/updates
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
; Rimuovi la riga seguente se non vuoi che l'installazione richieda privilegi amministratore
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=release\installer
OutputBaseFilename=LAC_Translate_v{#MyAppVersion}_Setup
SetupIconFile=logo_alt.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
DisableWelcomePage=no
DisableReadyPage=no
DisableFinishedPage=no

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "english"; MessagesFile: "compiler:Languages\English.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "startmenu"; Description: "Crea voci nel menu Start"; GroupDescription: "Opzioni installazione"; Flags: checkedonce

[Files]
; Eseguibile principale
Source: "dist\LAC_Translate.exe"; DestDir: "{app}"; Flags: ignoreversion
; Documentazione
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion; DestName: "README.txt"
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
; Directory config e license
; NOTE: Non copiare i file, verranno creati al primo avvio
; Source: "config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs
; Source: "license\*"; DestDir: "{app}\license"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
procedure InitializeWizard();
begin
  // Personalizzazione wizard
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  // Verifica prerequisiti qui se necessario
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Azioni post-installazione
  end;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}\config"
Type: filesandordirs; Name: "{app}\license"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\output"

[Registry]
; Associazione file PDF opzionale (commentata - da abilitare se necessario)
; Root: HKCR; Subkey: ".pdf\OpenWithProgIds"; ValueType: string; ValueName: "LACTranslateFile"; ValueData: ""; Flags: uninsdeletevalue
; Root: HKCR; Subkey: "LACTranslateFile"; ValueType: string; ValueData: "LAC TRANSLATE Document"; Flags: uninsdeletekey
; Root: HKCR; Subkey: "LACTranslateFile\DefaultIcon"; ValueType: string; ValueData: "{app}\{#MyAppExeName},0"
; Root: HKCR; Subkey: "LACTranslateFile\shell\open\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

