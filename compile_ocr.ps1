# compile_ocr.ps1
# Compiles ocr.cs into ocr.exe using .NET Framework CSC

# Path to CSC (C# Compiler) - usually in .NET Framework dir
$csc_path = "$env:windir\Microsoft.NET\Framework64\v4.0.30319\csc.exe"

# Output and Source
$out_path = "$PSScriptRoot\ocr.exe"
$src_path = "$PSScriptRoot\assets\scripts\ocr.cs"
if (-not (Test-Path $src_path)) {
    # Fallback to current dir if assets not found
    $src_path = "$PSScriptRoot\ocr.cs" 
}

if (-not (Test-Path $src_path)) {
    Write-Error "Source file not found: $src_path"
    exit 1
}

# Metadata Paths
$sys32 = "$env:windir\System32\WinMetadata"
$net4 = "$env:windir\Microsoft.NET\Framework64\v4.0.30319"

# References
# We include all likely candidates found on standard systems.
$refs_list = @(
    "$sys32\Windows.Foundation.winmd",
    "$sys32\Windows.Media.winmd",
    "$sys32\Windows.Globalization.winmd",
    "$sys32\Windows.Graphics.winmd",
    "$sys32\Windows.Storage.winmd",
    "$net4\System.Runtime.WindowsRuntime.dll",
    "$net4\System.Runtime.dll",
    "$net4\System.IO.dll",
    "$net4\System.Threading.Tasks.dll"
)

# Join references with comma
$ref_str = $refs_list -join ","

# Construct command
# /target:exe /out:... /r:... source
$cmd = "& `"$csc_path`" /target:exe /out:`"$out_path`" /r:$ref_str `"$src_path`""

Write-Host "Compiling ocr.exe..."
Write-Host "Source: $src_path"
Write-Host "Refs: $ref_str"

Invoke-Expression $cmd

if ($LASTEXITCODE -eq 0) {
    Write-Host "Success: $out_path created."
}
else {
    Write-Error "Compilation Failed."
    exit 1
}
