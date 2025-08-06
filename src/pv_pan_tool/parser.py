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
from typing import Any, Dict, List, Optional, Tuple, Union

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
    """
    Parser .PAN files containing photovoltaic module specifications.

    This class provides functionality to:
    - Scan directories for .PAN files
    - Track processed files using a registry system
    - Parse .PAN files into structured PVModule objects
    - Handle file encodings and hierarchical .PAN structures
    - Convert units and map fields to standardized models

    The parser follows PV*SOL's standardized .PAN format, which uses:
    - Hierarchical objects (PVObject_ blocks)
    - Key-value pairs for specifications
    - Structured objects for IAM profiles and commercial data

    Features:
    - Automatic detection of new/changed files
    - Unit conversion (meters to mm, mV/°C to %/°C)
    - Technology string to CellType enum mapping
    - IAM profile extraction
    - Temperature coefficient conversion

    Registry System:
    - Tracks processed files to avoid reprocessing
    - Uses SHA-256 hashes to detect changes
    - Stores parsing status and errors

    Example Usage:
    ```python
    from pv_pan_tool.parser import PANFileParser

    # Initialize parser with data directory
    parser = PANFileParser(base_directory="path/to/pan_files")

    # Parse all new/changed files
    results = parser.parse_directory()

    # Access parsing results
    for file_path, result in results.items():
        if result.success:
            module = result.module
            print(f"Parsed: {module.manufacturer_info.name} {module.manufacturer_info.model}")
            print(f"Power: {module.electrical_params.pmax_stc}W")
            print(f"Dimensions: {module.physical_params.width}x{module.physical_params.height}mm")
        else:
            print(f"Failed to parse {file_path}: {result.error_message}")

    # Get statistics
    stats = parser.get_statistics(results)
    print(f"Success rate: {stats['success_rate']:.1f}%")
    ```

    File Structure Example:
    ```
    project_root/
    ├── Manufacturer_A/
    │   ├── Model_X/
    │   │   ├── spec.pan
    │   │   └── variant.pan
    │   └── Model_Y/
    │       └── data.pan
    └── Manufacturer_B/
        └── Model_Z.pan
    """
    FIELD_MAPPING = {
        # Commercial info
        'Manufacturer': ('manufacturer_info', 'name'),
        'Model': ('manufacturer_info', 'model'),
        'DataSource': ('manufacturer_info', 'data_source'),
        'YearBeg': ('manufacturer_info', 'year'),
        'Width': ('physical_params', 'width'),
        'Height': ('physical_params', 'height'),
        'Depth': ('physical_params', 'thickness'),
        'Weight': ('physical_params', 'weight'),

        # Electrical parameters
        'NCelS': ('physical_params', 'cells_in_series'),
        'NCelP': ('physical_params', 'cells_in_parallel'),
        'NDiode': ('electrical_params', 'bypass_diodes'),
        'GRef': ('electrical_params', 'g_ref'),
        'TRef': ('electrical_params', 't_ref'),
        'PNom': ('electrical_params', 'pmax_stc'),
        'Isc': ('electrical_params', 'isc_stc'),
        'Voc': ('electrical_params', 'voc_stc'),
        'Imp': ('electrical_params', 'imp_stc'),
        'Vmp': ('electrical_params', 'vmp_stc'),
        'muISC': ('electrical_params', 'temp_coeff_isc'),
        'muVocSpec': ('electrical_params', 'temp_coeff_voc'),
        'muPmpReq': ('electrical_params', 'temp_coeff_pmax'),
        'BifacialityFactor': ('electrical_params', 'bifaciality_factor'),
        'RShunt': ('electrical_params', 'r_shunt'),
        'RSerie': ('electrical_params', 'r_series'),
        'VMaxIEC': ('electrical_params', 'max_system_voltage'),
    }

    # Unit conversions for consistent storage
    UNIT_CONVERSIONS = {
        'width': 1000,        # m to mm
        'height': 1000,       # m to mm
        'thickness': 1000,    # m to mm
        'temp_coeff_voc': 0.1,  # mV/°C to %/°C
    }

    def __init__(self, base_directory: str, registry_file: str = "parsed_files_registry.json"):
        self.base_directory = Path(base_directory)
        self.registry_file = Path(registry_file)
        self.registry: Dict[str, ParsedFileRegistry] = {}
        self.load_registry()

    def load_registry(self) -> None:
        """Load the parsed files registry from disk, if it exists."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.registry = {
                        k: ParsedFileRegistry(**v) for k, v in data.items()
                    }
            except Exception as e:
                print(f"Failed to load registry: {e}")
                self.registry = {}
        else:
            self.registry = {}

    def save_registry(self) -> None:
        """Save the parsing registry to file."""
        try:
            data = {
                str(k): v.dict() for k, v in self.registry.items()
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
        """Read .PAN file content with multiple encoding attempts."""
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

    def parse_pan_structure(self, content: str) -> Dict[str, Any]:
        """Parse .pan file content into a structured dictionary."""
        result = {}
        stack = []
        current = result
        lines = content.splitlines()

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Handle object blocks
            if stripped.startswith("PVObject_"):
                parts = stripped.split('=', 1)
                if len(parts) < 2:
                    continue

                obj_name = parts[0][9:]  # Remove "PVObject_" prefix
                obj_type = parts[1]

                new_obj = {"__type__": obj_type}
                current[obj_name] = new_obj
                stack.append(current)
                current = new_obj

            elif stripped.startswith("End of PVObject"):
                if stack:
                    current = stack.pop()

            # Handle key-value pairs
            elif '=' in stripped:
                key, value = [part.strip() for part in stripped.split('=', 1)]

                # Handle comma-separated values (like IAM points)
                if ',' in value:
                    current[key] = [v.strip() for v in value.split(',')]
                else:
                    current[key] = value

        return result

    def parse_numeric_value(self, value: Union[str, List[str]]) -> Optional[float]:
        """Parse numeric value from string or list."""
        try:
            if isinstance(value, list) and value:
                return float(value[0].replace(',', '.'))
            elif isinstance(value, str):
                return float(value.replace(',', '.'))
        except (ValueError, TypeError):
            return None
        return None

    def map_pan_data(self, pan_data: Dict, manufacturer: str, model: str, file_metadata: FileMetadata) -> PVModule:
        """Map parsed .pan data to PVModule object."""
        # Initialize objects
        manufacturer_info = ManufacturerInfo(name=manufacturer, model=model)
        physical_params = PhysicalParameters()
        electrical_params = ElectricalParameters()
        certification_info = CertificationInfo()

        # Extract root object if exists
        if "" in pan_data:
            pan_data = pan_data[""]  # Extract root pvModule object

        # Extract commercial info and root level parameters
        commercial = pan_data.get("Commercial", {})

        # Process both commercial section and root level fields
        data_sources = [commercial, pan_data]
        for data_source in data_sources:
            for pan_field, (obj_name, attr_name) in self.FIELD_MAPPING.items():
                if pan_field in data_source:
                    value = data_source[pan_field]
                    # Determine target object
                    target = None
                    if obj_name == 'manufacturer_info':
                        target = manufacturer_info
                    elif obj_name == 'physical_params':
                        target = physical_params
                    elif obj_name == 'electrical_params':
                        target = electrical_params

                    if target:
                        num_value = self.parse_numeric_value(value)
                        if num_value is not None:
                            # Apply unit conversions
                            if attr_name in self.UNIT_CONVERSIONS:
                                num_value *= self.UNIT_CONVERSIONS[attr_name]
                            setattr(target, attr_name, num_value)
                        else:
                            setattr(target, attr_name, value)

        # Extract IAM profile
        iam = pan_data.get("IAM", {})
        for i in range(1, 10):
            point_key = f"Point_{i}"
            if point_key in iam:
                try:
                    # Extract IAM value (second value in comma-separated pair)
                    point_value = iam[point_key]
                    if isinstance(point_value, list):
                        # Handle list format: [angle, iam_value]
                        iam_value = float(point_value[1].strip())
                    elif isinstance(point_value, str):
                        # Handle string format: "angle, iam_value"
                        iam_value = float(point_value.split(',')[1].strip())
                    else:
                        continue
                    setattr(electrical_params, f"iam_{5*(i-1)}", iam_value)
                except (IndexError, ValueError, TypeError):
                    continue

        # Handle cell technology mapping
        tech_map = {
            "mtSiMono": CellType.MONOCRYSTALLINE,
            "mtSiPoly": CellType.POLYCRYSTALLINE,
            "mtCIS": CellType.CIGS,
            "mtCdTe": CellType.CDTE,
        }
        tech_str = pan_data.get("Technol", "")
        cell_type = tech_map.get(tech_str, CellType.UNKNOWN)

        # Handle temperature coefficient units conversion
        if electrical_params.temp_coeff_voc and electrical_params.voc_stc:
            # Convert mV/°C to %/°C
            electrical_params.temp_coeff_voc = (
                electrical_params.temp_coeff_voc * 0.1 /
                electrical_params.voc_stc
            )

        # Create PV module
        return PVModule(
            manufacturer_info=manufacturer_info,
            electrical_params=electrical_params,
            physical_params=physical_params,
            certification_info=certification_info,
            file_metadata=file_metadata,
            cell_type=cell_type,
            technology=tech_str,
            raw_data=pan_data  # Store raw parsed structure
        )

    def create_file_metadata(self, file_path: Path, manufacturer: str, model: str) -> FileMetadata:
        """Create file metadata object."""
        stat = file_path.stat()
        return FileMetadata(
            file_path=file_path,
            file_name=file_path.name,
            file_size=stat.st_size,
            file_hash=self.calculate_file_hash(file_path),
            last_modified=datetime.fromtimestamp(stat.st_mtime),
            parsed_at=datetime.now(),
            manufacturer_folder=manufacturer,
            model_folder=model
        )

    def update_registry(self, file_path: Path, success: bool, error: str = "") -> None:
        """Update parsing registry."""
        stat = file_path.stat()
        self.registry[str(file_path)] = ParsedFileRegistry(
            file_path=file_path,
            file_hash=self.calculate_file_hash(file_path),
            file_size=stat.st_size,
            last_modified=datetime.fromtimestamp(stat.st_mtime),
            parsed_at=datetime.now(),
            parser_version="1.0.0",
            success=success,
            error_message=error
        )

    def parse_file(self, file_path: Path) -> ParsingResult:
        try:
            # 1. Read file content
            content = self.read_pan_file(file_path)
            if content is None:
                return ParsingResult(
                    success=False,
                    error_message="Could not read file with any encoding"
                )

            # 2. Parse file structure
            pan_data = self.parse_pan_structure(content)
            if not pan_data:
                return ParsingResult(
                    success=False,
                    error_message="Failed to parse file structure"
                )

            # 3. Extract manufacturer/model from path
            manufacturer, model = self.extract_manufacturer_model_from_path(file_path)

            # 4. Create file metadata
            file_metadata = self.create_file_metadata(file_path, manufacturer, model)

            # 5. Map to PVModule object
            pv_module = self.map_pan_data(pan_data, manufacturer, model, file_metadata)

            # 6. Update registry
            self.update_registry(file_path, True)

            # 7. Return successful result
            return ParsingResult(
                success=True,
                module=pv_module,
                parameters_extracted=len([v for v in pv_module.dict().values() if v is not None]),
                warnings=[]  # We could add warning collection later
            )

        except Exception as e:
            self.update_registry(file_path, False, str(e))
            return ParsingResult(
                success=False,
                error_message=str(e)
            )

    def parse_directory(self, max_files: Optional[int] = None) -> Dict[str, ParsingResult]:
        """
        Parse all .PAN files in the directory.
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