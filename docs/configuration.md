# Configuration Guide

The PV PAN Tool can be configured through multiple methods to customize its behavior for your specific needs.

## Configuration Methods

### 1. Command Line Options
Most settings can be specified directly via command-line arguments:

```bash
pv-pan-tool parse --input-dir /path/to/files --output-db custom.db
```

### 2. Configuration File
Create a YAML configuration file for persistent settings:

**config.yaml:**
```yaml
# Database settings
database_path: "data/database/pv_modules.db"
backup_directory: "data/backups"

# Parsing settings  
default_input_directory: "data/pan_files"
batch_size: 100
parallel_workers: 4

# Output settings
default_output_format: "table"
include_details_by_default: false

# Performance settings
query_timeout: 30
max_results_limit: 1000

# Logging settings
log_level: "INFO"
log_file: "logs/pv_pan_tool.log"
```

Usage:
```bash
pv-pan-tool --config-file config.yaml parse --recursive
```

### 3. Environment Variables
Set environment variables for system-wide configuration:

```bash
export PV_PAN_DATABASE_PATH="/opt/pv_data/modules.db"
export PV_PAN_LOG_LEVEL="DEBUG"
export PV_PAN_WORKERS="8"
```

## Configuration Hierarchy

Settings are applied in order of precedence:
1. **Command-line arguments** (highest priority)
2. **Configuration file** options
3. **Environment variables**  
4. **Default values** (lowest priority)

## Database Configuration

### Database Location
```yaml
database_path: "custom/path/to/database.db"
```

### Backup Settings
```yaml
backup_directory: "backups/"
auto_backup: true
backup_retention_days: 30
compress_backups: true
```

### Performance Tuning
```yaml
connection_pool_size: 10
query_timeout: 60
pragma_settings:
  journal_mode: "WAL"
  cache_size: 10000
  temp_store: "MEMORY"
```

## Parsing Configuration

### Input Settings
```yaml
default_input_directory: "data/pan_files"
file_extensions: [".PAN", ".pan"]
recursive_scan: true
follow_symlinks: false
```

### Processing Options
```yaml
batch_size: 200
parallel_workers: 6
skip_duplicates: true
encoding_fallback: ["utf-8", "latin-1", "cp1252"]
```

### Error Handling
```yaml
continue_on_error: true
max_errors_per_batch: 10
error_log_file: "logs/parsing_errors.log"
```

## Output Configuration

### Default Formats
```yaml
default_output_format: "table"  # table, json, csv, excel
table_max_width: 120
json_indent: 2
csv_delimiter: ","
```

### Export Settings
```yaml
include_details_by_default: false
max_export_records: 50000
export_compression: false
```

## Logging Configuration

### Log Levels
```yaml
log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
log_file: "logs/pv_pan_tool.log"
log_rotation: true
log_max_size: "10MB"
log_backup_count: 5
```

### Console Output
```yaml
console_log_level: "WARNING"
progress_bars: true
color_output: true
```

## Search and Filter Defaults

### Default Limits
```yaml
default_search_limit: 100
max_search_limit: 10000
default_sort_by: "pmax_stc"
```

### Filter Presets
```yaml
filter_presets:
  residential:
    power_min: 250
    power_max: 450
    efficiency_min: 18.0
    
  commercial:
    power_min: 400
    power_max: 600
    efficiency_min: 20.0
    
  utility:
    power_min: 550
    efficiency_min: 21.0
```

## Integration Settings

### API Configuration
```yaml
api_enabled: false
api_host: "localhost"
api_port: 8000
api_key_required: true
```

### Web Interface
```yaml
web_interface: false
web_port: 8080
web_host: "127.0.0.1"
```

## Example Configuration Files

### Development Configuration
```yaml
# config_dev.yaml
database_path: "dev_data/modules.db"
log_level: "DEBUG"
parallel_workers: 2
auto_backup: false
console_log_level: "DEBUG"
progress_bars: true
```

### Production Configuration  
```yaml
# config_prod.yaml
database_path: "/var/lib/pv_pan_tool/modules.db"
backup_directory: "/var/backups/pv_pan_tool"
log_level: "WARNING"
log_file: "/var/log/pv_pan_tool.log"
parallel_workers: 8
auto_backup: true
compress_backups: true
```

### High Performance Configuration
```yaml
# config_performance.yaml
parallel_workers: 16
batch_size: 500
connection_pool_size: 20
pragma_settings:
  journal_mode: "WAL"  
  synchronous: "NORMAL"
  cache_size: 50000
  temp_store: "MEMORY"
query_timeout: 120
```

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `PV_PAN_DATABASE_PATH` | Database file path | `data/database/pv_modules.db` |
| `PV_PAN_LOG_LEVEL` | Logging level | `INFO` |
| `PV_PAN_WORKERS` | Number of parallel workers | `4` |
| `PV_PAN_BATCH_SIZE` | Parsing batch size | `100` |
| `PV_PAN_CONFIG_FILE` | Configuration file path | `config.yaml` |
| `PV_PAN_BACKUP_DIR` | Backup directory | `data/backups` |

## Configuration Validation

The tool validates configuration on startup:

```bash
# Check configuration validity
pv-pan-tool --config-file config.yaml info --verbose
```

Validation includes:
- File path accessibility
- Database connectivity  
- Parameter value ranges
- Required dependencies
- Permission checks

## Troubleshooting Configuration

### Common Issues

**Database Permission Errors:**
```yaml
database_path: "/path/with/write/permissions/modules.db"
```

**Performance Issues:**
```yaml
parallel_workers: 2  # Reduce if system overloaded
batch_size: 50       # Smaller batches for limited memory
```

**Encoding Problems:**
```yaml
encoding_fallback: ["utf-8", "latin-1", "cp1252", "utf-16"]
```

### Configuration Testing
Test configuration changes:
```bash
# Dry run with new config
pv-pan-tool --config-file new_config.yaml info

# Test parsing with sample data
pv-pan-tool --config-file new_config.yaml parse --input-dir test_data
```
