#ifndef BioGuardProjectRoot
#define BioGuardProjectRoot SourcePath + "\..\.."
#endif
#define ServiceName "BioGuardAuthority"
#define ServiceExe "BioGuardService.exe"
#define ServiceVersion Trim(FileRead(FileOpen(BioGuardProjectRoot + "\releases\windows\VERSION")))

[Setup]
AppId={{C174844B-E807-4A54-A9AD-FD4A12F285D3}
AppName=BioGuard Authority disposable VM test
AppVersion={#ServiceVersion}
DefaultDirName={autopf}\{#ServiceName}
DisableDirPage=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0
OutputDir={#BioGuardProjectRoot}\installer_output
OutputBaseFilename=BioGuard_Service_VM_v{#ServiceVersion}
AllowCancelDuringInstall=yes
CloseApplications=yes
CloseApplicationsFilter={#ServiceExe}
UninstallDisplayName=BioGuard Authority VM test (not login enforcement)

[Files]
Source: "{#BioGuardProjectRoot}\dist\BioGuardService\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Code]
function InitializeSetup(): Boolean;
begin
  Result := MsgBox('DISPOSABLE WINDOWS VM ONLY. This package does not enforce Windows login MFA. Keep a VM snapshot and administrator console. Continue?', mbConfirmation, MB_YESNO) = IDYES;
end;

function ServiceCommand(Command: String): Boolean;
var ExitCode: Integer;
begin
  Result := Exec(ExpandConstant('{app}\{#ServiceExe}'), Command + ' --vm-test', '', SW_HIDE, ewWaitUntilTerminated, ExitCode);
  if Result then Result := ExitCode = 0;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var ExitCode: Integer;
begin
  Result := '';
  // Never copy over an installed/running service. Require explicit removal so
  // a failed update cannot silently mix old binaries with a new runtime.
  if Exec(ExpandConstant('{sys}\sc.exe'), 'query {#ServiceName}', '', SW_HIDE, ewWaitUntilTerminated, ExitCode) then
    if ExitCode = 0 then
      Result := 'BioGuardAuthority already exists. Cancel, snapshot the VM, remove the old VM service, and then install. In-place upgrade is not yet supported.';
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if not ServiceCommand('install') then
      RaiseException('Service installation failed; no partially configured service should remain. Restore the VM snapshot if rollback fails.');
    if not ServiceCommand('start') then
    begin
      ServiceCommand('remove');
      RaiseException('Service start failed. Service removal attempted; restore the VM snapshot if necessary.');
    end;
  end;
end;

function InitializeUninstall(): Boolean;
var ExitCode: Integer;
begin
  Result := True;
  // Stop before deleting dependencies; do not kill unrelated processes.
  ServiceCommand('stop');
  if not Exec(ExpandConstant('{sys}\sc.exe'), 'query {#ServiceName}', '', SW_HIDE, ewWaitUntilTerminated, ExitCode) then
  begin Result := False; Exit; end;
  if ExitCode = 0 then
    Result := ServiceCommand('remove');
  if not Result then MsgBox('Cannot remove service. Files retained. Recover using the VM administrator console.', mbError, MB_OK);
end;
