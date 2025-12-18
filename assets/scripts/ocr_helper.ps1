
# ocr_helper.ps1
# Usage: powershell -File ocr_helper.ps1 "path/to/image.png"

param (
    [string]$ImagePath
)

if (-not (Test-Path $ImagePath)) {
    Write-Error "File not found: $ImagePath"
    exit 1
}

# Load WinRT Assemblies
[System.Reflection.Assembly]::LoadWithPartialName("System.Runtime.WindowsRuntime") | Out-Null
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]

Function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}

try {
    # Load required types
    $null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType=WindowsRuntime]
    $null = [Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType=WindowsRuntime]
    $null = [Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime]

    # Initialize OCR Engine
    $ocrEngine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
    
    if ($null -eq $ocrEngine) {
        Write-Host "Error: OCR Engine could not be created."
        exit 0
    }

    # Load file
    $path = [System.IO.Path]::GetFullPath($ImagePath)
    $fileTask = [Windows.Storage.StorageFile]::GetFileFromPathAsync($path)
    $storageFile = Await $fileTask ([Windows.Storage.StorageFile])

    # Open stream
    $streamTask = $storageFile.OpenAsync([Windows.Storage.FileAccessMode]::Read)
    $stream = Await $streamTask ([Windows.Storage.Streams.IRandomAccessStream])

    # Create Decoder
    $decoderTask = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)
    $decoder = Await $decoderTask ([Windows.Graphics.Imaging.BitmapDecoder])

    # Get SoftwareBitmap
    $bitmapTask = $decoder.GetSoftwareBitmapAsync()
    $bitmap = Await $bitmapTask ([Windows.Graphics.Imaging.SoftwareBitmap])

    # Recognize
    $ocrTask = $ocrEngine.RecognizeAsync($bitmap)
    $result = Await $ocrTask ([Windows.Media.Ocr.OcrResult])

    # Output text
    foreach ($line in $result.Lines) {
        Write-Host $line.Text
    }

} catch {
    Write-Error "OCR Error: $_"
    exit 1
}
