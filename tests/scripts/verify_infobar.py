import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QScrollArea
from PyQt6.QtCore import Qt
from qfluentwidgets import InfoBar, InfoBarPosition

app = QApplication(sys.argv)

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(800, 600)
        self.setWindowTitle("InfoBar Test")
        
        self.layout = QVBoxLayout(self)
        
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.scroll.setWidget(self.content)
        
        self.layout.addWidget(self.scroll)
        
        self.button = QPushButton("Show InfoBar", self)
        self.button.clicked.connect(self.show_infobar)
        self.layout.addWidget(self.button)
        
    def show_infobar(self):
        print("Attempting to show InfoBar with None content...")
        try:
            # Test None content
            InfoBar.success(
                title=None,
                content=None,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            print("InfoBar shown successfully with None content")
        except Exception as e:
            print(f"CRASH: {e}")
            import traceback
            traceback.print_exc()

w = TestWindow()
w.show()

# Auto-click to test without interaction
from PyQt6.QtCore import QTimer
QTimer.singleShot(1000, w.show_infobar)
QTimer.singleShot(2000, app.quit)

sys.exit(app.exec())
