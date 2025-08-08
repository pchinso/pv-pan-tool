"""
Statistics widget for PV PAN Tool Desktop Application.

Minimal placeholder implementation to allow the application to run.
"""
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class StatsWidget(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Statistics functionality coming soon."))
        layout.addStretch()

    def refresh_data(self):
        # Placeholder for refreshing statistics
        pass
