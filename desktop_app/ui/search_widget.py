"""
Search widget for PV PAN Tool Desktop Application.

This module provides advanced search functionality with filters,
results display, and export capabilities.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class SearchWorker(QThread):
    """Worker thread for search operations."""

    search_completed = pyqtSignal(dict)
    search_error = pyqtSignal(str)

    def __init__(self, search_controller, search_params):
        super().__init__()
        self.search_controller = search_controller
        self.search_params = search_params

    def run(self):
        """Execute search in background."""
        try:
            modules = self.search_controller.search_modules(self.search_params)
            payload = {"success": True, "modules": modules}
            self.search_completed.emit(payload)
        except Exception as e:
            self.search_error.emit(str(e))


class SearchWidget(QWidget):
    """Widget for advanced module search."""

    # Signals
    modules_selected = pyqtSignal(list)  # Emitted when modules are selected

    def __init__(self, search_controller):
        super().__init__()

        self.search_controller = search_controller
        self.current_results = []
        self.selected_modules = []

        # Search delay timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

        self.init_ui()
        self.setup_connections()

        # Load initial filter options
        QTimer.singleShot(100, self.load_filter_options)

    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_layout = self.create_header_section()
        main_layout.addLayout(header_layout)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Filters panel
        filters_widget = self.create_filters_panel()
        splitter.addWidget(filters_widget)

        # Results panel
        results_widget = self.create_results_panel()
        splitter.addWidget(results_widget)

        # Set splitter proportions
        splitter.setSizes([300, 700])
        main_layout.addWidget(splitter)

    def create_header_section(self):
        """Create the header section."""
        layout = QHBoxLayout()

        # Title
        title_label = QLabel("Search Modules")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #3daee9;
                padding: 5px;
            }
        """)

        # Quick search
        self.quick_search = QLineEdit()
        self.quick_search.setPlaceholderText("Quick search by manufacturer, model, or ID...")
        self.quick_search.setMinimumWidth(300)

        # Search button
        self.search_btn = QPushButton("🔍 Search")

        # Clear button
        self.clear_btn = QPushButton("🗑️ Clear")

        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(QLabel("Quick Search:"))
        layout.addWidget(self.quick_search)
        layout.addWidget(self.search_btn)
        layout.addWidget(self.clear_btn)

        return layout

    def create_filters_panel(self):
        """Create the filters panel."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        widget.setMaximumWidth(350)

        # Scroll area for filters
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Filters container
        filters_container = QWidget()
        filters_layout = QVBoxLayout(filters_container)

        # Manufacturer filter
        manufacturer_group = QGroupBox("Manufacturer")
        manufacturer_layout = QVBoxLayout(manufacturer_group)
        self.manufacturer_combo = QComboBox()
        self.manufacturer_combo.setEditable(True)
        manufacturer_layout.addWidget(self.manufacturer_combo)
        filters_layout.addWidget(manufacturer_group)

        # Power filter
        power_group = QGroupBox("Power Range (W)")
        power_layout = QVBoxLayout(power_group)
        power_range_layout = QHBoxLayout()
        self.power_min_spin = QSpinBox()
        self.power_min_spin.setRange(0, 2000)
        self.power_max_spin = QSpinBox()
        self.power_max_spin.setRange(0, 2000)
        self.power_max_spin.setValue(1000)
        power_range_layout.addWidget(QLabel("Min:"))
        power_range_layout.addWidget(self.power_min_spin)
        power_range_layout.addWidget(QLabel("Max:"))
        power_range_layout.addWidget(self.power_max_spin)
        power_layout.addLayout(power_range_layout)
        filters_layout.addWidget(power_group)

        # Size filter (mm)
        size_group = QGroupBox("Size Range (mm)")
        size_layout = QVBoxLayout(size_group)
        # Height row
        height_layout = QHBoxLayout()
        self.height_min_spin = QSpinBox()
        self.height_min_spin.setRange(0, 4000)
        self.height_max_spin = QSpinBox()
        self.height_max_spin.setRange(0, 4000)
        self.height_max_spin.setValue(3000)
        height_layout.addWidget(QLabel("Height Min:"))
        height_layout.addWidget(self.height_min_spin)
        height_layout.addWidget(QLabel("Max:"))
        height_layout.addWidget(self.height_max_spin)
        size_layout.addLayout(height_layout)
        # Width row
        width_layout = QHBoxLayout()
        self.width_min_spin = QSpinBox()
        self.width_min_spin.setRange(0, 3000)
        self.width_max_spin = QSpinBox()
        self.width_max_spin.setRange(0, 3000)
        self.width_max_spin.setValue(2000)
        width_layout.addWidget(QLabel("Width Min:"))
        width_layout.addWidget(self.width_min_spin)
        width_layout.addWidget(QLabel("Max:"))
        width_layout.addWidget(self.width_max_spin)
        size_layout.addLayout(width_layout)
        filters_layout.addWidget(size_group)

        # Efficiency filter
        efficiency_group = QGroupBox("Efficiency Range (%)")
        efficiency_layout = QVBoxLayout(efficiency_group)
        efficiency_range_layout = QHBoxLayout()
        self.efficiency_min_spin = QDoubleSpinBox()
        self.efficiency_min_spin.setRange(0, 30)
        self.efficiency_min_spin.setDecimals(1)
        self.efficiency_max_spin = QDoubleSpinBox()
        self.efficiency_max_spin.setRange(0, 30)
        self.efficiency_max_spin.setValue(25.0)
        self.efficiency_max_spin.setDecimals(1)
        efficiency_range_layout.addWidget(QLabel("Min:"))
        efficiency_range_layout.addWidget(self.efficiency_min_spin)
        efficiency_range_layout.addWidget(QLabel("Max:"))
        efficiency_range_layout.addWidget(self.efficiency_max_spin)
        efficiency_layout.addLayout(efficiency_range_layout)
        filters_layout.addWidget(efficiency_group)

        # Cell type filter
        celltype_group = QGroupBox("Cell Type")
        celltype_layout = QVBoxLayout(celltype_group)
        self.celltype_combo = QComboBox()
        celltype_layout.addWidget(self.celltype_combo)
        filters_layout.addWidget(celltype_group)

        # Module type filter
        moduletype_group = QGroupBox("Module Type")
        moduletype_layout = QVBoxLayout(moduletype_group)
        self.moduletype_combo = QComboBox()
        moduletype_layout.addWidget(self.moduletype_combo)
        filters_layout.addWidget(moduletype_group)

        filters_layout.addStretch()
        scroll_area.setWidget(filters_container)

        layout = QVBoxLayout(widget)
        layout.addWidget(scroll_area)
        return widget

    def create_results_panel(self):
        """Create the results panel."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(widget)

        # Results header
        results_header_layout = QHBoxLayout()

        self.results_label = QLabel("Results: 0 modules")
        self.results_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #3daee9;
                padding: 5px;
            }
        """)

        # Progress bar
        self.search_progress = QProgressBar()
        self.search_progress.setVisible(False)
        self.search_progress.setMaximumWidth(200)

        # Export button
        self.export_btn = QPushButton("📤 Export Results")
        self.export_btn.setEnabled(False)

        # Compare button
        self.compare_btn = QPushButton("⚖️ Compare Selected")
        self.compare_btn.setEnabled(False)

        results_header_layout.addWidget(self.results_label)
        results_header_layout.addWidget(self.search_progress)
        results_header_layout.addStretch()
        results_header_layout.addWidget(self.export_btn)
        results_header_layout.addWidget(self.compare_btn)

        layout.addLayout(results_header_layout)

        # Results table
        self.results_table = self.create_results_table()
        layout.addWidget(self.results_table)

        return widget

    def create_results_table(self):
        """Create the results table."""
        table = QTableWidget()
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        table.setSortingEnabled(True)

        # Set columns
        columns = [
            "ID", "Manufacturer", "Model", "Series", "Power (W)",
            "Efficiency (%)", "Height (mm)", "Width (mm)", "Voc (V)", "Isc (A)",
            "Cell Type", "Module Type"
        ]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)

        # Configure headers
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)

        # Style the table
        table.setStyleSheet("""
            QTableWidget {
                gridline-color: #555555;
                background-color: #2b2b2b;
                alternate-background-color: #353535;
            }
            QTableWidget::item {
                padding: 6px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #3daee9;
            }
            QHeaderView::section {
                background-color: #404040;
                padding: 8px;
                border: 1px solid #555555;
                font-weight: bold;
            }
        """)

        return table

    def setup_connections(self):
        """Setup signal connections."""
        # Search triggers
        self.quick_search.textChanged.connect(self.on_search_text_changed)
        self.search_btn.clicked.connect(self.perform_search)
        self.clear_btn.clicked.connect(self.clear_search)

        # Filter changes
        self.manufacturer_combo.currentTextChanged.connect(self.on_filter_changed)
        self.power_min_spin.valueChanged.connect(self.on_filter_changed)
        self.power_max_spin.valueChanged.connect(self.on_filter_changed)
        self.efficiency_min_spin.valueChanged.connect(self.on_filter_changed)
        self.efficiency_max_spin.valueChanged.connect(self.on_filter_changed)
        self.celltype_combo.currentTextChanged.connect(self.on_filter_changed)
        self.moduletype_combo.currentTextChanged.connect(self.on_filter_changed)
        self.height_min_spin.valueChanged.connect(self.on_filter_changed)
        self.height_max_spin.valueChanged.connect(self.on_filter_changed)
        self.width_min_spin.valueChanged.connect(self.on_filter_changed)
        self.width_max_spin.valueChanged.connect(self.on_filter_changed)

        # Table selection
        self.results_table.itemSelectionChanged.connect(self.on_selection_changed)

        # Action buttons
        self.export_btn.clicked.connect(self.export_results)
        self.compare_btn.clicked.connect(self.compare_selected)

    def load_filter_options(self):
        """Load filter options from database."""
        try:
            options = self.search_controller.get_filter_options()

            # Manufacturers
            manufacturers = ["All"] + options.get("manufacturers", [])
            self.manufacturer_combo.clear()
            self.manufacturer_combo.addItems(manufacturers)

            # Cell types
            cell_types = ["All"] + options.get("cell_types", [])
            self.celltype_combo.clear()
            self.celltype_combo.addItems(cell_types)

            # Module types
            module_types = ["All"] + options.get("module_types", [])
            self.moduletype_combo.clear()
            self.moduletype_combo.addItems(module_types)

            # Power range
            power_range = options.get("power_range", {"min": 0, "max": 1000})
            self.power_min_spin.setMaximum(int(power_range["max"]))
            self.power_max_spin.setMaximum(int(power_range["max"]))
            self.power_max_spin.setValue(int(power_range["max"]))

            # Efficiency range
            efficiency_range = options.get("efficiency_range", {"min": 0, "max": 25})
            self.efficiency_min_spin.setMaximum(efficiency_range["max"])
            self.efficiency_max_spin.setMaximum(efficiency_range["max"])
            self.efficiency_max_spin.setValue(efficiency_range["max"])

            # Size range
            size_range = options.get("size_range", None)
            if size_range:
                hmin = int(size_range.get("height_min", 0))
                hmax = int(size_range.get("height_max", 4000))
                wmin = int(size_range.get("width_min", 0))
                wmax = int(size_range.get("width_max", 3000))
                self.height_min_spin.setMaximum(hmax)
                self.height_max_spin.setMaximum(max(hmax, 1))
                self.height_max_spin.setValue(hmax)
                self.width_min_spin.setMaximum(wmax)
                self.width_max_spin.setMaximum(max(wmax, 1))
                self.width_max_spin.setValue(wmax)

        except Exception as e:
            print(f"Error loading filter options: {e}")

    def on_search_text_changed(self, text):
        """Handle search text changes."""
        # Restart timer for delayed search
        self.search_timer.stop()
        if text.strip():
            self.search_timer.start(500)  # 500ms delay

    def on_filter_changed(self):
        """Handle filter changes."""
        # Trigger search if there are existing results
        if self.current_results:
            self.search_timer.stop()
            self.search_timer.start(300)  # Shorter delay for filters

    def perform_search(self):
        """Perform the search operation."""
        # Build search parameters
        search_params = self.build_search_params()

        # Show progress
        self.search_progress.setVisible(True)
        self.search_btn.setEnabled(False)

        # Start search worker
        self.search_worker = SearchWorker(self.search_controller, search_params)
        self.search_worker.search_completed.connect(self.on_search_completed)
        self.search_worker.search_error.connect(self.on_search_error)
        self.search_worker.start()

    def build_search_params(self):
        """Build search parameters from UI."""
        params = {}

        # Quick search text
        quick_text = self.quick_search.text().strip()
        if quick_text:
            # Try to determine if it's an ID, manufacturer, or model
            if quick_text.isdigit():
                params["id"] = int(quick_text)
            else:
                params["manufacturer"] = quick_text

        # Manufacturer filter
        manufacturer = self.manufacturer_combo.currentText()
        if manufacturer and manufacturer != "All":
            params["manufacturer"] = manufacturer

        # Power range
        power_min = self.power_min_spin.value()
        power_max = self.power_max_spin.value()
        if power_min > 0:
            params["power_min"] = power_min
        if power_max < self.power_max_spin.maximum():
            params["power_max"] = power_max

        # Efficiency range
        eff_min = self.efficiency_min_spin.value()
        eff_max = self.efficiency_max_spin.value()
        if eff_min > 0:
            params["efficiency_min"] = eff_min
        if eff_max < self.efficiency_max_spin.maximum():
            params["efficiency_max"] = eff_max

        # Size ranges (mm)
        hmin = self.height_min_spin.value()
        hmax = self.height_max_spin.value()
        wmin = self.width_min_spin.value()
        wmax = self.width_max_spin.value()
        if hmin > 0:
            params["height_min"] = hmin
        if hmax < self.height_max_spin.maximum():
            params["height_max"] = hmax
        if wmin > 0:
            params["width_min"] = wmin
        if wmax < self.width_max_spin.maximum():
            params["width_max"] = wmax

        # Cell type
        cell_type = self.celltype_combo.currentText()
        if cell_type and cell_type != "All":
            params["cell_type"] = cell_type

        # Module type
        module_type = self.moduletype_combo.currentText()
        if module_type and module_type != "All":
            params["module_type"] = module_type

        # Sorting
        params["sort_by"] = "pmax_stc"
        params["sort_order"] = "desc"
        params["limit"] = 1000

        return params

    def on_search_completed(self, results):
        """Handle search completion."""
        self.search_progress.setVisible(False)
        self.search_btn.setEnabled(True)

        if results.get("success"):
            self.current_results = results.get("modules", [])
            self.update_results_display()

            # Update results label
            count = len(self.current_results)
            self.results_label.setText(f"Results: {count:,} modules")

            # Enable export if we have results
            self.export_btn.setEnabled(count > 0)

        else:
            error = results.get("error", "Unknown error")
            QMessageBox.warning(self, "Search Error", f"Search failed:\n{error}")

    def on_search_error(self, error_message):
        """Handle search error."""
        self.search_progress.setVisible(False)
        self.search_btn.setEnabled(True)

        QMessageBox.warning(
            self,
            "Search Error",
            f"Search operation failed:\n{error_message}"
        )

    def update_results_display(self):
        """Update the results table."""
        table = self.results_table
        table.setRowCount(len(self.current_results))

        for row, module in enumerate(self.current_results):
            # ID
            table.setItem(row, 0, QTableWidgetItem(str(module.get("id", ""))))

            # Manufacturer
            table.setItem(row, 1, QTableWidgetItem(module.get("manufacturer", "")))

            # Model
            table.setItem(row, 2, QTableWidgetItem(module.get("model", "")))

            # Series
            table.setItem(row, 3, QTableWidgetItem(module.get("series", "")))

            # Power
            power = module.get("pmax_stc")
            power_text = f"{power:.0f}" if power else "N/A"
            table.setItem(row, 4, QTableWidgetItem(power_text))

            # Efficiency
            efficiency = module.get("efficiency_stc")
            eff_text = f"{efficiency:.1f}" if efficiency else "N/A"
            table.setItem(row, 5, QTableWidgetItem(eff_text))

            # Height (mm)
            height = module.get("height")
            height_text = f"{height:.0f}" if height else "N/A"
            table.setItem(row, 6, QTableWidgetItem(height_text))

            # Width (mm)
            width = module.get("width")
            width_text = f"{width:.0f}" if width else "N/A"
            table.setItem(row, 7, QTableWidgetItem(width_text))

            # Voc
            voc = module.get("voc_stc")
            voc_text = f"{voc:.1f}" if voc else "N/A"
            table.setItem(row, 8, QTableWidgetItem(voc_text))

            # Isc
            isc = module.get("isc_stc")
            isc_text = f"{isc:.1f}" if isc else "N/A"
            table.setItem(row, 9, QTableWidgetItem(isc_text))

            # Cell Type
            table.setItem(row, 10, QTableWidgetItem(module.get("cell_type", "")))

            # Module Type
            table.setItem(row, 11, QTableWidgetItem(module.get("module_type", "")))

        # Resize columns
        table.resizeColumnsToContents()

    def on_selection_changed(self):
        """Handle table selection changes."""
        selected_rows = set()
        for item in self.results_table.selectedItems():
            selected_rows.add(item.row())

        # Get selected modules
        self.selected_modules = []
        for row in selected_rows:
            if row < len(self.current_results):
                self.selected_modules.append(self.current_results[row])

        # Enable compare button if we have selections
        self.compare_btn.setEnabled(len(self.selected_modules) >= 2)

        # Emit signal
        self.modules_selected.emit(self.selected_modules)

    def clear_search(self):
        """Clear search and filters."""
        # Clear search text
        self.quick_search.clear()

        # Reset filters
        self.manufacturer_combo.setCurrentText("All")
        self.power_min_spin.setValue(0)
        self.power_max_spin.setValue(self.power_max_spin.maximum())
        self.efficiency_min_spin.setValue(0)
        self.efficiency_max_spin.setValue(self.efficiency_max_spin.maximum())
        self.celltype_combo.setCurrentText("All")
        self.moduletype_combo.setCurrentText("All")
        self.height_min_spin.setValue(0)
        self.height_max_spin.setValue(self.height_max_spin.maximum())
        self.width_min_spin.setValue(0)
        self.width_max_spin.setValue(self.width_max_spin.maximum())

        # Clear results
        self.current_results = []
        self.selected_modules = []
        self.results_table.setRowCount(0)
        self.results_label.setText("Results: 0 modules")
        self.export_btn.setEnabled(False)
        self.compare_btn.setEnabled(False)

    def export_results(self):
        """Export search results."""
        if not self.current_results:
            return

        try:
            from pathlib import Path

            from PyQt6.QtWidgets import QFileDialog

            # Default export directory under project root
            project_root = Path(__file__).resolve().parents[2]
            export_dir = project_root / 'data' / 'exports'
            export_dir.mkdir(parents=True, exist_ok=True)

            # Default filename
            default_name = f"search_results_{len(self.current_results)}_modules.csv"
            default_path = export_dir / default_name

            # Get export file path (defaulting to data/exports)
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Search Results",
                str(default_path),
                "CSV Files (*.csv);;JSON Files (*.json);;Excel Files (*.xlsx)"
            )

            if file_path:
                # Use search controller to export
                export_path = self.search_controller.export_search_results(
                    self.current_results,
                    file_path
                )

                if export_path:
                    QMessageBox.information(
                        self,
                        "Export Successful",
                        f"Search results exported successfully to:\n{export_path}"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Export Failed",
                        "Failed to export search results"
                    )

        except Exception as e:
            QMessageBox.warning(
                self,
                "Export Error",
                f"Error during export: {str(e)}"
            )

    def compare_selected(self):
        """Compare selected modules."""
        if len(self.selected_modules) < 2:
            QMessageBox.information(
                self,
                "Selection Required",
                "Please select at least 2 modules to compare."
            )
            return

        # Emit signal with selected modules for comparison
        self.modules_selected.emit(self.selected_modules)

        # Show message
        QMessageBox.information(
            self,
            "Modules Selected",
            f"Selected {len(self.selected_modules)} modules for comparison.\n"
            "Switch to the Compare tab to view the comparison."
        )

    def refresh_data(self):
        """Refresh search data."""
        self.load_filter_options()

        # Re-run search if we have current results
        if self.current_results:
            self.perform_search()

    def get_selected_modules(self):
        """Get currently selected modules."""
        return self.selected_modules.copy()
        return self.selected_modules.copy()
