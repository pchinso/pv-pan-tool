# Export Command

The `export` command allows you to export PV module data from the database to various file formats for further analysis, reporting, or integration with other tools.

## Usage

```bash
pv-pan-tool export [OPTIONS]
```

## Options

| Option | Type | Description |
|--------|------|-------------|
| `-m, --manufacturer` | TEXT | Filter by manufacturer name |
| `-M, --model` | TEXT | Filter by model name |
| `-p, --power-min` | FLOAT | Minimum power rating in watts |
| `-P, --power-max` | FLOAT | Maximum power rating in watts |
| `-e, --efficiency-min` | FLOAT | Minimum efficiency percentage |
| `-E, --efficiency-max` | FLOAT | Maximum efficiency percentage |
| `-c, --cell-type` | CHOICE | Filter by cell type |
| `-f, --format` | CHOICE | Output format: csv, json, excel |
| `-o, --output` | PATH | Output file path (required) |
| `--include-details` | FLAG | Include detailed technical specifications |
| `-l, --limit` | INTEGER | Maximum number of records to export |
| `-s, --sort-by` | CHOICE | Sort exported data by parameter |

## Export Formats

### CSV Format
Comma-separated values for spreadsheet applications:

**Basic Export:**
```bash
pv-pan-tool export --format csv --output modules.csv
```

**Filtered Export:**
```bash
pv-pan-tool export --manufacturer "Jinko" --power-min 500 --format csv --output jinko_500w.csv
```

### JSON Format  
Structured data for programming and API integration:

```bash
pv-pan-tool export --format json --output modules.json --include-details
```

### Excel Format
Native Excel files with formatting:

```bash
pv-pan-tool export --format excel --output modules.xlsx --include-details
```

## Data Fields

### Standard Export Fields
All export formats include these core fields:
- Module ID and unique identifier
- Manufacturer and model information  
- Electrical specifications (power, efficiency, voltage, current)
- Physical dimensions and weight
- Cell type and configuration
- Module type and technology

### Detailed Export Fields (--include-details)
Additional technical specifications:
- Temperature coefficients
- Operating conditions and ratings  
- Mechanical load specifications
- Certification standards
- Manufacturing details
- Performance guarantees

## Use Case Examples

### Project Documentation
Export modules for project specifications:
```bash
pv-pan-tool export --power-range 400-500 --efficiency-min 20 --format excel --output residential_options.xlsx
```

### Market Analysis
Export data for market research:
```bash
pv-pan-tool export --format json --include-details --output market_data.json
```

### Supplier Comparison  
Export by manufacturer for procurement analysis:
```bash
pv-pan-tool export --manufacturer "Jinko,Longi,Trina" --format csv --output supplier_comparison.csv
```

### Technical Documentation
Detailed specifications for engineering:
```bash
pv-pan-tool export --cell-type monocrystalline --include-details --format excel --output mono_specs.xlsx
```

## Integration Examples

### Spreadsheet Analysis
CSV and Excel exports can be directly imported into:
- Microsoft Excel
- Google Sheets  
- LibreOffice Calc
- Financial modeling tools

### Programming Integration
JSON exports work seamlessly with:
- Python pandas DataFrames
- R data analysis
- Database imports
- Web applications
- API endpoints

### Reporting Systems
Exported data can feed into:
- Business intelligence tools
- Automated report generation
- Project management systems
- Customer proposals
