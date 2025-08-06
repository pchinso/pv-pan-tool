"""
Statistics command for PV PAN Tool CLI.

This module provides statistical analysis and reporting
functionality for the PV module database.
"""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.bar import Bar

from ...database import PVModuleDatabase
from ..utils.config import get_config
from ..utils.formatters import format_statistics_table, format_json

console = Console()


@click.command()
@click.option(
    "--by-manufacturer", "-m",
    is_flag=True,
    help="Show statistics grouped by manufacturer"
)
@click.option(
    "--by-cell-type", "-c",
    is_flag=True,
    help="Show statistics grouped by cell type"
)
@click.option(
    "--by-module-type", "-t",
    is_flag=True,
    help="Show statistics grouped by module type"
)
@click.option(
    "--power-ranges", "-p",
    is_flag=True,
    help="Show power range distribution"
)
@click.option(
    "--efficiency-ranges", "-e",
    is_flag=True,
    help="Show efficiency range distribution"
)
@click.option(
    "--top-manufacturers", "-T",
    type=int,
    default=10,
    help="Show top N manufacturers by module count"
)
@click.option(
    "--format", "-f",
    "output_format",
    type=click.Choice(['table', 'json']),
    default='table',
    help="Output format"
)
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    help="Save statistics to file"
)
@click.pass_context
def stats(ctx, by_manufacturer, by_cell_type, by_module_type, 
         power_ranges, efficiency_ranges, top_manufacturers, 
         output_format, output):
    """
    Show database statistics and analysis.
    
    Display various statistical analyses of the PV module database
    including distributions, ranges, and summaries.
    
    Examples:
        pv-pan-tool stats
        pv-pan-tool stats --by-manufacturer
        pv-pan-tool stats --power-ranges --efficiency-ranges
        pv-pan-tool stats --by-cell-type --format json
        pv-pan-tool stats --top-manufacturers 5
    """
    config = ctx.obj.get('config', {})
    verbose = ctx.obj.get('verbose', False)
    
    # Get database path
    db_path = get_config('database_path', 'data/database/pv_modules.db', 
                        config_file=ctx.obj.get('config_file'))
    
    try:
        db = PVModuleDatabase(str(db_path))
        
        # Get basic statistics
        with console.status("[bold green]Calculating statistics..."):
            basic_stats = db.get_statistics()
        
        if output_format == 'json':
            show_stats_json(db, basic_stats, by_manufacturer, by_cell_type, 
                          by_module_type, power_ranges, efficiency_ranges)
        else:
            show_stats_table(db, basic_stats, by_manufacturer, by_cell_type, 
                           by_module_type, power_ranges, efficiency_ranges, 
                           top_manufacturers, verbose)
        
        # Save to file if requested
        if output:
            save_statistics(db, basic_stats, output, output_format, verbose)
            
    except Exception as e:
        console.print(f"[red]Error generating statistics: {e}[/red]")
        if verbose:
            console.print_exception()
        raise click.Abort()


def show_stats_table(db, basic_stats, by_manufacturer, by_cell_type, 
                    by_module_type, power_ranges, efficiency_ranges, 
                    top_manufacturers, verbose):
    """Display statistics in table format."""
    
    # Basic statistics panel
    show_basic_statistics(basic_stats)
    
    # Conditional detailed statistics
    if by_manufacturer or not any([by_cell_type, by_module_type, power_ranges, efficiency_ranges]):
        show_manufacturer_statistics(db, top_manufacturers)
    
    if by_cell_type:
        show_cell_type_statistics(db)
    
    if by_module_type:
        show_module_type_statistics(db)
    
    if power_ranges:
        show_power_range_statistics(db)
    
    if efficiency_ranges:
        show_efficiency_range_statistics(db)
    
    if verbose:
        show_additional_statistics(db)


def show_basic_statistics(stats):
    """Show basic database statistics."""
    basic_info = f"""
Total Modules: {stats.get('total_modules', 0):,}
Total Manufacturers: {stats.get('total_manufacturers', 0)}
Total Models: {stats.get('total_models', 0)}

Power Range: {stats.get('power_range', {}).get('min', 0):.1f}W - {stats.get('power_range', {}).get('max', 0):.1f}W
Average Power: {stats.get('power_range', {}).get('avg', 0):.1f}W

Efficiency Range: {stats.get('efficiency_range', {}).get('min', 0):.2f}% - {stats.get('efficiency_range', {}).get('max', 0):.2f}%
Average Efficiency: {stats.get('efficiency_range', {}).get('avg', 0):.2f}%
"""
    
    panel = Panel(
        basic_info.strip(),
        title="Database Overview",
        border_style="green"
    )
    console.print(panel)


def show_manufacturer_statistics(db, top_count):
    """Show manufacturer statistics."""
    manufacturers = db.get_manufacturer_statistics(limit=top_count)
    
    if not manufacturers:
        return
    
    table = Table(title=f"Top {top_count} Manufacturers")
    table.add_column("Rank", style="cyan", width=4)
    table.add_column("Manufacturer", style="blue", width=20)
    table.add_column("Modules", style="green", justify="right", width=8)
    table.add_column("Avg Power (W)", style="red", justify="right", width=12)
    table.add_column("Avg Efficiency (%)", style="magenta", justify="right", width=15)
    table.add_column("Power Range", style="yellow", width=15)
    
    for i, mfg in enumerate(manufacturers, 1):
        power_range = f"{mfg.get('min_power', 0):.0f}-{mfg.get('max_power', 0):.0f}W"
        table.add_row(
            str(i),
            mfg.get('manufacturer', '')[:20],
            str(mfg.get('module_count', 0)),
            f"{mfg.get('avg_power', 0):.1f}",
            f"{mfg.get('avg_efficiency', 0):.2f}",
            power_range
        )
    
    console.print(table)


def show_cell_type_statistics(db):
    """Show cell type distribution."""
    cell_types = db.get_cell_type_statistics()
    
    if not cell_types:
        return
    
    table = Table(title="Cell Type Distribution")
    table.add_column("Cell Type", style="cyan", width=15)
    table.add_column("Count", style="green", justify="right", width=8)
    table.add_column("Percentage", style="blue", justify="right", width=10)
    table.add_column("Avg Power (W)", style="red", justify="right", width=12)
    table.add_column("Avg Efficiency (%)", style="magenta", justify="right", width=15)
    
    total_modules = sum(ct.get('count', 0) for ct in cell_types)
    
    for cell_type in cell_types:
        count = cell_type.get('count', 0)
        percentage = (count / total_modules * 100) if total_modules > 0 else 0
        
        table.add_row(
            cell_type.get('cell_type', '').title(),
            str(count),
            f"{percentage:.1f}%",
            f"{cell_type.get('avg_power', 0):.1f}",
            f"{cell_type.get('avg_efficiency', 0):.2f}"
        )
    
    console.print(table)


def show_module_type_statistics(db):
    """Show module type distribution."""
    module_types = db.get_module_type_statistics()
    
    if not module_types:
        return
    
    table = Table(title="Module Type Distribution")
    table.add_column("Module Type", style="cyan", width=15)
    table.add_column("Count", style="green", justify="right", width=8)
    table.add_column("Percentage", style="blue", justify="right", width=10)
    table.add_column("Avg Power (W)", style="red", justify="right", width=12)
    
    total_modules = sum(mt.get('count', 0) for mt in module_types)
    
    for module_type in module_types:
        count = module_type.get('count', 0)
        percentage = (count / total_modules * 100) if total_modules > 0 else 0
        
        table.add_row(
            module_type.get('module_type', '').title(),
            str(count),
            f"{percentage:.1f}%",
            f"{module_type.get('avg_power', 0):.1f}"
        )
    
    console.print(table)


def show_power_range_statistics(db):
    """Show power range distribution."""
    power_ranges = db.get_power_range_distribution()
    
    if not power_ranges:
        return
    
    table = Table(title="Power Range Distribution")
    table.add_column("Power Range (W)", style="cyan", width=15)
    table.add_column("Count", style="green", justify="right", width=8)
    table.add_column("Percentage", style="blue", justify="right", width=10)
    table.add_column("Visual", style="yellow", width=20)
    
    total_modules = sum(pr.get('count', 0) for pr in power_ranges)
    max_count = max(pr.get('count', 0) for pr in power_ranges) if power_ranges else 1
    
    for power_range in power_ranges:
        count = power_range.get('count', 0)
        percentage = (count / total_modules * 100) if total_modules > 0 else 0
        
        # Create visual bar
        bar_width = int((count / max_count) * 15) if max_count > 0 else 0
        visual_bar = "█" * bar_width + "░" * (15 - bar_width)
        
        range_str = f"{power_range.get('min_power', 0):.0f}-{power_range.get('max_power', 0):.0f}"
        
        table.add_row(
            range_str,
            str(count),
            f"{percentage:.1f}%",
            visual_bar
        )
    
    console.print(table)


def show_efficiency_range_statistics(db):
    """Show efficiency range distribution."""
    eff_ranges = db.get_efficiency_range_distribution()
    
    if not eff_ranges:
        return
    
    table = Table(title="Efficiency Range Distribution")
    table.add_column("Efficiency Range (%)", style="cyan", width=18)
    table.add_column("Count", style="green", justify="right", width=8)
    table.add_column("Percentage", style="blue", justify="right", width=10)
    table.add_column("Visual", style="yellow", width=20)
    
    total_modules = sum(er.get('count', 0) for er in eff_ranges)
    max_count = max(er.get('count', 0) for er in eff_ranges) if eff_ranges else 1
    
    for eff_range in eff_ranges:
        count = eff_range.get('count', 0)
        percentage = (count / total_modules * 100) if total_modules > 0 else 0
        
        # Create visual bar
        bar_width = int((count / max_count) * 15) if max_count > 0 else 0
        visual_bar = "█" * bar_width + "░" * (15 - bar_width)
        
        range_str = f"{eff_range.get('min_efficiency', 0):.1f}-{eff_range.get('max_efficiency', 0):.1f}"
        
        table.add_row(
            range_str,
            str(count),
            f"{percentage:.1f}%",
            visual_bar
        )
    
    console.print(table)


def show_additional_statistics(db):
    """Show additional detailed statistics."""
    # Technology trends
    tech_stats = db.get_technology_statistics()
    
    if tech_stats:
        tech_info = f"""
Most Common Cell Type: {tech_stats.get('most_common_cell_type', 'N/A')}
Most Common Module Type: {tech_stats.get('most_common_module_type', 'N/A')}
Average Module Area: {tech_stats.get('avg_area', 0):.2f} m²
Average Power Density: {tech_stats.get('avg_power_density', 0):.1f} W/m²
"""
        
        tech_panel = Panel(
            tech_info.strip(),
            title="Technology Statistics",
            border_style="blue"
        )
        console.print(tech_panel)


def show_stats_json(db, basic_stats, by_manufacturer, by_cell_type, 
                   by_module_type, power_ranges, efficiency_ranges):
    """Display statistics in JSON format."""
    stats_data = {
        'basic_statistics': basic_stats
    }
    
    if by_manufacturer:
        stats_data['manufacturer_statistics'] = db.get_manufacturer_statistics()
    
    if by_cell_type:
        stats_data['cell_type_statistics'] = db.get_cell_type_statistics()
    
    if by_module_type:
        stats_data['module_type_statistics'] = db.get_module_type_statistics()
    
    if power_ranges:
        stats_data['power_range_distribution'] = db.get_power_range_distribution()
    
    if efficiency_ranges:
        stats_data['efficiency_range_distribution'] = db.get_efficiency_range_distribution()
    
    json_output = format_json(stats_data, indent=2)
    console.print(json_output)


def save_statistics(db, basic_stats, output_path, output_format, verbose):
    """Save statistics to file."""
    try:
        # Collect all statistics
        stats_data = {
            'basic_statistics': basic_stats,
            'manufacturer_statistics': db.get_manufacturer_statistics(),
            'cell_type_statistics': db.get_cell_type_statistics(),
            'module_type_statistics': db.get_module_type_statistics(),
            'power_range_distribution': db.get_power_range_distribution(),
            'efficiency_range_distribution': db.get_efficiency_range_distribution(),
        }
        
        if output_format == 'json':
            content = format_json(stats_data, indent=2)
        else:
            # Convert to CSV-like format
            content = convert_stats_to_csv(stats_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        console.print(f"[green]Statistics saved to:[/green] {output_path}")
        
    except Exception as e:
        console.print(f"[red]Error saving statistics: {e}[/red]")


def convert_stats_to_csv(stats_data):
    """Convert statistics data to CSV format."""
    lines = []
    
    # Basic statistics
    lines.append("Basic Statistics")
    lines.append("Metric,Value")
    basic = stats_data.get('basic_statistics', {})
    lines.append(f"Total Modules,{basic.get('total_modules', 0)}")
    lines.append(f"Total Manufacturers,{basic.get('total_manufacturers', 0)}")
    lines.append(f"Min Power,{basic.get('power_range', {}).get('min', 0)}")
    lines.append(f"Max Power,{basic.get('power_range', {}).get('max', 0)}")
    lines.append(f"Avg Power,{basic.get('power_range', {}).get('avg', 0)}")
    lines.append("")
    
    # Manufacturer statistics
    lines.append("Manufacturer Statistics")
    lines.append("Manufacturer,Module Count,Avg Power,Avg Efficiency")
    for mfg in stats_data.get('manufacturer_statistics', []):
        lines.append(f"{mfg.get('manufacturer', '')},{mfg.get('module_count', 0)},{mfg.get('avg_power', 0):.1f},{mfg.get('avg_efficiency', 0):.2f}")
    lines.append("")
    
    # Cell type statistics
    lines.append("Cell Type Statistics")
    lines.append("Cell Type,Count,Avg Power,Avg Efficiency")
    for ct in stats_data.get('cell_type_statistics', []):
        lines.append(f"{ct.get('cell_type', '')},{ct.get('count', 0)},{ct.get('avg_power', 0):.1f},{ct.get('avg_efficiency', 0):.2f}")
    
    return '\n'.join(lines)

