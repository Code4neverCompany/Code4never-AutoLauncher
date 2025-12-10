
try {
    $code = Get-Content "assets\scripts\ocr.cs" -Raw
    
    # Get Framework Path for System.Runtime.WindowsRuntime
    $frameworkPath = [System.Runtime.InteropServices.RuntimeEnvironment]::GetRuntimeDirectory()
    $sysRuntimeWinRt = Join-Path $frameworkPath "System.Runtime.WindowsRuntime.dll"
    
    # Facades path
    $facadesPath = Join-Path $frameworkPath "Facades"
    $sysRuntime = Join-Path $facadesPath "System.Runtime.dll"
    $sysThreadingTasks = Join-Path $facadesPath "System.Threading.Tasks.dll"
    $sysIO = Join-Path $facadesPath "System.IO.dll"
    $sysRuntimeInterop = Join-Path $facadesPath "System.Runtime.InteropServices.dll"

    $refs = @(
        "System.Drawing",
        $sysRuntimeWinRt,
        $sysRuntime,
        $sysThreadingTasks,
        $sysIO,
        $sysRuntimeInterop,
        "C:\Windows\System32\WinMetadata\Windows.Foundation.winmd",
        "C:\Windows\System32\WinMetadata\Windows.Graphics.winmd",
        "C:\Windows\System32\WinMetadata\Windows.Media.winmd",
        "C:\Windows\System32\WinMetadata\Windows.Storage.winmd"
    )

    Add-Type -TypeDefinition $code -ReferencedAssemblies $refs -OutputAssembly "assets\scripts\ocr.exe" -OutputType ConsoleApplication
    Write-Host "Compilation Successful: assets\scripts\ocr.exe"
}
catch {
    Write-Error "Compilation Failed: $_"
    exit 1
}
