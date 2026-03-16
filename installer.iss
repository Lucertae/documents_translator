; ==========================================================================
; LAC Translate — Inno Setup Installer Script
;
; Prerequisiti:
;   1. PyInstaller ha gia' generato  dist\lac-translate\  con l'exe + DLL
;   2. Inno Setup 6.x installato (https://jrsoftware.org/isinfo.php)
;
; Compilare con:
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
; ==========================================================================

#define MyAppName      "LAC Translate"
#define MyAppVersion   "1.2.0"
#define MyAppPublisher "LUCERTAE SRLS"
#define MyAppExeName   "lac-translate.exe"
#define MyAppURL       "https://github.com/Lucertae/documents_translator"

[Setup]
; Identificativo univoco dell'app (generato una volta, NON cambiare mai)
AppId={{7A3D9B2E-4F1C-4E8A-B6D0-2C5A8F3E7D1B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; Nessun permesso elevato richiesto — installa per l'utente corrente
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Cartella output per il Setup.exe compilato
OutputDir=dist
OutputBaseFilename=LAC-Translate-Setup-{#MyAppVersion}
; Icona dell'installer
SetupIconFile=assets\icon.ico
; Compressione (lzma2: ottimo rapporto dimensione/velocita')
Compression=lzma2/ultra64
SolidCompression=yes
; UI
WizardStyle=modern
WizardSizePercent=110,110
; Il programma non e' piccolo — disabilitiamo la stima tempo
DisableFinishedPage=no
DisableWelcomePage=no
; Info importanti
LicenseFile=
InfoBeforeFile=
; Piattaforma
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Versione minima Windows
MinVersion=10.0
; Disinstallazione pulita
Uninstallable=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
; Evita sovrascrivere configurazioni utente
ChangesEnvironment=no

[Languages]
Name: "italian";   MessagesFile: "compiler:Languages\Italian.isl"
Name: "english";   MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";  Description: "Crea un'icona sul &Desktop";  GroupDescription: "Icone aggiuntive:"; Flags: unchecked
Name: "startmenu";    Description: "Crea un collegamento nel menu &Start"; GroupDescription: "Icone aggiuntive:"; Flags: checked

[Files]
; Tutta la cartella di output di PyInstaller
Source: "dist\lac-translate\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}";                Filename: "{app}\{#MyAppExeName}"; Tasks: startmenu
Name: "{group}\Disinstalla {#MyAppName}";     Filename: "{uninstallexe}";        Tasks: startmenu
Name: "{autodesktop}\{#MyAppName}";           Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Lancia l'app alla fine dell'installazione (opzionale)
Filename: "{app}\{#MyAppExeName}"; Description: "Avvia {#MyAppName}"; Flags: nowait postinstall skipifsilent
