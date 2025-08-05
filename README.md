# PV PAN Tool

A comprehensive tool for parsing and comparing photovoltaic module specifications from .PAN files.

## Features

- Parse .PAN files from specified directories
- Extract technical parameters and specifications
- Build and maintain a searchable database
- Compare modules and manufacturers
- Export comparison reports
- Command-line interface for easy automation

## Installation

### Prerequisites
- Python 3.11 or higher
- Git

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd pv-pan-tool

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

## Usage

### Basic Commands
```bash
# Show help
pv-pan-tool --help

# Parse PAN files from directory
pv-pan-tool parse --input-dir "C:\path\to\pan\files"

# Compare modules
pv-pan-tool compare --manufacturer "SunPower" --model "SPR-X21-345"

# Export database to CSV
pv-pan-tool export --format csv --output "modules.csv"
```

## Development

### Running Tests
```bash
poetry run pytest
poetry run pytest --cov
```

### Code Quality
```bash
# Format code
poetry run black .
poetry run isort .

# Linting
poetry run flake8 src/ tests/

# Type checking
poetry run mypy src/
```

## License

MIT License - see LICENSE file for details.