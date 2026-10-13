# Run in disposable VM as an ordinary user after installing the VM service package.
# Does not mutate login providers or services. Native outcomes require actual runs.
param([switch]$DisposableVM)
$ErrorActionPreference = 'Stop'
if (-not $DisposableVM) { throw 'Explicit -DisposableVM is required.' }
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run these access-denial checks as an ordinary VM user.'
}
$service = Get-CimInstance Win32_Service -Filter "Name='BioGuardAuthority'"
if (-not $service) { throw 'VM test service missing.' }
if ($service.StartName -ne 'NT AUTHORITY\LocalService') { throw 'Unexpected service identity.' }
if ($service.StartMode -ne 'Auto' -or $service.State -ne 'Running') { throw 'Service must run with automatic startup.' }
$env:ADBIOGUARD_VM_TESTS = '1'
python -m unittest tests.windows.test_service_integration -v
if ($LASTEXITCODE -ne 0) { throw 'Native IPC/SCM checks failed.' }
Write-Output 'SCM/IPC checks passed. Still required: GUI End task, crash recovery, reboot, user switch/RDP, install cancellation, removal and snapshot restore.'
Write-Output 'Native Windows login MFA, alternate-provider filtering and biometric verification are NOT implemented by this service.'
