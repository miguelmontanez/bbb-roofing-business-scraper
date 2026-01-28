"""
Merge multiple CSV files (partial scraper runs) into a single CSV.
Usage:
    python merge_csvs.py --input data/*.csv --output data/merged_records.csv [--dedupe]

If --dedupe is provided, rows will be deduplicated by the tuple
(business_name, street_address, city, state).
"""
import argparse
import csv
from pathlib import Path
from typing import List, Set, Tuple


def merge_csv_files(inputs: List[str], output: str, dedupe: bool = False) -> int:
    files = []
    for pattern in inputs:
        files.extend(Path().glob(pattern))

    files = [f for f in files if f.is_file()]
    if not files:
        print(f"No files matched input patterns: {inputs}")
        return 0

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    seen_keys: Set[Tuple[str, str, str, str]] = set()
    total_written = 0
    header_written = False
    header = None

    for f in files:
        with f.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames:
                if not header_written:
                    header = reader.fieldnames
                    with output_path.open("w", encoding="utf-8", newline="") as outfh:
                        writer = csv.DictWriter(outfh, fieldnames=header, restval="")
                        writer.writeheader()
                    header_written = True
                elif header and reader.fieldnames != header:
                    print(f"Warning: header mismatch in {f}; attempting to align columns.")

            for row in reader:
                if dedupe:
                    key = (
                        (row.get("business_name") or "").strip().lower(),
                        (row.get("street_address") or "").strip().lower(),
                        (row.get("city") or "").strip().lower(),
                        (row.get("state") or "").strip().lower(),
                    )
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                # Append row to output
                with output_path.open("a", encoding="utf-8", newline="") as outfh:
                    writer = csv.DictWriter(outfh, fieldnames=header, restval="")
                    writer.writerow({col: row.get(col, "") for col in header})
                    total_written += 1

    print(f"Merged {len(files)} files -> {output_path} (rows written: {total_written})")
    return total_written


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge partial CSV outputs into one CSV")
    parser.add_argument("--input", nargs="+", required=True, help="Input file glob(s), e.g. data/*.csv")
    parser.add_argument("--output", required=False, default="data/merged_records.csv", help="Output CSV path")
    parser.add_argument("--dedupe", action="store_true", help="Deduplicate rows by business_name+address+city+state")

    args = parser.parse_args()
    merge_csv_files(args.input, args.output, dedupe=args.dedupe)
