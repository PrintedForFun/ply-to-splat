param(
    [string]$InputFile,
    [string]$OutputFile,
    [double]$Subsample,
    [double]$SplatSize
)

function Read-OptionalValue {
    param(
        [string]$Prompt,
        [string]$DefaultValue
    )

    $value = Read-Host $Prompt
    if ([string]::IsNullOrWhiteSpace($value)) {
        return $DefaultValue
    }

    return $value
}

if ([string]::IsNullOrWhiteSpace($InputFile)) {
    $InputFile = Read-OptionalValue -Prompt "Input PLY file" -DefaultValue "./input.ply"
}

if ([string]::IsNullOrWhiteSpace($OutputFile)) {
    $OutputFile = Read-OptionalValue -Prompt "Output splat PLY file" -DefaultValue "./output.ply"
}

if (-not $PSBoundParameters.ContainsKey('Subsample')) {
    $subsampleInput = Read-OptionalValue -Prompt "Subsampling value (e.g. 0.0075)" -DefaultValue "0.0075"
    $Subsample = [double]$subsampleInput
}

if (-not $PSBoundParameters.ContainsKey('SplatSize')) {
    $splatSizeInput = Read-OptionalValue -Prompt "Splat size / scale value (e.g. -5)" -DefaultValue "-5"
    $SplatSize = [double]$splatSizeInput
}

if ($Subsample -le 0) {
    throw "Subsample must be greater than 0."
}

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
    "--ss",
    "$Subsample",
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
    "--scale",
    "$SplatSize",
    "$tmp",
    "$OutputFile"
)
& $pythonExe @pythonArgs @splatArgs
$exitCode = $LASTEXITCODE

Pop-Location

Remove-Item -Force -ErrorAction SilentlyContinue $tmp

exit $exitCode
