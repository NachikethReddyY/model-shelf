$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

uv tool install --force .

$toolBin = if ($env:UV_TOOL_BIN_DIR) { $env:UV_TOOL_BIN_DIR } else { Join-Path $HOME ".local\bin" }
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")

if (-not (($userPath -split ";") -contains $toolBin)) {
  $newPath = if ([string]::IsNullOrWhiteSpace($userPath)) { $toolBin } else { "$toolBin;$userPath" }
  [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
  Write-Host "Updated user PATH with $toolBin"
}

$env:Path = "$toolBin;$env:Path"

Write-Host ""
Write-Host "Installed the global ms command."
Write-Host ""
Write-Host "For this PowerShell session, run:"
Write-Host ""
Write-Host "  `$env:Path = `"$toolBin;`$env:Path`""
Write-Host ""
Write-Host "Then test:"
Write-Host ""
Write-Host "  ms --help"
Write-Host ""
Write-Host "New terminals should pick this up automatically."
