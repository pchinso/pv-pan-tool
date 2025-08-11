"""
UI components for PV PAN Tool Desktop Application.

This package contains all the user interface components
for the PyQt6 desktop application.
"""

from .main_window import MainWindow
from .search_widget import SearchWidget
from .compare_widget import CompareWidget
from .stats_widget import StatsWidget
from .settings_dialog import SettingsDialog

__all__ = [
    "MainWindow",
    "SearchWidget", 
    "CompareWidget",
    "StatsWidget",
    "SettingsDialog",
]

