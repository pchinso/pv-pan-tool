# Parse Command

The `parse` command processes .PAN files and extracts photovoltaic module specifications into a structured SQLite database.

## Usage

```bash
pv-pan-tool parse [OPTIONS]
```

## Options

| Option | Type | Description |
|--------|------|-------------|
| `-i, --input-dir` | PATH | Directory containing .PAN files to parse |
| `-r, --recursive` | FLAG | Search subdirectories recursively |
| `-f, --force` | FLAG | Force re-parsing of already processed files |
| `-o, --output-db` | PATH | Path to output database file (default: data/database/pv_modules.db) |
| `--clear-db` | FLAG | Clear existing database before parsing |
| `--batch-size` | INTEGER | Number of files to process in each batch (default: 100) |
| `--workers` | INTEGER | Number of parallel workers (default: 4) |

## Examples

### Basic parsing

```bash
pv-pan-tool parse --input-dir "C:\pan_files"
```

### Recursive parsing with progress

```bash
pv-pan-tool parse --input-dir "data/pan_files" --recursive --verbose
```

### Force re-parse all files

```bash
pv-pan-tool parse --input-dir "data/pan_files" --recursive --force
```

### Clear database and start fresh

```bash
pv-pan-tool parse --input-dir "data/pan_files" --clear-db --recursive
```

## Output

The command processes each .PAN file and:

1. **Extracts specifications** including:
   - Electrical parameters (Pmax, Voc, Isc, Vmp, Imp)
   - Efficiency ratings
   - Mechanical dimensions and weight
   - Cell configuration and type
   - Temperature coefficients
   - Operating conditions

2. **Stores in database** with:
   - Unique module identification
   - Manufacturer and model information
   - Complete technical specifications
   - File metadata and parsing timestamps

3. **Shows progress** including:
   - Files processed vs. total
   - Processing rate (files/second)
   - Errors and skipped files
   - Final statistics

## File Registry

The parser maintains a registry (`parsed_files_registry.json`) to track:

- Previously processed files
- File modification times
- Processing status
- Error history

This enables incremental parsing - only new or modified files are reprocessed unless `--force` is used.

## Error Handling

The parser handles various error conditions gracefully:

- **Invalid .PAN format**: Logs error and continues with next file
- **Missing required parameters**: Uses default values where possible
- **Encoding issues**: Attempts multiple encodings (UTF-8, Latin-1, CP1252)
- **Database conflicts**: Updates existing records with newer data

## Performance

Processing performance depends on:

- Number of .PAN files
- File size and complexity
- System specifications
- Database location (SSD vs. HDD)

Typical performance: **100-500 files per second** on modern systems.

## Supported .PAN Formats

The parser supports various .PAN file formats including:

- **PVsyst format**: Standard industry format
- **SAM format**: System Advisor Model files
- **Custom formats**: Manufacturer-specific variants
- **Multi-language**: Files with international character sets

## Database Schema

Parsed data is stored in a normalized SQLite database with tables for:

- **pv_modules**: Main module specifications
- **manufacturers**: Manufacturer information
- **parsing_log**: Processing history and metadata
