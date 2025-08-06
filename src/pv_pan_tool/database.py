"""
Database management for PV module specifications.

This module provides functionality to store, query, and manage
PV module data in a SQLite database.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from .models import PVModule, ParsingResult


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
                    series_fuse_rating REAL,
                    max_system_voltage REAL,
                    
                    -- Physical parameters
                    length REAL,
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
                module.physical_params.length and 
                module.physical_params.width):
                try:
                    length = float(module.physical_params.length)
                    width = float(module.physical_params.width)
                    pmax = float(module.electrical_params.pmax_stc)
                    
                    area_m2 = (length * width) / 1_000_000  # mm² to m²
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
                    noct, series_fuse_rating, max_system_voltage,
                    length, width, thickness, weight,
                    cells_in_series, cells_in_parallel, total_cells,
                    cell_type, module_type,
                    efficiency_stc, power_density, area_m2,
                    file_path, file_name, file_size, file_hash,
                    manufacturer_folder, model_folder,
                    parsed_at, parser_version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                module.unique_id,
                module.manufacturer_info.name,
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
                module.electrical_params.series_fuse_rating,
                module.electrical_params.max_system_voltage,
                module.physical_params.length,
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
            self._insert_raw_data(cursor, module_id, module.raw_pan_data)
            
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
                module.physical_params.length and 
                module.physical_params.width):
                try:
                    length = float(module.physical_params.length)
                    width = float(module.physical_params.width)
                    pmax = float(module.electrical_params.pmax_stc)
                    
                    area_m2 = (length * width) / 1_000_000  # mm² to m²
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
                    noct = ?, series_fuse_rating = ?, max_system_voltage = ?,
                    length = ?, width = ?, thickness = ?, weight = ?,
                    cells_in_series = ?, cells_in_parallel = ?, total_cells = ?,
                    cell_type = ?, module_type = ?,
                    efficiency_stc = ?, power_density = ?, area_m2 = ?,
                    file_path = ?, file_name = ?, file_size = ?, file_hash = ?,
                    manufacturer_folder = ?, model_folder = ?,
                    parsed_at = ?, parser_version = ?, updated_at = ?
                WHERE id = ?
            """, (
                module.manufacturer_info.name,
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
                module.electrical_params.series_fuse_rating,
                module.electrical_params.max_system_voltage,
                module.physical_params.length,
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
            self._insert_raw_data(cursor, module_id, module.raw_pan_data)
            
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
            
            return {
                "total_modules": total_modules,
                "total_manufacturers": total_manufacturers,
                "min_power": power_stats[0] if power_stats[0] else 0,
                "max_power": power_stats[1] if power_stats[1] else 0,
                "avg_power": power_stats[2] if power_stats[2] else 0,
                "min_efficiency": efficiency_stats[0] if efficiency_stats[0] else 0,
                "max_efficiency": efficiency_stats[1] if efficiency_stats[1] else 0,
                "avg_efficiency": efficiency_stats[2] if efficiency_stats[2] else 0,
                "cell_type_distribution": cell_types
            }
    
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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM raw_pan_data")
            cursor.execute("DELETE FROM certifications")
            cursor.execute("DELETE FROM pv_modules")
            conn.commit()
            print("Database cleared successfully")

