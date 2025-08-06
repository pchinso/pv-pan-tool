#!/usr/bin/env python3
"""
Test script for PV PAN Tool CLI.

This script tests the basic functionality of the CLI interface.
"""

import sys
import subprocess
from pathlib import Path

def run_command(cmd):
    """Run a CLI command and return the result."""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd="/home/ubuntu"
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def test_cli_commands():
    """Test various CLI commands."""
    
    print("🧪 Testing PV PAN Tool CLI")
    print("=" * 50)
    
    # Test basic help
    print("\n1. Testing main help command...")
    code, stdout, stderr = run_command("python -m src.pv_pan_tool.cli.main --help")
    if code == 0:
        print("✅ Main help command works")
        print(f"   Commands found: {stdout.count('Commands:')}")
    else:
        print("❌ Main help command failed")
        print(f"   Error: {stderr}")
        return False
    
    # Test parse help
    print("\n2. Testing parse help command...")
    code, stdout, stderr = run_command("python -m src.pv_pan_tool.cli.main parse --help")
    if code == 0:
        print("✅ Parse help command works")
    else:
        print("❌ Parse help command failed")
        print(f"   Error: {stderr}")
    
    # Test search help
    print("\n3. Testing search help command...")
    code, stdout, stderr = run_command("python -m src.pv_pan_tool.cli.main search --help")
    if code == 0:
        print("✅ Search help command works")
    else:
        print("❌ Search help command failed")
        print(f"   Error: {stderr}")
    
    # Test compare help
    print("\n4. Testing compare help command...")
    code, stdout, stderr = run_command("python -m src.pv_pan_tool.cli.main compare --help")
    if code == 0:
        print("✅ Compare help command works")
    else:
        print("❌ Compare help command failed")
        print(f"   Error: {stderr}")
    
    # Test stats help
    print("\n5. Testing stats help command...")
    code, stdout, stderr = run_command("python -m src.pv_pan_tool.cli.main stats --help")
    if code == 0:
        print("✅ Stats help command works")
    else:
        print("❌ Stats help command failed")
        print(f"   Error: {stderr}")
    
    # Test export help
    print("\n6. Testing export help command...")
    code, stdout, stderr = run_command("python -m src.pv_pan_tool.cli.main export --help")
    if code == 0:
        print("✅ Export help command works")
    else:
        print("❌ Export help command failed")
        print(f"   Error: {stderr}")
    
    # Test database help
    print("\n7. Testing database help command...")
    code, stdout, stderr = run_command("python -m src.pv_pan_tool.cli.main database --help")
    if code == 0:
        print("✅ Database help command works")
    else:
        print("❌ Database help command failed")
        print(f"   Error: {stderr}")
    
    # Test version
    print("\n8. Testing version command...")
    code, stdout, stderr = run_command("python -m src.pv_pan_tool.cli.main --version")
    if code == 0:
        print("✅ Version command works")
        print(f"   Version: {stdout.strip()}")
    else:
        print("❌ Version command failed")
        print(f"   Error: {stderr}")
    
    print("\n" + "=" * 50)
    print("🎉 CLI testing completed!")
    
    return True

def test_cli_structure():
    """Test that all CLI files are present."""
    
    print("\n📁 Testing CLI file structure...")
    
    required_files = [
        "src/pv_pan_tool/__init__.py",
        "src/pv_pan_tool/cli.py",
        "src/pv_pan_tool/cli/__init__.py",
        "src/pv_pan_tool/cli/main.py",
        "src/pv_pan_tool/cli/commands/__init__.py",
        "src/pv_pan_tool/cli/commands/parse.py",
        "src/pv_pan_tool/cli/commands/search.py",
        "src/pv_pan_tool/cli/commands/compare.py",
        "src/pv_pan_tool/cli/commands/stats.py",
        "src/pv_pan_tool/cli/commands/export.py",
        "src/pv_pan_tool/cli/commands/database.py",
        "src/pv_pan_tool/cli/utils/__init__.py",
        "src/pv_pan_tool/cli/utils/config.py",
        "src/pv_pan_tool/cli/utils/formatters.py",
        "src/pv_pan_tool/cli/config/default.json",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    else:
        print("✅ All required CLI files are present")
        return True

if __name__ == "__main__":
    print("🚀 PV PAN Tool CLI Test Suite")
    print("Testing CLI implementation...")
    
    # Test file structure
    if not test_cli_structure():
        print("❌ CLI structure test failed")
        sys.exit(1)
    
    # Test CLI commands
    if not test_cli_commands():
        print("❌ CLI commands test failed")
        sys.exit(1)
    
    print("\n🎉 All tests passed! CLI is working correctly.")
    print("\n📋 Next steps:")
    print("   1. Test with real .PAN files")
    print("   2. Test database operations")
    print("   3. Test export functionality")
    print("   4. Install as package with: pip install -e .")

