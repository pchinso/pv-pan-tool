"""
Test script for the PAN file parser.
This script tests the parser with your real .PAN files directory.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from pv_pan_tool.parser import PANFileParser


def main():
    """Main test function."""
    print("=" * 60)
    print("           PV PAN Tool - Parser Test")
    print("=" * 60)
    print()

    # Your specific directory
    base_directory = r"C:\Users\slpcs.ABG\OneDrive - Cox\PAN_catalog\01. Modulos"

    print(f"Base directory: {base_directory}")
    print()

    # Check if directory exists
    if not Path(base_directory).exists():
        print(f"❌ ERROR: Directory does not exist: {base_directory}")
        print("Please check the path and try again.")
        return

    print("✅ Directory exists, initializing parser...")
    print()

    try:
        # Initialize parser
        parser = PANFileParser(base_directory)
        print("✅ Parser initialized successfully")

        # Scan for files
        print("🔍 Scanning for .PAN files...")
        all_files = parser.scan_directory()
        print(f"📁 Found {len(all_files)} .PAN files total")

        if len(all_files) == 0:
            print("⚠️  No .PAN files found in the directory")
            return

        # Show first few files found
        print()
        print("📋 First 10 files found:")
        for i, file_path in enumerate(all_files, 1):
            relative_path = file_path.relative_to(Path(base_directory))
            print(f"  {i:2d}. {relative_path}")


        # Check which files need processing
        new_files = parser.get_new_files(all_files)
        print()
        print(f"📊 Files to process: {len(new_files)} new/modified files")

        if len(new_files) == 0:
            print("✅ All files have been processed already")
            return

        # Test with all new files
        test_files = new_files
        print()
        print(f"🧪 Testing with first {len(test_files)} files:")
        print()

        results = {}

        for i, file_path in enumerate(test_files, 1):
            print(f"Processing {i}/{len(test_files)}: {file_path.name}")

            # Extract manufacturer and model from path
            manufacturer, model = parser.extract_manufacturer_model_from_path(file_path)
            print(f"  📂 Manufacturer: {manufacturer}")
            print(f"  📦 Model: {model}")

            # Parse the file
            result = parser.parse_file(file_path)
            results[str(file_path)] = result

            if result.success:
                module = result.module
                print(f"  ✅ SUCCESS! Extracted {result.parameters_extracted} parameters")

                # Show key parameters
                if module.electrical_params.pmax_stc:
                    print(f"     🔋 Power: {module.electrical_params.pmax_stc} W")
                if module.electrical_params.voc_stc:
                    print(f"     ⚡ Voc: {module.electrical_params.voc_stc} V")
                if module.electrical_params.isc_stc:
                    print(f"     ⚡ Isc: {module.electrical_params.isc_stc} A")
                if module.physical_params.height and module.physical_params.width:
                    print(f"     📏 Dimensions: {module.physical_params.height} x {module.physical_params.width} mm")
                if module.efficiency_stc:
                    print(f"     📈 Efficiency: {module.efficiency_stc:.2f}%")

            else:
                print(f"  ❌ FAILED: {result.error_message}")

            print()

        # Show statistics
        stats = parser.get_statistics(results)
        print("=" * 60)
        print("                    STATISTICS")
        print("=" * 60)
        print(f"Total files processed: {stats['total_files']}")
        print(f"Successful: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        print(f"Average parameters extracted: {stats['avg_parameters_extracted']:.1f}")
        print()

        # Show registry info
        print("📝 Registry information:")
        print(f"   Total files in registry: {len(parser.registry)}")
        print(f"   Registry file: {parser.registry_file}")
        print()

        print("✅ Test completed successfully!")
        print()
        print("🚀 Next steps:")
        print("   1. Review the results above")
        print("   2. If satisfied, process all files with: parser.parse_directory()")
        print("   3. Create database and comparison tools")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
