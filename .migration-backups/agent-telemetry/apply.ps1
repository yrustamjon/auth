$ErrorActionPreference='Stop'
$taskAgentRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../agent'))
if($taskAgentRoot -ne 'C:\Users\User\Desktop\for auth\agent'){throw 'Unexpected agent checkout.'}
$taskManifest=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'baseline.json') -Raw | ConvertFrom-Json
foreach($taskEntry in $taskManifest){
    if((Get-FileHash -LiteralPath (Join-Path $taskAgentRoot $taskEntry.path) -Algorithm SHA256).Hash -ne $taskEntry.hash){throw ('Source changed: '+$taskEntry.path)}
}
foreach($taskRelative in @('services/telemetry.py','tests/test_telemetry_outbox.py','platform_adapters/windows/runtime.py','app/controller.py')){
    $taskTarget=Join-Path $taskAgentRoot $taskRelative
    $taskBackup=Join-Path $PSScriptRoot ('before/'+$taskRelative)
    if((Test-Path -LiteralPath $taskTarget) -and -not (Test-Path -LiteralPath $taskBackup)){
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $taskBackup) | Out-Null
        Copy-Item -LiteralPath $taskTarget -Destination $taskBackup
    }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot ('stage/'+$taskRelative)) -Destination $taskTarget
}
Write-Output 'Applied durable telemetry and lifecycle hooks to four agent source files.'
