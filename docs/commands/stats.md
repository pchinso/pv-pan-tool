# Statistics Command

The `stats` command provides comprehensive statistical analysis and insights about the PV module database, including manufacturer comparisons, technology trends, and market analysis.

## Usage

```bash
pv-pan-tool stats [OPTIONS]
```

## Options

| Option | Type | Description |
|--------|------|-------------|
| `--by-manufacturer` | FLAG | Show statistics grouped by manufacturer |
| `--by-cell-type` | FLAG | Show statistics grouped by cell technology |
| `--by-power-range` | FLAG | Show statistics by power output ranges |
| `-l, --limit` | INTEGER | Limit number of results shown |
| `-s, --sort-by` | CHOICE | Sort results by: count, power, efficiency |
| `-f, --format` | CHOICE | Output format: table, json, csv |
| `-o, --output` | PATH | Save statistics to file |

## Statistical Reports

### Overall Database Statistics
Basic overview of the entire database:

```bash
pv-pan-tool stats
```

Shows:
- Total number of modules
- Total number of manufacturers  
- Power range (minimum to maximum)
- Efficiency range (minimum to maximum)
- Average specifications across all modules

### Manufacturer Analysis

```bash
pv-pan-tool stats --by-manufacturer
```

Provides per-manufacturer statistics:
- Number of module models
- Average power output
- Average efficiency rating
- Power range for each manufacturer
- Market share by module count

### Technology Analysis

```bash
pv-pan-tool stats --by-cell-type
```

Breaks down statistics by cell technology:
- Module count per technology type
- Average specifications by technology
- Performance characteristics comparison
- Market adoption trends

### Power Range Analysis

```bash
pv-pan-tool stats --by-power-range
```

Categorizes modules into power ranges:
- Residential (< 400W)
- Commercial (400-600W)  
- Utility (> 600W)
- Distribution within each category

## Example Outputs

### Overall Statistics
```
╭─────────────────── Database Statistics ────────────────────╮
│ Total Modules: 61                                          │
│ Total Manufacturers: 3                                     │
│ Total Models: 45                                          │
│                                                           │
│ Power Range: 560.0W - 720.0W                             │
│ Efficiency Range: 21.7% - 23.3%                          │
│ Average Power: 642.5W                                     │
│ Average Efficiency: 22.4%                                 │
╰──────────────────────────────────────────────────────────╯
```

### Manufacturer Statistics
```
Manufacturer Statistics
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Manufacturer   ┃ Module Count ┃ Avg Power    ┃ Avg Efficiency ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ JinkoSolar     │ 35           │ 650.2W       │ 22.6%          │
│ LONGi          │ 18           │ 625.8W       │ 22.1%          │  
│ Trina Solar    │ 8            │ 670.5W       │ 22.8%          │
└────────────────┴──────────────┴──────────────┴────────────────┘
```

## Analysis Features

### Trend Analysis
Identify market trends and patterns:
- Technology adoption rates
- Power output evolution  
- Efficiency improvements over time
- Manufacturer market positioning

### Performance Benchmarking
Compare performance across categories:
- Best-in-class efficiency by power range
- Technology performance comparison
- Manufacturer performance ranking
- Price-performance analysis (when price data available)

### Market Intelligence
Understand market dynamics:
- Market share by manufacturer
- Technology distribution
- Product portfolio analysis
- Competitive positioning

## Export and Reporting

### Save Statistics
```bash
# Export to CSV for spreadsheet analysis
pv-pan-tool stats --by-manufacturer --format csv --output manufacturer_stats.csv

# Export to JSON for programmatic use  
pv-pan-tool stats --format json --output database_stats.json
```

### Integration with Analysis Tools
Statistics can be exported for use with:
- Business intelligence platforms
- Data visualization tools
- Market research reports
- Investment analysis
- Technology assessments

## Use Cases

### Market Research
```bash
pv-pan-tool stats --by-manufacturer --sort-by efficiency --limit 10
```

### Technology Assessment
```bash
pv-pan-tool stats --by-cell-type --format json --output tech_analysis.json
```

### Competitive Analysis
```bash
pv-pan-tool stats --by-manufacturer --sort-by count --output market_share.csv
```

### Product Planning
```bash
pv-pan-tool stats --by-power-range --format table
```
