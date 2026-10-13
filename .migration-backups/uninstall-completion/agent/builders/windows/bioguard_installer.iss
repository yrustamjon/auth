#ifndef BioGuardProjectRoot
#define BioGuardProjectRoot SourcePath + "\..\.."
#endif

; AD BioGuard — Inno Setup installer
; Inno Setup 6.6+ kerak (CreateCustomForm signature).

#define MyAppName      "AD BioGuard"
#ifndef MyAppVersion
#define MyAppVersion Trim(FileRead(FileOpen(BioGuardProjectRoot + "\releases\windows\VERSION")))
#endif
#define MyAppPublisher "AD Systems"
#define MyAppExeName   "BioGuard.exe"
#define MyBuildDir     BioGuardProjectRoot + "\dist\BioGuard"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\AD BioGuard
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=admin
OutputDir={#BioGuardProjectRoot}\installer_output
OutputBaseFilename=BioGuard_Setup_v{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
AllowCancelDuringInstall=yes
DisableWelcomePage=no
MinVersion=10.0
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
CloseApplications=yes
CloseApplicationsFilter=BioGuard.exe
DisableDirPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Desktop shortcut yaratish"; Flags: checkedonce

[Files]
Source: "{#BioGuardProjectRoot}\dist\BioGuardSupervisor.exe"; Flags: dontcopy
Source: "{#BioGuardProjectRoot}\builders\windows\recover-supervisor.cmd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#BioGuardProjectRoot}\dist\BioGuardSupervisor.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#BioGuardProjectRoot}\dist\BioGuardWatchdog.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#BioGuardProjectRoot}\dist\BioGuardLifecycle.exe"; Flags: dontcopy
Source: "{#BioGuardProjectRoot}\dist\BioGuardLifecycle.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}";       Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall BioGuard"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKU; Subkey: "{code:GetTargetUserSID}\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "ADBioGuard"; \
  ValueData: """{app}\BioGuardWatchdog.exe"""; Flags: uninsdeletevalue

Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; ValueName: "ADBioGuard"; Flags: deletevalue

Root: HKLM; Subkey: "SOFTWARE\AD BioGuard"; \
  ValueType: string; ValueName: "InstallPath"; \
  ValueData: "{app}"
Root: HKLM; Subkey: "SOFTWARE\AD BioGuard"; ValueType: string; ValueName: "TargetUserSID"; ValueData: "{code:GetTargetUserSID}"
Root: HKLM; Subkey: "SOFTWARE\AD BioGuard"; ValueType: string; ValueName: "RecoveryGeneration"; ValueData: "{code:GetRecoveryGeneration}"

[Run]
Filename: "{app}\BioGuardWatchdog.exe"; \
  Description: "AD BioGuard ni hozir ishga tushirish"; \
  Flags: nowait postinstall skipifsilent runasoriginaluser

[Code]

type
  NativeInt = Integer; // Inno Setup 6 builds a 32-bit setup process.

// Only nonsensitive process/pipe/path context is passed to the helper.
// Tokens travel through a local process-verified pipe, never through files/args.
function CreateFileW(Name: String; Access, Share: Cardinal; Security: NativeInt; Creation, Flags: Cardinal; Template: NativeInt): NativeInt;
external 'CreateFileW@kernel32.dll stdcall';
function CloseHandle(Handle: NativeInt): Boolean;
external 'CloseHandle@kernel32.dll stdcall';
function WriteFile(Handle: NativeInt; Buffer: String; Count: Cardinal; var Written: Cardinal; Overlapped: NativeInt): Boolean;
external 'WriteFile@kernel32.dll stdcall';
function ReadFile(Handle: NativeInt; Buffer: String; Count: Cardinal; var Read: Cardinal; Overlapped: NativeInt): Boolean;
external 'ReadFile@kernel32.dll stdcall';
function PeekNamedPipe(Handle: NativeInt; Buffer: NativeInt; Size: Cardinal; Read: NativeInt; var Available: Cardinal; Left: NativeInt): Boolean;
external 'PeekNamedPipe@kernel32.dll stdcall';
function GetNamedPipeServerProcessId(Handle: NativeInt; var PID: Cardinal): Boolean;
external 'GetNamedPipeServerProcessId@kernel32.dll stdcall';
function OpenProcess(Access: Cardinal; Inherit: Boolean; PID: Cardinal): NativeInt;
external 'OpenProcess@kernel32.dll stdcall';
function QueryFullProcessImageNameW(Handle: NativeInt; Flags: Cardinal; Buffer: String; var Size: Cardinal): Boolean;
external 'QueryFullProcessImageNameW@kernel32.dll stdcall';
function GetCurrentProcessId: Cardinal;
external 'GetCurrentProcessId@kernel32.dll stdcall';
function GetTickCount: Cardinal;
external 'GetTickCount@kernel32.dll stdcall';
function SetTimer(Window: HWND; ID: UINT_PTR; Interval: UINT; Callback: NativeInt): UINT_PTR;
external 'SetTimer@user32.dll stdcall';
function KillTimer(Window: HWND; ID: UINT_PTR): Boolean;
external 'KillTimer@user32.dll stdcall';
function PostMessageW(Window: HWND; Message: UINT; WParam: UINT_PTR; LParam: NativeInt): Boolean;
external 'PostMessageW@user32.dll stdcall';

var
  ActivationPage: TInputQueryWizardPage;
  ActivationStatus: TNewStaticText;
  ActivationButton: TNewButton;
  RemovalForm: TSetupForm;
  RemovalEntry: TNewEdit;
  RemovalStatus: TNewStaticText;
  RemovalButton, ResumeButton: TNewButton;
  PipeHandle: NativeInt;
  TimerID: UINT_PTR;
  PipeName, ExpectedHelper, BrokerState, OrganizationName, DeviceName, TargetUserSID, TargetUser: String;
  Waiting, UninstallMode, Closing, Polling, InspectSent, VerifyDone, VerificationInFlight, InstallBrokerStarted: Boolean;
  BrokerInstallPath: String;
  LastCommand, LastMessage: String;

function GetTargetUserSID(Param: String): String;
begin
  if TargetUserSID = '' then RaiseException('Target desktop identity unavailable.');
  Result := TargetUserSID;
end;

function GetRecoveryGeneration(Param: String): String;
begin
  Result := PipeName;
end;

function FieldAt(Value: String; Index: Integer): String;
var P, I: Integer;
begin
  for I := 0 to Index - 1 do begin
    P := Pos(#9, Value);
    if P = 0 then begin Result := ''; Exit; end;
    Delete(Value, 1, P);
  end;
  P := Pos(#9, Value);
  if P > 0 then Result := Copy(Value, 1, P - 1) else Result := Value;
end;

function ConnectBroker: Boolean;
var PID, Count: Cardinal; Process: NativeInt; ImagePath: String;
begin
  Result := PipeHandle <> 0;
  if Result then Exit;
  PipeHandle := CreateFileW('\\.\pipe\' + PipeName, $C0000000, 0, 0, 3, 0, 0);
  if PipeHandle = -1 then begin PipeHandle := 0; Result := False; Exit; end;
  Result := GetNamedPipeServerProcessId(PipeHandle, PID);
  if Result then begin
    Process := OpenProcess($1000, False, PID);
    Result := Process <> 0;
    if Result then begin
      Count := 32768;
      ImagePath := StringOfChar(#0, Count);
      Result := QueryFullProcessImageNameW(Process, 0, ImagePath, Count);
      if Result then Result := CompareText(Copy(ImagePath, 1, Count), ExpectedHelper) = 0;
      CloseHandle(Process);
    end;
  end;
  if not Result then begin CloseHandle(PipeHandle); PipeHandle := 0; end;
end;

function BrokerCommand(Command, Secret: String): Boolean;
var Buffer: String; Written: Cardinal;
begin
  Result := False;
  if Waiting or not ConnectBroker then Exit;
  Buffer := Command + #9 + Secret;
  Result := WriteFile(PipeHandle, Buffer, Length(Buffer) * 2, Written, 0);
  if Result then Result := Written = Length(Buffer) * 2;
  if Result then begin
    Waiting := True; LastCommand := Command;
    if Command = 'verify' then VerificationInFlight := True;
  end;
end;

procedure ReadReply;
var Available, Count: Cardinal; Buffer, SID: String;
begin
  if not Waiting or (PipeHandle = 0) then Exit;
  if not PeekNamedPipe(PipeHandle, 0, 0, 0, Available, 0) then begin
    BrokerState := 'error'; LastMessage := 'Helper bilan aloqa uzildi.'; Exit;
  end;
  if Available = 0 then Exit;
  if Available > 65536 then RaiseException('Invalid lifecycle response size');
  Buffer := StringOfChar(#0, 32768);
  if not ReadFile(PipeHandle, Buffer, 65536, Count, 0) then Exit;
  SetLength(Buffer, Count div 2);
  BrokerState := FieldAt(Buffer, 0);
  OrganizationName := FieldAt(Buffer, 1);
  DeviceName := FieldAt(Buffer, 2);
  SID := FieldAt(Buffer, 3);
  if (TargetUserSID <> '') and (SID <> TargetUserSID) then RaiseException('Desktop identity changed; operation refused.');
  TargetUserSID := SID;
  TargetUser := FieldAt(Buffer, 4);
  LastMessage := FieldAt(Buffer, 5);
  Waiting := False;
  if VerificationInFlight and (BrokerState <> 'pending') then begin
    VerifyDone := BrokerState = 'ready';
    VerificationInFlight := False;
  end;
end;

procedure RefreshControls;
begin
  if UninstallMode then begin
    if RemovalForm = nil then Exit;
    RemovalStatus.Caption := OrganizationName + #13#10 + DeviceName + #13#10 + TargetUser + #13#10 + LastMessage;
    RemovalButton.Enabled := (not Waiting) and (BrokerState <> 'pending');
    if BrokerState = 'checked' then RemovalButton.Caption := 'O''chirish' else RemovalButton.Caption := 'Tekshirish';
    if BrokerState = 'pending' then RemovalStatus.Caption := 'Server javobi kutilmoqda...';
    if BrokerState = 'approved' then begin
      RemovalButton.OnClick := nil;
      RemovalButton.ModalResult := mrOk;
      PostMessageW(RemovalButton.Handle, $F5, 0, 0); // BM_CLICK completes ShowModal.
    end;
    if BrokerState = 'removed' then begin
      RemovalStatus.Caption := 'Bu o''chirish yakunlangan. Yangi o''rnatishni o''chirish uchun yangi kod kerak.';
      RemovalButton.Enabled := False;
    end;
  end else begin
    if ActivationPage = nil then Exit;
    ActivationStatus.Caption := LastMessage;
    if BrokerState = 'ready' then ActivationStatus.Caption := 'Aktivatsiya faol: ' + OrganizationName + #13#10 + DeviceName + #13#10 + 'Windows user: ' + TargetUser;
    if BrokerState = 'pending' then ActivationStatus.Caption := 'Aktivatsiya tekshirilmoqda...';
    ActivationButton.Enabled := (not Waiting) and (BrokerState <> 'pending');
    if WizardForm.CurPageID = ActivationPage.ID then WizardForm.NextButton.Enabled := BrokerState = 'ready';
    if WizardForm.CurPageID = wpReady then WizardForm.NextButton.Enabled := VerifyDone and (BrokerState = 'ready');
  end;
end;

procedure PollBroker(Window: HWND; Message: UINT; ID: UINT_PTR; Tick: DWORD);
begin
  if Closing or Polling then Exit;
  Polling := True;
  try
    if ConnectBroker then begin
      ReadReply;
      if not Waiting then begin
        if not InspectSent then begin
          if UninstallMode then BrokerCommand('state', '') else BrokerCommand('inspect', '');
          InspectSent := True;
        end else if BrokerState = 'pending' then BrokerCommand('state', '');
      end;
      RefreshControls;
    end;
  finally Polling := False; end;
end;

procedure ActivationClick(Sender: TObject);
begin
  VerifyDone := False;
  if Trim(ActivationPage.Values[0]) <> '' then BrokerCommand('activate', ActivationPage.Values[0])
  else BrokerCommand('inspect', '');
  ActivationPage.Values[0] := '';
end;

function NewPipeName: String;
var Digest: String;
begin
  Digest := GetSHA256OfString(IntToStr(GetCurrentProcessId) + ':' + IntToStr(GetTickCount) + ':' + ExpandConstant('{tmp}'));
  Result := 'BioGuardLifecycle-' + Copy(Digest, 1, 8) + '-' + Copy(Digest, 9, 4) + '-' + Copy(Digest, 13, 4) + '-' + Copy(Digest, 17, 4) + '-' + Copy(Digest, 21, 12);
end;

function InitializeSetup: Boolean;
begin
  Result := not WizardSilent;
  if not Result then MsgBox('Interactive token activation is required.', mbError, MB_OK);
end;

procedure InitializeWizard;
begin
  PipeName := NewPipeName;
  ActivationPage := CreateInputQueryPage(wpWelcome, 'Aktivatsiya', 'Avval tashkilot tokenini tasdiqlang', 'Org tokenni kiriting yoki Ctrl+V bilan joylashtiring. Avvalgi aktivatsiya bo''lsa, uning holati ko''rsatiladi.');
  ActivationPage.Add('Org token:', True);
  ActivationButton := TNewButton.Create(WizardForm);
  ActivationButton.Parent := ActivationPage.Surface;
  ActivationButton.SetBounds(0, ScaleY(95), ScaleX(140), ScaleY(28));
  ActivationButton.Caption := 'Tekshirish';
  ActivationButton.OnClick := @ActivationClick;
  ActivationStatus := TNewStaticText.Create(WizardForm);
  ActivationStatus.Parent := ActivationPage.Surface;
  ActivationStatus.SetBounds(0, ScaleY(140), ActivationPage.SurfaceWidth, ScaleY(100));
  ActivationStatus.AutoSize := False;
  ActivationStatus.WordWrap := True;
  ActivationStatus.Caption := 'Helper ishga tushmoqda. Setupni oddiy Windows foydalanuvchisi sifatida oching.';
  ExtractTemporaryFile('BioGuardLifecycle.exe');
  ExpectedHelper := ExpandConstant('{tmp}\BioGuardLifecycle.exe');
end;

procedure CurPageChanged(CurPageID: Integer);
var ExitCode: Integer;
begin
  if CurPageID = ActivationPage.ID then begin
    if not InstallBrokerStarted then begin
      BrokerInstallPath := WizardDirValue;
      if not ExecAsOriginalUser(ExpectedHelper, '--broker install --pipe-name ' + PipeName + ' --parent-pid ' + IntToStr(GetCurrentProcessId) + ' --install-path "' + BrokerInstallPath + '"', '', SW_HIDE, ewNoWait, ExitCode) then RaiseException('Cannot start original-user activation helper');
      InstallBrokerStarted := True;
      TimerID := SetTimer(0, 0, 250, CreateCallback(@PollBroker));
    end;
    RefreshControls;
  end;
  if CurPageID = wpReady then begin
    VerifyDone := False;
    VerificationInFlight := False;
    if Waiting then ReadReply;
    if not BrokerCommand('verify', '') then LastMessage := 'Tayyorlik tekshiruvini qayta urining.';
    RefreshControls;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = ActivationPage.ID then Result := BrokerState = 'ready';
end;

function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo, MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
begin
  Result := 'Tashkilot: ' + OrganizationName + NewLine + 'Qurilma: ' + DeviceName + NewLine + 'Windows user: ' + TargetUser + NewLine + MemoDirInfo + NewLine + MemoTasksInfo;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var ExitCode: Integer;
begin
  Result := '';
  if (BrokerState <> 'ready') or not VerifyDone or (TargetUserSID = '') then Result := 'Aktivatsiya hali tasdiqlanmagan. Orqaga qayting va internet bilan qayta tekshiring.';
  if CompareText(WizardDirValue, BrokerInstallPath) <> 0 then Result := 'Installation directory changed after activation. Restart Setup.';
  if Result = '' then begin
    ExtractTemporaryFile('BioGuardSupervisor.exe');
    if not Exec(ExpandConstant('{tmp}\BioGuardSupervisor.exe'), 'stop', '', SW_HIDE, ewWaitUntilTerminated, ExitCode) or (ExitCode <> 0) then
      Result := 'Avvalgi kuzatuvchini to‘xtatib bo‘lmadi. Fayllar o‘zgartirilmagan.';
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var ExitCode: Integer;
begin
  if CurStep = ssPostInstall then begin
    if not Exec(ExpandConstant('{app}\BioGuardLifecycle.exe'), '--prepare-native-recovery --refresh-native-recovery --target-sid ' + TargetUserSID + ' --install-path "' + ExpandConstant('{app}') + '"', '', SW_HIDE, ewWaitUntilTerminated, ExitCode) or (ExitCode <> 0) then
      RaiseException('Recovery nusxasi tayyorlanmadi. Kuzatuvchi ishga tushirilmagan; setup yopilgach tiklashni tayyorlang.');
    if not Exec(ExpandConstant('{app}\BioGuardSupervisor.exe'), 'install', '', SW_HIDE, ewWaitUntilTerminated, ExitCode) or (ExitCode <> 0) then
      RaiseException('Kuzatuvchi xizmati o‘rnatilmadi. O‘rnatuvchini administrator sifatida qayta ishga tushiring.');
  end;
end;

procedure StopBroker;
begin
  Closing := True;
  if TimerID <> 0 then begin KillTimer(0, TimerID); TimerID := 0; end;
  if PipeHandle <> 0 then begin
    if not Waiting then BrokerCommand('cancel', '');
    CloseHandle(PipeHandle); PipeHandle := 0;
  end;
end;

procedure DeinitializeSetup;
begin
  StopBroker;
end;

procedure RemovalClick(Sender: TObject);
begin
  if BrokerState = 'checked' then begin
    BrokerCommand('begin', RemovalEntry.Text);
    RemovalEntry.Text := '';
  end else BrokerCommand('check', RemovalEntry.Text);
end;

procedure ResumeClick(Sender: TObject);
begin
  BrokerCommand('resume', '');
end;

function InitializeUninstall: Boolean;
var ExitCode: Integer; Launcher: String; CancelButton: TNewButton;
begin
  Result := False;
  if UninstallSilent then Exit;
  if not RegQueryStringValue(HKLM64, 'SOFTWARE\AD BioGuard', 'TargetUserSID', TargetUserSID) then begin
    MsgBox('Installed desktop identity is missing. Install the updated agent as its intended user before removing it.', mbError, MB_OK); Exit;
  end;
  UninstallMode := True;
  PipeName := NewPipeName;
  Launcher := ExpandConstant('{app}\BioGuardLifecycle.exe');
  if not FileExists(Launcher) then Launcher := ExpandConstant('{commonappdata}\AD BioGuard\native-removal\BioGuardLifecycle.exe');
  ExpectedHelper := ExpandConstant('{commonappdata}\AD BioGuard\lifecycle\') + PipeName + '\BioGuardLifecycle.exe';
  if not Exec(Launcher, '--launch-target-user --target-sid ' + TargetUserSID + ' --broker uninstall --pipe-name ' + PipeName + ' --parent-pid ' + IntToStr(GetCurrentProcessId) + ' --install-path "' + ExpandConstant('{app}') + '"', '', SW_HIDE, ewWaitUntilTerminated, ExitCode) or (ExitCode <> 0) then begin
    MsgBox('Log in as the installed desktop user. The helper could not start; files were retained.', mbError, MB_OK); Exit;
  end;
  RemovalForm := CreateCustomForm(ScaleX(520), ScaleY(280), False, False);
  RemovalForm.Caption := 'AD BioGuard — o''chirish ruxsati';
  RemovalStatus := TNewStaticText.Create(RemovalForm); RemovalStatus.Parent := RemovalForm;
  RemovalStatus.SetBounds(ScaleX(20), ScaleY(15), ScaleX(480), ScaleY(90)); RemovalStatus.AutoSize := False; RemovalStatus.WordWrap := True;
  RemovalStatus.Caption := 'Qurilma uchun bir martalik kodni kiriting. Internet talab qilinadi. Kodni tashkilot admini yoki shaxsiy hisob egasi beradi.';
  RemovalEntry := TNewEdit.Create(RemovalForm); RemovalEntry.Parent := RemovalForm;
  RemovalEntry.SetBounds(ScaleX(20), ScaleY(115), ScaleX(480), ScaleY(25)); RemovalEntry.PasswordChar := '*';
  RemovalButton := TNewButton.Create(RemovalForm); RemovalButton.Parent := RemovalForm;
  RemovalButton.SetBounds(ScaleX(20), ScaleY(165), ScaleX(140), ScaleY(30)); RemovalButton.Caption := 'Tekshirish'; RemovalButton.OnClick := @RemovalClick;
  ResumeButton := TNewButton.Create(RemovalForm); ResumeButton.Parent := RemovalForm;
  ResumeButton.SetBounds(ScaleX(170), ScaleY(165), ScaleX(190), ScaleY(30)); ResumeButton.Caption := 'O''chirishni davom ettirish'; ResumeButton.OnClick := @ResumeClick;
  CancelButton := TNewButton.Create(RemovalForm); CancelButton.Parent := RemovalForm;
  CancelButton.SetBounds(ScaleX(370), ScaleY(165), ScaleX(130), ScaleY(30)); CancelButton.Caption := 'Bekor'; CancelButton.ModalResult := mrCancel; CancelButton.Cancel := True;
  TimerID := SetTimer(0, 0, 250, CreateCallback(@PollBroker));
  Result := RemovalForm.ShowModal = mrOk;
  KillTimer(0, TimerID); TimerID := 0;
  RemovalForm.Free; RemovalForm := nil;
  if BrokerState <> 'approved' then Result := False;
end;

function AwaitBroker(ExpectedState: String): Boolean;
var Started: Cardinal;
begin
  Started := GetTickCount;
  repeat
    ReadReply;
    if not Waiting and (BrokerState <> 'pending') then begin Result := BrokerState = ExpectedState; Exit; end;
    if not Waiting then BrokerCommand('state', '');
    Sleep(50);
  until GetTickCount - Started > 15000;
  Result := False;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var ExitCode: Integer;
begin
  if CurUninstallStep = usUninstall then begin
    if not BrokerCommand('resume', '') or not AwaitBroker('approved') then RaiseException('Online removal permission unavailable. Files retained.');
    if not Exec(ExpectedHelper, '--check-native-recovery --target-sid ' + TargetUserSID + ' --install-path "' + ExpandConstant('{app}') + '"', '', SW_HIDE, ewWaitUntilTerminated, ExitCode) or (ExitCode <> 0) then RaiseException('Recovery snapshot unavailable. Close uninstall and prepare recovery before retrying. Files retained.');
    if not Exec(ExpectedHelper, '--stop-supervisor', '', SW_HIDE, ewWaitUntilTerminated, ExitCode) or (ExitCode <> 0) then RaiseException('Kuzatuvchi xizmati to‘xtatilmadi. Fayllar saqlab qolindi.');
    if not Exec(ExpectedHelper, '--stop-agent --install-path "' + ExpandConstant('{app}') + '"', '', SW_HIDE, ewWaitUntilTerminated, ExitCode) or (ExitCode <> 0) then RaiseException('Cannot stop this installation safely. Files retained.');
  end;
  if CurUninstallStep = usPostUninstall then begin
    if not Exec(ExpectedHelper, '--cleanup-install-cache --install-path "' + ExpandConstant('{app}') + '"', '', SW_HIDE, ewWaitUntilTerminated, ExitCode) or (ExitCode <> 0) then RaiseException('Cache cleanup failed. Removal remains pending.');
    if not BrokerCommand('cleanup', '') or not AwaitBroker('removed') then MsgBox('O''chirish hali yakunlanmagan. Internetga ulanib, ProgramData\AD BioGuard\native-removal\BioGuardLifecycle.exe --retry-native-removal ni administrator sifatida oching. Faqat server javobi qolgan bo''lsa LocalAppData\ADBioGuardRemoval\BioGuardLifecycle.exe --resume-removal ishlaydi.', mbError, MB_OK)
    else RegDeleteKeyIncludingSubkeys(HKLM64, 'SOFTWARE\AD BioGuard');
  end;
end;

procedure DeinitializeUninstall;
begin
  StopBroker;
end;
