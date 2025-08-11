"""
Output formatting utilities for PV PAN Tool CLI.

This module provides functions for formatting data output
in various formats (tables, JSON, CSV, etc.).
"""

import json
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table


def format_module_table(modules: List[Dict[str, Any]],
                       title: str = "Modules",
                       verbose: bool = False) -> Table:
    """
    Format a list of modules as a Rich table.

    Args:
        modules: List of module dictionaries
        title: Table title
        verbose: Include additional columns

    Returns:
        Rich Table object
    """
    table = Table(title=title)

    # Basic columns
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Manufacturer", style="blue", width=12)
    table.add_column("Model", style="green", width=15)
    table.add_column("Power (W)", style="red", justify="right", width=8)
    table.add_column("Efficiency (%)", style="magenta", justify="right", width=10)

    if verbose:
        table.add_column("Voc (V)", style="yellow", justify="right", width=7)
        table.add_column("Isc (A)", style="cyan", justify="right", width=7)
        table.add_column("Cell Type", style="dim", width=12)
        table.add_column("Dimensions", style="dim", width=12)

    # Add rows
    for module in modules:
        row = [
            str(module.get('id', '')),
            truncate_string(module.get('manufacturer', ''), 12),
            truncate_string(module.get('model', ''), 15),
            format_number(module.get('pmax_stc'), 1),
            format_number(module.get('efficiency_stc'), 2),
        ]

        if verbose:
            row.extend([
                format_number(module.get('voc_stc'), 1),
                format_number(module.get('isc_stc'), 2),
                truncate_string(module.get('cell_type', ''), 12),
                format_dimensions(module.get('height'), module.get('width'))
            ])

        table.add_row(*row)

    return table


def format_comparison_table(modules: List[Dict[str, Any]],
                          title: str = "Module Comparison") -> Table:
    """
    Format modules for side-by-side comparison.

    Args:
        modules: List of module dictionaries
        title: Table title

    Returns:
        Rich Table object
    """
    table = Table(title=title, show_header=True)

    # Add parameter column
    table.add_column("Parameter", style="bold cyan", width=20)

    # Add one column per module
    for i, module in enumerate(modules):
        manufacturer = truncate_string(module.get('manufacturer', ''), 10)
        model = truncate_string(module.get('model', ''), 10)
        table.add_column(f"{manufacturer}\n{model}", style="green", width=12)

    # Define parameters to compare
    parameters = [
        ("Power (W)", "pmax_stc", 1),
        ("Efficiency (%)", "efficiency_stc", 2),
        ("Voc (V)", "voc_stc", 1),
        ("Isc (A)", "isc_stc", 2),
        ("Vmp (V)", "vmp_stc", 1),
        ("Imp (A)", "imp_stc", 2),
    ("Height (mm)", "height", 0),
        ("Width (mm)", "width", 0),
        ("Thickness (mm)", "thickness", 1),
        ("Weight (kg)", "weight", 1),
        ("Cell Type", "cell_type", None),
        ("Module Type", "module_type", None),
        ("Cells in Series", "cells_in_series", 0),
        ("Total Cells", "total_cells", 0),
    ]

    # Add rows
    for param_name, param_key, decimals in parameters:
        row = [param_name]
        for module in modules:
            value = module.get(param_key)
            if decimals is not None and isinstance(value, (int, float)):
                formatted_value = format_number(value, decimals)
            else:
                formatted_value = str(value) if value is not None else ""
            row.append(formatted_value)
        table.add_row(*row)

    return table


def format_statistics_table(stats: Dict[str, Any]) -> Table:
    """
    Format database statistics as a table.

    Args:
        stats: Statistics dictionary

    Returns:
        Rich Table object
    """
    table = Table(title="Database Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    # Basic stats
    table.add_row("Total Modules", str(stats.get('total_modules', 0)))
    table.add_row("Total Manufacturers", str(stats.get('total_manufacturers', 0)))

    # Power range
    power_range = stats.get('power_range', {})
    if power_range:
        table.add_row("Power Range (W)",
                     f"{power_range.get('min', 0):.1f} - {power_range.get('max', 0):.1f}")

    # Efficiency range
    efficiency_range = stats.get('efficiency_range', {})
    if efficiency_range:
        table.add_row("Efficiency Range (%)",
                     f"{efficiency_range.get('min', 0):.2f} - {efficiency_range.get('max', 0):.2f}")

    # Cell type distribution
    cell_types = stats.get('cell_type_distribution', {})
    if cell_types:
        for cell_type, count in cell_types.items():
            table.add_row(f"  {cell_type.title()}", str(count))

    return table


def format_search_results(results: List[Dict[str, Any]],
                         format_type: str = "table",
                         verbose: bool = False) -> str:
    """
    Format search results in the specified format.

    Args:
        results: List of module dictionaries
        format_type: Output format ('table', 'json', 'csv')
        verbose: Include additional details

    Returns:
        Formatted string
    """
    if format_type == "json":
        return format_json(results)
    elif format_type == "csv":
        return format_csv(results)
    else:  # table
        console = Console()
        table = format_module_table(results, verbose=verbose)
        with console.capture() as capture:
            console.print(table)
        return capture.get()


def format_json(data: Any, indent: int = 2) -> str:
    """
    Format data as JSON string.

    Args:
        data: Data to format
        indent: JSON indentation

    Returns:
        JSON string
    """
    # Clean None values and convert to JSON-serializable format
    if isinstance(data, list):
        clean_data = []
        for item in data:
            if isinstance(item, dict):
                clean_item = {k: v for k, v in item.items() if v is not None}
                clean_data.append(clean_item)
            else:
                clean_data.append(item)
    else:
        clean_data = data

    return json.dumps(clean_data, indent=indent, ensure_ascii=False)


def format_csv(data: List[Dict[str, Any]], delimiter: str = ",") -> str:
    """
    Format data as CSV string.

    Args:
        data: List of dictionaries to format
        delimiter: CSV delimiter

    Returns:
        CSV string
    """
    if not data:
        return ""

    # Get all unique keys
    all_keys = set()
    for item in data:
        all_keys.update(item.keys())

    sorted_keys = sorted(all_keys)

    # Build CSV
    lines = []

    # Header
    lines.append(delimiter.join(sorted_keys))

    # Rows
    for item in data:
        row = []
        for key in sorted_keys:
            value = item.get(key, '')
            if value is None:
                value = ''

            # Escape CSV special characters
            value_str = str(value).replace('"', '""')
            if delimiter in value_str or '"' in value_str or '\n' in value_str:
                value_str = f'"{value_str}"'

            row.append(value_str)

        lines.append(delimiter.join(row))

    return '\n'.join(lines)


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.

    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def format_number(value: Optional[float], decimals: int) -> str:
    """
    Format number with specified decimal places.

    Args:
        value: Number to format
        decimals: Number of decimal places

    Returns:
        Formatted string
    """
    if value is None:
        return ""

    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return str(value)


def format_dimensions(height: Optional[float], width: Optional[float]) -> str:
    """
    Format module dimensions.

    Args:
        height: Height in mm
        width: Width in mm

    Returns:
        Formatted dimensions string
    """
    if height is not None and width is not None:
        return f"{height:.0f}×{width:.0f}"
    elif height is not None:
        return f"{height:.0f}×?"
    elif width is not None:
        return f"?×{width:.0f}"
    else:
        return ""


def format_percentage(value: Optional[float], decimals: int = 1) -> str:
    """
    Format value as percentage.

    Args:
        value: Value to format
        decimals: Number of decimal places

    Returns:
        Formatted percentage string
    """
    if value is None:
        return ""

    try:
        return f"{float(value):.{decimals}f}%"
    except (ValueError, TypeError):
        return str(value)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
