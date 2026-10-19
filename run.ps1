param(
    [switch]$Fullscreen,
    [switch]$Practice,
    [string]$DataDir = "",
    [switch]$Booth,
    [switch]$SetupOnly  # prepare .venv and stop; used by build_exe.bat
)
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$venv = Join-Path $root '.venv'

function Get-VenvPython {
    foreach ($rel in @('Scripts\python.exe', 'bin/python')) {
        $candidate = Join-Path $venv $rel
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    return $null
}

# Windows ships a "python" shortcut that only points to the Microsoft Store; it prints "Python" and exits.
# A candidate counts only if it really runs and is 3.11-3.13: arcade 3.3.3 needs pymunk 6.9.0, which has no
# prebuilt package for Python 3.14 and would need a C compiler there.
function Find-Python {
    $candidates = @(@{Exe = 'py'; Args = @('-3.13')}, @{Exe = 'py'; Args = @('-3.12')}, @{Exe = 'py'; Args = @('-3.11')},
                    @{Exe = 'python'; Args = @()}, @{Exe = 'python3'; Args = @()})
    foreach ($candidate in $candidates) {
        if (-not (Get-Command $candidate.Exe -ErrorAction SilentlyContinue)) { continue }
        try {
            $ok = & $candidate.Exe @($candidate.Args) -c "import sys; print((3, 11) <= sys.version_info[:2] <= (3, 13))" 2>$null
        } catch { continue }
        if ($LASTEXITCODE -eq 0 -and "$ok".Trim() -eq 'True') { return $candidate }
    }
    return $null
}

function Install-Requirements($python) {
    if ($uv) {
        & $uv.Source pip install --python $python -r (Join-Path $root 'requirements.txt') | Out-Host
    } else {
        & $python -m pip install --disable-pip-version-check -r (Join-Path $root 'requirements.txt') | Out-Host
    }
    return $LASTEXITCODE -eq 0
}

$uv = Get-Command uv -ErrorAction SilentlyContinue
$python = Get-VenvPython
if (-not $python -and $uv) {
    # uv-managed Pythons are not on PATH as "python"; uv finds one, or downloads it, by itself.
    Write-Host "처음 실행이라 uv로 게임 실행 환경(.venv)을 만듭니다. 1~2분 걸릴 수 있어요..."
    & $uv.Source venv --python 3.13 $venv | Out-Host  # downloads Python 3.13 when the PC does not have it
    if ($LASTEXITCODE -ne 0) { Write-Host "uv로 실행 환경을 만들지 못했습니다." -ForegroundColor Red; exit 1 }
    $python = Get-VenvPython
    if (-not (Install-Requirements $python)) {
        Remove-Item -Recurse -Force -LiteralPath $venv  # retry from scratch next time
        Write-Host "필요한 파일을 받지 못했습니다. 인터넷 연결을 확인한 뒤 다시 실행하세요." -ForegroundColor Red
        exit 1
    }
}
if (-not $python) {
    $system = Find-Python
    if (-not $system) {
        Write-Host ""
        Write-Host "Python 3.11~3.13이 설치되어 있지 않습니다. (3.14는 필요한 부품이 아직 지원하지 않아요)" -ForegroundColor Yellow
        Write-Host "1. uv를 쓰는 PC라면 uv가 PATH에 있는지 확인하세요(명령 프롬프트에서 uv --version)."
        Write-Host "   아니면 https://www.python.org/downloads/ 에서 Python 3.13을 설치하고 'Add python.exe to PATH'를 체크하세요."
        Write-Host "2. 설치가 끝나면 start_game.bat를 다시 실행하세요. 처음 한 번은 인터넷으로 필요한 파일을 받습니다."
        exit 1
    }
    Write-Host "처음 실행이라 게임 실행 환경(.venv)을 만듭니다. 1~2분 걸릴 수 있어요..."
    & $system.Exe @($system.Args) -m venv $venv | Out-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "실행 환경을 만들지 못했습니다." -ForegroundColor Red; exit 1 }
    $python = Get-VenvPython
    if (-not (Install-Requirements $python)) {
        Remove-Item -Recurse -Force -LiteralPath $venv  # retry from scratch next time
        Write-Host "필요한 파일을 받지 못했습니다. 인터넷 연결을 확인한 뒤 다시 실행하세요." -ForegroundColor Red
        exit 1
    }
}
if ($SetupOnly) { Write-Output $python; exit 0 }
$taskArgs = @((Join-Path $root 'run_game.py'))
if ($Fullscreen) { $taskArgs += '--fullscreen' }
if ($Practice) { $taskArgs += '--practice' }
if ($Booth) { $taskArgs += '--booth' }
if ($DataDir) { $taskArgs += @('--data-dir', $DataDir) }
& $python @taskArgs
exit $LASTEXITCODE
