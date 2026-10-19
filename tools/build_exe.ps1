# Builds dist\PasswordGuardian\PasswordGuardian.exe (and a zip of that folder) for PCs without Python.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = & (Join-Path $root 'run.ps1') -SetupOnly | Select-Object -Last 1
if ($LASTEXITCODE -ne 0 -or -not $python) { exit 1 }

Write-Host "실행 파일 제작 도구(PyInstaller)를 준비합니다..."
$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($uv) {
    & $uv.Source pip install --python $python -r (Join-Path $root 'requirements-build.txt') | Out-Host
} else {
    & $python -m pip install --disable-pip-version-check -r (Join-Path $root 'requirements-build.txt') | Out-Host
}
if ($LASTEXITCODE -ne 0) { Write-Host "PyInstaller를 설치하지 못했습니다. 인터넷 연결을 확인하세요." -ForegroundColor Red; exit 1 }

Write-Host "PasswordGuardian.exe를 만드는 중입니다. 1~2분 걸립니다..."
Push-Location $root
try {
    & $python -m PyInstaller --noconfirm --clean --distpath dist --workpath build PasswordGuardian.spec
    if ($LASTEXITCODE -ne 0) { Write-Host "실행 파일을 만들지 못했습니다. 위 메시지를 확인하세요." -ForegroundColor Red; exit 1 }
    Compress-Archive -Path 'dist\PasswordGuardian' -DestinationPath 'dist\PasswordGuardian.zip' -Force
} finally {
    Pop-Location
}
Write-Host ""
Write-Host "완료: $root\dist\PasswordGuardian\PasswordGuardian.exe" -ForegroundColor Green
Write-Host "부스 제출용 압축 파일: $root\dist\PasswordGuardian.zip"
Write-Host "런처 실행 옵션: --booth (전체 화면은 기본값)"
