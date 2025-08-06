"""
PAN File Parser for PV Module Specifications.

This module provides functionality to parse .PAN files and extract
photovoltaic module specifications.
"""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from .models import (
    CellType,
    CertificationInfo,
    ElectricalParameters,
    FileMetadata,
    ManufacturerInfo,
    ModuleType,
    ParsedFileRegistry,
    ParsingResult,
    PhysicalParameters,
    PVModule,
)


class PANFileParser:
    """Parser for .PAN files containing PV module specifications."""

    def __init__(self, base_directory: str, registry_file: str = "parsed_files_registry.json"):
        """
        Initialize the PAN file parser.

        Args:
            base_directory: Base directory to scan for .PAN files
            registry_file: File to store parsing registry
        """
        self.base_directory = Path(base_directory)
        self.registry_file = Path(registry_file)
        self.registry: Dict[str, ParsedFileRegistry] = {}
        self.load_registry()

        # Parameter mapping for different .PAN file formats
        self.parameter_mappings = {
            # Electrical parameters
            "pmax_stc": ["Pmax", "P_max", "Pmax_stc", "Power", "Nominal_Power"],
            "vmp_stc": ["Vmp", "V_mp", "Vmpp", "V_mpp", "Voltage_at_Pmax"],
            "imp_stc": ["Imp", "I_mp", "Impp", "I_mpp", "Current_at_Pmax"],
            "voc_stc": ["Voc", "V_oc", "Open_Circuit_Voltage"],
            "isc_stc": ["Isc", "I_sc", "Short_Circuit_Current"],
            "temp_coeff_pmax": ["TempCoeff_Pmax", "Temp_Coeff_P", "Alpha_P"],
            "temp_coeff_voc": ["TempCoeff_Voc", "Temp_Coeff_V", "Beta_Voc"],
            "temp_coeff_isc": ["TempCoeff_Isc", "Temp_Coeff_I", "Alpha_Isc"],
            "noct": ["NOCT", "Nominal_Operating_Cell_Temperature"],
            "series_fuse": ["Series_Fuse", "Fuse_Rating"],
            "max_system_voltage": ["Max_System_Voltage", "Maximum_System_Voltage"],

            # Physical parameters
            "length": ["Length", "Module_Length", "L"],
            "width": ["Width", "Module_Width", "W"],
            "thickness": ["Thickness", "Module_Thickness", "T"],
            "weight": ["Weight", "Module_Weight"],
            "cells_series": ["Cells_in_Series", "Series_Cells", "Ns"],
            "cells_parallel": ["Cells_in_Parallel", "Parallel_Cells", "Np"],

            # Manufacturer info
            "manufacturer": ["Manufacturer", "Company", "Brand"],
            "model": ["Model", "Part_Number", "Product_Name"],
            "series": ["Series", "Product_Series"],
        }

    def load_registry(self) -> None:
        """Load the parsing registry from file."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.registry = {
                        path: ParsedFileRegistry(**entry)
                        for path, entry in data.items()
                    }
            except Exception as e:
                print(f"Warning: Could not load registry: {e}")
                self.registry = {}
        else:
            self.registry = {}

    def save_registry(self) -> None:
        """Save the parsing registry to file."""
        try:
            data = {
                str(path): entry.dict()
                for path, entry in self.registry.items()
            }
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save registry: {e}")

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception:
            return ""

    def scan_directory(self) -> List[Path]:
        """
        Scan the base directory for .PAN files.

        Returns:
            List of paths to .PAN files found
        """
        pan_files = []

        if not self.base_directory.exists():
            print(f"Warning: Base directory does not exist: {self.base_directory}")
            return pan_files

        # Search for .PAN files recursively
        for pattern in ["**/*.pan", "**/*.PAN"]:
            pan_files.extend(self.base_directory.glob(pattern))

        return sorted(set(pan_files))

    def extract_manufacturer_model_from_path(self, file_path: Path) -> Tuple[str, str]:
        """
        Extract manufacturer and model from file path structure.

        Expected structure: .../Manufacturer/Model/file.pan

        Args:
            file_path: Path to the .PAN file

        Returns:
            Tuple of (manufacturer, model)
        """
        try:
            # Get relative path from base directory
            relative_path = file_path.relative_to(self.base_directory)
            parts = relative_path.parts

            if len(parts) >= 3:
                # Structure: Manufacturer/Model/file.pan
                manufacturer = parts[0]
                model = parts[1]
            elif len(parts) >= 2:
                # Structure: Manufacturer/file.pan
                manufacturer = parts[0]
                model = file_path.stem  # Use filename without extension
            else:
                # Structure: file.pan
                manufacturer = "Unknown"
                model = file_path.stem

            return manufacturer, model

        except ValueError:
            # File is not under base directory
            return "Unknown", file_path.stem

    def get_new_files(self, all_files: List[Path]) -> List[Path]:
        """
        Get list of files that need to be processed (new or modified).

        Args:
            all_files: List of all .PAN files found

        Returns:
            List of files that need processing
        """
        new_files = []

        for file_path in all_files:
            file_str = str(file_path)

            try:
                # Get file stats
                stat = file_path.stat()
                current_size = stat.st_size
                current_modified = datetime.fromtimestamp(stat.st_mtime)
                current_hash = self.calculate_file_hash(file_path)

                # Check if file needs processing
                if file_str in self.registry:
                    registry_entry = self.registry[file_str]
                    if (registry_entry.file_hash == current_hash and
                        registry_entry.file_size == current_size and
                        registry_entry.success):
                        # File unchanged and previously processed successfully
                        continue

                new_files.append(file_path)

            except Exception as e:
                print(f"Warning: Could not check file {file_path}: {e}")
                new_files.append(file_path)  # Process it anyway

        return new_files

    def read_pan_file(self, file_path: Path) -> Optional[str]:
        """
        Read .PAN file content with multiple encoding attempts.

        Args:
            file_path: Path to the .PAN file

        Returns:
            File content as string, or None if reading failed
        """
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                break

        return None

    def parse_numeric_value(self, value_str: str) -> Optional[float]:
        """
        Parse numeric value from string, handling units and formatting.

        Args:
            value_str: String containing numeric value

        Returns:
            Parsed float value or None if parsing failed
        """
        if not value_str or value_str.strip() == "":
            return None

        # Clean the string
        cleaned = value_str.strip().replace(',', '.')

        # Remove common units and extra text
        units_to_remove = ['W', 'V', 'A', 'mm', 'kg', 'C', '%', '°C', 'Wp', 'x']
        for unit in units_to_remove:
            cleaned = cleaned.replace(unit, ' ')

        # Extract all numeric values using regex
        matches = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', cleaned)

        if matches:
            try:
                # For strings like "pvCommercial x 1.134 mm", we want the last numeric value
                # which is typically the actual measurement
                numeric_values = [float(match) for match in matches]

                # Filter out values that are clearly not measurements (like years, small decimals that might be coefficients)
                reasonable_values = [v for v in numeric_values if v > 0.1]

                if reasonable_values:
                    # Return the last reasonable value (typically the actual measurement)
                    return reasonable_values[-1]
                elif numeric_values:
                    # If no reasonable values, return the last numeric value
                    return numeric_values[-1]

            except ValueError:
                pass

        return None

    def extract_parameter_value(self, content: str, parameter_names: List[str]) -> Optional[Union[str, float]]:
        """
        Extract parameter value from .PAN file content.

        Args:
            content: .PAN file content
            parameter_names: List of possible parameter names to search for

        Returns:
            Extracted value or None if not found
        """
        for param_name in parameter_names:
            # Try different patterns
            patterns = [
                rf'{param_name}\s*=\s*([^\n\r]+)',
                rf'{param_name}\s*:\s*([^\n\r]+)',
                rf'{param_name}\s+([^\n\r]+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    value_str = match.group(1).strip()

                    # Try to parse as numeric first
                    numeric_value = self.parse_numeric_value(value_str)
                    if numeric_value is not None:
                        return numeric_value

                    # Return as string if not numeric
                    return value_str

        return None

    def parse_file(self, file_path: Path) -> ParsingResult:
        """
        Parse a single .PAN file.

        Args:
            file_path: Path to the .PAN file

        Returns:
            ParsingResult with parsed data or error information
        """
        try:
            # Read file content
            content = self.read_pan_file(file_path)
            if content is None:
                return ParsingResult(
                    success=False,
                    error_message="Could not read file with any encoding"
                )

            # Extract manufacturer and model from path
            manufacturer, model = self.extract_manufacturer_model_from_path(file_path)

            # Get file metadata
            stat = file_path.stat()
            file_hash = self.calculate_file_hash(file_path)

            # Extract parameters
            parameters_extracted = 0
            warnings = []

            # Electrical parameters
            electrical_params = ElectricalParameters()
            for param, names in self.parameter_mappings.items():
                if param.startswith(('pmax', 'vmp', 'imp', 'voc', 'isc', 'temp_coeff', 'noct', 'series_fuse', 'max_system')):
                    value = self.extract_parameter_value(content, names)
                    if value is not None:
                        setattr(electrical_params, param, value)
                        parameters_extracted += 1

            # Physical parameters
            physical_params = PhysicalParameters()
            for param, names in self.parameter_mappings.items():
                if param.startswith(('length', 'width', 'thickness', 'weight', 'cells')):
                    value = self.extract_parameter_value(content, names)
                    if value is not None:
                        if param == 'cells_series':
                            physical_params.cells_in_series = int(value) if isinstance(value, (int, float)) else None
                        elif param == 'cells_parallel':
                            physical_params.cells_in_parallel = int(value) if isinstance(value, (int, float)) else None
                        else:
                            # Ensure numeric values are properly converted to float
                            if isinstance(value, str):
                                numeric_value = self.parse_numeric_value(value)
                                if numeric_value is not None:
                                    setattr(physical_params, param, numeric_value)
                                else:
                                    warnings.append(f"Could not parse numeric value for {param}: '{value}'")
                            else:
                                setattr(physical_params, param, value)
                        parameters_extracted += 1

            # Calculate total cells if possible
            if physical_params.cells_in_series and physical_params.cells_in_parallel:
                physical_params.total_cells = physical_params.cells_in_series * physical_params.cells_in_parallel

            # Manufacturer info
            manufacturer_info = ManufacturerInfo(
                name=manufacturer,
                model=model
            )

            # Try to extract series from content
            series_value = self.extract_parameter_value(content, self.parameter_mappings.get('series', []))
            if series_value:
                manufacturer_info.series = str(series_value)

            # Certification info
            certification_info = CertificationInfo()

            # File metadata
            file_metadata = FileMetadata(
                file_path=file_path,
                file_name=file_path.name,
                file_size=stat.st_size,
                file_hash=file_hash,
                manufacturer_folder=manufacturer,
                model_folder=model
            )

            # Create PV module
            pv_module = PVModule(
                manufacturer_info=manufacturer_info,
                electrical_params=electrical_params,
                physical_params=physical_params,
                certification_info=certification_info,
                file_metadata=file_metadata,
                raw_pan_data={"content": content[:1000]}  # Store first 1000 chars for reference
            )

            # Update registry
            registry_entry = ParsedFileRegistry(
                file_path=file_path,
                file_hash=file_hash,
                file_size=stat.st_size,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                parsed_at=datetime.now(),
                parser_version="1.0.0",
                success=True
            )
            self.registry[str(file_path)] = registry_entry

            return ParsingResult(
                success=True,
                module=pv_module,
                parameters_extracted=parameters_extracted,
                parameters_missing=len(self.parameter_mappings) - parameters_extracted,
                warnings=warnings
            )

        except Exception as e:
            # Update registry with error
            registry_entry = ParsedFileRegistry(
                file_path=file_path,
                file_hash=self.calculate_file_hash(file_path),
                file_size=file_path.stat().st_size if file_path.exists() else 0,
                last_modified=datetime.fromtimestamp(file_path.stat().st_mtime) if file_path.exists() else datetime.now(),
                parsed_at=datetime.now(),
                parser_version="1.0.0",
                success=False,
                error_message=str(e)
            )
            self.registry[str(file_path)] = registry_entry

            return ParsingResult(
                success=False,
                error_message=str(e)
            )

    def parse_directory(self, max_files: Optional[int] = None) -> Dict[str, ParsingResult]:
        """
        Parse all .PAN files in the directory.

        Args:
            max_files: Maximum number of files to process (for testing)

        Returns:
            Dictionary mapping file paths to parsing results
        """
        all_files = self.scan_directory()
        new_files = self.get_new_files(all_files)

        if max_files:
            new_files = new_files[:max_files]

        results = {}

        print(f"Found {len(all_files)} total .PAN files")
        print(f"Processing {len(new_files)} new/modified files")

        for i, file_path in enumerate(new_files, 1):
            print(f"Processing {i}/{len(new_files)}: {file_path.name}")
            result = self.parse_file(file_path)
            results[str(file_path)] = result

            if i % 10 == 0:  # Save registry every 10 files
                self.save_registry()

        # Save final registry
        self.save_registry()

        return results

    def get_statistics(self, results: Dict[str, ParsingResult]) -> Dict[str, Union[int, float]]:
        """
        Get parsing statistics.

        Args:
            results: Dictionary of parsing results

        Returns:
            Dictionary with statistics
        """
        total_files = len(results)
        successful = sum(1 for r in results.values() if r.success)
        failed = total_files - successful

        if successful > 0:
            avg_parameters = sum(r.parameters_extracted for r in results.values() if r.success) / successful
        else:
            avg_parameters = 0

        return {
            "total_files": total_files,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_files * 100) if total_files > 0 else 0,
            "avg_parameters_extracted": avg_parameters
        }
