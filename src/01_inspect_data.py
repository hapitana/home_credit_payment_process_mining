from pathlib import Path

import polars as pl


base_dir = Path(__file__).resolve().parents[1]
raw_dir = base_dir / "data" / "raw"
report_dir = base_dir / "outputs" / "reports"

report_dir.mkdir(parents=True, exist_ok=True)

file_names = [
    "application_train.csv",
    "previous_application.csv",
    "installments_payments.csv",
]

report_lines = []

for file_name in file_names:
    file_path = raw_dir / file_name

    if not file_path.exists():
        print(f"\nFile not found: {file_path}")
        report_lines.append(f"\nFILE NOT FOUND: {file_name}")
        continue

    file_size_mb = file_path.stat().st_size / (1024 ** 2)

    print(f"\nInspecting file: {file_name}")
    print(f"File size: {file_size_mb:.2f} MB")

    lazy_frame = pl.scan_csv(file_path)
    schema = lazy_frame.collect_schema()

    column_count = len(schema)

    print(f"Number of columns: {column_count}")
    print("\nColumn names and data types:")

    report_lines.append(f"\nFILE: {file_name}")
    report_lines.append(f"File size: {file_size_mb:.2f} MB")
    report_lines.append(f"Number of columns: {column_count}")

    for column_name, data_type in schema.items():
        column_info = f"{column_name}: {data_type}"

        print(column_info)
        report_lines.append(column_info)

    print("\nCounting rows...")

    row_count = lazy_frame.select(pl.len()).collect().item()

    print(f"Number of rows: {row_count:,}")
    report_lines.append(f"Number of rows: {row_count:,}")

report_path = report_dir / "data_schema.txt"

report_path.write_text(
    "\n".join(report_lines),
    encoding="utf-8",
)

print("\nData inspection completed.")
print(f"Schema report saved to: {report_path}")