# Compare Command

The `compare` command performs side-by-side comparisons of multiple PV modules, displaying their specifications in an organized table format.

## Usage

```bash
pv-pan-tool compare [OPTIONS]
```

## Options

| Option | Type | Description |
|--------|------|-------------|
| `-i, --ids` | TEXT | Comma-separated list of module IDs to compare |
| `-m, --manufacturer` | TEXT | Compare modules from specific manufacturers |
| `-M, --model` | TEXT | Compare specific models (comma-separated) |
| `-p, --top-power` | INTEGER | Compare top N modules by power rating |
| `-e, --top-efficiency` | INTEGER | Compare top N modules by efficiency |
| `-P, --power-range` | TEXT | Compare modules in power range (format: min-max) |
| `-E, --efficiency-range` | TEXT | Compare modules in efficiency range (format: min-max) |
| `-c, --cell-type` | CHOICE | Filter by cell type |
| `-l, --limit` | INTEGER | Maximum number of modules to compare |
| `-f, --format` | CHOICE | Output format: table, json, csv |
| `-o, --output` | PATH | Save comparison to file |
| `-s, --sort-by` | CHOICE | Sort modules by parameter |

## Selection Methods

### By Module IDs
Compare specific modules by database ID:
```bash
pv-pan-tool compare --ids 1,5,12,25
```

### By Top Performance
Compare highest performing modules:
```bash
# Top 5 by power rating
pv-pan-tool compare --top-power 5

# Top 3 by efficiency
pv-pan-tool compare --top-efficiency 3
```

### By Manufacturer
Compare modules from specific manufacturers:
```bash
pv-pan-tool compare --manufacturer "Jinko,Longi,Trina" --limit 6
```

### By Ranges
Compare modules within specific parameter ranges:
```bash
# Power range 600-700W
pv-pan-tool compare --power-range 600-700 --limit 5

# Efficiency range 21.5-23%  
pv-pan-tool compare --efficiency-range 21.5-23 --limit 4

# Combined ranges
pv-pan-tool compare --power-range 650-700 --efficiency-range 22-23
```

## Output Formats

### Table Format (Default)
Side-by-side comparison in a formatted table showing:

```
                          Module Comparison                          
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃                      ┃ JinkoSolar   ┃ JinkoSolar   ┃ JinkoSolar   ┃
┃ Parameter            ┃ JKM720N...   ┃ JKM715N...   ┃ JKM710N...   ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ Power (W)            │ 720.0        │ 715.0        │ 710.0        │
│ Efficiency (%)       │ 23.18        │ 23.02        │ 22.86        │
│ Voc (V)              │ 49.0         │ 48.9         │ 48.7         │
│ Isc (A)              │ 18.67        │ 18.60        │ 18.53        │
└──────────────────────┴──────────────┴──────────────┴──────────────┘
```

### JSON Format
Structured comparison data:
```json
{
  "comparison": {
    "modules": [
      {
        "id": 1,
        "manufacturer": "JinkoSolar", 
        "model": "JKM720N-72HL4-BDV",
        "specifications": {
          "pmax_stc": 720.0,
          "efficiency_stc": 23.18,
          "voc_stc": 49.0
        }
      }
    ],
    "parameters_compared": [...],
    "selection_criteria": {...}
  }
}
```

### CSV Format
Comparison data in spreadsheet format with modules as columns.

## Comparison Parameters

The comparison includes all key specifications:

**Electrical Parameters:**
- Maximum power (Pmax)
- Efficiency percentage  
- Open circuit voltage (Voc)
- Short circuit current (Isc)
- Voltage at maximum power (Vmp)
- Current at maximum power (Imp)

**Physical Parameters:**
- Module dimensions (length, width, thickness)
- Weight
- Cell configuration
- Module type (standard, bifacial, etc.)

**Performance Parameters:**
- Temperature coefficients
- Operating conditions
- Certification standards

## Sorting Options

Results can be sorted by any parameter:
- `pmax_stc` - Maximum power (default)
- `efficiency_stc` - Efficiency
- `voc_stc` - Open circuit voltage
- `isc_stc` - Short circuit current
- `price_per_watt` - Cost per watt (if available)

```bash
pv-pan-tool compare --top-power 5 --sort-by efficiency_stc
```

## Use Case Examples

### Technology Comparison
Compare different cell technologies:
```bash
# Monocrystalline vs bifacial modules
pv-pan-tool compare --top-power 3 --cell-type monocrystalline
pv-pan-tool compare --top-power 3 --cell-type bifacial
```

### Manufacturer Analysis  
Compare leading manufacturers:
```bash
pv-pan-tool compare --manufacturer "Jinko" --top-power 2 
pv-pan-tool compare --manufacturer "Longi" --top-power 2
```

### Project Planning
Compare modules for specific project requirements:
```bash
# Commercial project: 600W+ modules
pv-pan-tool compare --power-range 600-750 --limit 5

# Residential: high efficiency, standard size
pv-pan-tool compare --efficiency-range 21-23 --power-range 350-450
```

### Market Analysis
Analyze market segments:
```bash
# Premium segment: highest efficiency
pv-pan-tool compare --top-efficiency 10

# Value segment: cost-effective options  
pv-pan-tool compare --power-range 400-500 --sort-by price_per_watt
```

## Export and Sharing

### Save Comparisons
```bash
# Save to CSV for spreadsheet analysis
pv-pan-tool compare --top-power 10 --format csv --output top_modules.csv

# Save to JSON for further processing
pv-pan-tool compare --manufacturer "Jinko,Longi" --format json --output comparison.json
```

### Integration with Other Tools
The comparison output can be integrated with:
- Spreadsheet applications (CSV format)
- Data analysis tools (JSON format)  
- Report generation systems
- Project documentation
