
param (
    [string]$ImagePath
)

# Bridge to handle COM object opaque types using dynamic
try {
    Add-Type -TypeDefinition @"
    using System;
    using System.Collections.Generic;
    using System.Reflection;

    public class OcrBridge {
        public static void PrintLines(object linesObj) {
            try {
                // Use reflection or dynamic if available. 
                // Since this runs in PS process where types are loaded, maybe reflection works better?
                // But dynamic is safest for __ComObject.
                
                dynamic lines = linesObj;
                int count = 0;
                
                // Try Count property
                try {
                    count = lines.Count;
                } catch {
                     // Try Size?
                     try { count = lines.Size; } catch {}
                }
                
                Console.WriteLine("BRIDGE: Found " + count + " lines.");
                
                for (int i = 0; i < count; i++) {
                    try {
                        // Access via indexer
                        dynamic line = lines[i]; 
                        string text = line.Text;
                        Console.WriteLine(text);
                    } catch {
                        // Try GetAt
                         try {
                            dynamic line = lines.GetAt((uint)i);
                            Console.WriteLine(line.Text);
                         } catch (Exception ex) {
                            Console.WriteLine("BRIDGE: Error at " + i + ": " + ex.Message);
                         }
                    }
                }
            } catch (Exception e) {
                Console.WriteLine("BRIDGE: Global Error: " + e.Message);
            }
        }
    }
"@ -Language CSharp
}
catch {
    Write-Host "DEBUG: Failed to add type: $_"
}

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
    $null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
    $null = [Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType = WindowsRuntime]
    $null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]

    # Load Globalization
    $null = [Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]

    # Try explicit English first
    $lang = [Windows.Globalization.Language]::new("en-US")
    $ocrEngine = $null
    
    if ([Windows.Media.Ocr.OcrEngine]::IsLanguageSupported($lang)) {
        $ocrEngine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
        Write-Host "DEBUG: Created OCR Engine with English (en-US)"
    }

    if ($null -eq $ocrEngine) {
        $ocrEngine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
        Write-Host "DEBUG: Created OCR Engine from User Profile: $($ocrEngine.RecognizerLanguage.DisplayName)"
    }
    
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

    Write-Host "DEBUG: Image Decoded. Size: $($decoder.PixelWidth)x$($decoder.PixelHeight)"

    # Get SoftwareBitmap
    $bitmapTask = $decoder.GetSoftwareBitmapAsync()
    $bitmap = Await $bitmapTask ([Windows.Graphics.Imaging.SoftwareBitmap])

    # Recognize
    $ocrTask = $ocrEngine.RecognizeAsync($bitmap)
    $result = Await $ocrTask ([Windows.Media.Ocr.OcrResult])

    if ($null -eq $result) {
        Write-Host "DEBUG: OCR Result is null"
    }
    else {
        $lines = $result.Lines
        if ($null -eq $lines) {
            Write-Host "DEBUG: Lines collection is null"
        }
        else {
            # Offload to C# Bridge
            [OcrBridge]::PrintLines($lines)
        }
    }

}
catch {
    Write-Error "OCR Error: $_"
    exit 1
}
