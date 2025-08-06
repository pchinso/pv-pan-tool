"""
Configuration management for PV PAN Tool CLI.

This module handles loading, saving, and managing configuration settings
for the CLI application.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import click


def get_config_path(config_file: Optional[str] = None) -> Path:
    """
    Get the path to the configuration file.
    
    Args:
        config_file: Optional path to a specific config file
        
    Returns:
        Path to the configuration file
    """
    if config_file:
        return Path(config_file)
    
    # Try user config directory first
    user_config_dir = Path.home() / ".config" / "pv-pan-tool"
    user_config_file = user_config_dir / "config.json"
    
    if user_config_file.exists():
        return user_config_file
    
    # Fall back to default config in package
    package_dir = Path(__file__).parent.parent
    default_config = package_dir / "config" / "default.json"
    
    return default_config


def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file.
    
    Args:
        config_file: Optional path to a specific config file
        
    Returns:
        Configuration dictionary
    """
    config_path = get_config_path(config_file)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        click.echo(f"Configuration file not found: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        click.echo(f"Error parsing configuration file: {e}")
        return {}


def save_config(config: Dict[str, Any], config_file: Optional[str] = None) -> bool:
    """
    Save configuration to file.
    
    Args:
        config: Configuration dictionary to save
        config_file: Optional path to a specific config file
        
    Returns:
        True if successful, False otherwise
    """
    if config_file:
        config_path = Path(config_file)
    else:
        # Save to user config directory
        user_config_dir = Path.home() / ".config" / "pv-pan-tool"
        user_config_dir.mkdir(parents=True, exist_ok=True)
        config_path = user_config_dir / "config.json"
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        click.echo(f"Error saving configuration: {e}")
        return False


def get_config(key: str, default: Any = None, config_file: Optional[str] = None) -> Any:
    """
    Get a specific configuration value.
    
    Args:
        key: Configuration key (supports dot notation for nested keys)
        default: Default value if key is not found
        config_file: Optional path to a specific config file
        
    Returns:
        Configuration value or default
    """
    config = load_config(config_file)
    
    # Support dot notation for nested keys
    keys = key.split('.')
    value = config
    
    try:
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError):
        return default


def set_config(key: str, value: Any, config_file: Optional[str] = None) -> bool:
    """
    Set a configuration value.
    
    Args:
        key: Configuration key (supports dot notation for nested keys)
        value: Value to set
        config_file: Optional path to a specific config file
        
    Returns:
        True if successful, False otherwise
    """
    config = load_config(config_file)
    
    # Support dot notation for nested keys
    keys = key.split('.')
    current = config
    
    # Navigate to the parent of the target key
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    # Set the value
    current[keys[-1]] = value
    
    return save_config(config, config_file)


def init_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Initialize configuration, creating default if needed.
    
    Args:
        config_file: Optional path to a specific config file
        
    Returns:
        Configuration dictionary
    """
    config = load_config(config_file)
    
    # If no config exists, create default user config
    if not config and not config_file:
        # Load default config from package
        package_dir = Path(__file__).parent.parent
        default_config_path = package_dir / "config" / "default.json"
        
        try:
            with open(default_config_path, 'r', encoding='utf-8') as f:
                default_config = json.load(f)
            
            # Save as user config
            save_config(default_config)
            config = default_config
            
        except Exception as e:
            click.echo(f"Warning: Could not create default configuration: {e}")
    
    # Override with environment variables
    config = override_with_env_vars(config)
    
    return config


def override_with_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Override configuration with environment variables.
    
    Environment variables should be prefixed with PV_PAN_TOOL_
    and use underscores instead of dots.
    
    Args:
        config: Base configuration dictionary
        
    Returns:
        Configuration with environment variable overrides
    """
    env_prefix = "PV_PAN_TOOL_"
    
    for env_key, env_value in os.environ.items():
        if env_key.startswith(env_prefix):
            # Convert env key to config key
            config_key = env_key[len(env_prefix):].lower().replace('_', '.')
            
            # Try to parse as JSON for complex values
            try:
                parsed_value = json.loads(env_value)
            except json.JSONDecodeError:
                parsed_value = env_value
            
            # Set in config using dot notation
            keys = config_key.split('.')
            current = config
            
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            current[keys[-1]] = parsed_value
    
    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration values.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_keys = [
        'pan_directory',
        'database_path',
        'output_directory'
    ]
    
    for key in required_keys:
        if key not in config:
            click.echo(f"Missing required configuration key: {key}")
            return False
    
    # Validate paths exist or can be created
    pan_dir = Path(config['pan_directory'])
    if not pan_dir.exists():
        click.echo(f"PAN directory does not exist: {pan_dir}")
        return False
    
    # Ensure output directory can be created
    output_dir = Path(config['output_directory'])
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        click.echo(f"Cannot create output directory: {e}")
        return False
    
    return True

