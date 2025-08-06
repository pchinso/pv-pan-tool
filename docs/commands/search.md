# Search Command

The `search` command queries the PV module database to find modules matching specific criteria.

## Usage

```bash
pv-pan-tool search [OPTIONS]
```

## Options

| Option | Type | Description |
|--------|------|-------------|
| `-m, --manufacturer` | TEXT | Filter by manufacturer name (partial match) |
| `-M, --model` | TEXT | Filter by model name (partial match) |
| `-p, --power-min` | FLOAT | Minimum power rating in watts |
| `-P, --power-max` | FLOAT | Maximum power rating in watts |
| `-e, --efficiency-min` | FLOAT | Minimum efficiency percentage |
| `-E, --efficiency-max` | FLOAT | Maximum efficiency percentage |
| `-c, --cell-type` | CHOICE | Filter by cell type |
| `-l, --limit` | INTEGER | Maximum number of results to return |
| `-s, --sort-by` | CHOICE | Sort results by parameter |
| `-f, --format` | CHOICE | Output format: table, json, csv |
| `-o, --output` | PATH | Save results to file |
| `--include-details` | FLAG | Include detailed specifications |

## Cell Types

Available cell type filters:
- `monocrystalline` - Single crystal silicon
- `polycrystalline` - Multi-crystal silicon  
- `thin_film` - Thin-film technologies
- `perc` - Passivated Emitter Rear Cell
- `bifacial` - Bifacial modules
- `hjt` - Heterojunction technology
- `ibc` - Interdigitated Back Contact

## Sort Options

Results can be sorted by:
- `pmax_stc` - Maximum power (default)
- `efficiency_stc` - Efficiency percentage
- `voc_stc` - Open circuit voltage
- `isc_stc` - Short circuit current
- `price_per_watt` - Cost per watt (if available)

## Examples

### Basic manufacturer search

```bash
pv-pan-tool search --manufacturer "Jinko"
```

### Power and efficiency filtering

```bash
pv-pan-tool search --power-min 500 --power-max 700 --efficiency-min 21.0
```

### Cell type specific search

```bash
pv-pan-tool search --cell-type monocrystalline --limit 10 --sort-by efficiency_stc
```

### Complex multi-criteria search

```bash
pv-pan-tool search --manufacturer "Jinko,Longi" --power-min 600 --efficiency-min 22 --cell-type bifacial
```

### Export search results

```bash
pv-pan-tool search --manufacturer "Trina" --format csv --output trina_modules.csv
```

### Detailed specifications output

```bash
pv-pan-tool search --power-min 650 --include-details --format json
```

## Output Formats

### Table Format (Default)
Displays results in a formatted table showing:
- Module ID and manufacturer
- Model name
- Key specifications (power, efficiency, dimensions)
- Cell type and configuration

### JSON Format
Structured data including:
```json
{
  "modules": [
    {
      "id": 1,
      "manufacturer": "JinkoSolar",
      "model": "JKM720N-72HL4-BDV",
      "pmax_stc": 720.0,
      "efficiency_stc": 23.18,
      "cell_type": "monocrystalline",
      "module_type": "bifacial"
    }
  ],
  "total_results": 1,
  "search_criteria": {...}
}
```

### CSV Format
Comma-separated values suitable for spreadsheet import:
```csv
id,manufacturer,model,pmax_stc,efficiency_stc,voc_stc,isc_stc
1,JinkoSolar,JKM720N-72HL4-BDV,720.0,23.18,49.0,18.67
```

## Performance Tips

1. **Use specific filters** to reduce result sets
2. **Limit results** for faster display with `--limit`
3. **Index-friendly searches** use manufacturer and power filters
4. **Export large datasets** rather than displaying in terminal

## Search Examples by Use Case

### Residential Applications
Find modules suitable for home installations:
```bash
pv-pan-tool search --power-min 350 --power-max 450 --efficiency-min 20 --sort-by efficiency_stc
```

### Commercial Projects  
High-power modules for commercial installations:
```bash
pv-pan-tool search --power-min 500 --cell-type monocrystalline --sort-by pmax_stc --limit 20
```

### Utility Scale
Large utility-scale project modules:
```bash
pv-pan-tool search --power-min 600 --efficiency-min 21.5 --cell-type bifacial
```

### Budget Analysis
Cost-effective options (when price data available):
```bash
pv-pan-tool search --power-min 400 --sort-by price_per_watt --limit 15
```
