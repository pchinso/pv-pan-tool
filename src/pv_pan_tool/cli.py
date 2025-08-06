"""
CLI entry point for PV PAN Tool.

This module provides the main entry point for the command-line interface
as configured in pyproject.toml.
"""

from .cli.main import main

if __name__ == "__main__":
    main()
