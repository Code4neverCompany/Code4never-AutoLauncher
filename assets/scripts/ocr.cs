
using System;
using System.IO;
using System.Threading.Tasks;
using Windows.Graphics.Imaging;
using Windows.Media.Ocr;
using Windows.Storage;
using Windows.Storage.Streams;

namespace OcrTool
{
    class Program
    {
        static async Task Main(string[] args)
        {
            if (args.Length == 0)
            {
                Console.WriteLine("Usage: ocr.exe <image_path>");
                return;
            }

            string imagePath = args[0];
            if (!File.Exists(imagePath))
            {
                Console.WriteLine("Error: File not found");
                return;
            }

            try
            {
                // Initialize OCR Engine
                var ocrEngine = OcrEngine.TryCreateFromUserProfileLanguages();
                if (ocrEngine == null)
                {
                    Console.WriteLine("Error: Could not create OCR Engine (Language not supported?)");
                    return;
                }

                // Load Image
                StorageFile file = await StorageFile.GetFileFromPathAsync(Path.GetFullPath(imagePath));
                using (IRandomAccessStream stream = await file.OpenAsync(FileAccessMode.Read))
                {
                    BitmapDecoder decoder = await BitmapDecoder.CreateAsync(stream);
                    SoftwareBitmap softwareBitmap = await decoder.GetSoftwareBitmapAsync();

                    // OCR requires NV12 or Gray8, convert if needed
                    // Actually, OcrEngine supports BGRA8 too usually, but let's ensure it's software bitmap
                    // No, wait, TryCreateFromUserProfileLanguages()
                    
                    var ocrResult = await ocrEngine.RecognizeAsync(softwareBitmap);
                    
                    foreach (var line in ocrResult.Lines)
                    {
                        Console.WriteLine(line.Text);
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
            }
        }
    }
}
