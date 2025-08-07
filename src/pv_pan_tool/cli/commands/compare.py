"""
Compare command for PV PAN Tool CLI.

This module provides functionality to compare multiple PV modules
side by side with detailed parameter analysis.
"""

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...database import PVModuleDatabase
from ..utils.config import get_config
from ..utils.formatters import format_comparison_table, format_csv, format_json

console = Console()


@click.command()
@click.option(
    "--ids", "-i",
    help="Comma-separated list of module IDs to compare"
)
@click.option(
    "--manufacturer", "-m",
    help="Compare modules from specific manufacturers (comma-separated)"
)
@click.option(
    "--model", "-M",
    help="Compare specific models (comma-separated)"
)
@click.option(
    "--top-power", "-p",
    type=int,
    help="Compare top N modules by power rating"
)
@click.option(
    "--top-efficiency", "-e",
    type=int,
    help="Compare top N modules by efficiency"
)
@click.option(
    "--power-range", "-P",
    help="Compare modules in power range (format: min-max, e.g., 500-600)"
)
@click.option(
    "--efficiency-range", "-E",
    help="Compare modules in efficiency range (format: min-max, e.g., 20.5-22.0)"
)
@click.option(
    "--height-min",
    type=float,
    help="Minimum height (mm)"
)
@click.option(
    "--height-max",
    type=float,
    help="Maximum height (mm)"
)
@click.option(
    "--width-min",
    type=float,
    help="Minimum width (mm)"
)
@click.option(
    "--width-max",
    type=float,
    help="Maximum width (mm)"
)
@click.option(
    "--cell-type", "-c",
    type=click.Choice(['monocrystalline', 'polycrystalline', 'thin_film', 'perc', 'bifacial', 'hjt', 'ibc']),
    help="Filter by cell type"
)
@click.option(
    "--limit", "-l",
    type=int,
    default=5,
    help="Maximum number of modules to compare"
)
@click.option(
    "--format", "-f",
    "output_format",
    type=click.Choice(['table', 'json', 'csv']),
    default='table',
    help="Output format"
)
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    help="Save comparison to file"
)
@click.option(
    "--sort-by", "-s",
    type=click.Choice(['pmax_stc', 'efficiency_stc', 'voc_stc', 'isc_stc', 'price_per_watt']),
    default='pmax_stc',
    help="Sort modules by parameter"
)
@click.pass_context
def compare(ctx, ids, manufacturer, model, top_power, top_efficiency,
           power_range, efficiency_range, height_min, height_max, width_min,
           width_max, cell_type, limit, output_format,
           output, sort_by):
    """
    Compare multiple PV modules side by side.

    Compare modules based on various selection criteria and display
    their specifications in a detailed comparison table.

    Examples:
        pv-pan-tool compare --ids 1,2,3
        pv-pan-tool compare --top-power 5
        pv-pan-tool compare --manufacturer "Jinko,Longi" --limit 3
        pv-pan-tool compare --power-range 500-600 --efficiency-range 21-23
        pv-pan-tool compare --top-efficiency 3 --format json
    """
    config = ctx.obj.get('config', {})
    verbose = ctx.obj.get('verbose', False)

    # Get database path
    db_path = get_config('database_path', 'data/database/pv_modules.db',
                        config_file=ctx.obj.get('config_file'))

    try:
        db = PVModuleDatabase(str(db_path))

        # Determine selection method and get modules
        modules = []

        if ids:
            # Compare specific module IDs
            module_ids = [int(id.strip()) for id in ids.split(',')]
            modules = get_modules_by_ids(db, module_ids, verbose)

        elif top_power:
            # Compare top modules by power
            modules = get_top_modules_by_power(db, top_power, cell_type, height_min, height_max, width_min, width_max, verbose)

        elif top_efficiency:
            # Compare top modules by efficiency
            modules = get_top_modules_by_efficiency(db, top_efficiency, cell_type, height_min, height_max, width_min, width_max, verbose)

        elif manufacturer or model:
            # Compare modules by manufacturer/model
            modules = get_modules_by_manufacturer_model(db, manufacturer, model,
                                                       limit, sort_by, cell_type, height_min, height_max, width_min, width_max, verbose)

        elif power_range or efficiency_range:
            # Compare modules in specified ranges
            modules = get_modules_by_ranges(db, power_range, efficiency_range,
                                          limit, sort_by, cell_type, height_min, height_max, width_min, width_max, verbose)
        else:
            console.print("[red]Error: Must specify comparison criteria.[/red]")
            console.print("Use one of: --ids, --top-power, --top-efficiency, --manufacturer, --power-range")
            raise click.Abort()

        if not modules:
            console.print("[yellow]No modules found for comparison.[/yellow]")
            return

        # Limit number of modules for comparison
        if len(modules) > limit:
            modules = modules[:limit]
            console.print(f"[yellow]Limited comparison to {limit} modules[/yellow]")

        console.print(f"[green]Comparing {len(modules)} modules[/green]")

        # Display comparison
        if output_format == 'table':
            show_comparison_table(modules, verbose)
        elif output_format == 'json':
            show_comparison_json(modules)
        elif output_format == 'csv':
            show_comparison_csv(modules)

        # Save to file if requested
        if output:
            save_comparison(modules, output, output_format, verbose)

    except Exception as e:
        console.print(f"[red]Error during comparison: {e}[/red]")
        if verbose:
            console.print_exception()
        raise click.Abort()


def get_modules_by_ids(db, module_ids, verbose):
    """Get modules by specific IDs."""
    modules = []
    for module_id in module_ids:
        module = db.get_module_by_id(module_id)
        if module:
            modules.append(module)
        elif verbose:
            console.print(f"[yellow]Module ID {module_id} not found[/yellow]")
    return modules


def get_top_modules_by_power(db, count, cell_type, height_min, height_max, width_min, width_max, verbose):
    """Get top modules by power rating."""
    criteria = {}
    if cell_type:
        criteria['cell_type'] = cell_type

    return db.search_modules(
        cell_type=cell_type,
        min_height=height_min,
        max_height=height_max,
        min_width=width_min,
        max_width=width_max,
        limit=count
    )


def get_top_modules_by_efficiency(db, count, cell_type, height_min, height_max, width_min, width_max, verbose):
    """Get top modules by efficiency."""
    criteria = {}
    if cell_type:
        criteria['cell_type'] = cell_type

    return db.search_modules(
        cell_type=cell_type,
        min_height=height_min,
        max_height=height_max,
        min_width=width_min,
        max_width=width_max,
        limit=count
    )


def get_modules_by_manufacturer_model(db, manufacturer, model, limit, sort_by, cell_type, height_min, height_max, width_min, width_max, verbose):
    """Get modules by manufacturer and/or model."""
    return db.search_modules(
        manufacturer=manufacturer,
        model=model,
        cell_type=cell_type,
        min_height=height_min,
        max_height=height_max,
        min_width=width_min,
        max_width=width_max,
        limit=limit
    )


def get_modules_by_ranges(db, power_range, efficiency_range, limit, sort_by, cell_type, height_min, height_max, width_min, width_max, verbose):
    """Get modules by power and/or efficiency ranges."""
    power_min = power_max = eff_min = eff_max = None

    if power_range:
        try:
            power_min, power_max = map(float, power_range.split('-'))
        except ValueError:
            console.print(f"[red]Invalid power range format: {power_range}[/red]")
            console.print("Use format: min-max (e.g., 500-600)")
            raise click.Abort()

    if efficiency_range:
        try:
            eff_min, eff_max = map(float, efficiency_range.split('-'))
        except ValueError:
            console.print(f"[red]Invalid efficiency range format: {efficiency_range}[/red]")
            console.print("Use format: min-max (e.g., 20.5-22.0)")
            raise click.Abort()

    return db.search_modules(
        min_power=power_min,
        max_power=power_max,
        min_efficiency=eff_min,
        max_efficiency=eff_max,
        min_height=height_min,
        max_height=height_max,
        min_width=width_min,
        max_width=width_max,
        cell_type=cell_type,
        limit=limit
    )


def show_comparison_table(modules, verbose):
    """Display comparison in table format."""
    table = format_comparison_table(modules, "Module Comparison")
    console.print(table)

    if verbose:
        show_comparison_analysis(modules)


def show_comparison_analysis(modules):
    """Show additional analysis of the comparison."""
    if len(modules) < 2:
        return

    # Calculate ranges and averages
    powers = [m.get('pmax_stc') for m in modules if m.get('pmax_stc')]
    efficiencies = [m.get('efficiency_stc') for m in modules if m.get('efficiency_stc')]

    analysis_table = Table(title="Comparison Analysis")
    analysis_table.add_column("Metric", style="cyan")
    analysis_table.add_column("Min", style="red")
    analysis_table.add_column("Max", style="green")
    analysis_table.add_column("Average", style="blue")
    analysis_table.add_column("Range", style="yellow")

    if powers:
        power_min, power_max = min(powers), max(powers)
        power_avg = sum(powers) / len(powers)
        power_range = power_max - power_min
        analysis_table.add_row(
            "Power (W)",
            f"{power_min:.1f}",
            f"{power_max:.1f}",
            f"{power_avg:.1f}",
            f"{power_range:.1f}"
        )

    if efficiencies:
        eff_min, eff_max = min(efficiencies), max(efficiencies)
        eff_avg = sum(efficiencies) / len(efficiencies)
        eff_range = eff_max - eff_min
        analysis_table.add_row(
            "Efficiency (%)",
            f"{eff_min:.2f}",
            f"{eff_max:.2f}",
            f"{eff_avg:.2f}",
            f"{eff_range:.2f}"
        )

    console.print(analysis_table)


def show_comparison_json(modules):
    """Display comparison in JSON format."""
    json_output = format_json(modules, indent=2)
    console.print(json_output)


def show_comparison_csv(modules):
    """Display comparison in CSV format."""
    csv_output = format_csv(modules)
    console.print(csv_output)


def save_comparison(modules, output_path, output_format, verbose):
    """Save comparison to file."""
    try:
        if output_format == 'json':
            content = format_json(modules, indent=2)
        elif output_format == 'csv':
            content = format_csv(modules)
        else:  # table format - save as CSV
            content = format_csv(modules)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        console.print(f"[green]Comparison saved to:[/green] {output_path}")

    except Exception as e:
        console.print(f"[red]Error saving comparison: {e}[/red]")


@click.command()
@click.option(
    "--module-id", "-i",
    type=int,
    help="Show detailed information for specific module ID"
)
@click.option(
    "--manufacturer", "-m",
    help="Show details for modules from manufacturer"
)
@click.option(
    "--model", "-M",
    help="Show details for specific model"
)
@click.option(
    "--include-raw", "-r",
    is_flag=True,
    help="Include raw .PAN file data"
)
@click.pass_context
def details(ctx, module_id, manufacturer, model, include_raw):
    """
    Show detailed information for specific modules.

    Examples:
        pv-pan-tool details --module-id 123
        pv-pan-tool details --manufacturer "Jinko" --model "JKM590N"
        pv-pan-tool details --module-id 123 --include-raw
    """
    config = ctx.obj.get('config', {})
    verbose = ctx.obj.get('verbose', False)

    # Get database path
    db_path = get_config('database_path', 'data/database/pv_modules.db',
                        config_file=ctx.obj.get('config_file'))

    try:
        db = PVModuleDatabase(str(db_path))

        if module_id:
            # Show details for specific module
            module = db.get_module_by_id(module_id)
            if not module:
                console.print(f"[red]Module with ID {module_id} not found.[/red]")
                return

            show_module_details(module, include_raw, db)

        elif manufacturer or model:
            # Show details for modules matching criteria
            modules = db.search_modules(
                manufacturer=manufacturer,
                model=model,
                limit=10
            )

            if not modules:
                console.print("[yellow]No modules found matching criteria.[/yellow]")
                return

            for i, module in enumerate(modules):
                if i > 0:
                    console.print()  # Add spacing between modules
                show_module_details(module, include_raw, db)
        else:
            console.print("[red]Error: Must specify --module-id or --manufacturer/--model.[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error showing details: {e}[/red]")
        if verbose:
            console.print_exception()
        raise click.Abort()


def show_module_details(module, include_raw, db):
    """Show detailed information for a single module."""
    # Basic information panel
    basic_info = f"""
ID: {module.get('id', 'N/A')}
Manufacturer: {module.get('manufacturer', 'N/A')}
Model: {module.get('model', 'N/A')}
Series: {module.get('series', 'N/A')}
"""

    basic_panel = Panel(
        basic_info.strip(),
        title="Basic Information",
        border_style="blue"
    )
    console.print(basic_panel)

    # Electrical parameters table
    elec_table = Table(title="Electrical Parameters (STC)")
    elec_table.add_column("Parameter", style="cyan")
    elec_table.add_column("Value", style="green")
    elec_table.add_column("Unit", style="dim")

    elec_params = [
        ("Maximum Power", module.get('pmax_stc'), "W"),
        ("Voltage at Pmax", module.get('vmp_stc'), "V"),
        ("Current at Pmax", module.get('imp_stc'), "A"),
        ("Open Circuit Voltage", module.get('voc_stc'), "V"),
        ("Short Circuit Current", module.get('isc_stc'), "A"),
        ("Efficiency", module.get('efficiency_stc'), "%"),
    ]

    for param, value, unit in elec_params:
        if value is not None:
            if isinstance(value, float):
                value_str = f"{value:.2f}"
            else:
                value_str = str(value)
            elec_table.add_row(param, value_str, unit)

    console.print(elec_table)

    # Physical parameters table
    phys_table = Table(title="Physical Parameters")
    phys_table.add_column("Parameter", style="cyan")
    phys_table.add_column("Value", style="green")
    phys_table.add_column("Unit", style="dim")

    phys_params = [
        ("Length", module.get('length'), "mm"),
        ("Width", module.get('width'), "mm"),
        ("Thickness", module.get('thickness'), "mm"),
        ("Weight", module.get('weight'), "kg"),
        ("Cell Type", module.get('cell_type'), ""),
        ("Module Type", module.get('module_type'), ""),
        ("Cells in Series", module.get('cells_in_series'), ""),
        ("Total Cells", module.get('total_cells'), ""),
    ]

    for param, value, unit in phys_params:
        if value is not None:
            if isinstance(value, float) and unit in ['mm', 'kg']:
                value_str = f"{value:.1f}"
            else:
                value_str = str(value)
            phys_table.add_row(param, value_str, unit)

    console.print(phys_table)

    # File information
    file_info = f"""
File Path: {module.get('file_path', 'N/A')}
File Name: {module.get('file_name', 'N/A')}
File Size: {module.get('file_size', 'N/A')} bytes
Parsed At: {module.get('parsed_at', 'N/A')}
"""

    file_panel = Panel(
        file_info.strip(),
        title="File Information",
        border_style="yellow"
    )
    console.print(file_panel)

    # Raw data if requested
    if include_raw:
        raw_data = db.get_raw_pan_data(module.get('id'))
        if raw_data:
            raw_panel = Panel(
                raw_data[:1000] + "..." if len(raw_data) > 1000 else raw_data,
                title="Raw .PAN File Data (first 1000 chars)",
                border_style="dim"
            )
            console.print(raw_panel)


# Remove the problematic line at the end
# compare.add_command(details, name="details")
