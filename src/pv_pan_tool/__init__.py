"""
PV PAN Tool - A comprehensive tool for parsing and comparing photovoltaic module specifications.

This package provides functionality to:
- Parse .PAN files from specified directories
- Extract technical parameters and specifications
- Build and maintain a searchable database
- Compare modules and manufacturers
- Export comparison reports
- Command-line interface for easy automation
"""

__version__ = "0.1.0"
__author__ = "PV PAN Tool Team"
__email__ = "chinso@gmail.com"

from .database import PVModuleDatabase
from .models import ElectricalParameters, ManufacturerInfo, PhysicalParameters, PVModule
from .parser import PANFileParser

__all__ = [
    "PVModule",
    "ElectricalParameters",
    "PhysicalParameters",
    "ManufacturerInfo",
    "PANFileParser",
    "PVModuleDatabase",
]
