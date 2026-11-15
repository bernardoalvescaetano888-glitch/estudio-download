; Inno Setup — instalador do Estúdio do Cantor (Windows)
[Setup]
AppName=Estudio do Cantor
AppVersion=1.0.0
AppPublisher=Estudio do Cantor
DefaultDirName={autopf}\EstudioDoCantor
DefaultGroupName=Estudio do Cantor
OutputBaseFilename=EstudioDoCantor-Setup
OutputDir=output
Compression=lzma2/max
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest

[Files]
Source: "dist\EstudioDoCantor\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Estudio do Cantor"; Filename: "{app}\EstudioDoCantor.exe"
Name: "{autodesktop}\Estudio do Cantor"; Filename: "{app}\EstudioDoCantor.exe"

[Run]
Filename: "{app}\EstudioDoCantor.exe"; Description: "Abrir o Estúdio do Cantor"; Flags: postinstall nowait skipifsilent
