using System;
using System.IO;
using System.Threading;
using Windows.Graphics.Imaging;
using Windows.Media.Ocr;
using Windows.Storage;
using Windows.Storage.Streams;
using Windows.Foundation;

namespace AutoLauncher.OCR
{
    class Program
    {
        static void Main(string[] args)
        {
            if (args.Length == 0)
            {
                Console.WriteLine("Usage: ocr.exe <image_path>");
                return;
            }

            string imagePath = args[0];
            try
            {
                // Initialize OCR Engine
                // Try to force English first
                OcrEngine ocrEngine = null;
                var lang = new Windows.Globalization.Language("en-US");
                if (OcrEngine.IsLanguageSupported(lang))
                {
                    ocrEngine = OcrEngine.TryCreateFromLanguage(lang);
                }
                
                if (ocrEngine == null)
                {
                    ocrEngine = OcrEngine.TryCreateFromUserProfileLanguages();
                }

                if (ocrEngine == null)
                {
                    Console.WriteLine("Error: Could not create OCR Engine (Language not supported?)");
                    return;
                }
                Console.WriteLine("DEBUG: Engine Created. Language: " + ocrEngine.RecognizerLanguage.DisplayName);

                // Load Image
                var fileOp = StorageFile.GetFileFromPathAsync(Path.GetFullPath(imagePath));
                var file = Await(fileOp);

                var streamOp = file.OpenAsync(FileAccessMode.Read);
                using (var stream = Await(streamOp))
                {
                    var decoderOp = BitmapDecoder.CreateAsync(stream);
                    var decoder = Await(decoderOp);

                    Console.WriteLine("DEBUG: Image Decoded " + decoder.PixelWidth + "x" + decoder.PixelHeight);

                    var bitmapOp = decoder.GetSoftwareBitmapAsync();
                    var softwareBitmap = Await(bitmapOp);

                    var ocrOp = ocrEngine.RecognizeAsync(softwareBitmap);
                    var ocrResult = Await(ocrOp);

                    Console.WriteLine("DEBUG: Found " + ocrResult.Lines.Count + " lines.");

                    foreach (var line in ocrResult.Lines)
                    {
                        Console.WriteLine(line.Text);
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine("Error: " + ex.Message);
            }
        }

        // Helper to await WinRT async operations synchronously
        static T Await<T>(IAsyncOperation<T> op)
        {
            // Simple polling wait
            while (op.Status == AsyncStatus.Started)
            {
                Thread.Sleep(10);
            }

            if (op.Status == AsyncStatus.Completed)
            {
                return op.GetResults();
            }
            
            if (op.Status == AsyncStatus.Error)
            {
                throw new Exception("Async Operation Failed: " + op.ErrorCode.Message);
            }

            throw new Exception("Async Operation Canceled or Failed");
        }
    }
}
