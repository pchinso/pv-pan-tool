"""Data models for PV module specifications using Pydantic."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, model_validator, validator


class CellType(str, Enum):
    """Enumeration of solar cell types."""
    MONOCRYSTALLINE = "monocrystalline"
    POLYCRYSTALLINE = "polycrystalline"
    THIN_FILM = "thin_film"
    CIS = "cis"  # Copper indium selenide
    CIGS = "cigs"  # Copper indium gallium selenide
    CDTE = "cdte"  # Cadmium telluride
    PERC = "perc"
    BIFACIAL = "bifacial"
    HJT = "hjt"  # Heterojunction
    IBC = "ibc"  # Interdigitated back contact
    UNKNOWN = "unknown"


class ModuleType(str, Enum):
    """Enumeration of module types."""
    STANDARD = "standard"
    BIFACIAL = "bifacial"
    GLASS_GLASS = "glass_glass"
    FLEXIBLE = "flexible"
    BUILDING_INTEGRATED = "bipv"
    UNKNOWN = "unknown"


class ElectricalParameters(BaseModel):
    """Electrical parameters of a PV module."""

    # Standard test conditions (STC)
    pmax_stc: Optional[float] = Field(None, description="Maximum power at STC (W)")
    vmp_stc: Optional[float] = Field(None, description="Voltage at maximum power at STC (V)")
    imp_stc: Optional[float] = Field(None, description="Current at maximum power at STC (A)")
    voc_stc: Optional[float] = Field(None, description="Open circuit voltage at STC (V)")
    isc_stc: Optional[float] = Field(None, description="Short circuit current at STC (A)")

    # Temperature coefficients (%/°C)
    temp_coeff_pmax: Optional[float] = Field(None, description="Temperature coefficient of Pmax")
    temp_coeff_voc: Optional[float] = Field(None, description="Temperature coefficient of Voc")
    temp_coeff_isc: Optional[float] = Field(None, description="Temperature coefficient of Isc")

    # Reference conditions
    g_ref: Optional[float] = Field(1000.0, description="Reference irradiance (W/m²)")
    t_ref: Optional[float] = Field(25.0, description="Reference temperature (°C)")

    # Module configuration
    noct: Optional[float] = Field(None, description="Nominal Operating Cell Temperature (°C)")
    bypass_diodes: Optional[int] = Field(None, description="Number of bypass diodes")
    max_system_voltage: Optional[float] = Field(None, description="Maximum system voltage (V)")

    # Resistance parameters
    r_series: Optional[float] = Field(None, description="Series resistance (Ω)")
    r_shunt: Optional[float] = Field(None, description="Shunt resistance (Ω)")

    # Bifacial properties
    bifaciality_factor: Optional[float] = Field(None, description="Bifaciality factor (0-1)")

    # Incidence Angle Modifier (IAM) profile
    iam_0: Optional[float] = Field(None, description="IAM at 0° incidence")
    iam_30: Optional[float] = Field(None, description="IAM at 30° incidence")
    iam_45: Optional[float] = Field(None, description="IAM at 45° incidence")
    iam_60: Optional[float] = Field(None, description="IAM at 60° incidence")
    iam_70: Optional[float] = Field(None, description="IAM at 70° incidence")
    iam_75: Optional[float] = Field(None, description="IAM at 75° incidence")
    iam_80: Optional[float] = Field(None, description="IAM at 80° incidence")
    iam_85: Optional[float] = Field(None, description="IAM at 85° incidence")
    iam_90: Optional[float] = Field(None, description="IAM at 90° incidence")

    # Validators
    @validator('pmax_stc', 'vmp_stc', 'imp_stc', 'voc_stc', 'isc_stc',
               'r_series', 'r_shunt', 'max_system_voltage')
    def validate_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Value must be positive')
        return v

    @validator('bifaciality_factor')
    def validate_bifacial_range(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Bifaciality factor must be between 0 and 1')
        return v

    @validator('iam_0', 'iam_30', 'iam_45', 'iam_60', 'iam_70', 'iam_75', 'iam_80', 'iam_85', 'iam_90')
    def validate_iam_range(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('IAM values must be between 0 and 1')
        return v


class PhysicalParameters(BaseModel):
    """Physical parameters of a PV module.

    Note: 'height' corresponds to the vertical dimension when mounted,
           while 'width' is the horizontal dimension.
    """

    # Renamed fields to match parser output
    width: Optional[float] = Field(None, description="Module width (mm)")
    height: Optional[float] = Field(None, description="Module height (mm)")
    thickness: Optional[float] = Field(None, description="Module thickness (mm)")
    weight: Optional[float] = Field(None, description="Module weight (kg)")
    area: Optional[float] = Field(None, description="Front surface area (m²)")

    cells_in_series: Optional[int] = Field(None, description="Number of cells in series")
    cells_in_parallel: Optional[int] = Field(None, description="Number of cells in parallel")
    total_cells: Optional[int] = Field(None, description="Total number of cells")
    cell_area: Optional[float] = Field(None, description="Area of a single cell (cm²)")

    # Validators
    @validator('width', 'height', 'thickness', 'weight', 'cell_area', 'area')
    def validate_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Physical parameters must be positive')
        return v

    @model_validator(mode='after')
    def calculate_derived_fields(self):
        # Calculate total cells if possible
        if self.cells_in_series is not None and self.cells_in_parallel is not None:
            self.total_cells = self.cells_in_series * self.cells_in_parallel

        # Calculate area if possible
        if self.width is not None and self.height is not None:
            # Convert mm to m²
            self.area = (self.width / 1000) * (self.height / 1000)

        return self


class CertificationInfo(BaseModel):
    """Certification and compliance information."""

    iec_61215: Optional[bool] = Field(None, description="IEC 61215 certified")
    iec_61730: Optional[bool] = Field(None, description="IEC 61730 certified")
    ul_listed: Optional[bool] = Field(None, description="UL listed")
    ce_marking: Optional[bool] = Field(None, description="CE marking")
    sandia_certified: Optional[bool] = Field(None, description="Sandia certified")

    certifications: List[str] = Field(default_factory=list, description="Additional certifications")


class ManufacturerInfo(BaseModel):
    """Manufacturer information."""

    name: str = Field(..., description="Manufacturer name")
    model: str = Field(..., description="Model name/number")
    series: Optional[str] = Field(None, description="Product series")
    data_source: Optional[str] = Field(None, description="Data source specification")
    year: Optional[int] = Field(None, description="Year of product introduction")
    country_of_origin: Optional[str] = Field(None, description="Country of manufacture")


class FileMetadata(BaseModel):
    """Metadata about the .PAN file."""

    file_path: Path = Field(..., description="Full path to the .PAN file")
    file_name: str = Field(..., description="Name of the .PAN file")
    file_size: int = Field(..., description="File size in bytes")
    file_hash: str = Field(..., description="SHA-256 hash of the file content")
    last_modified: datetime = Field(..., description="Last modification timestamp")
    parsed_at: datetime = Field(default_factory=datetime.now, description="When the file was parsed")

    manufacturer_folder: Optional[str] = Field(None, description="Manufacturer folder name")
    model_folder: Optional[str] = Field(None, description="Model folder name")


class PVModule(BaseModel):
    """Complete PV module specification."""

    manufacturer_info: ManufacturerInfo
    electrical_params: ElectricalParameters
    physical_params: PhysicalParameters
    certification_info: CertificationInfo = Field(default_factory=CertificationInfo)
    file_metadata: FileMetadata

    # Technical specifications
    cell_type: CellType = Field(CellType.UNKNOWN, description="Solar cell technology")
    module_type: ModuleType = Field(ModuleType.STANDARD, description="Module construction type")
    technology: Optional[str] = Field(None, description="Raw technology string from .pan file")

    # Additional metadata
    notes: Optional[str] = Field(None, description="Additional notes")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Raw parsed data")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Path: lambda v: str(v)
        }

    @property
    def unique_id(self) -> str:
        """Generate a unique identifier for this module."""
        return f"{self.manufacturer_info.name}_{self.manufacturer_info.model}_{self.file_metadata.file_hash[:8]}"

    @property
    def efficiency_stc(self) -> Optional[float]:
        """Calculate module efficiency at STC."""
        pmax = self.electrical_params.pmax_stc
        area = self.physical_params.area

        if pmax and area:
            return (pmax / (area * 1000)) * 100  # Convert to percentage
        return None

    @model_validator(mode='after')
    def set_module_type_based_on_properties(self):
        """Set module type based on bifaciality and other properties."""
        if (self.electrical_params.bifaciality_factor and
            self.electrical_params.bifaciality_factor > 0):
            self.module_type = ModuleType.BIFACIAL
        return self


class ParsedFileRegistry(BaseModel):
    """Registry of parsed .PAN files to track processing status."""

    file_path: Path
    file_hash: str
    file_size: int
    last_modified: datetime
    parsed_at: datetime
    parser_version: str = Field("1.0.0", description="Parser version used")
    success: bool
    error_message: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Path: lambda v: str(v)
        }


class ParsingResult(BaseModel):
    """Result of parsing operation."""

    success: bool
    module: Optional[PVModule] = None
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    parameters_extracted: int = 0
    parameters_missing: int = 0

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Path: lambda v: str(v)
        }