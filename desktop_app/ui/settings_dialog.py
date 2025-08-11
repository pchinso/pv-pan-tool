"""
Settings dialog for PV PAN Tool Desktop Application.

This module provides a comprehensive settings dialog for configuring
the application behavior and preferences.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QStackedWidget,
    QWidget, QLabel, QLineEdit, QPushButton, QCheckBox, QSpinBox,
    QDoubleSpinBox, QComboBox, QColorDialog, QFileDialog, QGroupBox,
    QGridLayout, QSlider, QMessageBox, QDialogButtonBox, QFrame,
    QScrollArea, QTabWidget, QTextEdit
)
from PyQt6.QtCore import Qt, QSettings, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon


class SettingsPage(QWidget):
    """Base class for settings pages."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, title: str):
        super().__init__()
        self.title = title
        self.settings = QSettings()
        
    def load_settings(self):
        """Load settings from QSettings."""
        pass
        
    def save_settings(self):
        """Save settings to QSettings."""
        pass
        
    def reset_to_defaults(self):
        """Reset settings to default values."""
        pass


class DatabaseSettingsPage(SettingsPage):
    """Database settings page."""
    
    def __init__(self):
        super().__init__("Database")
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Database file section
        db_group = QGroupBox("Database File")
        db_layout = QGridLayout(db_group)
        
        # Database path
        db_layout.addWidget(QLabel("Database Path:"), 0, 0)
        self.db_path_edit = QLineEdit()
        self.db_path_browse_btn = QPushButton("Browse...")
        self.db_path_browse_btn.clicked.connect(self.browse_database_path)
        
        db_layout.addWidget(self.db_path_edit, 0, 1)
        db_layout.addWidget(self.db_path_browse_btn, 0, 2)
        
        # Auto backup
        self.auto_backup_check = QCheckBox("Enable automatic backups")
        db_layout.addWidget(self.auto_backup_check, 1, 0, 1, 3)
        
        # Backup frequency
        db_layout.addWidget(QLabel("Backup Frequency:"), 2, 0)
        self.backup_frequency_combo = QComboBox()
        self.backup_frequency_combo.addItems(["Daily", "Weekly", "Monthly"])
        db_layout.addWidget(self.backup_frequency_combo, 2, 1)
        
        # Backup location
        db_layout.addWidget(QLabel("Backup Directory:"), 3, 0)
        self.backup_path_edit = QLineEdit()
        self.backup_path_browse_btn = QPushButton("Browse...")
        self.backup_path_browse_btn.clicked.connect(self.browse_backup_path)
        
        db_layout.addWidget(self.backup_path_edit, 3, 1)
        db_layout.addWidget(self.backup_path_browse_btn, 3, 2)
        
        layout.addWidget(db_group)
        
        # Performance section
        perf_group = QGroupBox("Performance")
        perf_layout = QGridLayout(perf_group)
        
        # Cache size
        perf_layout.addWidget(QLabel("Cache Size (MB):"), 0, 0)
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(10, 1000)
        self.cache_size_spin.setValue(100)
        perf_layout.addWidget(self.cache_size_spin, 0, 1)
        
        # Vacuum frequency
        perf_layout.addWidget(QLabel("Optimize Database:"), 1, 0)
        self.vacuum_frequency_combo = QComboBox()
        self.vacuum_frequency_combo.addItems(["Never", "Weekly", "Monthly"])
        perf_layout.addWidget(self.vacuum_frequency_combo, 1, 1)
        
        layout.addWidget(perf_group)
        layout.addStretch()
        
    def browse_database_path(self):
        """Browse for database file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Database File",
            str(Path.home()),
            "SQLite Database (*.db);;All Files (*)"
        )
        if file_path:
            self.db_path_edit.setText(file_path)
            
    def browse_backup_path(self):
        """Browse for backup directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Backup Directory",
            str(Path.home())
        )
        if directory:
            self.backup_path_edit.setText(directory)
            
    def load_settings(self):
        """Load database settings."""
        self.db_path_edit.setText(
            self.settings.value("database/path", "data/database/pv_modules.db")
        )
        self.auto_backup_check.setChecked(
            self.settings.value("database/auto_backup", True, type=bool)
        )
        self.backup_frequency_combo.setCurrentText(
            self.settings.value("database/backup_frequency", "Weekly")
        )
        self.backup_path_edit.setText(
            self.settings.value("database/backup_path", str(Path.home() / "PV_Backups"))
        )
        self.cache_size_spin.setValue(
            self.settings.value("database/cache_size", 100, type=int)
        )
        self.vacuum_frequency_combo.setCurrentText(
            self.settings.value("database/vacuum_frequency", "Monthly")
        )
        
    def save_settings(self):
        """Save database settings."""
        self.settings.setValue("database/path", self.db_path_edit.text())
        self.settings.setValue("database/auto_backup", self.auto_backup_check.isChecked())
        self.settings.setValue("database/backup_frequency", self.backup_frequency_combo.currentText())
        self.settings.setValue("database/backup_path", self.backup_path_edit.text())
        self.settings.setValue("database/cache_size", self.cache_size_spin.value())
        self.settings.setValue("database/vacuum_frequency", self.vacuum_frequency_combo.currentText())
        
    def reset_to_defaults(self):
        """Reset to default values."""
        self.db_path_edit.setText("data/database/pv_modules.db")
        self.auto_backup_check.setChecked(True)
        self.backup_frequency_combo.setCurrentText("Weekly")
        self.backup_path_edit.setText(str(Path.home() / "PV_Backups"))
        self.cache_size_spin.setValue(100)
        self.vacuum_frequency_combo.setCurrentText("Monthly")


class AppearanceSettingsPage(SettingsPage):
    """Appearance settings page."""
    
    def __init__(self):
        super().__init__("Appearance")
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Theme section
        theme_group = QGroupBox("Theme")
        theme_layout = QGridLayout(theme_group)
        
        # Theme selection
        theme_layout.addWidget(QLabel("Application Theme:"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "Auto (System)"])
        theme_layout.addWidget(self.theme_combo, 0, 1)
        
        # Accent color
        theme_layout.addWidget(QLabel("Accent Color:"), 1, 0)
        self.accent_color_btn = QPushButton()
        self.accent_color_btn.setFixedSize(50, 30)
        self.accent_color_btn.clicked.connect(self.choose_accent_color)
        theme_layout.addWidget(self.accent_color_btn, 1, 1)
        
        layout.addWidget(theme_group)
        
        # Font section
        font_group = QGroupBox("Font")
        font_layout = QGridLayout(font_group)
        
        # Font family
        font_layout.addWidget(QLabel("Font Family:"), 0, 0)
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems([
            "System Default", "Arial", "Helvetica", "Segoe UI", 
            "Roboto", "Open Sans", "Ubuntu"
        ])
        font_layout.addWidget(self.font_family_combo, 0, 1)
        
        # Font size
        font_layout.addWidget(QLabel("Font Size:"), 1, 0)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(10)
        font_layout.addWidget(self.font_size_spin, 1, 1)
        
        layout.addWidget(font_group)
        
        # Chart colors section
        chart_group = QGroupBox("Chart Colors")
        chart_layout = QGridLayout(chart_group)
        
        chart_layout.addWidget(QLabel("Chart Color Scheme:"), 0, 0)
        self.chart_colors_combo = QComboBox()
        self.chart_colors_combo.addItems([
            "Default", "Colorful", "Pastel", "Professional", "High Contrast"
        ])
        chart_layout.addWidget(self.chart_colors_combo, 0, 1)
        
        layout.addWidget(chart_group)
        layout.addStretch()
        
    def choose_accent_color(self):
        """Choose accent color."""
        color = QColorDialog.getColor(QColor("#3daee9"), self, "Choose Accent Color")
        if color.isValid():
            self.accent_color_btn.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #555;"
            )
            self.accent_color = color.name()
            
    def load_settings(self):
        """Load appearance settings."""
        self.theme_combo.setCurrentText(
            self.settings.value("appearance/theme", "Dark")
        )
        
        accent_color = self.settings.value("appearance/accent_color", "#3daee9")
        self.accent_color = accent_color
        self.accent_color_btn.setStyleSheet(
            f"background-color: {accent_color}; border: 1px solid #555;"
        )
        
        self.font_family_combo.setCurrentText(
            self.settings.value("appearance/font_family", "System Default")
        )
        self.font_size_spin.setValue(
            self.settings.value("appearance/font_size", 10, type=int)
        )
        self.chart_colors_combo.setCurrentText(
            self.settings.value("appearance/chart_colors", "Default")
        )
        
    def save_settings(self):
        """Save appearance settings."""
        self.settings.setValue("appearance/theme", self.theme_combo.currentText())
        self.settings.setValue("appearance/accent_color", getattr(self, 'accent_color', '#3daee9'))
        self.settings.setValue("appearance/font_family", self.font_family_combo.currentText())
        self.settings.setValue("appearance/font_size", self.font_size_spin.value())
        self.settings.setValue("appearance/chart_colors", self.chart_colors_combo.currentText())
        
    def reset_to_defaults(self):
        """Reset to default values."""
        self.theme_combo.setCurrentText("Dark")
        self.accent_color = "#3daee9"
        self.accent_color_btn.setStyleSheet(
            f"background-color: {self.accent_color}; border: 1px solid #555;"
        )
        self.font_family_combo.setCurrentText("System Default")
        self.font_size_spin.setValue(10)
        self.chart_colors_combo.setCurrentText("Default")


class SearchDisplaySettingsPage(SettingsPage):
    """Search and display settings page."""
    
    def __init__(self):
        super().__init__("Search & Display")
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Search settings
        search_group = QGroupBox("Search Settings")
        search_layout = QGridLayout(search_group)
        
        # Results per page
        search_layout.addWidget(QLabel("Results per page:"), 0, 0)
        self.results_per_page_spin = QSpinBox()
        self.results_per_page_spin.setRange(10, 1000)
        self.results_per_page_spin.setValue(100)
        search_layout.addWidget(self.results_per_page_spin, 0, 1)
        
        # Auto-search delay
        search_layout.addWidget(QLabel("Auto-search delay (ms):"), 1, 0)
        self.auto_search_delay_spin = QSpinBox()
        self.auto_search_delay_spin.setRange(100, 2000)
        self.auto_search_delay_spin.setValue(500)
        search_layout.addWidget(self.auto_search_delay_spin, 1, 1)
        
        # Max search history
        search_layout.addWidget(QLabel("Max search history:"), 2, 0)
        self.max_search_history_spin = QSpinBox()
        self.max_search_history_spin.setRange(10, 200)
        self.max_search_history_spin.setValue(50)
        search_layout.addWidget(self.max_search_history_spin, 2, 1)
        
        layout.addWidget(search_group)
        
        # Display settings
        display_group = QGroupBox("Display Settings")
        display_layout = QGridLayout(display_group)
        
        # Default sort
        display_layout.addWidget(QLabel("Default sort column:"), 0, 0)
        self.default_sort_combo = QComboBox()
        self.default_sort_combo.addItems([
            "Power (pmax_stc)", "Efficiency (efficiency_stc)", 
            "Manufacturer", "Model", "ID"
        ])
        display_layout.addWidget(self.default_sort_combo, 0, 1)
        
        # Sort order
        display_layout.addWidget(QLabel("Default sort order:"), 1, 0)
        self.sort_order_combo = QComboBox()
        self.sort_order_combo.addItems(["Descending", "Ascending"])
        display_layout.addWidget(self.sort_order_combo, 1, 1)
        
        layout.addWidget(display_group)
        layout.addStretch()
        
    def load_settings(self):
        """Load search and display settings."""
        self.results_per_page_spin.setValue(
            self.settings.value("search/results_per_page", 100, type=int)
        )
        self.auto_search_delay_spin.setValue(
            self.settings.value("search/auto_search_delay", 500, type=int)
        )
        self.max_search_history_spin.setValue(
            self.settings.value("search/max_search_history", 50, type=int)
        )
        self.default_sort_combo.setCurrentText(
            self.settings.value("display/default_sort", "Power (pmax_stc)")
        )
        self.sort_order_combo.setCurrentText(
            self.settings.value("display/sort_order", "Descending")
        )
        
    def save_settings(self):
        """Save search and display settings."""
        self.settings.setValue("search/results_per_page", self.results_per_page_spin.value())
        self.settings.setValue("search/auto_search_delay", self.auto_search_delay_spin.value())
        self.settings.setValue("search/max_search_history", self.max_search_history_spin.value())
        self.settings.setValue("display/default_sort", self.default_sort_combo.currentText())
        self.settings.setValue("display/sort_order", self.sort_order_combo.currentText())
        
    def reset_to_defaults(self):
        """Reset to default values."""
        self.results_per_page_spin.setValue(100)
        self.auto_search_delay_spin.setValue(500)
        self.max_search_history_spin.setValue(50)
        self.default_sort_combo.setCurrentText("Power (pmax_stc)")
        self.sort_order_combo.setCurrentText("Descending")


class PerformanceSettingsPage(SettingsPage):
    """Performance settings page."""
    
    def __init__(self):
        super().__init__("Performance")
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Parsing settings
        parsing_group = QGroupBox("Parsing Performance")
        parsing_layout = QGridLayout(parsing_group)
        
        # Number of threads
        parsing_layout.addWidget(QLabel("Parsing threads:"), 0, 0)
        self.parsing_threads_spin = QSpinBox()
        self.parsing_threads_spin.setRange(1, 16)
        self.parsing_threads_spin.setValue(4)
        parsing_layout.addWidget(self.parsing_threads_spin, 0, 1)
        
        # Batch size
        parsing_layout.addWidget(QLabel("Batch size:"), 1, 0)
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(10, 1000)
        self.batch_size_spin.setValue(100)
        parsing_layout.addWidget(self.batch_size_spin, 1, 1)
        
        layout.addWidget(parsing_group)
        
        # Memory settings
        memory_group = QGroupBox("Memory Management")
        memory_layout = QGridLayout(memory_group)
        
        # Memory limit
        memory_layout.addWidget(QLabel("Memory limit (MB):"), 0, 0)
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(256, 8192)
        self.memory_limit_spin.setValue(1024)
        memory_layout.addWidget(self.memory_limit_spin, 0, 1)
        
        # Enable lazy loading
        self.lazy_loading_check = QCheckBox("Enable lazy loading for large datasets")
        self.lazy_loading_check.setChecked(True)
        memory_layout.addWidget(self.lazy_loading_check, 1, 0, 1, 2)
        
        # Background processing
        self.background_processing_check = QCheckBox("Enable background processing")
        self.background_processing_check.setChecked(True)
        memory_layout.addWidget(self.background_processing_check, 2, 0, 1, 2)
        
        layout.addWidget(memory_group)
        
        # Timeout settings
        timeout_group = QGroupBox("Timeouts")
        timeout_layout = QGridLayout(timeout_group)
        
        # Operation timeout
        timeout_layout.addWidget(QLabel("Operation timeout (seconds):"), 0, 0)
        self.operation_timeout_spin = QSpinBox()
        self.operation_timeout_spin.setRange(10, 300)
        self.operation_timeout_spin.setValue(60)
        timeout_layout.addWidget(self.operation_timeout_spin, 0, 1)
        
        layout.addWidget(timeout_group)
        layout.addStretch()
        
    def load_settings(self):
        """Load performance settings."""
        self.parsing_threads_spin.setValue(
            self.settings.value("performance/parsing_threads", 4, type=int)
        )
        self.batch_size_spin.setValue(
            self.settings.value("performance/batch_size", 100, type=int)
        )
        self.memory_limit_spin.setValue(
            self.settings.value("performance/memory_limit", 1024, type=int)
        )
        self.lazy_loading_check.setChecked(
            self.settings.value("performance/lazy_loading", True, type=bool)
        )
        self.background_processing_check.setChecked(
            self.settings.value("performance/background_processing", True, type=bool)
        )
        self.operation_timeout_spin.setValue(
            self.settings.value("performance/operation_timeout", 60, type=int)
        )
        
    def save_settings(self):
        """Save performance settings."""
        self.settings.setValue("performance/parsing_threads", self.parsing_threads_spin.value())
        self.settings.setValue("performance/batch_size", self.batch_size_spin.value())
        self.settings.setValue("performance/memory_limit", self.memory_limit_spin.value())
        self.settings.setValue("performance/lazy_loading", self.lazy_loading_check.isChecked())
        self.settings.setValue("performance/background_processing", self.background_processing_check.isChecked())
        self.settings.setValue("performance/operation_timeout", self.operation_timeout_spin.value())
        
    def reset_to_defaults(self):
        """Reset to default values."""
        self.parsing_threads_spin.setValue(4)
        self.batch_size_spin.setValue(100)
        self.memory_limit_spin.setValue(1024)
        self.lazy_loading_check.setChecked(True)
        self.background_processing_check.setChecked(True)
        self.operation_timeout_spin.setValue(60)


class SettingsDialog(QDialog):
    """Main settings dialog."""
    
    settings_applied = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.settings_pages = {}
        self.init_ui()
        self.setup_connections()
        
        # Set dialog properties
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(800, 600)
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Categories list
        self.categories_list = QListWidget()
        self.categories_list.setMaximumWidth(200)
        self.categories_list.setStyleSheet("""
            QListWidget {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #555555;
            }
            QListWidget::item:selected {
                background-color: #3daee9;
            }
        """)
        
        # Settings pages stack
        self.pages_stack = QStackedWidget()
        
        # Create settings pages
        self.create_settings_pages()
        
        # Buttons
        buttons_layout = QVBoxLayout()
        
        # Action buttons
        self.apply_btn = QPushButton("Apply")
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        self.reset_btn = QPushButton("Reset to Defaults")
        
        buttons_layout.addWidget(self.apply_btn)
        buttons_layout.addWidget(self.ok_btn)
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addSeparator()
        buttons_layout.addWidget(self.reset_btn)
        buttons_layout.addStretch()
        
        # Main layout
        content_layout = QVBoxLayout()
        content_layout.addWidget(self.pages_stack)
        
        layout.addWidget(self.categories_list)
        layout.addLayout(content_layout, 1)
        layout.addLayout(buttons_layout)
        
    def create_settings_pages(self):
        """Create all settings pages."""
        pages = [
            DatabaseSettingsPage(),
            AppearanceSettingsPage(),
            SearchDisplaySettingsPage(),
            PerformanceSettingsPage()
        ]
        
        for page in pages:
            self.add_settings_page(page)
            
        # Select first page
        if self.categories_list.count() > 0:
            self.categories_list.setCurrentRow(0)
            
    def add_settings_page(self, page: SettingsPage):
        """Add a settings page."""
        self.settings_pages[page.title] = page
        self.categories_list.addItem(page.title)
        self.pages_stack.addWidget(page)
        
    def setup_connections(self):
        """Setup signal connections."""
        self.categories_list.currentRowChanged.connect(self.pages_stack.setCurrentIndex)
        
        self.apply_btn.clicked.connect(self.apply_settings)
        self.ok_btn.clicked.connect(self.accept_settings)
        self.cancel_btn.clicked.connect(self.reject)
        self.reset_btn.clicked.connect(self.reset_current_page)
        
    def apply_settings(self):
        """Apply all settings."""
        try:
            for page in self.settings_pages.values():
                page.save_settings()
                
            # Emit signal
            self.settings_applied.emit()
            
            QMessageBox.information(
                self,
                "Settings Applied",
                "Settings have been applied successfully.\n"
                "Some changes may require restarting the application."
            )
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Settings Error",
                f"Failed to apply settings:\n{str(e)}"
            )
            
    def accept_settings(self):
        """Accept and apply settings."""
        self.apply_settings()
        self.accept()
        
    def reset_current_page(self):
        """Reset current page to defaults."""
        current_index = self.categories_list.currentRow()
        if current_index >= 0:
            page_title = self.categories_list.item(current_index).text()
            page = self.settings_pages.get(page_title)
            
            if page:
                reply = QMessageBox.question(
                    self,
                    "Reset Settings",
                    f"Are you sure you want to reset {page_title} settings to defaults?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    page.reset_to_defaults()
                    
    def get_setting(self, key: str, default_value=None):
        """Get a setting value."""
        settings = QSettings()
        return settings.value(key, default_value)
        
    def set_setting(self, key: str, value):
        """Set a setting value."""
        settings = QSettings()
        settings.setValue(key, value)
        
    @staticmethod
    def get_database_path():
        """Get database path from settings."""
        settings = QSettings()
        return settings.value("database/path", "data/database/pv_modules.db")
        
    @staticmethod
    def get_theme():
        """Get theme from settings."""
        settings = QSettings()
        return settings.value("appearance/theme", "Dark")
        
    @staticmethod
    def get_accent_color():
        """Get accent color from settings."""
        settings = QSettings()
        return settings.value("appearance/accent_color", "#3daee9")
        
    @staticmethod
    def get_results_per_page():
        """Get results per page from settings."""
        settings = QSettings()
        return settings.value("search/results_per_page", 100, type=int)
        
    @staticmethod
    def get_parsing_threads():
        """Get parsing threads from settings."""
        settings = QSettings()
        return settings.value("performance/parsing_threads", 4, type=int)

