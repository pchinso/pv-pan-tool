# PV PAN Tool Documentation

A comprehensive command-line tool for parsing, analyzing, and comparing photovoltaic (PV) module specifications from .PAN files.

## Overview

The PV PAN Tool provides a complete solution for working with PV module data:

- **Parse**: Process .PAN files and extract specifications into a structured database
- **Search**: Query modules by various criteria like manufacturer, power, efficiency
- **Compare**: Side-by-side comparison of multiple modules
- **Export**: Output data in CSV, JSON, or Excel formats
- **Statistics**: Analyze market trends and manufacturer data
- **Database Management**: Backup, restore, and maintain your module database

## Quick Start

```bash
# Parse .PAN files from a directory
pv-pan-tool parse --input-dir "C:\path\to\pan\files"

# Search for high-power modules
pv-pan-tool search --manufacturer "Jinko" --power-min 500

# Compare top 5 modules by power
pv-pan-tool compare --top-power 5

# Export search results to CSV
pv-pan-tool export --format csv --output modules.csv
```

## Installation

1. Clone the repository
2. Install dependencies with Poetry:
   ```bash
   poetry install
   ```
3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

## Usage

The tool provides several commands, each with comprehensive options:

- [parse](commands/parse.md) - Parse .PAN files into database
- [search](commands/search.md) - Search and filter modules
- [compare](commands/compare.md) - Compare multiple modules side-by-side
- [export](commands/export.md) - Export data to various formats
- [stats](commands/stats.md) - View database statistics and analysis
- [database](commands/database.md) - Database management operations
- [info](commands/info.md) - System information and overview

## Examples

### Basic Workflow

1. **Import Data**: Start by parsing your .PAN files
   ```bash
   pv-pan-tool parse --input-dir "data/pan_files" --recursive
   ```

2. **Search Modules**: Find modules matching your criteria
   ```bash
   pv-pan-tool search --manufacturer "Jinko" --power-min 600 --efficiency-min 21.5
   ```

3. **Compare Options**: Compare your shortlisted modules
   ```bash
   pv-pan-tool compare --ids 1,5,12 --format table
   ```

4. **Export Results**: Save your analysis
   ```bash
   pv-pan-tool export --manufacturer "Jinko,Longi" --format csv --output comparison.csv
   ```

### Advanced Usage

**Find the most efficient modules by manufacturer:**
```bash
pv-pan-tool stats --by-manufacturer --sort-by efficiency
```

**Compare modules in specific power and efficiency ranges:**
```bash
pv-pan-tool compare --power-range 650-700 --efficiency-range 22-23 --limit 5
```

**Export all monocrystalline modules with detailed specifications:**
```bash
pv-pan-tool export --cell-type monocrystalline --format json --include-details --output mono_modules.json
```

## Configuration

The tool can be configured via:
- Command-line options
- Configuration file (config.yaml)
- Environment variables

See [configuration.md](configuration.md) for detailed setup options.

## Data Sources

The tool processes industry-standard .PAN files used in PV system design software like PVsyst, SAM, and others. These files contain detailed electrical and mechanical specifications for PV modules.

## Support

For issues, feature requests, or contributions, please refer to the project repository.
