import sys
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPalette, QBrush, QFont
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame

class GameSimulation(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wuthering Waves") # Main game title
        self.showFullScreen()
        
        # Set dark background to simulate game loading screen
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#1a1a1a"))
        self.setPalette(palette)
        
        # Main layout to center the dialog
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create the custom dialog container
        dialog = QFrame()
        dialog.setFixedSize(600, 300)
        dialog.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border-radius: 10px;
                border: 1px solid #cccccc;
            }
        """)
        
        # Dialog Layout
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.setSpacing(0)
        
        # Header "Notice"
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("background-color: white; border-top-left-radius: 10px; border-top-right-radius: 10px; border-bottom: 2px solid #e0e0e0;")
        header_layout = QHBoxLayout(header)
        header_label = QLabel("Notice")
        header_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        dialog_layout.addWidget(header)
        
        # Content "Patching complete..."
        content_frame = QFrame()
        content_frame.setStyleSheet("background-color: #f8f8f8;")
        content_layout = QVBoxLayout(content_frame)
        content_label = QLabel("Patching complete. The game is restarting.")
        content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_label.setFont(QFont("Segoe UI", 11))
        content_layout.addWidget(content_label)
        dialog_layout.addWidget(content_frame)
        
        # Footer with "Confirm" button
        footer_frame = QFrame()
        footer_frame.setFixedHeight(70)
        footer_frame.setStyleSheet("background-color: #f8f8f8; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;")
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        footer_layout.setContentsMargins(20, 10, 30, 20)
        
        # The Confirm Button (Black with White Text)
        confirm_btn = QPushButton("Confirm")
        confirm_btn.setFixedSize(120, 40)
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: black;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """)
        confirm_btn.clicked.connect(self.on_confirm)
        footer_layout.addWidget(confirm_btn)
        
        dialog_layout.addWidget(footer_frame)
        
        main_layout.addWidget(dialog)

    def on_confirm(self):
        print("SIMULATION: 'Confirm' button clicked! Exiting...")
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = GameSimulation()
    game.show()
    print(f"Game Simulation Started. PID: {app.applicationPid()}")
    sys.exit(app.exec())
