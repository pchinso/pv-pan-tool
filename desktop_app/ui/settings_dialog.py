"""
Settings dialog for PV PAN Tool Desktop Application.

Minimal placeholder implementation to allow the application to run.
"""
from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Settings will be available soon."))
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
