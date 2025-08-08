"""
Search controller for PV PAN Tool Desktop Application.

This module provides search functionality and manages search operations
for the desktop application.
"""

from typing import Any, Dict, List, Optional, Tuple

from .database_controller import DatabaseController


class SearchController:
    """Controller for search operations."""

    def __init__(self, db_controller: DatabaseController):
        """
        Initialize the search controller.

        Args:
            db_controller: Database controller instance
        """
        self.db_controller = db_controller
        self.search_history = []
        self.saved_searches = {}

    def search_modules(self, search_params: Dict[str, Any]):
        """Search for modules and return a simple list for the UI table."""
        try:
            criteria = self._build_search_criteria(search_params)
            modules = self.db_controller.search_modules(criteria)

            # Optional in-memory sorting when requested by UI
            sort_by = criteria.get("sort_by")
            sort_order = criteria.get("sort_order", "desc")
            if sort_by:
                try:
                    modules.sort(key=lambda m: (m.get(sort_by) is None, m.get(sort_by)),
                                 reverse=(sort_order == "desc"))
                except Exception:
                    pass

            self._add_to_history(search_params, len(modules))
            return modules
        except Exception as e:
            return []

    def _build_search_criteria(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build database search criteria from search parameters.

        Args:
            search_params: Search parameters from UI

        Returns:
            Database search criteria
        """
        criteria = {}

        # Text filters
        if search_params.get("manufacturer"):
            criteria["manufacturer"] = search_params["manufacturer"]

        if search_params.get("model"):
            criteria["model"] = search_params["model"]

        if search_params.get("series"):
            criteria["series"] = search_params["series"]

        # Power range
        if search_params.get("power_min") is not None:
            criteria["power_min"] = search_params["power_min"]

        if search_params.get("power_max") is not None:
            criteria["power_max"] = search_params["power_max"]

        # Efficiency range
        if search_params.get("efficiency_min") is not None:
            criteria["efficiency_min"] = search_params["efficiency_min"]

        if search_params.get("efficiency_max") is not None:
            criteria["efficiency_max"] = search_params["efficiency_max"]

        # Voltage range
        if search_params.get("voltage_min") is not None:
            criteria["voltage_min"] = search_params["voltage_min"]

        if search_params.get("voltage_max") is not None:
            criteria["voltage_max"] = search_params["voltage_max"]

        # Current range
        if search_params.get("current_min") is not None:
            criteria["current_min"] = search_params["current_min"]

        if search_params.get("current_max") is not None:
            criteria["current_max"] = search_params["current_max"]

        # Cell type
        if search_params.get("cell_type"):
            criteria["cell_type"] = search_params["cell_type"]

        # Module type
        if search_params.get("module_type"):
            criteria["module_type"] = search_params["module_type"]

        # Size (height/width)
        if search_params.get("min_height") is not None:
            criteria["height_min"] = search_params["min_height"]

        if search_params.get("max_height") is not None:
            criteria["height_max"] = search_params["max_height"]

        if search_params.get("min_width") is not None:
            criteria["width_min"] = search_params["min_width"]

        if search_params.get("max_width") is not None:
            criteria["width_max"] = search_params["max_width"]

        # Sorting
        criteria["sort_by"] = search_params.get("sort_by", "pmax_stc")
        criteria["sort_order"] = search_params.get("sort_order", "desc")
        criteria["limit"] = search_params.get("limit", 100)

        return criteria

    def get_quick_search_suggestions(self, query: str, field: str = "manufacturer") -> List[str]:
        """
        Get quick search suggestions for autocomplete.

        Args:
            query: Partial query string
            field: Field to search in (manufacturer, model, etc.)

        Returns:
            List of suggestions
        """
        try:
            if field == "manufacturer":
                all_manufacturers = self.db_controller.get_manufacturers()
                return [m for m in all_manufacturers if query.lower() in m.lower()][:10]

            elif field == "model":
                # For models, we need to search across all models
                # This is a simplified implementation
                criteria = {"model": query}
                modules = self.db_controller.search_modules(criteria)
                models = list(set([m.get("model", "") for m in modules if m.get("model")]))
                return models[:10]

            elif field == "cell_type":
                all_cell_types = self.db_controller.get_cell_types()
                return [ct for ct in all_cell_types if query.lower() in ct.lower()]

            elif field == "module_type":
                all_module_types = self.db_controller.get_module_types()
                return [mt for mt in all_module_types if query.lower() in mt.lower()]

            return []

        except Exception as e:
            print(f"Error getting suggestions: {e}")
            return []

    def get_filter_options(self) -> Dict[str, List[str]]:
        """
        Get available filter options for dropdowns.

        Returns:
            Dictionary with filter options
        """
        try:
            return {
                "manufacturers": self.db_controller.get_manufacturers(),
                "cell_types": self.db_controller.get_cell_types(),
                "module_types": self.db_controller.get_module_types(),
                "power_range": self.db_controller.get_power_range(),
                "efficiency_range": self.db_controller.get_efficiency_range()
            }
        except Exception as e:
            print(f"Error getting filter options: {e}")
            return {
                "manufacturers": [],
                "cell_types": [],
                "module_types": [],
                "power_range": {"min": 0, "max": 1000},
                "efficiency_range": {"min": 0, "max": 25}
            }

    def get_advanced_search_options(self) -> Dict[str, Any]:
        """
        Get options for advanced search.

        Returns:
            Dictionary with advanced search options
        """
        try:
            stats = self.db_controller.get_basic_statistics()
            power_range = self.db_controller.get_power_range()
            efficiency_range = self.db_controller.get_efficiency_range()

            return {
                "total_modules": stats.get("total_modules", 0),
                "manufacturers": self.db_controller.get_manufacturers(),
                "cell_types": self.db_controller.get_cell_types(),
                "module_types": self.db_controller.get_module_types(),
                "power_range": power_range,
                "efficiency_range": efficiency_range,
                "sort_options": [
                    ("pmax_stc", "Power (W)"),
                    ("efficiency_stc", "Efficiency (%)"),
                    ("voc_stc", "Open Circuit Voltage (V)"),
                    ("isc_stc", "Short Circuit Current (A)"),
                    ("manufacturer", "Manufacturer"),
                    ("model", "Model")
                ]
            }
        except Exception as e:
            print(f"Error getting advanced search options: {e}")
            return {}

    def save_search(self, name: str, search_params: Dict[str, Any]) -> bool:
        """
        Save a search for later use.

        Args:
            name: Name for the saved search
            search_params: Search parameters to save

        Returns:
            True if successful, False otherwise
        """
        try:
            self.saved_searches[name] = search_params.copy()
            return True
        except Exception as e:
            print(f"Error saving search: {e}")
            return False

    def load_saved_search(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a saved search.

        Args:
            name: Name of the saved search

        Returns:
            Search parameters or None if not found
        """
        return self.saved_searches.get(name)

    def get_saved_searches(self) -> List[str]:
        """
        Get list of saved search names.

        Returns:
            List of saved search names
        """
        return list(self.saved_searches.keys())

    def delete_saved_search(self, name: str) -> bool:
        """
        Delete a saved search.

        Args:
            name: Name of the search to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            if name in self.saved_searches:
                del self.saved_searches[name]
                return True
            return False
        except Exception as e:
            print(f"Error deleting saved search: {e}")
            return False

    def _add_to_history(self, search_params: Dict[str, Any], result_count: int):
        """
        Add search to history.

        Args:
            search_params: Search parameters
            result_count: Number of results found
        """
        from datetime import datetime

        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "params": search_params.copy(),
            "result_count": result_count
        }

        self.search_history.insert(0, history_entry)

        # Keep only last 50 searches
        if len(self.search_history) > 50:
            self.search_history = self.search_history[:50]

    def get_search_history(self) -> List[Dict[str, Any]]:
        """
        Get search history.

        Returns:
            List of search history entries
        """
        return self.search_history.copy()

    def clear_search_history(self):
        """Clear search history."""
        self.search_history.clear()

    def get_popular_searches(self) -> List[Dict[str, Any]]:
        """
        Get popular search patterns.

        Returns:
            List of popular search patterns
        """
        # Analyze search history to find popular patterns
        manufacturer_counts = {}
        cell_type_counts = {}

        for entry in self.search_history:
            params = entry["params"]

            if "manufacturer" in params:
                manufacturer = params["manufacturer"]
                manufacturer_counts[manufacturer] = manufacturer_counts.get(manufacturer, 0) + 1

            if "cell_type" in params:
                cell_type = params["cell_type"]
                cell_type_counts[cell_type] = cell_type_counts.get(cell_type, 0) + 1

        popular = []

        # Top manufacturers
        for manufacturer, count in sorted(manufacturer_counts.items(),
                                        key=lambda x: x[1], reverse=True)[:5]:
            popular.append({
                "type": "manufacturer",
                "value": manufacturer,
                "count": count,
                "description": f"Manufacturer: {manufacturer}"
            })

        # Top cell types
        for cell_type, count in sorted(cell_type_counts.items(),
                                     key=lambda x: x[1], reverse=True)[:3]:
            popular.append({
                "type": "cell_type",
                "value": cell_type,
                "count": count,
                "description": f"Cell Type: {cell_type}"
            })

        return popular

    def export_search_results(self, modules: List[Dict[str, Any]],
                            format: str = "csv") -> Optional[str]:
        """
        Export search results to file.

        Args:
            modules: List of modules to export
            format: Export format (csv, json, xlsx)

        Returns:
            Path to exported file or None if failed
        """
        try:
            import os
            import tempfile
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if format == "csv":
                import csv

                temp_file = tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix=f'_search_results_{timestamp}.csv',
                    delete=False
                )

                if modules:
                    fieldnames = modules[0].keys()
                    writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(modules)

                temp_file.close()
                return temp_file.name

            elif format == "json":
                import json

                temp_file = tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix=f'_search_results_{timestamp}.json',
                    delete=False
                )

                json.dump(modules, temp_file, indent=2, default=str)
                temp_file.close()
                return temp_file.name

            return None

        except Exception as e:
            print(f"Error exporting search results: {e}")
            return None
