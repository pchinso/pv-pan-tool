"""
Example usage of the PV Module Database.
This script demonstrates how to use the database for real-world scenarios.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from pv_pan_tool.database import PVModuleDatabase
from pv_pan_tool.parser import PANFileParser


def example_1_populate_database():
    """Example 1: Populate database with parsed modules."""
    print("=" * 60)
    print("           EXAMPLE 1: POPULATE DATABASE")
    print("=" * 60)
    print()

    # Initialize database
    db = PVModuleDatabase()
    print("✅ Database initialized")

    # Initialize parser
    base_directory = r"C:\Users\slpcs.ABG\OneDrive - Cox\PAN_catalog\01. Modulos"
    parser = PANFileParser(base_directory)
    print("✅ Parser initialized")

    # Parse first 10 files and add to database
    print("🔍 Parsing first 10 files...")
    results = parser.parse_directory(max_files=20)

    # Insert into database
    print("💾 Inserting into database...")
    stats = db.bulk_insert_from_parser_results(results)

    print(f"📊 Results:")
    print(f"   Inserted: {stats['inserted']} modules")
    print(f"   Failed: {stats['failed']} modules")
    print(f"   Total processed: {stats['total']} files")
    print()


def example_2_search_and_filter():
    """Example 2: Search and filter modules."""
    print("=" * 60)
    print("           EXAMPLE 2: SEARCH & FILTER")
    print("=" * 60)
    print()

    db = PVModuleDatabase()

    # Search 1: Find all modules from a specific manufacturer
    print("🔍 Search 1: All Longi modules")
    longi_modules = db.search_modules(manufacturer="Longi", limit=5)
    print(f"Found {len(longi_modules)} Longi modules:")
    for module in longi_modules:
        print(f"   📦 {module['model']} - {module['pmax_stc']}W - {module['efficiency_stc']:.1f}%")
    print()

    # Search 2: High-power modules (>500W)
    print("🔍 Search 2: High-power modules (>500W)")
    high_power = db.search_modules(min_power=500, limit=5)
    print(f"Found {len(high_power)} high-power modules:")
    for module in high_power:
        print(f"   ⚡ {module['manufacturer']} {module['model']} - {module['pmax_stc']}W")
    print()

    # Search 3: High-efficiency modules (>22%)
    print("🔍 Search 3: High-efficiency modules (>22%)")
    high_efficiency = db.search_modules(min_efficiency=22, limit=5)
    print(f"Found {len(high_efficiency)} high-efficiency modules:")
    for module in high_efficiency:
        print(f"   📈 {module['manufacturer']} {module['model']} - {module['efficiency_stc']:.2f}%")
    print()

    # Search 4: Specific power range
    print("🔍 Search 4: Modules between 400-450W")
    mid_power = db.search_modules(min_power=400, max_power=450, limit=5)
    print(f"Found {len(mid_power)} modules in 400-450W range:")
    for module in mid_power:
        print(f"   🔋 {module['manufacturer']} {module['model']} - {module['pmax_stc']}W")
    print()


def example_3_statistics_and_analysis():
    """Example 3: Database statistics and analysis."""
    print("=" * 60)
    print("           EXAMPLE 3: STATISTICS & ANALYSIS")
    print("=" * 60)
    print()

    db = PVModuleDatabase()

    # Get overall statistics
    stats = db.get_statistics()

    print("📊 DATABASE STATISTICS:")
    print(f"   Total modules: {stats['total_modules']}")
    print(f"   Total manufacturers: {stats['total_manufacturers']}")
    print()

    print("⚡ POWER STATISTICS:")
    print(f"   Min power: {stats['min_power']:.1f}W")
    print(f"   Max power: {stats['max_power']:.1f}W")
    print(f"   Average power: {stats['avg_power']:.1f}W")
    print()

    print("📈 EFFICIENCY STATISTICS:")
    print(f"   Min efficiency: {stats['min_efficiency']:.2f}%")
    print(f"   Max efficiency: {stats['max_efficiency']:.2f}%")
    print(f"   Average efficiency: {stats['avg_efficiency']:.2f}%")
    print()

    print("🔬 CELL TYPE DISTRIBUTION:")
    for cell_type, count in stats['cell_type_distribution'].items():
        percentage = (count / stats['total_modules']) * 100
        print(f"   {cell_type}: {count} modules ({percentage:.1f}%)")
    print()

    # Get manufacturers list
    manufacturers = db.get_manufacturers()
    print(f"🏭 MANUFACTURERS ({len(manufacturers)} total):")
    for i, manufacturer in enumerate(manufacturers[:10], 1):
        models_count = len(db.get_models_by_manufacturer(manufacturer))
        print(f"   {i:2d}. {manufacturer} ({models_count} models)")
    if len(manufacturers) > 10:
        print(f"       ... and {len(manufacturers) - 10} more manufacturers")
    print()


def example_4_module_comparison():
    """Example 4: Compare specific modules."""
    print("=" * 60)
    print("           EXAMPLE 4: MODULE COMPARISON")
    print("=" * 60)
    print()

    db = PVModuleDatabase()

    # Find some modules to compare
    print("🔍 Finding modules for comparison...")

    # Get top 3 highest power modules
    high_power_modules = db.search_modules(limit=3)

    if len(high_power_modules) >= 2:
        print(f"📋 Comparing top {len(high_power_modules)} highest power modules:")
        print()

        # Create comparison table
        print(f"{'Parameter':<25} {'Module 1':<20} {'Module 2':<20} {'Module 3':<20}")
        print("-" * 85)

        # Basic info
        manufacturers = [m['manufacturer'] for m in high_power_modules]
        models = [m['model'] for m in high_power_modules]

        print(f"{'Manufacturer':<25} {manufacturers[0]:<20} {manufacturers[1] if len(manufacturers) > 1 else 'N/A':<20} {manufacturers[2] if len(manufacturers) > 2 else 'N/A':<20}")
        print(f"{'Model':<25} {models[0]:<20} {models[1] if len(models) > 1 else 'N/A':<20} {models[2] if len(models) > 2 else 'N/A':<20}")

        # Power specs
        powers = [f"{m['pmax_stc']:.0f}W" if m['pmax_stc'] else "N/A" for m in high_power_modules]
        vocs = [f"{m['voc_stc']:.1f}V" if m['voc_stc'] else "N/A" for m in high_power_modules]
        iscs = [f"{m['isc_stc']:.1f}A" if m['isc_stc'] else "N/A" for m in high_power_modules]

        print(f"{'Power (Pmax)':<25} {powers[0]:<20} {powers[1] if len(powers) > 1 else 'N/A':<20} {powers[2] if len(powers) > 2 else 'N/A':<20}")
        print(f"{'Voltage (Voc)':<25} {vocs[0]:<20} {vocs[1] if len(vocs) > 1 else 'N/A':<20} {vocs[2] if len(vocs) > 2 else 'N/A':<20}")
        print(f"{'Current (Isc)':<25} {iscs[0]:<20} {iscs[1] if len(iscs) > 1 else 'N/A':<20} {iscs[2] if len(iscs) > 2 else 'N/A':<20}")

        # Efficiency and dimensions
        efficiencies = [f"{m['efficiency_stc']:.2f}%" if m['efficiency_stc'] else "N/A" for m in high_power_modules]
        dimensions = [f"{m['length']:.0f}x{m['width']:.0f}mm" if m['length'] and m['width'] else "N/A" for m in high_power_modules]

        print(f"{'Efficiency':<25} {efficiencies[0]:<20} {efficiencies[1] if len(efficiencies) > 1 else 'N/A':<20} {efficiencies[2] if len(efficiencies) > 2 else 'N/A':<20}")
        print(f"{'Dimensions':<25} {dimensions[0]:<20} {dimensions[1] if len(dimensions) > 1 else 'N/A':<20} {dimensions[2] if len(dimensions) > 2 else 'N/A':<20}")

    else:
        print("❌ Not enough modules in database for comparison")
    print()


def example_5_export_data():
    """Example 5: Export data to CSV."""
    print("=" * 60)
    print("           EXAMPLE 5: EXPORT DATA")
    print("=" * 60)
    print()

    db = PVModuleDatabase()

    # Export 1: All high-power modules
    print("📤 Export 1: High-power modules (>500W) to CSV")
    export_file_1 = "high_power_modules.csv"
    count_1 = db.export_to_csv(export_file_1, {"min_power": 500})
    print(f"   ✅ Exported {count_1} modules to {export_file_1}")

    # Export 2: All modules from specific manufacturer
    print("📤 Export 2: All Longi modules to CSV")
    export_file_2 = "longi_modules.csv"
    count_2 = db.export_to_csv(export_file_2, {"manufacturer": "Longi"})
    print(f"   ✅ Exported {count_2} modules to {export_file_2}")

    # Export 3: High-efficiency modules
    print("📤 Export 3: High-efficiency modules (>22%) to CSV")
    export_file_3 = "high_efficiency_modules.csv"
    count_3 = db.export_to_csv(export_file_3, {"min_efficiency": 22})
    print(f"   ✅ Exported {count_3} modules to {export_file_3}")

    print()
    print("📁 CSV files created in project directory:")
    print(f"   📄 {export_file_1}")
    print(f"   📄 {export_file_2}")
    print(f"   📄 {export_file_3}")
    print()


def main():
    """Run all examples."""
    print("🚀 PV MODULE DATABASE - USAGE EXAMPLES")
    print("=" * 60)
    print()

    try:
        # Check if database exists and has data
        db = PVModuleDatabase()
        stats = db.get_statistics()

        if stats['total_modules'] == 0:
            print("⚠️  Database is empty. Running Example 1 to populate it first...")
            example_1_populate_database()
            print()
        else:
            print(f"✅ Database contains {stats['total_modules']} modules")
            print()

        # Run all examples
        example_2_search_and_filter()
        example_3_statistics_and_analysis()
        example_4_module_comparison()
        example_5_export_data()

        print("🎉 All examples completed successfully!")
        print()
        print("💡 You can now use these patterns in your own scripts:")
        print("   - Search modules by any criteria")
        print("   - Compare modules side by side")
        print("   - Export filtered data to CSV")
        print("   - Get comprehensive statistics")

    except Exception as e:
        print(f"❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
