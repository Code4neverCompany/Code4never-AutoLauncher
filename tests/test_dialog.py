import sys
from PyQt6.QtWidgets import QApplication, QMessageBox, QPushButton, QVBoxLayout, QWidget, QLabel

def create_test_dialog():
    app = QApplication(sys.argv)
    
    window = QWidget()
    window.setWindowTitle("Notice")
    window.setFixedSize(300, 150)
    
    layout = QVBoxLayout()
    
    label = QLabel("A new version is available.\nPlease update to continue.")
    layout.addWidget(label)
    
    btn = QPushButton("OK")
    btn.setObjectName("ok_button")
    btn.clicked.connect(lambda: (print("CLICKED: OK button pressed!"), app.quit()))
    layout.addWidget(btn)
    
    window.setLayout(layout)
    window.show()
    
    print(f"Test dialog started. Title: 'Notice', PID: {os.getpid()}")
    sys.exit(app.exec())

if __name__ == "__main__":
    import os
    create_test_dialog()
