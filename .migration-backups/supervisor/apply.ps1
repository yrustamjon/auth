$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../agent'))
if($taskRoot -ne 'C:\Users\User\Desktop\for auth\agent'){throw 'Unexpected agent checkout.'}
$taskManifest=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'baseline.json') -Raw | ConvertFrom-Json
foreach($taskEntry in $taskManifest){
    if((Get-FileHash -LiteralPath (Join-Path $taskRoot $taskEntry.path) -Algorithm SHA256).Hash -ne $taskEntry.hash){throw ('Source changed: '+$taskEntry.path)}
}
$taskFiles=@('services/supervision.py','services/telemetry.py','platform_adapters/windows/supervisor_process.py','platform_adapters/windows/watchdog_entry.py','platform_adapters/windows/supervisor_service.py','platform_adapters/windows/runtime.py','platform_adapters/windows/lifecycle.py','app/lifecycle_entry.py','builders/windows/bioguard-watchdog.spec','builders/windows/bioguard-supervisor.spec','builders/windows/bioguard_installer.iss','builders/windows/recover-supervisor.cmd','builders/windows/SUPERVISOR.md','.github/workflows/build.yml','tests/test_supervision.py','tests/test_supervisor_packaging.py','tests/test_supervisor_windows.py')
foreach($taskRelative in $taskFiles){
    $taskTarget=Join-Path $taskRoot $taskRelative
    $taskBackup=Join-Path $PSScriptRoot ('before/'+$taskRelative)
    if((Test-Path -LiteralPath $taskTarget) -and -not (Test-Path -LiteralPath $taskBackup)){
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $taskBackup) | Out-Null
        Copy-Item -LiteralPath $taskTarget -Destination $taskBackup
    }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot ('stage/'+$taskRelative)) -Destination $taskTarget
}
Write-Output 'Applied standard Windows supervisor, watchdog, installer integration, recovery and tests.'
