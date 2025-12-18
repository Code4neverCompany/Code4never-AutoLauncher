
import sys
import asyncio
from pathlib import Path

# Try to import winsdk
try:
    from winsdk.windows.media.ocr import OcrEngine
    from winsdk.windows.graphics.imaging import BitmapDecoder, SoftwareBitmap
    from winsdk.windows.storage import StorageFile, FileAccessMode
    from winsdk.windows.storage.streams import IRandomAccessStream
    from winsdk.windows.globalization import Language
except ImportError:
    print("Error: winsdk not installed. Please pip install winsdk")
    sys.exit(1)

async def run_ocr(image_path):
    try:
        # Load File
        file = await StorageFile.get_file_from_path_async(str(Path(image_path).resolve()))
        stream = await file.open_async(FileAccessMode.READ)
        
        # Decode
        decoder = await BitmapDecoder.create_async(stream)
        # OcrEngine requires input to be less than MaxImageDimension?
        # Usually fine for 1080p.
        
        soft_bmp = await decoder.get_software_bitmap_async()
        
        # Create Engine
        # Try English first
        lang = Language("en-US")
        engine = None
        if OcrEngine.is_language_supported(lang):
             engine = OcrEngine.try_create_from_language(lang)
        
        if not engine:
             engine = OcrEngine.try_create_from_user_profile_languages()
             
        if not engine:
            print("Error: Could not create OCR Engine.")
            return

        # Recognize
        result = await engine.recognize_async(soft_bmp)
        
        # Print
        if result and result.lines:
            for line in result.lines:
                print(line.text)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ocr.py <image_path>")
        sys.exit(1)
        
    path = sys.argv[1]
    asyncio.run(run_ocr(path))
