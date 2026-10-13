$ErrorActionPreference='Stop'
$taskAgentRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../agent'))
if ($taskAgentRoot -ne 'C:\Users\User\Desktop\for auth\agent') { throw 'Unexpected agent checkout.' }
$taskManifest=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'baseline.json') -Raw | ConvertFrom-Json
foreach($taskEntry in $taskManifest) {
    $taskTarget=Join-Path $taskAgentRoot $taskEntry.path
    if((Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash -ne $taskEntry.hash) {
        throw ('Agent file changed since review: '+$taskEntry.path)
    }
}
foreach($taskRelative in @('services/removal.py','services/lifecycle_broker.py','tests/test_uninstall_resume_flow.py')) {
    $taskTarget=Join-Path $taskAgentRoot $taskRelative
    $taskBackup=Join-Path $PSScriptRoot ('before/'+$taskRelative)
    if((Test-Path -LiteralPath $taskTarget) -and -not (Test-Path -LiteralPath $taskBackup)) {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $taskBackup) | Out-Null
        Copy-Item -LiteralPath $taskTarget -Destination $taskBackup
    }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot ('stage/'+$taskRelative)) -Destination $taskTarget
}
Write-Output 'Applied uninstall recovery fix to three agent source files; backups retained.'
