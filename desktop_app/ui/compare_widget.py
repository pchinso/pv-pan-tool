"""
Compare widget for PV PAN Tool Desktop Application.

This module provides functionality to compare multiple PV modules
side by side with detailed analysis and visualization.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Import matplotlib for charts (optional)
try:
    from matplotlib.figure import Figure
    try:
        # Preferred for PyQt6 / Matplotlib 3.5+
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    except Exception:
        # Fallback for environments with Qt5 backend
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False


class CompareWidget(QWidget):
    """Widget for comparing PV modules side by side.

    Optionally accepts an export controller to enable exporting comparison
    data directly from this widget.
    """

    # Signals
    modules_changed = pyqtSignal(list)  # Emitted when module selection changes

    def __init__(self, db_controller, export_controller=None):
        super().__init__()

        self.db_controller = db_controller
        # Export controller is optional but enables the Export button flow
        self.export_controller = export_controller
        self.compared_modules = []  # List of module dictionaries
        self.max_modules = 5  # Maximum modules to compare

        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title and controls
        header_layout = self.create_header_section()
        main_layout.addLayout(header_layout)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Module selection section
        selection_widget = self.create_selection_section()
        splitter.addWidget(selection_widget)

        # Comparison table
        self.comparison_table = self.create_comparison_table()
        splitter.addWidget(self.comparison_table)

        # Charts section (if matplotlib available)
        if MATPLOTLIB_AVAILABLE:
            charts_widget = self.create_charts_section()
            splitter.addWidget(charts_widget)

        # Set splitter proportions
        splitter.setSizes([150, 400, 300])
        main_layout.addWidget(splitter)

        # Analysis section
        analysis_widget = self.create_analysis_section()
        main_layout.addWidget(analysis_widget)

    def create_header_section(self):
        """Create the header section with title and controls."""
        layout = QHBoxLayout()

        # Title
        title_label = QLabel("Module Comparison")
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #3daee9;
                padding: 5px;
            }
            """
        )

        layout.addWidget(title_label)
        layout.addStretch()

        # Controls
        self.max_modules_spin = QSpinBox()
        self.max_modules_spin.setRange(2, 10)
        self.max_modules_spin.setValue(self.max_modules)
        self.max_modules_spin.setToolTip("Maximum number of modules to compare")

        max_label = QLabel("Max modules:")

        self.clear_all_btn = QPushButton("Clear All")
        self.clear_all_btn.setToolTip("Remove all modules from comparison")

        self.export_btn = QPushButton("Export Comparison")
        self.export_btn.setToolTip("Export comparison data")
        # Initially disabled until there are modules and a controller is provided
        self.export_btn.setEnabled(False)

        layout.addWidget(max_label)
        layout.addWidget(self.max_modules_spin)
        layout.addWidget(self.clear_all_btn)
        layout.addWidget(self.export_btn)

        return layout

    def create_selection_section(self):
        """Create the module selection section."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        widget.setMaximumHeight(120)

        layout = QVBoxLayout(widget)

        # Selection controls
        controls_layout = QHBoxLayout()

        # Search for modules to add
        search_label = QLabel("Add module:")
        self.module_search = QLineEdit()
        self.module_search.setPlaceholderText("Search by manufacturer, model, or ID...")

        self.add_module_btn = QPushButton("Add")
        self.add_module_btn.setEnabled(False)

        controls_layout.addWidget(search_label)
        controls_layout.addWidget(self.module_search, 1)
        controls_layout.addWidget(self.add_module_btn)

        layout.addLayout(controls_layout)

        # Selected modules display
        self.selected_modules_layout = QHBoxLayout()
        self.update_selected_modules_display()
        layout.addLayout(self.selected_modules_layout)

        return widget

    def create_comparison_table(self):
        """Create the main comparison table."""
        table = QTableWidget()
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        # Set table properties
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)

        # Style the table
        table.setStyleSheet("""
            QTableWidget {
                gridline-color: #555555;
                background-color: #2b2b2b;
                alternate-background-color: #353535;
            }
            QTableWidget::item {
                padding: 8px;
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

    def create_charts_section(self):
        """Create the charts section."""
        if not MATPLOTLIB_AVAILABLE:
            label = QLabel("Charts not available - matplotlib not installed")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return label

        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)

        layout = QHBoxLayout(widget)

        # Create matplotlib figures
        self.comparison_figure = Figure(figsize=(12, 4), facecolor='#2b2b2b')
        self.comparison_canvas = FigureCanvas(self.comparison_figure)

        layout.addWidget(self.comparison_canvas)

        return widget

    def create_analysis_section(self):
        """Create the analysis section."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        widget.setMaximumHeight(100)

        layout = QVBoxLayout(widget)

        # Analysis title
        analysis_label = QLabel("Analysis & Recommendations")
        analysis_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #3daee9;
                padding: 5px;
            }
        """)

        # Analysis text
        self.analysis_text = QLabel("Select modules to see comparison analysis...")
        self.analysis_text.setWordWrap(True)
        self.analysis_text.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #404040;
                border-radius: 4px;
                color: #ffffff;
            }
        """)

        layout.addWidget(analysis_label)
        layout.addWidget(self.analysis_text)

        return widget

    def setup_connections(self):
        """Setup signal connections."""
        self.module_search.textChanged.connect(self.on_search_text_changed)
        self.module_search.returnPressed.connect(self.search_and_add_module)
        self.add_module_btn.clicked.connect(self.search_and_add_module)
        self.clear_all_btn.clicked.connect(self.clear_all_modules)
        self.export_btn.clicked.connect(self.export_comparison)
        self.max_modules_spin.valueChanged.connect(self.on_max_modules_changed)

    def on_search_text_changed(self, text):
        """Handle search text changes."""
        self.add_module_btn.setEnabled(len(text.strip()) > 0)

    def search_and_add_module(self):
        """Search for a module and add it to comparison."""
        search_text = self.module_search.text().strip()
        if not search_text:
            return

        try:
            # Search for modules
            search_criteria = {}

            # Try to parse as ID first
            if search_text.isdigit():
                module = self.db_controller.get_module_by_id(int(search_text))
                if module:
                    self.add_module_to_comparison(module)
                    self.module_search.clear()
                    return

            # Search by text
            if len(search_text) >= 2:
                # Simple text search - could be enhanced
                search_criteria = {"manufacturer": search_text}
                modules = self.db_controller.search_modules(search_criteria)

                if modules:
                    # Add the first matching module
                    self.add_module_to_comparison(modules[0])
                    self.module_search.clear()
                else:
                    QMessageBox.information(
                        self,
                        "No Results",
                        f"No modules found matching '{search_text}'"
                    )

        except Exception as e:
            QMessageBox.warning(
                self,
                "Search Error",
                f"Error searching for modules: {str(e)}"
            )

    def add_module_to_comparison(self, module: Dict[str, Any]):
        """Add a module to the comparison."""
        if len(self.compared_modules) >= self.max_modules:
            QMessageBox.warning(
                self,
                "Maximum Reached",
                f"Maximum of {self.max_modules} modules can be compared at once."
            )
            return

        # Check if module already exists
        module_id = module.get("id")
        if any(m.get("id") == module_id for m in self.compared_modules):
            QMessageBox.information(
                self,
                "Already Added",
                "This module is already in the comparison."
            )
            return

        # Add module
        self.compared_modules.append(module)
        self.update_comparison_display()
        self.update_selected_modules_display()

        # Enable export if we have modules AND an export controller
        self.export_btn.setEnabled(bool(self.export_controller) and len(self.compared_modules) > 0)

        # Emit signal
        self.modules_changed.emit(self.compared_modules)

    def remove_module_from_comparison(self, module_id: int):
        """Remove a module from comparison."""
        self.compared_modules = [m for m in self.compared_modules if m.get("id") != module_id]
        self.update_comparison_display()
        self.update_selected_modules_display()

        # Disable export if no modules or no controller
        self.export_btn.setEnabled(bool(self.export_controller) and len(self.compared_modules) > 0)

        # Emit signal
        self.modules_changed.emit(self.compared_modules)

    def clear_all_modules(self):
        """Clear all modules from comparison."""
        if not self.compared_modules:
            return

        reply = QMessageBox.question(
            self,
            "Clear All",
            "Are you sure you want to remove all modules from comparison?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.compared_modules.clear()
            self.update_comparison_display()
            self.update_selected_modules_display()
            self.export_btn.setEnabled(False)
            self.modules_changed.emit(self.compared_modules)

    def update_selected_modules_display(self):
        """Update the display of selected modules."""
        # Clear existing widgets
        for i in reversed(range(self.selected_modules_layout.count())):
            child = self.selected_modules_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        if not self.compared_modules:
            label = QLabel("No modules selected for comparison")
            label.setStyleSheet("color: #888888; font-style: italic;")
            self.selected_modules_layout.addWidget(label)
            return

        # Add module chips
        for module in self.compared_modules:
            chip = self.create_module_chip(module)
            self.selected_modules_layout.addWidget(chip)

        self.selected_modules_layout.addStretch()

    def create_module_chip(self, module: Dict[str, Any]):
        """Create a chip widget for a selected module."""
        chip = QFrame()
        chip.setFrameStyle(QFrame.Shape.StyledPanel)
        chip.setStyleSheet("""
            QFrame {
                background-color: #3daee9;
                border-radius: 15px;
                padding: 5px 10px;
                margin: 2px;
            }
        """)

        layout = QHBoxLayout(chip)
        layout.setContentsMargins(8, 4, 8, 4)

        # Module info
        manufacturer = module.get("manufacturer", "Unknown")
        model = module.get("model", "Unknown")
        power = module.get("pmax_stc", 0)

        text = f"{manufacturer} {model}"
        if power:
            text += f" ({power}W)"

        label = QLabel(text)
        label.setStyleSheet("color: white; font-weight: bold;")

        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(20, 20)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.3);
                border: none;
                border-radius: 10px;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.5);
            }
        """)

        module_id = module.get("id")
        remove_btn.clicked.connect(lambda: self.remove_module_from_comparison(module_id))

        layout.addWidget(label)
        layout.addWidget(remove_btn)

        return chip

    def update_comparison_display(self):
        """Update the main comparison table and charts."""
        self.update_comparison_table()
        if MATPLOTLIB_AVAILABLE:
            self.update_comparison_charts()
        self.update_analysis()

    def update_comparison_table(self):
        """Update the comparison table."""
        table = self.comparison_table

        if not self.compared_modules:
            table.setRowCount(0)
            table.setColumnCount(0)
            return

        # Define comparison parameters
        parameters = [
            ("ID", "id"),
            ("Manufacturer", "manufacturer"),
            ("Model", "model"),
            ("Series", "series"),
            ("Power (W)", "pmax_stc"),
            ("Efficiency (%)", "efficiency_stc"),
            ("Voc (V)", "voc_stc"),
            ("Isc (A)", "isc_stc"),
            ("Vmp (V)", "vmp_stc"),
            ("Imp (A)", "imp_stc"),
            ("Height (mm)", "height"),
            ("Width (mm)", "width"),
            ("Thickness (mm)", "thickness"),
            ("Weight (kg)", "weight"),
            ("Cell Type", "cell_type"),
            ("Module Type", "module_type"),
            ("Cells in Series", "cells_in_series"),
            ("Total Cells", "total_cells"),
            ("Temp Coeff Pmax (%/°C)", "temp_coeff_pmax"),
            ("Temp Coeff Voc (%/°C)", "temp_coeff_voc"),
            ("Temp Coeff Isc (%/°C)", "temp_coeff_isc"),
        ]

        # Set table dimensions
        table.setRowCount(len(parameters))
        table.setColumnCount(len(self.compared_modules) + 1)  # +1 for parameter names

        # Set headers
        headers = ["Parameter"] + [
            f"{m.get('manufacturer', 'Unknown')} {m.get('model', 'Unknown')}"
            for m in self.compared_modules
        ]
        table.setHorizontalHeaderLabels(headers)

        # Populate table
        for row, (param_name, param_key) in enumerate(parameters):
            # Parameter name
            param_item = QTableWidgetItem(param_name)
            param_item.setFont(QFont("", -1, QFont.Weight.Bold))
            param_item.setBackground(QColor("#404040"))
            table.setItem(row, 0, param_item)

            # Module values
            values = []
            for col, module in enumerate(self.compared_modules):
                value = module.get(param_key)

                if value is None:
                    display_value = "N/A"
                elif isinstance(value, (int, float)):
                    if param_key in ["efficiency_stc", "temp_coeff_pmax", "temp_coeff_voc", "temp_coeff_isc"]:
                        display_value = f"{value:.2f}"
                    else:
                        display_value = f"{value:.1f}" if isinstance(value, float) else str(value)
                else:
                    display_value = str(value)

                item = QTableWidgetItem(display_value)

                # Store numeric value for comparison
                if isinstance(value, (int, float)):
                    values.append(value)

                table.setItem(row, col + 1, item)

            # Highlight best/worst values for numeric parameters
            if values and len(values) > 1:
                self.highlight_best_worst_values(table, row, values, param_key)

        # Resize columns
        table.resizeColumnsToContents()

        # Set minimum column widths
        for col in range(table.columnCount()):
            if table.columnWidth(col) < 100:
                table.setColumnWidth(col, 100)

    def highlight_best_worst_values(self, table, row, values, param_key):
        """Highlight best and worst values in the table."""
        if not values or len(values) < 2:
            return

        # Determine if higher is better
        higher_is_better = param_key in [
            "pmax_stc", "efficiency_stc", "voc_stc", "isc_stc", "vmp_stc", "imp_stc"
        ]

        # Find best and worst values
        if higher_is_better:
            best_value = max(values)
            worst_value = min(values)
        else:
            best_value = min(values)
            worst_value = max(values)

        # Apply highlighting
        for col, module in enumerate(self.compared_modules):
            value = module.get(param_key)
            if isinstance(value, (int, float)):
                item = table.item(row, col + 1)
                if item:
                    if value == best_value:
                        item.setBackground(QColor("#27ae60"))  # Green for best
                        item.setForeground(QColor("#ffffff"))
                    elif value == worst_value and len(values) > 2:
                        item.setBackground(QColor("#e74c3c"))  # Red for worst
                        item.setForeground(QColor("#ffffff"))

    def update_comparison_charts(self):
        """Update the comparison charts."""
        if not MATPLOTLIB_AVAILABLE or not self.compared_modules:
            return

        self.comparison_figure.clear()

        # Create subplots
        ax1 = self.comparison_figure.add_subplot(131)
        ax2 = self.comparison_figure.add_subplot(132)
        ax3 = self.comparison_figure.add_subplot(133)

        # Prepare data
        module_names = [
            f"{m.get('manufacturer', 'Unknown')}\n{m.get('model', 'Unknown')}"
            for m in self.compared_modules
        ]

        # Chart 1: Power comparison
        powers = [m.get("pmax_stc", 0) for m in self.compared_modules]
        if any(p > 0 for p in powers):
            bars1 = ax1.bar(range(len(powers)), powers, color='#3daee9', alpha=0.7)
            ax1.set_title("Power Comparison (W)", color='white')
            ax1.set_xticks(range(len(module_names)))
            ax1.set_xticklabels(module_names, rotation=45, ha='right', color='white')
            ax1.tick_params(colors='white')

            # Add value labels on bars
            for bar, power in zip(bars1, powers):
                if power > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(powers)*0.01,
                            f'{power:.0f}W', ha='center', va='bottom', color='white')

        # Chart 2: Efficiency comparison
        efficiencies = [m.get("efficiency_stc", 0) for m in self.compared_modules]
        if any(e > 0 for e in efficiencies):
            bars2 = ax2.bar(range(len(efficiencies)), efficiencies, color='#f39c12', alpha=0.7)
            ax2.set_title("Efficiency Comparison (%)", color='white')
            ax2.set_xticks(range(len(module_names)))
            ax2.set_xticklabels(module_names, rotation=45, ha='right', color='white')
            ax2.tick_params(colors='white')

            # Add value labels on bars
            for bar, eff in zip(bars2, efficiencies):
                if eff > 0:
                    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(efficiencies)*0.01,
                            f'{eff:.1f}%', ha='center', va='bottom', color='white')

        # Chart 3: Power density (W/m²)
            power_densities = []
        for module in self.compared_modules:
            power = module.get("pmax_stc", 0)
            length = module.get("height", 0)
            width = module.get("width", 0)

            if power > 0 and length > 0 and width > 0:
                area_m2 = (length * width) / 1000000  # Convert mm² to m²
                density = power / area_m2
                power_densities.append(density)
            else:
                power_densities.append(0)

        if any(d > 0 for d in power_densities):
            bars3 = ax3.bar(range(len(power_densities)), power_densities, color='#e74c3c', alpha=0.7)
            ax3.set_title("Power Density (W/m²)", color='white')
            ax3.set_xticks(range(len(module_names)))
            ax3.set_xticklabels(module_names, rotation=45, ha='right', color='white')
            ax3.tick_params(colors='white')

            # Add value labels on bars
            for bar, density in zip(bars3, power_densities):
                if density > 0:
                    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(power_densities)*0.01,
                            f'{density:.0f}', ha='center', va='bottom', color='white')

        # Style the figure
        self.comparison_figure.patch.set_facecolor('#2b2b2b')
        for ax in [ax1, ax2, ax3]:
            ax.set_facecolor('#2b2b2b')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')

        self.comparison_figure.tight_layout()
        self.comparison_canvas.draw()

    def update_analysis(self):
        """Update the analysis section."""
        if not self.compared_modules:
            self.analysis_text.setText("Select modules to see comparison analysis...")
            return

        if len(self.compared_modules) < 2:
            self.analysis_text.setText("Add at least 2 modules to see comparison analysis...")
            return

        # Perform basic analysis
        analysis_parts = []

        # Power analysis
        powers = [m.get("pmax_stc", 0) for m in self.compared_modules if m.get("pmax_stc", 0) > 0]
        if powers:
            max_power = max(powers)
            min_power = min(powers)
            avg_power = sum(powers) / len(powers)

            best_power_module = next(m for m in self.compared_modules if m.get("pmax_stc") == max_power)
            analysis_parts.append(
                f"🔋 Power: {best_power_module.get('manufacturer')} {best_power_module.get('model')} "
                f"leads with {max_power:.0f}W (range: {min_power:.0f}W - {max_power:.0f}W, avg: {avg_power:.0f}W)"
            )

        # Efficiency analysis
        efficiencies = [m.get("efficiency_stc", 0) for m in self.compared_modules if m.get("efficiency_stc", 0) > 0]
        if efficiencies:
            max_eff = max(efficiencies)
            min_eff = min(efficiencies)

            best_eff_module = next(m for m in self.compared_modules if m.get("efficiency_stc") == max_eff)
            analysis_parts.append(
                f"⚡ Efficiency: {best_eff_module.get('manufacturer')} {best_eff_module.get('model')} "
                f"is most efficient at {max_eff:.1f}% (range: {min_eff:.1f}% - {max_eff:.1f}%)"
            )

        # Size analysis
        areas = []
        for m in self.compared_modules:
            length = m.get("height", 0)
            width = m.get("width", 0)
            if length > 0 and width > 0:
                areas.append((length * width / 1000000, m))  # Convert to m²

        if areas:
            areas.sort(key=lambda x: x[0])
            smallest_area, smallest_module = areas[0]
            largest_area, largest_module = areas[-1]

            analysis_parts.append(
                f"📐 Size: {smallest_module.get('manufacturer')} {smallest_module.get('model')} "
                f"is most compact at {smallest_area:.2f}m², "
                f"{largest_module.get('manufacturer')} {largest_module.get('model')} "
                f"is largest at {largest_area:.2f}m²"
            )

        if analysis_parts:
            analysis_text = " • ".join(analysis_parts)
        else:
            analysis_text = "Analysis not available - insufficient data in selected modules."

        self.analysis_text.setText(analysis_text)

    def on_max_modules_changed(self, value):
        """Handle max modules change."""
        self.max_modules = value

        # Remove excess modules if necessary
        if len(self.compared_modules) > value:
            self.compared_modules = self.compared_modules[:value]
            self.update_comparison_display()
            self.update_selected_modules_display()

    def export_comparison(self):
        """Export the comparison data."""
        if not self.compared_modules:
            return

        try:
            from PyQt6.QtWidgets import QFileDialog

            # Get export file path
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Comparison",
                f"module_comparison_{len(self.compared_modules)}_modules.csv",
                "CSV Files (*.csv);;JSON Files (*.json);;Excel Files (*.xlsx)"
            )

            if file_path:
                # Use export controller
                if hasattr(self, 'export_controller') and self.export_controller is not None:
                    comparison_data = {
                        "modules": self.compared_modules,
                        "type": "manual_comparison",
                        "analysis": {"module_count": len(self.compared_modules)}
                    }

                    # Determine format from file extension
                    if file_path.lower().endswith('.json'):
                        format_type = 'json'
                    elif file_path.lower().endswith('.xlsx'):
                        format_type = 'xlsx'
                    else:
                        format_type = 'csv'

                    result = self.export_controller.export_comparison(
                        comparison_data, file_path, format_type
                    )

                    if result.get("success"):
                        QMessageBox.information(
                            self,
                            "Export Successful",
                            f"Comparison exported successfully to:\n{file_path}"
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            "Export Failed",
                            f"Failed to export comparison:\n{result.get('error', 'Unknown error')}"
                        )
                else:
                    QMessageBox.warning(
                        self,
                        "Export Error",
                        "Export controller not available"
                    )

        except Exception as e:
            QMessageBox.warning(
                self,
                "Export Error",
                f"Error during export: {str(e)}"
            )

    def refresh_data(self):
        """Refresh the widget data."""
        # Re-fetch module data for currently compared modules
        if self.compared_modules:
            module_ids = [m.get("id") for m in self.compared_modules if m.get("id")]
            if module_ids:
                try:
                    updated_modules = self.db_controller.get_modules_by_ids(module_ids)
                    if updated_modules:
                        self.compared_modules = updated_modules
                        self.update_comparison_display()
                        self.update_selected_modules_display()
                except Exception as e:
                    print(f"Error refreshing comparison data: {e}")

    def get_comparison_data(self):
        """Get current comparison data for external use."""
        return {
            "modules": self.compared_modules.copy(),
            "module_count": len(self.compared_modules),
            "max_modules": self.max_modules
        }
