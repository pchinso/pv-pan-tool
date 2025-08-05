"""Data models for PV module specifications using Pydantic."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, validator


class CellType(str, Enum):
    """Enumeration of solar cell types."""
    MONOCRYSTALLINE = "monocrystalline"
    POLYCRYSTALLINE = "polycrystalline"
    THIN_FILM = "thin_film"
    PERC = "perc"
    BIFACIAL = "bifacial"
    HJT = "hjt"
    IBC = "ibc"
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
    
    pmax_stc: Optional[float] = Field(None, description="Maximum power at STC (W)")
    vmp_stc: Optional[float] = Field(None, description="Voltage at maximum power at STC (V)")
    imp_stc: Optional[float] = Field(None, description="Current at maximum power at STC (A)")
    voc_stc: Optional[float] = Field(None, description="Open circuit voltage at STC (V)")
    isc_stc: Optional[float] = Field(None, description="Short circuit current at STC (A)")
    
    temp_coeff_pmax: Optional[float] = Field(None, description="Temperature coefficient of Pmax")
    temp_coeff_voc: Optional[float] = Field(None, description="Temperature coefficient of Voc")
    temp_coeff_isc: Optional[float] = Field(None, description="Temperature coefficient of Isc")
    
    noct: Optional[float] = Field(None, description="Nominal Operating Cell Temperature")
    series_fuse_rating: Optional[float] = Field(None, description="Series fuse rating (A)")
    max_system_voltage: Optional[float] = Field(None, description="Maximum system voltage (V)")
    
    @validator('pmax_stc')
    def validate_power(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Power must be positive')
        return v


class PhysicalParameters(BaseModel):
    """Physical parameters of a PV module."""
    
    length: Optional[float] = Field(None, description="Module length (mm)")
    width: Optional[float] = Field(None, description="Module width (mm)")
    thickness: Optional[float] = Field(None, description="Module thickness (mm)")
    weight: Optional[float] = Field(None, description="Module weight (kg)")
    
    cells_in_series: Optional[int] = Field(None, description="Number of cells in series")
    cells_in_parallel: Optional[int] = Field(None, description="Number of cells in parallel")
    total_cells: Optional[int] = Field(None, description="Total number of cells")
    
    @validator('length', 'width', 'thickness', 'weight')
    def validate_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Physical parameters must be positive')
        return v


class CertificationInfo(BaseModel):
    """Certification and compliance information."""
    
    iec_61215: Optional[bool] = Field(None, description="IEC 61215 certified")
    iec_61730: Optional[bool] = Field(None, description="IEC 61730 certified")
    ul_listed: Optional[bool] = Field(None, description="UL listed")
    ce_marking: Optional[bool] = Field(None, description="CE marking")
    
    certifications: Optional[List[str]] = Field(default_factory=list, description="Additional certifications")


class ManufacturerInfo(BaseModel):
    """Manufacturer information."""
    
    name: str = Field(..., description="Manufacturer name")
    model: str = Field(..., description="Model name/number")
    series: Optional[str] = Field(None, description="Product series")
    
    manufacturing_date: Optional[datetime] = Field(None, description="Manufacturing date")
    country_of_origin: Optional[str] = Field(None, description="Country of manufacture")


class FileMetadata(BaseModel):
    """Metadata about the .PAN file."""
    
    file_path: Path = Field(..., description="Full path to the .PAN file")
    file_name: str = Field(..., description="Name of the .PAN file")
    file_size: int = Field(..., description="File size in bytes")
    file_hash: str = Field(..., description="SHA-256 hash of the file content")
    
    parsed_at: datetime = Field(default_factory=datetime.now, description="When the file was parsed")
    parser_version: str = Field(default="1.0.0", description="Version of the parser used")
    
    manufacturer_folder: Optional[str] = Field(None, description="Manufacturer folder name")
    model_folder: Optional[str] = Field(None, description="Model folder name")


class PVModule(BaseModel):
    """Complete PV module specification."""
    
    manufacturer_info: ManufacturerInfo
    electrical_params: ElectricalParameters
    physical_params: PhysicalParameters
    cell_type: CellType = CellType.UNKNOWN
    module_type: ModuleType = ModuleType.STANDARD
    certification_info: CertificationInfo
    file_metadata: FileMetadata
    raw_pan_data: Dict[str, Union[str, float, int]] = Field(default_factory=dict)
    notes: Optional[str] = Field(None, description="Additional notes")
    
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
        if (self.electrical_params.pmax_stc and 
            self.physical_params.length and 
            self.physical_params.width):
            
            area_m2 = (self.physical_params.length * self.physical_params.width) / 1_000_000
            return (self.electrical_params.pmax_stc / (area_m2 * 1000)) * 100
        return None


class ParsedFileRegistry(BaseModel):
    """Registry of parsed .PAN files to track processing status."""
    
    file_path: Path
    file_hash: str
    file_size: int
    last_modified: datetime
    parsed_at: datetime
    parser_version: str
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