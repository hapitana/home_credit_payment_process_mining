from pathlib import Path

import polars as pl


base_dir = Path(__file__).resolve().parents[1]
raw_dir = base_dir / "data" / "raw"
report_dir = base_dir / "outputs" / "reports"

report_dir.mkdir(parents=True, exist_ok=True)

file_path = raw_dir / "installments_payments.csv"
report_path = report_dir / "duplicate_pattern_report.txt"
examples_path = report_dir / "duplicate_installment_examples.csv"

if not file_path.exists():
    raise FileNotFoundError(f"Input file not found: {file_path}")

key_columns = [
    "SK_ID_PREV",
    "NUM_INSTALMENT_NUMBER",
    "NUM_INSTALMENT_VERSION",
]

print("Inspecting repeated installment patterns...")

lazy_frame = pl.scan_csv(file_path)

duplicate_groups = (
    lazy_frame
    .group_by(key_columns)
    .agg(
        pl.len().alias("records_per_key"),
        pl.col("DAYS_INSTALMENT").n_unique().alias(
            "unique_due_dates"
        ),
        pl.col("DAYS_ENTRY_PAYMENT").n_unique().alias(
            "unique_payment_dates"
        ),
        pl.col("AMT_INSTALMENT").n_unique().alias(
            "unique_scheduled_amounts"
        ),
        pl.col("AMT_PAYMENT").n_unique().alias(
            "unique_payment_amounts"
        ),
    )
    .filter(pl.col("records_per_key") > 1)
)

print("Calculating duplicate group characteristics...")

summary = (
    duplicate_groups
    .select(
        pl.len().alias("duplicate_key_groups"),
        (pl.col("records_per_key") == 2).sum().alias(
            "groups_with_two_records"
        ),
        (pl.col("records_per_key") > 2).sum().alias(
            "groups_with_more_than_two_records"
        ),
        (pl.col("unique_due_dates") > 1).sum().alias(
            "groups_with_multiple_due_dates"
        ),
        (pl.col("unique_payment_dates") > 1).sum().alias(
            "groups_with_multiple_payment_dates"
        ),
        (pl.col("unique_scheduled_amounts") > 1).sum().alias(
            "groups_with_multiple_scheduled_amounts"
        ),
        (pl.col("unique_payment_amounts") > 1).sum().alias(
            "groups_with_multiple_payment_amounts"
        ),
    )
    .collect()
    .to_dicts()[0]
)

print("Selecting representative repeated-key examples...")

sample_keys = (
    duplicate_groups
    .sort(
        ["records_per_key", "SK_ID_PREV"],
        descending=[True, False],
    )
    .head(10)
    .select(key_columns)
    .collect()
)

examples = (
    lazy_frame
    .join(
        sample_keys.lazy(),
        on=key_columns,
        how="inner",
    )
    .sort(key_columns + ["DAYS_ENTRY_PAYMENT"])
    .collect()
)

examples.write_csv(examples_path)

report_lines = [
    "DUPLICATE INSTALLMENT PATTERN REPORT",
    "====================================",
    "",
]

for key, value in summary.items():
    report_lines.append(f"{key}: {value:,}")

report_lines.extend(
    [
        "",
        "INTERPRETATION",
        "==============",
        (
            "Repeated keys are not automatically treated as "
            "erroneous duplicate records."
        ),
        (
            "Different payment dates or payment amounts may "
            "indicate multiple records associated with one "
            "installment key."
        ),
        (
            "Further inspection is required before defining "
            "deduplication rules."
        ),
    ]
)

report_path.write_text(
    "\n".join(report_lines),
    encoding="utf-8",
)

print("\nDuplicate pattern summary")

for key, value in summary.items():
    print(f"{key}: {value:,}")

print("\nRepresentative repeated-key records")
print(examples)

print("\nInspection completed.")
print(f"Report saved to: {report_path}")
print(f"Example records saved to: {examples_path}")