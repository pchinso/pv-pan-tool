"""
Search widget for PV PAN Tool Desktop Application.

Basic search UI with common filters and a results table.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class SearchWidget(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.results = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Filters row 1: Manufacturer, Model
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Manufacturer:"))
        self.manufacturer_input = QLineEdit()
        self.manufacturer_input.setPlaceholderText("e.g., Jinko, LONGi")
        row1.addWidget(self.manufacturer_input)

        row1.addWidget(QLabel("Model:"))
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("e.g., 72M, Hi-MO")
        row1.addWidget(self.model_input)

        layout.addLayout(row1)

        # Filters row 2: Power range + Sort
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Power (W):"))
        self.power_min = QSpinBox()
        self.power_min.setRange(0, 2000)
        self.power_min.setValue(0)
        row2.addWidget(self.power_min)
        row2.addWidget(QLabel("to"))
        self.power_max = QSpinBox()
        self.power_max.setRange(0, 2000)
        self.power_max.setValue(800)
        row2.addWidget(self.power_max)

        row2.addStretch()

        row2.addWidget(QLabel("Sort by:"))
        self.sort_by = QComboBox()
        self.sort_by.addItems([
            "pmax_stc", "efficiency_stc", "voc_stc", "isc_stc", "manufacturer", "model"
        ])
        row2.addWidget(self.sort_by)
        self.sort_order = QComboBox()
        self.sort_order.addItems(["desc", "asc"])
        row2.addWidget(self.sort_order)

        layout.addLayout(row2)

        # Filters row 3: Size ranges (mm)
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Height (mm):"))
        self.min_height = QSpinBox()
        self.min_height.setRange(0, 4000)
        self.min_height.setValue(0)
        row3.addWidget(self.min_height)
        row3.addWidget(QLabel("to"))
        self.max_height = QSpinBox()
        self.max_height.setRange(0, 4000)
        self.max_height.setValue(0)
        row3.addWidget(self.max_height)

        row3.addSpacing(20)

        row3.addWidget(QLabel("Width (mm):"))
        self.min_width = QSpinBox()
        self.min_width.setRange(0, 4000)
        self.min_width.setValue(0)
        row3.addWidget(self.min_width)
        row3.addWidget(QLabel("to"))
        self.max_width = QSpinBox()
        self.max_width.setRange(0, 4000)
        self.max_width.setValue(0)
        row3.addWidget(self.max_width)

        row3.addStretch()

        layout.addLayout(row3)

        # Action buttons
        actions = QHBoxLayout()
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.run_search)
        actions.addWidget(self.search_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_filters)
        actions.addWidget(self.clear_btn)
        actions.addStretch()
        layout.addLayout(actions)

        # Results table
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Manufacturer", "Model", "Pmax (W)", "Voc (V)", "Isc (A)", "Eff (%)", "Size (mm)"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Initial search on load
        self.run_search()

    def _collect_params(self):
        def nz(v):
            return v if v != 0 else None
        params = {
            "manufacturer": self.manufacturer_input.text().strip() or None,
            "model": self.model_input.text().strip() or None,
            "power_min": nz(self.power_min.value()),
            "power_max": nz(self.power_max.value()),
            "min_height": nz(self.min_height.value()),
            "max_height": nz(self.max_height.value()),
            "min_width": nz(self.min_width.value()),
            "max_width": nz(self.max_width.value()),
            "sort_by": self.sort_by.currentText(),
            "sort_order": self.sort_order.currentText(),
            "limit": 200,
        }
        return params

    def run_search(self):
        criteria = self._collect_params()
        result = self.controller.search_modules(criteria)
        modules = result if isinstance(result, list) else []
        self.results = modules
        self._populate_table(modules)

    def _populate_table(self, modules):
        self.table.setRowCount(0)
        for m in modules:
            row = self.table.rowCount()
            self.table.insertRow(row)
            def get(k, default=""): return m.get(k, default)
            # Size
            width = get("width")
            height = get("height")
            size = f"{int(width)} x {int(height)}" if width and height else ""

            values = [
                get("id"), get("manufacturer"), get("model"),
                get("pmax_stc"), get("voc_stc"), get("isc_stc"),
                get("efficiency_stc"), size
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem("" if val is None else str(val))
                if col in (3,4,5,6):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, col, item)

    def clear_filters(self):
        self.manufacturer_input.clear()
        self.model_input.clear()
        self.power_min.setValue(0)
        self.power_max.setValue(800)
        self.min_height.setValue(0)
        self.max_height.setValue(0)
        self.min_width.setValue(0)
        self.max_width.setValue(0)
        self.sort_by.setCurrentText("pmax_stc")
        self.sort_order.setCurrentText("desc")
        self.run_search()

    def refresh_data(self):
        # Re-run search with current filters
        self.run_search()
