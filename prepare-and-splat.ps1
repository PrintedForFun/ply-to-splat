param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$InputFile,

    [Parameter(Mandatory=$true, Position=1)]
    [string]$OutputFile
)

$pythonExe = "python"
$pythonArgs = @()
if (-not (Get-Command $pythonExe -ErrorAction SilentlyContinue)) {
    $pythonExe = "python3"
}
if (-not (Get-Command $pythonExe -ErrorAction SilentlyContinue)) {
    $pythonExe = "py"
    $pythonArgs = @("-3")
}

try {
    & $pythonExe @pythonArgs --version > $null 2>&1
} catch {
    Write-Error "Python was not found on PATH. Activate your virtual environment and ensure 'python', 'python3', or 'py -3' is available."
    exit 1
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# Change to script directory so relative paths work
Push-Location $scriptRoot

$tmp = "tmp-mesh.ply"

$prepareArgs = @(
    "src/cloud-compare-prepare.py",
    "--rotate",
    "90,0,0",
    "$InputFile",
    "$tmp"
)
& $pythonExe @pythonArgs @prepareArgs
if ($LASTEXITCODE -ne 0) { 
    Pop-Location
    exit $LASTEXITCODE 
}

$splatArgs = @(
    "src/ply-to-splat.py",
    "$tmp",
    "$OutputFile"
)
& $pythonExe @pythonArgs @splatArgs
$exitCode = $LASTEXITCODE

Pop-Location

Remove-Item -Force -ErrorAction SilentlyContinue $tmp

exit $exitCode
