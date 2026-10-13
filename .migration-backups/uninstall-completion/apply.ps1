$ErrorActionPreference = 'Stop'
$agentFixRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$agentFixRoot = Join-Path $agentFixRoot 'agent'
$agentFixRoot = (Resolve-Path -LiteralPath $agentFixRoot).Path
if ($agentFixRoot -ne 'C:\Users\User\Desktop\for auth\agent') {
    throw 'Unexpected agent repository path'
}
$agentFixStage = Join-Path $PSScriptRoot 'agent'
$agentFixTarget = Join-Path $agentFixRoot 'platform_adapters/windows/lifecycle.py'
$agentFixExpectedHash = '2A57BAD463A730E468A0425D2010DED61AA57593292526CE3070B00A659471F4'
if ((Get-FileHash -LiteralPath $agentFixTarget -Algorithm SHA256).Hash -ne $agentFixExpectedHash) {
    throw 'Lifecycle source changed after review; refusing to overwrite'
}
$agentFixTestTarget = Join-Path $agentFixRoot 'tests/test_removal_completion.py'
if (Test-Path -LiteralPath $agentFixTestTarget) {
    throw 'Regression test already exists; refusing to overwrite'
}
Copy-Item -LiteralPath $agentFixTarget -Destination (Join-Path $PSScriptRoot 'lifecycle-before.py')
Copy-Item -LiteralPath (Join-Path $agentFixStage 'platform_adapters/windows/lifecycle.py') -Destination $agentFixTarget
Copy-Item -LiteralPath (Join-Path $agentFixStage 'tests/test_removal_completion.py') -Destination $agentFixTestTarget
Write-Output 'Applied reviewed uninstall fix and regression tests to agent repository.'
