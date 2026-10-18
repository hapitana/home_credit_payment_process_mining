from pathlib import Path

import polars as pl


base_dir = Path(__file__).resolve().parents[1]
raw_dir = base_dir / "data" / "raw"
report_dir = base_dir / "outputs" / "reports"

report_dir.mkdir(parents=True, exist_ok=True)

file_path = raw_dir / "installments_payments.csv"
report_path = report_dir / "loan_case_audit.txt"

if not file_path.exists():
    raise FileNotFoundError(f"Input file not found: {file_path}")

print("Auditing previous-loan case structure...")

lazy_frame = pl.scan_csv(file_path)

loan_profile = (
    lazy_frame
    .group_by("SK_ID_PREV")
    .agg(
        pl.len().alias("records_per_loan"),
        pl.col("SK_ID_CURR").n_unique().alias(
            "customer_ids_per_loan"
        ),
        pl.col("NUM_INSTALMENT_NUMBER").n_unique().alias(
            "unique_installment_numbers"
        ),
    )
)

print("Calculating loan-level statistics...")

loan_summary = (
    loan_profile
    .select(
        pl.len().alias("unique_loans"),
        pl.col("records_per_loan").mean().alias(
            "mean_records_per_loan"
        ),
        pl.col("records_per_loan").median().alias(
            "median_records_per_loan"
        ),
        pl.col("records_per_loan").max().alias(
            "maximum_records_per_loan"
        ),
        (pl.col("records_per_loan") == 1).sum().alias(
            "loans_with_one_record"
        ),
        (pl.col("records_per_loan") > 1).sum().alias(
            "loans_with_multiple_records"
        ),
        (pl.col("customer_ids_per_loan") > 1).sum().alias(
            "loans_linked_to_multiple_customers"
        ),
    )
    .collect()
    .to_dicts()[0]
)

print("Checking repeated installment keys...")

duplicate_summary = (
    lazy_frame
    .group_by(
        [
            "SK_ID_PREV",
            "NUM_INSTALMENT_NUMBER",
            "NUM_INSTALMENT_VERSION",
        ]
    )
    .agg(pl.len().alias("records_per_key"))
    .filter(pl.col("records_per_key") > 1)
    .select(
        pl.len().alias("duplicate_key_groups"),
        (pl.col("records_per_key") - 1).sum().alias(
            "extra_records_in_duplicate_groups"
        ),
    )
    .collect()
    .to_dicts()[0]
)

report_lines = [
    "PREVIOUS LOAN CASE AUDIT",
    "========================",
    "",
    f"Unique loans: {loan_summary['unique_loans']:,}",
    (
        "Mean records per loan: "
        f"{loan_summary['mean_records_per_loan']:.2f}"
    ),
    (
        "Median records per loan: "
        f"{loan_summary['median_records_per_loan']:.2f}"
    ),
    (
        "Maximum records per loan: "
        f"{loan_summary['maximum_records_per_loan']:,}"
    ),
    (
        "Loans with one record: "
        f"{loan_summary['loans_with_one_record']:,}"
    ),
    (
        "Loans with multiple records: "
        f"{loan_summary['loans_with_multiple_records']:,}"
    ),
    (
        "Loans linked to multiple customers: "
        f"{loan_summary['loans_linked_to_multiple_customers']:,}"
    ),
    "",
    "REPEATED INSTALLMENT KEY AUDIT",
    "==============================",
    (
        "Duplicate key groups: "
        f"{duplicate_summary['duplicate_key_groups']:,}"
    ),
    (
        "Extra records in duplicate groups: "
        f"{duplicate_summary['extra_records_in_duplicate_groups']:,}"
    ),
]

report_path.write_text(
    "\n".join(report_lines),
    encoding="utf-8",
)

print("\nLoan case summary")

for key, value in loan_summary.items():
    if isinstance(value, float):
        print(f"{key}: {value:.2f}")
    else:
        print(f"{key}: {value:,}")

print("\nRepeated installment key summary")

for key, value in duplicate_summary.items():
    print(f"{key}: {value:,}")

print("\nAudit completed.")
print(f"Report saved to: {report_path}")