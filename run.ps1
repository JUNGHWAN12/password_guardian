param(
    [switch]$Fullscreen,
    [switch]$Practice,
    [string]$DataDir = ""
)
$ErrorActionPreference = "Stop"
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { $taskPython = 'python' }
$taskArgs = @((Join-Path $PSScriptRoot 'run_game.py'))
if ($Fullscreen) { $taskArgs += '--fullscreen' }
if ($Practice) { $taskArgs += '--practice' }
if ($DataDir) { $taskArgs += @('--data-dir', $DataDir) }
& $taskPython @taskArgs
exit $LASTEXITCODE
