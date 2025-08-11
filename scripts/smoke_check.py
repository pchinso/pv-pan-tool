import os
import sys
from pathlib import Path

# Ensure src is on sys.path
repo_root = Path(__file__).resolve().parents[1]
src_dir = repo_root / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(repo_root))

# Use a headless backend to avoid GUI requirements during import
os.environ.setdefault("MPLBACKEND", "Agg")

ok = True
errors = []

# Try importing controllers and UI widgets
try:
    from desktop_app.controllers.database_controller import DatabaseController
except Exception as e:
    ok = False
    errors.append(f"Import DatabaseController failed: {e}")

try:
    from desktop_app.ui.compare_widget import CompareWidget  # noqa: F401
except Exception as e:
    ok = False
    errors.append(f"Import CompareWidget failed: {e}")

try:
    from desktop_app.ui.stats_widget import StatsWidget  # noqa: F401
except Exception as e:
    ok = False
    errors.append(f"Import StatsWidget failed: {e}")

# Try fetching statistics
summary = {}
if ok:
    try:
        db = DatabaseController()
        stats = db.get_detailed_statistics()
        if 'error' in stats:
            ok = False
            errors.append(f"DB stats error: {stats['error']}")
        else:
            summary = {
                'total_modules': stats.get('total_modules', 0),
                'manufacturers': stats.get('total_manufacturers', 0),
                'manufacturer_stats': len(stats.get('manufacturer_statistics', [])),
                'power_bins': len(stats.get('power_range_distribution', [])),
                'eff_bins': len(stats.get('efficiency_range_distribution', [])),
                'power_values': len(stats.get('power_values', [])),
                'eff_values': len(stats.get('efficiency_values', [])),
            }
    except Exception as e:
        ok = False
        errors.append(f"DB stats exception: {e}")

if ok:
    print("SMOKE_CHECK_OK")
    print(summary)
    sys.exit(0)
else:
    print("SMOKE_CHECK_FAIL")
    for err in errors:
        print("- ", err)
    sys.exit(1)
