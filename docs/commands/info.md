# Info Command

The `info` command provides a quick overview of system information and database statistics, giving you an instant snapshot of your PV module database status.

## Usage

```bash
pv-pan-tool info [OPTIONS]
```

## Options

| Option | Type | Description |
|--------|------|-------------|
| `-v, --verbose` | FLAG | Show detailed system information |
| `-f, --format` | CHOICE | Output format: table, json |
| `-o, --output` | PATH | Save information to file |

## Information Displayed

### System Information

- **Database Path**: Location of the SQLite database file
- **Database Size**: File size on disk
- **Last Modified**: When the database was last updated
- **Tool Version**: Current version of PV PAN Tool

### Database Statistics

- **Total Modules**: Number of PV modules in database
- **Total Manufacturers**: Number of unique manufacturers
- **Power Range**: Minimum and maximum power ratings
- **Efficiency Range**: Minimum and maximum efficiency values

## Examples

### Basic Info

```bash
pv-pan-tool info
```

Output:

```
╭─────────────── PV PAN Tool Information ────────────────╮
│ System Information                                     │
│ Database Path: data/database/pv_modules.db             │
│ Total Modules: 61                                      │
│ Total Manufacturers: 3                                 │
│ Power Range: 560.0W - 720.0W                          │
│ Efficiency Range: 21.7% - 23.3%                       │
╰────────────────────────────────────────────────────────╯
```

### Verbose Info

```bash
pv-pan-tool info --verbose
```

Additional information includes:

- Configuration file paths
- Environment settings
- Database schema version
- Index status
- Performance metrics

### JSON Format

```bash
pv-pan-tool info --format json
```

Structured output:

```json
{
  "system": {
    "database_path": "data/database/pv_modules.db",
    "database_size": 294912,
    "last_modified": "2025-01-06T15:56:15Z",
    "tool_version": "1.0.0"
  },
  "database": {
    "total_modules": 61,
    "total_manufacturers": 3,
    "power_range": {
      "min": 560.0,
      "max": 720.0,
      "average": 642.5
    },
    "efficiency_range": {
      "min": 21.7,
      "max": 23.3,
      "average": 22.4
    }
  }
}
```

## Use Cases

### Quick Status Check

Verify database status before operations:

```bash
pv-pan-tool info
```

### System Diagnostics

Get detailed system information for troubleshooting:

```bash
pv-pan-tool info --verbose
```

### Integration with Scripts

Export system info for automated monitoring:

```bash
pv-pan-tool info --format json --output system_status.json
```

### Project Planning

Check available data before starting analysis:

```bash
pv-pan-tool info
pv-pan-tool stats --by-manufacturer
```

## Interpreting Results

### Database Health Indicators

- **Module Count**: Should match expected number of parsed files
- **Manufacturer Count**: Indicates data diversity
- **Power/Efficiency Ranges**: Show data quality and completeness

### Performance Indicators

- **Database Size**: Large sizes may indicate performance considerations
- **Last Modified**: Shows data freshness
- **Response Time**: Quick responses indicate good database health

## Integration

The info command is designed for:

- **Health Checks**: Quick system status verification
- **Monitoring Scripts**: Automated system monitoring
- **Documentation**: System state for reports
- **Troubleshooting**: Initial diagnostic information
