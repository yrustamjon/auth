# Resume the existing online-authorized operation without copying a locked DAT.
# Run this script as administrator after closing the failed uninstaller.
$ErrorActionPreference = 'Stop'
$taskIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$taskPrincipal = [Security.Principal.WindowsPrincipal]::new($taskIdentity)
if (-not $taskPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run this script in PowerShell as administrator.'
}
$taskRegistry = Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\AD BioGuard'
$taskProgramFiles = if ($env:ProgramW6432) { $env:ProgramW6432 } else { $env:ProgramFiles }
$taskExpectedRoot = [IO.Path]::GetFullPath((Join-Path $taskProgramFiles 'AD BioGuard'))
$taskInstallRoot = [IO.Path]::GetFullPath($taskRegistry.InstallPath)
if ($taskInstallRoot -ne $taskExpectedRoot -or $taskRegistry.TargetUserSID -notmatch '^S-1-5-[0-9-]+$') {
    throw 'Installed path or desktop identity is invalid; recovery refused.'
}
foreach ($taskDirectory in @($taskInstallRoot, (Join-Path $env:ProgramData 'AD BioGuard'))) {
    if ((Test-Path -LiteralPath $taskDirectory) -and
        ((Get-Item -LiteralPath $taskDirectory).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'Recovery path is a reparse point; recovery refused.'
    }
}
$taskDataFiles = @(Get-ChildItem -LiteralPath $taskInstallRoot -Filter 'unins*.dat' -File)
if ($taskDataFiles.Count -eq 0) { throw 'Native uninstall log is missing.' }
foreach ($taskDataFile in $taskDataFiles) {
    try {
        $taskStream = [IO.File]::Open($taskDataFile.FullName, [IO.FileMode]::Open,
            [IO.FileAccess]::Read, [IO.FileShare]::Read)
        $taskStream.Dispose()
    } catch {
        throw 'Close the uninstall/error windows before running recovery again.'
    }
}
$taskHelper = Join-Path $taskInstallRoot 'BioGuardLifecycle.exe'
if (-not (Test-Path -LiteralPath $taskHelper -PathType Leaf)) { throw 'Installed lifecycle helper is missing.' }
$taskArguments = '--prepare-native-recovery --target-sid ' + $taskRegistry.TargetUserSID +
    ' --install-path "' + $taskInstallRoot + '"'
$taskPreparation = Start-Process -FilePath $taskHelper -ArgumentList $taskArguments -Wait -PassThru -WindowStyle Hidden
if ($taskPreparation.ExitCode -ne 0) { throw 'Recovery snapshot failed; removal was not started.' }
$taskRecoveryHelper = Join-Path $env:ProgramData 'AD BioGuard\native-removal\BioGuardLifecycle.exe'
$taskRecovery = Start-Process -FilePath $taskRecoveryHelper -ArgumentList '--retry-native-removal' -Wait -PassThru -WindowStyle Hidden
if ($taskRecovery.ExitCode -ne 0) { throw 'Native recovery launcher failed.' }
Write-Output 'Uninstaller reopened. Choose resume for the existing operation; internet is required.'
