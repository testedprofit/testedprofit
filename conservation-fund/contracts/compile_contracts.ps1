# Compile AlgoPool and ProfitLock contracts
# Run from the contracts/ directory

$env:VIRTUAL_ENV = "$PSScriptRoot\.venv"
$puyapy = "$PSScriptRoot\.venv\Scripts\puyapy.exe"

if (-not (Test-Path $puyapy)) {
    Write-Host "Creating venv and installing puyapy..."
    python.exe -m venv "$PSScriptRoot\.venv"
    & "$PSScriptRoot\.venv\Scripts\pip.exe" install algorand-python==3.5.0 puyapy
}

Write-Host "Compiling AlgoPool..."
& $puyapy "$PSScriptRoot\algo_pool\contract.py" --out-dir "$PSScriptRoot\artifacts\algo_pool\"

Write-Host "Compiling ProfitLock..."
& $puyapy "$PSScriptRoot\profit_lock\contract.py" --out-dir "$PSScriptRoot\artifacts\profit_lock\"

Write-Host ""
Write-Host "Done. Artifacts:"
Get-ChildItem "$PSScriptRoot\artifacts" -Recurse -Filter "*.teal" | Select-Object Name
