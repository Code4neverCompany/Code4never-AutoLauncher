from PyQt6.QtGui import QImage
import sys

try:
    if hasattr(QImage, 'fromHICON'):
        print("QImage.fromHICON exists")
    else:
        print("QImage.fromHICON does NOT exist")
except Exception as e:
    print(f"Error: {e}")
