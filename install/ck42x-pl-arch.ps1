# CK42X Payload Lab Architect — Windows installer
# Usage: irm https://www.ck42x.com/install/ck42x-pl-arch.ps1 | iex
$ErrorActionPreference = 'Stop'

$Version = if ($env:CK42X_PL_ARCH_VERSION) { $env:CK42X_PL_ARCH_VERSION } else { '0.1.13' }
$InstallRoot = if ($env:CK42X_PL_ARCH_HOME) { $env:CK42X_PL_ARCH_HOME } else { Join-Path $env:LOCALAPPDATA 'CK42X\ck42x-pl-arch' }
$BinDir = Join-Path $env:USERPROFILE '.local\bin'
$Tarball = if ($env:CK42X_PL_ARCH_URL) { $env:CK42X_PL_ARCH_URL } else { "https://www.ck42x.com/downloads/ck42x-pl-arch/ck42x-pl-arch-$Version.tar.gz" }
$GhTarball = 'https://github.com/lordbuffcloud/ck42x-pl-arch/archive/refs/heads/main.tar.gz'

function Get-PlArchSourceRoot {
  param([string]$Dir)
  $wrapped = Get-ChildItem -LiteralPath $Dir -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^ck42x-pl-arch' } |
    Select-Object -First 1
  if ($wrapped) { return $wrapped.FullName }
  if (Test-Path -LiteralPath (Join-Path $Dir 'pyproject.toml')) { return $Dir }
  return $null
}

function Install-FromArchive {
  param([string]$ArchivePath, [string]$WorkDir)
  if (-not (Get-Command tar -ErrorAction SilentlyContinue)) {
    throw 'tar is required (Windows 10 1903+ or install bsdtar)'
  }
  tar -xzf $ArchivePath -C $WorkDir
  $src = Get-PlArchSourceRoot -Dir $WorkDir
  if (-not $src) { throw 'Invalid package layout (expected pyproject.toml or ck42x-pl-arch-* folder)' }
  if (Test-Path $InstallRoot) { Remove-Item $InstallRoot -Recurse -Force }
  New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
  Copy-Item -Path (Join-Path $src '*') -Destination $InstallRoot -Recurse -Force
}

Write-Host ''
Write-Host '  CK42X Payload Lab Architect installer' -ForegroundColor Cyan
Write-Host '  AUTHORIZED LABS ONLY' -ForegroundColor Yellow
Write-Host ''

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw 'Python 3.10+ is required. Install from https://www.python.org/downloads/'
}

New-Item -ItemType Directory -Force -Path $InstallRoot, $BinDir | Out-Null
$tmp = Join-Path $env:TEMP "ck42x-pl-arch-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Force -Path $tmp | Out-Null

try {
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
  $archive = Join-Path $tmp 'pkg.tar.gz'
  Write-Host "-> Downloading ck42x-pl-arch $Version..." -ForegroundColor Gray
  Invoke-WebRequest -Uri $Tarball -OutFile $archive -UseBasicParsing
  Install-FromArchive -ArchivePath $archive -WorkDir $tmp
} catch {
  Write-Host "-> CDN install failed: $($_.Exception.Message)" -ForegroundColor Yellow
  Write-Host '-> Trying GitHub source fallback...' -ForegroundColor Gray
  try {
    $fallback = Join-Path $tmp 'github.tar.gz'
    Invoke-WebRequest -Uri $GhTarball -OutFile $fallback -UseBasicParsing
    Install-FromArchive -ArchivePath $fallback -WorkDir $tmp
  } catch {
    Write-Host '  Clone the repo or copy ck42x-pl-arch source into:' $InstallRoot -ForegroundColor DarkGray
    throw
  }
}

Write-Host '-> Installing Python package...' -ForegroundColor Gray
python -m pip install --user --upgrade $InstallRoot

$wrapperBody = @'
@echo off
python -m ck42x_pl_arch %*
'@
foreach ($name in @('ck42x', 'ck42x-pl-arch')) {
  Set-Content -LiteralPath (Join-Path $BinDir "$name.cmd") -Value $wrapperBody -Encoding ASCII
}

Write-Host ''
Write-Host '  Installed Payload Lab Architect' -ForegroundColor Green
Write-Host '  Run: ck42x' -ForegroundColor Cyan
Write-Host '  Alias: ck42x-pl-arch' -ForegroundColor DarkGray
Write-Host "  Add to PATH if needed: $BinDir" -ForegroundColor DarkGray
Write-Host ''
