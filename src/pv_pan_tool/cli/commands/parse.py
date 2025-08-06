"""
Parse command for PV PAN Tool CLI.

This module provides the parse command for parsing .PAN files
and storing the results in the database.
"""

import click
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

from ...parser import PANFileParser
from ...database import PVModuleDatabase
from ..utils.config import get_config

console = Console()


@click.command()
@click.option(
    "--input-dir", "-i",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Directory containing .PAN files to parse"
)
@click.option(
    "--max-files", "-m",
    type=int,
    help="Maximum number of files to process (for testing)"
)
@click.option(
    "--new-only", "-n",
    is_flag=True,
    help="Only process new or modified files"
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Force re-parsing of all files, ignoring registry"
)
@click.option(
    "--output-db", "-o",
    type=click.Path(path_type=Path),
    help="Output database path"
)
@click.option(
    "--dry-run", "-d",
    is_flag=True,
    help="Show what would be parsed without actually parsing"
)
@click.pass_context
def parse(ctx, input_dir, max_files, new_only, force, output_db, dry_run):
    """
    Parse .PAN files and store results in database.
    
    This command scans the specified directory (or default from config)
    for .PAN files, parses them to extract module specifications,
    and stores the results in a SQLite database.
    
    Examples:
        pv-pan-tool parse
        pv-pan-tool parse --input-dir "C:\\path\\to\\pan\\files"
        pv-pan-tool parse --max-files 10 --verbose
        pv-pan-tool parse --new-only
        pv-pan-tool parse --force
    """
    config = ctx.obj.get('config', {})
    verbose = ctx.obj.get('verbose', False)
    
    # Get input directory from option or config
    if not input_dir:
        input_dir = Path(get_config('pan_directory', config_file=ctx.obj.get('config_file')))
        if not input_dir or not input_dir.exists():
            console.print("[red]Error: No input directory specified and no valid default configured.[/red]")
            console.print("Use --input-dir option or configure default with:")
            console.print("  pv-pan-tool config set pan_directory \"C:\\path\\to\\pan\\files\"")
            raise click.Abort()
    
    # Get database path
    if not output_db:
        output_db = Path(get_config('database_path', 'data/database/pv_modules.db', 
                                   config_file=ctx.obj.get('config_file')))
    
    # Get max files from config if not specified
    if not max_files:
        max_files = get_config('max_files_per_batch', config_file=ctx.obj.get('config_file'))
    
    console.print(f"[blue]Parsing .PAN files from:[/blue] {input_dir}")
    console.print(f"[blue]Database:[/blue] {output_db}")
    
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No files will be actually parsed[/yellow]")
    
    try:
        # Initialize parser
        parser = PANFileParser(str(input_dir))
        
        # Get list of files to process
        if force:
            # Clear registry to force re-parsing
            parser.clear_registry()
            console.print("[yellow]Registry cleared - all files will be re-parsed[/yellow]")
        
        # Scan for files
        with console.status("[bold green]Scanning for .PAN files..."):
            all_files = parser.scan_directory()
        
        console.print(f"[green]Found {len(all_files)} total .PAN files[/green]")
        
        if new_only and not force:
            # Filter for new/modified files only
            new_files = parser.get_new_files(all_files)
            files_to_process = new_files
            console.print(f"[blue]New/modified files to process: {len(files_to_process)}[/blue]")
        else:
            files_to_process = all_files
        
        if max_files and len(files_to_process) > max_files:
            files_to_process = files_to_process[:max_files]
            console.print(f"[yellow]Limited to {max_files} files for processing[/yellow]")
        
        if not files_to_process:
            console.print("[green]No files to process.[/green]")
            return
        
        if dry_run:
            show_dry_run_results(files_to_process, verbose)
            return
        
        # Initialize database
        db = PVModuleDatabase(str(output_db))
        
        # Parse files with progress bar
        results = parse_files_with_progress(parser, files_to_process, verbose)
        
        # Store results in database
        store_results_in_database(db, results, verbose)
        
        # Show summary
        show_parsing_summary(results, len(all_files))
        
    except Exception as e:
        console.print(f"[red]Error during parsing: {e}[/red]")
        if verbose:
            console.print_exception()
        raise click.Abort()


def parse_files_with_progress(parser, files_to_process, verbose):
    """Parse files with a progress bar."""
    results = {}
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("Parsing files...", total=len(files_to_process))
        
        for i, file_path in enumerate(files_to_process):
            if verbose:
                progress.update(task, description=f"Parsing {file_path.name}")
            
            try:
                result = parser.parse_file(file_path)
                results[str(file_path)] = result
                
                if verbose and result.success:
                    console.print(f"[green]✓[/green] {file_path.name}")
                elif verbose:
                    console.print(f"[red]✗[/red] {file_path.name}: {result.error_message}")
                    
            except Exception as e:
                if verbose:
                    console.print(f"[red]✗[/red] {file_path.name}: {e}")
            
            progress.update(task, advance=1)
    
    return results


def store_results_in_database(db, results, verbose):
    """Store parsing results in the database."""
    successful_results = [r for r in results.values() if r.success and r.module]
    
    if not successful_results:
        console.print("[yellow]No successful parsing results to store.[/yellow]")
        return
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("Storing in database...", total=len(successful_results))
        
        inserted = 0
        updated = 0
        failed = 0
        
        for result in successful_results:
            try:
                module_id = db.insert_module(result.module, update_if_exists=True)
                if module_id:
                    if db.module_exists(result.module.unique_id):
                        updated += 1
                    else:
                        inserted += 1
                else:
                    failed += 1
                    
            except Exception as e:
                failed += 1
                if verbose:
                    console.print(f"[red]Failed to store module: {e}[/red]")
            
            progress.update(task, advance=1)
    
    # Show database storage summary
    table = Table(title="Database Storage Summary")
    table.add_column("Operation", style="cyan")
    table.add_column("Count", style="green")
    
    table.add_row("Inserted", str(inserted))
    table.add_row("Updated", str(updated))
    table.add_row("Failed", str(failed))
    
    console.print(table)


def show_dry_run_results(files_to_process, verbose):
    """Show what would be processed in dry run mode."""
    table = Table(title="Files to be Processed (Dry Run)")
    table.add_column("File", style="cyan")
    table.add_column("Path", style="dim")
    
    for file_path in files_to_process[:20]:  # Show first 20
        table.add_row(file_path.name, str(file_path.parent))
    
    if len(files_to_process) > 20:
        table.add_row("...", f"... and {len(files_to_process) - 20} more files")
    
    console.print(table)


def show_parsing_summary(results, total_files):
    """Show summary of parsing results."""
    successful = sum(1 for r in results.values() if r.success)
    failed = len(results) - successful
    
    summary_text = f"""
Parsing completed successfully!

Files processed: {len(results)} of {total_files} total
Successful: {successful}
Failed: {failed}
Success rate: {(successful/len(results)*100):.1f}%
"""
    
    panel = Panel(
        summary_text.strip(),
        title="Parsing Summary",
        border_style="green" if failed == 0 else "yellow"
    )
    console.print(panel)

