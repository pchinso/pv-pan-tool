"""
Main window for PV PAN Tool Desktop Application.

This module contains the main window class that serves as the
primary interface for the application.
"""

import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

# Import controllers
sys.path.append(str(Path(__file__).parent.parent))
from controllers.database_controller import DatabaseController
from controllers.export_controller import ExportController
from controllers.search_controller import SearchController

from .compare_widget import CompareWidget

# Import UI widgets
from .search_widget import SearchWidget
from .settings_dialog import SettingsDialog
from .stats_widget import StatsWidget


class DatabaseStatusWorker(QThread):
    """Worker thread for checking database status."""

    status_updated = pyqtSignal(dict)

    def __init__(self, db_controller):
        super().__init__()
        self.db_controller = db_controller
        self.running = True

    def run(self):
        """Run the status check loop."""
        while self.running:
            try:
                stats = self.db_controller.get_basic_statistics()
                self.status_updated.emit(stats)
            except Exception as e:
                self.status_updated.emit({"error": str(e)})

            # Wait 30 seconds before next check
            self.msleep(30000)

    def stop(self):
        """Stop the worker thread."""
        self.running = False
        self.quit()
        self.wait()


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Initialize controllers
        self.db_controller = DatabaseController()
        self.search_controller = SearchController(self.db_controller)
        self.export_controller = ExportController(self.db_controller)

        # Initialize UI
        self.init_ui()
        self.init_menu_bar()
        self.init_tool_bar()
        self.init_status_bar()

        # Initialize status worker
        self.status_worker = DatabaseStatusWorker(self.db_controller)
        self.status_worker.status_updated.connect(self.update_status)
        self.status_worker.start()

        # Set window properties
        self.setWindowTitle("PV PAN Tool - Photovoltaic Module Database")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # Center window on screen
        self.center_on_screen()

        # Load initial data
        self.load_initial_data()

    def init_ui(self):
        """Initialize the main user interface."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Create header section
        header_frame = self.create_header_section()
        main_layout.addWidget(header_frame)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(True)

        # Create and add tabs
        self.create_tabs()

        main_layout.addWidget(self.tab_widget)

    def create_header_section(self):
        """Create the header section with logo and quick stats."""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_frame.setMaximumHeight(80)

        header_layout = QHBoxLayout(header_frame)

        # Logo and title section
        title_layout = QVBoxLayout()

        title_label = QLabel("PV PAN Tool")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #3daee9;
                margin: 0px;
            }
        """)

        subtitle_label = QLabel("Photovoltaic Module Database & Analysis Tool")
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #cccccc;
                margin: 0px;
            }
        """)

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        title_layout.addStretch()

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        # Quick stats section
        self.stats_layout = QHBoxLayout()
        self.create_quick_stats()
        header_layout.addLayout(self.stats_layout)

        return header_frame

    def create_quick_stats(self):
        """Create quick statistics display."""
        # Total modules stat
        self.total_modules_label = QLabel("Modules: --")
        self.total_modules_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
                background-color: #404040;
                padding: 8px 12px;
                border-radius: 4px;
                margin: 2px;
            }
        """)

        # Total manufacturers stat
        self.total_manufacturers_label = QLabel("Manufacturers: --")
        self.total_manufacturers_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
                background-color: #404040;
                padding: 8px 12px;
                border-radius: 4px;
                margin: 2px;
            }
        """)

        # Database status
        self.db_status_label = QLabel("DB: Checking...")
        self.db_status_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
                background-color: #f39c12;
                padding: 8px 12px;
                border-radius: 4px;
                margin: 2px;
            }
        """)

        self.stats_layout.addWidget(self.total_modules_label)
        self.stats_layout.addWidget(self.total_manufacturers_label)
        self.stats_layout.addWidget(self.db_status_label)

    def create_tabs(self):
        """Create and configure all tabs."""
        # Dashboard tab
        self.dashboard_widget = self.create_dashboard_widget()
        self.tab_widget.addTab(self.dashboard_widget, "📊 Dashboard")

        # Search tab
        self.search_widget = SearchWidget(self.search_controller)
        self.tab_widget.addTab(self.search_widget, "🔍 Search")

        # Compare tab (pass export controller to enable export functionality)
        self.compare_widget = CompareWidget(self.db_controller, export_controller=self.export_controller)
        self.tab_widget.addTab(self.compare_widget, "⚖️ Compare")

        # Statistics tab
        self.stats_widget = StatsWidget(self.db_controller)
        self.tab_widget.addTab(self.stats_widget, "📈 Statistics")

        # Parse tab
        self.parse_widget = self.create_parse_widget()
        self.tab_widget.addTab(self.parse_widget, "📁 Parse Files")

        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # Setup widget connections
        self.setup_widget_connections()

    def setup_widget_connections(self):
        """Setup connections between widgets."""
        # Connect search widget to compare widget
        self.search_widget.modules_selected.connect(self.on_modules_selected_for_comparison)

        # Connect compare widget changes
        self.compare_widget.modules_changed.connect(self.on_comparison_modules_changed)

    def on_modules_selected_for_comparison(self, modules):
        """Handle modules selected for comparison from search."""
        if len(modules) >= 2:
            # Add modules to comparison
            for module in modules:
                self.compare_widget.add_module_to_comparison(module)

            # Switch to compare tab
            self.tab_widget.setCurrentIndex(2)  # Compare tab index

    def on_comparison_modules_changed(self, modules):
        """Handle changes in comparison modules."""
        # Update header stats or other UI elements if needed
        pass

    def create_dashboard_widget(self):
        """Create the dashboard widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Welcome message
        welcome_label = QLabel("Welcome to PV PAN Tool")
        welcome_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #3daee9;
                padding: 20px;
                text-align: center;
            }
        """)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Quick actions
        actions_frame = QFrame()
        actions_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        actions_layout = QHBoxLayout(actions_frame)

        # Parse files button
        parse_btn = QPushButton("📁 Parse .PAN Files")
        parse_btn.setMinimumHeight(60)
        parse_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(4))

        # Search modules button
        search_btn = QPushButton("🔍 Search Modules")
        search_btn.setMinimumHeight(60)
        search_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))

        # View statistics button
        stats_btn = QPushButton("📈 View Statistics")
        stats_btn.setMinimumHeight(60)
        stats_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(3))

        actions_layout.addWidget(parse_btn)
        actions_layout.addWidget(search_btn)
        actions_layout.addWidget(stats_btn)

        layout.addWidget(welcome_label)
        layout.addWidget(actions_frame)
        layout.addStretch()

        return widget

    def create_parse_widget(self):
        """Create the file parsing widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Title
        title_label = QLabel("Parse .PAN Files")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #3daee9;
                padding: 10px;
            }
        """)

        # Parse controls
        controls_frame = QFrame()
        controls_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        controls_layout = QVBoxLayout(controls_frame)

        # Directory selection
        dir_layout = QHBoxLayout()
        dir_label = QLabel("Directory:")
        self.dir_path_label = QLabel("Not selected")
        select_dir_btn = QPushButton("Select Directory")
        select_dir_btn.clicked.connect(self.select_parse_directory)

        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.dir_path_label, 1)
        dir_layout.addWidget(select_dir_btn)

        # Parse options
        options_layout = QHBoxLayout()
        self.new_only_check = QPushButton("New Files Only")
        self.new_only_check.setCheckable(True)
        self.verbose_check = QPushButton("Verbose Output")
        self.verbose_check.setCheckable(True)

        options_layout.addWidget(self.new_only_check)
        options_layout.addWidget(self.verbose_check)
        options_layout.addStretch()

        # Parse button
        self.parse_btn = QPushButton("🚀 Start Parsing")
        self.parse_btn.setMinimumHeight(40)
        self.parse_btn.clicked.connect(self.start_parsing)

        # Progress bar
        self.parse_progress = QProgressBar()
        self.parse_progress.setVisible(False)

        controls_layout.addLayout(dir_layout)
        controls_layout.addLayout(options_layout)
        controls_layout.addWidget(self.parse_btn)
        controls_layout.addWidget(self.parse_progress)

        layout.addWidget(title_label)
        layout.addWidget(controls_frame)
        layout.addStretch()

        return widget

    def init_menu_bar(self):
        """Initialize the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # Parse action
        parse_action = QAction("&Parse Files...", self)
        parse_action.setShortcut("Ctrl+P")
        parse_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(4))
        file_menu.addAction(parse_action)

        file_menu.addSeparator()

        # Export action
        export_action = QAction("&Export Data...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.show_export_dialog)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        # Refresh action
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_data)
        view_menu.addAction(refresh_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        # Settings action
        settings_action = QAction("&Settings...", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)

        # Database menu
        database_menu = menubar.addMenu("&Database")

        # Backup action
        backup_action = QAction("&Backup Database...", self)
        backup_action.triggered.connect(self.backup_database)
        database_menu.addAction(backup_action)

        # Optimize action
        optimize_action = QAction("&Optimize Database", self)
        optimize_action.triggered.connect(self.optimize_database)
        database_menu.addAction(optimize_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def init_tool_bar(self):
        """Initialize the tool bar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Parse action
        parse_action = QAction("📁 Parse", self)
        parse_action.setToolTip("Parse .PAN files")
        parse_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(4))
        toolbar.addAction(parse_action)

        # Search action
        search_action = QAction("🔍 Search", self)
        search_action.setToolTip("Search modules")
        search_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        toolbar.addAction(search_action)

        # Compare action
        compare_action = QAction("⚖️ Compare", self)
        compare_action.setToolTip("Compare modules")
        compare_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        toolbar.addAction(compare_action)

        toolbar.addSeparator()

        # Refresh action
        refresh_action = QAction("🔄 Refresh", self)
        refresh_action.setToolTip("Refresh data")
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)

        # Export action
        export_action = QAction("📤 Export", self)
        export_action.setToolTip("Export data")
        export_action.triggered.connect(self.show_export_dialog)
        toolbar.addAction(export_action)

    def init_status_bar(self):
        """Initialize the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Status message
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        # Progress bar for operations
        self.operation_progress = QProgressBar()
        self.operation_progress.setMaximumWidth(200)
        self.operation_progress.setVisible(False)
        self.status_bar.addPermanentWidget(self.operation_progress)

        # Database connection status
        self.connection_status = QLabel("🔗 Connected")
        self.status_bar.addPermanentWidget(self.connection_status)

    def center_on_screen(self):
        """Center the window on the screen."""
        screen = self.screen().availableGeometry()
        window = self.frameGeometry()
        window.moveCenter(screen.center())
        self.move(window.topLeft())

    def load_initial_data(self):
        """Load initial data and update UI."""
        try:
            # Update quick stats
            self.update_quick_stats()

            # Set status
            self.status_label.setText("Application loaded successfully")

        except Exception as e:
            self.status_label.setText(f"Error loading data: {str(e)}")
            QMessageBox.warning(
                self,
                "Loading Error",
                f"Failed to load initial data:\n\n{str(e)}"
            )

    def update_quick_stats(self):
        """Update the quick statistics display."""
        try:
            stats = self.db_controller.get_basic_statistics()

            total_modules = stats.get('total_modules', 0)
            total_manufacturers = stats.get('total_manufacturers', 0)

            self.total_modules_label.setText(f"Modules: {total_modules:,}")
            self.total_manufacturers_label.setText(f"Manufacturers: {total_manufacturers}")

            # Update database status
            if total_modules > 0:
                self.db_status_label.setText("DB: Connected")
                self.db_status_label.setStyleSheet("""
                    QLabel {
                        font-size: 14px;
                        font-weight: bold;
                        color: #ffffff;
                        background-color: #27ae60;
                        padding: 8px 12px;
                        border-radius: 4px;
                        margin: 2px;
                    }
                """)
            else:
                self.db_status_label.setText("DB: Empty")
                self.db_status_label.setStyleSheet("""
                    QLabel {
                        font-size: 14px;
                        font-weight: bold;
                        color: #ffffff;
                        background-color: #f39c12;
                        padding: 8px 12px;
                        border-radius: 4px;
                        margin: 2px;
                    }
                """)

        except Exception as e:
            self.db_status_label.setText("DB: Error")
            self.db_status_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: #ffffff;
                    background-color: #e74c3c;
                    padding: 8px 12px;
                    border-radius: 4px;
                    margin: 2px;
                }
            """)

    def update_status(self, stats):
        """Update status from worker thread."""
        if "error" in stats:
            self.connection_status.setText("❌ Error")
            self.connection_status.setToolTip(f"Database error: {stats['error']}")
        else:
            self.connection_status.setText("🔗 Connected")
            self.connection_status.setToolTip("Database connection active")

            # Update quick stats
            total_modules = stats.get('total_modules', 0)
            total_manufacturers = stats.get('total_manufacturers', 0)

            self.total_modules_label.setText(f"Modules: {total_modules:,}")
            self.total_manufacturers_label.setText(f"Manufacturers: {total_manufacturers}")

    def on_tab_changed(self, index):
        """Handle tab change events."""
        tab_names = ["Dashboard", "Search", "Compare", "Statistics", "Parse Files"]
        if 0 <= index < len(tab_names):
            self.status_label.setText(f"Switched to {tab_names[index]} tab")

            # Refresh data for specific tabs
            if index == 3:  # Statistics tab
                self.stats_widget.refresh_data()

    def select_parse_directory(self):
        """Select directory for parsing .PAN files."""
        from PyQt6.QtWidgets import QFileDialog

        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory with .PAN Files",
            str(Path.home())
        )

        if directory:
            self.dir_path_label.setText(directory)
            self.parse_btn.setEnabled(True)

    def start_parsing(self):
        """Start parsing .PAN files."""
        directory = self.dir_path_label.text()
        if directory == "Not selected":
            QMessageBox.warning(self, "No Directory", "Please select a directory first.")
            return

        # TODO: Implement parsing logic
        QMessageBox.information(self, "Parsing", "Parsing functionality will be implemented.")

    def refresh_data(self):
        """Refresh all data in the application."""
        self.status_label.setText("Refreshing data...")

        try:
            # Update quick stats
            self.update_quick_stats()

            # Refresh current tab
            current_index = self.tab_widget.currentIndex()
            if current_index == 1:  # Search tab
                self.search_widget.refresh_data()
            elif current_index == 2:  # Compare tab
                self.compare_widget.refresh_data()
            elif current_index == 3:  # Statistics tab
                self.stats_widget.refresh_data()

            self.status_label.setText("Data refreshed successfully")

        except Exception as e:
            self.status_label.setText(f"Error refreshing data: {str(e)}")
            QMessageBox.warning(
                self,
                "Refresh Error",
                f"Failed to refresh data:\n\n{str(e)}"
            )

    def show_export_dialog(self):
        """Show export dialog."""
        # TODO: Implement export dialog
        QMessageBox.information(self, "Export", "Export dialog will be implemented.")

    def show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec()

    def backup_database(self):
        """Backup the database."""
        # TODO: Implement database backup
        QMessageBox.information(self, "Backup", "Database backup will be implemented.")

    def optimize_database(self):
        """Optimize the database."""
        # TODO: Implement database optimization
        QMessageBox.information(self, "Optimize", "Database optimization will be implemented.")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About PV PAN Tool",
            """
            <h3>PV PAN Tool v1.0.0</h3>
            <p>A comprehensive tool for parsing, analyzing, and comparing
            photovoltaic module specifications from .PAN files.</p>

            <p><b>Features:</b></p>
            <ul>
            <li>Parse .PAN files into structured database</li>
            <li>Advanced search and filtering</li>
            <li>Module comparison and analysis</li>
            <li>Statistical analysis and reporting</li>
            <li>Data export in multiple formats</li>
            </ul>

            <p><b>Built with:</b> Python, PyQt6, SQLite</p>
            <p><b>Copyright:</b> 2024 PV Tools</p>
            """
        )

    def closeEvent(self, event):
        """Handle application close event."""
        # Stop status worker
        if hasattr(self, 'status_worker'):
            self.status_worker.stop()

        # Accept the close event
        event.accept()

            <p><b>Copyright:</b> 2024 PV Tools</p>
            """
        )

    def closeEvent(self, event):
        """Handle application close event."""
        # Stop status worker
        if hasattr(self, 'status_worker'):
            self.status_worker.stop()

        # Accept the close event
        event.accept()
