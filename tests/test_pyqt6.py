
try:
    from PyQt6.QtWidgets import QApplication, QWidget
    from PyQt6.QtCore import Qt
    print("PyQt6 imports successful")
    
    try:
        print(f"Qt.Horizontal: {Qt.Horizontal}")
    except AttributeError:
        print("Qt.Horizontal not found (expected in PyQt6)")
        try:
            print(f"Qt.Orientation.Horizontal: {Qt.Orientation.Horizontal}")
        except AttributeError:
            print("Qt.Orientation.Horizontal not found")

except ImportError as e:
    print(f"PyQt6 import failed: {e}")
