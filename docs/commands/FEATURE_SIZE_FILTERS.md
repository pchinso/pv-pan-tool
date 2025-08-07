# Size Filtering Feature Implementation

## Overview

Added height and width filtering capabilities to the PV PAN Tool export command, allowing users to filter modules by their physical dimensions.

## Changes Made

### 1. Database Layer (`src/pv_pan_tool/database.py`)

#### Updated `search_modules` method

- Added 4 new parameters: `min_height`, `max_height`, `min_width`, `max_width`
- Added corresponding SQL filters for height and width dimensions
- Updated method documentation to reflect new parameters

**New Parameters:**

- `min_height: Optional[float]` - Minimum height in mm
- `max_height: Optional[float]` - Maximum height in mm
- `min_width: Optional[float]` - Minimum width in mm
- `max_width: Optional[float]` - Maximum width in mm

### 2. Export Command (`src/pv_pan_tool/cli/commands/export.py`)

#### Added new command-line options

- `--height-min, -h FLOAT` - Minimum height (mm)
- `--height-max, -H FLOAT` - Maximum height (mm)
- `--width-min, -w FLOAT` - Minimum width (mm)
- `--width-max, -W FLOAT` - Maximum width (mm)

#### Updated function signature

- Added height and width parameters to the export function
- Updated criteria dictionary to include size filters
- Updated search_modules call to pass new parameters

#### Enhanced documentation

- Added examples showing size filtering usage
- Updated help text for all new options

## Usage Examples

### Command Line Examples

1. **Export compact modules:**

   ```bash
   pv-pan-tool export --format csv --height-max 1800 --width-max 1200 --output compact_modules.csv
   ```

2. **Export large utility-scale modules:**

   ```bash
   pv-pan-tool export --format xlsx --height-min 2000 --output large_modules.xlsx
   ```

3. **Export modules within specific size range:**

   ```bash
   pv-pan-tool export --format json --height-min 1800 --height-max 2200 --width-min 1000 --width-max 1300 --output standard_size.json
   ```

4. **Combine size filters with other criteria:**

   ```bash
   pv-pan-tool export --format csv --efficiency-min 22 --height-max 1800 --width-max 1200 --manufacturer 'SunPower' --output efficient_compact.csv
   ```

### Database Query Example

```python
modules = db.search_modules(
    manufacturer='Jinko',
    min_power=450,
    max_power=550,
    min_efficiency=21.0,
    min_height=1900,      # New: minimum height in mm
    max_height=2100,      # New: maximum height in mm
    min_width=1050,       # New: minimum width in mm
    max_width=1250,       # New: maximum width in mm
    limit=10
)
```

## Technical Details

### Database Schema

The implementation leverages existing `height` and `width` columns in the `pv_modules` table:

- `height REAL` - Module height in millimeters
- `width REAL` - Module width in millimeters

### SQL Query Generation

The new filters generate additional WHERE clauses:

```sql
SELECT * FROM pv_modules WHERE
    -- ... existing filters ...
    AND height >= ?      -- min_height filter
    AND height <= ?      -- max_height filter
    AND width >= ?       -- min_width filter
    AND width <= ?       -- max_width filter
    ORDER BY pmax_stc DESC
```

## Benefits

1. **Enhanced Filtering**: Users can now filter modules by physical dimensions
2. **Installation Compatibility**: Find modules that fit specific space constraints
3. **Application-Specific Searches**: Easily identify compact vs. utility-scale modules
4. **Combined Filtering**: Size filters work seamlessly with existing power, efficiency, and manufacturer filters

## Backwards Compatibility

- All existing functionality remains unchanged
- New parameters are optional with default values of `None`
- Existing scripts and commands continue to work without modification

## Files Modified

1. `src/pv_pan_tool/database.py` - Updated search_modules method
2. `src/pv_pan_tool/cli/commands/export.py` - Added size filter options

## Future Enhancements

This implementation provides the foundation for adding size filtering to other commands:

- Search command (`src/pv_pan_tool/cli/commands/search.py`)
- Compare command (`src/pv_pan_tool/cli/commands/compare.py`)

The same pattern can be applied to these commands by adding the same height/width options and updating their respective search_modules calls.
