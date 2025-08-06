"""
Main CLI entry point for PV PAN Tool.

This module provides the main command-line interface for the PV PAN Tool,
allowing users to parse .PAN files, query the database, compare modules,
and export data.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..database import PVModuleDatabase
from .commands import parse, search, compare, export, stats, database
from .utils.config import get_config, init_config

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="pv-pan-tool")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--config-file", type=click.Path(), help="Path to configuration file")
@click.pass_context
def main(ctx, verbose, config_file):
    """
    PV PAN Tool - Parse and compare photovoltaic module specifications.
    
    A comprehensive tool for parsing .PAN files, building a searchable database,
    and comparing solar panel specifications.
    
    Examples:
        pv-pan-tool parse --input-dir "C:\\path\\to\\pan\\files"
        pv-pan-tool search --manufacturer "Jinko" --power-min 500
        pv-pan-tool compare --top-power 5
        pv-pan-tool export --format csv --output modules.csv
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Store global options in context
    ctx.obj['verbose'] = verbose
    ctx.obj['config_file'] = config_file
    
    # Initialize configuration
    try:
        config = init_config(config_file)
        ctx.obj['config'] = config
    except Exception as e:
        if verbose:
            console.print(f"[yellow]Warning: Could not load configuration: {e}[/yellow]")
        ctx.obj['config'] = {}
    
    # Show welcome message for main command
    if ctx.invoked_subcommand is None:
        show_welcome()


def show_welcome():
    """Show welcome message and basic usage information."""
    welcome_text = Text()
    welcome_text.append("PV PAN Tool", style="bold blue")
    welcome_text.append(" - Photovoltaic Module Analysis Tool\n\n", style="blue")
    welcome_text.append("Parse .PAN files, build databases, and compare solar panel specifications.\n\n")
    welcome_text.append("Quick Start:\n", style="bold")
    welcome_text.append("  pv-pan-tool parse                    # Parse .PAN files\n")
    welcome_text.append("  pv-pan-tool search --help            # Search modules\n")
    welcome_text.append("  pv-pan-tool compare --help           # Compare modules\n")
    welcome_text.append("  pv-pan-tool --help                   # Show all commands\n")
    
    panel = Panel(
        welcome_text,
        title="Welcome to PV PAN Tool",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)


@main.command()
@click.pass_context
def info(ctx):
    """Show system information and database statistics."""
    config = ctx.obj.get('config', {})
    verbose = ctx.obj.get('verbose', False)
    
    # Database information
    try:
        db_path = config.get('database_path', 'data/database/pv_modules.db')
        db = PVModuleDatabase(db_path)
        stats = db.get_statistics()
        
        info_text = Text()
        info_text.append("System Information\n", style="bold blue")
        info_text.append(f"Database Path: {db_path}\n")
        info_text.append(f"Total Modules: {stats['total_modules']}\n")
        info_text.append(f"Total Manufacturers: {stats['total_manufacturers']}\n")
        info_text.append(f"Power Range: {stats['min_power']:.1f}W - {stats['max_power']:.1f}W\n")
        info_text.append(f"Efficiency Range: {stats['min_efficiency']:.1f}% - {stats['max_efficiency']:.1f}%\n")
        
        if verbose:
            info_text.append(f"\nConfiguration:\n", style="bold")
            for key, value in config.items():
                info_text.append(f"  {key}: {value}\n")
        
        panel = Panel(
            info_text,
            title="PV PAN Tool Information",
            border_style="green"
        )
        console.print(panel)
        
    except Exception as e:
        console.print(f"[red]Error getting system information: {e}[/red]")


# Register command groups
main.add_command(parse)
main.add_command(search)
main.add_command(compare)
main.add_command(stats)
main.add_command(export)
main.add_command(database)


if __name__ == "__main__":
    main()

