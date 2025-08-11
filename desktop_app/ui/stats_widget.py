"""
Statistics widget for PV PAN Tool Desktop Application.

This module provides comprehensive statistics and visualizations
for the PV module database.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# Import matplotlib for charts
try:
    import matplotlib.pyplot as plt
    import numpy as np

    # Use the QtAgg backend compatible with PyQt6
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class StatsCalculationWorker(QThread):
    """Worker thread for calculating statistics."""

    stats_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, db_controller):
        super().__init__()
        self.db_controller = db_controller

    def run(self):
        """Calculate statistics in background."""
        try:
            stats = self.db_controller.get_detailed_statistics()
            self.stats_ready.emit(stats)
        except Exception as e:
            self.error_occurred.emit(str(e))


class StatCard(QFrame):
    """A card widget for displaying a single statistic."""

    def __init__(self, title: str, value: str, subtitle: str = "", color: str = "#3daee9"):
        super().__init__()
        self.init_ui(title, value, subtitle, color)

    def init_ui(self, title: str, value: str, subtitle: str, color: str):
        """Initialize the stat card UI."""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #404040;
                border-radius: 8px;
                border-left: 4px solid {color};
                padding: 8px;
                margin: 4px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 10px;
                font-weight: normal;
                margin-bottom: 5px;
            }
        """)

        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 2px;
            }}
        """)

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        # Subtitle if provided
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 9px;
                    font-style: italic;
                }
            """)
            layout.addWidget(subtitle_label)

        layout.addStretch()

    def update_value(self, value: str, subtitle: str = ""):
        """Update the card value."""
        # Find and update the value label
        layout = self.layout()
        if layout.count() >= 2:
            value_label = layout.itemAt(1).widget()
            if isinstance(value_label, QLabel):
                value_label.setText(value)

        # Update subtitle if provided
        if subtitle and layout.count() >= 3:
            subtitle_label = layout.itemAt(2).widget()
            if isinstance(subtitle_label, QLabel):
                subtitle_label.setText(subtitle)


class StatsWidget(QWidget):
    """Widget for displaying database statistics and charts."""

    def __init__(self, db_controller):
        super().__init__()

        self.db_controller = db_controller
        self.current_stats = {}
        self.charts_created = False

        self.init_ui()
        self.setup_connections()

        # Load initial data
        QTimer.singleShot(100, self.refresh_data)

    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_layout = self.create_header_section()
        main_layout.addLayout(header_layout)

        # Main content
        content_splitter = QSplitter(Qt.Orientation.Vertical)

        # KPI Cards section
        kpi_widget = self.create_kpi_section()
        content_splitter.addWidget(kpi_widget)

        # Charts section
        if MATPLOTLIB_AVAILABLE:
            charts_widget = self.create_charts_section()
            content_splitter.addWidget(charts_widget)
        else:
            no_charts_label = QLabel("Charts not available - matplotlib not installed")
            no_charts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_charts_label.setStyleSheet("color: #888888; font-style: italic; padding: 20px;")
            content_splitter.addWidget(no_charts_label)

        # Set splitter proportions (smaller KPI panel)
        content_splitter.setSizes([120, 680])
        content_splitter.setStretchFactor(0, 0)
        content_splitter.setStretchFactor(1, 1)
        main_layout.addWidget(content_splitter)

    def create_header_section(self):
        """Create the header section."""
        layout = QHBoxLayout()

        # Title
        title_label = QLabel("Database Statistics")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #3daee9;
                padding: 5px;
            }
        """)

        layout.addWidget(title_label)
        layout.addStretch()

        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setToolTip("Refresh statistics")

        # Export button
        self.export_btn = QPushButton("📤 Export Charts")
        self.export_btn.setToolTip("Export charts as images")
        self.export_btn.setEnabled(MATPLOTLIB_AVAILABLE)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)

        layout.addWidget(self.progress_bar)
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.export_btn)

        return layout

    def create_kpi_section(self):
        """Create the KPI cards section."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        widget.setMaximumHeight(110)

        # Scroll area for KPI cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Container for cards
        cards_widget = QWidget()
        self.kpi_layout = QHBoxLayout(cards_widget)
        self.kpi_layout.setContentsMargins(8, 8, 8, 8)

        # Create initial cards
        self.create_kpi_cards()

        scroll_area.setWidget(cards_widget)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll_area)

        return widget

    def create_kpi_cards(self):
        """Create KPI cards."""
        # Clear existing cards
        for i in reversed(range(self.kpi_layout.count())):
            child = self.kpi_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # Create cards
        self.total_modules_card = StatCard("Total Modules", "Loading...", color="#3daee9")
        self.manufacturers_card = StatCard("Manufacturers", "Loading...", color="#f39c12")
        self.avg_power_card = StatCard("Average Power", "Loading...", "Watts", "#e74c3c")
        self.avg_efficiency_card = StatCard("Average Efficiency", "Loading...", "Percent", "#27ae60")
        self.top_manufacturer_card = StatCard("Top Manufacturer", "Loading...", color="#9b59b6")

        # Add cards to layout
        self.kpi_layout.addWidget(self.total_modules_card)
        self.kpi_layout.addWidget(self.manufacturers_card)
        self.kpi_layout.addWidget(self.avg_power_card)
        self.kpi_layout.addWidget(self.avg_efficiency_card)
        self.kpi_layout.addWidget(self.top_manufacturer_card)
        self.kpi_layout.addStretch()

    def create_charts_section(self):
        """Create the charts section."""
        if not MATPLOTLIB_AVAILABLE:
            return QLabel("Charts not available")

        # Tab widget for different chart categories
        self.charts_tab_widget = QTabWidget()

        # Overview tab
        overview_tab = self.create_overview_charts_tab()
        self.charts_tab_widget.addTab(overview_tab, "📊 Overview")

        # Distributions tab
        distributions_tab = self.create_distributions_charts_tab()
        self.charts_tab_widget.addTab(distributions_tab, "📈 Distributions")

        # Correlations tab
        correlations_tab = self.create_correlations_charts_tab()
        self.charts_tab_widget.addTab(correlations_tab, "🔗 Correlations")

        return self.charts_tab_widget

    def create_overview_charts_tab(self):
        """Create overview charts tab."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Manufacturer distribution pie chart
        self.manufacturer_figure = Figure(figsize=(6, 4), facecolor='#2b2b2b')
        self.manufacturer_canvas = FigureCanvas(self.manufacturer_figure)

        # Cell type distribution donut chart
        self.celltype_figure = Figure(figsize=(6, 4), facecolor='#2b2b2b')
        self.celltype_canvas = FigureCanvas(self.celltype_figure)

        layout.addWidget(self.manufacturer_canvas)
        layout.addWidget(self.celltype_canvas)

        return widget

    def create_distributions_charts_tab(self):
        """Create distributions charts tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Power and efficiency histograms
        self.distributions_figure = Figure(figsize=(12, 8), facecolor='#2b2b2b')
        self.distributions_canvas = FigureCanvas(self.distributions_figure)

        layout.addWidget(self.distributions_canvas)

        return widget

    def create_correlations_charts_tab(self):
        """Create correlations charts tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Scatter plots for correlations
        self.correlations_figure = Figure(figsize=(12, 8), facecolor='#2b2b2b')
        self.correlations_canvas = FigureCanvas(self.correlations_figure)

        layout.addWidget(self.correlations_canvas)

        return widget

    def setup_connections(self):
        """Setup signal connections."""
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.export_btn.clicked.connect(self.export_charts)

    def refresh_data(self):
        """Refresh statistics data."""
        self.progress_bar.setVisible(True)
        self.refresh_btn.setEnabled(False)

        # Start background calculation
        self.stats_worker = StatsCalculationWorker(self.db_controller)
        self.stats_worker.stats_ready.connect(self.on_stats_ready)
        self.stats_worker.error_occurred.connect(self.on_stats_error)
        self.stats_worker.start()

    def on_stats_ready(self, stats: Dict[str, Any]):
        """Handle statistics calculation completion."""
        self.current_stats = stats
        self.update_kpi_cards()

        if MATPLOTLIB_AVAILABLE:
            self.update_all_charts()

        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)

    def on_stats_error(self, error_message: str):
        """Handle statistics calculation error."""
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)

        QMessageBox.warning(
            self,
            "Statistics Error",
            f"Failed to calculate statistics:\n{error_message}"
        )

    def update_kpi_cards(self):
        """Update KPI cards with current statistics."""
        if not self.current_stats:
            return

        # Total modules
        total_modules = self.current_stats.get("total_modules", 0)
        self.total_modules_card.update_value(f"{total_modules:,}")

        # Manufacturers
        total_manufacturers = self.current_stats.get("total_manufacturers", 0)
        self.manufacturers_card.update_value(str(total_manufacturers))

        # Average power
        # Values provided by database: avg_power, avg_efficiency
        avg_power = self.current_stats.get("avg_power", 0)
        if avg_power > 0:
            self.avg_power_card.update_value(f"{avg_power:.0f}W")
        else:
            self.avg_power_card.update_value("N/A")

        # Average efficiency
        avg_efficiency = self.current_stats.get("avg_efficiency", 0)
        if avg_efficiency > 0:
            self.avg_efficiency_card.update_value(f"{avg_efficiency:.1f}%")
        else:
            self.avg_efficiency_card.update_value("N/A")

        # Top manufacturer
        manufacturer_stats = self.current_stats.get("manufacturer_statistics", [])
        if manufacturer_stats:
            top_manufacturer = manufacturer_stats[0]
            name = top_manufacturer.get("manufacturer", "Unknown")
            count = top_manufacturer.get("module_count", 0)
            self.top_manufacturer_card.update_value(name, f"{count} modules")
        else:
            self.top_manufacturer_card.update_value("N/A")

    def update_all_charts(self):
        """Update all charts with current data."""
        if not MATPLOTLIB_AVAILABLE or not self.current_stats:
            return

        self.update_manufacturer_chart()
        self.update_celltype_chart()
        self.update_distributions_charts()
        self.update_correlations_charts()

    def update_manufacturer_chart(self):
        """Update manufacturer distribution pie chart."""
        self.manufacturer_figure.clear()

        manufacturer_stats = self.current_stats.get("manufacturer_statistics", [])
        if not manufacturer_stats:
            ax = self.manufacturer_figure.add_subplot(111)
            ax.text(0.5, 0.5, "No data", color='white', ha='center', va='center', transform=ax.transAxes)
            ax.set_axis_off()
            self.manufacturer_canvas.draw()
            return

        ax = self.manufacturer_figure.add_subplot(111)

        # Prepare data (show top 8, group others)
        if len(manufacturer_stats) > 8:
            top_manufacturers = manufacturer_stats[:8]
            others_count = sum(m.get("module_count", 0) for m in manufacturer_stats[8:])

            labels = [m.get("manufacturer", "Unknown") for m in top_manufacturers]
            sizes = [m.get("module_count", 0) for m in top_manufacturers]

            if others_count > 0:
                labels.append("Others")
                sizes.append(others_count)
        else:
            labels = [m.get("manufacturer", "Unknown") for m in manufacturer_stats]
            sizes = [m.get("module_count", 0) for m in manufacturer_stats]

        total = sum(sizes)
        if total <= 0 or len(sizes) == 0:
            ax.text(0.5, 0.5, "No data", color='white', ha='center', va='center', transform=ax.transAxes)
            ax.set_axis_off()
        else:
            # Create pie chart
            colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                textprops={'color': 'white', 'fontsize': 9}
            )

        ax.set_title("Manufacturer Distribution", color='white', fontsize=12, pad=20)

        # Style the chart
        self.manufacturer_figure.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#2b2b2b')

        self.manufacturer_figure.tight_layout()
        self.manufacturer_canvas.draw()

    def update_celltype_chart(self):
        """Update cell type distribution donut chart."""
        self.celltype_figure.clear()

        celltype_stats = self.current_stats.get("cell_type_statistics", [])
        if not celltype_stats:
            ax = self.celltype_figure.add_subplot(111)
            ax.text(0.5, 0.5, "No data", color='white', ha='center', va='center', transform=ax.transAxes)
            ax.set_axis_off()
            self.celltype_canvas.draw()
            return

        ax = self.celltype_figure.add_subplot(111)

        # Prepare data
        labels = [ct.get("cell_type", "Unknown") for ct in celltype_stats]
        sizes = [ct.get("count", 0) for ct in celltype_stats]

        total = sum(sizes)
        if total <= 0 or len(sizes) == 0:
            ax.text(0.5, 0.5, "No data", color='white', ha='center', va='center', transform=ax.transAxes)
            ax.set_axis_off()
        else:
            # Create donut chart
            colors = plt.cm.Pastel1(np.linspace(0, 1, len(labels)))
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                pctdistance=0.85,
                textprops={'color': 'white', 'fontsize': 9}
            )

            # Create donut hole
            centre_circle = plt.Circle((0, 0), 0.70, fc='#2b2b2b')
            ax.add_artist(centre_circle)

        ax.set_title("Cell Type Distribution", color='white', fontsize=12, pad=20)

        # Style the chart
        self.celltype_figure.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#2b2b2b')

        self.celltype_figure.tight_layout()
        self.celltype_canvas.draw()

    def update_distributions_charts(self):
        """Update power and efficiency distribution histograms."""
        self.distributions_figure.clear()

        # Get power and efficiency ranges
        power_range = self.current_stats.get("power_range_distribution", [])
        efficiency_range = self.current_stats.get("efficiency_range_distribution", [])

        if not power_range and not efficiency_range:
            return

        # Create subplots
        if power_range and efficiency_range:
            ax1 = self.distributions_figure.add_subplot(221)
            ax2 = self.distributions_figure.add_subplot(222)
            ax3 = self.distributions_figure.add_subplot(223)
            ax4 = self.distributions_figure.add_subplot(224)
        elif power_range:
            ax1 = self.distributions_figure.add_subplot(121)
            ax2 = self.distributions_figure.add_subplot(122)
            ax3 = ax4 = None
        elif efficiency_range:
            ax3 = self.distributions_figure.add_subplot(121)
            ax4 = self.distributions_figure.add_subplot(122)
            ax1 = ax2 = None
        else:
            return

        # Power distribution
        if power_range and ax1:
            # Build readable labels from min/max keys returned by DB
            ranges = [f"{int(pr.get('min_power', 0))}-{int(pr.get('max_power', 0))}" for pr in power_range]
            counts = [int(pr.get("count", 0)) for pr in power_range]

            bars = ax1.bar(range(len(ranges)), counts, color='#3daee9', alpha=0.7)
            ax1.set_title("Power Distribution", color='white')
            ax1.set_xlabel("Power Range (W)", color='white')
            ax1.set_ylabel("Count", color='white')
            ax1.set_xticks(range(len(ranges)))
            ax1.set_xticklabels(ranges, rotation=45, ha='right', color='white')
            ax1.tick_params(colors='white')

            # Add value labels
            if counts and max(counts) > 0:
                for bar, count in zip(bars, counts):
                    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(counts)*0.01,
                            str(count), ha='center', va='bottom', color='white')

        # Power box plot
        if ax2:
            powers = self.current_stats.get("power_values", [])
            if powers:
                ax2.boxplot(powers, vert=True, patch_artist=True,
                            boxprops=dict(facecolor='#3daee9', color='white'),
                            medianprops=dict(color='white'))
                ax2.set_ylabel("Power (W)", color='white')
            else:
                ax2.text(0.5, 0.5, "No data", ha='center', va='center', transform=ax2.transAxes, color='white')
            ax2.set_title("Power Statistics", color='white')

        # Efficiency distribution
        if efficiency_range and ax3:
            ranges = [f"{er.get('min_efficiency', 0):.2f}-{er.get('max_efficiency', 0):.2f}" for er in efficiency_range]
            counts = [int(er.get("count", 0)) for er in efficiency_range]

            bars = ax3.bar(range(len(ranges)), counts, color='#f39c12', alpha=0.7)
            ax3.set_title("Efficiency Distribution", color='white')
            ax3.set_xlabel("Efficiency Range (%)", color='white')
            ax3.set_ylabel("Count", color='white')
            ax3.set_xticks(range(len(ranges)))
            ax3.set_xticklabels(ranges, rotation=45, ha='right', color='white')
            ax3.tick_params(colors='white')

            # Add value labels
            if counts and max(counts) > 0:
                for bar, count in zip(bars, counts):
                    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(counts)*0.01,
                            str(count), ha='center', va='bottom', color='white')

        # Efficiency box plot
        if ax4:
            effs = self.current_stats.get("efficiency_values", [])
            if effs:
                ax4.boxplot(effs, vert=True, patch_artist=True,
                            boxprops=dict(facecolor='#f39c12', color='white'),
                            medianprops=dict(color='white'))
                ax4.set_ylabel("Efficiency (%)", color='white')
            else:
                ax4.text(0.5, 0.5, "No data", ha='center', va='center', transform=ax4.transAxes, color='white')
            ax4.set_title("Efficiency Statistics", color='white')

        # Style all axes
        for ax in [ax1, ax2, ax3, ax4]:
            if ax:
                ax.set_facecolor('#2b2b2b')
                for spine in ax.spines.values():
                    spine.set_color('white')

        self.distributions_figure.patch.set_facecolor('#2b2b2b')
        self.distributions_figure.tight_layout()
        self.distributions_canvas.draw()

    def update_correlations_charts(self):
        """Update correlation scatter plots."""
        self.correlations_figure.clear()

        # For now, create placeholder correlation charts
        # In a real implementation, you'd fetch raw data for scatter plots

        ax1 = self.correlations_figure.add_subplot(221)
        ax2 = self.correlations_figure.add_subplot(222)
        ax3 = self.correlations_figure.add_subplot(223)
        ax4 = self.correlations_figure.add_subplot(224)

        # Placeholder correlation plots
        correlations = [
            (ax1, "Power vs Efficiency", "Power (W)", "Efficiency (%)"),
            (ax2, "Power vs Area", "Power (W)", "Area (m²)"),
            (ax3, "Efficiency vs Weight", "Efficiency (%)", "Weight (kg)"),
            (ax4, "Voltage vs Current", "Voltage (V)", "Current (A)")
        ]

        for ax, title, xlabel, ylabel in correlations:
            # Generate sample data for demonstration
            x = np.random.normal(400, 100, 50)  # Sample power data
            y = np.random.normal(20, 3, 50)     # Sample efficiency data

            ax.scatter(x, y, alpha=0.6, color='#3daee9', s=30)
            ax.set_title(title, color='white', fontsize=10)
            ax.set_xlabel(xlabel, color='white', fontsize=9)
            ax.set_ylabel(ylabel, color='white', fontsize=9)
            ax.tick_params(colors='white', labelsize=8)
            ax.set_facecolor('#2b2b2b')

            for spine in ax.spines.values():
                spine.set_color('white')

        self.correlations_figure.patch.set_facecolor('#2b2b2b')
        self.correlations_figure.tight_layout()
        self.correlations_canvas.draw()

    def export_charts(self):
        """Export all charts as images."""
        if not MATPLOTLIB_AVAILABLE:
            QMessageBox.warning(self, "Export Error", "Charts not available for export")
            return

        try:
            import os

            from PyQt6.QtWidgets import QFileDialog

            # Get export directory
            directory = QFileDialog.getExistingDirectory(
                self,
                "Select Export Directory",
                str(Path.home())
            )

            if directory:
                export_path = Path(directory)

                # Export each chart
                charts_to_export = [
                    (self.manufacturer_figure, "manufacturer_distribution.png"),
                    (self.celltype_figure, "celltype_distribution.png"),
                    (self.distributions_figure, "power_efficiency_distributions.png"),
                    (self.correlations_figure, "parameter_correlations.png")
                ]

                exported_files = []
                for figure, filename in charts_to_export:
                    # Export if the figure exists and has axes (i.e., something to render)
                    try:
                        if figure is not None and getattr(figure, 'axes', None):
                            file_path = export_path / filename
                            figure.savefig(
                                str(file_path),
                                dpi=300,
                                bbox_inches='tight',
                                facecolor='#2b2b2b',
                                edgecolor='none'
                            )
                            exported_files.append(filename)
                    except Exception:
                        # Skip this figure if saving fails; continue with others
                        pass

                if exported_files:
                    QMessageBox.information(
                        self,
                        "Export Successful",
                        f"Charts exported successfully to:\n{directory}\n\n"
                        f"Files: {', '.join(exported_files)}"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Export Error",
                        "No charts were available for export"
                    )

        except Exception as e:
            QMessageBox.warning(
                self,
                "Export Error",
                f"Failed to export charts:\n{str(e)}"
            )

    def get_current_statistics(self):
        """Get current statistics data."""
        return self.current_stats.copy() if self.current_stats else {}
