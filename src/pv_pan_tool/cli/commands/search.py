"""
Search command for PV PAN Tool CLI.

This module provides search functionality for finding modules
in the database based on various criteria.
"""

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...database import PVModuleDatabase
from ..utils.config import get_config
from ..utils.formatters import format_module_table, format_search_results

console = Console()


@click.command()
@click.option(
    "--manufacturer", "-m",
    help="Filter by manufacturer name (partial match)"
)
@click.option(
    "--model", "-M",
    help="Filter by model name (partial match)"
)
@click.option(
    "--series", "-s",
    help="Filter by series name (partial match)"
)
@click.option(
    "--power-min", "-p",
    type=float,
    help="Minimum power rating (W)"
)
@click.option(
    "--power-max", "-P",
    type=float,
    help="Maximum power rating (W)"
)
@click.option(
    "--efficiency-min", "-e",
    type=float,
    help="Minimum efficiency (%)"
)
@click.option(
    "--efficiency-max", "-E",
    type=float,
    help="Maximum efficiency (%)"
)
@click.option(
    "--cell-type", "-c",
    type=click.Choice(['monocrystalline', 'polycrystalline', 'thin_film', 'perc', 'bifacial', 'hjt', 'ibc']),
    help="Filter by cell type"
)
@click.option(
    "--module-type", "-t",
    type=click.Choice(['standard', 'bifacial', 'glass_glass', 'flexible', 'bipv']),
    help="Filter by module type"
)
@click.option(
    "--sort-by", "-S",
    type=click.Choice(['pmax_stc', 'efficiency_stc', 'manufacturer', 'model', 'voc_stc', 'isc_stc']),
    default='pmax_stc',
    help="Sort results by field"
)
@click.option(
    "--sort-order", "-O",
    type=click.Choice(['asc', 'desc']),
    default='desc',
    help="Sort order"
)
@click.option(
    "--limit", "-l",
    type=int,
    default=20,
    help="Maximum number of results to show"
)
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    help="Save results to file (CSV format)"
)
@click.option(
    "--format", "-f",
    "output_format",
    type=click.Choice(['table', 'json', 'csv']),
    default='table',
    help="Output format"
)
@click.pass_context
def search(ctx, manufacturer, model, series, power_min, power_max,
          efficiency_min, efficiency_max, cell_type, module_type,
          sort_by, sort_order, limit, output, output_format):
    """
    Search for modules in the database.

    Search for PV modules based on various criteria such as manufacturer,
    model, power rating, efficiency, cell type, and more.

    Examples:
        pv-pan-tool search --manufacturer "Jinko"
        pv-pan-tool search --power-min 500 --power-max 600
        pv-pan-tool search --efficiency-min 22.0 --sort-by efficiency_stc
        pv-pan-tool search --manufacturer "Longi" --cell-type "monocrystalline"
        pv-pan-tool search --power-min 550 --limit 10 --output results.csv
    """
    config = ctx.obj.get('config', {})
    verbose = ctx.obj.get('verbose', False)

    # Get database path
    db_path = get_config('database_path', 'data/database/pv_modules.db',
                        config_file=ctx.obj.get('config_file'))

    try:
        db = PVModuleDatabase(str(db_path))

        # Build search criteria
        criteria = {}
        if manufacturer:
            criteria['manufacturer'] = manufacturer
        if model:
            criteria['model'] = model
        if series:
            criteria['series'] = series
        if power_min is not None:
            criteria['power_min'] = power_min
        if power_max is not None:
            criteria['power_max'] = power_max
        if efficiency_min is not None:
            criteria['efficiency_min'] = efficiency_min
        if efficiency_max is not None:
            criteria['efficiency_max'] = efficiency_max
        if cell_type:
            criteria['cell_type'] = cell_type
        if module_type:
            criteria['module_type'] = module_type

        if verbose:
            console.print(f"[blue]Search criteria:[/blue] {criteria}")
            console.print(f"[blue]Sort by:[/blue] {sort_by} ({sort_order})")
            console.print(f"[blue]Limit:[/blue] {limit}")

        # Perform search
        with console.status("[bold green]Searching database..."):
            results = db.search_modules(
                manufacturer=manufacturer,
                model=model,
                min_power=power_min,
                max_power=power_max,
                min_efficiency=efficiency_min,
                max_efficiency=efficiency_max,
                cell_type=cell_type,
                limit=limit
            )

        if not results:
            console.print("[yellow]No modules found matching the search criteria.[/yellow]")
            return

        console.print(f"[green]Found {len(results)} modules[/green]")

        # Format and display results
        if output_format == 'table':
            show_search_results_table(results, verbose)
        elif output_format == 'json':
            show_search_results_json(results)
        elif output_format == 'csv':
            show_search_results_csv(results)

        # Save to file if requested
        if output:
            save_search_results(results, output, verbose)

    except Exception as e:
        console.print(f"[red]Error during search: {e}[/red]")
        if verbose:
            console.print_exception()
        raise click.Abort()


def show_search_results_table(results, verbose):
    """Display search results in table format."""
    table = Table(title="Search Results")

    # Add columns
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Manufacturer", style="blue", width=12)
    table.add_column("Model", style="green", width=15)
    table.add_column("Power (W)", style="red", justify="right", width=8)
    table.add_column("Efficiency (%)", style="magenta", justify="right", width=10)
    table.add_column("Voc (V)", style="yellow", justify="right", width=7)
    table.add_column("Isc (A)", style="cyan", justify="right", width=7)

    if verbose:
        table.add_column("Cell Type", style="dim", width=12)
        table.add_column("Dimensions", style="dim", width=12)

    # Add rows
    for module in results:
        row = [
            str(module.get('id', '')),
            module.get('manufacturer', '')[:12],
            module.get('model', '')[:15],
            f"{module.get('pmax_stc', 0):.1f}" if module.get('pmax_stc') else '',
            f"{module.get('efficiency_stc', 0):.2f}" if module.get('efficiency_stc') else '',
            f"{module.get('voc_stc', 0):.1f}" if module.get('voc_stc') else '',
            f"{module.get('isc_stc', 0):.2f}" if module.get('isc_stc') else '',
        ]

        if verbose:
            row.extend([
                module.get('cell_type', '')[:12],
                f"{module.get('length', 0):.0f}x{module.get('width', 0):.0f}" if module.get('length') and module.get('width') else ''
            ])

        table.add_row(*row)

    console.print(table)


def show_search_results_json(results):
    """Display search results in JSON format."""
    import json

    # Convert to JSON-serializable format
    json_results = []
    for module in results:
        json_module = {}
        for key, value in module.items():
            if value is not None:
                json_module[key] = value
        json_results.append(json_module)

    json_output = json.dumps(json_results, indent=2, ensure_ascii=False)
    console.print(json_output)


def show_search_results_csv(results):
    """Display search results in CSV format."""
    if not results:
        return

    # Get all unique keys
    all_keys = set()
    for module in results:
        all_keys.update(module.keys())

    # Sort keys for consistent output
    sorted_keys = sorted(all_keys)

    # Print header
    console.print(','.join(sorted_keys))

    # Print rows
    for module in results:
        row = []
        for key in sorted_keys:
            value = module.get(key, '')
            if value is None:
                value = ''
            # Escape commas and quotes in CSV
            value_str = str(value).replace('"', '""')
            if ',' in value_str or '"' in value_str:
                value_str = f'"{value_str}"'
            row.append(value_str)
        console.print(','.join(row))


def save_search_results(results, output_path, verbose):
    """Save search results to file."""
    try:
        import csv

        if not results:
            console.print("[yellow]No results to save.[/yellow]")
            return

        # Get all unique keys
        all_keys = set()
        for module in results:
            all_keys.update(module.keys())

        sorted_keys = sorted(all_keys)

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=sorted_keys)
            writer.writeheader()

            for module in results:
                # Clean None values
                clean_module = {k: v for k, v in module.items() if v is not None}
                writer.writerow(clean_module)

        console.print(f"[green]Results saved to:[/green] {output_path}")

    except Exception as e:
        console.print(f"[red]Error saving results: {e}[/red]")


@click.command()
@click.option(
    "--type", "-t",
    "list_type",
    type=click.Choice(['manufacturers', 'models', 'series', 'cell-types', 'module-types']),
    required=True,
    help="Type of items to list"
)
@click.option(
    "--manufacturer", "-m",
    help="Filter models/series by manufacturer"
)
@click.option(
    "--limit", "-l",
    type=int,
    default=50,
    help="Maximum number of items to show"
)
@click.pass_context
def list_items(ctx, list_type, manufacturer, limit):
    """
    List manufacturers, models, or other categorical data.

    Examples:
        pv-pan-tool list manufacturers
        pv-pan-tool list models --manufacturer "Jinko"
        pv-pan-tool list cell-types
    """
    config = ctx.obj.get('config', {})
    verbose = ctx.obj.get('verbose', False)

    # Get database path
    db_path = get_config('database_path', 'data/database/pv_modules.db',
                        config_file=ctx.obj.get('config_file'))

    try:
        db = PVModuleDatabase(str(db_path))

        if list_type == 'manufacturers':
            items = db.get_manufacturers()
            title = "Manufacturers"
            columns = ["Manufacturer", "Module Count"]

        elif list_type == 'models':
            if manufacturer:
                items = db.get_models_by_manufacturer(manufacturer)
                title = f"Models by {manufacturer}"
            else:
                items = db.get_all_models()
                title = "All Models"
            columns = ["Model", "Manufacturer", "Count"]

        elif list_type == 'series':
            if manufacturer:
                items = db.get_series_by_manufacturer(manufacturer)
                title = f"Series by {manufacturer}"
            else:
                items = db.get_all_series()
                title = "All Series"
            columns = ["Series", "Manufacturer", "Count"]

        elif list_type == 'cell-types':
            items = db.get_cell_types()
            title = "Cell Types"
            columns = ["Cell Type", "Count"]

        elif list_type == 'module-types':
            items = db.get_module_types()
            title = "Module Types"
            columns = ["Module Type", "Count"]

        if not items:
            console.print(f"[yellow]No {list_type} found.[/yellow]")
            return

        # Limit results
        if len(items) > limit:
            items = items[:limit]
            title += f" (showing first {limit})"

        # Create table
        table = Table(title=title)
        for col in columns:
            table.add_column(col)

        for item in items:
            if isinstance(item, dict):
                row = [str(item.get(col.lower().replace(' ', '_'), '')) for col in columns]
            else:
                row = [str(item)]
            table.add_row(*row)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing {list_type}: {e}[/red]")
        if verbose:
            console.print_exception()
        raise click.Abort()


# Remove the problematic line at the end
# search.add_command(list_items, name="list")
