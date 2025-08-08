#!/usr/bin/env python3
"""
PV PAN Tool Desktop Application

Main entry point for the PyQt6 desktop application.
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

# Add the src directory to the Python path
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

try:
    from pv_pan_tool.database import PVModuleDatabase
    from pv_pan_tool.models import PVModule
    from pv_pan_tool.parser import PANParser
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure the src directory is in the Python path")
    sys.exit(1)

from ui.main_window import MainWindow


class PVPanToolApp(QApplication):
    """Main application class for PV PAN Tool."""
    
    def __init__(self, argv):
        super().__init__(argv)
        
        # Set application properties
        self.setApplicationName("PV PAN Tool")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("PV Tools")
        self.setOrganizationDomain("pvtools.com")
        
        # Set application icon
        icon_path = Path(__file__).parent / "resources" / "icons" / "app_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Set application style
        self.setStyle('Fusion')  # Modern cross-platform style
        
        # Apply dark theme
        self.apply_dark_theme()
        
        # Initialize main window
        self.main_window = None
        
    def apply_dark_theme(self):
        """Apply a dark theme to the application."""
        dark_stylesheet = """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
            selection-background-color: #3daee9;
        }
        
        QTabWidget::pane {
            border: 1px solid #555555;
            background-color: #2b2b2b;
        }
        
        QTabBar::tab {
            background-color: #404040;
            color: #ffffff;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #3daee9;
        }
        
        QTabBar::tab:hover {
            background-color: #505050;
        }
        
        QPushButton {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 6px 12px;
            border-radius: 4px;
            min-width: 80px;
        }
        
        QPushButton:hover {
            background-color: #505050;
        }
        
        QPushButton:pressed {
            background-color: #3daee9;
        }
        
        QPushButton:disabled {
            background-color: #2b2b2b;
            color: #666666;
        }
        
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 4px;
            border-radius: 2px;
        }
        
        QLineEdit:focus, QComboBox:focus {
            border: 2px solid #3daee9;
        }
        
        QTableWidget {
            background-color: #2b2b2b;
            alternate-background-color: #353535;
            gridline-color: #555555;
            selection-background-color: #3daee9;
        }
        
        QHeaderView::section {
            background-color: #404040;
            color: #ffffff;
            padding: 6px;
            border: 1px solid #555555;
        }
        
        QScrollBar:vertical {
            background-color: #404040;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #606060;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #707070;
        }
        
        QProgressBar {
            background-color: #404040;
            border: 1px solid #555555;
            border-radius: 4px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #3daee9;
            border-radius: 3px;
        }
        
        QStatusBar {
            background-color: #404040;
            color: #ffffff;
            border-top: 1px solid #555555;
        }
        
        QMenuBar {
            background-color: #404040;
            color: #ffffff;
            border-bottom: 1px solid #555555;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 4px 8px;
        }
        
        QMenuBar::item:selected {
            background-color: #3daee9;
        }
        
        QMenu {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
        }
        
        QMenu::item {
            padding: 4px 20px;
        }
        
        QMenu::item:selected {
            background-color: #3daee9;
        }
        """
        
        self.setStyleSheet(dark_stylesheet)
    
    def initialize_main_window(self):
        """Initialize and show the main window."""
        try:
            self.main_window = MainWindow()
            self.main_window.show()
            return True
        except Exception as e:
            QMessageBox.critical(
                None,
                "Initialization Error",
                f"Failed to initialize the application:\n\n{str(e)}\n\n"
                "Please check that the database is accessible and try again."
            )
            return False
    
    def run(self):
        """Run the application."""
        if self.initialize_main_window():
            return self.exec()
        else:
            return 1


def main():
    """Main entry point."""
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    # Create application
    app = PVPanToolApp(sys.argv)
    
    # Run application
    exit_code = app.run()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

