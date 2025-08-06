"""
Database management command for PV PAN Tool CLI.

This module provides database management functionality
including backup, restore, clear, and maintenance operations.
"""

import click
import shutil
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

from ...database import PVModuleDatabase
from ..utils.config import get_config, set_config

console = Console()


@click.group()
@click.pass_context
def database(ctx):
    """
    Database management operations.
    
    Manage the PV module database including backup, restore,
    clear operations, and maintenance tasks.
    """
    pass


@database.command()
@click.pass_context
def info(ctx):
    """Show database information and statistics."""
    config = ctx.obj.get('config', {})
    verbose = ctx.obj.get('verbose', False)
    
    # Get database path
    db_path = get_config('database_path', 'data/database/pv_modules.db', 
                        config_file=ctx.obj.get('config_file'))
    
    try:
        db_file = Path(db_path)
        
        # Database file information
        if db_file.exists():
            file_size = db_file.stat().st_size
            modified_time = datetime.fromtimestamp(db_file.stat().st_mtime)
            
            file_info = f"""
Database Path: {db_path}
File Size: {format_file_size(file_size)}
Last Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        else:
            file_info = f"""
Database Path: {db_path}
Status: File does not exist
"""
        
        file_panel = Panel(
            file_info.strip(),
            title="Database File Information",
            border_style="blue"
        )
        console.print(file_panel)
        
        # Database statistics (if file exists)
        if db_file.exists():
            db = PVModuleDatabase(str(db_path))
            stats = db.get_statistics()
            
            stats_info = f"""
Total Modules: {stats.get('total_modules', 0):,}
Total Manufacturers: {stats.get('total_manufacturers', 0)}
Total Models: {stats.get('total_models', 0)}

Power Range: {stats.get('power_range', {}).get('min', 0):.1f}W - {stats.get('power_range', {}).get('max', 0):.1f}W
Efficiency Range: {stats.get('efficiency_range', {}).get('min', 0):.2f}% - {stats.get('efficiency_range', {}).get('max', 0):.2f}%
"""
            
            stats_panel = Panel(
                stats_info.strip(),
                title="Database Statistics",
                border_style="green"
            )
            console.print(stats_panel)
            
            if verbose:
                show_table_info(db)
        
    except Exception as e:
        console.print(f"[red]Error getting database information: {e}[/red]")
        if verbose:
            console.print_exception()


@database.command()
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    help="Backup file path (default: auto-generated)"
)
@click.option(
    "--compress", "-c",
    is_flag=True,
    help="Compress backup file"
)
@click.pass_context
def backup(ctx, output, compress):
    """Create a backup of the database."""
    config = ctx.obj.get('config', {})
    verbose = ctx.obj.get('verbose', False)
    
    # Get database path
    db_path = get_config('database_path', 'data/database/pv_modules.db', 
                        config_file=ctx.obj.get('config_file'))
    
    db_file = Path(db_path)
    
    if not db_file.exists():
        console.print(f"[red]Database file does not exist: {db_path}[/red]")
        raise click.Abort()
    
    try:
        # Generate backup filename if not provided
        if not output:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = Path(get_config('backup_directory', 'backups', 
                                       config_file=ctx.obj.get('config_file')))
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            if compress:
                output = backup_dir / f"pv_modules_backup_{timestamp}.db.gz"
            else:
                output = backup_dir / f"pv_modules_backup_{timestamp}.db"
        
        console.print(f"[blue]Creating backup...[/blue]")
        console.print(f"[blue]Source:[/blue] {db_path}")
        console.print(f"[blue]Destination:[/blue] {output}")
        
        # Create backup
        if compress:
            import gzip
            with open(db_file, 'rb') as f_in:
                with gzip.open(output, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(db_file, output)
        
        # Verify backup
        if output.exists():
            backup_size = output.stat().st_size
            original_size = db_file.stat().st_size
            
            success_info = f"""
Backup created successfully!

Original size: {format_file_size(original_size)}
Backup size: {format_file_size(backup_size)}
Compression: {((original_size - backup_size) / original_size * 100):.1f}% saved
Location: {output}
"""
            
            success_panel = Panel(
                success_info.strip(),
                title="Backup Complete",
                border_style="green"
            )
            console.print(success_panel)
        else:
            console.print("[red]Error: Backup file was not created[/red]")
            
    except Exception as e:
        console.print(f"[red]Error creating backup: {e}[/red]")
        if verbose:
            console.print_exception()
        raise click.Abort()


@database.command()
@click.option(
    "--input", "-i",
    "input_file",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Backup file to restore from"
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Force restore without confirmation"
)
@click.pass_context
def restore(ctx, input_file, force):
    """Restore database from backup."""
    config = ctx.obj.get('config', {})
    verbose = ctx.obj.get('verbose', False)
    
    # Get database path
    db_path = get_config('database_path', 'data/database/pv_modules.db', 
                        config_file=ctx.obj.get('config_file'))
    
    db_file = Path(db_path)
    
    # Confirm restore operation
    if not force:
        if db_file.exists():
            console.print(f"[yellow]Warning: This will overwrite the existing database at {db_path}[/yellow]")
            if not Confirm.ask("Do you want to continue?"):
                console.print("Restore cancelled.")
                return
        else:
            console.print(f"[blue]Restoring database to {db_path}[/blue]")
            if not Confirm.ask("Continue with restore?"):
                console.print("Restore cancelled.")
                return
    
    try:
        # Create database directory if needed
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        console.print(f"[blue]Restoring from backup...[/blue]")
        console.print(f"[blue]Source:[/blue] {input_file}")
        console.print(f"[blue]Destination:[/blue] {db_path}")
        
        # Restore from backup
        if input_file.suffix == '.gz':
            import gzip
            with gzip.open(input_file, 'rb') as f_in:
                with open(db_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(input_file, db_file)
        
        # Verify restore
        if db_file.exists():
            # Test database integrity
            db = PVModuleDatabase(str(db_path))
            stats = db.get_statistics()
            
            success_info = f"""
Database restored successfully!

Modules: {stats.get('total_modules', 0):,}
Manufacturers: {stats.get('total_manufacturers', 0)}
File size: {format_file_size(db_file.stat().st_size)}
"""
            
            success_panel = Panel(
                success_info.strip(),
                title="Restore Complete",
                border_style="green"
            )
            console.print(success_panel)
        else:
            console.print("[red]Error: Database file was not restored[/red]")
            
    except Exception as e:
        console.print(f"[red]Error restoring database: {e}[/red]")
        if verbose:
            console.print_exception()
        raise click.Abort()


@database.command()
@click.option(
    "--confirm",
    is_flag=True,
    help="Confirm deletion without interactive prompt"
)
@click.pass_context
def clear(ctx, confirm):
    """Clear all data from the database."""
    config = ctx.obj.get('config', {})
    verbose = ctx.obj.get('verbose', False)
    
    # Get database path
    db_path = get_config('database_path', 'data/database/pv_modules.db', 
                        config_file=ctx.obj.get('config_file'))
    
    db_file = Path(db_path)
    
    if not db_file.exists():
        console.print(f"[yellow]Database file does not exist: {db_path}[/yellow]")
        return
    
    # Confirm clear operation
    if not confirm:
        console.print(f"[red]Warning: This will permanently delete all data in the database![/red]")
        console.print(f"[yellow]Database: {db_path}[/yellow]")
        
        if not Confirm.ask("Are you sure you want to clear the database?"):
            console.print("Clear operation cancelled.")
            return
    
    try:
        db = PVModuleDatabase(str(db_path))
        
        # Get current statistics before clearing
        stats = db.get_statistics()
        modules_count = stats.get('total_modules', 0)
        
        console.print(f"[blue]Clearing database with {modules_count:,} modules...[/blue]")
        
        # Clear database
        db.clear_database()
        
        # Verify clearing
        new_stats = db.get_statistics()
        
        if new_stats.get('total_modules', 0) == 0:
            success_info = f"""
Database cleared successfully!

Modules removed: {modules_count:,}
Database is now empty.
"""
            
            success_panel = Panel(
                success_info.strip(),
                title="Clear Complete",
                border_style="green"
            )
            console.print(success_panel)
        else:
            console.print("[red]Error: Database was not completely cleared[/red]")
            
    except Exception as e:
        console.print(f"[red]Error clearing database: {e}[/red]")
        if verbose:
            console.print_exception()
        raise click.Abort()


@database.command()
@click.pass_context
def optimize(ctx):
    """Optimize database performance."""
    config = ctx.obj.get('config', {})
    verbose = ctx.obj.get('verbose', False)
    
    # Get database path
    db_path = get_config('database_path', 'data/database/pv_modules.db', 
                        config_file=ctx.obj.get('config_file'))
    
    try:
        console.print("[blue]Optimizing database...[/blue]")
        
        db = PVModuleDatabase(str(db_path))
        
        # Run optimization operations
        with console.status("[bold green]Running VACUUM..."):
            db.vacuum_database()
        
        with console.status("[bold green]Analyzing tables..."):
            db.analyze_database()
        
        with console.status("[bold green]Rebuilding indexes..."):
            db.rebuild_indexes()
        
        console.print("[green]Database optimization completed![/green]")
        
    except Exception as e:
        console.print(f"[red]Error optimizing database: {e}[/red]")
        if verbose:
            console.print_exception()
        raise click.Abort()


@database.command()
@click.pass_context
def check(ctx):
    """Check database integrity."""
    config = ctx.obj.get('config', {})
    verbose = ctx.obj.get('verbose', False)
    
    # Get database path
    db_path = get_config('database_path', 'data/database/pv_modules.db', 
                        config_file=ctx.obj.get('config_file'))
    
    try:
        console.print("[blue]Checking database integrity...[/blue]")
        
        db = PVModuleDatabase(str(db_path))
        
        # Run integrity checks
        integrity_results = db.check_integrity()
        
        if integrity_results.get('ok', False):
            console.print("[green]Database integrity check passed![/green]")
        else:
            console.print("[red]Database integrity check failed![/red]")
            for error in integrity_results.get('errors', []):
                console.print(f"[red]• {error}[/red]")
        
        # Additional checks
        if verbose:
            orphaned_records = db.find_orphaned_records()
            if orphaned_records:
                console.print(f"[yellow]Found {len(orphaned_records)} orphaned records[/yellow]")
            else:
                console.print("[green]No orphaned records found[/green]")
        
    except Exception as e:
        console.print(f"[red]Error checking database: {e}[/red]")
        if verbose:
            console.print_exception()
        raise click.Abort()


def show_table_info(db):
    """Show detailed table information."""
    try:
        table_info = db.get_table_info()
        
        table = Table(title="Database Tables")
        table.add_column("Table", style="cyan")
        table.add_column("Rows", style="green", justify="right")
        table.add_column("Size", style="blue", justify="right")
        
        for table_data in table_info:
            table.add_row(
                table_data.get('name', ''),
                str(table_data.get('row_count', 0)),
                format_file_size(table_data.get('size_bytes', 0))
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[yellow]Could not get table information: {e}[/yellow]")


def format_file_size(size_bytes):
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

