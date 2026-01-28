import json
from pathlib import Path
import importlib.util

# Load csv_exporter module directly to avoid importing src package
spec = importlib.util.spec_from_file_location("csv_exporter", "src/csv_exporter.py")
csv_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(csv_mod)
CSVExporter = csv_mod.CSVExporter

in_path = Path("data/chicago_records.json")
out_path = Path("data/chicago_records.csv")

if not in_path.exists():
    print("Input JSON not found:", in_path)
    raise SystemExit(1)

with in_path.open("r", encoding="utf-8") as f:
    records = json.load(f)

ok = CSVExporter.export(records, str(out_path))
print("Export success:", ok)
is_valid, errors = CSVExporter.validate_csv(str(out_path))
print("Validation:", is_valid)
if errors:
    print("Errors:", errors)
