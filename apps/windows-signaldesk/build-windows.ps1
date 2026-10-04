Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw "Node.js is required." }
if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) { throw "Rust/Cargo is required." }

npm install
npm run tauri build

Write-Host ""
Write-Host "Installers:"
Get-ChildItem ".\src-tauri\target\release\bundle" -Recurse -File |
  Where-Object { $_.Extension -in ".exe", ".msi" } |
  Select-Object FullName, Length
