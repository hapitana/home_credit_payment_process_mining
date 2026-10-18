from pathlib import Path

import polars as pl


base_dir = Path(__file__).resolve().parents[1]
processed_dir = base_dir / "data" / "processed"
report_dir = base_dir / "outputs" / "reports"

report_dir.mkdir(parents=True, exist_ok=True)

input_path = processed_dir / "payment_event_log.parquet"
report_path = report_dir / "event_log_validation_report.txt"
sample_path = report_dir / "sample_loan_traces.csv"

if not input_path.exists():
    raise FileNotFoundError(f"Input file not found: {input_path}")

print("Validating event log structure...")

event_log = pl.scan_parquet(input_path)

case_profile = (
    event_log
    .group_by("case_id")
    .agg(
        pl.len().alias("event_count"),
        pl.col("customer_id").n_unique().alias("customer_count"),
        pl.col("activity").n_unique().alias("activity_types"),
        pl.col("timestamp").min().alias("first_event"),
        pl.col("timestamp").max().alias("last_event"),
    )
)

print("Calculating case-level statistics...")

case_summary = (
    case_profile
    .select(
        pl.len().alias("total_cases"),
        pl.col("event_count").mean().alias("mean_events_per_case"),
        pl.col("event_count").median().alias("median_events_per_case"),
        pl.col("event_count").max().alias("maximum_events_per_case"),
        (pl.col("event_count") == 1).sum().alias(
            "single_event_cases"
        ),
        (pl.col("customer_count") != 1).sum().alias(
            "cases_with_invalid_customer_count"
        ),
        (pl.col("last_event") < pl.col("first_event")).sum().alias(
            "cases_with_invalid_time_range"
        ),
        pl.col("activity_types").max().alias(
            "maximum_activity_types_per_case"
        ),
    )
    .collect()
    .to_dicts()[0]
)

print("Calculating activity distribution...")

activity_summary = (
    event_log
    .group_by("activity")
    .agg(pl.len().alias("event_count"))
    .sort("event_count", descending=True)
    .collect()
)

print("Selecting representative loan traces...")

sample_cases = (
    case_profile
    .sort("event_count", descending=True)
    .head(10)
    .select("case_id")
    .collect()
)

sample_traces = (
    event_log
    .join(sample_cases.lazy(), on="case_id", how="inner")
    .sort(
        [
            "case_id",
            "timestamp",
            "installment_number",
            "installment_version",
        ]
    )
    .select(
        "case_id",
        "customer_id",
        "timestamp",
        "activity",
        "installment_number",
        "installment_version",
        "payment_delay_days",
        "scheduled_amount",
        "payment_amount",
    )
    .collect()
)

sample_traces.write_csv(sample_path)

report_lines = [
    "EVENT LOG VALIDATION REPORT",
    "===========================",
    "",
]

for key, value in case_summary.items():
    if isinstance(value, float):
        report_lines.append(f"{key}: {value:.2f}")
    else:
        report_lines.append(f"{key}: {value:,}")

report_lines.extend(
    [
        "",
        "ACTIVITY DISTRIBUTION",
        "=====================",
    ]
)

for row in activity_summary.iter_rows(named=True):
    report_lines.append(
        f"{row['activity']}: {row['event_count']:,}"
    )

report_lines.extend(
    [
        "",
        "METHODOLOGICAL NOTES",
        "====================",
        (
            "Cases with one event may have incomplete observed "
            "payment histories."
        ),
        (
            "Payment timing categories describe payment outcomes, "
            "not the full business workflow."
        ),
        (
            "Equal timestamps may occur; secondary sorting is used "
            "for reproducible inspection, not to assert true event order."
        ),
    ]
)

report_path.write_text(
    "\n".join(report_lines),
    encoding="utf-8",
)

print("\nCase-level validation")

for key, value in case_summary.items():
    if isinstance(value, float):
        print(f"{key}: {value:.2f}")
    else:
        print(f"{key}: {value:,}")

print("\nActivity distribution")
print(activity_summary)

print("\nSample trace records")
print(f"Number of sample records: {sample_traces.height:,}")

print("\nValidation completed.")
print(f"Report saved to: {report_path}")
print(f"Sample traces saved to: {sample_path}")