"""
Database controller for PV PAN Tool Desktop Application.

This module provides a controller layer between the UI and the database,
handling all database operations and data management.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add the src directory to the Python path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent / "src"
sys.path.insert(0, str(src_dir))

from pv_pan_tool.database import PVModuleDatabase
from pv_pan_tool.models import PVModule, ParsingResult
from pv_pan_tool.parser import PANParser


class DatabaseController:
    """Controller for database operations."""
    
    def __init__(self, db_path: str = None):
        """
        Initialize the database controller.
        
        Args:
            db_path: Path to the database file. If None, uses default path.
        """
        if db_path is None:
            # Use default database path relative to the project root
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "data" / "database" / "pv_modules.db"
        
        self.db_path = str(db_path)
        self.database = PVModuleDatabase(self.db_path)
        self.parser = PANParser()
    
    def get_basic_statistics(self) -> Dict[str, Any]:
        """
        Get basic database statistics.
        
        Returns:
            Dictionary containing basic statistics
        """
        try:
            return self.database.get_statistics()
        except Exception as e:
            return {
                "total_modules": 0,
                "total_manufacturers": 0,
                "total_models": 0,
                "error": str(e)
            }
    
    def get_detailed_statistics(self) -> Dict[str, Any]:
        """
        Get detailed database statistics.
        
        Returns:
            Dictionary containing detailed statistics
        """
        try:
            stats = self.database.get_statistics()
            
            # Add manufacturer statistics
            manufacturer_stats = self.database.get_manufacturer_statistics()
            stats["manufacturer_statistics"] = manufacturer_stats
            
            # Add cell type statistics
            cell_type_stats = self.database.get_cell_type_statistics()
            stats["cell_type_statistics"] = cell_type_stats
            
            # Add power range distribution
            power_ranges = self.database.get_power_range_distribution()
            stats["power_range_distribution"] = power_ranges
            
            # Add efficiency range distribution
            efficiency_ranges = self.database.get_efficiency_range_distribution()
            stats["efficiency_range_distribution"] = efficiency_ranges
            
            return stats
            
        except Exception as e:
            return {"error": str(e)}
    
    def search_modules(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for modules based on criteria.
        
        Args:
            criteria: Search criteria dictionary
            
        Returns:
            List of matching modules
        """
        try:
            return self.database.search_modules(
                criteria=criteria,
                sort_by=criteria.get("sort_by", "pmax_stc"),
                sort_order=criteria.get("sort_order", "desc"),
                limit=criteria.get("limit", 100)
            )
        except Exception as e:
            print(f"Error searching modules: {e}")
            return []
    
    def get_module_by_id(self, module_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific module by ID.
        
        Args:
            module_id: The module ID
            
        Returns:
            Module data or None if not found
        """
        try:
            return self.database.get_module_by_id(module_id)
        except Exception as e:
            print(f"Error getting module {module_id}: {e}")
            return None
    
    def get_modules_by_ids(self, module_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Get multiple modules by their IDs.
        
        Args:
            module_ids: List of module IDs
            
        Returns:
            List of module data
        """
        modules = []
        for module_id in module_ids:
            module = self.get_module_by_id(module_id)
            if module:
                modules.append(module)
        return modules
    
    def get_manufacturers(self) -> List[str]:
        """
        Get list of all manufacturers.
        
        Returns:
            List of manufacturer names
        """
        try:
            return self.database.get_manufacturers()
        except Exception as e:
            print(f"Error getting manufacturers: {e}")
            return []
    
    def get_models_by_manufacturer(self, manufacturer: str) -> List[str]:
        """
        Get list of models for a specific manufacturer.
        
        Args:
            manufacturer: Manufacturer name
            
        Returns:
            List of model names
        """
        try:
            return self.database.get_models_by_manufacturer(manufacturer)
        except Exception as e:
            print(f"Error getting models for {manufacturer}: {e}")
            return []
    
    def get_cell_types(self) -> List[str]:
        """
        Get list of all cell types.
        
        Returns:
            List of cell types
        """
        try:
            return self.database.get_cell_types()
        except Exception as e:
            print(f"Error getting cell types: {e}")
            return []
    
    def get_module_types(self) -> List[str]:
        """
        Get list of all module types.
        
        Returns:
            List of module types
        """
        try:
            return self.database.get_module_types()
        except Exception as e:
            print(f"Error getting module types: {e}")
            return []
    
    def get_power_range(self) -> Dict[str, float]:
        """
        Get the power range of all modules.
        
        Returns:
            Dictionary with min and max power values
        """
        try:
            stats = self.database.get_statistics()
            return stats.get("power_range", {"min": 0, "max": 0})
        except Exception as e:
            print(f"Error getting power range: {e}")
            return {"min": 0, "max": 0}
    
    def get_efficiency_range(self) -> Dict[str, float]:
        """
        Get the efficiency range of all modules.
        
        Returns:
            Dictionary with min and max efficiency values
        """
        try:
            stats = self.database.get_statistics()
            return stats.get("efficiency_range", {"min": 0, "max": 0})
        except Exception as e:
            print(f"Error getting efficiency range: {e}")
            return {"min": 0, "max": 0}
    
    def parse_pan_files(self, directory: str, new_only: bool = False, 
                       max_files: int = None, progress_callback=None) -> Dict[str, Any]:
        """
        Parse .PAN files from a directory.
        
        Args:
            directory: Directory containing .PAN files
            new_only: Only parse new or modified files
            max_files: Maximum number of files to process
            progress_callback: Callback function for progress updates
            
        Returns:
            Dictionary with parsing results
        """
        try:
            directory_path = Path(directory)
            if not directory_path.exists():
                return {"error": f"Directory does not exist: {directory}"}
            
            # Find .PAN files
            pan_files = list(directory_path.glob("**/*.PAN"))
            pan_files.extend(list(directory_path.glob("**/*.pan")))
            
            if not pan_files:
                return {"error": "No .PAN files found in directory"}
            
            if max_files:
                pan_files = pan_files[:max_files]
            
            results = {
                "total_files": len(pan_files),
                "processed": 0,
                "successful": 0,
                "failed": 0,
                "errors": []
            }
            
            for i, pan_file in enumerate(pan_files):
                try:
                    # Update progress
                    if progress_callback:
                        progress_callback(i, len(pan_files), str(pan_file.name))
                    
                    # Check if file should be skipped (new_only mode)
                    if new_only and self.database.is_file_processed(str(pan_file)):
                        continue
                    
                    # Parse the file
                    parsing_result = self.parser.parse_file(str(pan_file))
                    
                    if parsing_result.success and parsing_result.module:
                        # Insert into database
                        module_id = self.database.insert_module(
                            parsing_result.module,
                            str(pan_file),
                            parsing_result.raw_content
                        )
                        
                        if module_id:
                            results["successful"] += 1
                        else:
                            results["failed"] += 1
                            results["errors"].append(f"Failed to insert {pan_file.name}")
                    else:
                        results["failed"] += 1
                        error_msg = f"Failed to parse {pan_file.name}"
                        if parsing_result.errors:
                            error_msg += f": {', '.join(parsing_result.errors)}"
                        results["errors"].append(error_msg)
                    
                    results["processed"] += 1
                    
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"Error processing {pan_file.name}: {str(e)}")
            
            # Final progress update
            if progress_callback:
                progress_callback(len(pan_files), len(pan_files), "Complete")
            
            return results
            
        except Exception as e:
            return {"error": f"Error during parsing: {str(e)}"}
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path for the backup file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def optimize_database(self) -> bool:
        """
        Optimize the database performance.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.database.vacuum_database()
            self.database.analyze_database()
            return True
        except Exception as e:
            print(f"Error optimizing database: {e}")
            return False
    
    def clear_database(self) -> bool:
        """
        Clear all data from the database.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.database.clear_database()
            return True
        except Exception as e:
            print(f"Error clearing database: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the database file.
        
        Returns:
            Dictionary with database information
        """
        try:
            db_file = Path(self.db_path)
            
            if not db_file.exists():
                return {"exists": False, "path": self.db_path}
            
            stat = db_file.stat()
            
            return {
                "exists": True,
                "path": self.db_path,
                "size_bytes": stat.st_size,
                "size_mb": stat.st_size / (1024 * 1024),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def test_connection(self) -> bool:
        """
        Test the database connection.
        
        Returns:
            True if connection is working, False otherwise
        """
        try:
            stats = self.database.get_statistics()
            return "total_modules" in stats
        except Exception:
            return False

