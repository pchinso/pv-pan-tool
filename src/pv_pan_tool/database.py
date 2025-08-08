"""
Database management for PV module specifications.

This module provides functionality to store, query, and manage
PV module data in a SQLite database.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .models import ParsingResult, PVModule


class PVModuleDatabase:
    """Database manager for PV module specifications."""

    def __init__(self, db_path: str = "data/database/pv_modules.db"):
        """
        Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def _normalize_value(self, value):
        """Helper method to convert list values to strings for database compatibility."""
        if isinstance(value, list):
            return ", ".join(str(v) for v in value) if value else None
        return value

    def init_database(self) -> None:
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create main modules table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pv_modules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unique_id TEXT UNIQUE NOT NULL,

                    -- Manufacturer information
                    manufacturer TEXT NOT NULL,
                    model TEXT NOT NULL,
                    series TEXT,

                    -- Electrical parameters (STC)
                    pmax_stc REAL,
                    vmp_stc REAL,
                    imp_stc REAL,
                    voc_stc REAL,
                    isc_stc REAL,

                    -- Temperature coefficients
                    temp_coeff_pmax REAL,
                    temp_coeff_voc REAL,
                    temp_coeff_isc REAL,

                    -- Additional electrical
                    noct REAL,
                    max_system_voltage REAL,

                    -- Physical parameters
                    height REAL,
                    width REAL,
                    thickness REAL,
                    weight REAL,
                    cells_in_series INTEGER,
                    cells_in_parallel INTEGER,
                    total_cells INTEGER,

                    -- Technology
                    cell_type TEXT,
                    module_type TEXT,

                    -- Calculated values
                    efficiency_stc REAL,
                    power_density REAL,
                    area_m2 REAL,

                    -- File metadata
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_size INTEGER,
                    file_hash TEXT,
                    manufacturer_folder TEXT,
                    model_folder TEXT,

                    -- Processing metadata
                    parsed_at TEXT NOT NULL,
                    parser_version TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create certifications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS certifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    module_id INTEGER,
                    certification_name TEXT,
                    certified BOOLEAN,
                    FOREIGN KEY (module_id) REFERENCES pv_modules (id)
                )
            """)

            # Create raw data table for storing original .PAN content
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS raw_pan_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    module_id INTEGER,
                    parameter_name TEXT,
                    parameter_value TEXT,
                    FOREIGN KEY (module_id) REFERENCES pv_modules (id)
                )
            """)

            # Create indexes for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_manufacturer ON pv_modules (manufacturer)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_model ON pv_modules (model)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pmax ON pv_modules (pmax_stc)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_efficiency ON pv_modules (efficiency_stc)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cell_type ON pv_modules (cell_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_unique_id ON pv_modules (unique_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_hash ON pv_modules (file_hash)")

            conn.commit()

    def module_exists(self, unique_id: str) -> bool:
        """Check if a module with the given unique_id already exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM pv_modules WHERE unique_id = ?", (unique_id,))
            return cursor.fetchone()[0] > 0

    def is_file_processed(self, file_path: str) -> bool:
        """Return True if a module with the given file path already exists in DB."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM pv_modules WHERE file_path = ?", (str(file_path),))
            return cursor.fetchone()[0] > 0

    def get_module_id_by_unique_id(self, unique_id: str) -> Optional[int]:
        """Get the database ID of a module by its unique_id."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM pv_modules WHERE unique_id = ?", (unique_id,))
            result = cursor.fetchone()
            return result[0] if result else None

    def insert_module(self, module: PVModule, update_if_exists: bool = True) -> Optional[int]:
        """
        Insert a PV module into the database.

        Args:
            module: PVModule instance to insert
            update_if_exists: If True, update existing module; if False, skip

        Returns:
            ID of the inserted/updated module, or None if skipped
        """
        # Check if module already exists
        if self.module_exists(module.unique_id):
            if update_if_exists:
                print(f"Module {module.unique_id} already exists, updating...")
                return self.update_module(module)
            else:
                print(f"Module {module.unique_id} already exists, skipping...")
                return self.get_module_id_by_unique_id(module.unique_id)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Calculate derived values
            efficiency = None
            power_density = None
            area_m2 = None

            if (module.electrical_params.pmax_stc and
                module.physical_params.height and
                module.physical_params.width):
                try:
                    height = float(module.physical_params.height)
                    width = float(module.physical_params.width)
                    pmax = float(module.electrical_params.pmax_stc)

                    area_m2 = (height * width) / 1_000_000  # mm² to m²
                    efficiency = (pmax / (area_m2 * 1000)) * 100  # Efficiency %
                    power_density = pmax / area_m2  # W/m²
                except (ValueError, TypeError, ZeroDivisionError):
                    pass

            # Get current timestamp
            current_time = datetime.now().isoformat()

            # Insert main module data
            cursor.execute("""
                INSERT INTO pv_modules (
                    unique_id, manufacturer, model, series,
                    pmax_stc, vmp_stc, imp_stc, voc_stc, isc_stc,
                    temp_coeff_pmax, temp_coeff_voc, temp_coeff_isc,
                    noct, max_system_voltage,
                    height, width, thickness, weight,
                    cells_in_series, cells_in_parallel, total_cells,
                    cell_type, module_type,
                    efficiency_stc, power_density, area_m2,
                    file_path, file_name, file_size, file_hash,
                    manufacturer_folder, model_folder,
                    parsed_at, parser_version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                module.unique_id,
                self._normalize_value(module.manufacturer_info.name),
                module.manufacturer_info.model,
                module.manufacturer_info.series,
                module.electrical_params.pmax_stc,
                module.electrical_params.vmp_stc,
                module.electrical_params.imp_stc,
                module.electrical_params.voc_stc,
                module.electrical_params.isc_stc,
                module.electrical_params.temp_coeff_pmax,
                module.electrical_params.temp_coeff_voc,
                module.electrical_params.temp_coeff_isc,
                module.electrical_params.noct,
                module.electrical_params.max_system_voltage,
                module.physical_params.height,
                module.physical_params.width,
                module.physical_params.thickness,
                module.physical_params.weight,
                module.physical_params.cells_in_series,
                module.physical_params.cells_in_parallel,
                module.physical_params.total_cells,
                module.cell_type.value,
                module.module_type.value,
                efficiency,
                power_density,
                area_m2,
                str(module.file_metadata.file_path),
                module.file_metadata.file_name,
                module.file_metadata.file_size,
                module.file_metadata.file_hash,
                module.file_metadata.manufacturer_folder,
                module.file_metadata.model_folder,
                module.file_metadata.parsed_at.isoformat(),
                module.file_metadata.parser_version,
                current_time,
                current_time
            ))

            module_id = cursor.lastrowid

            # Insert related data
            self._insert_certifications(cursor, module_id, module.certification_info)
            self._insert_raw_data(cursor, module_id, module.raw_data)

            conn.commit()
            return module_id

    def update_module(self, module: PVModule) -> Optional[int]:
        """Update an existing module in the database."""
        module_id = self.get_module_id_by_unique_id(module.unique_id)
        if not module_id:
            return None

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Calculate derived values
            efficiency = None
            power_density = None
            area_m2 = None

            if (module.electrical_params.pmax_stc and
                module.physical_params.height and
                module.physical_params.width):
                try:
                    height = float(module.physical_params.height)
                    width = float(module.physical_params.width)
                    pmax = float(module.electrical_params.pmax_stc)

                    area_m2 = (height * width) / 1_000_000  # mm² to m²
                    efficiency = (pmax / (area_m2 * 1000)) * 100  # Efficiency %
                    power_density = pmax / area_m2  # W/m²
                except (ValueError, TypeError, ZeroDivisionError):
                    pass

            # Update main module data
            cursor.execute("""
                UPDATE pv_modules SET
                    manufacturer = ?, model = ?, series = ?,
                    pmax_stc = ?, vmp_stc = ?, imp_stc = ?, voc_stc = ?, isc_stc = ?,
                    temp_coeff_pmax = ?, temp_coeff_voc = ?, temp_coeff_isc = ?,
                    noct = ?, max_system_voltage = ?,
                    height = ?, width = ?, thickness = ?, weight = ?,
                    cells_in_series = ?, cells_in_parallel = ?, total_cells = ?,
                    cell_type = ?, module_type = ?,
                    efficiency_stc = ?, power_density = ?, area_m2 = ?,
                    file_path = ?, file_name = ?, file_size = ?, file_hash = ?,
                    manufacturer_folder = ?, model_folder = ?,
                    parsed_at = ?, parser_version = ?, updated_at = ?
                WHERE id = ?
            """, (
                self._normalize_value(module.manufacturer_info.name),
                module.manufacturer_info.model,
                module.manufacturer_info.series,
                module.electrical_params.pmax_stc,
                module.electrical_params.vmp_stc,
                module.electrical_params.imp_stc,
                module.electrical_params.voc_stc,
                module.electrical_params.isc_stc,
                module.electrical_params.temp_coeff_pmax,
                module.electrical_params.temp_coeff_voc,
                module.electrical_params.temp_coeff_isc,
                module.electrical_params.noct,
                module.electrical_params.max_system_voltage,
                module.physical_params.height,
                module.physical_params.width,
                module.physical_params.thickness,
                module.physical_params.weight,
                module.physical_params.cells_in_series,
                module.physical_params.cells_in_parallel,
                module.physical_params.total_cells,
                module.cell_type.value,
                module.module_type.value,
                efficiency,
                power_density,
                area_m2,
                str(module.file_metadata.file_path),
                module.file_metadata.file_name,
                module.file_metadata.file_size,
                module.file_metadata.file_hash,
                module.file_metadata.manufacturer_folder,
                module.file_metadata.model_folder,
                module.file_metadata.parsed_at.isoformat(),
                module.file_metadata.parser_version,
                datetime.now().isoformat(),
                module_id
            ))

            # Delete and re-insert related data
            cursor.execute("DELETE FROM certifications WHERE module_id = ?", (module_id,))
            cursor.execute("DELETE FROM raw_pan_data WHERE module_id = ?", (module_id,))

            self._insert_certifications(cursor, module_id, module.certification_info)
            self._insert_raw_data(cursor, module_id, module.raw_data)

            conn.commit()
            return module_id

    def _insert_certifications(self, cursor, module_id: int, certification_info) -> None:
        """Helper method to insert certifications."""
        cert_data = [
            ("IEC 61215", certification_info.iec_61215),
            ("IEC 61730", certification_info.iec_61730),
            ("UL Listed", certification_info.ul_listed),
            ("CE Marking", certification_info.ce_marking),
        ]

        for cert_name, certified in cert_data:
            if certified is not None:
                cursor.execute("""
                    INSERT INTO certifications (module_id, certification_name, certified)
                    VALUES (?, ?, ?)
                """, (module_id, cert_name, certified))

        # Insert additional certifications
        if certification_info.certifications:
            for cert in certification_info.certifications:
                cursor.execute("""
                    INSERT INTO certifications (module_id, certification_name, certified)
                    VALUES (?, ?, ?)
                """, (module_id, cert, True))

    def _insert_raw_data(self, cursor, module_id: int, raw_pan_data: dict) -> None:
        """Helper method to insert raw PAN data."""
        for key, value in raw_pan_data.items():
            cursor.execute("""
                INSERT INTO raw_pan_data (module_id, parameter_name, parameter_value)
                VALUES (?, ?, ?)
            """, (module_id, key, str(value)))

    def get_module_by_id(self, module_id: int) -> Optional[Dict]:
        """Get a module by its database ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM pv_modules WHERE id = ?", (module_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def search_modules(self,
                      manufacturer: Optional[str] = None,
                      model: Optional[str] = None,
                      min_power: Optional[float] = None,
                      max_power: Optional[float] = None,
                      min_efficiency: Optional[float] = None,
                      max_efficiency: Optional[float] = None,
                      cell_type: Optional[str] = None,
                      module_type: Optional[str] = None,
                      min_height: Optional[float] = None,
                      max_height: Optional[float] = None,
                      min_width: Optional[float] = None,
                      max_width: Optional[float] = None,
                      sort_by: Optional[str] = None,
                      sort_order: str = "desc",
                      limit: Optional[int] = None) -> List[Dict]:
        """
        Search modules with various filters.

        Args:
            manufacturer: Filter by manufacturer name (partial match)
            model: Filter by model name (partial match)
            min_power: Minimum power in watts
            max_power: Maximum power in watts
            min_efficiency: Minimum efficiency in %
            max_efficiency: Maximum efficiency in %
            cell_type: Filter by cell type
            min_height: Minimum height in mm
            max_height: Maximum height in mm
            min_width: Minimum width in mm
            max_width: Maximum width in mm
            limit: Maximum number of results

        Returns:
            List of matching modules
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM pv_modules WHERE 1=1"
            params = []

            if manufacturer:
                query += " AND manufacturer LIKE ?"
                params.append(f"%{manufacturer}%")

            if model:
                query += " AND model LIKE ?"
                params.append(f"%{model}%")

            if min_power is not None:
                query += " AND pmax_stc >= ?"
                params.append(min_power)

            if max_power is not None:
                query += " AND pmax_stc <= ?"
                params.append(max_power)

            if min_efficiency is not None:
                query += " AND efficiency_stc >= ?"
                params.append(min_efficiency)

            if max_efficiency is not None:
                query += " AND efficiency_stc <= ?"
                params.append(max_efficiency)

            if cell_type:
                query += " AND cell_type = ?"
                params.append(cell_type)

            if module_type:
                query += " AND module_type = ?"
                params.append(module_type)

            if min_height is not None:
                query += " AND height >= ?"
                params.append(min_height)

            if max_height is not None:
                query += " AND height <= ?"
                params.append(max_height)

            if min_width is not None:
                query += " AND width >= ?"
                params.append(min_width)

            if max_width is not None:
                query += " AND width <= ?"
                params.append(max_width)

            # Sorting (whitelist to avoid SQL injection)
            allowed_sort = {
                "pmax_stc", "efficiency_stc", "voc_stc", "isc_stc",
                "vmp_stc", "imp_stc", "manufacturer", "model"
            }
            if sort_by in allowed_sort:
                order = "DESC" if str(sort_order).lower() == "desc" else "ASC"
                query += f" ORDER BY {sort_by} {order}"
            else:
                query += " ORDER BY pmax_stc DESC"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_manufacturers(self) -> List[str]:
        """Get list of all manufacturers in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT manufacturer FROM pv_modules ORDER BY manufacturer")
            return [row[0] for row in cursor.fetchall()]

    def get_cell_types(self) -> List[str]:
        """Get list of all cell types in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT cell_type FROM pv_modules WHERE cell_type IS NOT NULL ORDER BY cell_type")
            return [row[0] for row in cursor.fetchall()]

    def get_module_types(self) -> List[str]:
        """Get list of all module types in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT module_type FROM pv_modules WHERE module_type IS NOT NULL ORDER BY module_type")
            return [row[0] for row in cursor.fetchall()]

    def get_models_by_manufacturer(self, manufacturer: str) -> List[str]:
        """Get list of models for a specific manufacturer."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT model FROM pv_modules
                WHERE manufacturer = ?
                ORDER BY model
            """, (manufacturer,))
            return [row[0] for row in cursor.fetchall()]

    def get_statistics(self) -> Dict[str, Union[int, float]]:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Basic counts
            cursor.execute("SELECT COUNT(*) FROM pv_modules")
            total_modules = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT manufacturer) FROM pv_modules")
            total_manufacturers = cursor.fetchone()[0]

            # Power statistics
            cursor.execute("""
                SELECT
                    MIN(pmax_stc) as min_power,
                    MAX(pmax_stc) as max_power,
                    AVG(pmax_stc) as avg_power
                FROM pv_modules
                WHERE pmax_stc IS NOT NULL
            """)
            power_stats = cursor.fetchone()

            # Efficiency statistics
            cursor.execute("""
                SELECT
                    MIN(efficiency_stc) as min_efficiency,
                    MAX(efficiency_stc) as max_efficiency,
                    AVG(efficiency_stc) as avg_efficiency
                FROM pv_modules
                WHERE efficiency_stc IS NOT NULL
            """)
            efficiency_stats = cursor.fetchone()

            # Cell type distribution
            cursor.execute("""
                SELECT cell_type, COUNT(*) as count
                FROM pv_modules
                GROUP BY cell_type
                ORDER BY count DESC
            """)
            cell_types = dict(cursor.fetchall())

            # Models count (distinct models across manufacturers)
            cursor.execute("SELECT COUNT(DISTINCT model) FROM pv_modules")
            total_models = cursor.fetchone()[0]

            # Build backward-compatible structure
            min_power = float(power_stats[0]) if power_stats and power_stats[0] is not None else 0.0
            max_power = float(power_stats[1]) if power_stats and power_stats[1] is not None else 0.0
            avg_power = float(power_stats[2]) if power_stats and power_stats[2] is not None else 0.0
            min_eff = float(efficiency_stats[0]) if efficiency_stats and efficiency_stats[0] is not None else 0.0
            max_eff = float(efficiency_stats[1]) if efficiency_stats and efficiency_stats[1] is not None else 0.0
            avg_eff = float(efficiency_stats[2]) if efficiency_stats and efficiency_stats[2] is not None else 0.0

            return {
                "total_modules": total_modules,
                "total_manufacturers": total_manufacturers,
                "total_models": total_models,
                # flat stats
                "min_power": min_power,
                "max_power": max_power,
                "avg_power": avg_power,
                "min_efficiency": min_eff,
                "max_efficiency": max_eff,
                "avg_efficiency": avg_eff,
                # nested ranges for CLI/UI compatibility
                "power_range": {"min": min_power, "max": max_power, "avg": avg_power},
                "efficiency_range": {"min": min_eff, "max": max_eff, "avg": avg_eff},
                # distributions
                "cell_type_distribution": cell_types,
            }

    def get_cell_type_statistics(self) -> List[Dict[str, Any]]:
        """Aggregate statistics grouped by cell type."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    cell_type,
                    COUNT(*) as count,
                    AVG(pmax_stc) as avg_power,
                    AVG(efficiency_stc) as avg_efficiency
                FROM pv_modules
                WHERE cell_type IS NOT NULL
                GROUP BY cell_type
                ORDER BY count DESC
                """
            )
            rows = cursor.fetchall()
            return [
                {
                    "cell_type": row[0] or "unknown",
                    "count": row[1] or 0,
                    "avg_power": round(row[2], 1) if row[2] else 0,
                    "avg_efficiency": round(row[3], 2) if row[3] else 0,
                }
                for row in rows
            ]

    def get_module_type_statistics(self) -> List[Dict[str, Any]]:
        """Aggregate statistics grouped by module type."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    module_type,
                    COUNT(*) as count,
                    AVG(pmax_stc) as avg_power,
                    AVG(efficiency_stc) as avg_efficiency
                FROM pv_modules
                WHERE module_type IS NOT NULL
                GROUP BY module_type
                ORDER BY count DESC
                """
            )
            rows = cursor.fetchall()
            return [
                {
                    "module_type": row[0] or "unknown",
                    "count": row[1] or 0,
                    "avg_power": round(row[2], 1) if row[2] else 0,
                    "avg_efficiency": round(row[3], 2) if row[3] else 0,
                }
                for row in rows
            ]

    def get_power_range_distribution(self, bin_size: Optional[float] = None) -> List[Dict[str, Any]]:
        """Return distribution of modules across power ranges."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MIN(pmax_stc), MAX(pmax_stc) FROM pv_modules WHERE pmax_stc IS NOT NULL")
            row = cursor.fetchone()
            if not row or row[0] is None or row[1] is None:
                return []

            min_power, max_power = float(row[0]), float(row[1])
            span = max_power - min_power
            if span <= 0:
                return []

            # Choose a reasonable bin size
            if bin_size is None:
                if span <= 500:
                    bin_size = 50
                elif span <= 1000:
                    bin_size = 100
                else:
                    bin_size = 200

            # Build bins
            start = int(min_power // bin_size * bin_size)
            end = int((max_power // bin_size + 1) * bin_size)
            bins = []
            for bmin in range(start, end, int(bin_size)):
                bins.append({"min_power": bmin, "max_power": bmin + bin_size, "count": 0})

            # Fetch all powers and bin in Python for simplicity
            cursor.execute("SELECT pmax_stc FROM pv_modules WHERE pmax_stc IS NOT NULL")
            powers = [float(r[0]) for r in cursor.fetchall()]
            for p in powers:
                idx = int((p - start) // bin_size)
                if 0 <= idx < len(bins):
                    bins[idx]["count"] += 1

            return bins

    def get_efficiency_range_distribution(self, bin_size: Optional[float] = None) -> List[Dict[str, Any]]:
        """Return distribution of modules across efficiency ranges."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MIN(efficiency_stc), MAX(efficiency_stc) FROM pv_modules WHERE efficiency_stc IS NOT NULL")
            row = cursor.fetchone()
            if not row or row[0] is None or row[1] is None:
                return []

            min_eff, max_eff = float(row[0]), float(row[1])
            span = max_eff - min_eff
            if span <= 0:
                return []

            # Choose reasonable bin size in percentage points
            if bin_size is None:
                if span <= 5:
                    bin_size = 0.25
                elif span <= 10:
                    bin_size = 0.5
                else:
                    bin_size = 1.0

            # Build bins
            import math
            start = math.floor(min_eff / bin_size) * bin_size
            end = math.ceil(max_eff / bin_size) * bin_size
            bins = []
            current = start
            while current < end:
                bins.append({"min_efficiency": current, "max_efficiency": current + bin_size, "count": 0})
                current += bin_size

            # Fetch all efficiencies and bin
            cursor.execute("SELECT efficiency_stc FROM pv_modules WHERE efficiency_stc IS NOT NULL")
            effs = [float(r[0]) for r in cursor.fetchall()]
            for e in effs:
                idx = int((e - start) // bin_size)
                if 0 <= idx < len(bins):
                    bins[idx]["count"] += 1

            return bins

    def get_manufacturer_statistics(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get statistics grouped by manufacturer."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    manufacturer,
                    COUNT(*) as module_count,
                    AVG(pmax_stc) as avg_power,
                    AVG(efficiency_stc) as avg_efficiency,
                    MIN(pmax_stc) as min_power,
                    MAX(pmax_stc) as max_power
                FROM pv_modules
                WHERE pmax_stc IS NOT NULL
                GROUP BY manufacturer
                ORDER BY module_count DESC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query)
            results = cursor.fetchall()

            return [
                {
                    "manufacturer": row[0],
                    "module_count": row[1],
                    "avg_power": round(row[2], 1) if row[2] else 0,
                    "avg_efficiency": round(row[3], 2) if row[3] else 0,
                    "min_power": row[4] if row[4] else 0,
                    "max_power": row[5] if row[5] else 0,
                    "power_range": f"{row[4]:.0f}-{row[5]:.0f}W" if row[4] and row[5] else "N/A"
                }
                for row in results
            ]

    # --- New helpers for raw values (for box plots and advanced charts) ---
    def get_all_powers(self) -> List[float]:
        """Return a list of all module Pmax (W) values available."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pmax_stc FROM pv_modules WHERE pmax_stc IS NOT NULL")
            return [float(r[0]) for r in cursor.fetchall() if r[0] is not None]

    def get_all_efficiencies(self) -> List[float]:
        """Return a list of all module efficiency (%) values available."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT efficiency_stc FROM pv_modules WHERE efficiency_stc IS NOT NULL")
            return [float(r[0]) for r in cursor.fetchall() if r[0] is not None]

    def export_to_csv(self, output_file: str, filters: Optional[Dict] = None) -> int:
        """
        Export modules to CSV file.

        Args:
            output_file: Path to output CSV file
            filters: Optional filters to apply (same as search_modules)

        Returns:
            Number of modules exported
        """
        import csv

        # Get modules with filters
        if filters:
            modules = self.search_modules(**filters)
        else:
            modules = self.search_modules()

        if not modules:
            return 0

        # Write to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = modules[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for module in modules:
                writer.writerow(module)

        return len(modules)

    def compare_modules(self, module_ids: List[int]) -> List[Dict]:
        """
        Compare multiple modules side by side.

        Args:
            module_ids: List of module IDs to compare

        Returns:
            List of module data for comparison
        """
        modules = []
        for module_id in module_ids:
            module = self.get_module_by_id(module_id)
            if module:
                modules.append(module)

        return modules

    def get_size_range(self) -> Dict[str, float]:
        """Get min/max ranges for height and width in mm."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT MIN(height), MAX(height), MIN(width), MAX(width)
                FROM pv_modules
                WHERE height IS NOT NULL AND width IS NOT NULL
                """
            )
            row = cursor.fetchone()
            if not row:
                return {"height_min": 0, "height_max": 0, "width_min": 0, "width_max": 0}
            return {
                "height_min": float(row[0]) if row[0] is not None else 0,
                "height_max": float(row[1]) if row[1] is not None else 0,
                "width_min": float(row[2]) if row[2] is not None else 0,
                "width_max": float(row[3]) if row[3] is not None else 0,
            }

    def bulk_insert_from_parser_results(self, results: Dict[str, ParsingResult], update_existing: bool = True) -> Dict[str, int]:
        """
        Bulk insert modules from parser results.

        Args:
            results: Dictionary of parsing results from parser
            update_existing: Whether to update existing modules or skip them

        Returns:
            Dictionary with statistics of insertion
        """
        inserted = 0
        updated = 0
        skipped = 0
        failed = 0

        for file_path, result in results.items():
            if result.success and result.module:
                try:
                    if self.module_exists(result.module.unique_id):
                        if update_existing:
                            self.insert_module(result.module, update_if_exists=True)
                            updated += 1
                        else:
                            skipped += 1
                    else:
                        self.insert_module(result.module, update_if_exists=False)
                        inserted += 1
                except Exception as e:
                    print(f"Failed to insert module from {file_path}: {e}")
                    failed += 1
            else:
                failed += 1

        return {
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
            "failed": failed,
            "total": len(results)
        }

    def clear_database(self) -> None:
        """Clear all data from the database (for testing purposes)."""
        import gc
        import time

        # Force garbage collection to close any lingering connections
        gc.collect()
        time.sleep(0.1)  # Small delay

        try:
            if self.db_path.exists():
                # Remove the entire database file to force schema recreation
                self.db_path.unlink()
                print("Database file deleted successfully")
            else:
                print("No database file found")
        except PermissionError:
            # Fallback: just clear the data if file is locked
            print("Database file locked, clearing data instead")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DROP TABLE IF EXISTS raw_pan_data")
                cursor.execute("DROP TABLE IF EXISTS certifications")
                cursor.execute("DROP TABLE IF EXISTS pv_modules")
                conn.commit()
                print("Database tables dropped successfully")

        # Reinitialize with new schema
        self.init_database()

    # --- Maintenance and utility operations expected by CLI/Desktop ---
    def vacuum_database(self) -> None:
        """Run VACUUM to rebuild the database file and reclaim space."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("VACUUM")
            conn.commit()

    def analyze_database(self) -> None:
        """Run ANALYZE to update SQLite statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("ANALYZE")
            conn.commit()

    def rebuild_indexes(self) -> None:
        """Rebuild indexes (REINDEX)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("REINDEX")
            conn.commit()

    def check_integrity(self) -> Dict[str, Any]:
        """Run PRAGMA integrity_check and return results."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                rows = cursor.fetchall()
                errors = [r[0] for r in rows if r and r[0] != "ok"]
                return {"ok": len(errors) == 0, "errors": errors}
        except Exception as e:
            return {"ok": False, "errors": [str(e)]}

    def get_table_info(self) -> List[Dict[str, Any]]:
        """Return basic table info: name and row counts.

        Note: SQLite doesn't provide per-table size easily; size_bytes will be 0.
        """
        info: List[Dict[str, Any]] = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [r[0] for r in cursor.fetchall()]
            for t in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {t}")
                    count = int(cursor.fetchone()[0])
                except Exception:
                    count = 0
                info.append({"name": t, "row_count": count, "size_bytes": 0})
        return info

    def get_raw_pan_data(self, module_id: int) -> Dict[str, Any]:
        """Return raw .PAN key/value data for a given module id."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT parameter_name, parameter_value FROM raw_pan_data WHERE module_id = ?",
                (module_id,),
            )
            rows = cursor.fetchall()
            return {name: value for name, value in rows}

    def find_orphaned_records(self) -> List[Dict[str, Any]]:
        """Find records in auxiliary tables that reference non-existent modules."""
        issues: List[Dict[str, Any]] = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Certifications orphans
            cursor.execute(
                """
                SELECT c.id, c.module_id FROM certifications c
                LEFT JOIN pv_modules m ON m.id = c.module_id
                WHERE m.id IS NULL
                """
            )
            for cid, mid in cursor.fetchall():
                issues.append({"table": "certifications", "id": cid, "module_id": mid})

            # Raw PAN orphans
            cursor.execute(
                """
                SELECT r.id, r.module_id FROM raw_pan_data r
                LEFT JOIN pv_modules m ON m.id = r.module_id
                WHERE m.id IS NULL
                """
            )
            for rid, mid in cursor.fetchall():
                issues.append({"table": "raw_pan_data", "id": rid, "module_id": mid})
        return issues

    def get_technology_statistics(self) -> Dict[str, Any]:
        """Return simple technology statistics for CLI/UI usage."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Most common cell type
            cursor.execute(
                """
                SELECT cell_type, COUNT(*) as cnt
                FROM pv_modules
                WHERE cell_type IS NOT NULL
                GROUP BY cell_type
                ORDER BY cnt DESC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            most_common_cell_type = row[0] if row else None

            # Most common module type
            cursor.execute(
                """
                SELECT module_type, COUNT(*) as cnt
                FROM pv_modules
                WHERE module_type IS NOT NULL
                GROUP BY module_type
                ORDER BY cnt DESC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            most_common_module_type = row[0] if row else None

            # Averages
            cursor.execute(
                "SELECT AVG(area_m2), AVG(power_density) FROM pv_modules WHERE area_m2 IS NOT NULL"
            )
            row = cursor.fetchone()
            avg_area = float(row[0]) if row and row[0] is not None else 0.0
            avg_power_density = float(row[1]) if row and row[1] is not None else 0.0

            return {
                "most_common_cell_type": most_common_cell_type or "unknown",
                "most_common_module_type": most_common_module_type or "unknown",
                "avg_area": avg_area,
                "avg_power_density": avg_power_density,
            }